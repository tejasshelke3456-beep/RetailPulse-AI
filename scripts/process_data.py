"""
RetailPulse AI - process_data.py
One-shot script: generate dataset -> build DB -> train ML model.
Run once before starting the Flask app.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Step 1: Generate dataset
print("=" * 55)
print("STEP 1: Generating synthetic dataset …")
print("=" * 55)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "generate_dataset",
    os.path.join(BASE_DIR, "data", "generate_dataset.py")
)
gen_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_mod)

# Step 2: Build database + RFM
print("\n" + "=" * 55)
print("STEP 2: Building database + RFM analysis …")
print("=" * 55)
from database import build_database
build_database()

# Step 3: Train ML model
print("\n" + "=" * 55)
print("STEP 3: Training churn prediction models …")
print("=" * 55)
from ml.train_model import train
train()

print("\n" + "=" * 55)
print("[OK] All processing complete. Run: python app.py")
print("=" * 55)
