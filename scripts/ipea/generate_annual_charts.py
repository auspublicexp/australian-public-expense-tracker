from pathlib import Path
import sys
import shutil
import re
import os

# ============================================================
# ADD PROJECT SCRIPTS FOLDER TO PYTHON PATH
# ============================================================

PROJECT_DIR = Path(__file__).parents[2]
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
# SETTINGS
# ============================================================

# None = generate every complete Australian financial year available.
# To test one year only, set for example: TARGET_FINANCIAL_YEAR = "FY2024-25"
TARGET_FINANCIAL_YEAR = None

IPEA_SOURCE_TEXT = "IPEA parliamentary expenditure data via data.gov.au"

# ============================================================
# WEBSITE OUTPUT + CLICKABLE FOOTER
# ============================================================

_website_chart_dir = os.getenv("APET_IPEA_WEBSITE_CHART_DIR")
IPEA_WEBSITE_CHART_DIR = Path(_website_chart_dir) if _website_chart_dir else None


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


ANNUAL_OUTPUT_DIR = None  # Set inside generate_financial_year().

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
# ANNUAL CHART DEFINITIONS
# ============================================================

TOP_CHARTS = [
    ("04", "Top Annual Parliamentary Expense Totals", "total", None),
    ("05", "Top Annual Travel Spending", "major", [
        "Travel Allowance", "Family Travel", "Employee Travel", "International Travel",
        "Scheduled Commercial Transport", "Unscheduled Commercial Transport",
        "Other Car Costs", "Fares", "Parking", "Private-Plated Vehicle",
        "Private Vehicle Allowance", "Cancelled Transport",
        "Cabcharge / Other Car Costs", "COMCAR", "Domestic Travel",
        "Representing Australia", "Parliamentary Delegations",
        "Ministerial Visits", "Official Visits", "Representing a Minister",
    ]),
    ("06", "Top Annual Domestic Travel", "major", ["Domestic Travel"]),
    ("07", "Top Annual International Travel", "major", [
        "International Travel", "Representing Australia", "Parliamentary Delegations",
        "Ministerial Visits", "Official Visits", "Representing a Minister",
    ]),
    ("08", "Top Annual COMCAR Spending", "major", ["COMCAR"]),
    ("09", "Top Annual Travel Allowance", "major", ["Travel Allowance"]),
    ("10", "Top Annual Printing and Communications", "major", [
        "Printing and Communications", "Additional Printing and Communications", "Publications",
    ]),
    ("11", "Top Annual Publications", "major", ["Publications"]),
    ("12", "Top Annual Telecommunications", "major", [
        "Telephonic Services", "Telecommunications - Usage",
        "Telecommunications - Residential - Official",
    ]),
    ("13", "Top Annual Office Consumables and Services", "major", [
        "Office Consumables and Services"
    ]),
]

# ============================================================
# DATA LOADING
# ============================================================

def financial_year_components(financial_year):
    """
    Return the four calendar-quarter extracts that make up an Australian FY.

    Example:
      FY2024-25 = 2024 Q3 + 2024 Q4 + 2025 Q1 + 2025 Q2
    """
    match = re.fullmatch(r"FY(\d{4})-(\d{2})", financial_year)
    if not match:
        raise ValueError(f"Unexpected financial year label: {financial_year}")

    start_year = int(match.group(1))
    end_year = start_year + 1

    return [
        (start_year, 3),
        (start_year, 4),
        (end_year, 1),
        (end_year, 2),
    ]


def financial_year_period_text(financial_year):
    match = re.fullmatch(r"FY(\d{4})-(\d{2})", financial_year)
    if not match:
        raise ValueError(f"Unexpected financial year label: {financial_year}")

    start_year = int(match.group(1))
    return f"July {start_year} to June {start_year + 1}"


def load_annual_data(financial_year, annual_output_dir):
    component_quarters = financial_year_components(financial_year)
    files = []

    for year, quarter in component_quarters:
        expected = IPEA_DATA_DIR / f"{year}q{quarter:02d}_dataextract.csv"
        if not expected.exists():
            raise FileNotFoundError(
                f"Missing IPEA quarterly extract required for {financial_year}: "
                f"{expected.name}"
            )
        files.append(expected)

    print(f"\nGenerating annual charts for: {financial_year}")
    print(f"Period: {financial_year_period_text(financial_year)}")
    print(f"Output folder: {annual_output_dir}")
    print("Using four quarterly files:")

    for file in files:
        print(f" - {file.name}")

    df = pd.concat(
        [pd.read_csv(file, low_memory=False) for file in files],
        ignore_index=True
    )

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


