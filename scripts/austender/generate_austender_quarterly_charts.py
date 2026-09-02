from pathlib import Path
import os
import sys
import shutil

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["svg.fonttype"] = "none"
import matplotlib.ticker as ticker

PROJECT_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_DIR / "scripts"

sys.path.append(str(SCRIPTS_DIR))

import chart_helpers as chart_helpers_module
from chart_helpers import *

# ============================================================
# SETTINGS
# ============================================================

TARGET_FY_QUARTER = None  # None = generate all available quarters; set a value to test one quarter

MASTER_FILE = (
    PROJECT_DIR
    / "output"
    / "austender"
    / "austender_master.csv"
)

AUSTENDER_SOURCE_TEXT = (
    "AusTender contract notice export via tenders.gov.au"
)

# ============================================================
# WEBSITE OUTPUT + CLICKABLE FOOTER
# ============================================================

AUSTENDER_WEBSITE_CHART_DIR_VALUE = os.environ.get(
    "APET_AUSTENDER_WEBSITE_CHART_DIR"
)
AUSTENDER_WEBSITE_CHART_DIR = (
    Path(AUSTENDER_WEBSITE_CHART_DIR_VALUE).expanduser()
    if AUSTENDER_WEBSITE_CHART_DIR_VALUE
    else None
)


def mirror_file_to_website(source_path):
    """Copy an SVG/CSV into the matching website quarter folder."""
    if AUSTENDER_WEBSITE_CHART_DIR is None:
        return

    quarter_name = source_path.parent.name
    website_quarter_dir = AUSTENDER_WEBSITE_CHART_DIR / quarter_name
    website_quarter_dir.mkdir(parents=True, exist_ok=True)

    destination = website_quarter_dir / source_path.name
    shutil.copy2(source_path, destination)
    print(f"Copied website asset: {destination}")


