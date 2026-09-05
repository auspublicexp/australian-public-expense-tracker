"""Generate prototype APET PBS government-expenditure trend charts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

BLUE = "#1f77b4"
GREEN, GREY = "#6aa84f", "#888888"
PBS_URL = "https://www.pbs.gov.au/statistics/dos-and-dop/dos-and-dop"
APET_URL, X_URL = "https://auspublicexp.org/", "https://x.com/auspublicexp"
NOTE = "Government contribution by month of supply. APET excludes the latest complete source quarter and any incomplete quarter."
plt.rcParams["svg.fonttype"] = "none"


def money_tick(value, _position):
    return f"${value / 1e9:,.1f}b" if abs(value) >= 1e9 else f"${value / 1e6:,.0f}m"


def add_logo(fig, logo):
    if logo.exists():
        area = fig.add_axes([.025, .008, .105, .105]); area.imshow(mpimg.imread(logo)); area.axis("off")


def finish(fig, ax, output, logo):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=.22); ax.set_axisbelow(True)
    add_logo(fig, logo)
    parts = [("Source: Department of Health, Disability and Ageing via ", None, "#555"),
             ("pbs.gov.au", PBS_URL, "#0d6efd"), ("  |  ", None, "#555"),
             ("auspublicexp.org", APET_URL, "#0d6efd"),
             ("  |  Australian Public Expense Tracker  |  ", None, "#555"),
             ("@auspublicexp", X_URL, "#0d6efd")]
    x = .15
    for label, url, colour in parts:
        artist = fig.text(x, .04, label, fontsize=8.2, color=colour, url=url)
        fig.canvas.draw(); x += artist.get_window_extent(renderer=fig.canvas.get_renderer()).width / fig.bbox.width
    fig.text(.15, .018, NOTE, fontsize=7.3, color="#555")
    fig.subplots_adjust(left=.12, right=.96, top=.82, bottom=.20)
    output.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "svg"):
        fig.savefig(output.with_suffix("." + suffix), dpi=180, bbox_inches="tight")
    plt.close(fig)


def chart(data, period, title, output, logo):
    summary = data.groupby(period, as_index=False).agg(
        government_contribution_dollars=("government_contribution_dollars", "sum"),
        prescriptions=("prescription_count", "sum"),
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(summary[period], summary.government_contribution_dollars, color=BLUE)
    ax.set_title(title, fontsize=20, loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(money_tick)); ax.tick_params(axis="x", rotation=35)
    ax.bar_label(bars, labels=[money_tick(v, 0) for v in summary.government_contribution_dollars], padding=4, fontsize=9)
    ax.margins(y=.14)
    summary.to_csv(output.with_name(output.name + "_data.csv"), index=False)
    finish(fig, ax, output, logo)


def horizontal(data, label, value, title, output, logo, top=12):
    summary = data.nlargest(top, value).sort_values(value)
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(summary[label], summary[value], color=BLUE)
    ax.set_title(title, fontsize=20, loc="left")
    ax.xaxis.set_major_formatter(FuncFormatter(money_tick))
    ax.bar_label(bars, labels=[money_tick(v, 0) for v in summary[value]], padding=4, fontsize=9)
    ax.margins(x=.16)
    summary.sort_values(value, ascending=False).to_csv(output.with_name(output.name + "_data.csv"), index=False)
    finish(fig, ax, output, logo)


def medicine_summary(data):
    usable = data[~data.drug_name.str.upper().isin(["99999Z", "UNKNOWN", "UNKNOWN MEDICINE"])]
    return usable.groupby("drug_name", as_index=False).agg(
        government_contribution_dollars=("government_contribution_dollars", "sum"),
        prescriptions=("prescription_count", "sum"),
    )


def annual_increases(data, previous_fy, current_fy, output, logo):
    usable = data[
        data.financial_year.isin([previous_fy, current_fy])
        & ~data.drug_name.str.upper().isin(["99999Z", "UNKNOWN", "UNKNOWN MEDICINE"])
    ]
    medicines = usable.groupby(
        ["drug_name", "financial_year"], as_index=False
    ).government_contribution_dollars.sum()
    pivot = medicines.pivot(index="drug_name", columns="financial_year", values="government_contribution_dollars").fillna(0)
    pivot["increase_dollars"] = pivot[current_fy] - pivot[previous_fy]
    # Avoid presenting a tiny prior-year base as a misleading large increase.
    result = pivot[pivot[previous_fy] >= 1_000_000].nlargest(12, "increase_dollars").reset_index()
    result = result.sort_values("increase_dollars")
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(result.drug_name, result.increase_dollars, color=GREEN)
    ax.set_title(f"Largest increases in PBS/RPBS government expenditure\n{previous_fy} to {current_fy}", fontsize=19, loc="left")
    ax.xaxis.set_major_formatter(FuncFormatter(money_tick))
    ax.bar_label(bars, labels=[money_tick(v, 0) for v in result.increase_dollars], padding=4, fontsize=9)
    ax.margins(x=.17)
    result.sort_values("increase_dollars", ascending=False).to_csv(output.with_name(output.name + "_data.csv"), index=False)
    finish(fig, ax, output, logo)


def contribution_comparison(data, output, logo):
    summary = data.groupby("financial_year", as_index=False).agg(
        government_contribution_dollars=("government_contribution_dollars", "sum"),
        patient_contribution_dollars=("patient_contribution_dollars", "sum"),
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.bar(summary.financial_year, summary.government_contribution_dollars, color=BLUE, label="Government contribution")
    ax.bar(summary.financial_year, summary.patient_contribution_dollars,
           bottom=summary.government_contribution_dollars, color=GREY, label="Patient contribution")
    ax.set_title("PBS and RPBS prescription costs by contributor", fontsize=20, loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(money_tick)); ax.tick_params(axis="x", rotation=35)
    ax.legend(frameon=False, loc="upper left")
    summary.to_csv(output.with_name(output.name + "_data.csv"), index=False)
    finish(fig, ax, output, logo)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", type=Path, default=project_root / "data/pbs/normalized/pbs_monthly_medicines.csv")
    parser.add_argument("--validation-file", type=Path, default=project_root / "output/validation/pbs_latest.json")
    parser.add_argument("--output-dir", type=Path, default=project_root / "output/pbs_prototype")
    parser.add_argument("--logo", type=Path, default=project_root / "branding/APETLogo400x400.png")
    args = parser.parse_args()
    data = pd.read_csv(args.data_file, parse_dates=["month_of_supply"])
    validation = json.loads(args.validation_file.read_text(encoding="utf-8"))
    cutoff = pd.Timestamp(validation["publication_cutoff"])
    data = data[data.month_of_supply <= cutoff].copy()
    if data.empty:
        raise ValueError("No normalized PBS rows fall on or before the publication cutoff")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    complete_fy = data.groupby("financial_year").month_of_supply.nunique()
    annual = data[data.financial_year.isin(complete_fy[complete_fy == 12].index)]
    chart(annual, "financial_year", "PBS and RPBS government expenditure by financial year",
          args.output_dir / "01_government_expenditure_by_financial_year", args.logo)
    chart(data, "financial_quarter", "PBS and RPBS government expenditure by financial quarter",
          args.output_dir / "02_government_expenditure_by_financial_quarter", args.logo)

    annual_periods = sorted(annual.financial_year.unique())
    latest_fy = annual_periods[-1]
    latest_annual = annual[annual.financial_year == latest_fy]
    horizontal(medicine_summary(latest_annual), "drug_name", "government_contribution_dollars",
               f"Medicines with the largest government expenditure\n{latest_fy}",
               args.output_dir / "03_top_medicines_latest_financial_year", args.logo)

    latest_quarter = sorted(data.financial_quarter.unique())[-1]
    latest_quarter_data = data[data.financial_quarter == latest_quarter]
    horizontal(medicine_summary(latest_quarter_data), "drug_name", "government_contribution_dollars",
               f"Medicines with the largest government expenditure\n{latest_quarter.replace('_', ' ')}",
               args.output_dir / "04_top_medicines_latest_financial_quarter", args.logo)

    if len(annual_periods) >= 2:
        annual_increases(annual, annual_periods[-2], annual_periods[-1],
                         args.output_dir / "05_largest_annual_medicine_increases", args.logo)
    contribution_comparison(annual, args.output_dir / "06_government_and_patient_contributions", args.logo)
    print(f"Created prototype charts through {cutoff:%B %Y}: {args.output_dir}")


if __name__ == "__main__":
    main()
