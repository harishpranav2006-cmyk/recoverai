#!/usr/bin/env python
"""
RecoverAI — Seed Database from Synthetic CSVs
==============================================
Reads generated CSVs and inserts records into the SQLite database.
Separate from data generation to keep concerns decoupled.

Usage:
    python scripts/seed_database.py
    python scripts/seed_database.py --data-dir data/synthetic --db sqlite:///./recoverai.db
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from rich.console import Console

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed RecoverAI database from synthetic CSVs")
    parser.add_argument("--data-dir", type=str, default=None, help="Directory containing CSVs")
    parser.add_argument("--db", type=str, default=None, help="Database URL override")
    args = parser.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else project_root / "data" / "synthetic"

    # Override database URL if provided
    if args.db:
        import os
        os.environ["DATABASE_URL"] = args.db

    # Import after potential env override
    from backend.config import Settings
    settings = Settings()
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.database import Base
    import backend.models  # noqa: F401 — registers all models

    console.print("[bold cyan]RecoverAI — Database Seeder[/bold cyan]")
    console.print(f"  Data dir: {data_dir}")
    console.print(f"  Database: {settings.database_url}")
    console.print()

    # Check CSVs exist
    cust_csv = data_dir / "customers.csv"
    pay_csv = data_dir / "payments.csv"

    if not cust_csv.exists():
        console.print(f"[red]ERROR:[/red] {cust_csv} not found. Run generate_data.py first.")
        sys.exit(1)
    if not pay_csv.exists():
        console.print(f"[red]ERROR:[/red] {pay_csv} not found. Run generate_data.py first.")
        sys.exit(1)

    # Create engine
    engine = create_engine(
        settings.database_url,
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    )

    # Drop and recreate tables
    console.print("  Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    console.print("  Creating tables...")
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Load CSVs
        cust_df = pd.read_csv(cust_csv)
        pay_df = pd.read_csv(pay_csv)

        # Map column names to ORM schemas (customer_id -> id, payment_id -> id)
        if "customer_id" in cust_df.columns:
            cust_df = cust_df.rename(columns={"customer_id": "id"})
        if "payment_id" in pay_df.columns:
            pay_df = pay_df.rename(columns={"payment_id": "id"})

        # Insert customers
        console.print(f"  Inserting {len(cust_df):,} customers...")
        cust_df.to_sql("customers", engine, if_exists="append", index=False)

        # Insert payments
        console.print(f"  Inserting {len(pay_df):,} payments...")
        pay_df.to_sql("payments", engine, if_exists="append", index=False)

        session.commit()
        console.print()
        console.print("[green]✓[/green] Database seeded successfully.")

        # Verify row counts
        from sqlalchemy import text
        for table in ["customers", "payments"]:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            console.print(f"  {table}: {count:,} rows")

    except Exception as e:
        session.rollback()
        console.print(f"[red]ERROR:[/red] {e}")
        sys.exit(1)
    finally:
        session.close()

    console.print()
    console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
    main()
