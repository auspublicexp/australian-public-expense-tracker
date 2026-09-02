from collections import Counter
import os
from pathlib import Path
import re

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data" / "grantconnect"

# Override this when downloads are stored somewhere else, for example:
# APET_DOWNLOAD_DIR="D:\Downloads" python reconcile_grantconnect_archive.py
DOWNLOAD_DIR = Path(
    os.environ.get("APET_DOWNLOAD_DIR", Path.home() / "Downloads")
)

files = sorted(DATA_DIR.glob("grantconnect_FY*.xlsx"))
print(f"Scanning {len(files)} workbook files...", flush=True)
frames = []
intervals = []
errors = []

for path in files:
    raw = pd.read_excel(path, header=None)
    header_row = next(
        idx
        for idx, row in raw.head(30).iterrows()
        if "GA ID" in [str(value).strip() for value in row.tolist()]
        and "Publish Date" in [str(value).strip() for value in row.tolist()]
    )
    data = pd.read_excel(path, header=header_row)

    date_range = str(raw.iloc[8, 1])
    match = re.fullmatch(
        r"(\d{1,2}-[A-Za-z]{3}-\d{4}) to (\d{1,2}-[A-Za-z]{3}-\d{4})",
        date_range,
    )
    if not match:
        errors.append(f"invalid criteria range: {path.name}")
        continue

    start = pd.to_datetime(match.group(1))
    end = pd.to_datetime(match.group(2))
    intervals.append((start, end, path.name))

    month = start.month
    start_year = start.year if month >= 7 else start.year - 1
    quarter = (
        1 if month in (7, 8, 9)
        else 2 if month in (10, 11, 12)
        else 3 if month in (1, 2, 3)
        else 4
    )
    expected_label = f"FY{start_year}-{(start_year + 1) % 100:02d}_Q{quarter}"
    if expected_label not in path.name:
        errors.append(f"quarter: {path.name}; expected {expected_label}")

    publish_dates = pd.to_datetime(data["Publish Date"], errors="coerce")
    if (
        publish_dates.isna().any()
        or (publish_dates.dt.normalize() < start).any()
        or (publish_dates.dt.normalize() > end).any()
    ):
        errors.append(f"publish date outside criteria: {path.name}")

    if len(data) >= 10000:
        errors.append(f"possible cap: {path.name}")
    if data.duplicated().any():
        errors.append(f"internal duplicate: {path.name}")

    data["__file"] = path.name
    frames.append(data)
    if len(frames) % 10 == 0:
        print(f"Scanned {len(frames)} files...", flush=True)

all_data = pd.concat(frames, ignore_index=True)
data_without_file = all_data.drop(columns=["__file"])

coverage = Counter()
for start, end, _ in intervals:
    for day in pd.date_range(start, end, freq="D"):
        coverage[day.date()] += 1

expected_days = [
    day.date()
    for day in pd.date_range("2020-01-01", "2026-08-31", freq="D")
]
missing_days = [day for day in expected_days if coverage[day] == 0]
overlapping_days = [day for day in expected_days if coverage[day] > 1]
outside_days = [
    day for day in coverage
    if day < expected_days[0] or day > expected_days[-1]
]

print("files", len(files))
print("rows", len(all_data))
print("unique_ga", all_data["GA ID"].nunique())
print("exact_duplicates_across_files", int(data_without_file.duplicated().sum()))
print("duplicate_GA_IDs", int(all_data.duplicated(subset=["GA ID"]).sum()))
print("missing_covered_days", len(missing_days))
print("overlapping_covered_days", len(overlapping_days))
print("outside_days", len(outside_days))
print("errors", errors)
print(
    "raw_downloads_left",
    len(list(DOWNLOAD_DIR.glob("GrantConnect-Grant-Award-List_*.xlsx"))),
)

publish = pd.to_datetime(all_data["Publish Date"])

def fy_quarter(value):
    start_year = value.year if value.month >= 7 else value.year - 1
    quarter = (
        1 if value.month in (7, 8, 9)
        else 2 if value.month in (10, 11, 12)
        else 3 if value.month in (1, 2, 3)
        else 4
    )
    return f"FY{start_year}-{(start_year + 1) % 100:02d}_Q{quarter}"

all_data["FYQ"] = publish.apply(fy_quarter)
print(all_data.groupby("FYQ").size().to_string())

