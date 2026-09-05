"""Build year-partitioned ARC grant search files for the APET website."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


COLUMNS = [
    "project_code", "scheme_name", "program_name", "funding_commencement_year",
    "administering_organisation", "grant_summary", "national_interest_test_statement",
    "lead_investigator", "current_funding_dollars", "grant_status",
    "primary_field_of_research", "investigators", "official_record_url",
]


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).split())


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", type=Path, default=project_root / "data/arc_grants/normalized/arc_grants_projects.csv")
    parser.add_argument("--output-dir", type=Path, default=project_root / "output/arc_grants/search-data")
    parser.add_argument("--website-dir", type=Path, default=project_root / "website/public_html/arc-grants/search-data")
    args = parser.parse_args()

    data = pd.read_csv(args.input_file, usecols=COLUMNS, low_memory=False)
    data["funding_commencement_year"] = pd.to_numeric(data["funding_commencement_year"], errors="coerce")
    data["current_funding_dollars"] = pd.to_numeric(data["current_funding_dollars"], errors="coerce").fillna(0)
    data = data.dropna(subset=["funding_commencement_year"]).copy()
    data["funding_commencement_year"] = data["funding_commencement_year"].astype(int)
    for column in COLUMNS:
        if column not in {"funding_commencement_year", "current_funding_dollars"}:
            data[column] = data[column].map(clean_text)

    manifest = {
        "columns": COLUMNS,
        "years": [],
        "programs": sorted(value for value in data["program_name"].unique() if value),
        "schemes": sorted(value for value in data["scheme_name"].unique() if value),
        "statuses": sorted(value for value in data["grant_status"].unique() if value),
        "record_count": int(len(data)),
        "notes": "Whole-of-project ARC allocations; not cash paid during the commencement year.",
    }

    for destination in (args.output_dir, args.website_dir):
        destination.mkdir(parents=True, exist_ok=True)
        for old_file in destination.glob("CY????.json"):
            old_file.unlink()

    for year, rows in data.sort_values(["funding_commencement_year", "current_funding_dollars"], ascending=[True, False]).groupby("funding_commencement_year"):
        records = rows[COLUMNS].values.tolist()
        filename = f"CY{year}.json"
        payload = json.dumps(records, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for destination in (args.output_dir, args.website_dir):
            (destination / filename).write_text(payload, encoding="utf-8")
        manifest["years"].append({"year": int(year), "file": filename, "records": len(records)})

    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    for destination in (args.output_dir, args.website_dir):
        (destination / "manifest.json").write_text(manifest_text, encoding="utf-8")
    print(f"Built ARC search index: {len(data):,} projects across {len(manifest['years'])} years")
    print(f"Website files: {args.website_dir}")


if __name__ == "__main__":
    main()
