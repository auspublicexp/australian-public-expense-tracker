"""Generate the first APET charts from normalized annual ABS GFS data."""

from argparse import ArgumentParser
import os
from pathlib import Path
import re
import shutil
import sys
import matplotlib
matplotlib.use("Agg")  # Safe when APET runs without a desktop display.
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "abs_gfs" / "normalized"
LEGACY_DATA_DIR = Path(__file__).resolve().parent / "data" / "abs_gfs" / "normalized"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from chart_helpers import add_brand_logo

APET_BLUE, ACCENT = "#1f77b4", "#e69138"
SOURCE = "ABS, Government Finance Statistics, Annual, 2024-25"
ABS_URL = "https://www.abs.gov.au/statistics/economy/government"
APET_URL = "https://auspublicexp.org/"
X_URL = "https://x.com/auspublicexp"
plt.rcParams["svg.fonttype"] = "none"

website_dir = os.environ.get("APET_ABS_GFS_WEBSITE_CHART_DIR")
WEBSITE_CHART_DIR = (
    Path(website_dir).expanduser()
    if website_dir
    else PROJECT_ROOT / "website" / "public_html" / "charts" / "abs_gfs"
)
published_output_dir = os.environ.get("APET_ABS_GFS_OUTPUT_DIR")
PUBLISHED_OUTPUT_DIR = Path(published_output_dir).expanduser() if published_output_dir else None


def destination_for(path: Path, root: Path) -> Path:
    """Keep financial-year subfolders when copying a generated chart asset."""
    if re.fullmatch(r"FY\d{4}-\d{2}_annual", path.parent.name):
        return root / path.parent.name / path.name
    return root / path.name


def copy_asset(path: Path, root: Path, label: str) -> None:
    destination = destination_for(path, root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if path.resolve() == destination.resolve():
        return
    shutil.copy2(path, destination)
    print(f"Copied {label} asset: {destination}")


def mirror_to_website(path: Path) -> None:
    """Copy a generated SVG/CSV into the matching website annual folder."""
    if path.suffix.lower() not in {".svg", ".csv"}:
        return
    copy_asset(path, WEBSITE_CHART_DIR, "website")


def mirror_to_published_output(path: Path) -> None:
    """Optionally copy PNG, SVG and CSV assets to APET's main output folder."""
    if PUBLISHED_OUTPUT_DIR is not None and path.suffix.lower() in {".png", ".svg", ".csv"}:
        copy_asset(path, PUBLISHED_OUTPUT_DIR, "output")


def save_chart_data(data: pd.DataFrame, output: Path) -> None:
    data_path = output.with_name(output.name + "_data.csv")
    data.to_csv(data_path, index=False)
    mirror_to_website(data_path)
    mirror_to_published_output(data_path)


def finish(fig, ax, output: Path, note: str) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.22)
    add_brand_logo(fig)

    # Separate text artists make the blue labels clickable in SVG output,
    # matching the established APET AusTender, IPEA and GrantConnect format.
    footer_segments = [
        ("Source: Australian Bureau of Statistics export via ", None, "#555555"),
        ("abs.gov.au", ABS_URL, "#0d6efd"),
        ("  |  ", None, "#555555"),
        ("auspublicexp.org", APET_URL, "#0d6efd"),
        ("  |  Australian Public Expense Tracker  |  ", None, "#555555"),
        ("@auspublicexp", X_URL, "#0d6efd"),
    ]
    x = 0.17
    for label, url, color in footer_segments:
        artist = fig.text(
            x, 0.038, label,
            ha="left", va="bottom", fontsize=9, color=color, url=url,
        )
        fig.canvas.draw()
        bbox = artist.get_window_extent(renderer=fig.canvas.get_renderer())
        x += bbox.width / fig.bbox.width

    fig.text(0.17, 0.018, note, ha="left", va="bottom", fontsize=8, color="#555555")
    fig.subplots_adjust(left=0.1, right=0.97, top=0.86, bottom=0.19)
    for extension in ("png", "svg"):
        saved = output.with_suffix(f".{extension}")
        fig.savefig(saved, dpi=180, bbox_inches="tight")
        mirror_to_website(saved)
        mirror_to_published_output(saved)
    plt.close(fig)


