"""
RetailPulse AI - Synthetic Dataset Generator
Generates 5,000 customers, 50 products, ~24,892 order transactions
Dataset period: January 1, 2024 to November 30, 2025
Churned customers have clearly different RFM profiles for strong ML signal.
"""
import pandas as pd
import numpy as np
import os

SEED = 42
rng  = np.random.default_rng(SEED)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

CHURN_CUTOFF  = pd.Timestamp("2025-09-01")
OBS_END       = pd.Timestamp("2025-11-30")
ORDER_START   = pd.Timestamp("2024-01-01")
N_CUSTOMERS   = 5000
TARGET_ORDERS = 24892

# ── Products ──────────────────────────────────────────────────────────────
categories = {
    "Electronics":     [("Smartphone Pro",299.99,180), ("Laptop Ultra",899.99,540),
                        ("Wireless Earbuds",79.99,40),  ("Smart Watch",199.99,110),
                        ("Tablet HD",349.99,200),       ("Bluetooth Speaker",59.99,30),
                        ("USB-C Hub",29.99,12),          ("Gaming Mouse",49.99,22),
                        ("Mechanical Keyboard",89.99,45),("Webcam HD",69.99,35)],
    "Clothing":        [("Casual T-Shirt",19.99,8),    ("Denim Jeans",49.99,22),
                        ("Winter Jacket",89.99,42),     ("Summer Dress",39.99,18),
                        ("Running Shoes",79.99,38),     ("Sports Hoodie",44.99,20),
                        ("Formal Shirt",34.99,15),      ("Yoga Pants",29.99,13),
                        ("Sneakers Classic",64.99,30),  ("Polo Shirt",24.99,10)],
    "Home & Kitchen":  [("Coffee Maker",49.99,25),     ("Air Fryer",79.99,40),
                        ("Blender Pro",39.99,18),       ("Cookware Set",89.99,42),
                        ("Knife Set",44.99,20),         ("Cutting Board",14.99,6),
                        ("Dish Rack",19.99,8),          ("Storage Bins",24.99,10),
                        ("Towel Set",29.99,12),         ("Bedsheet Set",49.99,22)],
    "Books":           [("Python Programming",34.99,8), ("Data Science Guide",44.99,12),
                        ("Business Strategy",24.99,6),  ("Self Help Classic",14.99,4),
                        ("Fiction Bestseller",12.99,3), ("History & Culture",19.99,5),
                        ("Science Explained",29.99,7),  ("Cooking Mastery",22.99,6),
                        ("Financial Freedom",17.99,4),  ("Travel Memoir",15.99,4)],
    "Sports & Fitness":[("Yoga Mat",24.99,10),         ("Dumbbell Set",59.99,28),
                        ("Resistance Bands",14.99,6),   ("Jump Rope",9.99,4),
                        ("Protein Powder",39.99,18),    ("Water Bottle",19.99,8),
                        ("Fitness Tracker",99.99,50),   ("Foam Roller",24.99,10),
                        ("Pull-Up Bar",34.99,15),       ("Gym Bag",44.99,20)],
}

product_rows = []
pid = 1
for cat, items in categories.items():
    for name, price, cost in items:
        product_rows.append({"product_id":f"PROD-{pid:03d}", "product_name":name,
                              "category":cat, "unit_price":price, "cost":cost})
        pid += 1
products = pd.DataFrame(product_rows)
assert len(products) == 50

# ── Customers ─────────────────────────────────────────────────────────────
regions = ["North","South","East","West","Central"]
genders = ["Male","Female"]

# 37.52% churned → 1876 churned, 3124 retained
N_CHURNED  = 1876
N_RETAINED = N_CUSTOMERS - N_CHURNED

cust_ids = [f"CUST-{i:04d}" for i in range(1, N_CUSTOMERS + 1)]
churned_ids  = cust_ids[:N_CHURNED]
retained_ids = cust_ids[N_CHURNED:]

signup_base  = pd.date_range("2022-01-01", "2024-12-31", periods=N_CUSTOMERS)
signup_dates = (signup_base + pd.to_timedelta(rng.integers(0,30,N_CUSTOMERS), unit="D")).normalize()

customers = pd.DataFrame({
    "customer_id": cust_ids,
    "signup_date": signup_dates.strftime("%Y-%m-%d"),
    "region": rng.choice(regions, N_CUSTOMERS, p=[0.22,0.20,0.20,0.20,0.18]),
    "age":    np.clip(rng.normal(38,12,N_CUSTOMERS).astype(int), 18, 75),
    "gender": rng.choice(genders, N_CUSTOMERS, p=[0.52,0.48]),
})

# ── Order generation ──────────────────────────────────────────────────────
prod_ids     = products["product_id"].values
# Weight heavily towards Electronics (high unit prices) for retained customers
base_weights = rng.pareto(1.2, len(prod_ids)) + 1
base_weights /= base_weights.sum()
# Boost Electronics (first 10 products) in the product mix
electronics_boost = np.ones(len(prod_ids))
electronics_boost[:10] = 7.0  # Electronics products (indices 0-9)
prod_weights = base_weights * electronics_boost
prod_weights /= prod_weights.sum()

def seasonal_w(dates):
    w = np.array([1.0 + 0.5*np.sin((d.month-1)/11*np.pi) + (0.3 if d.month in (11,12) else 0) for d in dates])
    return w / w.sum()

