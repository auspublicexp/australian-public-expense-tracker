"""Build compact browser-ready indexes for the APET hospital-funding explorer."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd

MONTH_NUMBER = {
    "July": 1, "August": 2, "September": 3, "October": 4,
    "November": 5, "December": 6, "January": 7, "February": 8,
    "March": 9, "April": 10, "May": 11, "June": 12,
}


def compact_rows(frame: pd.DataFrame, columns: list[str]) -> list[list[object]]:
    result = []
    for row in frame[columns].itertuples(index=False, name=None):
        result.append([int(value) if isinstance(value, (int, float)) and column == "payment_dollars" else value
                       for column, value in zip(columns, row)])
    return result


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=project_root / "data/public_hospital_funding/normalized")
    parser.add_argument("--output-dir", type=Path, default=project_root / "output/public_hospital_funding/explorer-data")
    parser.add_argument("--website-dir", type=Path, default=project_root / "website/public_html/hospital-funding/explorer-data")
    args = parser.parse_args()

    states = pd.read_csv(args.data_dir / "monthly_payments_by_state.csv")
    categories = pd.read_csv(args.data_dir / "monthly_payments_by_service_category.csv")
    for frame in (states, categories):
        frame["financial_month"] = frame["month"].map(MONTH_NUMBER)
        if frame["financial_month"].isna().any():
            raise ValueError("An unexpected month name was found")
        frame["quarter"] = "Q" + (((frame["financial_month"] - 1) // 3) + 1).astype(str)
        frame["payment_dollars"] = pd.to_numeric(frame["payment_dollars"], errors="raise").round().astype("int64")

    state_columns = ["financial_year", "financial_month", "month", "quarter", "state_territory", "payment_dollars"]
    category_columns = state_columns[:-1] + ["funding_method", "service_category", "payment_dollars"]
    years = sorted(states["financial_year"].unique())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.website_dir.mkdir(parents=True, exist_ok=True)

    periods = []
    for year in years:
        filename = f"{year}.json"
        payload = {
            "state_rows": compact_rows(states[states.financial_year == year].sort_values(["financial_month", "state_territory"]), state_columns),
            "category_rows": compact_rows(categories[categories.financial_year == year].sort_values(["financial_month", "state_territory", "funding_method", "service_category"]), category_columns),
        }
        output = args.output_dir / filename
        output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        shutil.copy2(output, args.website_dir / filename)
        periods.append({"financial_year": year, "file": filename,
                        "state_records": len(payload["state_rows"]), "category_records": len(payload["category_rows"])})

    manifest = {
        "state_columns": state_columns,
        "category_columns": category_columns,
        "periods": periods,
        "jurisdictions": sorted(states["state_territory"].unique()),
        "funding_methods": sorted(categories["funding_method"].unique()),
        "service_categories": sorted(categories["service_category"].unique()),
        "state_record_count": int(len(states)),
        "category_record_count": int(len(categories)),
        "negative_category_adjustment_count": int((categories["payment_dollars"] < 0).sum()),
        "notes": "State totals and service-category components are separate series and must not be added together.",
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copy2(manifest_path, args.website_dir / "manifest.json")
    print(f"Built hospital explorer index: {len(states):,} state-month and {len(categories):,} category-month records")
    print(f"Website files: {args.website_dir}")


if __name__ == "__main__":
    main()
