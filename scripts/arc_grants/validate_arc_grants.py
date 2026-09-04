"""Validate normalized ARC grants and write JSON/text reports."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", type=Path, default=project_root / "data" / "arc_grants" / "normalized" / "arc_grants_projects.csv")
    parser.add_argument("--manifest", type=Path, default=project_root / "data" / "arc_grants" / "raw" / "manifest.json")
    parser.add_argument("--output-dir", type=Path, default=project_root / "output" / "validation")
    args = parser.parse_args()
    with args.data_file.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    issues = []
    codes = [row["project_code"].strip() for row in rows]
    ids = [row["arc_api_id"].strip() for row in rows]
    duplicate_codes = sum(count - 1 for count in Counter(codes).values() if count > 1 and codes)
    duplicate_ids = sum(count - 1 for count in Counter(ids).values() if count > 1 and ids)
    if len(rows) != manifest.get("records_downloaded"):
        issues.append("Normalized row count does not match the raw manifest count")
    if manifest.get("complete_collection") and len(rows) != manifest.get("api_reported_total_records"):
        issues.append("Complete download row count does not match the API-reported total")
    if duplicate_codes: issues.append(f"Found {duplicate_codes} duplicate project codes")
    if duplicate_ids: issues.append(f"Found {duplicate_ids} duplicate ARC API IDs")
    missing = {field: sum(not row[field].strip() for row in rows) for field in (
        "project_code", "scheme_name", "funding_commencement_year",
        "administering_organisation", "current_funding_dollars")}
    negative = sum(float(row["current_funding_dollars"]) < 0 for row in rows if row["current_funding_dollars"])
    if negative: issues.append(f"Found {negative} negative current-funding values")
    statuses = Counter(row["grant_status"] or "(missing)" for row in rows)
    report = {
        "status": "PASS" if not issues else "FAIL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "complete_collection": bool(manifest.get("complete_collection")),
        "normalized_rows": len(rows),
        "api_reported_total_records": manifest.get("api_reported_total_records"),
        "pages_downloaded": manifest.get("requested_pages"),
        "duplicate_project_codes": duplicate_codes,
        "duplicate_api_ids": duplicate_ids,
        "missing_key_fields": missing,
        "negative_current_funding_rows": negative,
        "grant_status_counts": dict(sorted(statuses.items())),
        "issues": issues,
        "interpretation_note": (
            "Amounts are ARC whole-of-project grant allocations, not cash paid during the "
            "funding commencement year. Current funding can include post-award variations."
        ),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "arc_grants_latest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"ARC GRANTS VALIDATION: {report['status']}",
        f"Normalized rows: {len(rows):,}",
        f"API-reported complete collection: {manifest.get('api_reported_total_records', 'unknown'):,}",
        f"Duplicate project codes: {duplicate_codes:,}",
        f"Duplicate ARC API IDs: {duplicate_ids:,}", "", "Missing key fields:",
    ] + [f"- {key}: {value:,}" for key, value in missing.items()]
    lines += ["", report["interpretation_note"]]
    if issues: lines += ["", "Issues:"] + [f"- {issue}" for issue in issues]
    text = "\n".join(lines) + "\n"
    (args.output_dir / "arc_grants_latest.txt").write_text(text, encoding="utf-8")
    print(text)
    if issues: raise SystemExit(1)


if __name__ == "__main__":
    main()