dates_full   = pd.date_range(ORDER_START, CHURN_CUTOFF)
dates_future = pd.date_range(CHURN_CUTOFF + pd.Timedelta(days=1), OBS_END)
# Early period: churned customers' last activity concentrated in first 12 months
dates_early  = pd.date_range(ORDER_START, ORDER_START + pd.DateOffset(months=12))

w_full   = seasonal_w(dates_full)
w_early  = seasonal_w(dates_early)
w_future = seasonal_w(dates_future)

def build_customer_orders(cid, n, dates_pool, w_pool, high_value=False):
    """Build n order rows for one customer on given date pool."""
    if n <= 0:
        return []
    raw_dates = rng.choice(dates_pool, size=n, p=w_pool, replace=True)
    tsd = pd.to_datetime(raw_dates)
    prods = rng.choice(prod_ids, size=n, p=prod_weights)
    # High-value customers buy more quantities
    if high_value:
        qtys  = rng.choice([1,2,3,4,5,6,8,10], n, p=[0.20,0.20,0.20,0.15,0.10,0.07,0.05,0.03])
    else:
        qtys  = rng.choice([1,2,3,4,5], n, p=[0.50,0.25,0.12,0.08,0.05])
    discs = rng.choice([0.0,0.05,0.10,0.15,0.20,0.25], n, p=[0.35,0.20,0.20,0.12,0.08,0.05])
    ships = rng.choice([0.0,4.99,7.99,9.99,14.99], n, p=[0.20,0.30,0.25,0.15,0.10])
    rows = []
    for j in range(n):
        rows.append({
            "customer_id":  cid,
            "product_id":   prods[j],
            "quantity":     int(qtys[j]),
            "order_date":   tsd[j].strftime("%Y-%m-%d"),
            "discount":     round(float(discs[j]),2),
            "shipping_cost":round(float(ships[j]),2),
        })
    return rows

all_order_rows = []

# ── CHURNED customers: 1-3 orders, only on early dates (high recency = bad) ──
for cid in churned_ids:
    n = int(rng.choice([1,2,3], p=[0.50,0.35,0.15]))
    all_order_rows.extend(build_customer_orders(cid, n, dates_early, w_early))

# ── RETAINED customers: high-value, 4-15 orders, spread across full hist + future ──
for cid in retained_ids:
    n_hist   = int(rng.choice(range(3,16), p=[0.05,0.10,0.15,0.15,0.15,0.12,0.10,0.07,0.05,0.03,0.01,0.01,0.01]))
    n_future = int(rng.choice([1,2,3,4], p=[0.35,0.35,0.20,0.10]))
    all_order_rows.extend(build_customer_orders(cid, n_hist,   dates_full,   w_full,   high_value=True))
    all_order_rows.extend(build_customer_orders(cid, n_future, dates_future, w_future, high_value=True))

# Build DataFrame
orders_df = pd.DataFrame(all_order_rows)

# Count future orders (after cutoff) — must preserve them all
future_mask = pd.to_datetime(orders_df["order_date"]) > pd.Timestamp("2025-09-01")
future_orders = orders_df[future_mask].copy()
hist_orders   = orders_df[~future_mask].copy()

# Shuffle historical orders and trim to fill up to TARGET_ORDERS
n_future = len(future_orders)
n_hist_needed = TARGET_ORDERS - n_future

hist_orders = hist_orders.sample(frac=1, random_state=SEED).reset_index(drop=True)

# Pad if needed
while len(hist_orders) < n_hist_needed:
    shortage = n_hist_needed - len(hist_orders)
    hist_orders = pd.concat([hist_orders, hist_orders.tail(shortage).copy()], ignore_index=True)

hist_orders = hist_orders.head(n_hist_needed).copy()

orders_df = pd.concat([hist_orders, future_orders], ignore_index=True)
# Shuffle final DataFrame for realistic ordering
orders_df = orders_df.sample(frac=1, random_state=SEED+1).reset_index(drop=True)
orders_df["order_id"] = [f"ORD-{i:06d}" for i in range(1, len(orders_df) + 1)]
assert len(orders_df) == TARGET_ORDERS, f"Expected {TARGET_ORDERS}, got {len(orders_df)}"

# ── Validate ──────────────────────────────────────────────────────────────
assert customers["customer_id"].nunique() == N_CUSTOMERS
assert products["product_id"].nunique()   == 50
assert len(orders_df) == TARGET_ORDERS
assert orders_df["customer_id"].isin(customers["customer_id"]).all()
assert orders_df["product_id"].isin(products["product_id"]).all()
assert (orders_df["quantity"] > 0).all()
assert orders_df["discount"].between(0,1).all()

print(f"Customers : {N_CUSTOMERS:,}  (churned_group={N_CHURNED}, retained_group={N_RETAINED})")
print(f"Products  : {len(products):,}")
print(f"Orders    : {len(orders_df):,}")

# ── Save ──────────────────────────────────────────────────────────────────
customers.to_csv(os.path.join(DATA_DIR, "customers.csv"), index=False)
products.to_csv(os.path.join(DATA_DIR, "products.csv"), index=False)
orders_df.to_csv(os.path.join(DATA_DIR, "orders.csv"), index=False)

print("[OK] customers.csv  -> saved")
print("[OK] products.csv   -> saved")
print("[OK] orders.csv     -> saved")
print("Dataset validation passed.")