def trend(summary: pd.DataFrame, output_dir: Path) -> None:
    values = summary["value_millions"] / 1000
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(summary["financial_year"], values, color=APET_BLUE, linewidth=3, marker="o")
    ax.fill_between(range(len(values)), values, alpha=0.10, color=APET_BLUE)
    ax.set_title("Australian general government expenses passed $1 trillion", fontsize=21, loc="left")
    ax.set_ylabel("$ billions")
    ax.tick_params(axis="x", rotation=35)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:,.0f}b"))
    ax.annotate(f"${values.iloc[-1]:,.1f}b", (len(values)-1, values.iloc[-1]),
                xytext=(-5, 14), textcoords="offset points", ha="right", weight="bold")
    finish(fig, ax, output_dir / "01_total_expenses_trend",
           "Current prices; original series; accrual basis")
    save_chart_data(summary[["financial_year", "value_millions"]],
                    output_dir / "01_total_expenses_trend")


def purpose_latest(purposes: pd.DataFrame, output_dir: Path) -> None:
    latest = purposes["financial_year"].max()
    data = purposes[purposes["financial_year"] == latest].copy()
    data["billions"] = data["value_millions"] / 1000
    data = data.sort_values("billions")
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(data["purpose"], data["billions"], color=APET_BLUE)
    ax.set_title(f"Where general government expenses went in {latest}", fontsize=21, loc="left")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:,.0f}b"))
    ax.bar_label(bars, labels=[f"${v:,.1f}b" for v in data["billions"]], padding=4)
    ax.set_xlim(0, data["billions"].max() * 1.18)
    finish(fig, ax, output_dir / "02_expenses_by_purpose",
           "All Australia general government; current prices")
    save_chart_data(data[["purpose", "value_millions"]].sort_values("value_millions", ascending=False),
                    output_dir / "02_expenses_by_purpose")


def purpose_change(purposes: pd.DataFrame, output_dir: Path) -> None:
    first, latest = purposes["financial_year"].min(), purposes["financial_year"].max()
    pivot = purposes.pivot(index="purpose", columns="financial_year", values="value_millions")
    change = ((pivot[latest] / pivot[first]) - 1).sort_values()
    fig, ax = plt.subplots(figsize=(12, 8))
    colors = [ACCENT if value >= change.median() else APET_BLUE for value in change]
    bars = ax.barh(change.index, change.values, color=colors)
    ax.set_title(
        f"Fastest-growing expense purposes\nNominal change, {first} to {latest}",
        fontsize=19,
        loc="left",
    )
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax.bar_label(bars, labels=[f"{v:.0%}" for v in change], padding=4)
    ax.set_xlim(0, change.max() * 1.17)
    finish(fig, ax, output_dir / "03_purpose_growth_since_2015_16",
           "Nominal change in current-price expenses; not adjusted for inflation")
    save_chart_data(change.rename("nominal_change_fraction").reset_index(),
                    output_dir / "03_purpose_growth_since_2015_16")


def purpose_shares(purposes: pd.DataFrame, output_dir: Path) -> None:
    totals = purposes.groupby("financial_year")["value_millions"].transform("sum")
    data = purposes.assign(share=purposes["value_millions"] / totals)
    selected = ["Social protection", "Health", "Education", "General public services", "Defence"]
    pivot = data[data["purpose"].isin(selected)].pivot(index="financial_year", columns="purpose", values="share")
    fig, ax = plt.subplots(figsize=(12, 7))
    for column in selected:
        ax.plot(pivot.index, pivot[column], linewidth=2.5, marker="o", label=column)
    ax.set_title("How the mix of government expenses has changed", fontsize=21, loc="left")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.tick_params(axis="x", rotation=35)
    ax.legend(frameon=False, ncol=2)
    finish(fig, ax, output_dir / "04_major_purpose_shares",
           "Share of All Australia general government expenses")
    save_chart_data(pivot.reset_index(), output_dir / "04_major_purpose_shares")


