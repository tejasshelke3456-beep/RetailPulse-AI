# RetailPulse AI

## An Intelligent E-Commerce Sales, Customer Behavior, and Predictive Analytics Dashboard

---

## Project Overview

RetailPulse AI is a full-stack Business Intelligence and Machine Learning web application that transforms raw e-commerce transaction data into actionable insights. It implements a complete end-to-end analytics pipeline:

```
Data → Cleaning → Database → RFM Analysis → ML Prediction → Business Insights → Recommendations → Executive Dashboard
```

---

## Problem Statement

E-commerce businesses generate massive volumes of transactional data but often lack the tools to:
- Identify customers at risk of churning before revenue is lost
- Understand which customer segments drive the most value
- Prioritize marketing spend on the right segments
- Convert raw data into actionable business intelligence

---

## Objectives

1. Build a realistic synthetic e-commerce dataset (5,000 customers, 24,892 orders)
2. Implement RFM (Recency, Frequency, Monetary) customer segmentation
3. Train a leakage-free churn prediction model using Random Forest
4. Expose all analytics via a REST API (13 endpoints)
5. Deliver a responsive, professional analytics dashboard

---

## Features

- **Executive KPI Dashboard** — Revenue, Profit, Churn Rate, Retention Rate, AOV
- **Sales & Products Analytics** — Category performance, monthly trends, top products
- **Customer RFM Segmentation** — VIP, Loyal, Potential Loyalist, At Risk, Hibernating
- **Customer Search** — Real-time lookup by Customer ID
- **Risk & Opportunities** — 6 data-driven insights, 6 prioritized recommendations
- **AI Churn Prediction** — Random Forest model with real-time inference
- **Responsive Design** — Desktop and mobile-friendly Tailwind CSS UI

---

## Architecture

```
RetailPulse-AI/
├── app.py              # Flask application (13 REST endpoints + 5 page routes)
├── database.py         # SQLite DB builder + RFM analysis
├── requirements.txt
├── README.md
├── .env.example
│
├── data/
│   ├── generate_dataset.py   # Synthetic dataset generator
│   ├── customers.csv         # 5,000 customers
│   ├── products.csv          # 50 products
│   ├── orders.csv            # 24,892 orders
│   └── ecommerce.db          # SQLite database
│
├── ml/
│   ├── train_model.py        # Model training (LR + RF)
│   ├── predict_churn.py      # Reusable prediction module
│   └── churn_model.pkl       # Serialized Random Forest model
│
├── scripts/
│   ├── process_data.py       # One-shot bootstrap pipeline
│   ├── test_integration.py   # Integration test suite
│   └── test_insights.py      # Insights/recommendations test suite
│
├── utils/
│   ├── preprocessing.py      # Data cleaning & feature engineering
│   └── insights.py           # Dynamic insights & recommendations engine
│
├── templates/
│   ├── base.html             # Shared layout (sidebar, navbar)
│   ├── index.html            # Executive overview
│   ├── sales.html            # Sales & products
│   ├── customers.html        # Customer analytics
│   ├── risk.html             # Risk & opportunities
│   └── prediction.html       # AI churn prediction
│
└── static/
    ├── css/
    └── js/
        ├── dashboard.js      # Overview page logic
        ├── sales.js          # Sales page logic
        ├── customers.js      # Customers page logic
        ├── risk.js           # Risk page logic
        └── prediction.js     # Prediction page logic
```

---

## Technology Stack

| Layer        | Technology                              |
|--------------|-----------------------------------------|
| Backend      | Python 3, Flask                         |
| Data         | Pandas, NumPy                           |
| ML           | Scikit-learn, joblib                    |
| Database     | SQLite (via Python sqlite3)             |
| Frontend     | HTML5, Tailwind CSS (CDN), Vanilla JS   |
| Charts       | Chart.js                                |
| Icons        | Font Awesome                            |

---

## Dataset

| Metric            | Value                      |
|-------------------|----------------------------|
| Customers         | 5,000                      |
| Products          | 50                         |
| Orders            | 24,892                     |
| Period            | Jan 1, 2024 – Nov 30, 2025 |
| Categories        | 5 (Electronics, Clothing, Home & Kitchen, Books, Sports & Fitness) |
| Total Revenue     | ~$7.76M                    |

### Churn Design
- **Churned customers (37.52%)**: Only purchased in the first 12 months (2024) — high recency (inactive long before cutoff), low frequency
- **Retained customers (62.48%)**: Active throughout the full period including post-cutoff (Sep–Nov 2025)
- Historical feature cutoff: **2025-09-01**
- Future observation window: **2025-09-02 to 2025-11-30**

---

## RFM Methodology

