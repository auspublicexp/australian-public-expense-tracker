"""Generate long-term APET trend charts from complete IPEA financial years."""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

BLUE, GREEN, ORANGE = "#1f77b4", "#6aa84f", "#e69138"
IPEA_URL = "https://www.ipea.gov.au/reporting"
APET_URL, X_URL = "https://auspublicexp.org/", "https://x.com/auspublicexp"
NOTE = "Reported parliamentary expenses. Categories use an APET crosswalk for documented IPEA label changes."
plt.rcParams["svg.fonttype"] = "none"

CATEGORY_MAP = {
    "Office Administrative Costs": "Office Administration",
    "Employee Costs": "Employee Travel",
    "Domestic Scheduled Fares": "Scheduled Commercial Transport",
    "Unscheduled Transport": "Unscheduled Commercial Transport",
    "Overseas Travel": "International Travel",
    "Family Travel Costs": "Family Travel",
    "Family or Nominee Travel": "Family Travel",
}
TREND_CATEGORIES = ["Office Administration", "Office Facilities", "Employee Travel",
                    "Travel Allowance", "Other Car Costs", "International Travel"]
OFFICE_CATEGORIES = {"Office Administration", "Office Facilities", "Telecommunications"}
TRAVEL_CATEGORIES = {"Employee Travel", "Travel Allowance", "Other Car Costs",
                     "International Travel", "Family Travel"}


def money(value, _position=0):
    return f"${value / 1e6:,.0f}m"


def add_footer(fig, logo: Path) -> None:
    if logo.exists():
        area = fig.add_axes([.025, .008, .105, .105]); area.imshow(mpimg.imread(logo)); area.axis("off")
    parts = [("Source: Independent Parliamentary Expenses Authority via ", None, "#555"),
             ("ipea.gov.au", IPEA_URL, "#0d6efd"), ("  |  ", None, "#555"),
             ("auspublicexp.org", APET_URL, "#0d6efd"),
             ("  |  Australian Public Expense Tracker  |  ", None, "#555"),
             ("@auspublicexp", X_URL, "#0d6efd")]
    x = .15
    for label, url, colour in parts:
        artist = fig.text(x, .04, label, fontsize=8.2, color=colour, url=url)
        fig.canvas.draw(); x += artist.get_window_extent(renderer=fig.canvas.get_renderer()).width / fig.bbox.width
    fig.text(.15, .018, NOTE, fontsize=7.3, color="#555")


def finish(fig, ax, output: Path, logo: Path) -> None:
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", linestyle="--", alpha=.22); ax.set_axisbelow(True)
    add_footer(fig, logo); fig.subplots_adjust(left=.11, right=.96, top=.83, bottom=.20)
    output.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "svg"):
        fig.savefig(output.with_suffix("." + suffix), dpi=180, bbox_inches="tight")
    plt.close(fig)


def available_years(data_dir: Path) -> list[tuple[str, list[Path]]]:
    found = {}
    for path in data_dir.glob("*q*_dataextract.csv"):
        match = re.fullmatch(r"(\d{4})q0?([1-4])_dataextract\.csv", path.name, re.I)
        if match:
            found[(int(match.group(1)), int(match.group(2)))] = path
    years = []
    for start in sorted({year for year, _ in found}):
        components = [(start, 3), (start, 4), (start + 1, 1), (start + 1, 2)]
        if all(item in found for item in components):
            years.append((f"FY{start}-{str(start + 1)[-2:]}", [found[item] for item in components]))
    return years


def load_summary(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    totals, categories = [], []
    for financial_year, files in available_years(data_dir):
        parts = []
        for path in files:
            frame = pd.read_csv(path, usecols=["HighLevelCategory", "Amount"], low_memory=False)
            frame["Amount"] = pd.to_numeric(frame.Amount.astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False), errors="coerce").fillna(0)
            frame["HighLevelCategory"] = frame.HighLevelCategory.fillna("Uncategorised").astype(str).str.strip().replace(CATEGORY_MAP)
            parts.append(frame)
        annual = pd.concat(parts, ignore_index=True)
        totals.append({"financial_year": financial_year, "reported_expenses_dollars": annual.Amount.sum()})
        grouped = annual.groupby("HighLevelCategory", as_index=False).Amount.sum()
        grouped["financial_year"] = financial_year; categories.append(grouped)
    if not totals:
        raise ValueError("No complete IPEA financial years were found")
    return pd.DataFrame(totals), pd.concat(categories, ignore_index=True)


