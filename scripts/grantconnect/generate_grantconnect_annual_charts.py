from pathlib import Path
import os
import re
import shutil
import sys

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd

# Keep text as real text in SVG output instead of converting glyphs to paths.
plt.rcParams["svg.fonttype"] = "none"


# ============================================================
# IMPORT SHARED CHART HELPERS
# ============================================================

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(SCRIPTS_DIR))

import chart_helpers as chart_helpers_module  # noqa: E402

from chart_helpers import (  # noqa: E402
    DATA_DIR,
    OUTPUT_DIR,
    DEFAULT_BAR_COLOR,
    PROJECT_BLUE,
    add_standard_footer,
    apply_chart_layout,
    wrap_label,
    create_horizontal_bar_chart,
    save_chart_data,
)


# ============================================================
# SETTINGS
# ============================================================

GRANTCONNECT_DATA_DIR = DATA_DIR / "grantconnect"
GRANTCONNECT_OUTPUT_DIR = OUTPUT_DIR / "grantconnect"
GRANTCONNECT_WEBSITE_CHART_DIR_VALUE = os.environ.get(
    "APET_GRANTCONNECT_WEBSITE_CHART_DIR"
)
GRANTCONNECT_WEBSITE_CHART_DIR = (
    Path(GRANTCONNECT_WEBSITE_CHART_DIR_VALUE).expanduser()
    if GRANTCONNECT_WEBSITE_CHART_DIR_VALUE
    else None
)

# This matches monthly files and split-month files such as:
# grantconnect_FY2024-25_Q4_2025-05.xlsx
# grantconnect_FY2024-25_Q4_2025-04a.xlsx
# Files inside archive_incomplete are ignored because this glob is not recursive.
INPUT_FILE_PATTERN = "grantconnect_FY????-??_Q?_????-??*.xlsx"

# Use None to regenerate every complete financial year available in the
# monthly files. To generate one year only, use—for example—"FY2024-25".
TARGET_FINANCIAL_YEAR = None
COMPLETE_YEARS_ONLY = True

SOURCE_TEXT = (
    "GrantConnect grant award export via grants.gov.au"
    "  |  auspublicexp.org"
)
LOCAL_TOP_N = 10

VALUE_COL = "Value (AUD)"
DATE_COL = "Publish Date"
GA_ID_COL = "GA ID"

GRANTCONNECT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CLICKABLE FOOTER LINKS
# ============================================================

def add_standard_footer_with_links(fig, ax, source_text):
    """Render one footer line whose visible link text is clickable in SVG.

    The same labels remain visible in PNG output, but URL metadata is only
    actionable in vector formats such as SVG.
    """
    chart_helpers_module.add_brand_logo(fig)

    segments = [
        ("Source: GrantConnect grant award export via ", None, "#555555"),
        ("grants.gov.au", "https://grants.gov.au/", "#0d6efd"),
        ("  |  ", None, "#555555"),
        ("auspublicexp.org", "https://auspublicexp.org/", "#0d6efd"),
        ("  |  Australian Public Expense Tracker  |  ", None, "#555555"),
        ("@auspublicexp", "https://x.com/auspublicexp", "#0d6efd"),
    ]

    # Build the footer from left to right, measuring each segment so the
    # clickable text occupies exactly the same line rather than being repeated.
    x = 0.17
    y = 0.025
    renderer = fig.canvas.get_renderer()

    for label, url, color in segments:
        artist = fig.text(
            x,
            y,
            label,
            ha="left",
            va="bottom",
            fontsize=11,
            color=color,
            url=url,
        )
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bbox = artist.get_window_extent(renderer=renderer)
        x += bbox.width / fig.bbox.width


# The shared value-chart helper looks up add_standard_footer in its own module.
# Patch it so all GrantConnect charts use the same single-line linked footer.
chart_helpers_module.add_standard_footer = add_standard_footer_with_links


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(value):
    if pd.isna(value):
        return "Not specified"

    value = str(value).strip()

    if value == "" or value.lower() in {"nan", "none"}:
        return "Not specified"

    return " ".join(value.split())


def find_monthly_excel_files(folder):
    files = sorted(folder.glob(INPUT_FILE_PATTERN))

    if not files:
        raise FileNotFoundError(
            f"No monthly GrantConnect files matching "
            f"{INPUT_FILE_PATTERN!r} were found in:\n{folder}\n\n"
            "Expected names such as "
            "grantconnect_FY2024-25_Q3_2025-01.xlsx."
        )

    return files


