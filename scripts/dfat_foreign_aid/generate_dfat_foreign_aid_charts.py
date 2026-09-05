"""Generate APET DFAT foreign-aid overview and annual financial-year charts."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

BLUE, GREEN = "#1f77b4", "#6aa84f"
DFAT_URL = "https://adp.dfat.gov.au/data-downloads"
APET_URL, X_URL = "https://auspublicexp.org/", "https://x.com/auspublicexp"
NOTE = "DFAT IATI reported disbursements (type 3), including adjustments; excludes commitments and budgets."
plt.rcParams["svg.fonttype"] = "none"


def money_tick(value, _position=0):
    if abs(value) >= 1e9:
        return f"${value / 1e9:,.1f}b"
    return f"${value / 1e6:,.0f}m"


def add_logo(fig, logo: Path):
    if logo.exists():
        logo_ax = fig.add_axes([.025, .008, .105, .105])
        logo_ax.imshow(mpimg.imread(logo)); logo_ax.axis("off")


def finish(fig, ax, output: Path, logo: Path, note=NOTE, grid_axis="x"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, linestyle="--", alpha=.22); ax.set_axisbelow(True)
    add_logo(fig, logo)
    parts = [
        ("Source: Australian Department of Foreign Affairs and Trade via ", None, "#555"),
        ("adp.dfat.gov.au", DFAT_URL, "#0d6efd"), ("  |  ", None, "#555"),
        ("auspublicexp.org", APET_URL, "#0d6efd"),
        ("  |  Australian Public Expense Tracker  |  ", None, "#555"),
        ("@auspublicexp", X_URL, "#0d6efd"),
    ]
    x = .15
    for label, url, colour in parts:
        artist = fig.text(x, .04, label, fontsize=8.2, color=colour, url=url)
        fig.canvas.draw()
        x += artist.get_window_extent(renderer=fig.canvas.get_renderer()).width / fig.bbox.width
    fig.text(.15, .02, note, fontsize=7.3, color="#555")
    fig.subplots_adjust(left=.25, right=.96, top=.83, bottom=.18)
    output.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "svg"):
        fig.savefig(output.with_suffix("." + suffix), dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_data(data: pd.DataFrame, output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output.with_name(output.name + "_data.csv"), index=False)


def horizontal(data, label, value, title, output, logo, top=12, note=NOTE):
    data = data.nlargest(top, value).sort_values(value)
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(data[label], data[value], color=BLUE)
    ax.set_title(title, fontsize=20, loc="left")
    ax.xaxis.set_major_formatter(FuncFormatter(money_tick))
    ax.bar_label(bars, labels=[money_tick(v) for v in data[value]], padding=4, fontsize=9)
    ax.margins(x=.17)
    save_data(data.sort_values(value, ascending=False), output)
    finish(fig, ax, output, logo, note=note)


def overview(data, output_root, logo):
    annual = data.groupby("financial_year", as_index=False).value_dollars.sum()
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(annual.financial_year, annual.value_dollars, marker="o", linewidth=3, color=BLUE)
    ax.set_title("Australian foreign-aid disbursements by financial year", fontsize=20, loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(money_tick))
    for x, y in zip(annual.financial_year, annual.value_dollars):
        ax.annotate(money_tick(y), (x, y), xytext=(0, 9), textcoords="offset points", ha="center")
    ax.margins(x=.08, y=.18)
    save_data(annual, output_root / "01_total_disbursements_by_financial_year")
    finish(fig, ax, output_root / "01_total_disbursements_by_financial_year", logo, grid_axis="y")

    sectors = data.groupby(["financial_year", "sector_category"], as_index=False).value_dollars.sum()
    leading = sectors.groupby("sector_category").value_dollars.sum().nlargest(7).index
    pivot = sectors[sectors.sector_category.isin(leading)].pivot(
        index="financial_year", columns="sector_category", values="value_dollars"
    ).fillna(0)
    fig, ax = plt.subplots(figsize=(12, 7))
    for sector in pivot.columns:
        ax.plot(pivot.index, pivot[sector], marker="o", linewidth=2.2, label=sector)
    ax.set_title("Australian foreign-aid disbursement trends by sector", fontsize=20, loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(money_tick)); ax.legend(frameon=False, fontsize=8, ncol=2)
    save_data(sectors[sectors.sector_category.isin(leading)], output_root / "02_sector_trends")
    finish(fig, ax, output_root / "02_sector_trends", logo, grid_axis="y")


def annual_charts(data, financial_year, output_root, logo):
    year = data[data.financial_year == financial_year]
    folder = output_root / f"{financial_year}_annual"
    countries = year[year.recipient_country.ne("")].groupby("recipient_country", as_index=False).value_dollars.sum()
    country_note = NOTE + " Country chart includes only transactions carrying a recipient-country code."
    horizontal(countries, "recipient_country", "value_dollars",
               f"Largest country-coded Australian aid disbursements\n{financial_year}",
               folder / "01_disbursements_by_country", logo, note=country_note)
    sectors = year[year.sector_category.ne("")].groupby("sector_category", as_index=False).value_dollars.sum()
    horizontal(sectors, "sector_category", "value_dollars",
               f"Australian aid disbursements by sector\n{financial_year}",
               folder / "02_disbursements_by_sector", logo)
    activities = year.groupby(["activity_id", "activity_title", "implementing_organisation"], as_index=False).value_dollars.sum()
    activities["chart_label"] = activities.activity_title.where(
        activities.activity_title.ne(""), activities.activity_id
    ).str.slice(0, 65)
    horizontal(activities, "chart_label", "value_dollars",
               f"Largest Australian aid activities by reported disbursement\n{financial_year}",
               folder / "03_largest_activities", logo)
    print(f"Created DFAT foreign-aid charts for {financial_year}: {folder}")


def copy_website_assets(output_root: Path, website_dir: Path) -> int:
    copied = 0
    for source in output_root.rglob("*"):
        if source.is_file() and (source.suffix.lower() == ".svg" or source.name.endswith("_data.csv")):
            destination = website_dir / source.relative_to(output_root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination); copied += 1
    return copied


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", type=Path, default=project_root / "data/dfat_foreign_aid/normalized/dfat_aid_transactions.csv")
    parser.add_argument("--output-root", type=Path, default=project_root / "output/foreign_aid")
    parser.add_argument("--website-dir", type=Path, default=project_root / "website/public_html/charts/foreign_aid")
    parser.add_argument("--logo", type=Path, default=project_root / "branding/APETLogo400x400.png")
    parser.add_argument("--no-website-copy", action="store_true")
    args = parser.parse_args()
    data = pd.read_csv(args.data_file, dtype={"transaction_type_code": str}, keep_default_na=False)
    disbursements = data[data.transaction_type_code == "3"].copy()
    disbursements["value_dollars"] = pd.to_numeric(disbursements.value_dollars, errors="raise")
    if disbursements.empty:
        raise ValueError("No validated IATI type-3 disbursements were found")
    args.output_root.mkdir(parents=True, exist_ok=True)
    overview(disbursements, args.output_root, args.logo)
    years = sorted(disbursements.financial_year.unique())
    for financial_year in years:
        annual_charts(disbursements, financial_year, args.output_root, args.logo)
    copied = 0 if args.no_website_copy else copy_website_assets(args.output_root, args.website_dir)
    print(f"Generated overview charts and {len(years)} annual periods.")
    if not args.no_website_copy:
        print(f"Copied {copied} website-ready SVG/CSV files to: {args.website_dir}")


if __name__ == "__main__":
    main()
