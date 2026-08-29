"""
RecoverAI — Safe Database Auto-Initialization & Environment Verification
========================================================================
Ensures database tables exist, seeds synthetic demo data idempotently if empty,
and verifies required ML artifacts before application startup.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import Base, SessionLocal, engine
import backend.models  # noqa: F401 — register all ORM models

logger = logging.getLogger("recoverai.init_db")


REQUIRED_ML_ARTIFACTS: List[str] = [
    "model.joblib",
    "preprocessor.joblib",
    "shap_explainer.joblib",
    "feature_columns.json",
    "model_metadata.json",
    "evaluation_report.json",
]


def verify_ml_artifacts() -> Dict[str, bool]:
    """
    Verifies that all trained ML and explainability artifacts are present on disk.
    Returns a dictionary mapping filename to existence status.
    """
    artifacts_dir = settings.project_root / "ml" / "artifacts"
    status: Dict[str, bool] = {}
    for filename in REQUIRED_ML_ARTIFACTS:
        exists = (artifacts_dir / filename).exists()
        status[filename] = exists
        if not exists:
            logger.warning("ML artifact missing: %s", artifacts_dir / filename)

    all_present = all(status.values())
    if all_present:
        logger.info("All %d required ML artifacts successfully verified.", len(REQUIRED_ML_ARTIFACTS))
    else:
        logger.warning("Some ML artifacts are missing. ML prediction endpoints may fail.")
    return status


def initialize_database() -> Tuple[int, int]:
    """
    Safely and idempotently initializes the database:
    1. Creates all database tables if they do not exist.
    2. Checks if the database is already seeded (count > 0).
    3. If empty, seeds synthetic demo records (5,000 customers, 50,000 payments).
    4. Verifies required ML artifacts.

    Returns (customer_count, payment_count).
    """
    logger.info("Verifying database schema...")
    Base.metadata.create_all(bind=engine)

    session: Session = SessionLocal()
    try:
        from backend.models.customer import Customer
        from backend.models.payment import Payment

        cust_count = session.query(Customer).count()
        pmt_count = session.query(Payment).count()

        if cust_count > 0 and pmt_count > 0:
            logger.info(
                "Database already populated: %d customers, %d payments. Skipping seeding.",
                cust_count,
                pmt_count,
            )
            verify_ml_artifacts()
            return cust_count, pmt_count

        logger.info("Empty or partial database detected (customers=%d, payments=%d). Seeding...", cust_count, pmt_count)

        # Check for pre-generated synthetic CSVs
        synthetic_dir = settings.project_root / "data" / "synthetic"
        cust_csv = synthetic_dir / "customers.csv"
        pay_csv = synthetic_dir / "payments.csv"

        if cust_csv.exists() and pay_csv.exists():
            logger.info("Loading seed data from existing CSVs in %s...", synthetic_dir)
            cust_df = pd.read_csv(cust_csv)
            pay_df = pd.read_csv(pay_csv)
        else:
            logger.info("Synthetic CSVs not found on disk. Generating deterministic synthetic dataset...")
            from ml.data_generator import GenerationConfig, SyntheticDataGenerator

            config = GenerationConfig(
                seed=settings.data_seed,
                num_customers=settings.num_customers,
                num_payments=settings.num_payments,
            )
            gen = SyntheticDataGenerator(config)
            cust_df, pay_df = gen.generate()

            # Attempt to persist generated CSVs if directory writable
            try:
                synthetic_dir.mkdir(parents=True, exist_ok=True)
                cust_df.to_csv(cust_csv, index=False)
                pay_df.to_csv(pay_csv, index=False)
                logger.info("Saved generated CSVs to %s", synthetic_dir)
            except Exception as e:
                logger.warning("Could not persist synthetic CSVs to disk: %s", e)

        # Normalize column names to match ORM models
        if "customer_id" in cust_df.columns:
            cust_df = cust_df.rename(columns={"customer_id": "id"})
        if "payment_id" in pay_df.columns:
            pay_df = pay_df.rename(columns={"payment_id": "id"})

        # Insert customers if needed
        if cust_count == 0:
            logger.info("Inserting %d customer records...", len(cust_df))
            cust_df.to_sql("customers", engine, if_exists="append", index=False)

        # Insert payments if needed
        if pmt_count == 0:
            logger.info("Inserting %d payment records...", len(pay_df))
            pay_df.to_sql("payments", engine, if_exists="append", index=False)

        session.commit()

        final_cust = session.query(Customer).count()
        final_pmt = session.query(Payment).count()
        logger.info("Database seeding complete: %d customers, %d payments.", final_cust, final_pmt)

        verify_ml_artifacts()
        return final_cust, final_pmt

    except Exception as e:
        session.rollback()
        logger.error("Database initialization encountered an error: %s", e, exc_info=True)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    c, p = initialize_database()
    print(f"Database ready: {c:,} customers, {p:,} payments.")
