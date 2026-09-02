from pathlib import Path
import os
import sys
import shutil

# ============================================================
# ADD PROJECT SCRIPTS FOLDER TO PYTHON PATH
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_DIR / "scripts"

sys.path.append(str(SCRIPTS_DIR))

# ============================================================
# IMPORT SHARED HELPERS
# ============================================================

import chart_helpers as chart_helpers_module
from chart_helpers import *

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["svg.fonttype"] = "none"

# ============================================================
# SETTINGS — CHANGE THIS FOR EACH QUARTER
# ============================================================

TARGET_CSV = None  # None = generate all available quarterly CSVs; set a filename to test one quarter

IPEA_SOURCE_TEXT = "IPEA parliamentary expenditure data via data.gov.au"

# ============================================================
# WEBSITE OUTPUT + CLICKABLE FOOTER
# ============================================================

website_chart_dir = os.environ.get("APET_IPEA_WEBSITE_CHART_DIR")
IPEA_WEBSITE_CHART_DIR = (
    Path(website_chart_dir).expanduser() if website_chart_dir else None
)


def mirror_file_to_website(source_path):
    """Copy an SVG/CSV into the matching website chart folder."""
    if IPEA_WEBSITE_CHART_DIR is None:
        return

    period_name = source_path.parent.name
    website_period_dir = IPEA_WEBSITE_CHART_DIR / period_name
    website_period_dir.mkdir(parents=True, exist_ok=True)

    destination = website_period_dir / source_path.name
    shutil.copy2(source_path, destination)
    print(f"Copied website asset: {destination}")


def add_ipea_footer(fig, ax, source_text=None):
    """Render one footer line with clickable visible text in SVG output."""
    chart_helpers_module.add_brand_logo(fig)

    segments = [
        ("Source: IPEA parliamentary expenditure data via ", None, "#555555"),
        ("data.gov.au", "https://data.gov.au/", "#0d6efd"),
        ("  |  ", None, "#555555"),
        ("ipea.gov.au", "https://www.ipea.gov.au/", "#0d6efd"),
        ("  |  ", None, "#555555"),
        ("auspublicexp.org", "https://auspublicexp.org/", "#0d6efd"),
        ("  |  Australian Public Expense Tracker  |  ", None, "#555555"),
        ("@auspublicexp", "https://x.com/auspublicexp", "#0d6efd"),
    ]

    x = 0.17
    y = 0.025

    for label, url, color in segments:
        artist = fig.text(
            x, y, label,
            ha="left", va="bottom",
            fontsize=11, color=color, url=url,
        )
        fig.canvas.draw()
        bbox = artist.get_window_extent(renderer=fig.canvas.get_renderer())
        x += bbox.width / fig.bbox.width


# Shared helper-based charts, if used, should get the same footer.
chart_helpers_module.add_standard_footer = add_ipea_footer


# ============================================================
# CSV COLUMN NAMES
# ============================================================

NAME_COL = "FullNameWithTitle"
PARTY_COL = "Party"
STATE_COL = "StateOrTerritory"
HIGH_LEVEL_COL = "HighLevelCategory"
MAJOR_COL = "MajorSubCategory"
AMOUNT_COL = "Amount"

# ============================================================
# CHART DEFINITIONS
# ============================================================

TOP_CHARTS = [
    ("04", "Top Parliamentary Expense Totals", "total", None),
    ("05", "Top Travel Spending", "major", [
        "Travel Allowance", "Family Travel", "Employee Travel", "International Travel",
        "Scheduled Commercial Transport", "Unscheduled Commercial Transport",
        "Other Car Costs", "Fares", "Parking", "Private-Plated Vehicle",
        "Private Vehicle Allowance", "Cancelled Transport",
        "Cabcharge / Other Car Costs", "COMCAR", "Domestic Travel",
        "Representing Australia", "Parliamentary Delegations",
        "Ministerial Visits", "Official Visits", "Representing a Minister",
    ]),
    ("06", "Top Domestic Travel", "major", ["Domestic Travel"]),
    ("07", "Top International Travel", "major", [
        "International Travel", "Representing Australia", "Parliamentary Delegations",
        "Ministerial Visits", "Official Visits", "Representing a Minister",
    ]),
    ("08", "Top COMCAR Spending", "major", ["COMCAR"]),
    ("09", "Top Travel Allowance", "major", ["Travel Allowance"]),
    ("10", "Top Printing and Communications", "major", [
        "Printing and Communications", "Additional Printing and Communications", "Publications",
    ]),
    ("11", "Top Publications", "major", ["Publications"]),
    ("12", "Top Telecommunications", "major", [
        "Telephonic Services", "Telecommunications - Usage",
        "Telecommunications - Residential - Official",
    ]),
    ("13", "Top Office Consumables and Services", "major", [
        "Office Consumables and Services"
    ]),
]