def read_grantconnect_excel(file_path):
    """Find the GrantConnect table header and return its award rows."""
    preview = pd.read_excel(file_path, header=None, nrows=40)
    header_row = None

    for idx, row in preview.iterrows():
        values = [str(value).strip() for value in row.dropna().tolist()]

        if (
            GA_ID_COL in values
            and "Grant Activity" in values
            and DATE_COL in values
            and VALUE_COL in values
        ):
            header_row = idx
            break

    if header_row is None:
        raise ValueError(
            f"Could not find the GrantConnect header row in {file_path.name}."
        )

    return pd.read_excel(file_path, header=header_row)


def standardise_columns(df, file_name):
    df = df.dropna(how="all").copy()
    df.columns = [str(column).strip() for column in df.columns]

    required_cols = [
        GA_ID_COL,
        "Grant Activity",
        "Agency",
        "Category",
        "Recipient Name",
        "GO ID",
        DATE_COL,
        VALUE_COL,
    ]

    missing_cols = [column for column in required_cols if column not in df.columns]

    if missing_cols:
        missing_text = "\n".join(f"- {column}" for column in missing_cols)
        raise ValueError(
            f"{file_name} is missing expected GrantConnect columns:\n"
            f"{missing_text}"
        )

    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df[VALUE_COL] = pd.to_numeric(df[VALUE_COL], errors="coerce").fillna(0)

    text_cols = [
        GA_ID_COL,
        "Grant Activity",
        "Agency",
        "Category",
        "Recipient Name",
        "GO ID",
    ]

    for column in text_cols:
        df[column] = df[column].apply(clean_text)

    invalid_dates = df[DATE_COL].isna().sum()

    if invalid_dates:
        print(
            f"  WARNING: removing {invalid_dates:,} rows with an invalid "
            "Publish Date."
        )

    df = df.dropna(subset=[DATE_COL]).copy()
    return df


def load_and_validate_monthly_files():
    files = find_monthly_excel_files(GRANTCONNECT_DATA_DIR)
    frames = []

    print("Loading monthly GrantConnect files:")

    for file_path in files:
        file_df = read_grantconnect_excel(file_path)
        file_df = standardise_columns(file_df, file_path.name)

        row_count = len(file_df)
        exact_duplicates = int(file_df.duplicated().sum())
        unique_ga_ids = int(file_df[GA_ID_COL].nunique())
        date_min = file_df[DATE_COL].min().date()
        date_max = file_df[DATE_COL].max().date()

        print(
            f"- {file_path.name}: {row_count:,} rows; "
            f"{unique_ga_ids:,} unique GA IDs; "
            f"{exact_duplicates:,} exact duplicates; "
            f"{date_min} to {date_max}"
        )

        # The previous faulty quarterly export contained exactly 10,000
        # unique awards. Stop rather than silently publish incomplete charts.
        if unique_ga_ids >= 10000:
            raise ValueError(
                f"\n{file_path.name} contains {unique_ga_ids:,} unique GA IDs "
                "and may have reached the GrantConnect export ceiling.\n"
                "Split that date range into smaller exports before continuing."
            )

        frames.append(file_df)

    combined = pd.concat(frames, ignore_index=True)
    rows_before = len(combined)
    combined = combined.drop_duplicates().copy()
    duplicates_removed = rows_before - len(combined)

    # A repeated GA ID after exact deduplication may indicate overlapping
    # downloads or different copies of an award. Stop for manual review.
    repeated_ga_mask = combined.duplicated(subset=[GA_ID_COL], keep=False)

    if repeated_ga_mask.any():
        repeated_ids = combined.loc[repeated_ga_mask, GA_ID_COL].nunique()
        examples = (
            combined.loc[repeated_ga_mask, GA_ID_COL]
            .drop_duplicates()
            .head(10)
            .tolist()
        )
        raise ValueError(
            f"\nFound {repeated_ids:,} GA IDs more than once after removing "
            f"exact duplicates. Examples: {examples}\n"
            "Check for overlapping monthly date ranges before continuing."
        )

    print(f"\nRows loaded from all files: {rows_before:,}")
    print(f"Exact duplicate rows removed: {duplicates_removed:,}")
    print(f"Validated grant awards: {len(combined):,}")

    return combined


