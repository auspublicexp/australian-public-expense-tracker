"""Generate APET Medicare Benefits Schedule expenditure charts."""
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
SOURCE_URL = "https://www.health.gov.au/resources/collections/medicare-statistics-collection"
APET_URL, X_URL = "https://auspublicexp.org/", "https://x.com/auspublicexp"
NOTE = "Benefits paid for MBS claims processed by Medicare; this is not total Australian health expenditure."
plt.rcParams["svg.fonttype"] = "none"


def money(value, _position=0):
    return f"${value / 1e9:,.1f}b" if abs(value) >= 1e9 else f"${value / 1e6:,.0f}m"


def count(value, _position=0):
    return f"{value / 1e6:,.1f}m" if abs(value) >= 1e6 else f"{value / 1e3:,.0f}k"


def finish(fig, ax, output: Path, logo: Path) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=.22)
    ax.set_axisbelow(True)
    if logo.exists():
        area = fig.add_axes([.025, .008, .105, .105]); area.imshow(mpimg.imread(logo)); area.axis("off")
    parts = [("Source: Department of Health, Disability and Ageing via ", None, "#555"),
             ("health.gov.au", SOURCE_URL, "#0d6efd"), ("  |  ", None, "#555"),
             ("auspublicexp.org", APET_URL, "#0d6efd"),
             ("  |  Australian Public Expense Tracker  |  ", None, "#555"),
             ("@auspublicexp", X_URL, "#0d6efd")]
    x = .15
    for label, url, colour in parts:
        artist = fig.text(x, .04, label, fontsize=8.2, color=colour, url=url)
        fig.canvas.draw(); x += artist.get_window_extent(renderer=fig.canvas.get_renderer()).width / fig.bbox.width
    fig.text(.15, .018, NOTE, fontsize=7.3, color="#555")
    fig.subplots_adjust(left=.13, right=.96, top=.82, bottom=.20)
    output.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "svg"):
        fig.savefig(output.with_suffix("." + suffix), dpi=180, bbox_inches="tight")
    plt.close(fig)


def bars(summary, label, value, title, output, logo, formatter=money, colour=BLUE, top=None):
    if top:
        summary = summary.nlargest(top, value)
    summary = summary.sort_values(value)
    fig, ax = plt.subplots(figsize=(12, 7))
    plotted = ax.barh(summary[label], summary[value], color=colour)
    ax.set_title(title, fontsize=20, loc="left")
    ax.xaxis.set_major_formatter(FuncFormatter(formatter))
    ax.bar_label(plotted, labels=[formatter(v) for v in summary[value]], padding=4, fontsize=9)
    ax.margins(x=.16)
    output.parent.mkdir(parents=True, exist_ok=True)
    summary.sort_values(value, ascending=False).to_csv(output.with_name(output.name + "_data.csv"), index=False)
    finish(fig, ax, output, logo)


def line_chart(summary, period, value, title, output, logo):
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(summary[period], summary[value], color=BLUE, marker="o", linewidth=2.5)
    ax.set_title(title, fontsize=20, loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(money))
    ax.tick_params(axis="x", rotation=35)
    output.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output.with_name(output.name + "_data.csv"), index=False)
    finish(fig, ax, output, logo)


def period_charts(data, label, folder, logo):
    national = data[(data.state == "Australia") & (data.service_type != "Total Medicare")]
    categories = national.groupby("service_type", as_index=False).agg(
        benefits_dollars=("benefits_dollars", "sum"), services=("services", "sum"))
    bars(categories, "service_type", "benefits_dollars", f"Medicare benefits by type of service\n{label}",
         folder / "01_benefits_by_service_type", logo)
    states = data[(data.state != "Australia") & (data.state != "Unknown") & (data.service_type == "Total Medicare")]
    states = states.groupby("state", as_index=False).agg(benefits_dollars=("benefits_dollars", "sum"), services=("services", "sum"))
    bars(states, "state", "benefits_dollars", f"Medicare benefits by patient state or territory\n{label}",
         folder / "02_benefits_by_state", logo)
    categories["average_benefit_per_service"] = categories.benefits_dollars / categories.services
    bars(categories, "service_type", "average_benefit_per_service",
         f"Average Medicare benefit per service\n{label}", folder / "03_average_benefit_per_service", logo,
         formatter=lambda value, _position=0: f"${value:,.0f}", colour=GREEN)


