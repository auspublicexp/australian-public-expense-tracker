from pathlib import Path
import shutil
import subprocess
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
GRANTCONNECT_WEBSITE_CHART_DIR = Path(
    r"C:\dev\australian-public-expense-tracker\website\public_html\charts\grantconnect"
)

# This matches monthly files and split-month files such as:
# grantconnect_FY2024-25_Q4_2025-05.xlsx
# grantconnect_FY2024-25_Q4_2025-04a.xlsx
# Files inside archive_incomplete are ignored because this glob is not recursive.
INPUT_FILE_PATTERN = "grantconnect_FY????-??_Q?_????-??*.xlsx"

# Use None to regenerate every quarter available in the monthly files.
# To generate one quarter only, use—for example—"FY2024-25_Q3".
TARGET_FY_QUARTER = None
COMPLETE_QUARTERS_ONLY = True

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


def add_financial_quarter_columns(df):
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

    quarter_number = month.map(
        {
            7: 1,
            8: 1,
            9: 1,
            10: 2,
            11: 2,
            12: 2,
            1: 3,
            2: 3,
            3: 3,
            4: 4,
            5: 4,
            6: 4,
        }
    )

    df["FY Quarter"] = (
        df["Financial Year"] + "_Q" + quarter_number.astype(str)
    )

    return df


def quarter_period_text(fy_quarter):
    quarter = fy_quarter.rsplit("_Q", 1)[1]

    return {
        "1": "July to September",
        "2": "October to December",
        "3": "January to March",
        "4": "April to June",
    }[quarter]


def save_outputs(data, chart_path):
    """Save supporting CSV data and mirror it into the website quarter folder."""
    data_path = chart_path.with_name(chart_path.stem + "_data.csv")
    save_chart_data(data, data_path)
    mirror_file_to_website(data_path)


def mirror_file_to_website(source_path):
    """Copy a generated website asset into the matching website quarter folder."""
    quarter_name = source_path.parent.name
    website_quarter_dir = GRANTCONNECT_WEBSITE_CHART_DIR / quarter_name
    website_quarter_dir.mkdir(parents=True, exist_ok=True)

    destination = website_quarter_dir / source_path.name
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
# QUARTERLY CHART GENERATION
# ============================================================

def generate_charts_for_quarter(df, fy_quarter):
    quarter_df = df[df["FY Quarter"] == fy_quarter].copy()
    period_text = quarter_period_text(fy_quarter)

    output_folder = GRANTCONNECT_OUTPUT_DIR / fy_quarter
    output_folder.mkdir(parents=True, exist_ok=True)

    total_value = quarter_df[VALUE_COL].sum()
    grant_count = len(quarter_df)
    title_suffix = f"{fy_quarter}\n{period_text}"

    print("\n" + "=" * 60)
    print(f"Generating GrantConnect charts for {title_suffix}")
    print(f"Published grant awards: {grant_count:,}")
    print(f"Total reported value: ${total_value:,.0f}")
    print(f"Output folder: {output_folder}")
    print("=" * 60)

    agency_value = (
        quarter_df.groupby("Agency", as_index=False)[VALUE_COL]
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
        quarter_df.groupby("Category", as_index=False)[VALUE_COL]
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
        quarter_df.groupby("Recipient Name", as_index=False)[VALUE_COL]
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
        quarter_df.sort_values(VALUE_COL, ascending=False)
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
        quarter_df.groupby("Agency", as_index=False)
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
        quarter_df.groupby("Category", as_index=False)
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
        quarter_df.groupby(["GO ID", "Grant Activity"], as_index=False)[VALUE_COL]
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
        quarter_df.groupby("Agency", as_index=False)
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
    df = add_financial_quarter_columns(df)

    available_quarters = sorted(df["FY Quarter"].unique())

    print("\nFY quarters found:")
    for fy_quarter in available_quarters:
        count = (df["FY Quarter"] == fy_quarter).sum()
        print(f"- {fy_quarter}: {count:,} grant awards")

    if TARGET_FY_QUARTER is not None:
        if TARGET_FY_QUARTER not in available_quarters:
            raise ValueError(
                f"No records found for {TARGET_FY_QUARTER}.\n"
                f"Available quarters: {available_quarters}"
            )

        quarters_to_generate = [TARGET_FY_QUARTER]

    else:
        quarters_to_generate = []

        expected_months = {
            "Q1": {7, 8, 9},
            "Q2": {10, 11, 12},
            "Q3": {1, 2, 3},
            "Q4": {4, 5, 6},
        }

        for fy_quarter in available_quarters:
            quarter_name = fy_quarter.rsplit("_", 1)[1]

            months_found = set(
                df.loc[
                    df["FY Quarter"] == fy_quarter,
                    DATE_COL,
                ].dt.month.unique()
            )

            required_months = expected_months[quarter_name]

            if COMPLETE_QUARTERS_ONLY and months_found != required_months:
                print(
                    f"Skipping incomplete quarter {fy_quarter}: "
                    f"months found {sorted(months_found)}, "
                    f"expected {sorted(required_months)}"
                )
                continue

            quarters_to_generate.append(fy_quarter)

    print("\nQuarters that will be generated:")
    for fy_quarter in quarters_to_generate:
        print(f"- {fy_quarter}")

    for fy_quarter in quarters_to_generate:
        generate_charts_for_quarter(df, fy_quarter)

    search_builder = Path(__file__).with_name("build_grantconnect_search_index.py")
    if search_builder.exists():
        print("\nUpdating the GrantConnect website search index...")
        subprocess.run([sys.executable, str(search_builder)], check=True)

    print("\nDone.")


if __name__ == "__main__":
    main()
