from pathlib import Path
import re
import textwrap

import pandas as pd
import matplotlib.ticker as ticker
from matplotlib.patches import Patch
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "output"
BRANDING_DIR = PROJECT_DIR / "branding"

IPEA_DATA_DIR = DATA_DIR / "ipea"
IPEA_OUTPUT_DIR = OUTPUT_DIR / "ipea"

AUSTENDER_DATA_DIR = DATA_DIR / "austender"
AUSTENDER_OUTPUT_DIR = OUTPUT_DIR / "austender"

IPEA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
AUSTENDER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# GENERAL SETTINGS
# ============================================================

TOP_N = 10

PROJECT_NAME = "Australian Public Expense Tracker"
X_HANDLE = "@auspublicexp"
LOGO_FILE = BRANDING_DIR / "APETLogo400x400.png"

PROJECT_BLUE = "#1f77b4"
DEFAULT_COLOR = "#777777"
DEFAULT_BAR_COLOR = PROJECT_BLUE
DEFENCE_COLOR = "#4f81bd"
NON_DEFENCE_COLOR = "#888888"
CONSULTANCY_COLOR = "#6aa84f"

# ============================================================
# PARTY COLOURS
# ============================================================

PARTY_COLORS = {
    "Australian Labor Party (ALP)": "#b94a48",
    "Liberal Party of Australia": "#4f81bd",
    "National Party of Australia": "#6aa84f",
    "Australian Greens": "#4f8f4f",
    "One Nation Australia": "#e69138",
    "Independent": "#888888",
    "Uncategorised": "#777777",
}

# ============================================================
# KNOWN PARTY OVERRIDES
# ============================================================

KNOWN_PARTY_OVERRIDES = {
    "Pauline Hanson": "One Nation Australia",
}

# ============================================================
# CLEANING HELPERS
# ============================================================

def clean_name(name):
    name = str(name).strip()

    prefixes = [
        "Senator the Hon ",
        "Senator ",
        "The Hon Dr ",
        "The Hon ",
        "Hon ",
        "Dr ",
        "Mr ",
        "Mrs ",
        "Ms ",
        "Miss ",
    ]

    for prefix in prefixes:
        if name.startswith(prefix):
            name = name.replace(prefix, "", 1)

    suffixes = [
        " MP",
        " MLA",
        " MLC",
        " AC",
        " AO",
        " AM",
        " OAM",
        " KC",
        " QC",
        " SC",
        " OM",
    ]

    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]

    return name.title()


def clean_party_name(party):
    party = str(party).strip()

    if party == "" or party.lower() in ["nan", "none", "unknown"]:
        return "Uncategorised"

    party_map = {
        "Australian Labor Party": "Australian Labor Party (ALP)",
        "Australian Labor Party (ALP)": "Australian Labor Party (ALP)",
        "AUSTRALIAN LABOR PARTY": "Australian Labor Party (ALP)",
        "ALP": "Australian Labor Party (ALP)",

        "Liberal Party of Australia": "Liberal Party of Australia",
        "LIBERAL PARTY OF AUSTRALIA": "Liberal Party of Australia",
        "Liberal Party": "Liberal Party of Australia",
        "LIBERAL PARTY": "Liberal Party of Australia",

        "National Party of Australia": "National Party of Australia",
        "NATIONAL PARTY OF AUSTRALIA": "National Party of Australia",
        "National Party": "National Party of Australia",
        "NATIONAL PARTY": "National Party of Australia",

        "Australian Greens": "Australian Greens",
        "AUSTRALIAN GREENS": "Australian Greens",
        "Greens": "Australian Greens",
        "GREENS": "Australian Greens",

        "Pauline Hanson's One Nation": "One Nation Australia",
        "PAULINE HANSON'S ONE NATION": "One Nation Australia",
        "One Nation": "One Nation Australia",
        "ONE NATION": "One Nation Australia",

        "Independent": "Independent",
        "INDEPENDENT": "Independent",
    }

    return party_map.get(party, party)


