"""Build the small JSON dataset used by the APET ABS GFS topic explorer."""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from validation_report import write_validation_report

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHART_ROOT = Path(os.getenv(
    "APET_ABS_GFS_CHART_ROOT",
    PROJECT_ROOT / "website" / "public_html" / "charts" / "abs_gfs",
))
OUTPUT_PATH = Path(os.getenv(
    "APET_ABS_GFS_EXPLORER_INDEX",
    PROJECT_ROOT / "website" / "public_html" / "abs-gfs" / "abs-gfs-explorer.json",
))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    if not CHART_ROOT.is_dir():
        raise FileNotFoundError(f"ABS GFS chart folder not found: {CHART_ROOT}")

    records: list[dict[str, object]] = []
    purposes: set[str] = set()
    levels: set[str] = set()
    years: list[dict[str, object]] = []

    folders = sorted(
        path for path in CHART_ROOT.iterdir()
        if path.is_dir() and re.fullmatch(r"FY\d{4}-\d{2}_annual", path.name)
    )
    for folder in folders:
        financial_year = folder.name.removesuffix("_annual")
        start_year = int(financial_year[2:6])
        years.append({"key": financial_year, "label": financial_year, "sort": start_year})
        annual_url = f"/abs-gfs/annual.php?period={folder.name}"

        purpose_values = {
            row["purpose"]: float(row["value_millions"])
            for row in read_rows(folder / "02_expenses_by_purpose_data.csv")
        }
        purpose_total = sum(purpose_values.values())
        for purpose, value in purpose_values.items():
            purposes.add(purpose)
            records.append({
                "topic_type": "purpose", "topic": purpose, "financial_year": financial_year,
                "sort": start_year, "value_millions": value,
                "share_percent": (value / purpose_total * 100) if purpose_total else None,
                "url": annual_url,
            })

        level_rows = read_rows(folder / "07_expenses_by_government_level_data.csv")
        level_total = sum(float(row["value_millions"]) for row in level_rows)
        for row in level_rows:
            level = row["government_level"]
            value = float(row["value_millions"])
            levels.add(level)
            records.append({
                "topic_type": "level", "topic": level, "financial_year": financial_year,
                "sort": start_year, "value_millions": value,
                "share_percent": (value / level_total * 100) if level_total else None,
                "url": annual_url,
            })

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "basis": "Nominal current-price, original-series ABS GFS values.",
        "years": years, "purposes": sorted(purposes), "government_levels": sorted(levels),
        "records": records,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Saved {len(records)} ABS GFS explorer observations to {OUTPUT_PATH}")
    write_validation_report(
        "abs_gfs",
        {
            "annual_financial_years": len(years),
            "earliest_financial_year": years[0]["key"] if years else "none",
            "latest_financial_year": years[-1]["key"] if years else "none",
            "expenditure_purposes": len(purposes),
            "government_levels": len(levels),
            "explorer_observations": len(records),
            "explorer_index": OUTPUT_PATH,
        },
        checks=[
            "Each annual chart folder contained purpose and government-level data.",
            "Purpose and government-level shares were recalculated from reported values.",
            "Values are labelled as nominal current-price ABS GFS figures.",
        ],
    )


if __name__ == "__main__":
    main()
