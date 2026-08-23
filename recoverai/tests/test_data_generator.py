"""
Tests for the RecoverAI synthetic data generator.
Covers: shape, schema, validation rules, reproducibility, demo scenarios,
leakage prevention, and distribution sanity checks.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ml.data_generator import (
    SyntheticDataGenerator,
    GenerationConfig,
    FEATURE_COLUMNS,
    LEAKAGE_COLUMNS,
    TARGET_COLUMN,
    IDENTIFIER_COLUMNS,
)


# ─── Shape & Schema ──────────────────────────────────────────────────────────

class TestDatasetShape:
    """Verify dataset dimensions and required columns."""

    def test_payment_count_exact(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        assert pay is not None
        assert len(pay) == small_generator.config.num_payments

    def test_customer_count_exact(self, small_generator: SyntheticDataGenerator) -> None:
        cust = small_generator._customers_df
        assert cust is not None
        assert len(cust) == small_generator.config.num_customers

    def test_required_payment_columns_present(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        required = (
            IDENTIFIER_COLUMNS + FEATURE_COLUMNS +
            [TARGET_COLUMN] + LEAKAGE_COLUMNS +
            ["timestamp", "payment_success", "demo_scenario"]
        )
        # Remove duplicates
        required = list(set(required))
        for col in required:
            assert col in pay.columns, f"Missing column: {col}"

    def test_required_customer_columns_present(self, small_generator: SyntheticDataGenerator) -> None:
        cust = small_generator._customers_df
        for col in ["customer_id", "name", "email", "region", "segment", "created_at", "lifetime_value", "age_days"]:
            assert col in cust.columns, f"Missing column: {col}"


# ─── Validation Rules ────────────────────────────────────────────────────────

class TestValidationRules:
    """Verify all 8 validation rules pass."""

    def test_all_validations_pass(self, small_generator: SyntheticDataGenerator) -> None:
        results = small_generator.validate()
        for check, passed in results.items():
            assert passed, f"Validation failed: {check}"

    def test_no_duplicate_payment_ids(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        assert pay["payment_id"].is_unique

    def test_no_duplicate_customer_ids(self, small_generator: SyntheticDataGenerator) -> None:
        cust = small_generator._customers_df
        assert cust["customer_id"].is_unique

    def test_valid_foreign_keys(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        cust = small_generator._customers_df
        cust_ids = set(cust["customer_id"])
        assert pay["customer_id"].isin(cust_ids).all()

    def test_no_negative_amounts(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        assert (pay["amount"] >= 0).all()

    def test_valid_failure_reasons(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        valid = set(small_generator.config.failure_type_weights.keys())
        failed = pay[pay["payment_success"] == False]  # noqa: E712
        if len(failed) > 0:
            assert failed["failure_reason"].isin(valid).all()

    def test_valid_payment_methods(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        valid = set(small_generator.config.payment_method_weights.keys())
        assert pay["payment_method"].isin(valid).all()

    def test_consistent_success_status(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        successful = pay[pay["payment_success"] == True]  # noqa: E712
        if len(successful) > 0:
            assert successful["failure_reason"].isna().all()

    def test_consistent_failure_status(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        failed = pay[pay["payment_success"] == False]  # noqa: E712
        if len(failed) > 0:
            assert failed["failure_reason"].notna().all()

    def test_no_negative_retry_count(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        assert (pay["retry_count"] >= 0).all()

    def test_no_negative_recovery_time(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        recovery_times = pay["recovery_time_hours"].dropna()
        if len(recovery_times) > 0:
            assert (recovery_times >= 0).all()


# ─── Reproducibility ─────────────────────────────────────────────────────────

class TestReproducibility:
    """Verify deterministic output given same seed, different output for different seeds."""

    def test_same_seed_produces_identical_dataset(self) -> None:
        config = GenerationConfig(seed=42, num_customers=100, num_payments=1000)

        gen1 = SyntheticDataGenerator(config)
        cust1, pay1 = gen1.generate()

        gen2 = SyntheticDataGenerator(config)
        cust2, pay2 = gen2.generate()

        pd.testing.assert_frame_equal(cust1, cust2)
        pd.testing.assert_frame_equal(pay1, pay2)

    def test_different_seed_produces_different_dataset(self) -> None:
        config1 = GenerationConfig(seed=42, num_customers=100, num_payments=1000)
        config2 = GenerationConfig(seed=99, num_customers=100, num_payments=1000)

        gen1 = SyntheticDataGenerator(config1)
        _, pay1 = gen1.generate()

        gen2 = SyntheticDataGenerator(config2)
        _, pay2 = gen2.generate()

        # Amounts should differ (they're random)
        assert not pay1["amount"].equals(pay2["amount"])

    def test_config_saved_and_loadable(self, tmp_path: Path) -> None:
        config = GenerationConfig(seed=42, num_customers=100, num_payments=1000)
        gen = SyntheticDataGenerator(config)
        gen.generate()
        gen.save(tmp_path)

        config_path = tmp_path / "generation_config.json"
        assert config_path.exists()

        loaded = json.loads(config_path.read_text())
        assert loaded["seed"] == 42
        assert loaded["num_customers"] == 100
        assert loaded["num_payments"] == 1000


# ─── Leakage Prevention ──────────────────────────────────────────────────────

class TestLeakagePrevention:
    """Ensure leakage columns are documented and separated from features."""

    def test_leakage_columns_not_in_features(self) -> None:
        overlap = set(LEAKAGE_COLUMNS) & set(FEATURE_COLUMNS)
        assert len(overlap) == 0, f"Leakage columns in feature set: {overlap}"

    def test_target_not_in_features(self) -> None:
        assert TARGET_COLUMN not in FEATURE_COLUMNS

    def test_simulated_prob_not_in_features(self) -> None:
        assert "simulated_recovery_probability" not in FEATURE_COLUMNS

    def test_recovery_time_not_in_features(self) -> None:
        assert "recovery_time_hours" not in FEATURE_COLUMNS

    def test_recovered_amount_not_in_features(self) -> None:
        assert "recovered_amount" not in FEATURE_COLUMNS


# ─── Distribution Sanity ─────────────────────────────────────────────────────

class TestDistributionSanity:
    """Verify distributions are realistic and not degenerate."""

    def test_multiple_failure_types_present(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        failed = pay[pay["payment_success"] == False]  # noqa: E712
        if len(failed) > 0:
            unique_reasons = failed["failure_reason"].nunique()
            assert unique_reasons >= 5, f"Only {unique_reasons} failure types"

    def test_multiple_payment_methods_present(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        assert pay["payment_method"].nunique() >= 4

    def test_multiple_segments_present(self, small_generator: SyntheticDataGenerator) -> None:
        cust = small_generator._customers_df
        assert cust["segment"].nunique() >= 3

    def test_recovery_rate_realistic(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        failed = pay[pay["payment_success"] == False]  # noqa: E712
        if len(failed) > 0:
            with_outcome = failed[failed["actual_recovery_outcome"].notna()]
            if len(with_outcome) > 0:
                rate = with_outcome["actual_recovery_outcome"].mean()
                assert 0.15 < rate < 0.85, f"Recovery rate {rate:.2f} seems unrealistic"

    def test_failure_types_have_different_recovery_rates(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        failed = pay[(pay["payment_success"] == False) & (pay["actual_recovery_outcome"].notna())]  # noqa: E712
        if len(failed) < 50:
            pytest.skip("Not enough failed payments for this test")
        rates = failed.groupby("failure_reason")["actual_recovery_outcome"].mean()
        # There should be meaningful variation across failure types
        if len(rates) >= 2:
            assert rates.max() - rates.min() > 0.05, "Recovery rates too uniform across failure types"

    def test_amounts_have_variance(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        positive_amounts = pay[pay["amount"] > 0]["amount"]
        if len(positive_amounts) > 0:
            assert positive_amounts.std() > 0, "All amounts are identical"

    def test_has_both_successful_and_failed_payments(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        assert pay["payment_success"].sum() > 0, "No successful payments"
        assert (~pay["payment_success"]).sum() > 0, "No failed payments"


# ─── Demo Scenarios ──────────────────────────────────────────────────────────

class TestDemoScenarios:
    """Verify demo scenario tagging."""

    def test_demo_scenarios_tagged(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        tagged = pay[pay["demo_scenario"].notna()]
        assert len(tagged) > 0, "No demo scenarios tagged"

    def test_demo_scenario_values_valid(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        valid_scenarios = {
            "HIGH_RECOVERY_CASE", "MEDIUM_RECOVERY_CASE", "LOW_RECOVERY_CASE",
            "HIGH_VALUE_CUSTOMER", "MULTIPLE_RETRY_CASE",
            "TEMPORARY_FAILURE_CASE", "PERMANENT_FAILURE_CASE",
        }
        tagged = pay[pay["demo_scenario"].notna()]
        for scenario in tagged["demo_scenario"].unique():
            assert scenario in valid_scenarios, f"Invalid demo scenario: {scenario}"

    def test_most_records_not_demo(self, small_generator: SyntheticDataGenerator) -> None:
        pay = small_generator._payments_df
        non_demo = pay[pay["demo_scenario"].isna()]
        # Vast majority should NOT be demo scenarios
        assert len(non_demo) > len(pay) * 0.9


# ─── File Output ──────────────────────────────────────────────────────────────

class TestFileOutput:
    """Verify saved files are correct."""

    def test_save_creates_all_files(self, small_generator: SyntheticDataGenerator, tmp_path: Path) -> None:
        paths = small_generator.save(tmp_path)
        assert (tmp_path / "customers.csv").exists()
        assert (tmp_path / "payments.csv").exists()
        assert (tmp_path / "generation_config.json").exists()
        assert (tmp_path / "data_quality_report.json").exists()

    def test_quality_report_valid_json(self, small_generator: SyntheticDataGenerator, tmp_path: Path) -> None:
        small_generator.save(tmp_path)
        report = json.loads((tmp_path / "data_quality_report.json").read_text())
        assert report["seed"] == 42
        assert report["validation_results"]["all_passed"] is True
        assert "feature_columns" in report
        assert "leakage_columns" in report

    def test_csv_roundtrip(self, small_generator: SyntheticDataGenerator, tmp_path: Path) -> None:
        small_generator.save(tmp_path)
        pay_loaded = pd.read_csv(tmp_path / "payments.csv")
        assert len(pay_loaded) == len(small_generator._payments_df)
        assert set(pay_loaded.columns) == set(small_generator._payments_df.columns)
