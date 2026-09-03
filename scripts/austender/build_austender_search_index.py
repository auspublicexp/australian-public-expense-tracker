"""Build compact, period-based search files for the APET AusTender website."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from validation_report import write_validation_report


PROJECT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MASTER_FILE = Path(
    os.environ.get(
        "APET_AUSTENDER_MASTER_FILE",
        PROJECT_DIR / "output" / "austender" / "austender_master.csv",
    )
)
DEFAULT_WEBSITE_DIR = Path(
    os.environ.get(
        "APET_AUSTENDER_SEARCH_DIR",
        PROJECT_DIR / "website" / "public_html" / "austender",
    )
)
EXPORT_START_DATE = pd.Timestamp("2025-01-01")

REQUIRED_COLUMNS = [
    "Agency",
    "CN ID",
    "Parent CN ID",
    "Publish Date",
    "Amendment Publish Date",
    "Start Date",
    "End Date",
    "Value",
    "Description",
    "Category",
    "Procurement Method",
    "Supplier Name",
    "FY Quarter",
    "Root CN ID",
    "Record Date",
]

MONTH_RANGES = {
    "Q1": "July to September",
    "Q2": "October to December",
    "Q3": "January to March",
    "Q4": "April to June",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master-file", type=Path, default=DEFAULT_MASTER_FILE)
    parser.add_argument("--website-dir", type=Path, default=DEFAULT_WEBSITE_DIR)
    return parser.parse_args()


def quarter_end(period: str) -> pd.Timestamp:
    match = re.fullmatch(r"FY(\d{4})-\d{2}_(Q[1-4])", period)
    if not match:
        raise ValueError(f"Invalid financial-year quarter: {period}")
    start_year = int(match.group(1))
    end_year = start_year + 1
    dates = {
        "Q1": f"{start_year}-09-30",
        "Q2": f"{start_year}-12-31",
        "Q3": f"{end_year}-03-31",
        "Q4": f"{end_year}-06-30",
    }
    return pd.Timestamp(dates[match.group(2)]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)


def period_label(period: str) -> str:
    fy_label, quarter = period.split("_")
    return f"{fy_label} {quarter} — {MONTH_RANGES[quarter]}"


def clean_supplier_name(value: object) -> str:
    if pd.isna(value):
        return "Not stated"
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or "Not stated"


def text_value(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def date_value(value: object) -> str:
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).date().isoformat()


def resolve_versions_as_at(data: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    resolved = data.copy()
    resolved["Root CN ID"] = resolved["Root CN ID"].where(
        resolved["Root CN ID"].notna(),
        resolved["Parent CN ID"].where(resolved["Parent CN ID"].notna(), resolved["CN ID"]),
    )
    resolved["Record Date"] = resolved["Record Date"].where(
        resolved["Record Date"].notna(),
        resolved["Amendment Publish Date"].where(
            resolved["Amendment Publish Date"].notna(),
            resolved["Publish Date"],
        ),
    )
    resolved = resolved[resolved["Record Date"].notna() & (resolved["Record Date"] <= cutoff)]
    return (
        resolved.sort_values(["Root CN ID", "Record Date", "CN ID"], na_position="first")
        .drop_duplicates("Root CN ID", keep="last")
        .reset_index(drop=True)
    )


def build_search_index(master_file: Path, website_dir: Path) -> dict:
    if not master_file.is_file():
        raise FileNotFoundError(f"AusTender master file not found: {master_file}")

    data = pd.read_csv(master_file, low_memory=False)
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(f"AusTender master file is missing columns: {missing}")

    for column in [
        "Publish Date",
        "Amendment Publish Date",
        "Start Date",
        "End Date",
        "Record Date",
    ]:
        data[column] = pd.to_datetime(data[column], errors="coerce")
    data["Value"] = pd.to_numeric(data["Value"], errors="coerce").fillna(0)

    periods = sorted(
        str(value)
        for value in data["FY Quarter"].dropna().unique()
        if re.fullmatch(r"FY\d{4}-\d{2}_Q[1-4]", str(value))
        and quarter_end(str(value)) >= EXPORT_START_DATE
    )

    search_dir = website_dir / "search-data"
    search_dir.mkdir(parents=True, exist_ok=True)
    period_metadata = []
    all_agencies: set[str] = set()
    total_records = 0

    for period in periods:
        period_rows = data[data["FY Quarter"].astype("string") == period].copy()
        records_frame = resolve_versions_as_at(period_rows, quarter_end(period))
        records = []

        for row in records_frame.itertuples(index=False, name=None):
            values = dict(zip(records_frame.columns, row))
            cn_id = text_value(values["CN ID"])
            supplier = clean_supplier_name(values["Supplier Name"])
            agency = text_value(values["Agency"])
            if agency:
                all_agencies.add(agency)

            records.append(
                {
                    "cn_id": cn_id,
                    "root_cn_id": text_value(values["Root CN ID"]),
                    "supplier": supplier,
                    "agency": agency,
                    "description": text_value(values["Description"]),
                    "value": round(float(values["Value"]), 2),
                    "publish_date": date_value(values["Publish Date"]),
                    "start_date": date_value(values["Start Date"]),
                    "end_date": date_value(values["End Date"]),
                    "category": text_value(values["Category"]),
                    "procurement_method": text_value(values["Procurement Method"]),
                    "period": period,
                    "apet_url": f"/austender/?period={period}",
                    "austender_url": (
                        "https://www.tenders.gov.au/cn/search"
                        f"?KeywordTypeSearch=AllWord&Keyword={quote_plus(cn_id)}"
                    ),
                }
            )

        records.sort(key=lambda item: (-item["value"], item["supplier"].casefold(), item["cn_id"]))
        file_name = f"{period}.json"
        (search_dir / file_name).write_text(
            json.dumps(records, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        period_metadata.append(
            {
                "key": period,
                "label": period_label(period),
                "file": f"/austender/search-data/{file_name}",
                "records": len(records),
            }
        )
        total_records += len(records)
        print(f"Wrote {len(records):,} searchable contracts for {period}")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": master_file.name,
        "total_records": total_records,
        "periods": period_metadata,
        "agencies": sorted(all_agencies, key=str.casefold),
        "notes": [
            "Values are reported contract notice values, not payments.",
            "Contract amendments are resolved as at the end of each reporting quarter.",
            "AusTender links open an official contract-notice search for the selected CN ID.",
        ],
    }
    manifest_path = website_dir / "austender-search-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote manifest: {manifest_path}")
    print(f"Total searchable contract records: {total_records:,}")
    publish_dates = pd.to_datetime(data["Publish Date"], errors="coerce").dropna()
    write_validation_report(
        "austender",
        {
            "master_file": master_file,
            "normalized_master_records": int(len(data)),
            "searchable_contract_records": total_records,
            "earliest_publish_date": (
                publish_dates.min().date().isoformat() if not publish_dates.empty else "none"
            ),
            "latest_publish_date": (
                publish_dates.max().date().isoformat() if not publish_dates.empty else "none"
            ),
            "reporting_periods": len(period_metadata),
            "agencies_indexed": len(all_agencies),
            "search_manifest": manifest_path,
        },
        checks=[
            "All required normalized AusTender columns were present.",
            "Contract values and reporting dates were parsed before indexing.",
            "Contract amendments were resolved as at each reporting-period end.",
        ],
    )
    return manifest


def main() -> None:
    args = parse_args()
    build_search_index(args.master_file, args.website_dir)


if __name__ == "__main__":
    main()