def add_financial_year_columns(df):
    month = df[DATE_COL].dt.month
    calendar_year = df[DATE_COL].dt.year

    financial_year_start = calendar_year.where(month >= 7, calendar_year - 1)
    financial_year_end = (financial_year_start + 1) % 100

    df["Financial Year"] = (
        "FY"
        + financial_year_start.astype(str)
        + "-"
        + financial_year_end.astype(str).str.zfill(2)
    )

    return df


def financial_year_period_text(financial_year):
    """Return a human-readable July-to-June period for an FY label."""
    match = re.fullmatch(r"FY(\d{4})-(\d{2})", financial_year)
    if not match:
        raise ValueError(f"Unexpected financial year label: {financial_year}")

    start_year = int(match.group(1))
    end_year = start_year + 1
    return f"July {start_year} to June {end_year}"


def save_outputs(data, chart_path):
    """Save supporting CSV data and mirror it into the website annual folder."""
    data_path = chart_path.with_name(chart_path.stem + "_data.csv")
    save_chart_data(data, data_path)
    mirror_file_to_website(data_path)


def mirror_file_to_website(source_path):
    """Copy a generated website asset into the matching website annual folder."""
    if GRANTCONNECT_WEBSITE_CHART_DIR is None:
        return

    period_name = source_path.parent.name
    website_period_dir = GRANTCONNECT_WEBSITE_CHART_DIR / period_name
    website_period_dir.mkdir(parents=True, exist_ok=True)

    destination = website_period_dir / source_path.name
    shutil.copy2(source_path, destination)
    print(f"Copied website asset: {destination}")


def mirror_svg_to_website(svg_path):
    """Backward-compatible wrapper for SVG website mirroring."""
    mirror_file_to_website(svg_path)


# ============================================================
# CHART HELPERS
# ============================================================

def count_formatter(value, position):
    return f"{value:,.0f}"


def create_horizontal_count_chart(
    data,
    label_col,
    value_col,
    title,
    output_path,
    xlabel="Number of grant awards published",
    left=0.34,
    label_width=34,
    label_lines=2,
):
    chart_data = data.sort_values(value_col, ascending=True).copy()
    chart_data["ChartLabel"] = chart_data[label_col].apply(
        lambda value: wrap_label(
            value,
            width=label_width,
            max_lines=label_lines,
        )
    )

    fig, ax = plt.subplots(figsize=(16, 9))
    bars = ax.barh(
        chart_data["ChartLabel"],
        chart_data[value_col],
        color=PROJECT_BLUE,
    )

    ax.set_title(title, fontsize=26, pad=25)
    ax.set_xlabel(xlabel, fontsize=16)
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(count_formatter))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.25)

    ax.bar_label(
        bars,
        labels=[f"{value:,.0f}" for value in chart_data[value_col]],
        padding=4,
        fontsize=11,
        fontweight="bold",
    )

    add_standard_footer_with_links(fig, ax, source_text=SOURCE_TEXT)
    apply_chart_layout(fig, left=left)

    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    svg_path = output_path.with_suffix(".svg")
    plt.savefig(svg_path, format="svg", bbox_inches="tight")
    plt.close()

    print(f"Saved chart: {output_path.name}")
    print(f"Saved chart: {svg_path.name}")
    mirror_svg_to_website(svg_path)


def make_value_chart(
    data,
    label_col,
    value_col,
    title,
    output_path,
    total_value,
    count,
    xlabel="Reported Grant Award Value (AUD)",
    left=0.34,
    label_width=34,
    label_lines=2,
):
    if data.empty:
        print(f"Skipped empty chart: {title}")
        return

    create_horizontal_bar_chart(
        data=data,
        label_col=label_col,
        value_col=value_col,
        title=title,
        output_path=output_path,
        source_text=SOURCE_TEXT,
        xlabel=xlabel,
        left=left,
        label_width=label_width,
        label_lines=label_lines,
        bar_color=DEFAULT_BAR_COLOR,
    )

    # Generate a matching scalable SVG for the website.
    # svg.fonttype='none' keeps chart text as text where supported.
    svg_path = output_path.with_suffix(".svg")
    create_horizontal_bar_chart(
        data=data,
        label_col=label_col,
        value_col=value_col,
        title=title,
        output_path=svg_path,
        source_text=SOURCE_TEXT,
        xlabel=xlabel,
        left=left,
        label_width=label_width,
        label_lines=label_lines,
        bar_color=DEFAULT_BAR_COLOR,
    )
    mirror_svg_to_website(svg_path)

    save_outputs(
        data=data,
        chart_path=output_path,
    )


