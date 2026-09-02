from pathlib import Path
import re
import shutil
import sys
import tempfile

import requests

# ============================================================
# APET — DOWNLOAD MISSING IPEA QUARTERLY DATA
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parents[2]
IPEA_DATA_DIR = PROJECT_DIR / "data" / "ipea"

CKAN_API = "https://data.gov.au/data/api/3/action/package_search"
START_YEAR = 2020

# None = fetch every missing IPEA quarter from START_YEAR onward.
# Set, for example, 2023 if you only want to fetch through 2023.
END_YEAR = None

MONTH_TO_QUARTER = {
    "January": 1,
    "April": 2,
    "July": 3,
    "October": 4,
}

REQUIRED_COLUMNS = {
    "FullNameWithTitle",
    "HighLevelCategory",
    "MajorSubCategory",
    "Amount",
}


def get_ipea_datasets():
    """Return all IPEA datasets from data.gov.au's CKAN API."""
    response = requests.get(
        CKAN_API,
        params={
            "fq": "organization:ipea",
            "rows": 100,
        },
        timeout=60,
    )
    response.raise_for_status()

    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError("data.gov.au CKAN API returned success=false")

    return payload["result"]["results"]


def parse_quarter_from_title(title):
    """
    Convert a title such as:
    Current and Former Parliamentarians' Expenditure 1 July to 30 September 2020
    into (2020, 3).
    """
    match = re.search(
        r"Expenditure\s+1\s+(January|April|July|October)\s+to\s+"
        r"\d{1,2}\s+\w+\s+(\d{4})$",
        title,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    month = match.group(1).title()
    year = int(match.group(2))
    return year, MONTH_TO_QUARTER[month]


def find_expenses_resource(dataset):
    """Select the main quarterly parliamentarian expenses CSV resource."""
    candidates = []

    for resource in dataset.get("resources", []):
        name = str(resource.get("name", "")).lower()
        fmt = str(resource.get("format", "")).lower()
        url = str(resource.get("url", ""))

        if "expense" not in name:
            continue

        if "csv" not in fmt and not url.lower().endswith(".csv"):
            continue

        candidates.append(resource)

    if not candidates:
        return None

    # The expenses resource is normally position 0. Sort defensively.
    candidates.sort(key=lambda item: item.get("position", 999))
    return candidates[0]


def validate_download(csv_path):
    """Check that the downloaded file looks like an IPEA expense extract."""
    import csv

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        headers = next(reader, [])

    headers = {header.strip() for header in headers}
    missing = REQUIRED_COLUMNS - headers

    if missing:
        raise ValueError(
            f"{csv_path.name} is missing expected columns: {sorted(missing)}"
        )


def download_file(url, destination):
    """Stream one official CSV to disk safely."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=".csv",
        dir=destination.parent,
        delete=False,
    ) as temp:
        temp_path = Path(temp.name)

        with requests.get(url, stream=True, timeout=120) as response:
            response.raise_for_status()

            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    temp.write(chunk)

    try:
        validate_download(temp_path)
        shutil.move(str(temp_path), destination)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def main():
    IPEA_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Checking official IPEA datasets on data.gov.au...")
    datasets = get_ipea_datasets()

    available = []

    for dataset in datasets:
        title = str(dataset.get("title", "")).strip()
        parsed = parse_quarter_from_title(title)

        if parsed is None:
            continue

        year, quarter = parsed

        if year < START_YEAR:
            continue

        if END_YEAR is not None and year > END_YEAR:
            continue

        resource = find_expenses_resource(dataset)
        if resource is None:
            print(f"Warning: no expenses CSV resource found for: {title}")
            continue

        available.append(
            {
                "year": year,
                "quarter": quarter,
                "title": title,
                "url": resource["url"],
            }
        )

    available.sort(key=lambda item: (item["year"], item["quarter"]))

    if not available:
        raise RuntimeError("No matching IPEA quarterly datasets were found.")

    downloaded = 0
    skipped = 0

    for item in available:
        filename = (
            f"{item['year']}q{item['quarter']:02d}_dataextract.csv"
        )
        destination = IPEA_DATA_DIR / filename

        if destination.exists():
            print(f"Already present: {filename}")
            skipped += 1
            continue

        print()
        print(f"Downloading: {filename}")
        print(f"Period: {item['title']}")
        print(f"Source: {item['url']}")

        download_file(item["url"], destination)

        print(f"Saved: {destination}")
        downloaded += 1

    print()
    print("=" * 72)
    print(f"Downloaded new quarterly files: {downloaded}")
    print(f"Already present / skipped: {skipped}")
    print(f"IPEA data folder: {IPEA_DATA_DIR}")
    print()
    print(
        "You can now rerun generate_quarterly_charts.py and "
        "generate_annual_charts.py."
    )


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"Network/download error: {exc}", file=sys.stderr)
        raise

