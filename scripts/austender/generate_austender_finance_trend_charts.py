"""Generate APET long-term AusTender charts from Finance's official annual statistics.

This deliberately uses the Department of Finance annual series, not APET's weekly
AusTender archive. The two sources are kept separate because older contracts that
appear in a recent weekly export do not form a complete historical collection.
"""
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

plt.rcParams["svg.fonttype"] = "none"

BLUE = "#4472A8"
FINANCE_URL = (
    "https://www.finance.gov.au/government/procurement/"
    "statistics-australian-government-procurement-contracts-"
)
APET_URL = "https://auspublicexp.org/"
X_URL = "https://x.com/auspublicexp"

# Small, published historical series transcribed from the Department of Finance
# table. Values are maximum reported contract values, not expenditure paid.
ANNUAL_DATA = [
    ("FY2016-17", 47_354.6, 64_092),
    ("FY2017-18", 71_127.3, 73_458),
    ("FY2018-19", 64_454.6, 78_150),
    ("FY2019-20", 53_975.4, 81_174),
    ("FY2020-21", 69_794.5, 84_054),
    ("FY2021-22", 80_793.4, 92_303),
    ("FY2022-23", 74_824.4, 83_625),
    ("FY2023-24", 99_641.1, 83_453),
    ("FY2024-25", 104_899.8, 86_926),
]


def billions(value: float, _position: int = 0) -> str:
    return f"${value / 1_000:,.0f}b"


def thousands(value: float, _position: int = 0) -> str:
    return f"{value / 1_000:,.0f}k"


def add_footer(fig: plt.Figure, logo: Path) -> None:
    if logo.exists():
        area = fig.add_axes([0.025, 0.008, 0.105, 0.105])
        area.imshow(mpimg.imread(logo))
        area.axis("off")

    parts = [
        ("Source: Australian Government Department of Finance via ", None, "#555555"),
        ("finance.gov.au", FINANCE_URL, "#0d6efd"),
        ("  |  ", None, "#555555"),
        ("auspublicexp.org", APET_URL, "#0d6efd"),
        ("  |  Australian Public Expense Tracker  |  ", None, "#555555"),
        ("@auspublicexp", X_URL, "#0d6efd"),
    ]
    x = 0.15
    for label, url, colour in parts:
        artist = fig.text(x, 0.04, label, fontsize=8.1, color=colour, url=url)
        fig.canvas.draw()
        x += artist.get_window_extent(
            renderer=fig.canvas.get_renderer()
        ).width / fig.bbox.width

    fig.text(
        0.15,
        0.018,
        "Maximum reported contract values, including multi-year contracts; not annual expenditure paid. Reporting changed from FY2024-25.",
        fontsize=7.1,
        color="#555555",
    )


def finish(fig: plt.Figure, ax: plt.Axes, output: Path, logo: Path) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.24)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", rotation=35)
    add_footer(fig, logo)
    fig.subplots_adjust(left=0.11, right=0.96, top=0.80, bottom=0.23)
    output.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "svg"):
        fig.savefig(output.with_suffix("." + suffix), dpi=180, bbox_inches="tight")
    plt.close(fig)


def mark_reporting_change(ax: plt.Axes) -> None:
    ax.axvline(7.5, color="#777777", linestyle=":", linewidth=1.4)
    ax.text(
        7.55,
        0.97,
        "Reporting change\nfrom FY2024-25",
        transform=ax.get_xaxis_transform(),
        va="top",
        fontsize=8,
        color="#555555",
    )


def value_chart(data: pd.DataFrame, output: Path, logo: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["financial_year"],
        data["reported_contract_value_millions"],
        marker="o",
        linewidth=3,
        color=BLUE,
    )
    ax.set_title(
        "Maximum reported value of Australian Government contracts\nby financial year",
        fontsize=19,
        loc="left",
    )
    ax.set_ylabel("Maximum reported contract value")
    ax.yaxis.set_major_formatter(FuncFormatter(billions))
    for x, value in zip(
        data["financial_year"], data["reported_contract_value_millions"]
    ):
        ax.annotate(
            billions(value),
            (x, value),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
        )
    ax.margins(y=0.17)
    mark_reporting_change(ax)
    finish(fig, ax, output, logo)


def count_chart(data: pd.DataFrame, output: Path, logo: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(
        data["financial_year"],
        data["number_of_contracts"],
        marker="o",
        linewidth=3,
        color=BLUE,
    )
    ax.set_title(
        "Number of Australian Government contracts reported\nby financial year",
        fontsize=19,
        loc="left",
    )
    ax.set_ylabel("Number of contracts")
    ax.yaxis.set_major_formatter(FuncFormatter(thousands))
    for x, value in zip(data["financial_year"], data["number_of_contracts"]):
        ax.annotate(
            f"{value:,.0f}",
            (x, value),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
        )
    ax.margins(y=0.17)
    mark_reporting_change(ax)
    finish(fig, ax, output, logo)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=project_root / "output/austender/trends"
    )
    parser.add_argument(
        "--website-dir",
        type=Path,
        default=project_root / "website/public_html/charts/austender/trends",
    )
    parser.add_argument(
        "--logo", type=Path, default=project_root / "branding/APETLogo400x400.png"
    )
    parser.add_argument(
        "--skip-website", action="store_true", help="Do not copy SVG/CSV website assets"
    )
    args = parser.parse_args()

    data = pd.DataFrame(
        ANNUAL_DATA,
        columns=[
            "financial_year",
            "reported_contract_value_millions",
            "number_of_contracts",
        ],
    )
    if data["financial_year"].duplicated().any() or (data.iloc[:, 1:] < 0).any().any():
        raise ValueError("The embedded Finance annual statistics failed validation")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    data_file = args.output_dir / "finance_austender_annual_statistics.csv"
    data.to_csv(data_file, index=False)
    value_chart(
        data,
        args.output_dir / "01_reported_contract_value_by_financial_year",
        args.logo,
    )
    count_chart(
        data,
        args.output_dir / "02_number_of_contracts_by_financial_year",
        args.logo,
    )

    if not args.skip_website:
        args.website_dir.mkdir(parents=True, exist_ok=True)
        for source in args.output_dir.iterdir():
            if source.suffix.lower() == ".svg" or source.suffix.lower() == ".csv":
                shutil.copy2(source, args.website_dir / source.name)

    print(f"Created 2 Finance/AusTender trend charts: {args.output_dir.resolve()}")
    if not args.skip_website:
        print(f"Copied website-ready SVG/CSV files to: {args.website_dir.resolve()}")
    print("The historical value-band chart was not created because comparable annual band data is unavailable.")


if __name__ == "__main__":
    main()
