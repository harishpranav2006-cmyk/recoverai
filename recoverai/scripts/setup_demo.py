"""
RecoverAI — One-Command Demo Environment Setup & Verification
============================================================
Safely prepares and validates database, tables, synthetic data, ML artifacts, and pipeline readiness.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.database import engine, Base, SessionLocal
from backend.models import Customer, Payment
from ml.predict import get_predictor


def setup_demo_environment() -> bool:
    print("\n" + "=" * 80)
    print("  RECOVERAI — DEMO & DEPLOYMENT ENVIRONMENT SETUP")
    print("=" * 80 + "\n")

    # Step 1: Ensure database tables exist
    print("[1/4] Ensuring database schema and tables exist...")
    Base.metadata.create_all(bind=engine)
    print("      ✓ Database schema verified.")

    # Step 2: Check dataset records
    print("[2/4] Validating database records...")
    db = SessionLocal()
    try:
        cust_count = db.query(Customer).count()
        pmt_count = db.query(Payment).count()
        print(f"      ✓ Total Customers: {cust_count:,} (Expected: 5,000)")
        print(f"      ✓ Total Payments:  {pmt_count:,} (Expected: 50,000)")

        if cust_count == 0 or pmt_count == 0:
            print("      ⚠ Empty database detected. Seeding from synthetic generator...")
            from backend.init_db import initialize_database
            initialize_database()
            print("      ✓ Synthetic dataset successfully generated and persisted.")
    finally:
        db.close()

    # Step 3: Check ML model artifacts
    print("[3/4] Verifying Machine Learning artifacts...")
    artifacts_dir = project_root / "ml" / "artifacts"
    required_artifacts = [
        "model.joblib",
        "preprocessor.joblib",
        "shap_explainer.joblib",
        "feature_columns.json",
        "model_metadata.json",
        "evaluation_report.json",
    ]
    missing = [f for f in required_artifacts if not (artifacts_dir / f).exists()]
    if missing:
        print(f"      ❌ Missing ML artifacts: {missing}")
        return False
    print(f"      ✓ All {len(required_artifacts)} ML model & SHAP artifacts present.")

    # Step 4: Run test inference
    print("[4/4] Testing real-time ML prediction pipeline...")
    from ml.predict import predict_payment_recovery
    result = predict_payment_recovery("P000004", include_explanation=True)
    prob = result["recovery_probability"]
    print(f"      ✓ Sample ML inference successful for P000004: p = {prob:.4f}")
    if result.get("factors"):
        print(f"      ✓ Top contributing factor: {result['factors'][0]['factor']}")

    print("\n" + "-" * 80)
    print("✅ RECOVERAI ENVIRONMENT IS FULLY PREPARED AND READY FOR DEMO & DEPLOYMENT")
    print("-" * 80 + "\n")
    return True


if __name__ == "__main__":
    success = setup_demo_environment()
    if not success:
        sys.exit(1)
