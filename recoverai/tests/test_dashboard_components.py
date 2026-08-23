"""
RecoverAI — Dashboard Components & Theme Unit & Regression Tests
================================================================
Validates metric formatting, Plotly chart generators, API data contracts, and theme contract completeness.
"""

from __future__ import annotations

import re
import pandas as pd
import pytest

from dashboard.components.charts import (
    create_failure_analysis_chart,
    create_probability_gauge_chart,
    create_recovery_trend_chart,
    create_revenue_breakdown_donut,
    create_segment_recovery_chart,
    create_strategy_performance_chart,
)
from dashboard.components.metrics import format_inr, format_percent
from dashboard.config import COLORS, STATUS_BADGES, STRATEGY_ICONS, TIER_COLORS


class TestDashboardTheme:
    """Tests for centralized theme configuration and high-contrast color contract."""

    REQUIRED_CANONICAL_KEYS = [
        "bg_dark",
        "surface",
        "surface_alt",
        "primary",
        "success",
        "warning",
        "danger",
        "info",
        "text_primary",
        "text_secondary",
        "border",
    ]

    REQUIRED_BACKWARDS_COMPATIBLE_ALIASES = [
        "background",
        "card_bg",
        "card_border",
        "text_dark",
        "text_muted",
        "error",
        "sidebar_bg",
    ]

    def test_theme_contains_all_canonical_keys(self) -> None:
        """Verifies that all required theme keys exist in COLORS."""
        for key in self.REQUIRED_CANONICAL_KEYS:
            assert key in COLORS, f"Missing required canonical theme key: '{key}'"

    def test_theme_contains_backwards_compatible_aliases(self) -> None:
        """Verifies that components using legacy aliases resolve cleanly."""
        for key in self.REQUIRED_BACKWARDS_COMPATIBLE_ALIASES:
            assert key in COLORS, f"Missing backwards-compatible alias: '{key}'"

    def test_colors_are_valid_hex(self) -> None:
        """Verifies all color values in COLORS are valid 6-digit hex codes."""
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for key, val in COLORS.items():
            assert hex_pattern.match(val), f"Invalid hex color for '{key}': '{val}'"

    def test_high_contrast_text_guarantee(self) -> None:
        """Ensures primary text is pure white and secondary text is high-contrast light gray."""
        assert COLORS["text_primary"].upper() == "#FFFFFF"
        assert COLORS["text_dark"].upper() == "#FFFFFF"
        assert COLORS["text_secondary"].upper() == "#E5E7EB"
        assert COLORS["text_muted"].upper() == "#E5E7EB"

    def test_high_contrast_backgrounds(self) -> None:
        """Ensures background and card surfaces adhere to the high-contrast fintech specification."""
        assert COLORS["bg_dark"].upper() == "#0B0F17"
        assert COLORS["surface"].upper() == "#111827"
        assert COLORS["card_bg"].upper() == "#111827"
        assert COLORS["border"].upper() == "#1F2937"

    def test_tier_colors_match_theme(self) -> None:
        """Verifies 3-tier policy colors map to high-contrast status colors."""
        assert TIER_COLORS["HIGH_CONFIDENCE"].upper() == "#22C55E"
        assert TIER_COLORS["ACTIONABLE_OUTREACH"].upper() == "#F59E0B"
        assert TIER_COLORS["SUPPRESS_OR_ESCALATE"].upper() == "#EF4444"


class TestMetricFormatters:
    """Tests for Indian currency and percentage formatters."""

    def test_format_inr_basic(self) -> None:
        assert format_inr(1250.50) == "₹1,250.50"
        assert format_inr(0.0) == "₹0.00"
        assert format_inr(None) == "₹0.00"

    def test_format_inr_large_values(self) -> None:
        assert "L" in format_inr(250_000.0)  # 2.50 L
        assert "Cr" in format_inr(15_000_000.0)  # 1.50 Cr

    def test_format_percent(self) -> None:
        assert format_percent(0.5718) == "57.2%"
        assert format_percent(1.0) == "100.0%"
        assert format_percent(0.0) == "0.0%"
        assert format_percent(None) == "0.0%"