# ============================================================
# DATA LOADING
# ============================================================

def get_previous_csv(target_csv):
    csv_files = sorted(
        IPEA_DATA_DIR.glob("*_dataextract.csv"),
        key=lambda file: quarter_sort_key(file.stem)
    )

    for i, csv_file in enumerate(csv_files):
        if csv_file.name == target_csv and i > 0:
            return csv_files[i - 1]

    return None


def load_data(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = df.columns.str.strip()

    df[AMOUNT_COL] = (
        df[AMOUNT_COL]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
    )

    df[AMOUNT_COL] = pd.to_numeric(df[AMOUNT_COL], errors="coerce").fillna(0)

    df[PARTY_COL] = df.apply(
        lambda row: get_display_party(row[NAME_COL], row[PARTY_COL]),
        axis=1
    )

    return df


def filter_data(df, filter_type, categories):
    if filter_type == "total":
        return df.copy()

    return df[df[MAJOR_COL].isin(categories)].copy()

# ============================================================
# DATA PREPARATION
# ============================================================

def prepare_top_10(df):
    data = (
        df.groupby([NAME_COL, PARTY_COL])[AMOUNT_COL]
        .sum()
        .reset_index()
        .sort_values(AMOUNT_COL, ascending=False)
        .head(TOP_N)
    )

    data["DisplayName"] = data[NAME_COL].apply(clean_name)
    data["Color"] = data[PARTY_COL].apply(get_party_color)

    return data


def prepare_high_level_category_data(df):
    data = df.copy()

    data[HIGH_LEVEL_COL] = (
        data[HIGH_LEVEL_COL]
        .fillna("Uncategorised")
        .astype(str)
        .str.strip()
    )

    data.loc[data[HIGH_LEVEL_COL] == "", HIGH_LEVEL_COL] = "Uncategorised"

    return (
        data.groupby(HIGH_LEVEL_COL)[AMOUNT_COL]
        .sum()
        .reset_index()
        .sort_values(AMOUNT_COL, ascending=False)
        .head(TOP_N)
    )


def prepare_party_data(df):
    data = df.copy()

    data[PARTY_COL] = (
        data[PARTY_COL]
        .fillna("Uncategorised")
        .apply(clean_party_name)
    )

    chart_data = (
        data.groupby(PARTY_COL)[AMOUNT_COL]
        .sum()
        .reset_index()
        .sort_values(AMOUNT_COL, ascending=False)
    )

    chart_data["Color"] = chart_data[PARTY_COL].apply(get_party_color)

    return chart_data


def prepare_state_data(df):
    data = df.copy()

    data[STATE_COL] = (
        data[STATE_COL]
        .fillna("Uncategorised")
        .astype(str)
        .str.strip()
    )

    data.loc[data[STATE_COL] == "", STATE_COL] = "Uncategorised"

    return (
        data.groupby(STATE_COL)[AMOUNT_COL]
        .sum()
        .reset_index()
        .sort_values(AMOUNT_COL, ascending=False)
    )


def prepare_biggest_increase(current_df, previous_df):
    comparison = current_df.merge(
        previous_df,
        on=[NAME_COL, PARTY_COL],
        how="left",
        suffixes=("_Current", "_Previous")
    )

    comparison["Amount_Previous"] = comparison["Amount_Previous"].fillna(0)
    comparison["Increase"] = comparison["Amount_Current"] - comparison["Amount_Previous"]

    data = (
        comparison[comparison["Increase"] > 0]
        .sort_values("Increase", ascending=False)
        .head(TOP_N)
        .copy()
    )

    data["DisplayName"] = data[NAME_COL].apply(clean_name)
    data["Color"] = data[PARTY_COL].apply(get_party_color)

    return data

# ============================================================
# EXPORT HELPERS
# ============================================================

def export_top_data(data, output_path):
    # Person-level supporting data uses the official full name, but exposes
    # only the fields useful to readers. DisplayName and Color remain
    # internal chart-rendering fields.
    export_df = data[
        [NAME_COL, PARTY_COL, AMOUNT_COL]
    ].copy()

    export_df = export_df.rename(columns={
        NAME_COL: "Name",
    })

    export_df.to_csv(output_path, index=False)
    mirror_file_to_website(output_path)
    print(f"Saved data: {output_path.name}")


def export_increase_data(data, output_path):
    export_df = data[
        ["DisplayName", NAME_COL, PARTY_COL,
         "Amount_Previous", "Amount_Current", "Increase"]
    ].copy()

    export_df.to_csv(output_path, index=False)
    mirror_file_to_website(output_path)
    print(f"Saved data: {output_path.name}")

# ============================================================
# CHART HELPERS
# ============================================================

def add_party_legend(ax, parties):
    ax.legend(
        handles=party_legend_handles(parties),
        title="Party",
        loc="lower right",
        fontsize=10,
        title_fontsize=11
    )


# ============================================================
# CHART CREATION
# ============================================================

def create_top_chart(data, title, xlabel, output_path):
    fig, ax = plt.subplots(figsize=(16, 9))

    bars = ax.barh(
        data["DisplayName"],
        data[AMOUNT_COL],
        color=data["Color"]
    )

    ax.invert_yaxis()
    ax.set_title(title, fontsize=26, pad=25)

    style_currency_axis(ax, xlabel)
    add_value_labels(ax, bars, data[AMOUNT_COL])
    add_party_legend(ax, data[PARTY_COL])

    add_ipea_footer(fig, ax, source_text=IPEA_SOURCE_TEXT)
    apply_chart_layout(fig)

    plt.savefig(output_path, dpi=150, bbox_inches="tight")

    svg_path = output_path.with_suffix(".svg")
    plt.savefig(svg_path, format="svg", bbox_inches="tight")
    mirror_file_to_website(svg_path)

    plt.close()

    print(f"Saved chart: {output_path.name}")
    print(f"Saved chart: {svg_path.name}")


def create_high_level_category_chart(data, title, output_path):
    chart_data = data.sort_values(AMOUNT_COL, ascending=True)

    fig, ax = plt.subplots(figsize=(16, 9))

    bars = ax.barh(
        chart_data[HIGH_LEVEL_COL],
        chart_data[AMOUNT_COL],
        color=DEFAULT_BAR_COLOR
    )

    ax.set_title(title, fontsize=26, pad=25)

    style_currency_axis(ax, "Reported Spending (AUD)")
    add_value_labels(ax, bars, chart_data[AMOUNT_COL])

    add_ipea_footer(fig, ax, source_text=IPEA_SOURCE_TEXT)
    apply_chart_layout(fig, left=0.18)

    plt.savefig(output_path, dpi=150, bbox_inches="tight")

    svg_path = output_path.with_suffix(".svg")
    plt.savefig(svg_path, format="svg", bbox_inches="tight")
    mirror_file_to_website(svg_path)

    plt.close()

    print(f"Saved chart: {output_path.name}")
    print(f"Saved chart: {svg_path.name}")


def create_party_chart(data, title, output_path):
    chart_data = data.sort_values(AMOUNT_COL, ascending=True)

    fig, ax = plt.subplots(figsize=(16, 9))

    bars = ax.barh(
        chart_data[PARTY_COL],
        chart_data[AMOUNT_COL],
        color=chart_data["Color"]
    )

    ax.set_title(title, fontsize=26, pad=25)

    style_currency_axis(ax, "Reported Spending (AUD)")
    add_value_labels(ax, bars, chart_data[AMOUNT_COL])
    add_party_legend(ax, chart_data[PARTY_COL])

    add_ipea_footer(fig, ax, source_text=IPEA_SOURCE_TEXT)
    apply_chart_layout(fig, left=0.18)

    plt.savefig(output_path, dpi=150, bbox_inches="tight")

    svg_path = output_path.with_suffix(".svg")
    plt.savefig(svg_path, format="svg", bbox_inches="tight")
    mirror_file_to_website(svg_path)

    plt.close()

    print(f"Saved chart: {output_path.name}")
    print(f"Saved chart: {svg_path.name}")


def create_state_chart(data, title, output_path):
    chart_data = data.sort_values(AMOUNT_COL, ascending=True)

    fig, ax = plt.subplots(figsize=(16, 9))

    bars = ax.barh(
        chart_data[STATE_COL],
        chart_data[AMOUNT_COL],
        color=DEFAULT_BAR_COLOR
    )

    ax.set_title(title, fontsize=26, pad=25)

    style_currency_axis(ax, "Reported Spending (AUD)")
    add_value_labels(ax, bars, chart_data[AMOUNT_COL])

    add_ipea_footer(fig, ax, source_text=IPEA_SOURCE_TEXT)
    apply_chart_layout(fig, left=0.12)

    plt.savefig(output_path, dpi=150, bbox_inches="tight")

    svg_path = output_path.with_suffix(".svg")
    plt.savefig(svg_path, format="svg", bbox_inches="tight")
    mirror_file_to_website(svg_path)

    plt.close()

    print(f"Saved chart: {output_path.name}")
    print(f"Saved chart: {svg_path.name}")


def create_increase_chart(data, title, xlabel, output_path):
    fig, ax = plt.subplots(figsize=(16, 9))

    bars = ax.barh(
        data["DisplayName"],
        data["Increase"],
        color=data["Color"]
    )

    ax.invert_yaxis()
    ax.set_title(title, fontsize=26, pad=25)

    style_currency_axis(ax, xlabel)
    add_value_labels(ax, bars, data["Increase"])
    add_party_legend(ax, data[PARTY_COL])

    add_ipea_footer(fig, ax, source_text=IPEA_SOURCE_TEXT)
    apply_chart_layout(fig)

    plt.savefig(output_path, dpi=150, bbox_inches="tight")

    svg_path = output_path.with_suffix(".svg")
    plt.savefig(svg_path, format="svg", bbox_inches="tight")
    mirror_file_to_website(svg_path)

    plt.close()

    print(f"Saved chart: {output_path.name}")
    print(f"Saved chart: {svg_path.name}")

# ============================================================
# MAIN SCRIPT
# ============================================================

def discover_quarterly_csvs():
    """Return available IPEA quarterly extracts in chronological order."""
    return sorted(
        IPEA_DATA_DIR.glob("*_dataextract.csv"),
        key=lambda file: quarter_sort_key(file.stem),
    )


def generate_quarter(csv_path):
    """Generate all standard IPEA charts/data for one quarterly extract."""

    target_path = csv_path

    if not target_path.exists():
        raise FileNotFoundError(f"Could not find {target_path}")

    target_base = target_path.stem
    target_period = quarter_label(target_base)

    quarter_output_dir = IPEA_OUTPUT_DIR / target_base
    quarter_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating charts for: {target_base}")
    print(f"Output folder: {quarter_output_dir}")

    current_raw_df = load_data(target_path)

    # -----------------------------
    # 01–03 OVERVIEW CHARTS
    # -----------------------------

    high_level_data = prepare_high_level_category_data(current_raw_df)

    high_level_data.to_csv(
        quarter_output_dir / "01_spending_by_high_level_category_data.csv",
        index=False
    )
    mirror_file_to_website(quarter_output_dir / "01_spending_by_high_level_category_data.csv")
    print("Saved data: 01_spending_by_high_level_category_data.csv")

    create_high_level_category_chart(
        data=high_level_data,
        title=f"Reported Spending by High-Level Category\n{target_period}",
        output_path=quarter_output_dir / "01_spending_by_high_level_category.png"
    )

    party_data = prepare_party_data(current_raw_df)

    party_data.to_csv(
        quarter_output_dir / "02_spending_by_party_data.csv",
        index=False
    )
    mirror_file_to_website(quarter_output_dir / "02_spending_by_party_data.csv")
    print("Saved data: 02_spending_by_party_data.csv")

    create_party_chart(
        data=party_data,
        title=f"Reported Spending by Party\n{target_period}",
        output_path=quarter_output_dir / "02_spending_by_party.png"
    )

    state_data = prepare_state_data(current_raw_df)

    state_data.to_csv(
        quarter_output_dir / "03_spending_by_state_data.csv",
        index=False
    )
    mirror_file_to_website(quarter_output_dir / "03_spending_by_state_data.csv")
    print("Saved data: 03_spending_by_state_data.csv")

    create_state_chart(
        data=state_data,
        title=f"Reported Spending by State or Territory\n{target_period}",
        output_path=quarter_output_dir / "03_spending_by_state.png"
    )

    # -----------------------------
    # 04–13 TOP SPENDING CHARTS
    # -----------------------------

    for number, title_name, filter_type, categories in TOP_CHARTS:
        filtered_df = filter_data(current_raw_df, filter_type, categories)
        top_data = prepare_top_10(filtered_df)

        chart_title = f"{title_name}\n{target_period}"
        slug = title_name.lower().replace(" ", "_").replace("&", "and")

        chart_output = quarter_output_dir / f"{number}_{slug}.png"
        data_output = quarter_output_dir / f"{number}_{slug}_data.csv"

        export_top_data(top_data, data_output)

        create_top_chart(
            data=top_data,
            title=chart_title,
            xlabel=f"{title_name.replace('Top ', 'Total ')} (AUD)",
            output_path=chart_output
        )

    print(f"Finished generating standard charts for {target_base}.")


available_csvs = discover_quarterly_csvs()

if not available_csvs:
    raise FileNotFoundError(
        f"No quarterly IPEA CSV files found in {IPEA_DATA_DIR}"
    )

if TARGET_CSV is None:
    csvs_to_generate = available_csvs
else:
    target_path = IPEA_DATA_DIR / TARGET_CSV
    if target_path not in available_csvs:
        raise FileNotFoundError(
            f"Could not find {target_path}. "
            f"Available files: {[path.name for path in available_csvs]}"
        )
    csvs_to_generate = [target_path]

print(f"\nQuarterly IPEA files to generate: {len(csvs_to_generate)}")

for csv_path in csvs_to_generate:
    print("\n" + "=" * 72)
    generate_quarter(csv_path)

print("\nFinished generating IPEA quarterly charts for all selected files.")

