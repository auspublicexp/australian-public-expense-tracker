"""Build the compact client-side data index for the APET MBS explorer."""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SUM_COLUMNS = ["services", "benefits_dollars", "bulk_billed_services", "patient_billed_services"]
COLUMNS = ["period_type", "period", "sort", "state", "service_type", *SUM_COLUMNS,
           "average_benefit_per_service", "bulk_billing_rate", "url"]


def finish(frame: pd.DataFrame, period_type: str) -> pd.DataFrame:
    frame = frame.copy()
    frame["period_type"] = period_type
    frame["average_benefit_per_service"] = frame.benefits_dollars.div(frame.services).fillna(0)
    frame["bulk_billing_rate"] = frame.bulk_billed_services.div(frame.services).fillna(0) * 100
    suffix = "_annual" if period_type == "annual" else ""
    page = "annual" if period_type == "annual" else "quarter"
    frame["url"] = frame.period.map(lambda value: f"/mbs/{page}.php?period={value}{suffix}")
    return frame[COLUMNS]


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", type=Path, default=project_root / "data/mbs/normalized/mbs_quarterly.csv")
    parser.add_argument("--output-file", type=Path, default=project_root / "output/mbs/mbs-explorer.json")
    parser.add_argument("--website-file", type=Path, default=project_root / "website/public_html/charts/mbs/mbs-explorer.json")
    args = parser.parse_args()
    data = pd.read_csv(args.data_file)

    quarterly = data.rename(columns={"financial_quarter": "period"})
    quarterly["sort"] = quarterly.quarter_end.str.replace("-", "", regex=False).astype(int)
    quarterly = finish(quarterly, "quarterly")

    complete = data.groupby("financial_year").financial_quarter.nunique()
    complete_years = complete[complete == 4].index
    annual = data[data.financial_year.isin(complete_years)].groupby(
        ["financial_year", "state", "service_type"], as_index=False
    )[SUM_COLUMNS].sum().rename(columns={"financial_year": "period"})
    annual["sort"] = annual.period.str.extract(r"FY(\d{4})")[0].astype(int)
    annual = finish(annual, "annual")
    combined = pd.concat([annual, quarterly], ignore_index=True).sort_values(
        ["period_type", "sort", "state", "service_type"]
    )
    combined = combined.round({"benefits_dollars": 2, "average_benefit_per_service": 2,
                               "bulk_billing_rate": 2})
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "columns": COLUMNS,
        "records": combined.where(pd.notna(combined), None).values.tolist(),
        "states": sorted(data.state.unique()),
        "service_types": sorted(data.service_type.unique()),
        "periods": {
            "annual": sorted(annual.period.unique()),
            "quarterly": sorted(quarterly.period.unique()),
        },
    }
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    args.website_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.output_file, args.website_file)
    print(f"Saved {len(combined):,} explorer records: {args.output_file}")
    print(f"Copied website index to: {args.website_file}")


if __name__ == "__main__":
    main()
