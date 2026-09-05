"""Validate normalized DFAT foreign-aid transactions and write latest-run reports."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", type=Path, default=project_root / "data/dfat_foreign_aid/normalized/dfat_aid_transactions.csv")
    parser.add_argument("--manifest", type=Path, default=project_root / "data/dfat_foreign_aid/raw/manifest.json")
    parser.add_argument("--output-dir", type=Path, default=project_root / "output/validation")
    args = parser.parse_args()
    with args.data_file.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    issues = []
    required = ("activity_id", "transaction_type_code", "transaction_date", "financial_year", "value_dollars", "currency")
    missing = {field: sum(not row[field].strip() for row in rows) for field in required}
    if any(missing.values()):
        issues.append("One or more required normalized fields are missing")
    currencies = Counter(row["currency"] or "(missing)" for row in rows)
    if set(currencies) != {"AUD"}:
        issues.append(f"Expected only AUD transactions; found {dict(currencies)}")
    types = Counter(row["transaction_type_code"] for row in rows)
    if "3" not in types:
        issues.append("No IATI disbursement transactions (type 3) were found")
    annual = defaultdict(float)
    negative_disbursements = 0
    for row in rows:
        try:
            amount = float(row["value_dollars"])
        except ValueError:
            issues.append(f"Invalid monetary value in activity {row['activity_id']}")
            continue
        if row["transaction_type_code"] == "3":
            annual[row["financial_year"]] += amount
            negative_disbursements += amount < 0
    report = {
        "status": "PASS" if not issues else "FAIL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_resource_last_modified": manifest.get("resource_last_modified"),
        "normalized_transactions": len(rows),
        "activities": len({row["activity_id"] for row in rows}),
        "financial_years": sorted({row["financial_year"] for row in rows}),
        "transaction_type_counts": dict(sorted(types.items())),
        "currency_counts": dict(sorted(currencies.items())),
        "missing_required_fields": missing,
        "negative_disbursement_rows": negative_disbursements,
        "annual_disbursement_dollars": dict(sorted(annual.items())),
        "issues": issues,
        "interpretation_note": (
            "Charts use IATI transaction type 3 (disbursements), not commitments (type 2), "
            "budgets or whole-of-project investment values. Negative rows are retained because "
            "DFAT uses them for adjustments and returned funds."
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "dfat_foreign_aid_latest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"DFAT FOREIGN AID VALIDATION: {report['status']}",
        f"Activities: {report['activities']:,}",
        f"Normalized transactions: {len(rows):,}",
        f"Transaction types: {dict(types)}",
        f"Negative disbursement adjustments retained: {negative_disbursements:,}",
        "", "Reported disbursements by financial year:",
    ] + [f"- {fy}: ${amount:,.0f}" for fy, amount in sorted(annual.items())]
    lines += ["", report["interpretation_note"]]
    if issues:
        lines += ["", "Issues:"] + [f"- {issue}" for issue in issues]
    text = "\n".join(lines) + "\n"
    (args.output_dir / "dfat_foreign_aid_latest.txt").write_text(text, encoding="utf-8")
    print(text)
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
