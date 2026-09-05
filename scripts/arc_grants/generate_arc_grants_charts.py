"""Generate APET overview and calendar-year ARC grant-allocation charts."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

BLUE, GREEN = "#1f77b4", "#6aa84f"
ARC_URL = "https://www.arc.gov.au/funding-research/funding-outcomes/grants-dataset"
APET_URL, X_URL = "https://auspublicexp.org/", "https://x.com/auspublicexp"
NOTE = "Whole-of-project ARC allocations grouped by funding commencement year; not cash paid in that year."
plt.rcParams["svg.fonttype"] = "none"


def money_tick(value, _position):
    return f"${value / 1e9:,.1f}b" if abs(value) >= 1e9 else f"${value / 1e6:,.0f}m"


def add_logo(fig, logo):
    if logo.exists():
        ax = fig.add_axes([.025, .008, .105, .105]); ax.imshow(mpimg.imread(logo)); ax.axis("off")


def finish(fig, ax, output, logo, note=NOTE, grid_axis="x"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, linestyle="--", alpha=.22); ax.set_axisbelow(True)
    add_logo(fig, logo)
    parts = [("Source: Australian Research Council via ", None, "#555"),
             ("arc.gov.au", ARC_URL, "#0d6efd"), ("  |  ", None, "#555"),
             ("auspublicexp.org", APET_URL, "#0d6efd"),
             ("  |  Australian Public Expense Tracker  |  ", None, "#555"),
             ("@auspublicexp", X_URL, "#0d6efd")]
    x = .15
    for label, url, colour in parts:
        artist = fig.text(x, .04, label, fontsize=8.5, color=colour, url=url)
        fig.canvas.draw(); x += artist.get_window_extent(renderer=fig.canvas.get_renderer()).width / fig.bbox.width
    fig.text(.15, .02, note, fontsize=7.5, color="#555")
    fig.subplots_adjust(left=.20, right=.96, top=.83, bottom=.18)
    output.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "svg"):
        fig.savefig(output.with_suffix("." + suffix), dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_data(data, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output.with_name(output.name + "_data.csv"), index=False)


def horizontal(data, label, value, title, output, logo, top=10):
    data = data.nlargest(top, value).sort_values(value)
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(data[label], data[value], color=BLUE)
    ax.set_title(title, fontsize=20, loc="left"); ax.xaxis.set_major_formatter(FuncFormatter(money_tick))
    ax.bar_label(bars, labels=[money_tick(v, 0) for v in data[value]], padding=4, fontsize=9)
    ax.margins(x=.15); save_data(data.sort_values(value, ascending=False), output); finish(fig, ax, output, logo)


def overview(data, output_root, logo):
    annual = data.groupby("funding_commencement_year", as_index=False).agg(
        projects=("project_code", "count"), current_funding_dollars=("current_funding_dollars", "sum"))
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(annual.funding_commencement_year, annual.current_funding_dollars, marker="o", color=BLUE, linewidth=2.5)
    ax.set_title("ARC grant allocations by funding commencement year", fontsize=20, loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(money_tick)); ax.tick_params(axis="x", rotation=45)
    save_data(annual, output_root / "01_funding_by_commencement_year"); finish(fig, ax, output_root / "01_funding_by_commencement_year", logo, grid_axis="y")

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(annual.funding_commencement_year, annual.projects, color=GREEN)
    ax.set_title("Number of ARC projects by funding commencement year", fontsize=20, loc="left")
    ax.bar_label(bars, fontsize=7, rotation=90, padding=3); ax.tick_params(axis="x", rotation=45)
    save_data(annual[["funding_commencement_year", "projects"]], output_root / "02_projects_by_commencement_year")
    finish(fig, ax, output_root / "02_projects_by_commencement_year", logo, grid_axis="y")

    organisations = data.groupby("administering_organisation", as_index=False).agg(
        projects=("project_code", "count"), current_funding_dollars=("current_funding_dollars", "sum"))
    horizontal(organisations, "administering_organisation", "current_funding_dollars",
               "Largest administering organisations in the ARC dataset",
               output_root / "03_largest_administering_organisations", logo, 15)

    programs = data.groupby(["funding_commencement_year", "program_name"], as_index=False).current_funding_dollars.sum()
    pivot = programs.pivot(index="funding_commencement_year", columns="program_name", values="current_funding_dollars").fillna(0)
    fig, ax = plt.subplots(figsize=(12, 7))
    for program in pivot.columns:
        ax.plot(pivot.index, pivot[program], marker="o", linewidth=2.5, label=program)
    ax.set_title(
        "ARC allocation trends by program\n"
        "Discovery: fundamental research  |  Linkage: collaborative research, partnerships and infrastructure",
        fontsize=17, loc="left",
    )
    ax.yaxis.set_major_formatter(FuncFormatter(money_tick)); ax.tick_params(axis="x", rotation=45); ax.legend(frameon=False)
    save_data(programs, output_root / "04_funding_by_program_over_time")
    finish(fig, ax, output_root / "04_funding_by_program_over_time", logo, grid_axis="y")


def calendar_year(data, year, output_root, logo):
    year_data = data[data.funding_commencement_year == year].copy()
    folder = output_root / f"CY{year}"
    organisations = year_data.groupby("administering_organisation", as_index=False).agg(
        projects=("project_code", "count"), current_funding_dollars=("current_funding_dollars", "sum"))
    horizontal(organisations, "administering_organisation", "current_funding_dollars",
               f"ARC allocations by administering organisation\nCalendar year {year}", folder / "01_funding_by_organisation", logo)
    schemes = year_data.groupby("scheme_name", as_index=False).agg(
        projects=("project_code", "count"), current_funding_dollars=("current_funding_dollars", "sum"))
    horizontal(schemes, "scheme_name", "current_funding_dollars",
               f"ARC allocations by scheme\nCalendar year {year}", folder / "02_funding_by_scheme", logo)
    fields = year_data.dropna(subset=["primary_field_of_research"]).groupby("primary_field_of_research", as_index=False).agg(
        projects=("project_code", "count"), current_funding_dollars=("current_funding_dollars", "sum"))
    horizontal(fields, "primary_field_of_research", "current_funding_dollars",
               f"Largest primary fields of research\nCalendar year {year}", folder / "03_funding_by_research_field", logo)
    grants = year_data[["project_code", "administering_organisation", "lead_investigator", "grant_summary",
                        "current_funding_dollars", "official_record_url"]].copy()
    grants["chart_label"] = grants.project_code + " — " + grants.administering_organisation
    horizontal(grants, "chart_label", "current_funding_dollars",
               f"Largest ARC project allocations\nCalendar year {year}", folder / "04_largest_projects", logo)
    print(f"Created ARC charts for calendar year {year}: {folder}")


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-file", type=Path, default=project_root / "data/arc_grants/normalized/arc_grants_projects.csv")
    parser.add_argument("--output-root", type=Path, default=project_root / "output/arc_grants")
    parser.add_argument("--calendar-year", type=int)
    parser.add_argument("--all-calendar-years", action="store_true")
    parser.add_argument("--include-current-year", action="store_true",
                        help="Include the still-in-progress calendar year in charts")
    parser.add_argument("--logo", type=Path, default=project_root / "branding/APETLogo400x400.png")
    args = parser.parse_args()
    data = pd.read_csv(args.data_file, low_memory=False)
    available = sorted(int(year) for year in data.funding_commencement_year.dropna().unique())
    completed = available if args.include_current_year else [year for year in available if year < datetime.now().year]
    years = completed if args.all_calendar_years else [args.calendar_year or completed[-1]]
    unknown = sorted(set(years) - set(available))
    if unknown: raise ValueError(f"Unknown calendar year(s): {unknown}")
    args.output_root.mkdir(parents=True, exist_ok=True)
    overview(data[data.funding_commencement_year.isin(completed)], args.output_root, args.logo)
    for year in years: calendar_year(data, year, args.output_root, args.logo)
    search_builder = Path(__file__).with_name("build_arc_grants_search_index.py")
    if search_builder.exists():
        print("\nUpdating the ARC website search index...")
        subprocess.run([sys.executable, str(search_builder), "--input-file", str(args.data_file)], check=True)


if __name__ == "__main__":
    main()

