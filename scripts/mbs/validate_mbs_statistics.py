"""Validate normalized Medicare statistics and write an APET quality report."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", type=Path, default=project_root / "data/mbs/normalized/mbs_quarterly.csv")
    parser.add_argument("--output-dir", type=Path, default=project_root / "output/validation")
    args = parser.parse_args()
    data = pd.read_csv(args.data_file)
    issues = []
    keys = ["financial_quarter", "state", "service_type"]
    duplicates = int(data.duplicated(keys).sum())
    if duplicates:
        issues.append(f"Found {duplicates} duplicate quarter/state/service rows")
    numeric = ["services", "benefits_dollars", "bulk_billed_services", "patient_billed_services"]
    missing_values = {column: int(data[column].isna().sum()) for column in numeric}
    if any(missing_values.values()):
        issues.append(f"Missing numeric values: {missing_values}")
    quarters = sorted(data.financial_quarter.unique())
    national = data[(data.state == "Australia") & (data.service_type == "Total Medicare")]
    if len(national) != len(quarters):
        issues.append("A national Total Medicare record is not present for every quarter")
    states = data[(data.state != "Australia") & (data.service_type == "Total Medicare")]
    state_totals = states.groupby("financial_quarter").benefits_dollars.sum()
    national_totals = national.set_index("financial_quarter").benefits_dollars
    differences = (state_totals - national_totals).abs()
    max_difference = float(differences.max()) if not differences.empty else 0.0
    if max_difference > 1:
        issues.append(f"National/state benefit reconciliation differs by up to ${max_difference:,.2f}")
    years = data.groupby("financial_year").financial_quarter.nunique()
    report = {
        "status": "PASS" if not issues else "REVIEW",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "normalized_rows": len(data), "first_quarter": quarters[0], "last_quarter": quarters[-1],
        "financial_years": int(data.financial_year.nunique()),
        "complete_financial_years": int((years == 4).sum()),
        "duplicate_keys": duplicates, "missing_numeric_values": missing_values,
        "maximum_national_state_reconciliation_difference_dollars": round(max_difference, 2),
        "issues": issues,
        "interpretation_note": "Benefits are MBS claims processed by Medicare, not total Australian health spending.",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / "mbs_latest.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"MBS VALIDATION: {report['status']}")
    print(f"Coverage: {quarters[0]} to {quarters[-1]} | Rows: {len(data):,}")
    print(f"Saved: {path}")
    if issues:
        for issue in issues:
            print(f"REVIEW: {issue}")


if __name__ == "__main__":
    main()