def change_from_previous_year(purposes: pd.DataFrame, year: str, output_dir: Path) -> None:
    years = sorted(purposes["financial_year"].unique())
    position = years.index(year)
    if position == 0:
        return
    previous = years[position - 1]
    pivot = purposes[purposes["financial_year"].isin([previous, year])].pivot(
        index="purpose", columns="financial_year", values="value_millions")
    change = ((pivot[year] / pivot[previous]) - 1).sort_values()
    fig, ax = plt.subplots(figsize=(12, 8))
    colors = [ACCENT if value >= 0 else "#777777" for value in change]
    bars = ax.barh(change.index, change.values, color=colors)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_title(f"How expenses changed from {previous} to {year}", fontsize=20, loc="left")
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax.bar_label(bars, labels=[f"{value:+.1%}" for value in change], padding=4)
    margin = max(abs(change.min()), abs(change.max())) * 0.18
    ax.set_xlim(change.min() - margin, change.max() + margin)
    finish(fig, ax, output_dir / "06_change_from_previous_financial_year",
           "Nominal change in current-price expenses; not adjusted for inflation")
    save_chart_data(change.rename("nominal_change_fraction").reset_index(),
                    output_dir / "06_change_from_previous_financial_year")


def expenses_by_level(levels: pd.DataFrame, year: str, output_dir: Path) -> None:
    data = levels[levels["financial_year"] == year].copy()
    data["value_billions"] = data["value_millions"] / 1000
    data = data.sort_values("value_billions")
    fig, ax = plt.subplots(figsize=(12, 6.5))
    bars = ax.barh(data["government_level"], data["value_billions"], color=APET_BLUE)
    ax.set_title(f"General government expenses by level\n{year}", fontsize=20, loc="left")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:,.0f}b"))
    ax.bar_label(bars, labels=[f"${value:,.1f}b" for value in data["value_billions"]], padding=4)
    ax.set_xlim(0, data["value_billions"].max() * 1.18)
    finish(fig, ax, output_dir / "07_expenses_by_government_level",
           "Published level totals are not additive because of transfers between governments")
    save_chart_data(data[["government_level", "value_millions"]].sort_values("value_millions", ascending=False),
                    output_dir / "07_expenses_by_government_level")


def every_hundred_dollars(purposes: pd.DataFrame, output_dir: Path) -> None:
    latest = purposes["financial_year"].max()
    data = purposes[purposes["financial_year"] == latest].copy()
    data["dollars_per_100"] = data["value_millions"] / data["value_millions"].sum() * 100
    data = data.sort_values("dollars_per_100").tail(6)
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(data["purpose"], data["dollars_per_100"], color=APET_BLUE)
    ax.set_title(f"Where every $100 of government expenses went\n{latest}", fontsize=20, loc="left")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.bar_label(bars, labels=[f"${v:,.1f}" for v in data["dollars_per_100"]], padding=4)
    ax.set_xlim(0, data["dollars_per_100"].max() * 1.18)
    finish(fig, ax, output_dir / "05_out_of_every_100",
           "Largest six purposes; shares of All Australia general government expenses")
    save_chart_data(data[["purpose", "dollars_per_100"]].sort_values("dollars_per_100", ascending=False),
                    output_dir / "05_out_of_every_100")


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR if DEFAULT_DATA_DIR.exists() else LEGACY_DATA_DIR,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "output" / "abs_gfs",
    )
    parser.add_argument("--financial-year", help="Generate one FY such as FY2024-25; default is every FY")
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(args.data_dir / "annual_expenses.csv")
    purposes = pd.read_csv(args.data_dir / "expenses_by_purpose.csv")
    levels = pd.read_csv(args.data_dir / "expenses_by_level.csv")

    # The long-run charts belong at the ABS landing level rather than being
    # repeated identically inside every financial-year folder.
    trend(summary, args.output_root)
    purpose_change(purposes, args.output_root)
    purpose_shares(purposes, args.output_root)

    available_years = sorted(purposes["financial_year"].unique())
    years = [args.financial_year] if args.financial_year else available_years
    unknown = set(years) - set(available_years)
    if unknown:
        raise ValueError(f"Unknown financial year: {sorted(unknown)}; available: {available_years}")

    for year in years:
        year_dir = args.output_root / f"{year}_annual"
        year_dir.mkdir(parents=True, exist_ok=True)
        year_purposes = purposes[purposes["financial_year"] == year]
        purpose_latest(year_purposes, year_dir)
        every_hundred_dollars(year_purposes, year_dir)
        change_from_previous_year(purposes, year, year_dir)
        expenses_by_level(levels, year, year_dir)
        print(f"Created financial-year charts: {year_dir}")

    print(f"Finished ABS GFS charts for {len(years)} financial year(s).")


if __name__ == "__main__":
    main()
