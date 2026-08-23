#!/usr/bin/env python
"""
RecoverAI — Generate Synthetic Dataset
=======================================
Creates customers.csv, payments.csv, generation_config.json, and
data_quality_report.json in data/synthetic/.

Usage:
    python scripts/generate_data.py
    python scripts/generate_data.py --seed 99 --customers 1000 --payments 10000
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Force UTF-8 on Windows to avoid Rich encoding issues
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from ml.data_generator import SyntheticDataGenerator, GenerationConfig, FEATURE_COLUMNS, LEAKAGE_COLUMNS

console = Console(force_terminal=True, force_jupyter=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate RecoverAI synthetic dataset")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--customers", type=int, default=5000, help="Number of customers")
    parser.add_argument("--payments", type=int, default=50000, help="Number of payments")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else project_root / "data" / "synthetic"

    console.print(Panel.fit(
        "[bold cyan]RecoverAI — Synthetic Data Generator[/bold cyan]\n"
        "[dim]All data is synthetic. No real customer information.[/dim]",
        border_style="cyan",
    ))

    # Configure
    config = GenerationConfig(
        seed=args.seed,
        num_customers=args.customers,
        num_payments=args.payments,
    )
    console.print(f"  Seed:       [bold]{config.seed}[/bold]")
    console.print(f"  Customers:  [bold]{config.num_customers:,}[/bold]")
    console.print(f"  Payments:   [bold]{config.num_payments:,}[/bold]")
    console.print()

    # Generate
    with console.status("[bold green]Generating customers..."):
        gen = SyntheticDataGenerator(config)
        customers_df, payments_df = gen.generate()

    console.print("[green]✓[/green] Data generated successfully.")

    # Validate
    with console.status("[bold yellow]Running validation..."):
        validation = gen.validate()

    if validation["all_passed"]:
        console.print("[green]✓[/green] All validation checks passed.")
    else:
        console.print("[red]✗[/red] Validation FAILED:")
        for check, passed in validation.items():
            if check != "all_passed" and not passed:
                console.print(f"  [red]FAIL[/red] {check}")
        sys.exit(1)

    # Save
    with console.status("[bold blue]Saving files..."):
        paths = gen.save(output_dir)

    console.print(f"[green]✓[/green] Files saved to: {output_dir}")
    for label, path in paths.items():
        console.print(f"  {label}: [dim]{path}[/dim]")
    console.print()

    # ── Summary Report ────────────────────────────────────────────────
    _print_report(customers_df, payments_df, config, validation)


def _print_report(customers_df, payments_df, config, validation) -> None:
    """Print the rich console summary report."""
    pay = payments_df
    cust = customers_df
    failed = pay[pay["payment_success"] == False]  # noqa: E712

    console.print()
    console.rule("[bold cyan]RecoverAI — Dataset Generation Report[/bold cyan]")
    console.print()

    # ── Shape ──
    console.print(f"  [bold]Payments:[/bold]  {len(pay):,} rows × {len(pay.columns)} columns")
    console.print(f"  [bold]Customers:[/bold] {len(cust):,} rows × {len(cust.columns)} columns")
    console.print(f"  [bold]Date Range:[/bold] {config.date_start} → {config.date_end}")
    console.print(f"  [bold]Successful:[/bold] {int(pay['payment_success'].sum()):,}  |  [bold]Failed:[/bold] {len(failed):,}")
    console.print()

    # ── Payment Amounts ──
    amounts = pay[pay["amount"] > 0]["amount"]
    if len(amounts) > 0:
        tbl = Table(title="Payment Amounts (₹)", box=box.SIMPLE_HEAVY)
        tbl.add_column("Stat", style="cyan")
        tbl.add_column("Value", justify="right")
        tbl.add_row("Min", f"₹{amounts.min():,.2f}")
        tbl.add_row("Max", f"₹{amounts.max():,.2f}")
        tbl.add_row("Mean", f"₹{amounts.mean():,.2f}")
        tbl.add_row("Median", f"₹{amounts.median():,.2f}")
        tbl.add_row("Std Dev", f"₹{amounts.std():,.2f}")
        console.print(tbl)
        console.print()

    # ── Failure Types ──
    if len(failed) > 0:
        tbl = Table(title="Failure Type Distribution", box=box.SIMPLE_HEAVY)
        tbl.add_column("Failure Reason", style="yellow")
        tbl.add_column("Count", justify="right")
        tbl.add_column("Pct", justify="right")
        for reason, count in failed["failure_reason"].value_counts().items():
            pct = count / len(failed) * 100
            tbl.add_row(reason, f"{count:,}", f"{pct:.1f}%")
        console.print(tbl)
        console.print()

    # ── Payment Methods ──
    tbl = Table(title="Payment Method Distribution", box=box.SIMPLE_HEAVY)
    tbl.add_column("Method", style="green")
    tbl.add_column("Count", justify="right")
    tbl.add_column("Pct", justify="right")
    for method, count in pay["payment_method"].value_counts().items():
        pct = count / len(pay) * 100
        tbl.add_row(method, f"{count:,}", f"{pct:.1f}%")
    console.print(tbl)
    console.print()

    # ── Customer Segments ──
    tbl = Table(title="Customer Segment Distribution", box=box.SIMPLE_HEAVY)
    tbl.add_column("Segment", style="magenta")
    tbl.add_column("Count", justify="right")
    tbl.add_column("Pct", justify="right")
    for seg, count in cust["segment"].value_counts().items():
        pct = count / len(cust) * 100
        tbl.add_row(seg, f"{count:,}", f"{pct:.1f}%")
    console.print(tbl)
    console.print()

    # ── Recovery Rates ──
    failed_with_outcome = failed[failed["actual_recovery_outcome"].notna()]
    if len(failed_with_outcome) > 0:
        overall = failed_with_outcome["actual_recovery_outcome"].mean() * 100
        console.print(f"  [bold]Overall Recovery Rate:[/bold] {overall:.1f}%")
        console.print()

        tbl = Table(title="Recovery Rate by Failure Type", box=box.SIMPLE_HEAVY)
        tbl.add_column("Failure Reason", style="yellow")
        tbl.add_column("Recovery Rate", justify="right")
        tbl.add_column("Count", justify="right")
        for reason in sorted(failed_with_outcome["failure_reason"].unique()):
            subset = failed_with_outcome[failed_with_outcome["failure_reason"] == reason]
            rate = subset["actual_recovery_outcome"].mean() * 100
            tbl.add_row(reason, f"{rate:.1f}%", f"{len(subset):,}")
        console.print(tbl)
        console.print()

    # ── Demo Scenarios ──
    demo_count = pay["demo_scenario"].notna().sum()
    console.print(f"  [bold]Demo Scenarios Tagged:[/bold] {demo_count}")
    if demo_count > 0:
        for scenario, count in pay[pay["demo_scenario"].notna()]["demo_scenario"].value_counts().items():
            console.print(f"    {scenario}: {count}")
    console.print()

    # ── Column Classification ──
    console.print(f"  [bold]Feature Columns:[/bold]  {len(FEATURE_COLUMNS)}")
    console.print(f"  [bold]Leakage Columns:[/bold]  {len(LEAKAGE_COLUMNS)} [red](NEVER use as ML input)[/red]")
    console.print()

    # ── Sample Records ──
    console.print("[bold]Sample Payment Records (5 rows):[/bold]")
    sample_cols = ["payment_id", "customer_id", "amount", "payment_method",
                   "payment_success", "failure_reason", "actual_recovery_outcome", "demo_scenario"]
    available_cols = [c for c in sample_cols if c in pay.columns]
    console.print(pay[available_cols].sample(5, random_state=config.seed).to_string(index=False))
    console.print()

    console.print("[bold]Sample Customer Records (3 rows):[/bold]")
    console.print(cust.sample(3, random_state=config.seed).to_string(index=False))
    console.print()

    # ── Schema ──
    console.print("[bold]Payments Schema:[/bold]")
    for col in pay.columns:
        console.print(f"  {col}: {pay[col].dtype}")
    console.print()

    # ── Validation ──
    console.print("[bold]Validation Results:[/bold]")
    for check, passed in validation.items():
        icon = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"  {icon} {check}")
    console.print()

    console.rule("[bold green]Generation Complete[/bold green]")


if __name__ == "__main__":
    main()
