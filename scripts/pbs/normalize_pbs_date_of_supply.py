"""Normalize PBS Date of Supply data to monthly medicine-level APET records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

REQUIRED = {
    "MONTH_OF_SUPPLY", "ATC5_CODE", "DRUG_NAME", "PRSCRPTN_CNT",
    "PATIENT_CONTRIB", "GOVT_CONTRIB", "TOTAL_COST",
}
NUMERIC = ["PRSCRPTN_CNT", "PATIENT_CONTRIB", "GOVT_CONTRIB", "TOTAL_COST"]


def fy_label(month: pd.Timestamp) -> str:
    start = month.year if month.month >= 7 else month.year - 1
    return f"FY{start}-{str(start + 1)[-2:]}"


def fq_label(month: pd.Timestamp) -> str:
    quarter = ((month.month - 7) % 12) // 3 + 1
    return f"{fy_label(month)}_Q{quarter}"


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", type=Path)
    parser.add_argument("--raw-dir", type=Path, default=project_root / "data/pbs/raw")
    parser.add_argument("--output-dir", type=Path, default=project_root / "data/pbs/normalized")
    args = parser.parse_args()
    candidates = sorted(args.raw_dir.glob("dos-jul-*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    source = args.input_file or (candidates[0] if candidates else None)
    if source is None or not source.exists():
        raise FileNotFoundError("No PBS Date of Supply workbook found. Run fetch_pbs_date_of_supply.py first.")

    workbook = pd.ExcelFile(source)
    parts = []
    source_rows = 0
    for sheet in workbook.sheet_names:
        frame = pd.read_excel(source, sheet_name=sheet)
        missing = sorted(REQUIRED - set(frame.columns))
        if missing:
            raise ValueError(f"{sheet} is missing required columns: {missing}")
        source_rows += len(frame)
        frame = frame[list(REQUIRED)].copy()
        frame["MONTH_OF_SUPPLY"] = pd.to_datetime(
            frame["MONTH_OF_SUPPLY"].astype("Int64").astype(str), format="%Y%m", errors="coerce"
        )
        for column in NUMERIC:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame["ATC5_CODE"] = frame["ATC5_CODE"].fillna("UNKNOWN").astype(str).str.strip()
        frame["DRUG_NAME"] = frame["DRUG_NAME"].fillna("Unknown medicine").astype(str).str.strip()
        if frame["MONTH_OF_SUPPLY"].isna().any():
            raise ValueError(f"{sheet} contains invalid MONTH_OF_SUPPLY values")
        grouped = frame.groupby(["MONTH_OF_SUPPLY", "ATC5_CODE", "DRUG_NAME"], as_index=False)[NUMERIC].sum()
        parts.append(grouped)
        print(f"Read {sheet}: {len(frame):,} source rows -> {len(grouped):,} monthly medicine rows")

    data = pd.concat(parts, ignore_index=True)
    data = data.groupby(["MONTH_OF_SUPPLY", "ATC5_CODE", "DRUG_NAME"], as_index=False)[NUMERIC].sum()
    data = data.rename(columns={
        "MONTH_OF_SUPPLY": "month_of_supply", "ATC5_CODE": "atc5_code", "DRUG_NAME": "drug_name",
        "PRSCRPTN_CNT": "prescription_count", "PATIENT_CONTRIB": "patient_contribution_dollars",
        "GOVT_CONTRIB": "government_contribution_dollars", "TOTAL_COST": "total_cost_dollars",
    })
    data["financial_year"] = data.month_of_supply.map(fy_label)
    data["financial_quarter"] = data.month_of_supply.map(fq_label)
    data["month_of_supply"] = data.month_of_supply.dt.strftime("%Y-%m-01")
    columns = ["month_of_supply", "financial_year", "financial_quarter", "atc5_code", "drug_name",
               "prescription_count", "government_contribution_dollars", "patient_contribution_dollars",
               "total_cost_dollars"]
    data = data[columns].sort_values(["month_of_supply", "drug_name", "atc5_code"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "pbs_monthly_medicines.csv"
    data.to_csv(output, index=False)
    metadata = {"source_file": source.name, "source_rows": source_rows, "normalized_rows": len(data),
                "first_month": data.month_of_supply.min(), "last_month": data.month_of_supply.max()}
    (args.output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(data):,} normalized rows: {output}")


if __name__ == "__main__":
    main()
