"""Generate APET public-hospital-funding trend and annual comparison charts."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter

BLUE, GREEN, RED = "#1f77b4", "#6aa84f", "#c0504d"
NHFB_URL = "https://www.publichospitalfunding.gov.au/public-hospital-funding/report"
APET_URL, X_URL = "https://auspublicexp.org/", "https://x.com/auspublicexp"
plt.rcParams["svg.fonttype"] = "none"


def dollar_tick(value, _position):
    return f"${value / 1e9:,.0f}b"


def mirror(path, output_root, website_root):
    if path.suffix.lower() not in {".svg", ".csv"}:
        return
    destination = website_root / path.relative_to(output_root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if path.resolve() != destination.resolve():
        shutil.copy2(path, destination)


def save_data(data, output, output_root, website_root):
    path = output.with_name(output.name + "_data.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(path, index=False)
    mirror(path, output_root, website_root)


def finish(fig, ax, output, logo, output_root, website_root, note, grid_axis="x"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, linestyle="--", alpha=.22)
    ax.set_axisbelow(True)
    if logo.exists():
        logo_ax = fig.add_axes([.025, .008, .105, .105])
        logo_ax.imshow(mpimg.imread(logo)); logo_ax.axis("off")
    links = [
        ("Source: National Health Funding Body via ", None, "#555"),
        ("publichospitalfunding.gov.au", NHFB_URL, "#0d6efd"), ("  |  ", None, "#555"),
        ("auspublicexp.org", APET_URL, "#0d6efd"),
        ("  |  Australian Public Expense Tracker  |  ", None, "#555"),
        ("@auspublicexp", X_URL, "#0d6efd"),
    ]
    x = .15
    for label, url, colour in links:
        artist = fig.text(x, .04, label, fontsize=8.5, color=colour, url=url)
        fig.canvas.draw()
        x += artist.get_window_extent(renderer=fig.canvas.get_renderer()).width / fig.bbox.width
    fig.text(.15, .02, note, fontsize=7.5, color="#555")
    fig.subplots_adjust(left=.18, right=.96, top=.83, bottom=.18)
    output.parent.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "svg"):
        saved = output.with_suffix("." + extension)
        fig.savefig(saved, dpi=180, bbox_inches="tight")
        mirror(saved, output_root, website_root)
    plt.close(fig)


def line_chart(data, x, series, title, output, logo, output_root, website_root, note):
    pivot = data.pivot(index=x, columns=series, values="payment_dollars")
    fig, ax = plt.subplots(figsize=(12, 7))
    for name in pivot.columns:
        ax.plot(pivot.index, pivot[name], marker="o", linewidth=2.5, label=name)
    ax.set_title(title, fontsize=20, loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(dollar_tick)); ax.tick_params(axis="x", rotation=35)
    ax.legend(ncol=4, frameon=False, loc="upper left")
    save_data(data, output, output_root, website_root)
    finish(fig, ax, output, logo, output_root, website_root, note, "y")


def signed_bar(data, label, value, title, output, logo, output_root, website_root, note, percent=False):
    data = data.sort_values(value)
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(data[label], data[value], color=[GREEN if v >= 0 else RED for v in data[value]])
    ax.axvline(0, color="#333", linewidth=.8); ax.set_title(title, fontsize=20, loc="left")
    ax.margins(x=.16)
    if percent:
        ax.xaxis.set_major_formatter(PercentFormatter()); labels = [f"{v:+.1f}%" for v in data[value]]
    else:
        ax.xaxis.set_major_formatter(FuncFormatter(dollar_tick)); labels = [f"${v / 1e9:+,.2f}b" for v in data[value]]
    ax.bar_label(bars, labels=labels, padding=4, fontsize=9)
    save_data(data.sort_values(value, ascending=False), output, output_root, website_root)
    finish(fig, ax, output, logo, output_root, website_root, note)


def overview_charts(states, categories, output_root, logo, website_root):
    note = "Nominal cash-basis payments; values are not adjusted for inflation."
    totals = states.groupby("financial_year", as_index=False)["payment_dollars"].sum()
    totals["change_dollars"] = totals.payment_dollars.diff()
    totals["change_percent"] = totals.payment_dollars.pct_change() * 100
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.plot(totals.financial_year, totals.payment_dollars, marker="o", linewidth=3, color=BLUE)
    ax.set_title("Public hospital funding payments over time", fontsize=20, loc="left")
    ax.yaxis.set_major_formatter(FuncFormatter(dollar_tick)); ax.tick_params(axis="x", rotation=35)
    save_data(totals, output_root / "01_total_payments_trend", output_root, website_root)
    finish(fig, ax, output_root / "01_total_payments_trend", logo, output_root, website_root, note, "y")
    changes = totals.dropna(subset=["change_percent"])
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(changes.financial_year, changes.change_percent,
                  color=[GREEN if v >= 0 else RED for v in changes.change_percent])
    ax.axhline(0, color="#333", linewidth=.8)
    ax.set_title("Annual change in public hospital funding payments", fontsize=20, loc="left")
    ax.yaxis.set_major_formatter(PercentFormatter()); ax.tick_params(axis="x", rotation=35)
    ax.bar_label(bars, labels=[f"{v:+.1f}%" for v in changes.change_percent], padding=3)
    save_data(changes, output_root / "02_annual_payment_change", output_root, website_root)
    finish(fig, ax, output_root / "02_annual_payment_change", logo, output_root, website_root, note, "y")
    state_totals = states.groupby(["financial_year", "state_territory"], as_index=False).payment_dollars.sum()
    line_chart(state_totals, "financial_year", "state_territory",
               "Public hospital funding trends by state and territory",
               output_root / "03_state_payment_trends", logo, output_root, website_root, note)
    methods = categories.groupby(["financial_year", "funding_method"], as_index=False).payment_dollars.sum()
    line_chart(methods, "financial_year", "funding_method", "Activity-based and block payments over time",
               output_root / "04_funding_method_trends", logo, output_root, website_root,
               note + " Service categories do not cover every payment type.")
    print(f"Created long-term overview charts: {output_root}")


def annual_charts(states, categories, year, previous_year, output_root, logo, website_root):
    folder = output_root / f"{year}_annual"
    note = "Nominal cash-basis payments; values are not adjusted for inflation."
    current = states[states.financial_year == year].groupby("state_territory", as_index=False).payment_dollars.sum()
    current["share_percent"] = current.payment_dollars / current.payment_dollars.sum() * 100
    share = current.sort_values("share_percent")
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(share.state_territory, share.share_percent, color=BLUE)
    ax.set_title(f"State and territory share of reported payments\n{year}", fontsize=20, loc="left")
    ax.xaxis.set_major_formatter(PercentFormatter()); ax.bar_label(bars, labels=[f"{v:.1f}%" for v in share.share_percent], padding=4)
    save_data(current.sort_values("share_percent", ascending=False), folder / "01_state_share", output_root, website_root)
    finish(fig, ax, folder / "01_state_share", logo, output_root, website_root, note)
    if previous_year:
        previous = states[states.financial_year == previous_year].groupby("state_territory", as_index=False).payment_dollars.sum()
        previous = previous.rename(columns={"payment_dollars": "previous_payment_dollars"})
        change = current.merge(previous, on="state_territory", how="outer").fillna(0)
        change = change.rename(columns={"payment_dollars": "current_payment_dollars"})
        change["change_dollars"] = change.current_payment_dollars - change.previous_payment_dollars
        change["change_percent"] = change.change_dollars / change.previous_payment_dollars.replace(0, pd.NA) * 100
        signed_bar(change.dropna(subset=["change_percent"]), "state_territory", "change_percent",
                   f"Change in payments by state and territory\n{previous_year} to {year}",
                   folder / "02_state_change_from_previous_year", logo, output_root, website_root, note, True)
        current_cat = categories[categories.financial_year == year].groupby("service_category", as_index=False).payment_dollars.sum().rename(columns={"payment_dollars": "current_payment_dollars"})
        previous_cat = categories[categories.financial_year == previous_year].groupby("service_category", as_index=False).payment_dollars.sum().rename(columns={"payment_dollars": "previous_payment_dollars"})
        cat = current_cat.merge(previous_cat, on="service_category", how="outer").fillna(0)
        cat["change_dollars"] = cat.current_payment_dollars - cat.previous_payment_dollars
        cat = cat.loc[cat.change_dollars.abs().nlargest(10).index]
        signed_bar(cat, "service_category", "change_dollars",
                   f"Largest changes in service-category payments\n{previous_year} to {year}",
                   folder / "03_category_change_from_previous_year", logo, output_root, website_root,
                   note + " Categories do not cover every payment type.")
    print(f"Created annual comparison charts for {year}: {folder}")


def remove_old_annual_assets(years, output_root, website_root):
    old = ("01_payments_by_state", "02_payments_by_service_category", "03_payments_by_funding_method")
    for root in (output_root, website_root):
        for year in years:
            folder = root / f"{year}_annual"
            for base in old:
                for suffix in (".png", ".svg", "_data.csv"):
                    path = folder / (base + suffix)
                    if path.exists(): path.unlink()


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=project_root / "data/public_hospital_funding/normalized")
    parser.add_argument("--output-root", type=Path, default=project_root / "output/public_hospital_funding")
    parser.add_argument("--website-output-root", type=Path, default=project_root / "website/public_html/charts/public_hospital_funding")
    parser.add_argument("--financial-year")
    parser.add_argument("--all-financial-years", action="store_true")
    parser.add_argument("--logo", type=Path, default=project_root / "branding/APETLogo400x400.png")
    args = parser.parse_args()
    states = pd.read_csv(args.data_dir / "monthly_payments_by_state.csv")
    categories = pd.read_csv(args.data_dir / "monthly_payments_by_service_category.csv")
    available = sorted(states.financial_year.unique())
    if args.financial_year and args.all_financial_years:
        raise ValueError("Use either --financial-year or --all-financial-years, not both")
    years = available if args.all_financial_years else [args.financial_year or available[-1]]
    unknown = sorted(set(years) - set(available))
    if unknown: raise ValueError(f"Unknown financial year(s) {unknown}; available: {available}")
    args.output_root.mkdir(parents=True, exist_ok=True); args.website_output_root.mkdir(parents=True, exist_ok=True)
    remove_old_annual_assets(years, args.output_root, args.website_output_root)
    overview_charts(states, categories, args.output_root, args.logo, args.website_output_root)
    for year in years:
        position = available.index(year)
        annual_charts(states, categories, year, available[position - 1] if position else None,
                      args.output_root, args.logo, args.website_output_root)
    explorer_builder = script_dir / "build_public_hospital_funding_explorer_index.py"
    if explorer_builder.exists():
        subprocess.run([sys.executable, str(explorer_builder), "--data-dir", str(args.data_dir)], check=True)


if __name__ == "__main__":
    main()
