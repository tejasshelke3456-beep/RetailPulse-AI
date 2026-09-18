"""
RetailPulse AI - Data Preprocessing & Derived Fields
"""
import pandas as pd
import numpy as np


def load_and_clean(customers_df, products_df, orders_df):
    """Clean raw CSVs and return validated DataFrames."""
    # -- Customers ----------------------------------------------------------
    c = customers_df.copy()
    c.drop_duplicates(subset="customer_id", keep="first", inplace=True)
    c["signup_date"] = pd.to_datetime(c["signup_date"], errors="coerce")
    c.dropna(subset=["customer_id", "signup_date"], inplace=True)
    c["age"] = pd.to_numeric(c["age"], errors="coerce").fillna(30).astype(int)
    c["age"] = c["age"].clip(18, 100)
    c["region"] = c["region"].fillna("Unknown")
    c["gender"] = c["gender"].fillna("Unknown")

    # -- Products -----------------------------------------------------------
    p = products_df.copy()
    p.drop_duplicates(subset="product_id", keep="first", inplace=True)
    p["unit_price"] = pd.to_numeric(p["unit_price"], errors="coerce")
    p["cost"]       = pd.to_numeric(p["cost"], errors="coerce")
    p.dropna(subset=["product_id", "unit_price", "cost"], inplace=True)
    p = p[p["unit_price"] > 0]
    p = p[p["cost"] >= 0]

    # -- Orders -------------------------------------------------------------
    o = orders_df.copy()
    o.drop_duplicates(subset="order_id", keep="first", inplace=True)
    o["order_date"]    = pd.to_datetime(o["order_date"], errors="coerce")
    o["quantity"]      = pd.to_numeric(o["quantity"], errors="coerce")
    o["discount"]      = pd.to_numeric(o["discount"], errors="coerce")
    o["shipping_cost"] = pd.to_numeric(o["shipping_cost"], errors="coerce")
    o.dropna(subset=["order_id", "customer_id", "product_id", "order_date"], inplace=True)
    o = o[o["quantity"] > 0]
    o["discount"]      = o["discount"].clip(0, 1).fillna(0)
    o["shipping_cost"] = o["shipping_cost"].clip(0).fillna(0)

    # Foreign key validation
    valid_customers = set(c["customer_id"])
    valid_products  = set(p["product_id"])
    o = o[o["customer_id"].isin(valid_customers)]
    o = o[o["product_id"].isin(valid_products)]

    return c, p, o


def build_master(orders_df, customers_df, products_df):
    """Join and compute all derived financial fields."""
    master = orders_df.merge(products_df[["product_id", "category", "unit_price", "cost"]],
                             on="product_id", how="left")
    master = master.merge(customers_df[["customer_id", "region", "age", "gender"]],
                          on="customer_id", how="left")

    # -- Derived financial fields --------------------------------------------
    master["gross_amount"]    = master["quantity"] * master["unit_price"]
    master["discount_amount"] = master["gross_amount"] * master["discount"]
    master["net_revenue"]     = master["gross_amount"] - master["discount_amount"]
    master["cost_amount"]     = master["quantity"] * master["cost"]
    master["profit"]          = master["net_revenue"] - master["cost_amount"] - master["shipping_cost"]
    # Safe profit margin
    master["profit_margin"]   = np.where(
        master["net_revenue"] > 0,
        master["profit"] / master["net_revenue"] * 100,
        0.0
    )

    # -- Time fields --------------------------------------------------------
    master["month"]      = master["order_date"].dt.month
    master["year"]       = master["order_date"].dt.year
    master["quarter"]    = master["order_date"].dt.quarter
    master["year_month"] = master["order_date"].dt.to_period("M").astype(str)

    return master