def total_chart(totals, output, logo):
    fig, ax = plt.subplots(figsize=(12, 7)); ax.plot(totals.financial_year, totals.reported_expenses_dollars, marker="o", linewidth=3, color=BLUE)
    ax.set_title("Total reported parliamentary expenses by financial year", fontsize=20, loc="left"); ax.yaxis.set_major_formatter(FuncFormatter(money))
    for x, value in zip(totals.financial_year, totals.reported_expenses_dollars): ax.annotate(money(value), (x, value), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=9)
    ax.margins(y=.16); totals.to_csv(output.with_name(output.name + "_data.csv"), index=False); finish(fig, ax, output, logo)


def category_chart(categories, output, logo):
    selected = categories[categories.HighLevelCategory.isin(TREND_CATEGORIES)].copy()
    pivot = selected.pivot(index="financial_year", columns="HighLevelCategory", values="Amount").fillna(0)
    fig, ax = plt.subplots(figsize=(12, 7))
    for category in TREND_CATEGORIES:
        if category in pivot: ax.plot(pivot.index, pivot[category], marker="o", linewidth=2.2, label=category)
    ax.set_title("Selected parliamentary expense categories over time", fontsize=20, loc="left"); ax.yaxis.set_major_formatter(FuncFormatter(money)); ax.legend(frameon=False, ncol=2, loc="upper left")
    selected.rename(columns={"HighLevelCategory": "category", "Amount": "reported_expenses_dollars"}).to_csv(output.with_name(output.name + "_data.csv"), index=False)
    finish(fig, ax, output, logo)


def broad_chart(categories, output, logo):
    grouped = categories.copy()
    grouped["group"] = grouped.HighLevelCategory.map(lambda value: "Office and administration" if value in OFFICE_CATEGORIES else "Travel-related" if value in TRAVEL_CATEGORIES else "Other")
    grouped = grouped[grouped.group != "Other"].groupby(["financial_year", "group"], as_index=False).Amount.sum()
    pivot = grouped.pivot(index="financial_year", columns="group", values="Amount").fillna(0)
    fig, ax = plt.subplots(figsize=(12, 7))
    for label, colour in [("Office and administration", BLUE), ("Travel-related", ORANGE)]: ax.plot(pivot.index, pivot[label], marker="o", linewidth=3, label=label, color=colour)
    ax.set_title("Selected office-related and travel-related expenses", fontsize=20, loc="left"); ax.yaxis.set_major_formatter(FuncFormatter(money)); ax.legend(frameon=False)
    grouped.rename(columns={"Amount": "reported_expenses_dollars"}).to_csv(output.with_name(output.name + "_data.csv"), index=False); finish(fig, ax, output, logo)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=project_root / "data/ipea")
    parser.add_argument("--output-dir", type=Path, default=project_root / "output/ipea/trends")
    parser.add_argument("--website-dir", type=Path, default=project_root / "website/public_html/charts/ipea/trends")
    parser.add_argument("--logo", type=Path, default=project_root / "branding/APETLogo400x400.png")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    totals, categories = load_summary(args.data_dir)
    total_chart(totals, args.output_dir / "01_total_reported_expenses_by_financial_year", args.logo)
    category_chart(categories, args.output_dir / "02_selected_categories_over_time", args.logo)
    broad_chart(categories, args.output_dir / "03_office_and_travel_expenses_over_time", args.logo)
    for source in args.output_dir.glob("*"):
        if source.suffix.lower() == ".svg" or source.name.endswith("_data.csv"):
            args.website_dir.mkdir(parents=True, exist_ok=True); shutil.copy2(source, args.website_dir / source.name)
    print(f"Created 3 IPEA trend charts for {len(totals)} complete financial years: {args.output_dir.resolve()}")
    print(f"Copied website-ready SVG/CSV files to: {args.website_dir.resolve()}")


if __name__ == "__main__":
    main()