def export_simple_data(data, output_path):
    export_df = data.drop(columns=["Color"], errors="ignore")
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

# ============================================================
# MAIN SCRIPT
# ============================================================

def discover_available_quarters():
    """Return available (calendar_year, quarter) pairs for IPEA extracts."""
    available = set()
    pattern = re.compile(r"^(\d{4})q0?([1-4])_dataextract\.csv$", re.IGNORECASE)

    for csv_path in IPEA_DATA_DIR.glob("*_dataextract.csv"):
        match = pattern.match(csv_path.name)
        if match:
            available.add((int(match.group(1)), int(match.group(2))))

    return available


def discover_complete_financial_years():
    """
    Discover Australian financial years with all four required extracts.

    FY2024-25 requires:
      2024 Q3, 2024 Q4, 2025 Q1, 2025 Q2
    """
    available = discover_available_quarters()

    if not available:
        return []

    candidate_start_years = sorted({year for year, _ in available})
    complete = []

    for start_year in candidate_start_years:
        financial_year = f"FY{start_year}-{str(start_year + 1)[-2:]}"
        required = set(financial_year_components(financial_year))

        if required.issubset(available):
            complete.append(financial_year)

    return complete


def generate_financial_year(financial_year):
    """Generate the full annual IPEA chart/data set for one complete FY."""
    global ANNUAL_OUTPUT_DIR

    annual_output_dir = IPEA_OUTPUT_DIR / f"{financial_year}_annual"
    annual_output_dir.mkdir(parents=True, exist_ok=True)
    ANNUAL_OUTPUT_DIR = annual_output_dir

    df = load_annual_data(financial_year, annual_output_dir)
    period_text = financial_year_period_text(financial_year)
    title_suffix = f"{financial_year}\n{period_text}"

    high_level_data = prepare_high_level_category_data(df)
    export_simple_data(
        high_level_data,
        annual_output_dir / "01_annual_spending_by_high_level_category_data.csv"
    )
    create_high_level_category_chart(
        data=high_level_data,
        title=f"Annual Reported Spending by High-Level Category\n{title_suffix}",
        output_path=annual_output_dir / "01_annual_spending_by_high_level_category.png"
    )

    party_data = prepare_party_data(df)
    export_simple_data(
        party_data,
        annual_output_dir / "02_annual_spending_by_party_data.csv"
    )
    create_party_chart(
        data=party_data,
        title=f"Annual Reported Spending by Party\n{title_suffix}",
        output_path=annual_output_dir / "02_annual_spending_by_party.png"
    )

    state_data = prepare_state_data(df)
    export_simple_data(
        state_data,
        annual_output_dir / "03_annual_spending_by_state_data.csv"
    )
    create_state_chart(
        data=state_data,
        title=f"Annual Reported Spending by State or Territory\n{title_suffix}",
        output_path=annual_output_dir / "03_annual_spending_by_state.png"
    )

    for number, title_name, filter_type, categories in TOP_CHARTS:
        filtered_df = filter_data(df, filter_type, categories)
        top_data = prepare_top_10(filtered_df)

        chart_title = f"{title_name}\n{title_suffix}"
        slug = title_name.lower().replace(" ", "_").replace("&", "and")

        chart_output = annual_output_dir / f"{number}_{slug}.png"
        data_output = annual_output_dir / f"{number}_{slug}_data.csv"

        export_top_data(top_data, data_output)

        create_top_chart(
            data=top_data,
            title=chart_title,
            xlabel=f"{title_name.replace('Top Annual ', 'Total Annual ')} (AUD)",
            output_path=chart_output
        )

    print(f"Finished generating annual charts for {financial_year}.")


complete_financial_years = discover_complete_financial_years()

if TARGET_FINANCIAL_YEAR is None:
    financial_years_to_generate = complete_financial_years
else:
    if TARGET_FINANCIAL_YEAR not in complete_financial_years:
        raise ValueError(
            f"{TARGET_FINANCIAL_YEAR} is not a complete IPEA financial year. "
            f"Complete financial years available: {complete_financial_years}"
        )
    financial_years_to_generate = [TARGET_FINANCIAL_YEAR]

if not financial_years_to_generate:
    raise FileNotFoundError(
        "No complete Australian financial years were found in the IPEA extracts."
    )