def copy_website_assets(output_root: Path, website_dir: Path) -> int:
    copied = 0
    for source in output_root.rglob("*"):
        if source.is_file() and (source.suffix.lower() == ".svg" or source.name.endswith("_data.csv")):
            destination = website_dir / source.relative_to(output_root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination); copied += 1
    return copied


def remove_old_quarterly_overview(output_root: Path, website_dir: Path) -> None:
    """Remove the superseded crowded quarterly trend while retaining quarter pages."""
    stem = "02_benefits_by_financial_quarter"
    for path in (
        output_root / f"{stem}.png",
        output_root / f"{stem}.svg",
        output_root / f"{stem}_data.csv",
        website_dir / f"{stem}.svg",
        website_dir / f"{stem}_data.csv",
    ):
        if path.is_file():
            path.unlink()


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", type=Path, default=project_root / "data/mbs/normalized/mbs_quarterly.csv")
    parser.add_argument("--output-root", type=Path, default=project_root / "output/mbs")
    parser.add_argument("--website-dir", type=Path, default=project_root / "website/public_html/charts/mbs")
    parser.add_argument("--logo", type=Path, default=project_root / "branding/APETLogo400x400.png")
    parser.add_argument("--no-website-copy", action="store_true")
    parser.add_argument("--overview-only", action="store_true",
                        help="Regenerate only the annual trend chart in the main MBS folder")
    args = parser.parse_args()
    if not args.data_file.exists():
        raise FileNotFoundError("Normalized MBS data is missing. Run fetch, normalize and validate first; see scripts/mbs/README.md.")
    data = pd.read_csv(args.data_file)
    args.output_root.mkdir(parents=True, exist_ok=True)
    national = data[(data.state == "Australia") & (data.service_type == "Total Medicare")].copy()
    year_counts = national.groupby("financial_year").financial_quarter.nunique()
    complete_years = sorted(year_counts[year_counts == 4].index)
    annual = national[national.financial_year.isin(complete_years)].groupby("financial_year", as_index=False).agg(
        benefits_dollars=("benefits_dollars", "sum"), services=("services", "sum"))
    line_chart(annual, "financial_year", "benefits_dollars", "Medicare benefits paid by financial year",
               args.output_root / "01_benefits_by_financial_year", args.logo)
    remove_old_quarterly_overview(args.output_root, args.website_dir)
    if not args.overview_only:
        for financial_year in complete_years:
            period_charts(data[data.financial_year == financial_year], f"{financial_year} annual",
                          args.output_root / f"{financial_year}_annual", args.logo)
        for quarter in sorted(data.financial_quarter.unique()):
            period_charts(data[data.financial_quarter == quarter], quarter.replace("_", " "),
                          args.output_root / quarter, args.logo)
    png_count = len(list(args.output_root.rglob("*.png")))
    svg_count = len(list(args.output_root.rglob("*.svg")))
    if not png_count or png_count != svg_count:
        raise RuntimeError(f"Incomplete MBS chart output: {png_count} PNG and {svg_count} SVG files")
    copied = 0 if args.no_website_copy else copy_website_assets(args.output_root, args.website_dir)
    print(f"Created {png_count} PNG and {svg_count} SVG charts in: {args.output_root.resolve()}")
    if not args.no_website_copy:
        print(f"Copied {copied} website-ready SVG/CSV files to: {args.website_dir.resolve()}")


if __name__ == "__main__":
    main()
