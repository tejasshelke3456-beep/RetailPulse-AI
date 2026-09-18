"""
RetailPulse AI - Integration Test Suite
Tests all frontend routes and core APIs.
Run: python -m unittest scripts/test_integration.py -v
"""
import os
import sys
import json
import unittest
import threading
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Ensure DB + model exist before starting
DB_PATH    = os.path.join(BASE_DIR, "data", "ecommerce.db")
MODEL_PATH = os.path.join(BASE_DIR, "ml",   "churn_model.pkl")
if not os.path.exists(DB_PATH) or not os.path.exists(MODEL_PATH):
    print("Database or model missing - running bootstrap ...")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "generate_dataset",
        os.path.join(BASE_DIR, "data", "generate_dataset.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    from database import build_database
    build_database()
    from ml.train_model import train
    train()

import app as flask_app

flask_app.app.config["TESTING"] = True
CLIENT = flask_app.app.test_client()


class Test1FrontendRoutes(unittest.TestCase):
    """Test 1 – All 5 frontend routes return HTTP 200."""

    def _check(self, path):
        resp = CLIENT.get(path)
        self.assertEqual(resp.status_code, 200,
                         f"Route {path} returned {resp.status_code}")
        html = resp.data.decode("utf-8", errors="replace")
        # No raw Jinja or Markdown leakage
        self.assertNotIn("{{", html, f"Raw Jinja in {path}")
        self.assertNotIn("{%", html, f"Raw Jinja in {path}")
        self.assertNotIn("```", html, f"Markdown code fence in {path}")

    def test_index(self):       self._check("/")
    def test_sales(self):       self._check("/sales")
    def test_customers(self):   self._check("/customers")
    def test_risk(self):        self._check("/risk")
    def test_prediction(self):  self._check("/prediction")


class Test2CoreAPIs(unittest.TestCase):
    """Test 2 – Core APIs return valid JSON."""

    def _json(self, path):
        resp = CLIENT.get(path)
        self.assertEqual(resp.status_code, 200, f"API {path} returned {resp.status_code}")
        data = json.loads(resp.data)
        self.assertIsNotNone(data)
        return data

    def test_health(self):
        d = self._json("/api/health")
        self.assertIn("status", d)

    def test_kpis(self):
        d = self._json("/api/kpis")
        for k in ("total_revenue","total_profit","churn_rate","retention_rate"):
            self.assertIn(k, d)

    def test_sales_trend(self):
        d = self._json("/api/sales-trend")
        self.assertIsInstance(d, list)
        self.assertGreater(len(d), 0)

    def test_category_performance(self):
        d = self._json("/api/category-performance")
        self.assertIsInstance(d, list)
        self.assertGreater(len(d), 0)

    def test_top_products(self):
        d = self._json("/api/top-products")
        self.assertIsInstance(d, list)
        self.assertEqual(len(d), 10)

    def test_customer_segments(self):
        d = self._json("/api/customer-segments")
        self.assertIsInstance(d, list)
        self.assertGreater(len(d), 0)

    def test_regional_performance(self):
        d = self._json("/api/regional-performance")
        self.assertIsInstance(d, list)
        self.assertGreater(len(d), 0)

    def test_risk_analysis(self):
        d = self._json("/api/risk-analysis")
        self.assertIn("churn_summary", d)
        self.assertIn("segments", d)

    def test_insights(self):
        d = self._json("/api/insights")
        self.assertIsInstance(d, list)
        self.assertEqual(len(d), 6, f"Expected 6 insights, got {len(d)}")

    def test_opportunities(self):
        d = self._json("/api/opportunities")
        self.assertIsInstance(d, list)
        self.assertEqual(len(d), 6, f"Expected 6 recommendations, got {len(d)}")

    def test_churn_summary(self):
        d = self._json("/api/churn-summary")
        for k in ("total_customers","churned","retained","churn_rate"):
            self.assertIn(k, d)


class Test3CustomerLookup(unittest.TestCase):
    """Test 3 – Customer lookup: valid + invalid."""

    def test_valid_customer(self):
        resp = CLIENT.get("/api/customer/CUST-0001")
        self.assertEqual(resp.status_code, 200)
        d = json.loads(resp.data)
        self.assertEqual(d["customer_id"], "CUST-0001")

    def test_invalid_customer_returns_404(self):
        resp = CLIENT.get("/api/customer/CUST-99999")
        self.assertEqual(resp.status_code, 404)
        d = json.loads(resp.data)
        self.assertIn("error", d)


class Test4ChurnPrediction(unittest.TestCase):
    """Test 4 – Churn prediction endpoint."""

    VALID_PAYLOAD = {
        "historical_recency":   90,
        "historical_frequency": 5,
        "historical_monetary":  500,
        "total_items":          10,
        "average_order_value":  100,
        "average_discount":     0.1,
        "age":                  35,
        "region":               "North",
        "gender":               "Male",
    }

    def test_valid_prediction(self):
        resp = CLIENT.post(
            "/api/predict-churn",
            data=json.dumps(self.VALID_PAYLOAD),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        d = json.loads(resp.data)
        self.assertIn("churn_probability", d)
        self.assertIn("prediction", d)
        self.assertIn("risk_level", d)
        self.assertIn(d["risk_level"], ("High", "Medium", "Low"))
        self.assertGreaterEqual(d["churn_probability"], 0)
        self.assertLessEqual(d["churn_probability"], 1)

    def test_invalid_payload_missing_fields(self):
        resp = CLIENT.post(
            "/api/predict-churn",
            data=json.dumps({"age": 30}),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_payload_no_json(self):
        resp = CLIENT.post(
            "/api/predict-churn",
            data="not json",
            content_type="text/plain"
        )
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
