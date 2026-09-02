from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[2]
AUSTENDER_DIR = PROJECT_DIR / "data" / "austender"
OUTPUT_DIR = PROJECT_DIR / "output" / "austender"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

excel_files = sorted(AUSTENDER_DIR.glob("*.xlsx"))

all_data = []

for file in excel_files:
    print(f"Reading: {file.name}")

    df = pd.read_excel(file, header=2)

    df["Source File"] = file.name

    all_data.append(df)

# ============================================================
# COMBINE RAW AUSTENDER EXPORTS
# ============================================================

master_df = pd.concat(all_data, ignore_index=True)

# Convert date fields
master_df["Publish Date"] = pd.to_datetime(
    master_df["Publish Date"],
    errors="coerce",
)

if "Amendment Publish Date" in master_df.columns:
    master_df["Amendment Publish Date"] = pd.to_datetime(
        master_df["Amendment Publish Date"],
        errors="coerce",
    )

# ============================================================
# FINANCIAL YEAR
# ============================================================

def get_financial_year(date):
    if pd.isna(date):
        return pd.NA

    if date.month >= 7:
        return date.year + 1

    return date.year


# ============================================================
# FINANCIAL QUARTER
# ============================================================

def get_financial_quarter(date):
    if pd.isna(date):
        return pd.NA

    month = date.month

    if month in [7, 8, 9]:
        return "Q1"

    elif month in [10, 11, 12]:
        return "Q2"

    elif month in [1, 2, 3]:
        return "Q3"

    else:
        return "Q4"


def format_financial_year_label(financial_year):
    """
    Convert:
    2025 -> FY2024-25
    """

    if pd.isna(financial_year):
        return pd.NA

    financial_year = int(financial_year)

    fy_start = financial_year - 1
    fy_end_short = str(financial_year)[-2:]

    return f"FY{fy_start}-{fy_end_short}"


master_df["Financial Year"] = (
    master_df["Publish Date"]
    .apply(get_financial_year)
)

master_df["Quarter"] = (
    master_df["Publish Date"]
    .apply(get_financial_quarter)
)

master_df["FY Label"] = (
    master_df["Financial Year"]
    .apply(format_financial_year_label)
)

master_df["FY Quarter"] = (
    master_df["FY Label"]
    + "_"
    + master_df["Quarter"]
)

# ============================================================
# CONTRACT / AMENDMENT IDENTIFIERS
# ============================================================

# An amendment points back to the original contract using Parent CN ID.
# For an unamended contract, the CN ID itself is the root contract ID.

master_df["Root CN ID"] = (
    master_df["Parent CN ID"]
    .where(
        master_df["Parent CN ID"].notna(),
        master_df["CN ID"],
    )
)

# Record Date represents when this particular version of the contract
# was published.
#
# Original contract:
#     Publish Date
#
# Amendment:
#     Amendment Publish Date

master_df["Record Date"] = (
    master_df["Amendment Publish Date"]
    .where(
        master_df["Amendment Publish Date"].notna(),
        master_df["Publish Date"],
    )
)

# ============================================================
# SAVE RAW MASTER DATASET
# ============================================================

# IMPORTANT:
# This file deliberately keeps originals AND amendments.
# It acts as the full historical record of what AusTender published.

raw_output_file = (
    OUTPUT_DIR
    / "austender_master.csv"
)

master_df.to_csv(
    raw_output_file,
    index=False,
    encoding="utf-8-sig",
)

# ============================================================
# CREATE CURRENT CONTRACT STATE DATASET
# ============================================================

# For each underlying contract, keep only the latest published version.
#
# Example:
#
# CN123456
# CN123456-A1
# CN123456-A2
#
# -> keep CN123456-A2
#
# This file is useful for analysing the CURRENT state of contracts.
#
# Historical quarterly reporting should still resolve contract versions
# as they existed at the end of the relevant quarter.

current_df = (
    master_df
    .sort_values(
        [
            "Root CN ID",
            "Record Date",
            "CN ID",
        ],
        na_position="first",
    )
    .drop_duplicates(
        subset=["Root CN ID"],
        keep="last",
    )
    .reset_index(drop=True)
)

current_output_file = (
    OUTPUT_DIR
    / "austender_current_contracts.csv"
)

current_df.to_csv(
    current_output_file,
    index=False,
    encoding="utf-8-sig",
)

# ============================================================
# VALIDATION REPORT
# ============================================================

amendment_mask = (
    master_df["Parent CN ID"]
    .notna()
)

raw_value = pd.to_numeric(
    master_df["Value"],
    errors="coerce",
).fillna(0)

current_value = pd.to_numeric(
    current_df["Value"],
    errors="coerce",
).fillna(0)

multi_amendment_contracts = (
    master_df.loc[amendment_mask]
    .groupby("Root CN ID")
    .size()
    .gt(1)
    .sum()
)

print()
print("AusTender master build complete")
print("--------------------------------")

print(
    f"Files combined: "
    f"{len(excel_files):,}"
)

print(
    f"Raw rows: "
    f"{len(master_df):,}"
)

print(
    f"Amendment rows: "
    f"{amendment_mask.sum():,}"
)

print(
    f"Underlying contracts: "
    f"{master_df['Root CN ID'].nunique():,}"
)

print(
    f"Current-state rows: "
    f"{len(current_df):,}"
)

print(
    f"Contracts with multiple amendment rows: "
    f"{multi_amendment_contracts:,}"
)

print(
    f"Raw summed value: "
    f"${raw_value.sum():,.2f}"
)

print(
    f"Current-state summed value: "
    f"${current_value.sum():,.2f}"
)

print("\nFY Quarters found:")

print(
    sorted(
        master_df["FY Quarter"]
        .dropna()
        .unique()
    )
)

print(
    f"\nRaw master saved to:\n"
    f"{raw_output_file}"
)

print(
    f"\nCurrent contract state saved to:\n"
    f"{current_output_file}"
)