print(
    f"\nComplete IPEA financial years to generate: "
    f"{len(financial_years_to_generate)}"
)

for financial_year in financial_years_to_generate:
    print("\n" + "=" * 72)
    generate_financial_year(financial_year)

print(
    "\nFinished generating IPEA annual charts for all selected "
    "Australian financial years."
)

# Refresh the website's politician-name search after chart generation.
from build_ipea_search_index import main as build_ipea_search_index

build_ipea_search_index()
from pathlib import Path
import os
import sys
import shutil
import re

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
# SETTINGS
# ============================================================

# None = generate every complete Australian financial year available.
# To test one year only, set for example: TARGET_FINANCIAL_YEAR = "FY2024-25"
TARGET_FINANCIAL_YEAR = None

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


ANNUAL_OUTPUT_DIR = None  # Set inside generate_financial_year().

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
# ANNUAL CHART DEFINITIONS
# ============================================================

TOP_CHARTS = [
    ("04", "Top Annual Parliamentary Expense Totals", "total", None),
    ("05", "Top Annual Travel Spending", "major", [
        "Travel Allowance", "Family Travel", "Employee Travel", "International Travel",
        "Scheduled Commercial Transport", "Unscheduled Commercial Transport",
        "Other Car Costs", "Fares", "Parking", "Private-Plated Vehicle",
        "Private Vehicle Allowance", "Cancelled Transport",
        "Cabcharge / Other Car Costs", "COMCAR", "Domestic Travel",
        "Representing Australia", "Parliamentary Delegations",
        "Ministerial Visits", "Official Visits", "Representing a Minister",
    ]),
    ("06", "Top Annual Domestic Travel", "major", ["Domestic Travel"]),
    ("07", "Top Annual International Travel", "major", [
        "International Travel", "Representing Australia", "Parliamentary Delegations",
        "Ministerial Visits", "Official Visits", "Representing a Minister",
    ]),
    ("08", "Top Annual COMCAR Spending", "major", ["COMCAR"]),
    ("09", "Top Annual Travel Allowance", "major", ["Travel Allowance"]),
    ("10", "Top Annual Printing and Communications", "major", [
        "Printing and Communications", "Additional Printing and Communications", "Publications",
    ]),
    ("11", "Top Annual Publications", "major", ["Publications"]),
    ("12", "Top Annual Telecommunications", "major", [
        "Telephonic Services", "Telecommunications - Usage",
        "Telecommunications - Residential - Official",
    ]),
    ("13", "Top Annual Office Consumables and Services", "major", [
        "Office Consumables and Services"
    ]),
]

# ============================================================
# DATA LOADING
# ============================================================

def financial_year_components(financial_year):
    """
    Return the four calendar-quarter extracts that make up an Australian FY.

    Example:
      FY2024-25 = 2024 Q3 + 2024 Q4 + 2025 Q1 + 2025 Q2
    """
    match = re.fullmatch(r"FY(\d{4})-(\d{2})", financial_year)
    if not match:
        raise ValueError(f"Unexpected financial year label: {financial_year}")

    start_year = int(match.group(1))
    end_year = start_year + 1

    return [
        (start_year, 3),
        (start_year, 4),
        (end_year, 1),
        (end_year, 2),
    ]


def financial_year_period_text(financial_year):
    match = re.fullmatch(r"FY(\d{4})-(\d{2})", financial_year)
    if not match:
        raise ValueError(f"Unexpected financial year label: {financial_year}")

    start_year = int(match.group(1))
    return f"July {start_year} to June {start_year + 1}"


def load_annual_data(financial_year, annual_output_dir):
    component_quarters = financial_year_components(financial_year)
    files = []

    for year, quarter in component_quarters:
        expected = IPEA_DATA_DIR / f"{year}q{quarter:02d}_dataextract.csv"
        if not expected.exists():
            raise FileNotFoundError(
                f"Missing IPEA quarterly extract required for {financial_year}: "
                f"{expected.name}"
            )
        files.append(expected)

    print(f"\nGenerating annual charts for: {financial_year}")
    print(f"Period: {financial_year_period_text(financial_year)}")
    print(f"Output folder: {annual_output_dir}")
    print("Using four quarterly files:")

    for file in files:
        print(f" - {file.name}")

    df = pd.concat(
        [pd.read_csv(file, low_memory=False) for file in files],
        ignore_index=True
    )

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


def export_simple_data(data, output_path):
    export_df = data.drop(columns=["Color"], errors="ignore")
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