def add_austender_footer(fig, ax, source_text=None):
    """Render one footer line with clickable visible text in SVG output."""
    chart_helpers_module.add_brand_logo(fig)

    segments = [
        ("Source: AusTender contract notice export via ", None, "#555555"),
        ("tenders.gov.au", "https://www.tenders.gov.au/", "#0d6efd"),
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


chart_helpers_module.add_standard_footer = add_austender_footer


# ============================================================
# COLUMN NAMES
# ============================================================

AGENCY_COL = "Agency"
CN_ID_COL = "CN ID"
PARENT_CN_ID_COL = "Parent CN ID"
PUBLISH_DATE_COL = "Publish Date"
AMENDMENT_PUBLISH_DATE_COL = "Amendment Publish Date"
START_DATE_COL = "Start Date"
END_DATE_COL = "End Date"
VALUE_COL = "Value"
DESCRIPTION_COL = "Description"
CATEGORY_COL = "Category"
METHOD_COL = "Procurement Method"
CONSULTANCY_COL = "Consultancy"
SUPPLIER_COL = "Supplier Name"
SUPPLIER_CLEAN_COL = "Supplier Clean"
SUPPLIER_COUNTRY_COL = "Supplier Country"
FY_QUARTER_COL = "FY Quarter"

# ============================================================
# OUTPUT FOLDER
# ============================================================

# Set inside generate_quarter(). Chart wrapper functions use this variable.
export_output_dir = None

# ============================================================
# GENERAL HELPERS
# ============================================================

def clean_text(value):
    if pd.isna(value):
        return "Uncategorised"

    value = str(value).strip()

    if value == "":
        return "Uncategorised"

    return value


def clean_austender_data(df):
    data = df.copy()

    required_cols = [
        AGENCY_COL,
        CN_ID_COL,
        PARENT_CN_ID_COL,
        VALUE_COL,
        CATEGORY_COL,
        METHOD_COL,
        CONSULTANCY_COL,
        SUPPLIER_COL,
        SUPPLIER_COUNTRY_COL,
        DESCRIPTION_COL,
        PUBLISH_DATE_COL,
        FY_QUARTER_COL,
    ]

    missing_cols = [
        col
        for col in required_cols
        if col not in data.columns
    ]

    if missing_cols:
        raise ValueError(
            f"Missing expected columns: {missing_cols}"
        )

    # ---------------------------------
    # VALUE
    # ---------------------------------

    data[VALUE_COL] = pd.to_numeric(
        data[VALUE_COL],
        errors="coerce",
    ).fillna(0)

    # ---------------------------------
    # TEXT
    # ---------------------------------

    text_cols = [
        AGENCY_COL,
        CATEGORY_COL,
        METHOD_COL,
        CONSULTANCY_COL,
        SUPPLIER_COL,
        SUPPLIER_COUNTRY_COL,
        DESCRIPTION_COL,
        FY_QUARTER_COL,
    ]

    for col in text_cols:
        data[col] = (
            data[col]
            .apply(clean_text)
        )

    data[SUPPLIER_COUNTRY_COL] = (
        data[SUPPLIER_COUNTRY_COL]
        .str.upper()
    )

    data[CONSULTANCY_COL] = (
        data[CONSULTANCY_COL]
        .str.title()
    )

    # ---------------------------------
    # DATES
    # ---------------------------------

    data[PUBLISH_DATE_COL] = pd.to_datetime(
        data[PUBLISH_DATE_COL],
        errors="coerce",
    )

    if AMENDMENT_PUBLISH_DATE_COL in data.columns:
        data[AMENDMENT_PUBLISH_DATE_COL] = pd.to_datetime(
            data[AMENDMENT_PUBLISH_DATE_COL],
            errors="coerce",
        )

    if START_DATE_COL in data.columns:
        data[START_DATE_COL] = pd.to_datetime(
            data[START_DATE_COL],
            errors="coerce",
        )

    if END_DATE_COL in data.columns:
        data[END_DATE_COL] = pd.to_datetime(
            data[END_DATE_COL],
            errors="coerce",
        )

    return data


# ============================================================
# FINANCIAL QUARTER HELPERS
# ============================================================

def format_fy_quarter_label(fy_quarter):
    fy_text, quarter = fy_quarter.split("_")

    fy_display = fy_text.replace("-", "–")

    month_ranges = {
        "Q1": "July to September",
        "Q2": "October to December",
        "Q3": "January to March",
        "Q4": "April to June",
    }

    return (
        f"{fy_display} {quarter}\n"
        f"{month_ranges[quarter]}"
    )


def get_quarter_end_date(fy_quarter):
    """
    Return the end date for a financial quarter.

    Example:

    FY2025-26_Q4
        ->
    30 June 2026
    """

    fy_text, quarter = fy_quarter.split("_")

    start_year = int(
        fy_text[2:6]
    )

    end_year = start_year + 1

    quarter_end_dates = {
        "Q1": f"{start_year}-09-30",
        "Q2": f"{start_year}-12-31",
        "Q3": f"{end_year}-03-31",
        "Q4": f"{end_year}-06-30",
    }

    quarter_end = pd.Timestamp(
        quarter_end_dates[quarter]
    )

    # Include the entire final day
    return (
        quarter_end
        + pd.Timedelta(days=1)
        - pd.Timedelta(microseconds=1)
    )


# ============================================================
# AMENDMENT RESOLUTION
# ============================================================

def resolve_contract_versions_as_of(
    data,
    cutoff,
):
    """
    Resolve AusTender originals and amendments so that each
    underlying contract appears only once.

    The version retained is the latest version published on or
    before the supplied cutoff date.

    Example:

        CN123456       $10m
        CN123456-A1    $12m
        CN123456-A2    $15m

    If A2 existed by the quarter end:

        keep CN123456-A2 = $15m

    rather than adding:

        $10m + $12m + $15m
    """

    resolved = data.copy()

    if PARENT_CN_ID_COL not in resolved.columns:
        raise ValueError(
            f"Missing expected column: "
            f"{PARENT_CN_ID_COL}"
        )

    if AMENDMENT_PUBLISH_DATE_COL not in resolved.columns:
        raise ValueError(
            f"Missing expected column: "
            f"{AMENDMENT_PUBLISH_DATE_COL}"
        )

    # ---------------------------------
    # ROOT CONTRACT ID
    # ---------------------------------

    # Amendments point to their original contract using
    # Parent CN ID.
    #
    # An original contract uses its own CN ID.

    resolved["Root CN ID"] = (
        resolved[PARENT_CN_ID_COL]
        .where(
            resolved[PARENT_CN_ID_COL].notna(),
            resolved[CN_ID_COL],
        )
    )

    # ---------------------------------
    # VERSION / RECORD DATE
    # ---------------------------------

    # Original:
    #     Publish Date
    #
    # Amendment:
    #     Amendment Publish Date

    resolved["Record Date"] = (
        resolved[AMENDMENT_PUBLISH_DATE_COL]
        .where(
            resolved[
                AMENDMENT_PUBLISH_DATE_COL
            ].notna(),
            resolved[PUBLISH_DATE_COL],
        )
    )

    # ---------------------------------
    # HISTORICAL CUTOFF
    # ---------------------------------

    # Do not allow an amendment published after the quarter
    # to retrospectively change that quarter's chart.

    resolved = resolved[
        resolved["Record Date"] <= cutoff
    ].copy()

    # ---------------------------------
    # KEEP LATEST VERSION
    # ---------------------------------

    resolved = (
        resolved
        .sort_values(
            [
                "Root CN ID",
                "Record Date",
                CN_ID_COL,
            ],
            na_position="first",
        )
        .drop_duplicates(
            subset=["Root CN ID"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    return resolved


# ============================================================
# DATA PREPARATION
# ============================================================

def group_top_value(
    data,
    group_col,
    value_col=VALUE_COL,
    top_n=TOP_N,
):
    return (
        data
        .groupby(
            group_col,
            dropna=False,
        )[value_col]
        .sum()
        .reset_index()
        .sort_values(
            value_col,
            ascending=False,
        )
        .head(top_n)
    )


def group_top_count(
    data,
    group_col,
    count_col="Contract Count",
    top_n=TOP_N,
):
    return (
        data
        .groupby(
            group_col,
            dropna=False,
        )
        .size()
        .reset_index(
            name=count_col
        )
        .sort_values(
            count_col,
            ascending=False,
        )
        .head(top_n)
    )


def prepare_largest_contracts(data):
    columns = [
        CN_ID_COL,
        AGENCY_COL,
        SUPPLIER_CLEAN_COL,
        VALUE_COL,
        CATEGORY_COL,
        METHOD_COL,
        CONSULTANCY_COL,
        SUPPLIER_COUNTRY_COL,
        DESCRIPTION_COL,
    ]

    largest = (
        data[columns]
        .sort_values(
            VALUE_COL,
            ascending=False,
        )
        .drop_duplicates(
            subset=[
                SUPPLIER_CLEAN_COL,
                AGENCY_COL,
            ],
            keep="first",
        )
        .head(TOP_N)
        .reset_index(drop=True)
        .copy()
    )

    largest["Rank"] = (
        largest.index + 1
    )

    largest["ContractLabel"] = (
        largest["Rank"].astype(str)
        + ". "
        + largest[SUPPLIER_CLEAN_COL]
        + "\n"
        + largest[AGENCY_COL]
    )

    return largest


def prepare_overseas_supplier_spending(data):
    overseas_data = data[
        ~data[
            SUPPLIER_COUNTRY_COL
        ].isin(
            [
                "AUSTRALIA",
                "AU",
                "AUS",
            ]
        )
    ].copy()

    return group_top_value(
        overseas_data,
        SUPPLIER_COUNTRY_COL,
    )


# ============================================================
# COUNT CHART CREATION
# ============================================================

def create_horizontal_count_chart(
    data,
    label_col,
    count_col,
    title,
    output_path,
    source_text,
    xlabel="Number of Contracts",
    left=0.34,
    label_width=34,
    label_lines=2,
    bar_color=DEFAULT_BAR_COLOR,
):
    chart_data = (
        data
        .sort_values(
            count_col,
            ascending=True,
        )
        .copy()
    )

    chart_data["ChartLabel"] = (
        chart_data[label_col]
        .apply(
            lambda value: wrap_label(
                value,
                width=label_width,
                max_lines=label_lines,
            )
        )
    )

    fig, ax = plt.subplots(
        figsize=(16, 9)
    )

    bars = ax.barh(
        chart_data["ChartLabel"],
        chart_data[count_col],
        color=bar_color,
    )

    ax.set_title(
        title,
        fontsize=26,
        pad=25,
    )

    ax.set_xlabel(
        xlabel,
        fontsize=16,
    )

    ax.set_ylabel("")

    ax.xaxis.set_major_formatter(
        ticker.StrMethodFormatter(
            "{x:,.0f}"
        )
    )

    ax.spines[
        "top"
    ].set_visible(False)

    ax.spines[
        "right"
    ].set_visible(False)

    ax.grid(
        axis="x",
        linestyle="--",
        alpha=0.25,
    )

    max_value = (
        chart_data[count_col]
        .max()
    )

    for bar in bars:
        width = bar.get_width()

        if (
            max_value > 0
            and width > max_value * 0.35
        ):
            ax.text(
                width * 0.98,
                bar.get_y()
                + bar.get_height() / 2,
                f"{width:,.0f}",
                va="center",
                ha="right",
                fontsize=13,
                color="white",
                fontweight="bold",
            )

        else:
            ax.text(
                width
                + max_value * 0.01,
                bar.get_y()
                + bar.get_height() / 2,
                f"{width:,.0f}",
                va="center",
                ha="left",
                fontsize=13,
                color="#222222",
            )

    ax.set_xlim(
        0,
        max_value * 1.15,
    )

    add_austender_footer(
        fig,
        ax,
        source_text=source_text,
    )

    apply_chart_layout(
        fig,
        left=left,
    )

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    svg_path = output_path.with_suffix(".svg")
    plt.savefig(
        svg_path,
        format="svg",
        bbox_inches="tight",
    )
    mirror_file_to_website(svg_path)

    plt.close()

    print(f"Saved chart: {output_path.name}")
    print(f"Saved chart: {svg_path.name}")


# ============================================================
# CHART WRAPPERS
# ============================================================

def make_value_chart(
    number,
    data,
    label_col,
    title,
    filename_stub,
    title_prefix,
    left=0.34,
    label_width=34,
    label_lines=2,
    bar_color=DEFAULT_BAR_COLOR,
):
    if data.empty:
        print(
            f"Skipped empty chart: "
            f"{title}"
        )
        return

    data_output = (
        export_output_dir
        / f"{number}_{filename_stub}_data.csv"
    )

    chart_output = (
        export_output_dir
        / f"{number}_{filename_stub}.png"
    )


    save_chart_data(
        data,
        data_output,
    )
    mirror_file_to_website(data_output)


    create_horizontal_bar_chart(
        data=data,
        label_col=label_col,
        value_col=VALUE_COL,
        title=(
            f"{title}\n"
            f"Australian Government Procurement Data\n"
            f"{title_prefix}"
        ),
        output_path=chart_output,
        source_text=AUSTENDER_SOURCE_TEXT,
        xlabel="Reported Contract Value (AUD)",
        left=left,
        label_width=label_width,
        label_lines=label_lines,
        bar_color=bar_color,
    )

    svg_output = chart_output.with_suffix(".svg")
    create_horizontal_bar_chart(
        data=data,
        label_col=label_col,
        value_col=VALUE_COL,
        title=(
            f"{title}\n"
            f"Australian Government Procurement Data\n"
            f"{title_prefix}"
        ),
        output_path=svg_output,
        source_text=AUSTENDER_SOURCE_TEXT,
        xlabel="Reported Contract Value (AUD)",
        left=left,
        label_width=label_width,
        label_lines=label_lines,
        bar_color=bar_color,
    )
    mirror_file_to_website(svg_output)


def make_count_chart(
    number,
    data,
    label_col,
    title,
    filename_stub,
    title_prefix,
    left=0.34,
    label_width=34,
    label_lines=2,
    bar_color=DEFAULT_BAR_COLOR,
):
    if data.empty:
        print(
            f"Skipped empty chart: "
            f"{title}"
        )
        return

    count_col = "Contract Count"

    data_output = (
        export_output_dir
        / f"{number}_{filename_stub}_data.csv"
    )

    chart_output = (
        export_output_dir
        / f"{number}_{filename_stub}.png"
    )


    save_chart_data(
        data,
        data_output,
    )
    mirror_file_to_website(data_output)


    create_horizontal_count_chart(
        data=data,
        label_col=label_col,
        count_col=count_col,
        title=(
            f"{title}\n"
            f"Australian Government Procurement Data\n"
            f"{title_prefix}"
        ),
        output_path=chart_output,
        source_text=AUSTENDER_SOURCE_TEXT,
        xlabel="Number of Contracts",
        left=left,
        label_width=label_width,
        label_lines=label_lines,
        bar_color=bar_color,
    )


# ============================================================
# MAIN SCRIPT
# ============================================================

print(
    f"Loading master file:\n"
    f"{MASTER_FILE}"
)

master_df = pd.read_csv(
    MASTER_FILE,
    low_memory=False,
)

master_df = clean_austender_data(
    master_df
)


def generate_quarter(target_fy_quarter):
    """Generate the full AusTender chart/data set for one financial quarter."""
    global export_output_dir

    export_output_dir = (
        PROJECT_DIR
        / "output"
        / "austender"
        / target_fy_quarter
    )
    export_output_dir.mkdir(parents=True, exist_ok=True)


    # ---------------------------------
    # SELECT RAW QUARTER RECORDS
    # ---------------------------------

    quarter_raw_df = master_df[
        master_df[FY_QUARTER_COL]
        == target_fy_quarter
    ].copy()

    if quarter_raw_df.empty:
        available_quarters = sorted(
            master_df[
                FY_QUARTER_COL
            ]
            .dropna()
            .unique()
        )

        raise ValueError(
            f"No rows found for "
            f"{target_fy_quarter}.\n"
            f"Available quarters: "
            f"{available_quarters}"
        )

    # ---------------------------------
    # RESOLVE AMENDMENTS AS OF QUARTER END
    # ---------------------------------

    quarter_end = get_quarter_end_date(
        target_fy_quarter
    )

    df = resolve_contract_versions_as_of(
        quarter_raw_df,
        cutoff=quarter_end,
    )

    # ---------------------------------
    # CLEAN SUPPLIER NAMES
    # ---------------------------------

    df[SUPPLIER_CLEAN_COL] = (
        df[SUPPLIER_COL]
        .apply(clean_supplier_name)
    )

    # ---------------------------------
    # DEFENCE / NON-DEFENCE
    # ---------------------------------

    defence_df, non_defence_df = (
        split_defence_data(
            df,
            AGENCY_COL,
        )
    )

    title_prefix = format_fy_quarter_label(
        target_fy_quarter
    )

    # ============================================================
    # VALIDATION OUTPUT
    # ============================================================

    raw_total_value = (
        quarter_raw_df[
            VALUE_COL
        ].sum()
    )

    resolved_total_value = (
        df[
            VALUE_COL
        ].sum()
    )

    amendment_rows = (
        quarter_raw_df[
            PARENT_CN_ID_COL
        ]
        .notna()
        .sum()
    )

    print()
    print(
        f"Target quarter: "
        f"{target_fy_quarter}"
    )

    print(
        f"Chart title period: "
        f"{title_prefix}"
    )

    print(
        f"Quarter-end cutoff: "
        f"{quarter_end.date()}"
    )

    print()
    print(
        f"Raw rows for quarter: "
        f"{len(quarter_raw_df):,}"
    )

    print(
        f"Amendment rows in raw quarter: "
        f"{amendment_rows:,}"
    )

    print(
        f"Resolved underlying contracts "
        f"as of quarter end: "
        f"{len(df):,}"
    )

    print(
        f"Version rows removed from "
        f"aggregation: "
        f"{len(quarter_raw_df) - len(df):,}"
    )

    print()
    print(
        f"Raw summed value before "
        f"amendment resolution: "
        f"${raw_total_value:,.0f}"
    )

    print(
        f"Resolved reported contract "
        f"value: "
        f"${resolved_total_value:,.0f}"
    )

    print(
        f"Difference: "
        f"${raw_total_value - resolved_total_value:,.0f}"
    )

    print()
    print(
        f"Defence contract value: "
        f"${defence_df[VALUE_COL].sum():,.0f}"
    )

    print(
        f"Non-defence contract value: "
        f"${non_defence_df[VALUE_COL].sum():,.0f}"
    )

    print(
        f"Output folder:\n"
        f"{export_output_dir}"
    )

    # ============================================================
    # PUBLIC-FACING AUSTENDER CHARTS
    # ============================================================

    make_value_chart(
        "01",
        group_top_value(
            df,
            SUPPLIER_CLEAN_COL,
        ),
        SUPPLIER_CLEAN_COL,
        "Top Suppliers by Reported Contract Value",
        "top_suppliers_by_contract_value",
        title_prefix,
        left=0.34,
    )

    make_value_chart(
        "02",
        prepare_largest_contracts(df),
        "ContractLabel",
        "Largest Reported Contracts by Supplier and Agency",
        "largest_individual_contracts",
        title_prefix,
        left=0.46,
        label_width=38,
        label_lines=2,
    )

    make_value_chart(
        "03",
        group_top_value(
            defence_df,
            SUPPLIER_CLEAN_COL,
        ),
        SUPPLIER_CLEAN_COL,
        "Top Defence Suppliers by Reported Contract Value",
        "top_defence_suppliers_by_contract_value",
        title_prefix,
        left=0.34,
        bar_color=DEFENCE_COLOR,
    )

    make_value_chart(
        "04",
        group_top_value(
            df,
            METHOD_COL,
        ),
        METHOD_COL,
        "Reported Contract Value by Procurement Method",
        "spending_by_procurement_method",
        title_prefix,
        left=0.26,
    )

    make_value_chart(
        "05",
        prepare_overseas_supplier_spending(
            df
        ),
        SUPPLIER_COUNTRY_COL,
        "Reported Contract Value by Overseas Supplier Country",
        "overseas_supplier_spending_by_country",
        title_prefix,
        left=0.24,
    )

    make_value_chart(
        "06",
        group_top_value(
            non_defence_df,
            AGENCY_COL,
        ),
        AGENCY_COL,
        "Top Non-Defence Agencies by Reported Contract Value",
        "top_non_defence_agencies_by_contract_value",
        title_prefix,
        left=0.38,
        label_width=32,
        bar_color=NON_DEFENCE_COLOR,
    )

    make_count_chart(
        "07",
        group_top_count(
            df,
            SUPPLIER_CLEAN_COL,
        ),
        SUPPLIER_CLEAN_COL,
        "Top Suppliers by Number of Reported Contracts",
        "top_suppliers_by_contract_count",
        title_prefix,
        left=0.34,
    )

    print()
    print(
        "Finished generating public-facing "
        "AusTender quarterly charts."
    )


AUSTENDER_EXPORT_START_DATE = pd.Timestamp("2025-01-01")

available_quarters = sorted(
    str(value)
    for value in master_df[FY_QUARTER_COL].dropna().unique()
    if get_quarter_end_date(str(value)) >= AUSTENDER_EXPORT_START_DATE
)

if TARGET_FY_QUARTER is None:
    quarters_to_generate = available_quarters
else:
    if TARGET_FY_QUARTER not in available_quarters:
        raise ValueError(
            f"No rows found for {TARGET_FY_QUARTER}. "
            f"Available quarters: {available_quarters}"
        )
    quarters_to_generate = [TARGET_FY_QUARTER]

print(f"\nQuarters to generate: {len(quarters_to_generate)}")

for target_fy_quarter in quarters_to_generate:
    print("\n" + "=" * 72)
    generate_quarter(target_fy_quarter)

print("\nFinished generating AusTender charts for all selected quarters.")
