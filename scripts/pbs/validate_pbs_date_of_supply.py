"""Validate normalized PBS data and record the one-quarter publication cutoff."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def quarter_cutoff(months: pd.Series) -> pd.Timestamp:
    latest = months.max()
    current_end = latest.to_period("Q-JUN").end_time.normalize()
    if latest.normalize() != current_end.replace(day=1):
        current_end = (latest.to_period("Q-JUN") - 1).end_time.normalize()
    return (current_end - pd.offsets.QuarterEnd(startingMonth=6)).normalize()


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", type=Path, default=project_root / "data/pbs/normalized/pbs_monthly_medicines.csv")
    parser.add_argument("--output-dir", type=Path, default=project_root / "output/validation")
    args = parser.parse_args()
    data = pd.read_csv(args.data_file, parse_dates=["month_of_supply"])
    issues = []
    required = {"month_of_supply", "financial_year", "financial_quarter", "atc5_code", "drug_name",
                "prescription_count", "government_contribution_dollars", "patient_contribution_dollars", "total_cost_dollars"}
    missing_columns = sorted(required - set(data.columns))
    if missing_columns:
        issues.append(f"Missing required columns: {missing_columns}")
    duplicates = int(data.duplicated(["month_of_supply", "atc5_code", "drug_name"]).sum())
    if duplicates:
        issues.append(f"Found {duplicates} duplicate monthly medicine keys")
    value_columns = ["prescription_count", "government_contribution_dollars", "patient_contribution_dollars", "total_cost_dollars"]
    negative = {column: int((data[column] < 0).sum()) for column in value_columns}
    if any(negative.values()):
        issues.append("Negative aggregate values were found; review possible claim adjustments")
    reconciliation = (data.government_contribution_dollars + data.patient_contribution_dollars - data.total_cost_dollars).abs()
    reconciliation_difference = float(reconciliation.sum())
    months = pd.Series(sorted(data.month_of_supply.dropna().unique()))
    expected = pd.date_range(months.min(), months.max(), freq="MS")
    missing_months = [month.strftime("%Y-%m") for month in expected if month not in set(months)]
    if missing_months:
        issues.append(f"Missing months: {missing_months}")
    cutoff = quarter_cutoff(data.month_of_supply)
    published = data[data.month_of_supply <= cutoff]
    report = {
        "status": "PASS" if not issues else "REVIEW",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "normalized_rows": len(data), "first_source_month": data.month_of_supply.min().strftime("%Y-%m"),
        "last_source_month": data.month_of_supply.max().strftime("%Y-%m"),
        "publication_cutoff": cutoff.strftime("%Y-%m-%d"),
        "publication_rule": "Exclude the latest complete source quarter and any incomplete quarter",
        "published_rows": len(published), "missing_months": missing_months,
        "duplicate_monthly_medicine_keys": duplicates, "negative_value_rows": negative,
        "absolute_total_reconciliation_difference_dollars": round(reconciliation_difference, 2),
        "government_contribution_dollars_to_cutoff": round(float(published.government_contribution_dollars.sum()), 2),
        "issues": issues,
        "interpretation_note": "Government contribution is processed PBS/RPBS expenditure by month of supply; recent data can be revised.",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "pbs_latest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [f"PBS DATE OF SUPPLY VALIDATION: {report['status']}", f"Normalized rows: {len(data):,}",
             f"Source coverage: {report['first_source_month']} to {report['last_source_month']}",
             f"APET publication cutoff: {report['publication_cutoff']}",
             f"Published government contribution: ${report['government_contribution_dollars_to_cutoff']:,.2f}",
             f"Duplicate monthly medicine keys: {duplicates:,}",
             f"Absolute contribution-to-total reconciliation difference: ${reconciliation_difference:,.2f}",
             "", report["interpretation_note"]]
    if issues:
        lines += ["", "Items requiring review:"] + [f"- {issue}" for issue in issues]
    text = "\n".join(lines) + "\n"
    (args.output_dir / "pbs_latest.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