# ============================================================
# MAIN SCRIPT
# ============================================================

def discover_available_quarters():
    """Return available (calendar_year, quarter) pairs for IPEA extracts."""
    available = set()
    pattern = re.compile(r"^(\d{4})q0?([1-4])_dataextract\.csv$", re.IGNORECASE)

    for csv_path in IPEA_DATA_DIR.glob("*_dataextract.csv"):
        match = pattern.match(csv_path.name)
        if match:
            available.add((int(match.group(1)), int(match.group(2))))

    return available


def discover_complete_financial_years():
    """
    Discover Australian financial years with all four required extracts.

    FY2024-25 requires:
      2024 Q3, 2024 Q4, 2025 Q1, 2025 Q2
    """
    available = discover_available_quarters()

    if not available:
        return []

    candidate_start_years = sorted({year for year, _ in available})
    complete = []

    for start_year in candidate_start_years:
        financial_year = f"FY{start_year}-{str(start_year + 1)[-2:]}"
        required = set(financial_year_components(financial_year))

        if required.issubset(available):
            complete.append(financial_year)

    return complete


def generate_financial_year(financial_year):
    """Generate the full annual IPEA chart/data set for one complete FY."""
    global ANNUAL_OUTPUT_DIR

    annual_output_dir = IPEA_OUTPUT_DIR / f"{financial_year}_annual"
    annual_output_dir.mkdir(parents=True, exist_ok=True)
    ANNUAL_OUTPUT_DIR = annual_output_dir

    df = load_annual_data(financial_year, annual_output_dir)
    period_text = financial_year_period_text(financial_year)
    title_suffix = f"{financial_year}\n{period_text}"

    high_level_data = prepare_high_level_category_data(df)
    export_simple_data(
        high_level_data,
        annual_output_dir / "01_annual_spending_by_high_level_category_data.csv"
    )
    create_high_level_category_chart(
        data=high_level_data,
        title=f"Annual Reported Spending by High-Level Category\n{title_suffix}",
        output_path=annual_output_dir / "01_annual_spending_by_high_level_category.png"
    )

    party_data = prepare_party_data(df)
    export_simple_data(
        party_data,
        annual_output_dir / "02_annual_spending_by_party_data.csv"
    )
    create_party_chart(
        data=party_data,
        title=f"Annual Reported Spending by Party\n{title_suffix}",
        output_path=annual_output_dir / "02_annual_spending_by_party.png"
    )

    state_data = prepare_state_data(df)
    export_simple_data(
        state_data,
        annual_output_dir / "03_annual_spending_by_state_data.csv"
    )
    create_state_chart(
        data=state_data,
        title=f"Annual Reported Spending by State or Territory\n{title_suffix}",
        output_path=annual_output_dir / "03_annual_spending_by_state.png"
    )

    for number, title_name, filter_type, categories in TOP_CHARTS:
        filtered_df = filter_data(df, filter_type, categories)
        top_data = prepare_top_10(filtered_df)

        chart_title = f"{title_name}\n{title_suffix}"
        slug = title_name.lower().replace(" ", "_").replace("&", "and")

        chart_output = annual_output_dir / f"{number}_{slug}.png"
        data_output = annual_output_dir / f"{number}_{slug}_data.csv"

        export_top_data(top_data, data_output)

        create_top_chart(
            data=top_data,
            title=chart_title,
            xlabel=f"{title_name.replace('Top Annual ', 'Total Annual ')} (AUD)",
            output_path=chart_output
        )

    print(f"Finished generating annual charts for {financial_year}.")


complete_financial_years = discover_complete_financial_years()

if TARGET_FINANCIAL_YEAR is None:
    financial_years_to_generate = complete_financial_years
else:
    if TARGET_FINANCIAL_YEAR not in complete_financial_years:
        raise ValueError(
            f"{TARGET_FINANCIAL_YEAR} is not a complete IPEA financial year. "
            f"Complete financial years available: {complete_financial_years}"
        )
    financial_years_to_generate = [TARGET_FINANCIAL_YEAR]

if not financial_years_to_generate:
    raise FileNotFoundError(
        "No complete Australian financial years were found in the IPEA extracts."
    )

print(
    f"\nComplete IPEA financial years to generate: "
    f"{len(financial_years_to_generate)}"
)

for financial_year in financial_years_to_generate:
    print("\n" + "=" * 72)
    generate_financial_year(financial_year)

print(
    "\nFinished generating IPEA annual charts for all selected "
    "Australian financial years."
)

