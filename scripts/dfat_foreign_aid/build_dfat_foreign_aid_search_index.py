"""Build financial-year search files for APET's DFAT foreign-aid section."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


OUTPUT_COLUMNS = [
    "activity_id", "activity_title", "activity_description", "activity_status",
    "activity_start_date", "activity_end_date", "implementing_organisation",
    "financial_year", "disbursement_dollars", "recipient_country",
    "recipient_region", "sector", "sector_category", "source_dataset_url",
]
STATUS_LABELS = {
    "1": "Pipeline/identification", "2": "Implementation", "3": "Finalisation",
    "4": "Closed", "5": "Cancelled", "6": "Suspended",
}


def clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).split())


def join_unique(values: pd.Series) -> str:
    return " | ".join(dict.fromkeys(clean(value) for value in values if clean(value)))


def first_text(values: pd.Series) -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return ""


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", type=Path, default=project_root / "data/dfat_foreign_aid/normalized/dfat_aid_transactions.csv")
    parser.add_argument("--output-dir", type=Path, default=project_root / "output/foreign_aid/search-data")
    parser.add_argument("--website-dir", type=Path, default=project_root / "website/public_html/foreign-aid/search-data")
    args = parser.parse_args()

    data = pd.read_csv(args.input_file, dtype={"transaction_type_code": str, "activity_status_code": str}, keep_default_na=False)
    data = data[data["transaction_type_code"] == "3"].copy()
    data["value_dollars"] = pd.to_numeric(data["value_dollars"], errors="raise")
    if data.empty:
        raise ValueError("No IATI type-3 disbursements were found")

    grouped = data.groupby(["financial_year", "activity_id"], as_index=False).agg(
        activity_title=("activity_title", first_text),
        activity_description=("activity_description", first_text),
        activity_status_code=("activity_status_code", first_text),
        activity_start_date=("activity_start_date", first_text),
        activity_end_date=("activity_end_date", first_text),
        implementing_organisation=("implementing_organisation", join_unique),
        disbursement_dollars=("value_dollars", "sum"),
        recipient_country=("recipient_country", join_unique),
        recipient_region=("recipient_region", join_unique),
        sector=("sector", join_unique),
        sector_category=("sector_category", join_unique),
        source_dataset_url=("source_dataset_url", first_text),
    )
    grouped["activity_status"] = grouped["activity_status_code"].map(STATUS_LABELS).fillna(grouped["activity_status_code"])
    grouped = grouped.drop(columns="activity_status_code")[OUTPUT_COLUMNS]

    manifest = {
        "columns": OUTPUT_COLUMNS,
        "periods": [],
        "countries": sorted({item for values in grouped["recipient_country"] for item in values.split(" | ") if item}),
        "regions": sorted({item for values in grouped["recipient_region"] for item in values.split(" | ") if item}),
        "sector_categories": sorted({item for values in grouped["sector_category"] for item in values.split(" | ") if item}),
        "statuses": sorted(value for value in grouped["activity_status"].unique() if value),
        "record_count": int(len(grouped)),
        "transaction_count": int(len(data)),
        "negative_adjustment_count": int((data["value_dollars"] < 0).sum()),
        "notes": "Aggregated IATI type-3 disbursements by activity and Australian financial year.",
    }
    for destination in (args.output_dir, args.website_dir):
        destination.mkdir(parents=True, exist_ok=True)
        for old_file in destination.glob("FY????-??.json"):
            old_file.unlink()

    for financial_year, rows in grouped.sort_values(["financial_year", "disbursement_dollars"], ascending=[True, False]).groupby("financial_year"):
        filename = f"{financial_year}.json"
        records = rows[OUTPUT_COLUMNS].values.tolist()
        payload = json.dumps(records, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for destination in (args.output_dir, args.website_dir):
            (destination / filename).write_text(payload, encoding="utf-8")
        manifest["periods"].append({"financial_year": financial_year, "file": filename, "records": len(records)})

    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    for destination in (args.output_dir, args.website_dir):
        (destination / "manifest.json").write_text(manifest_text, encoding="utf-8")
    print(f"Built DFAT search index: {len(grouped):,} activity-year records from {len(data):,} disbursements")
    print(f"Website files: {args.website_dir}")


if __name__ == "__main__":
    main()