def get_display_party(name, party):
    clean_person_name = clean_name(name)

    if clean_person_name in KNOWN_PARTY_OVERRIDES:
        return KNOWN_PARTY_OVERRIDES[clean_person_name]

    return clean_party_name(party)


def get_party_color(party):
    clean_party = clean_party_name(party)
    return PARTY_COLORS.get(clean_party, DEFAULT_COLOR)

# ============================================================
# AUSTENDER HELPERS
# ============================================================

def is_defence_agency(agency_name):
    agency_name = str(agency_name).lower()
    return "defence" in agency_name


def split_defence_data(df, agency_col):
    defence_df = df[df[agency_col].apply(is_defence_agency)].copy()
    non_defence_df = df[~df[agency_col].apply(is_defence_agency)].copy()

    return defence_df, non_defence_df



# ============================================================
# SUPPLIER NAME OVERRIDES
# ============================================================

SUPPLIER_OVERRIDES = {
    "DELL AUSTRALIA PTY LIMITED": "DELL AUSTRALIA PTY LTD",
}


# ============================================================
# SUPPLIER NAME CLEANING
# ============================================================

def clean_supplier_name(name):

    if pd.isna(name):
        return name

    name = str(name).upper().strip()

    replacements = {
        " LIMITED": " LTD",
        " PROPRIETARY": " PTY",
        " PTY.": " PTY",
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    name = SUPPLIER_OVERRIDES.get(name, name)

    name = " ".join(name.split())

    return name

# ============================================================
# QUARTER HELPERS
# ============================================================

def quarter_sort_key(filename):
    match = re.match(r"(\d{4})q0?(\d)", filename.lower())

    if not match:
        return (9999, 9)

    return (int(match.group(1)), int(match.group(2)))


def quarter_label(base_name):
    """
    Convert IPEA calendar quarter filenames into
    Australian financial year quarter labels.

    Example:
    2025q01 -> FY2024–25 Q3 — Jan–Mar 2025
    """

    match = re.match(r"(\d{4})q0?(\d)", base_name.lower())

    if not match:
        return base_name

    year = int(match.group(1))
    quarter = int(match.group(2))

    month_labels = {
        1: "Jan–Mar",
        2: "Apr–Jun",
        3: "Jul–Sep",
        4: "Oct–Dec",
    }

    financial_mapping = {
        1: (year - 1, year, 3),
        2: (year - 1, year, 4),
        3: (year, year + 1, 1),
        4: (year, year + 1, 2),
    }

    fy_start, fy_end, fy_quarter = financial_mapping[quarter]

    fy_label = f"FY{fy_start}–{str(fy_end)[-2:]} Q{fy_quarter}"

    return f"{fy_label} — {month_labels[quarter]} {year}"

# ============================================================
# FORMATTERS
# ============================================================

def compact_currency_formatter(x, pos):
    if x >= 1_000_000_000:
        return f"${x / 1_000_000_000:.1f}B"

    if x >= 1_000_000:
        return f"${x / 1_000_000:.0f}M"

    if x >= 1_000:
        return f"${x / 1_000:.0f}K"

    return f"${x:,.0f}"


def currency_formatter():
    return ticker.FuncFormatter(compact_currency_formatter)


def add_value_labels(ax, bars, values):
    max_value = max(values) if len(values) > 0 else 0

    if max_value == 0:
        return

    for bar in bars:
        width = bar.get_width()

        ax.text(
            width + max_value * 0.006,
            bar.get_y() + bar.get_height() / 2,
            f"${width:,.0f}",
            va="center",
            ha="left",
            fontsize=11,
            color="#222222",
            fontweight="bold",
        )

    ax.set_xlim(0, max_value * 1.16)

# ============================================================
# CHART STYLE HELPERS
# ============================================================

def style_currency_axis(ax, xlabel="Reported Value (AUD)"):
    ax.set_xlabel(xlabel, fontsize=16)
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(currency_formatter())

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.grid(axis="x", linestyle="--", alpha=0.25)


def apply_chart_layout(fig, left=0.18):
    fig.subplots_adjust(
        left=left,
        right=0.96,
        top=0.86,
        bottom=0.20,
    )

# ============================================================
# FOOTER / BRANDING
# ============================================================

def add_brand_logo(fig, left=0.02, bottom=0.005, size=0.115):
    """Add the APET logo at the bottom-left of a chart figure."""
    if LOGO_FILE.exists():
        logo = mpimg.imread(LOGO_FILE)
        logo_ax = fig.add_axes([left, bottom, size, size])
        logo_ax.imshow(logo)
        logo_ax.axis("off")
    else:
        print(f"Warning: logo file not found: {LOGO_FILE}")


def add_standard_footer(
    fig,
    ax,
    source_text,
    project_name=PROJECT_NAME,
    x_handle=X_HANDLE,
):
    """Add standard APET branding to the bottom of a chart."""
    add_brand_logo(fig)

    footer_text = f"Source: {source_text}  |  {project_name}  |  {x_handle}"

    fig.text(
        0.17,
        0.03,
        footer_text,
        ha="left",
        va="center",
        fontsize=11,
        color="#555555",
    )

# ============================================================
# LEGEND HELPERS
# ============================================================

def party_legend_handles(parties):
    used_parties = sorted(set(clean_party_name(party) for party in parties))

    return [
        Patch(
            facecolor=get_party_color(party),
            label=party,
        )
        for party in used_parties
    ]


def wrap_label(value, width=34, max_lines=2):
    value = str(value).strip()

    if value == "" or value.lower() in ["nan", "none"]:
        value = "Uncategorised"

    wrapped_lines = textwrap.wrap(value, width=width)

    if len(wrapped_lines) <= max_lines:
        return "\n".join(wrapped_lines)

    kept_lines = wrapped_lines[:max_lines]
    kept_lines[-1] = kept_lines[-1].rstrip(".") + "..."

    return "\n".join(kept_lines)


def save_chart_data(data, output_path):
    data.to_csv(output_path, index=False)
    print(f"Saved data: {output_path.name}")


def create_horizontal_bar_chart(
    data,
    label_col,
    value_col,
    title,
    output_path,
    source_text,
    xlabel="Reported Value (AUD)",
    left=0.32,
    label_width=34,
    label_lines=2,
    bar_color=DEFAULT_BAR_COLOR,
):
    chart_data = data.sort_values(value_col, ascending=True).copy()

    chart_data["ChartLabel"] = chart_data[label_col].apply(
        lambda value: wrap_label(value, width=label_width, max_lines=label_lines)
    )

    # Dynamic height:
    # works better for charts with only 2–5 bars,
    # while still allowing taller charts for top 10 lists.
    row_count = len(chart_data)
    fig_height = max(4.8, min(10, row_count * 0.85 + 2.5))

    fig_width = 14 if row_count <= 3 else 16

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    bars = ax.barh(
        chart_data["ChartLabel"],
        chart_data[value_col],
        color=bar_color,
        height=0.62,
    )

    ax.set_title(title, fontsize=26, pad=22)

    style_currency_axis(ax, xlabel=xlabel)

    # Reduce vertical empty space, especially for small datasets
    ax.margins(y=0.12)

    add_value_labels(ax, bars, chart_data[value_col])
    add_standard_footer(fig, ax, source_text=source_text)

    # Slightly smaller default left margin than before
    apply_chart_layout(fig, left=left)

    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Saved chart: {output_path.name}")

# ============================================================
# SAVE X POST
# ============================================================

def save_x_post(output_path, text):
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(text)

    print(f"Saved X post: {output_path.name}")

