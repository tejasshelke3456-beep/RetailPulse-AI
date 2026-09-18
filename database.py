"""
RetailPulse AI - Database Builder
Creates SQLite tables and loads cleaned data + customer_features (RFM).
"""
import os
import sqlite3
import pandas as pd
import numpy as np
import sys

# Ensure project root on path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from utils.preprocessing import load_and_clean, build_master

DB_PATH   = os.path.join(BASE_DIR, "data", "ecommerce.db")
DATA_DIR  = os.path.join(BASE_DIR, "data")

CHURN_CUTOFF  = pd.Timestamp("2025-09-01")
CHURN_OBS_END = pd.Timestamp("2025-11-30")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def build_database():
    print("-- Loading CSVs …")
    customers_raw = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
    products_raw  = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
    orders_raw    = pd.read_csv(os.path.join(DATA_DIR, "orders.csv"))

    print("-- Cleaning data …")
    customers, products, orders_clean = load_and_clean(customers_raw, products_raw, orders_raw)
    master = build_master(orders_clean, customers, products)

    print("-- Creating database …")
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.executescript("""
        PRAGMA foreign_keys = OFF;
        DROP TABLE IF EXISTS customer_features;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;
        PRAGMA foreign_keys = ON;
    """)

    # customers table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            signup_date TEXT,
            region      TEXT,
            age         INTEGER,
            gender      TEXT
        )
    """)
    customers[["customer_id","signup_date","region","age","gender"]].to_sql(
        "customers", conn, if_exists="append", index=False
    )

    # products table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id   TEXT PRIMARY KEY,
            product_name TEXT,
            category     TEXT,
            unit_price   REAL,
            cost         REAL
        )
    """)
    products[["product_id","product_name","category","unit_price","cost"]].to_sql(
        "products", conn, if_exists="append", index=False
    )

    # orders table (with derived fields)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id       TEXT PRIMARY KEY,
            customer_id    TEXT,
            product_id     TEXT,
            quantity       INTEGER,
            order_date     TEXT,
            discount       REAL,
            shipping_cost  REAL,
            gross_amount   REAL,
            discount_amount REAL,
            net_revenue    REAL,
            cost_amount    REAL,
            profit         REAL,
            profit_margin  REAL,
            category       TEXT,
            unit_price     REAL,
            month          INTEGER,
            year           INTEGER,
            quarter        INTEGER,
            year_month     TEXT
        )
    """)
    order_cols = [
        "order_id","customer_id","product_id","quantity","order_date",
        "discount","shipping_cost","gross_amount","discount_amount",
        "net_revenue","cost_amount","profit","profit_margin","category",
        "unit_price","month","year","quarter","year_month"
    ]
    master[order_cols].to_sql("orders", conn, if_exists="append", index=False)

    # -- RFM Analysis --------------------------------------------------------
    print("-- Computing RFM …")
    reference_date = CHURN_OBS_END + pd.Timedelta(days=1)   # 2025-12-01
    master["order_date"] = pd.to_datetime(master["order_date"])

    # Historical features: orders up to CHURN_CUTOFF
    hist = master[master["order_date"] <= CHURN_CUTOFF]

    rfm = hist.groupby("customer_id").agg(
        last_purchase        = ("order_date", "max"),
        historical_frequency = ("order_id",   "nunique"),
        historical_monetary  = ("net_revenue", "sum"),
        total_items          = ("quantity",    "sum"),
        average_order_value  = ("net_revenue", "mean"),
        average_discount     = ("discount",    "mean"),
        total_profit         = ("profit",      "sum"),
    ).reset_index()

    rfm["historical_recency"] = (reference_date - rfm["last_purchase"]).dt.days

    # Churn label: no purchase in future window
    future = master[
        (master["order_date"] > CHURN_CUTOFF) &
        (master["order_date"] <= CHURN_OBS_END)
    ]
    active_future = set(future["customer_id"].unique())
    rfm["is_churned"] = rfm["customer_id"].apply(lambda x: 0 if x in active_future else 1)

    # Customers with ZERO historical orders -> unknown, drop from features
    # (customers who signed up after cutoff won't have hist rows)
    all_cust = set(customers["customer_id"])
    missing  = all_cust - set(rfm["customer_id"])
    if missing:
        fill = pd.DataFrame({"customer_id": list(missing)})
        fill["last_purchase"]        = pd.NaT
        fill["historical_frequency"] = 0
        fill["historical_monetary"]  = 0.0
        fill["total_items"]          = 0
        fill["average_order_value"]  = 0.0
        fill["average_discount"]     = 0.0
        fill["total_profit"]         = 0.0
        fill["historical_recency"]   = 999
        fill["is_churned"]           = 1
        rfm = pd.concat([rfm, fill], ignore_index=True)

    # RFM scores (1–5, higher=better)
    def score_col(series, ascending=True):
        """Bin into quintiles; ascending=True -> higher value = higher score."""
        try:
            if ascending:
                return pd.qcut(series.rank(method="first"), 5,
                               labels=[1,2,3,4,5]).astype(int)
            else:
                return pd.qcut(series.rank(method="first"), 5,
                               labels=[5,4,3,2,1]).astype(int)
        except Exception:
            return pd.Series([3]*len(series), index=series.index)

    valid_rfm = rfm[rfm["historical_frequency"] > 0].copy()

    valid_rfm["r_score"] = score_col(valid_rfm["historical_recency"],  ascending=False)
    valid_rfm["f_score"] = score_col(valid_rfm["historical_frequency"], ascending=True)
    valid_rfm["m_score"] = score_col(valid_rfm["historical_monetary"],  ascending=True)
    valid_rfm["rfm_score"] = valid_rfm["r_score"] + valid_rfm["f_score"] + valid_rfm["m_score"]

    # Segment assignment
    def assign_segment(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        score   = row["rfm_score"]
        if score >= 13:
            return "VIP"
        elif score >= 10:
            return "Loyal"
        elif f >= 3 and r >= 3:
            return "Potential Loyalist"
        elif r <= 2:
            return "Hibernating"
        else:
            return "At Risk"

    valid_rfm["segment"] = valid_rfm.apply(assign_segment, axis=1)

    # For customers with zero orders, assign defaults
    zero_rfm = rfm[rfm["historical_frequency"] == 0].copy()
    zero_rfm["r_score"]   = 1
    zero_rfm["f_score"]   = 1
    zero_rfm["m_score"]   = 1
    zero_rfm["rfm_score"] = 3
    zero_rfm["segment"]   = "Hibernating"

    rfm_full = pd.concat([valid_rfm, zero_rfm], ignore_index=True)

    # Merge with customer demographics
    rfm_full = rfm_full.merge(
        customers[["customer_id","region","age","gender"]],
        on="customer_id", how="left"
    )

    # Also compute full-period revenue/orders for display
    full_agg = master.groupby("customer_id").agg(
        total_revenue = ("net_revenue", "sum"),
        total_orders  = ("order_id",    "nunique"),
    ).reset_index()
    rfm_full = rfm_full.merge(full_agg, on="customer_id", how="left")
    rfm_full["total_revenue"] = rfm_full["total_revenue"].fillna(0)
    rfm_full["total_orders"]  = rfm_full["total_orders"].fillna(0).astype(int)

    # customer_features table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customer_features (
            customer_id          TEXT PRIMARY KEY,
            historical_recency   REAL,
            historical_frequency INTEGER,
            historical_monetary  REAL,
            total_items          INTEGER,
            average_order_value  REAL,
            average_discount     REAL,
            total_profit         REAL,
            r_score              INTEGER,
            f_score              INTEGER,
            m_score              INTEGER,
            rfm_score            INTEGER,
            segment              TEXT,
            is_churned           INTEGER,
            region               TEXT,
            age                  INTEGER,
            gender               TEXT,
            total_revenue        REAL,
            total_orders         INTEGER
        )
    """)
    feat_cols = [
        "customer_id","historical_recency","historical_frequency","historical_monetary",
        "total_items","average_order_value","average_discount","total_profit",
        "r_score","f_score","m_score","rfm_score","segment","is_churned",
        "region","age","gender","total_revenue","total_orders"
    ]
    rfm_full[feat_cols].to_sql("customer_features", conn, if_exists="append", index=False)

    conn.commit()
    conn.close()

    churn_pct = rfm_full["is_churned"].mean() * 100
    print(f"-- customer_features -> {len(rfm_full):,} rows  |  churn rate {churn_pct:.2f}%")
    print(f"-- Database saved to {DB_PATH}")
    print("Database build complete [OK]")


if __name__ == "__main__":
    build_database()
