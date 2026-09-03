"""Build compact GrantConnect search files for the APET website."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from validation_report import write_validation_report

PROJECT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = Path(os.getenv("APET_GRANTCONNECT_DATA_DIR", PROJECT_DIR / "data" / "grantconnect"))
DEFAULT_WEB_DIR = Path(os.getenv("APET_GRANTCONNECT_SEARCH_DIR", PROJECT_DIR / "website" / "public_html" / "grantconnect"))
PATTERN = "grantconnect_FY????-??_Q?_????-??*.xlsx"
REQUIRED = ["GA ID", "Grant Activity", "Agency", "Category", "Recipient Name", "GO ID", "Publish Date", "Value (AUD)"]


def read_export(path: Path) -> pd.DataFrame:
    preview = pd.read_excel(path, header=None, nrows=40)
    header = next((i for i, row in preview.iterrows() if {"GA ID", "Grant Activity", "Publish Date", "Value (AUD)"}.issubset({str(v).strip() for v in row.dropna()})), None)
    if header is None:
        raise ValueError(f"Could not find the GrantConnect header row in {path.name}")
    frame = pd.read_excel(path, header=header)
    frame.columns = [str(c).strip() for c in frame.columns]
    missing = [c for c in REQUIRED if c not in frame.columns]
    if missing:
        raise ValueError(f"{path.name} is missing columns: {', '.join(missing)}")
    return frame


def fy_quarter(value: pd.Timestamp) -> tuple[str, int]:
    start = value.year if value.month >= 7 else value.year - 1
    quarter = ((value.month - 7) % 12) // 3 + 1
    return f"FY{start}-{str(start + 1)[-2:]}", quarter


def clean(value: object) -> str:
    return "" if pd.isna(value) else " ".join(str(value).split())


def iso_date(value: object) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    return "" if pd.isna(parsed) else parsed.strftime("%Y-%m-%d")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--website-dir", type=Path, default=DEFAULT_WEB_DIR)
    args = parser.parse_args()

    files = sorted(args.data_dir.glob(PATTERN))
    if not files:
        raise FileNotFoundError(f"No GrantConnect files matching {PATTERN} in {args.data_dir}")
    data = pd.concat([read_export(path) for path in files], ignore_index=True)
    data["Publish Date"] = pd.to_datetime(data["Publish Date"], errors="coerce")
    data["Value (AUD)"] = pd.to_numeric(data["Value (AUD)"], errors="coerce")
    data = data.dropna(subset=["GA ID", "Publish Date", "Value (AUD)"]).drop_duplicates()
    duplicates = data["GA ID"].astype(str).str.strip().duplicated(keep=False)
    if duplicates.any():
        ids = sorted(data.loc[duplicates, "GA ID"].astype(str).unique())[:10]
        raise ValueError(f"Repeated GA IDs remain after exact de-duplication: {', '.join(ids)}")

    output = args.website_dir / "search-data"
    output.mkdir(parents=True, exist_ok=True)
    for old in output.glob("FY????-??_Q?.json"):
        old.unlink()

    periods: dict[str, list[dict]] = {}
    agencies, categories = set(), set()
    for _, row in data.iterrows():
        fy, quarter = fy_quarter(row["Publish Date"])
        key = f"{fy}_Q{quarter}"
        agency, category = clean(row["Agency"]), clean(row["Category"])
        agencies.add(agency) if agency else None
        categories.add(category) if category else None
        periods.setdefault(key, []).append({
            "ga": clean(row["GA ID"]), "go": clean(row["GO ID"]),
            "recipient": clean(row["Recipient Name"]), "activity": clean(row["Grant Activity"]),
            "agency": agency, "category": category, "value": round(float(row["Value (AUD)"]), 2),
            "published": iso_date(row["Publish Date"]), "start": iso_date(row.get("Start Date")),
            "end": iso_date(row.get("End Date")), "period": key,
        })

    quarter_items = []
    for key in sorted(periods):
        records = sorted(periods[key], key=lambda item: item["value"], reverse=True)
        (output / f"{key}.json").write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        fy, q = key.rsplit("_Q", 1)
        quarter_items.append({"key": key, "label": f"{fy} Q{q}", "financial_year": fy, "file": f"search-data/{key}.json", "records": len(records)})

    by_fy: dict[str, set[str]] = {}
    for item in quarter_items:
        by_fy.setdefault(item["financial_year"], set()).add(item["key"][-2:])
    annual = [{"key": fy, "label": fy, "quarters": [f"{fy}_Q{i}" for i in range(1, 5)]} for fy, qs in sorted(by_fy.items()) if qs == {"Q1", "Q2", "Q3", "Q4"}]
    manifest = {"generated_at": datetime.now(timezone.utc).isoformat(), "total_records": int(len(data)), "quarters": quarter_items, "annual": annual, "agencies": sorted(agencies), "categories": sorted(categories)}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Built GrantConnect search index: {len(data):,} awards across {len(periods)} quarters")
    write_validation_report(
        "grantconnect",
        {
            "source_files": len(files),
            "validated_awards": int(len(data)),
            "earliest_publish_date": data["Publish Date"].min().date().isoformat(),
            "latest_publish_date": data["Publish Date"].max().date().isoformat(),
            "quarters_indexed": len(periods),
            "complete_financial_years": len(annual),
            "search_index": output / "manifest.json",
        },
        checks=[
            "Required GrantConnect columns were present in every source file.",
            "Rows without an award ID, publish date or numeric value were excluded.",
            "No repeated GA IDs remained after exact de-duplication.",
        ],
    )


if __name__ == "__main__":
    main()
