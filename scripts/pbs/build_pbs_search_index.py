"""Build the compact browser-search index for APET PBS medicine expenditure."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd


def aggregate(data: pd.DataFrame, period_column: str, period_type: str) -> pd.DataFrame:
    grouped = data.groupby([period_column, "drug_name"], as_index=False).agg(
        atc5_codes=("atc5_code", lambda values: ", ".join(sorted(set(str(value) for value in values if str(value) != "UNKNOWN")))),
        government_contribution_dollars=("government_contribution_dollars", "sum"),
        patient_contribution_dollars=("patient_contribution_dollars", "sum"),
        total_cost_dollars=("total_cost_dollars", "sum"),
        prescription_count=("prescription_count", "sum"),
    ).rename(columns={period_column: "period"})
    grouped["period_type"] = period_type
    grouped["rank_by_government_expenditure"] = grouped.groupby("period")["government_contribution_dollars"].rank(
        method="min", ascending=False
    ).astype(int)
    grouped = grouped.sort_values(["drug_name", "period"])
    grouped["previous_government_contribution_dollars"] = grouped.groupby("drug_name")["government_contribution_dollars"].shift(1)
    grouped["change_dollars"] = grouped.government_contribution_dollars - grouped.previous_government_contribution_dollars
    grouped["change_percent"] = grouped.change_dollars / grouped.previous_government_contribution_dollars * 100
    grouped.loc[grouped.previous_government_contribution_dollars <= 0, ["change_dollars", "change_percent"]] = pd.NA
    grouped["government_dollars_per_prescription"] = (
        grouped.government_contribution_dollars / grouped.prescription_count.where(grouped.prescription_count > 0)
    )
    return grouped


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", type=Path, default=project_root / "data/pbs/normalized/pbs_monthly_medicines.csv")
    parser.add_argument("--validation-file", type=Path, default=project_root / "output/validation/pbs_latest.json")
    parser.add_argument("--output-file", type=Path, default=project_root / "output/pbs/pbs-search-index.json")
    parser.add_argument("--website-file", type=Path, default=project_root / "website/public_html/charts/pbs/pbs-search-index.json")
    args = parser.parse_args()

    data = pd.read_csv(args.data_file, parse_dates=["month_of_supply"])
    validation = json.loads(args.validation_file.read_text(encoding="utf-8"))
    cutoff = pd.Timestamp(validation["publication_cutoff"])
    data = data[data.month_of_supply <= cutoff].copy()
    data = data[~data.drug_name.str.upper().isin(["99999Z", "UNKNOWN", "UNKNOWN MEDICINE"])]

    fy_counts = data.groupby("financial_year").month_of_supply.nunique()
    complete_years = sorted(fy_counts[fy_counts == 12].index)
    q_counts = data.groupby("financial_quarter").month_of_supply.nunique()
    complete_quarters = sorted(q_counts[q_counts == 3].index)
    annual = aggregate(data[data.financial_year.isin(complete_years)], "financial_year", "annual")
    quarterly = aggregate(data[data.financial_quarter.isin(complete_quarters)], "financial_quarter", "quarterly")
    result = pd.concat([annual, quarterly], ignore_index=True)

    number_columns = ["government_contribution_dollars", "patient_contribution_dollars", "total_cost_dollars",
                      "prescription_count", "government_dollars_per_prescription", "change_dollars", "change_percent"]
    for column in number_columns:
        result[column] = pd.to_numeric(result[column], errors="coerce").round(2)
    result = result.astype(object).where(pd.notna(result), None)
    columns = ["drug_name", "atc5_codes", "period_type", "period", "government_contribution_dollars",
               "patient_contribution_dollars", "total_cost_dollars", "prescription_count",
               "government_dollars_per_prescription", "change_dollars", "change_percent",
               "rank_by_government_expenditure"]
    records = result[columns].values.tolist()
    payload = {
        "generated_from_cutoff": cutoff.strftime("%Y-%m-%d"),
        "publication_rule": validation["publication_rule"],
        "record_count": len(records),
        "periods": {"annual": complete_years, "quarterly": complete_quarters},
        "columns": columns,
        "records": records,
    }
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8"
    )
    args.website_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.output_file, args.website_file)
    print(f"Saved {len(records):,} PBS search records: {args.output_file}")
    print(f"Copied website search index: {args.website_file}")


if __name__ == "__main__":
    main()