| Metric    | Definition                                      | Score (1–5) |
|-----------|-------------------------------------------------|-------------|
| Recency   | Days since last purchase (lower = better)       | 5 = most recent |
| Frequency | Number of distinct orders (higher = better)     | 5 = most frequent |
| Monetary  | Total net revenue (higher = better)             | 5 = highest spend |

### Customer Segments

| Segment            | RFM Criteria                          |
|--------------------|---------------------------------------|
| VIP                | RFM Score ≥ 13                        |
| Loyal              | RFM Score 10–12                       |
| Potential Loyalist | F ≥ 3 and R ≥ 3                       |
| At Risk            | Other                                 |
| Hibernating        | R ≤ 2 or zero orders                  |

---

## ML Methodology

### Churn Definition
A customer is classified as **churned (is_churned = 1)** if they made **zero purchases** in the future observation window (2025-09-02 to 2025-11-30).

### Features Used (No Leakage)
All features derived exclusively from data on or before 2025-09-01:
- `historical_recency` — days since last purchase
- `historical_frequency` — number of orders
- `historical_monetary` — total spend
- `total_items` — total units purchased
- `average_order_value`
- `average_discount`
- `age`, `region` (encoded), `gender` (encoded)

### NOT Used (Leakage Prevention)
- Future orders, future revenue, future churn information
- Raw customer IDs, signup dates directly

---

## Model Results

| Model               | F1-Score | ROC-AUC |
|---------------------|----------|---------|
| Logistic Regression | 0.9576   | 0.9914  |
| Random Forest       | 0.9703   | 0.9919  |

**Production model: Random Forest** (higher F1 and AUC)

### Risk Level Definitions
| Level  | Churn Probability | Action |
|--------|-------------------|--------|
| High   | ≥ 70%             | Immediate win-back campaign |
| Medium | 40–70%            | Re-engagement strategy |
| Low    | < 40%             | Standard retention |

---

## API Reference

| # | Method | Endpoint                      | Description                    |
|---|--------|-------------------------------|--------------------------------|
| 1 | GET    | `/api/health`                 | System health check            |
| 2 | GET    | `/api/kpis`                   | 8 key performance indicators   |
| 3 | GET    | `/api/sales-trend`            | Monthly revenue & profit trend |
| 4 | GET    | `/api/category-performance`   | Revenue by product category    |
| 5 | GET    | `/api/top-products`           | Top 10 products by revenue     |
| 6 | GET    | `/api/customer-segments`      | RFM customer segment summary   |
| 7 | GET    | `/api/regional-performance`   | Revenue by geographic region   |
| 8 | GET    | `/api/risk-analysis`          | Churn & segment risk data      |
| 9 | GET    | `/api/opportunities`          | 6 prioritized recommendations  |
|10 | GET    | `/api/customer/<id>`          | Individual customer lookup     |
|11 | GET    | `/api/insights`               | 6 data-driven business insights|
|12 | GET    | `/api/churn-summary`          | Portfolio churn overview       |
|13 | POST   | `/api/predict-churn`          | Real-time churn prediction     |

---


---

## Installation

### Prerequisites
- Python 3.9+
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/retailpulse-ai.git
cd retailpulse-ai

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application (auto-bootstraps on first run)
python app.py
```

The app auto-generates the dataset, builds the database, and trains the model on first launch.

---

## Run Instructions

```bash
python app.py
```

Open your browser at: **http://127.0.0.1:5000/**

### Manual Bootstrap (optional)
```bash
python scripts/process_data.py
python app.py
```

---

## Testing

```bash
# Integration tests (21 tests)
python -m unittest scripts/test_integration.py -v

# Insights tests (14 tests)
python -m unittest scripts/test_insights.py -v

# Compilation check
python -m compileall .
```

---

## Project Structure

See [Architecture](#architecture) section above.

---

## Limitations

1. Uses a synthetic dataset — patterns may not reflect real e-commerce behavior
2. Churn prediction is based on a defined observation window, not real-time behavioral scoring
3. No authentication/authorization on API endpoints
4. SQLite is not suitable for production-scale data; a production deployment should use PostgreSQL
5. Model performance may vary on real datasets without retraining

---

## Future Scope

1. Real-time streaming data integration (Apache Kafka)
2. Deep learning churn models (LSTM for purchase sequences)
3. A/B testing framework for recommendation effectiveness
4. Email/notification alerts for high-risk customers
5. Role-based access control (RBAC)
6. PostgreSQL migration for scalability
7. Automated model retraining pipeline

---

## Author

**TEJAS KIRAN SHELKE**  
PRN: 2125PCAM1034

---

*RetailPulse AI v1.0 — Built as an internship project demonstrating full-stack BI + ML engineering.*
