"""
RetailPulse AI - Insights & Recommendations Test Suite
Validates the insights/recommendations logic.
Run: python -m unittest scripts/test_insights.py -v
"""
import os
import sys
import sqlite3
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from database import DB_PATH
from utils.insights import generate_insights


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class TestInsightsStructure(unittest.TestCase):
    """Test correct count, keys, and types of insights."""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(DB_PATH):
            raise unittest.SkipTest("Database not found – run scripts/process_data.py first")
        conn = _get_conn()
        cls.insights, cls.recs = generate_insights(conn)
        conn.close()

    def test_insights_count_is_6(self):
        self.assertEqual(len(self.insights), 6)

    def test_recs_count_is_6(self):
        self.assertEqual(len(self.recs), 6)

    def test_insight_has_required_keys(self):
        required = {"id", "title", "description", "category", "value", "trend"}
        for ins in self.insights:
            self.assertEqual(required, required & ins.keys(),
                             f"Insight missing keys: {required - ins.keys()}")

    def test_rec_has_required_keys(self):
        required = {"id", "title", "description", "category", "priority", "impact"}
        for rec in self.recs:
            self.assertEqual(required, required & rec.keys(),
                             f"Rec missing keys: {required - rec.keys()}")

    def test_insight_ids_unique(self):
        ids = [i["id"] for i in self.insights]
        self.assertEqual(len(ids), len(set(ids)))

    def test_rec_ids_unique(self):
        ids = [r["id"] for r in self.recs]
        self.assertEqual(len(ids), len(set(ids)))

    def test_insight_titles_non_empty(self):
        for ins in self.insights:
            self.assertTrue(len(ins["title"]) > 0)

    def test_rec_titles_non_empty(self):
        for rec in self.recs:
            self.assertTrue(len(rec["title"]) > 0)

    def test_insight_trends_valid(self):
        valid = {"up", "down", "neutral"}
        for ins in self.insights:
            self.assertIn(ins["trend"], valid)

    def test_rec_priorities_valid(self):
        valid = {"High", "Medium", "Low"}
        for rec in self.recs:
            self.assertIn(rec["priority"], valid)

    def test_insight_categories_non_empty(self):
        for ins in self.insights:
            self.assertTrue(len(ins["category"]) > 0)

    def test_rec_categories_non_empty(self):
        for rec in self.recs:
            self.assertTrue(len(rec["category"]) > 0)

    def test_insight_descriptions_meaningful(self):
        for ins in self.insights:
            self.assertGreater(len(ins["description"]), 20,
                               f"Description too short: {ins['description']}")

    def test_rec_descriptions_meaningful(self):
        for rec in self.recs:
            self.assertGreater(len(rec["description"]), 20,
                               f"Description too short: {rec['description']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
