"""Validate normalized NHFB files and produce readable JSON and text reports."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


EXPECTED_STATES = {"NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"}
EXPECTED_MONTHS = {"July", "August", "September", "October", "November", "December",
                   "January", "February", "March", "April", "May", "June"}


def load(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path,
                        default=project_root / "data" / "public_hospital_funding" / "normalized")
    parser.add_argument("--output-dir", type=Path, default=project_root / "output" / "validation")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    state_rows = load(args.data_dir / "monthly_payments_by_state.csv")
    category_rows = load(args.data_dir / "monthly_payments_by_service_category.csv")
    issues: list[str] = []

    keys = [(r["financial_year"], r["month"], r["state_territory"]) for r in state_rows]
    duplicates = sum(count - 1 for count in Counter(keys).values() if count > 1)
    if duplicates:
        issues.append(f"State file has {duplicates} duplicate period/state rows")
    if {r["state_territory"] for r in state_rows} != EXPECTED_STATES:
        issues.append("State file does not contain exactly the eight expected jurisdictions")
    if {r["month"] for r in state_rows} != EXPECTED_MONTHS:
        issues.append("State file does not contain exactly the twelve expected months")
    negative_state_rows = sum(int(r["payment_dollars"]) < 0 for r in state_rows)
    negative_category_rows = sum(int(r["payment_dollars"]) < 0 for r in category_rows)
    if negative_state_rows:
        issues.append(f"State totals contain {negative_state_rows} unexpected negative values")

    year_state_month_counts = Counter(r["financial_year"] for r in state_rows)
    for year, count in sorted(year_state_month_counts.items()):
        if count != len(EXPECTED_STATES) * len(EXPECTED_MONTHS):
            issues.append(f"{year} has {count} state-month rows; expected 96")

    state_totals: dict[str, int] = defaultdict(int)
    category_totals: dict[str, int] = defaultdict(int)
    for row in state_rows:
        state_totals[row["financial_year"]] += int(row["payment_dollars"])
    for row in category_rows:
        category_totals[row["financial_year"]] += int(row["payment_dollars"])

    coverage = {}
    for year, total in sorted(state_totals.items()):
        component = category_totals.get(year, 0)
        coverage[year] = round(component / total * 100, 2) if total else None
        if component > total:
            issues.append(f"Service-category total exceeds state total in {year}")

    report = {
        "status": "PASS" if not issues else "FAIL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "state_month_rows": len(state_rows),
        "service_category_rows": len(category_rows),
        "financial_years": sorted(state_totals),
        "jurisdictions": sorted({r["state_territory"] for r in state_rows}),
        "annual_state_payment_totals_dollars": dict(sorted(state_totals.items())),
        "annual_service_category_totals_dollars": dict(sorted(category_totals.items())),
        "service_category_coverage_percent": coverage,
        "negative_service_category_adjustment_rows": negative_category_rows,
        "issues": issues,
        "interpretation_note": (
            "These are cash-basis payments through the National Health Funding Pool and "
            "State Managed Funds, not the full cost of operating every Australian hospital. "
            "Service-category rows do not cover every item included in the state totals."
        ),
    }
    (args.output_dir / "public_hospital_funding_latest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        f"NHFB PUBLIC HOSPITAL FUNDING VALIDATION: {report['status']}",
        f"State-month rows: {len(state_rows):,}",
        f"Service-category rows: {len(category_rows):,}", "",
        f"Negative service-category adjustment rows retained: {negative_category_rows:,}", "",
        "Annual payments represented in the state trend file:",
    ]
    for year, total in sorted(state_totals.items()):
        lines.append(f"- {year}: ${total:,.0f}; category coverage {coverage[year]:.2f}%")
    lines += ["", report["interpretation_note"]]
    if issues:
        lines += ["", "Issues:"] + [f"- {issue}" for issue in issues]
    (args.output_dir / "public_hospital_funding_latest.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("\n".join(lines))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
