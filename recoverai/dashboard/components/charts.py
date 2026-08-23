"""
RecoverAI — Interactive Plotly Charts Component (Fintech High-Contrast Dark Theme)
==================================================================================
Generates high-contrast Plotly visualizations matching the actual backend API schemas.
Validates input columns robustly with clear, developer-friendly ValueErrors on contract mismatch.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard.config import COLORS, TIER_COLORS


def apply_fintech_theme(fig: go.Figure) -> go.Figure:
    """Applies a clean, high-contrast dark fintech theme to any Plotly figure."""
    fig.update_layout(
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            color="#FFFFFF",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#E5E7EB"),
        ),
        hoverlabel=dict(
            bgcolor="#111827",
            bordercolor="#3B82F6",
            font=dict(color="#FFFFFF", size=12),
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#1F2937",
            zeroline=False,
            showline=True,
            linecolor="#1F2937",
            tickfont=dict(color="#E5E7EB", size=11),
            title_font=dict(color="#FFFFFF", size=12),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#1F2937",
            zeroline=False,
            showline=True,
            linecolor="#1F2937",
            tickfont=dict(color="#E5E7EB", size=11),
            title_font=dict(color="#FFFFFF", size=12),
        ),
    )
    return fig


def create_recovery_trend_chart(trends_data: Optional[Dict[str, Any]]) -> go.Figure:
    """
    Creates a dual-axis time-series recovery trend chart (Volume vs Recovery Rate).
    Consumes TrendsAnalyticsResponse (/api/v1/analytics/trends) or normalized trend dict.
    """
    fig = go.Figure()

    if not trends_data:
        fig.add_annotation(text="No trend data available", showarrow=False, font=dict(size=14, color="#E5E7EB"))
        return apply_fintech_theme(fig)

    # 1. Extract data points from schema {"interval": "...", "points": [...]} or legacy dict
    if "points" in trends_data:
        points = trends_data.get("points", [])
        if not points:
            fig.add_annotation(text="No trend points available", showarrow=False, font=dict(size=14, color="#E5E7EB"))
            return apply_fintech_theme(fig)
        df = pd.DataFrame(points)
        # Normalize fields to standard chart dataframe
        if "date" in df.columns and "dates" not in df.columns:
            df["dates"] = df["date"]
        if "failed_amount" in df.columns and "failed_volume" not in df.columns:
            df["failed_volume"] = df["failed_amount"]
        if "recovered_amount" in df.columns and "recovered_volume" not in df.columns:
            df["recovered_volume"] = df["recovered_amount"]
    else:
        df = pd.DataFrame(trends_data)

    # 2. Validate required columns
    required_cols = ["dates", "failed_volume", "recovered_volume", "recovery_rate"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(
            f"create_recovery_trend_chart missing required columns: {missing}. Received columns: {list(df.columns)}"
        )

    df["recovery_rate_pct"] = df["recovery_rate"] * 100

    # Bar: Failed Volume
    fig.add_trace(
        go.Bar(
            x=df["dates"],
            y=df["failed_volume"],
            name="Failed Volume (₹)",
            marker_color="#374151",
            opacity=0.75,
            yaxis="y",
            hovertemplate="<b>%{x}</b><br>Failed Volume: ₹%{y:,.2f}<extra></extra>",
        )
    )

    # Bar: Recovered Volume
    fig.add_trace(
        go.Bar(
            x=df["dates"],
            y=df["recovered_volume"],
            name="Recovered Volume (₹)",
            marker_color="#3B82F6",
            yaxis="y",
            hovertemplate="<b>%{x}</b><br>Recovered Volume: ₹%{y:,.2f}<extra></extra>",
        )
    )

    # Line: Recovery Rate %
    fig.add_trace(
        go.Scatter(
            x=df["dates"],
            y=df["recovery_rate_pct"],
            name="Recovery Rate (%)",
            mode="lines+markers",
            line=dict(color="#22C55E", width=3),
            marker=dict(size=6, color="#4ADE80"),
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Recovery Rate: %{y:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>Monthly Involuntary Churn & Recovery Velocity</b>",
        barmode="overlay",
        yaxis=dict(
            title="Volume (₹)",
            showgrid=True,
            gridcolor="#1F2937",
            tickprefix="₹",
        ),
        yaxis2=dict(
            title="Recovery Rate (%)",
            overlaying="y",
            side="right",
            range=[0, 100],
            ticksuffix="%",
            showgrid=False,
            tickfont=dict(color="#4ADE80"),
            title_font=dict(color="#4ADE80"),
        ),
    )

    return apply_fintech_theme(fig)


def create_revenue_breakdown_donut(overview_data: Dict[str, Any]) -> go.Figure:
    """
    Creates a modern donut chart showing Recovered vs Unrecovered revenue volume.
    Consumes AnalyticsOverviewResponse (/api/v1/analytics/overview).
    """
    fig = go.Figure()

    if not overview_data:
        fig.add_annotation(text="No overview data available", showarrow=False, font=dict(size=14, color="#E5E7EB"))
        return apply_fintech_theme(fig)

    # Validate required keys
    required_keys = ["recovered_value", "unrecovered_value"]
    missing = [k for k in required_keys if k not in overview_data]
    if missing:
        raise ValueError(
            f"create_revenue_breakdown_donut missing required keys: {missing}. Received keys: {list(overview_data.keys())}"
        )

    recovered = float(overview_data.get("recovered_value", 0.0))
    unrecovered = float(overview_data.get("unrecovered_value", 0.0))

    fig.add_trace(
        go.Pie(
            labels=["Recovered Revenue", "Unrecovered Volume"],
            values=[recovered, unrecovered],
            hole=0.68,
            marker=dict(colors=["#22C55E", "#EF4444"]),
            textinfo="label+percent",
            textfont=dict(color="#FFFFFF", size=12),
            hovertemplate="<b>%{label}</b><br>Amount: ₹%{value:,.2f}<br>Share: %{percent}<extra></extra>",
        )
    )

    rate = float(overview_data.get("recovery_rate", 0.0)) * 100
    fig.update_layout(
        title="<b>Revenue Recovery Ratio</b>",
        annotations=[
            dict(
                text=f"<b>{rate:.1f}%</b><br><span style='font-size:11px;color:#E5E7EB'>Recovered</span>",
                x=0.5,
                y=0.5,
                font_size=20,
                font_color="#FFFFFF",
                showarrow=False,
            )
        ],
        showlegend=False,
    )

    return apply_fintech_theme(fig)


def create_strategy_performance_chart(strategy_data: Optional[List[Dict[str, Any]]]) -> go.Figure:
    """
    Creates a bar chart comparing recovery rates and volume across AI strategies.
    Consumes List[StrategyAnalyticsItem] (/api/v1/analytics/by-strategy).
    Supports either 'success_rate' (API schema) or 'recovery_rate' (legacy).
    """
    fig = go.Figure()

    if not strategy_data:
        fig.add_annotation(text="No strategy data available", showarrow=False, font=dict(size=14, color="#E5E7EB"))
        return apply_fintech_theme(fig)

    df = pd.DataFrame(strategy_data)

    # 1. Validate required columns
    base_required = ["strategy", "recovered_value"]
    missing_base = [col for col in base_required if col not in df.columns]
    has_rate_col = "success_rate" in df.columns or "recovery_rate" in df.columns

    if missing_base or not has_rate_col:
        raise ValueError(
            f"create_strategy_performance_chart missing required columns. "
            f"Expected 'strategy', 'recovered_value', and either 'success_rate' or 'recovery_rate'. "
            f"Received columns: {list(df.columns)}"
        )

    # 2. Extract rate column
    rate_col = "success_rate" if "success_rate" in df.columns else "recovery_rate"
    df["recovery_rate_pct"] = df[rate_col].astype(float) * 100
    df["strategy_label"] = df["strategy"].astype(str).str.replace("_", " ").str.title()

    fig.add_trace(
        go.Bar(
            x=df["strategy_label"],
            y=df["recovered_value"],
            name="Recovered Volume (₹)",
            marker_color="#3B82F6",
            hovertemplate="<b>%{x}</b><br>Recovered: ₹%{y:,.2f}<extra></extra>",
            yaxis="y",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["strategy_label"],
            y=df["recovery_rate_pct"],
            name="Conversion Rate (%)",
            mode="lines+markers",
            line=dict(color="#F59E0B", width=3),
            marker=dict(size=8, color="#FBBF24"),
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Conversion Rate: %{y:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>Recovery Efficacy by AI Decision Strategy</b>",
        yaxis=dict(title="Recovered Value (₹)", tickprefix="₹"),
        yaxis2=dict(
            title="Conversion Rate (%)",
            overlaying="y",
            side="right",
            range=[0, 100],
            ticksuffix="%",
            showgrid=False,
            tickfont=dict(color="#FBBF24"),
            title_font=dict(color="#FBBF24"),
        ),
    )

    return apply_fintech_theme(fig)


def create_failure_analysis_chart(failure_data: Optional[List[Dict[str, Any]]]) -> go.Figure:
    """
    Creates a stacked horizontal bar chart breaking down recovery across failure reasons.
    Consumes List[FailureAnalyticsItem] (/api/v1/analytics/by-failure).
    """
    fig = go.Figure()

    if not failure_data:
        fig.add_annotation(text="No failure analytics available", showarrow=False, font=dict(size=14, color="#E5E7EB"))
        return apply_fintech_theme(fig)

    df = pd.DataFrame(failure_data)

    if "failure_reason" not in df.columns:
        raise ValueError(
            f"create_failure_analysis_chart missing 'failure_reason'. Received columns: {list(df.columns)}"
        )

    # Normalize recovered amount/value
    if "recovered_value" not in df.columns and "recovered_amount" in df.columns:
        df["recovered_value"] = df["recovered_amount"]

    # Normalize unrecovered amount/value
    if "unrecovered_value" not in df.columns:
        if "total_amount" in df.columns and "recovered_value" in df.columns:
            df["unrecovered_value"] = (df["total_amount"] - df["recovered_value"]).clip(lower=0.0)
        elif "total_failed_value" in df.columns and "recovered_value" in df.columns:
            df["unrecovered_value"] = (df["total_failed_value"] - df["recovered_value"]).clip(lower=0.0)

    if "recovered_value" not in df.columns or "unrecovered_value" not in df.columns:
        raise ValueError(
            f"create_failure_analysis_chart missing recovered/unrecovered amount columns. "
            f"Received columns: {list(df.columns)}"
        )

    # Sort by total value
    sort_col = "total_amount" if "total_amount" in df.columns else ("total_failed_value" if "total_failed_value" in df.columns else "recovered_value")
    df = df.sort_values(sort_col, ascending=True)
    df["failure_label"] = df["failure_reason"].astype(str).str.replace("_", " ").str.title()

    fig.add_trace(
        go.Bar(
            y=df["failure_label"],
            x=df["recovered_value"],
            name="Recovered Value (₹)",
            orientation="h",
            marker_color="#22C55E",
            hovertemplate="<b>%{y}</b><br>Recovered: ₹%{x:,.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            y=df["failure_label"],
            x=df["unrecovered_value"],
            name="Unrecovered Value (₹)",
            orientation="h",
            marker_color="#EF4444",
            hovertemplate="<b>%{y}</b><br>Unrecovered: ₹%{x:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>Recovery Breakdown by Failure Classification</b>",
        barmode="stack",
        xaxis=dict(title="Payment Value (₹)", tickprefix="₹"),
        yaxis=dict(title=""),
    )

    return apply_fintech_theme(fig)


def create_segment_recovery_chart(segment_data: Optional[List[Dict[str, Any]]]) -> go.Figure:
    """
    Creates a grouped bar chart comparing recovery rates across customer segments.
    Consumes List[SegmentAnalyticsItem] (/api/v1/analytics/by-segment).
    """
    fig = go.Figure()

    if not segment_data:
        fig.add_annotation(text="No segment analytics available", showarrow=False, font=dict(size=14, color="#E5E7EB"))
        return apply_fintech_theme(fig)

    df = pd.DataFrame(segment_data)

    required_cols = ["segment", "recovered_value", "recovery_rate"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(
            f"create_segment_recovery_chart missing required columns: {missing}. Received columns: {list(df.columns)}"
        )

    df["segment_label"] = df["segment"].astype(str).str.replace("_", " ").str.title()
    df["recovery_rate_pct"] = df["recovery_rate"].astype(float) * 100

    fig.add_trace(
        go.Bar(
            x=df["segment_label"],
            y=df["recovered_value"],
            name="Recovered Volume (₹)",
            marker_color="#3B82F6",
            hovertemplate="<b>%{x}</b><br>Recovered: ₹%{y:,.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["segment_label"],
            y=df["recovery_rate_pct"],
            name="Recovery Rate (%)",
            mode="lines+markers",
            line=dict(color="#22C55E", width=3),
            marker=dict(size=8, color="#4ADE80"),
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Rate: %{y:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>Customer Segment Yield & Recovery Rates</b>",
        yaxis=dict(title="Volume (₹)", tickprefix="₹"),
        yaxis2=dict(
            title="Recovery Rate (%)",
            overlaying="y",
            side="right",
            range=[0, 100],
            ticksuffix="%",
            showgrid=False,
            tickfont=dict(color="#4ADE80"),
            title_font=dict(color="#4ADE80"),
        ),
    )

    return apply_fintech_theme(fig)


def create_probability_gauge_chart(probability: float, tier: str) -> go.Figure:
    """Creates a sleek gauge chart for calibrated ML recovery probability."""
    if probability is None or not isinstance(probability, (int, float)):
        raise ValueError(f"create_probability_gauge_chart expects numeric probability, received: {probability}")
    if not isinstance(tier, str):
        raise ValueError(f"create_probability_gauge_chart expects string tier, received: {tier}")

    prob_pct = float(probability) * 100
    tier_color = TIER_COLORS.get(tier, COLORS["primary"])

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=prob_pct,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "<b>Recovery Probability</b>", "font": {"size": 16, "color": "#FFFFFF"}},
            number={"suffix": "%", "font": {"size": 32, "color": tier_color, "family": "Inter"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#1F2937", "tickfont": {"color": "#E5E7EB"}},
                "bar": {"color": tier_color, "thickness": 0.3},
                "bgcolor": "#111827",
                "borderwidth": 1,
                "bordercolor": "#1F2937",
                "steps": [
                    {"range": [0, 45], "color": "#450A0A"},      # Suppress (Red)
                    {"range": [45, 65], "color": "#451A03"},     # Outreach (Amber)
                    {"range": [65, 100], "color": "#052E16"},    # Smart Retry (Green)
                ],
                "threshold": {
                    "line": {"color": tier_color, "width": 4},
                    "thickness": 0.75,
                    "value": prob_pct,
                },
            },
        )
    )

    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig
