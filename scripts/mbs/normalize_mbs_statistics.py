"""Normalize official quarterly Medicare statistics for APET."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

RENAME = {
    "Quarter": "source_quarter",
    "State": "state",
    "Broad Type of Service": "service_type",
    "Services": "services",
    "Benefits ($)": "benefits_dollars",
    "Bulk Billed Services": "bulk_billed_services",
    "Patient Billed Services": "patient_billed_services",
    "MBS Bulk Billing Rate (%)": "bulk_billing_rate",
    "Fee Charged ($)": "fees_charged_dollars",
}
STATE_NAMES = {"NSW": "New South Wales", "Vic": "Victoria", "Qld": "Queensland",
               "SA": "South Australia", "WA": "Western Australia", "Tas": "Tasmania",
               "NT": "Northern Territory", "ACT": "Australian Capital Territory",
               "Unk": "Unknown", "Australia": "Australia"}


def quarter_fields(value: str) -> tuple[str, str, str]:
    match = re.match(r"(\d{4})-(\d{2}) Q([1-4])", str(value))
    if not match:
        raise ValueError(f"Unrecognised Medicare quarter: {value}")
    start, end, quarter = match.groups()
    end_year = int(start) + 1
    month_day = {"1": "09-30", "2": "12-31", "3": "03-31", "4": "06-30"}[quarter]
    year = int(start) if quarter in {"1", "2"} else end_year
    return f"FY{start}-{end}", f"FY{start}-{end}_Q{quarter}", f"{year}-{month_day}"


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", type=Path)
    parser.add_argument("--raw-dir", type=Path, default=project_root / "data/mbs/raw")
    parser.add_argument("--output-dir", type=Path, default=project_root / "data/mbs/normalized")
    args = parser.parse_args()
    candidates = sorted(args.raw_dir.glob("*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    source = args.input_file or (candidates[0] if candidates else None)
    if source is None or not source.exists():
        raise FileNotFoundError("No Medicare workbook found. Run fetch_mbs_statistics.py first.")

    data = pd.read_excel(source, sheet_name="All Services", header=4)
    missing = sorted(set(RENAME) - set(data.columns))
    if missing:
        raise ValueError(f"The Medicare workbook is missing expected columns: {missing}")
    data = data[list(RENAME)].rename(columns=RENAME).dropna(subset=["source_quarter", "state", "service_type"])
    fields = data.source_quarter.map(quarter_fields)
    data[["financial_year", "financial_quarter", "quarter_end"]] = pd.DataFrame(fields.tolist(), index=data.index)
    data["state"] = data.state.astype(str).str.strip().map(STATE_NAMES).fillna(data.state.astype(str).str.strip())
    data["service_type"] = data.service_type.astype(str).str.strip()
    numeric = ["services", "benefits_dollars", "bulk_billed_services", "patient_billed_services",
               "bulk_billing_rate", "fees_charged_dollars"]
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.sort_values(["quarter_end", "service_type", "state"]).reset_index(drop=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "mbs_quarterly.csv"
    data.to_csv(output, index=False)
    metadata = {"source_file": source.name, "normalized_rows": len(data),
                "first_quarter": data.financial_quarter.iloc[0], "last_quarter": data.financial_quarter.iloc[-1]}
    (args.output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(data):,} normalized rows: {output}")


if __name__ == "__main__":
    main()