def make_count_chart(
    data,
    label_col,
    value_col,
    title,
    output_path,
    count,
    left=0.34,
    label_width=34,
    label_lines=2,
):
    if data.empty:
        print(f"Skipped empty chart: {title}")
        return

    create_horizontal_count_chart(
        data=data,
        label_col=label_col,
        value_col=value_col,
        title=title,
        output_path=output_path,
        left=left,
        label_width=label_width,
        label_lines=label_lines,
    )

    save_outputs(
        data=data,
        chart_path=output_path,
    )


# ============================================================
# ANNUAL CHART GENERATION
# ============================================================

def generate_charts_for_year(df, financial_year):
    year_df = df[df["Financial Year"] == financial_year].copy()
    period_text = financial_year_period_text(financial_year)

    output_folder = GRANTCONNECT_OUTPUT_DIR / f"{financial_year}_annual"
    output_folder.mkdir(parents=True, exist_ok=True)

    total_value = year_df[VALUE_COL].sum()
    grant_count = len(year_df)
    title_suffix = f"{financial_year}\n{period_text}"

    print("\n" + "=" * 60)
    print(f"Generating annual GrantConnect charts for {title_suffix}")
    print(f"Published grant awards: {grant_count:,}")
    print(f"Total reported value: ${total_value:,.0f}")
    print(f"Output folder: {output_folder}")
    print("=" * 60)

    agency_value = (
        year_df.groupby("Agency", as_index=False)[VALUE_COL]
        .sum()
        .sort_values(VALUE_COL, ascending=False)
        .head(LOCAL_TOP_N)
    )
    make_value_chart(
        agency_value,
        "Agency",
        VALUE_COL,
        f"Reported Value of Grant Awards by Agency\nPublished on GrantConnect — {title_suffix}",
        output_folder / "01_reported_grant_value_by_agency.png",
        total_value,
        grant_count,
        left=0.34,
    )

    category_value = (
        year_df.groupby("Category", as_index=False)[VALUE_COL]
        .sum()
        .sort_values(VALUE_COL, ascending=False)
        .head(LOCAL_TOP_N)
    )
    make_value_chart(
        category_value,
        "Category",
        VALUE_COL,
        f"Reported Value of Grant Awards by Category\nPublished on GrantConnect — {title_suffix}",
        output_folder / "02_reported_grant_value_by_category.png",
        total_value,
        grant_count,
        left=0.36,
    )

    recipient_value = (
        year_df.groupby("Recipient Name", as_index=False)[VALUE_COL]
        .sum()
        .sort_values(VALUE_COL, ascending=False)
        .head(LOCAL_TOP_N)
    )
    make_value_chart(
        recipient_value,
        "Recipient Name",
        VALUE_COL,
        f"Top Recipients by Reported Grant Award Value\nPublished on GrantConnect — {title_suffix}",
        output_folder / "03_top_grant_recipients_by_reported_value.png",
        total_value,
        grant_count,
        left=0.38,
    )

    largest_grants = (
        year_df.sort_values(VALUE_COL, ascending=False)
        .head(5)
        .reset_index(drop=True)
        .copy()
    )
    largest_grants["Rank"] = largest_grants.index + 1
    largest_grants["Grant Label"] = (
        largest_grants["Rank"].astype(str)
        + ". "
        + largest_grants["Recipient Name"]
        + " — "
        + largest_grants["Grant Activity"]
    )
    make_value_chart(
        largest_grants,
        "Grant Label",
        VALUE_COL,
        f"Largest Individual Grant Awards\nPublished on GrantConnect — {title_suffix}",
        output_folder / "04_largest_individual_grant_awards.png",
        total_value,
        grant_count,
        left=0.44,
        label_width=42,
        label_lines=4,
    )

    agency_count = (
        year_df.groupby("Agency", as_index=False)
        .size()
        .rename(columns={"size": "Grant Count"})
        .sort_values("Grant Count", ascending=False)
        .head(LOCAL_TOP_N)
    )
    make_count_chart(
        agency_count,
        "Agency",
        "Grant Count",
        f"Number of Grant Awards by Agency\nPublished on GrantConnect — {title_suffix}",
        output_folder / "05_number_of_grant_awards_by_agency.png",
        grant_count,
        left=0.34,
    )

    category_count = (
        year_df.groupby("Category", as_index=False)
        .size()
        .rename(columns={"size": "Grant Count"})
        .sort_values("Grant Count", ascending=False)
        .head(LOCAL_TOP_N)
    )
    make_count_chart(
        category_count,
        "Category",
        "Grant Count",
        f"Number of Grant Awards by Category\nPublished on GrantConnect — {title_suffix}",
        output_folder / "06_number_of_grant_awards_by_category.png",
        grant_count,
        left=0.36,
    )

    # This is not labelled as a "program" chart because GrantConnect
    # defines GO ID as the grant opportunity identifier while Grant Activity
    # is an award-level field. Grouping the two therefore represents exact
    # GO ID + Grant Activity combinations, not necessarily whole programs.
    activity_group_value = (
        year_df.groupby(["GO ID", "Grant Activity"], as_index=False)[VALUE_COL]
        .sum()
        .sort_values(VALUE_COL, ascending=False)
        .head(LOCAL_TOP_N)
    )
    activity_group_value["Activity Group Label"] = (
        activity_group_value["GO ID"] + " — " + activity_group_value["Grant Activity"]
    )
    make_value_chart(
        activity_group_value,
        "Activity Group Label",
        VALUE_COL,
        f"Top Grant Activity Groups by Reported Award Value\nPublished on GrantConnect — {title_suffix}",
        output_folder / "07_top_grant_activity_groups_by_reported_value.png",
        total_value,
        grant_count,
        left=0.44,
        label_width=42,
        label_lines=3,
    )

    agency_average = (
        year_df.groupby("Agency", as_index=False)
        .agg(
            **{
                "Average Grant Value": (VALUE_COL, "mean"),
                "Grant Count": (VALUE_COL, "size"),
                "Total Grant Value": (VALUE_COL, "sum"),
            }
        )
    )
    agency_average = agency_average[
        agency_average["Grant Count"] >= 10
    ].copy()
    agency_average = (
        agency_average.sort_values("Average Grant Value", ascending=False)
        .head(LOCAL_TOP_N)
    )
    make_value_chart(
        agency_average,
        "Agency",
        "Average Grant Value",
        f"Average Reported Grant Award Value by Agency\nPublished on GrantConnect — {title_suffix}",
        output_folder / "08_average_grant_award_size_by_agency.png",
        None,
        grant_count,
        xlabel="Average Reported Grant Award Value (AUD)",
        left=0.34,
    )


