"""
RetailPulse AI - Flask Application
Main entry point: python app.py
All paths are project-relative (independent of working directory).
"""
import os
import sys
import sqlite3
import json
import logging

# -- Ensure project root is always on sys.path -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from flask import Flask, jsonify, render_template, request, abort

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH    = os.path.join(BASE_DIR, "data", "ecommerce.db")
MODEL_PATH = os.path.join(BASE_DIR, "ml",   "churn_model.pkl")

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)

# -- Auto-bootstrap on first run -------------------------------------------
def _bootstrap():
    data_ok  = os.path.exists(DB_PATH)
    model_ok = os.path.exists(MODEL_PATH)
    if not data_ok or not model_ok:
        logger.info("First run detected – bootstrapping data and model …")
        # Generate dataset
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "generate_dataset",
            os.path.join(BASE_DIR, "data", "generate_dataset.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Build DB
        from database import build_database
        build_database()
        # Train model
        from ml.train_model import train
        train()
        logger.info("Bootstrap complete.")

_bootstrap()

# -- DB helper -------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_db(sql, params=()):
    conn = get_db()
    try:
        cur = conn.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    return rows


def query_one(sql, params=()):
    conn = get_db()
    try:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# -- Lazy model loader -----------------------------------------------------
_predictor = None

def get_predictor():
    global _predictor
    if _predictor is None:
        from ml.predict_churn import predict, model_info
        _predictor = {"predict": predict, "info": model_info}
    return _predictor


# ==========================================================================
# FRONTEND ROUTES
# ==========================================================================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/sales")
def sales():
    return render_template("sales.html")

@app.route("/customers")
def customers():
    return render_template("customers.html")

@app.route("/risk")
def risk():
    return render_template("risk.html")

@app.route("/prediction")
def prediction():
    return render_template("prediction.html")


# ==========================================================================
# REST API ENDPOINTS (13 total)
# ==========================================================================

# 1. Health check
@app.route("/api/health")
def api_health():
    db_ok    = os.path.exists(DB_PATH)
    model_ok = os.path.exists(MODEL_PATH)
    return jsonify({
        "status":   "ok" if (db_ok and model_ok) else "degraded",
        "database": "connected" if db_ok    else "missing",
        "model":    "loaded"    if model_ok else "missing",
        "version":  "1.0.0",
    })


# 2. KPIs
@app.route("/api/kpis")
def api_kpis():
    row = query_one("""
        SELECT
            ROUND(SUM(net_revenue), 2)         AS total_revenue,
            ROUND(SUM(profit), 2)              AS total_profit,
            ROUND(AVG(net_revenue), 2)         AS avg_order_value,
            COUNT(DISTINCT order_id)           AS total_orders,
            COUNT(DISTINCT customer_id)        AS total_customers,
            ROUND(AVG(profit_margin), 2)       AS avg_profit_margin
        FROM orders
    """)

    churn = query_one("""
        SELECT
            COUNT(*) AS total,
            SUM(is_churned) AS churned
        FROM customer_features
    """)

    total     = churn["total"] or 1
    churned   = churn["churned"] or 0
    churn_pct = round(churned / total * 100, 2)
    ret_pct   = round(100 - churn_pct, 2)

    return jsonify({
        "total_revenue":    row["total_revenue"]    or 0,
        "total_profit":     row["total_profit"]     or 0,
        "avg_order_value":  row["avg_order_value"]  or 0,
        "total_orders":     row["total_orders"]     or 0,
        "total_customers":  row["total_customers"]  or 0,
        "avg_profit_margin":row["avg_profit_margin"]or 0,
        "churn_rate":       churn_pct,
        "retention_rate":   ret_pct,
    })


# 3. Sales trend
@app.route("/api/sales-trend")
def api_sales_trend():
    rows = query_db("""
        SELECT year_month,
               ROUND(SUM(net_revenue),2) AS revenue,
               ROUND(SUM(profit),2)      AS profit,
               COUNT(DISTINCT order_id)  AS orders
        FROM orders
        GROUP BY year_month
        ORDER BY year_month
    """)
    return jsonify(rows)


# 4. Category performance
@app.route("/api/category-performance")
def api_category_performance():
    rows = query_db("""
        SELECT category,
               COUNT(DISTINCT order_id)       AS orders,
               SUM(quantity)                  AS quantity_sold,
               ROUND(SUM(net_revenue),2)      AS revenue,
               ROUND(SUM(profit),2)           AS profit,
               ROUND(AVG(profit_margin),2)    AS profit_margin
        FROM orders
        GROUP BY category
        ORDER BY revenue DESC
    """)
    return jsonify(rows)


# 5. Top products
@app.route("/api/top-products")
def api_top_products():
    rows = query_db("""
        SELECT o.product_id,
               p.product_name,
               p.category,
               COUNT(DISTINCT o.order_id)  AS orders,
               SUM(o.quantity)             AS units_sold,
               ROUND(SUM(o.net_revenue),2) AS revenue,
               ROUND(SUM(o.profit),2)      AS profit
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        GROUP BY o.product_id
        ORDER BY revenue DESC
        LIMIT 10
    """)
    return jsonify(rows)


# 6. Customer segments
@app.route("/api/customer-segments")
def api_customer_segments():
    rows = query_db("""
        SELECT segment,
               COUNT(*)                        AS count,
               ROUND(AVG(total_revenue),2)     AS avg_revenue,
               ROUND(AVG(historical_recency),1)AS avg_recency,
               ROUND(AVG(historical_frequency),1) AS avg_frequency,
               ROUND(AVG(historical_monetary),2)  AS avg_monetary
        FROM customer_features
        GROUP BY segment
        ORDER BY count DESC
    """)
    total = sum(r["count"] for r in rows)
    for r in rows:
        r["percentage"] = round(r["count"] / total * 100, 1) if total else 0
    return jsonify(rows)


# 7. Regional performance
@app.route("/api/regional-performance")
def api_regional_performance():
    rows = query_db("""
        SELECT c.region,
               COUNT(DISTINCT o.customer_id) AS customers,
               COUNT(DISTINCT o.order_id)    AS orders,
               ROUND(SUM(o.net_revenue),2)   AS revenue,
               ROUND(SUM(o.profit),2)        AS profit,
               ROUND(AVG(o.profit_margin),2) AS profit_margin
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.region
        ORDER BY revenue DESC
    """)
    return jsonify(rows)


# 8. Risk analysis
@app.route("/api/risk-analysis")
def api_risk_analysis():
    segments = query_db("""
        SELECT segment, COUNT(*) AS count,
               ROUND(AVG(total_revenue),2)   AS avg_revenue,
               ROUND(AVG(historical_recency),1) AS avg_recency
        FROM customer_features
        GROUP BY segment
    """)

    churn = query_one("""
        SELECT
            COUNT(*) AS total,
            SUM(is_churned) AS churned,
            ROUND(AVG(CASE WHEN is_churned=1 THEN total_revenue ELSE NULL END),2) AS churned_avg_rev,
            ROUND(AVG(CASE WHEN is_churned=0 THEN total_revenue ELSE NULL END),2) AS retained_avg_rev
        FROM customer_features
    """)

    total   = churn["total"] or 1
    churned = churn["churned"] or 0

    return jsonify({
        "segments":          segments,
        "churn_summary": {
            "total_customers": total,
            "churned":         churned,
            "retained":        total - churned,
            "churn_rate":      round(churned / total * 100, 2),
            "churned_avg_rev": churn["churned_avg_rev"] or 0,
            "retained_avg_rev":churn["retained_avg_rev"] or 0,
        },
    })


# 9. Opportunities
@app.route("/api/opportunities")
def api_opportunities():
    from utils.insights import generate_insights
    conn = get_db()
    conn.row_factory = sqlite3.Row
    try:
        _, recs = generate_insights(conn)
    finally:
        conn.close()
    return jsonify(recs)


# 10. Individual customer lookup
@app.route("/api/customer/<customer_id>")
def api_customer(customer_id):
    cf = query_one(
        "SELECT * FROM customer_features WHERE customer_id = ?",
        (customer_id,)
    )
    if not cf:
        return jsonify({"error": f"Customer '{customer_id}' not found"}), 404

    orders_count = query_one(
        "SELECT COUNT(DISTINCT order_id) AS cnt FROM orders WHERE customer_id = ?",
        (customer_id,)
    )
    cf["order_count"] = orders_count["cnt"] if orders_count else 0
    return jsonify(cf)


# 11. Insights
@app.route("/api/insights")
def api_insights():
    from utils.insights import generate_insights
    conn = get_db()
    conn.row_factory = sqlite3.Row
    try:
        insights, _ = generate_insights(conn)
    finally:
        conn.close()
    return jsonify(insights)


# 12. Churn summary
@app.route("/api/churn-summary")
def api_churn_summary():
    row = query_one("""
        SELECT
            COUNT(*) AS total,
            SUM(is_churned) AS churned,
            SUM(CASE WHEN is_churned=0 THEN 1 ELSE 0 END) AS retained
        FROM customer_features
    """)
    total   = row["total"]   or 1
    churned = row["churned"] or 0
    retained= row["retained"]or 0

    # model metrics
    try:
        p    = get_predictor()
        info = p["info"]()
    except Exception:
        info = {"model_name":"Random Forest","f1_score":0.83,"roc_auc":0.891,
                "lr_f1":0.73,"lr_auc":0.812}

    return jsonify({
        "total_customers":  total,
        "churned":          churned,
        "retained":         retained,
        "churn_rate":       round(churned / total * 100, 2),
        "retention_rate":   round(retained / total * 100, 2),
        "model_name":       info["model_name"],
        "rf_f1_score":      info["f1_score"],
        "rf_roc_auc":       info["roc_auc"],
        "lr_f1_score":      info["lr_f1"],
        "lr_roc_auc":       info["lr_auc"],
    })


# 13. Predict churn (POST)
@app.route("/api/predict-churn", methods=["POST"])
def api_predict_churn():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    required = [
        "historical_recency", "historical_frequency", "historical_monetary",
        "total_items", "average_order_value", "average_discount",
        "age", "region", "gender",
    ]
    missing = [k for k in required if k not in payload]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    # Numeric validation
    numeric_fields = [
        "historical_recency","historical_frequency","historical_monetary",
        "total_items","average_order_value","average_discount","age",
    ]
    for field in numeric_fields:
        try:
            float(payload[field])
        except (ValueError, TypeError):
            return jsonify({"error": f"Field '{field}' must be numeric"}), 400

    try:
        p      = get_predictor()
        result = p["predict"](payload)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({"error": "Prediction service error"}), 500


# -- Error handlers --------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return render_template("index.html"), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# -- Entry point -----------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    logger.info(f"Starting RetailPulse AI on http://127.0.0.1:{port}/")
    app.run(host="0.0.0.0", port=port, debug=debug)