class TestPlotlyCharts:
    """Tests for Plotly chart generators & data contracts."""

    def test_create_recovery_trend_chart_legacy_format(self) -> None:
        trends_data = {
            "dates": ["2026-01-01", "2026-02-01"],
            "failed_volume": [10000.0, 12000.0],
            "recovered_volume": [6000.0, 7500.0],
            "recovery_rate": [0.60, 0.625],
        }
        fig = create_recovery_trend_chart(trends_data)
        assert fig is not None
        assert len(fig.data) == 3

    def test_create_recovery_trend_chart_api_schema(self) -> None:
        """Tests that TrendsAnalyticsResponse schema with 'points' renders cleanly."""
        api_trends_data = {
            "interval": "monthly",
            "points": [
                {
                    "date": "2026-01",
                    "failed_count": 100,
                    "failed_amount": 50000.0,
                    "recovered_count": 60,
                    "recovered_amount": 35000.0,
                    "recovery_rate": 0.70,
                },
                {
                    "date": "2026-02",
                    "failed_count": 120,
                    "failed_amount": 60000.0,
                    "recovered_count": 75,
                    "recovered_amount": 42000.0,
                    "recovery_rate": 0.70,
                },
            ],
        }
        fig = create_recovery_trend_chart(api_trends_data)
        assert fig is not None
        assert len(fig.data) == 3

    def test_create_recovery_trend_chart_empty_or_none(self) -> None:
        fig_none = create_recovery_trend_chart(None)
        assert fig_none is not None
        fig_empty = create_recovery_trend_chart({"interval": "monthly", "points": []})
        assert fig_empty is not None

    def test_create_revenue_breakdown_donut(self) -> None:
        overview = {"recovered_value": 350000.0, "unrecovered_value": 250000.0, "recovery_rate": 0.583}
        fig = create_revenue_breakdown_donut(overview)
        assert fig is not None
        assert len(fig.data) == 1

    def test_create_strategy_performance_chart_api_schema_regression(self) -> None:
        """
        Regression test: Verifies that StrategyAnalyticsItem schema (/api/v1/analytics/by-strategy)
        which returns 'success_rate' does NOT cause KeyError: 'recovery_rate'.
        """
        api_strat_data = [
            {
                "strategy": "SMART_RETRY",
                "total_cases": 258,
                "successful_recoveries": 258,
                "recovered_value": 1252296.8,
                "success_rate": 1.0,
                "success_rate_percentage": "100.0%",
            },
            {
                "strategy": "CUSTOMER_OUTREACH",
                "total_cases": 150,
                "successful_recoveries": 75,
                "recovered_value": 450000.0,
                "success_rate": 0.50,
                "success_rate_percentage": "50.0%",
            },
        ]
        fig = create_strategy_performance_chart(api_strat_data)
        assert fig is not None
        assert len(fig.data) == 2

    def test_create_strategy_performance_chart_legacy_recovery_rate(self) -> None:
        """Tests that legacy test payloads with 'recovery_rate' also succeed."""
        legacy_data = [
            {"strategy": "SMART_RETRY", "recovered_value": 50000.0, "recovery_rate": 0.71},
            {"strategy": "CUSTOMER_OUTREACH", "recovered_value": 20000.0, "recovery_rate": 0.48},
        ]
        fig = create_strategy_performance_chart(legacy_data)
        assert fig is not None
        assert len(fig.data) == 2

    def test_create_strategy_performance_chart_missing_columns_raises_error(self) -> None:
        """Verifies that missing columns raise an informative ValueError."""
        invalid_data = [{"invalid_key": "foo"}]
        with pytest.raises(ValueError, match="create_strategy_performance_chart missing required columns"):
            create_strategy_performance_chart(invalid_data)

    def test_create_failure_analysis_chart_api_schema(self) -> None:
        """Tests that FailureAnalyticsItem (/api/v1/analytics/by-failure) renders cleanly."""
        api_fail_data = [
            {
                "failure_reason": "insufficient_funds",
                "total_failed": 3163,
                "recovered_count": 1895,
                "total_amount": 17468567.63,
                "recovered_amount": 10092828.63,
                "recovery_rate": 0.5991,
                "recovery_rate_percentage": "59.9%",
            },
        ]
        fig = create_failure_analysis_chart(api_fail_data)
        assert fig is not None
        assert len(fig.data) == 2

    def test_create_failure_analysis_chart_legacy(self) -> None:
        fail_data = [
            {"failure_reason": "insufficient_funds", "total_failed_value": 30000.0, "recovered_value": 15000.0, "unrecovered_value": 15000.0},
        ]
        fig = create_failure_analysis_chart(fail_data)
        assert fig is not None
        assert len(fig.data) == 2

    def test_create_segment_recovery_chart(self) -> None:
        seg_data = [
            {"segment": "enterprise", "recovered_value": 100000.0, "recovery_rate": 0.65},
        ]
        fig = create_segment_recovery_chart(seg_data)
        assert fig is not None
        assert len(fig.data) == 2

    def test_create_probability_gauge_chart(self) -> None:
        fig = create_probability_gauge_chart(0.732, "HIGH_CONFIDENCE")
        assert fig is not None
        assert len(fig.data) == 1

    def test_create_probability_gauge_chart_invalid_input_raises_error(self) -> None:
        with pytest.raises(ValueError, match="expects numeric probability"):
            create_probability_gauge_chart("not_a_number", "HIGH_CONFIDENCE")  # type: ignore
