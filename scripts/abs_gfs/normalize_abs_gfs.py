"""Normalize ABS GFS workbooks into small, chart-ready CSV tables."""

from argparse import ArgumentParser
from datetime import date
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

YEARS = [f"{year}-{str(year + 1)[-2:]}" for year in range(2015, 2025)]
PURPOSES = [
    "General public services", "Defence", "Public order and safety",
    "Economic affairs", "Environmental protection",
    "Housing and community amenities", "Health",
    "Recreation, culture and religion", "Education", "Social protection",
    "Transport",
]
LEVEL_FILES = {
    "Commonwealth": "table_130_commonwealth.xlsx",
    "State and territory": "table_239_total_state.xlsx",
    "Local": "table_339_total_local.xlsx",
}


def clean_label(value) -> str:
    return " ".join(str(value).strip().split()).casefold()


def read_table(path: Path, sheet: str) -> pd.DataFrame:
    frame = pd.read_excel(path, sheet_name=sheet, header=None)
    if frame.shape[1] != 11:
        raise ValueError(f"Unexpected layout in {path.name}/{sheet}: {frame.shape}")
    years = [str(value).strip() for value in frame.iloc[4, 1:].tolist()]
    if years != YEARS:
        raise ValueError(f"Unexpected years in {path.name}/{sheet}: {years}")
    return frame


def find_row(frame: pd.DataFrame, labels: list[str]) -> pd.Series:
    wanted = {clean_label(label) for label in labels}
    matches = frame[frame.iloc[:, 0].map(clean_label).isin(wanted)]
    if len(matches) != 1:
        raise ValueError(f"Expected one row for {labels}; found {len(matches)}")
    return matches.iloc[0]


def series_records(row: pd.Series, **dimensions) -> list[dict]:
    values = pd.to_numeric(row.iloc[1:], errors="raise")
    records = []
    for year, value in zip(YEARS, values, strict=True):
        start_year = int(year[:4])
        records.append({
        "period_type": "financial_year",
        "financial_year": f"FY{year}",
        "financial_year_slug": f"fy{start_year}_{str(start_year + 1)[-2:]}",
        "financial_year_quarter": "",
        "period_start": date(start_year, 7, 1).isoformat(),
        "period_end": date(start_year + 1, 6, 30).isoformat(),
        **dimensions, "value_millions": int(value),
        "unit": "AUD millions", "accounting_basis": "accrual",
        "price_basis": "current prices", "series_type": "original",
        })
    return records


def normalize(raw_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_levels = read_table(raw_dir / "table_939_all_levels.xlsx", "Table_1")
    summary = pd.DataFrame(series_records(
        find_row(all_levels, ["Total GFS expenses", "Total expenses"]),
        government_level="All Australia, all levels", sector="General government",
        measure="Total expenses", source_file="table_939_all_levels.xlsx",
        source_sheet="Table_1"))

    purpose_table = read_table(raw_dir / "table_939_all_levels.xlsx", "Table_4")
    purpose_records = []
    for purpose in PURPOSES:
        purpose_records.extend(series_records(
            find_row(purpose_table, [purpose, f"Total {purpose}"]),
            government_level="All Australia, all levels", sector="General government",
            purpose=purpose, source_file="table_939_all_levels.xlsx", source_sheet="Table_4"))
    purposes = pd.DataFrame(purpose_records)

    level_records = []
    for level, filename in LEVEL_FILES.items():
        table = read_table(raw_dir / filename, "Table_4")
        level_records.extend(series_records(
            find_row(table, ["Total expenses"]), government_level=level,
            sector="General government", measure="Total expenses",
            source_file=filename, source_sheet="Table_4"))
    levels = pd.DataFrame(level_records)

    key = read_table(raw_dir / "key_tables.xlsx", "Table_6")
    key_values = pd.to_numeric(find_row(key, ["GFS expenses"]).iloc[1:], errors="raise").astype("int64").tolist()
    if summary["value_millions"].tolist() != key_values:
        raise ValueError("Headline expenses do not reconcile with ABS Key Table 6")
    purpose_totals = purposes.groupby("financial_year")["value_millions"].sum()
    expected = summary.set_index("financial_year")["value_millions"]
    differences = purpose_totals - expected
    # ABS publishes these components rounded to the nearest $1 million. Adding
    # the displayed components can therefore differ from the displayed total
    # by a few million even though the underlying unrounded values reconcile.
    if differences.abs().max() > 5:
        raise ValueError(f"Purpose categories do not reconcile: {differences.to_dict()}")

    for name, frame in {"annual_expenses.csv": summary,
                        "expenses_by_purpose.csv": purposes,
                        "expenses_by_level.csv": levels}.items():
        frame.to_csv(output_dir / name, index=False)
        print(f"Saved {len(frame):,} rows: {output_dir / name}")
    print(
        "Validation passed: headline reconciles exactly; purpose totals are "
        f"within ABS rounding tolerance (largest difference ${differences.abs().max():,.0f}m)."
    )


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "abs_gfs" / "raw" / "FY2024-25",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "abs_gfs" / "normalized",
    )
    args = parser.parse_args()
    normalize(args.raw_dir, args.output_dir)


if __name__ == "__main__":
    main()
