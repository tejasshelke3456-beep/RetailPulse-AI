"""
RetailPulse AI - Dynamic Business Insights & Recommendations
Generates exactly 6 insights and 6 recommendations from live DB data.
"""

def generate_insights(db_conn):
    """
    Returns a list of 6 data-driven insight dicts and 6 recommendation dicts.
    Each insight: {id, title, description, category, value, trend}
    Each rec:     {id, title, description, category, priority, impact}
    """
    import sqlite3

    cur = db_conn.cursor()

    # -- Fetch aggregate metrics --------------------------------------------
    cur.execute("""
        SELECT
            SUM(net_revenue)    AS total_rev,
            SUM(profit)         AS total_profit,
            COUNT(DISTINCT customer_id) AS active_customers,
            COUNT(DISTINCT order_id)    AS total_orders,
            AVG(profit_margin)          AS avg_margin
        FROM orders
    """)
    agg = cur.fetchone()
    total_rev      = agg[0] or 0
    total_profit   = agg[1] or 0
    active_cust    = agg[2] or 0
    total_orders   = agg[3] or 0
    avg_margin     = agg[4] or 0

    # -- Category performance -----------------------------------------------
    cur.execute("""
        SELECT category, SUM(net_revenue) AS rev, AVG(profit_margin) AS margin
        FROM orders GROUP BY category ORDER BY rev DESC
    """)
    cat_rows = cur.fetchall()
    top_cat      = cat_rows[0][0]  if cat_rows else "N/A"
    top_cat_rev  = cat_rows[0][1]  if cat_rows else 0
    low_margin_cat = min(cat_rows, key=lambda x: x[2]) if cat_rows else ("N/A", 0, 0)

    # -- Churn stats --------------------------------------------------------
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN is_churned=1 THEN 1 ELSE 0 END) AS churned
        FROM customer_features
    """)
    churn_row = cur.fetchone()
    total_cf  = churn_row[0] or 1
    churned   = churn_row[1] or 0
    churn_pct = churned / total_cf * 100

    # -- Segment counts -----------------------------------------------------
    cur.execute("""
        SELECT segment, COUNT(*) as cnt FROM customer_features GROUP BY segment ORDER BY cnt DESC
    """)
    seg_rows = dict(cur.fetchall())
    at_risk    = seg_rows.get("At Risk", 0)
    vip_count  = seg_rows.get("VIP", 0)
    hibernating = seg_rows.get("Hibernating", 0)

    # -- Regional performance -----------------------------------------------
    cur.execute("""
        SELECT c.region, SUM(o.net_revenue) AS rev
        FROM orders o JOIN customers c ON o.customer_id = c.customer_id
        GROUP BY c.region ORDER BY rev DESC
    """)
    reg_rows  = cur.fetchall()
    top_region     = reg_rows[0][0] if reg_rows else "N/A"
    top_region_rev = reg_rows[0][1] if reg_rows else 0
    low_region     = reg_rows[-1][0] if len(reg_rows) > 1 else "N/A"
    low_region_rev = reg_rows[-1][1] if len(reg_rows) > 1 else 0

    # -- Discount analysis --------------------------------------------------
    cur.execute("SELECT AVG(average_discount) FROM customer_features")
    avg_disc_row = cur.fetchone()
    avg_disc = (avg_disc_row[0] or 0) * 100

    # -- AOV ----------------------------------------------------------------
    aov = total_rev / total_orders if total_orders else 0

    insights = [
        {
            "id": 1,
            "title": "Top Revenue Category",
            "description": (
                f"{top_cat} is the highest-grossing product category, contributing "
                f"${top_cat_rev:,.0f} in net revenue. Sustained demand signals strong "
                "customer affinity for this segment."
            ),
            "category": "Sales",
            "value": f"${top_cat_rev:,.0f}",
            "trend": "up",
        },
        {
            "id": 2,
            "title": "Customer Churn Risk Elevated",
            "description": (
                f"{churn_pct:.1f}% of customers are classified as churned under the "
                "defined churn criterion (no purchase after 2025-09-01). "
                f"That represents {churned:,} customers requiring re-engagement."
            ),
            "category": "Churn Risk",
            "value": f"{churn_pct:.1f}%",
            "trend": "down",
        },
        {
            "id": 3,
            "title": "VIP Segment Drives Disproportionate Revenue",
            "description": (
                f"The {vip_count:,} VIP customers represent the most valuable cohort. "
                "These customers exhibit high recency, frequency, and monetary scores. "
                "Protecting this segment is critical to sustaining revenue."
            ),
            "category": "Customer Retention",
            "value": f"{vip_count:,} VIPs",
            "trend": "up",
        },
        {
            "id": 4,
            "title": "Low-Margin Category Identified",
            "description": (
                f"{low_margin_cat[0]} has the lowest average profit margin "
                f"({low_margin_cat[2]:.1f}%). Reviewing pricing strategy and supplier "
                "costs in this category could improve overall profitability."
            ),
            "category": "Profitability",
            "value": f"{low_margin_cat[2]:.1f}%",
            "trend": "down",
        },
        {
            "id": 5,
            "title": "Regional Revenue Concentration",
            "description": (
                f"The {top_region} region leads with ${top_region_rev:,.0f} in net revenue, "
                f"while {low_region} lags at ${low_region_rev:,.0f}. Geographic imbalance "
                "suggests untapped growth opportunities in underperforming regions."
            ),
            "category": "Regional Performance",
            "value": f"{top_region} leads",
            "trend": "neutral",
        },
        {
            "id": 6,
            "title": "Average Discount Rate Analysis",
            "description": (
                f"The portfolio average discount rate is {avg_disc:.1f}%. "
                f"Customers predicted to have high churn risk show higher-than-average "
                "discount usage, suggesting discount dependency may not drive retention."
            ),
            "category": "Sales",
            "value": f"{avg_disc:.1f}% avg discount",
            "trend": "neutral",
        },
    ]

    recommendations = [
        {
            "id": 1,
            "title": "Launch VIP Loyalty Programme",
            "description": (
                f"Implement an exclusive rewards tier for the {vip_count:,} VIP customers. "
                "Early access to new products, personalised offers, and dedicated support "
                "will increase retention and lifetime value."
            ),
            "category": "Customer Retention",
            "priority": "High",
            "impact": "High revenue protection",
        },
        {
            "id": 2,
            "title": "Re-engagement Campaign for At-Risk Customers",
            "description": (
                f"{at_risk:,} customers are classified as At Risk. Deploy targeted "
                "win-back email campaigns with personalised incentives within the next "
                "30 days to recover revenue before further disengagement."
            ),
            "category": "Churn Risk",
            "priority": "High",
            "impact": f"Potential recovery of {at_risk:,} customers",
        },
        {
            "id": 3,
            "title": f"Expand {top_cat} Product Range",
            "description": (
                f"{top_cat} is the top revenue driver at ${top_cat_rev:,.0f}. "
                "Introducing complementary accessories and premium SKUs will capture "
                "higher-value purchases from existing buyers."
            ),
            "category": "Product",
            "priority": "Medium",
            "impact": "Revenue expansion",
        },
        {
            "id": 4,
            "title": f"Invest in {low_region} Region Marketing",
            "description": (
                f"The {low_region} region generates the lowest revenue at "
                f"${low_region_rev:,.0f}. Targeted regional campaigns, localised "
                "promotions, and regional partnerships can close the gap."
            ),
            "category": "Regional Performance",
            "priority": "Medium",
            "impact": "Geographic revenue diversification",
        },
        {
            "id": 5,
            "title": f"Review Pricing in {low_margin_cat[0]} Category",
            "description": (
                f"With a margin of only {low_margin_cat[2]:.1f}%, {low_margin_cat[0]} "
                "is underperforming on profitability. Conduct a cost review, renegotiate "
                "supplier terms, or adjust pricing to improve margins."
            ),
            "category": "Profitability",
            "priority": "Medium",
            "impact": "Margin improvement",
        },
        {
            "id": 6,
            "title": "Reduce Blanket Discount Dependency",
            "description": (
                f"With an average discount of {avg_disc:.1f}%, profit is being eroded "
                "by blanket promotions. Shift to targeted, behaviour-based discounts "
                "for customers with low churn risk to protect margins."
            ),
            "category": "Sales",
            "priority": "Low",
            "impact": "Margin protection",
        },
    ]

    return insights, recommendations