# ============================================================
# MAIN
# ============================================================

def main():
    df = load_and_validate_monthly_files()
    df = add_financial_year_columns(df)

    available_years = sorted(df["Financial Year"].unique())

    print("\nFinancial years found:")
    for financial_year in available_years:
        count = (df["Financial Year"] == financial_year).sum()
        months_found = sorted(
            df.loc[
                df["Financial Year"] == financial_year,
                DATE_COL,
            ].dt.month.unique()
        )
        print(
            f"- {financial_year}: {count:,} grant awards; "
            f"months found {months_found}"
        )

    if TARGET_FINANCIAL_YEAR is not None:
        if TARGET_FINANCIAL_YEAR not in available_years:
            raise ValueError(
                f"No records found for {TARGET_FINANCIAL_YEAR}.\n"
                f"Available years: {available_years}"
            )

        years_to_generate = [TARGET_FINANCIAL_YEAR]

    else:
        years_to_generate = []
        required_months = set(range(1, 13))

        for financial_year in available_years:
            months_found = set(
                df.loc[
                    df["Financial Year"] == financial_year,
                    DATE_COL,
                ].dt.month.unique()
            )

            if COMPLETE_YEARS_ONLY and months_found != required_months:
                print(
                    f"Skipping incomplete financial year {financial_year}: "
                    f"months found {sorted(months_found)}, "
                    f"expected all 12 calendar months"
                )
                continue

            years_to_generate.append(financial_year)

    print("\nFinancial years that will be generated:")
    for financial_year in years_to_generate:
        print(f"- {financial_year}")

    for financial_year in years_to_generate:
        generate_charts_for_year(df, financial_year)

    print("\nDone.")




if __name__ == "__main__":
    main()
