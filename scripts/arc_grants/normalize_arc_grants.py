"""Normalize ARC NCGP Grants API sample pages into one project-level CSV."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

FIELDS = [
    "arc_api_id", "project_code", "scheme_code", "scheme_name", "program_name", "scheme_round",
    "submission_year", "round_number", "funding_commencement_year", "administering_organisation",
    "announcement_administering_organisation", "grant_summary", "national_interest_test_statement",
    "lead_investigator", "announced_funding_dollars", "current_funding_dollars",
    "funding_variation_dollars", "grant_status", "primary_field_of_research",
    "anticipated_end_date", "investigators", "lief_register", "official_record_url",
]


def clean_amount(value):
    if value in (None, ""):
        return ""
    return round(float(value), 2)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=project_root / "data" / "arc_grants" / "raw")
    parser.add_argument("--output-dir", type=Path, default=project_root / "data" / "arc_grants" / "normalized")
    args = parser.parse_args()
    rows = []
    for path in sorted(args.input_dir.glob("arc_ncgp_grants_page_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        for item in payload.get("data", []):
            attributes = item.get("attributes", {})
            scheme = attributes.get("scheme-information") or {}
            announced = clean_amount(attributes.get("announced-funding-amount"))
            current = clean_amount(attributes.get("current-funding-amount"))
            rows.append({
                "arc_api_id": item.get("id", ""),
                "project_code": attributes.get("code", ""),
                "scheme_code": str(scheme.get("schemeCode", "")).strip(),
                "scheme_name": attributes.get("scheme-name", ""),
                "program_name": scheme.get("program", ""),
                "scheme_round": scheme.get("schemeRound", ""),
                "submission_year": scheme.get("submissionYear", ""),
                "round_number": scheme.get("roundNumber", ""),
                "funding_commencement_year": attributes.get("funding-commencement-year", ""),
                "administering_organisation": attributes.get("current-admin-organisation", ""),
                "announcement_administering_organisation": attributes.get("announcement-admin-organisation", ""),
                "grant_summary": attributes.get("grant-summary", ""),
                "national_interest_test_statement": attributes.get("national-interest-test-statement", ""),
                "lead_investigator": attributes.get("lead-investigator", ""),
                "announced_funding_dollars": announced,
                "current_funding_dollars": current,
                "funding_variation_dollars": round(current - announced, 2) if current != "" and announced != "" else "",
                "grant_status": attributes.get("grant-status", ""),
                "primary_field_of_research": attributes.get("primary-field-of-research", ""),
                "anticipated_end_date": attributes.get("anticipated-end-date", ""),
                "investigators": attributes.get("investigators", ""),
                "lief_register": json.dumps(attributes.get("lief-register") or [], ensure_ascii=False),
                "official_record_url": f"https://dataportal.arc.gov.au/NCGP/Web/Grant/Grant/{attributes.get('code', '')}",
            })
    if not rows:
        raise FileNotFoundError(f"No ARC raw page files found in {args.input_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.output_dir / "arc_grants_projects.csv"
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader(); writer.writerows(rows)
    print(f"Saved {len(rows):,} normalized ARC projects: {destination}")


if __name__ == "__main__":
    main()


