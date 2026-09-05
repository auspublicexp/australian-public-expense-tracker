"""Generate complete APET PBS overview, annual and quarterly chart folders."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from generate_pbs_prototype_charts import (
    BLUE, GREY, contribution_comparison, finish, horizontal, medicine_summary,
    money_tick,
)


def count_tick(value, _position):
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.1f}m"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.0f}k"
    return f"{value:,.0f}"


def count_horizontal(data, label, value, title, output, logo, top=12):
    summary = data.nlargest(top, value).sort_values(value)
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(summary[label], summary[value], color=BLUE)
    ax.set_title(title, fontsize=20, loc="left")
    ax.xaxis.set_major_formatter(FuncFormatter(count_tick))
    ax.bar_label(bars, labels=[count_tick(v, 0) for v in summary[value]], padding=4, fontsize=9)
    ax.margins(x=.16)
    summary.sort_values(value, ascending=False).to_csv(output.with_name(output.name + "_data.csv"), index=False)
    finish(fig, ax, output, logo)


def contribution_split(data, title, output, logo):
    government = float(data.government_contribution_dollars.sum())
    patient = float(data.patient_contribution_dollars.sum())
    summary = pd.DataFrame({"contributor": ["Australian Government", "Patients"],
                            "contribution_dollars": [government, patient]}).sort_values("contribution_dollars")
    fig, ax = plt.subplots(figsize=(12, 6.5))
    colours = [GREY if name == "Patients" else BLUE for name in summary.contributor]
    bars = ax.barh(summary.contributor, summary.contribution_dollars, color=colours)
    ax.set_title(title, fontsize=20, loc="left")
    ax.xaxis.set_major_formatter(FuncFormatter(money_tick))
    ax.bar_label(bars, labels=[money_tick(v, 0) for v in summary.contribution_dollars], padding=4, fontsize=11)
    ax.margins(x=.16)
    summary.sort_values("contribution_dollars", ascending=False).to_csv(
        output.with_name(output.name + "_data.csv"), index=False
    )
    finish(fig, ax, output, logo)


def period_charts(data, label, folder, logo):
    folder.mkdir(parents=True, exist_ok=True)
    medicines = medicine_summary(data)
    horizontal(medicines, "drug_name", "government_contribution_dollars",
               f"Medicines with the largest government expenditure\n{label}",
               folder / "01_top_medicines_by_government_expenditure", logo)
    count_horizontal(medicines, "drug_name", "prescriptions",
                     f"Most frequently supplied PBS and RPBS medicines\n{label}",
                     folder / "02_top_medicines_by_prescriptions", logo)
    contribution_split(data, f"Government and patient contributions\n{label}",
                       folder / "03_government_and_patient_contributions", logo)
    print(f"Created PBS charts for {label}: {folder}")


def overview_charts(data, annual, output_root, logo):
    annual_summary = annual.groupby("financial_year", as_index=False).agg(
        government_contribution_dollars=("government_contribution_dollars", "sum"),
        prescriptions=("prescription_count", "sum"),
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(annual_summary.financial_year, annual_summary.government_contribution_dollars, color=BLUE)
    ax.set_title("PBS and RPBS government expenditure by financial year", fontsize=20, loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(money_tick)); ax.tick_params(axis="x", rotation=35)
    ax.bar_label(bars, labels=[money_tick(v, 0) for v in annual_summary.government_contribution_dollars], padding=4)
    annual_summary.to_csv(output_root / "01_government_expenditure_by_financial_year_data.csv", index=False)
    finish(fig, ax, output_root / "01_government_expenditure_by_financial_year", logo)

    quarterly = data.groupby("financial_quarter", as_index=False).agg(
        government_contribution_dollars=("government_contribution_dollars", "sum"),
        prescriptions=("prescription_count", "sum"),
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(quarterly.financial_quarter, quarterly.government_contribution_dollars, color=BLUE)
    ax.set_title("PBS and RPBS government expenditure by financial quarter", fontsize=20, loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(money_tick)); ax.tick_params(axis="x", rotation=35)
    ax.bar_label(bars, labels=[money_tick(v, 0) for v in quarterly.government_contribution_dollars], padding=4, fontsize=8)
    quarterly.to_csv(output_root / "02_government_expenditure_by_financial_quarter_data.csv", index=False)
    finish(fig, ax, output_root / "02_government_expenditure_by_financial_quarter", logo)
    contribution_comparison(annual, output_root / "03_government_and_patient_contributions", logo)


def copy_website_assets(output_root: Path, website_dir: Path) -> int:
    copied = 0
    for source in output_root.rglob("*"):
        if source.is_file() and (source.suffix.lower() == ".svg" or source.name.endswith("_data.csv")):
            destination = website_dir / source.relative_to(output_root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied += 1
    return copied


def verify_complete_output(output_root: Path) -> dict[str, int]:
    """Confirm the publication archive contains every expected chart format."""
    counts = {
        "png": len(list(output_root.rglob("*.png"))),
        "svg": len(list(output_root.rglob("*.svg"))),
        "csv": len(list(output_root.rglob("*_data.csv"))),
    }
    if counts["png"] == 0:
        raise RuntimeError(f"No PNG charts were created in the output folder: {output_root}")
    if counts["png"] != counts["svg"]:
        raise RuntimeError(
            "PBS output is incomplete: "
            f"found {counts['png']} PNG charts but {counts['svg']} SVG charts in {output_root}"
        )
    return counts


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", type=Path, default=project_root / "data/pbs/normalized/pbs_monthly_medicines.csv")
    parser.add_argument("--validation-file", type=Path, default=project_root / "output/validation/pbs_latest.json")
    parser.add_argument("--output-root", type=Path, default=project_root / "output/pbs")
    parser.add_argument("--website-dir", type=Path, default=project_root / "website/public_html/charts/pbs")
    parser.add_argument("--logo", type=Path, default=project_root / "branding/APETLogo400x400.png")
    parser.add_argument("--no-website-copy", action="store_true")
    args = parser.parse_args()

    if not args.data_file.exists():
        raise FileNotFoundError(
            f"Prepared PBS data was not found at: {args.data_file}\n"
            "Run fetch_pbs_date_of_supply.py, then normalize_pbs_date_of_supply.py, "
            "then validate_pbs_date_of_supply.py before generating the charts."
        )
    if not args.validation_file.exists():
        raise FileNotFoundError(
            f"PBS validation report was not found at: {args.validation_file}\n"
            "Run validate_pbs_date_of_supply.py before generating the charts."
        )
    data = pd.read_csv(args.data_file, parse_dates=["month_of_supply"])
    validation = json.loads(args.validation_file.read_text(encoding="utf-8"))
    cutoff = pd.Timestamp(validation["publication_cutoff"])
    data = data[data.month_of_supply <= cutoff].copy()
    if data.empty:
        raise ValueError("No normalized PBS rows fall on or before the validated publication cutoff")
    args.output_root.mkdir(parents=True, exist_ok=True)

    fy_months = data.groupby("financial_year").month_of_supply.nunique()
    complete_years = sorted(fy_months[fy_months == 12].index)
    annual = data[data.financial_year.isin(complete_years)]
    overview_charts(data, annual, args.output_root, args.logo)
    for financial_year in complete_years:
        period_charts(data[data.financial_year == financial_year], f"{financial_year} annual",
                      args.output_root / f"{financial_year}_annual", args.logo)

    quarter_months = data.groupby("financial_quarter").month_of_supply.nunique()
    complete_quarters = sorted(quarter_months[quarter_months == 3].index)
    for quarter in complete_quarters:
        period_charts(data[data.financial_quarter == quarter], quarter.replace("_", " "),
                      args.output_root / quarter, args.logo)

    counts = verify_complete_output(args.output_root)
    copied = 0 if args.no_website_copy else copy_website_assets(args.output_root, args.website_dir)
    print(f"Generated {len(complete_years)} annual and {len(complete_quarters)} quarterly periods through {cutoff:%B %Y}.")
    print(
        f"Complete archive: {counts['png']} PNG, {counts['svg']} SVG and "
        f"{counts['csv']} supporting CSV files in: {args.output_root.resolve()}"
    )
    if not args.no_website_copy:
        print(f"Website copy: {copied} SVG/CSV files in: {args.website_dir.resolve()}")


if __name__ == "__main__":
    main()
