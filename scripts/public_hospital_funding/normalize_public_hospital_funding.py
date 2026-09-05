"""Normalize the NHFB wide financial-year CSVs into tidy monthly records."""

from __future__ import annotations

import argparse
import csv
import re
from datetime import date
from pathlib import Path


FY_PATTERN = re.compile(r"^20\d{2}-\d{2}$")
MONTH_NUMBERS = {
    "July": 7, "August": 8, "September": 9, "October": 10,
    "November": 11, "December": 12, "January": 1, "February": 2,
    "March": 3, "April": 4, "May": 5, "June": 6,
}


def month_start(financial_year: str, month: str) -> str:
    start_year = int(financial_year[:4])
    month_number = MONTH_NUMBERS[month]
    calendar_year = start_year if month_number >= 7 else start_year + 1
    return date(calendar_year, month_number, 1).isoformat()


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"No header found in {path}")
        years = [field for field in reader.fieldnames if FY_PATTERN.fullmatch(field)]
        return list(reader), years


def completed_financial_years(available_years: list[str], today: date | None = None) -> list[str]:
    """Return published financial years whose June end date has passed."""
    today = today or date.today()
    current_fy_start = today.year if today.month >= 7 else today.year - 1
    latest_completed_start = current_fy_start - 1
    return [year for year in available_years if int(year[:4]) <= latest_completed_start]


def parse_amount(value: str, context: str) -> int | None:
    cleaned = (value or "").strip().replace(",", "")
    if cleaned == "":
        return None
    try:
        number = float(cleaned)
    except ValueError as exc:
        raise ValueError(f"Invalid amount {value!r} at {context}") from exc
    if not number.is_integer():
        raise ValueError(f"Expected whole dollars but found {value!r} at {context}")
    return int(number)


def normalize_state(input_path: Path, output_path: Path, years: list[str]) -> int:
    rows, available_years = read_rows(input_path)
    selected = [year for year in years if year in available_years]
    if selected != years:
        raise ValueError(f"Missing requested years: {sorted(set(years) - set(selected))}")
    fields = ["financial_year", "month", "month_start", "state_territory", "payment_dollars"]
    count = 0
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            month = row["Month"].strip()
            if month not in MONTH_NUMBERS:
                raise ValueError(f"Unexpected month {month!r}")
            for year in selected:
                amount = parse_amount(row[year], f"{row['State/Territory']} {month} {year}")
                if amount is None:
                    continue
                writer.writerow({
                    "financial_year": f"FY{year}", "month": month,
                    "month_start": month_start(year, month),
                    "state_territory": row["State/Territory"].strip(),
                    "payment_dollars": amount,
                })
                count += 1
    return count


def normalize_category(input_path: Path, output_path: Path, years: list[str]) -> int:
    rows, available_years = read_rows(input_path)
    selected = [year for year in years if year in available_years]
    if selected != years:
        raise ValueError(f"Missing requested years: {sorted(set(years) - set(selected))}")
    fields = ["financial_year", "month", "month_start", "state_territory",
              "funding_method", "service_category", "payment_dollars"]
    count = 0
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            month = row["Month"].strip()
            if month not in MONTH_NUMBERS:
                raise ValueError(f"Unexpected month {month!r}")
            for year in selected:
                amount = parse_amount(row[year], f"{row['State/Territory']} {month} {year}")
                if amount is None:
                    continue
                writer.writerow({
                    "financial_year": f"FY{year}", "month": month,
                    "month_start": month_start(year, month),
                    "state_territory": row["State/Territory"].strip(),
                    "funding_method": row["Service Category Group"].strip(),
                    "service_category": row["Service Category"].strip(),
                    "payment_dollars": amount,
                })
                count += 1
    return count


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path,
                        default=project_root / "data" / "public_hospital_funding" / "raw")
    parser.add_argument("--output-dir", type=Path,
                        default=project_root / "data" / "public_hospital_funding" / "normalized")
    parser.add_argument(
        "--years", nargs="+",
        help="Financial years such as 2024-25; default is every completed year in the files",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    _, available_years = read_rows(args.raw_dir / "payments_by_state_trend.csv")
    years = args.years or completed_financial_years(available_years)
    if not years:
        raise ValueError("No completed financial-year columns were found")

    state_count = normalize_state(
        args.raw_dir / "payments_by_state_trend.csv",
        args.output_dir / "monthly_payments_by_state.csv", years,
    )
    category_count = normalize_category(
        args.raw_dir / "payments_by_service_category_trend.csv",
        args.output_dir / "monthly_payments_by_service_category.csv", years,
    )
    print(f"Completed financial years: {', '.join('FY' + year for year in years)}")
    print(f"Saved {state_count:,} state-month rows and {category_count:,} category-month rows.")


if __name__ == "__main__":
    main()
