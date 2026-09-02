"""Download official ABS annual Government Finance Statistics workbooks.

GFS is not currently in the ABS Data API catalogue, so this downloader uses
the official XLSX files linked from the annual release. Existing files are
kept unless --force is supplied.
"""

from argparse import ArgumentParser
from pathlib import Path
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RELEASE = "2024-25"
FINANCIAL_YEAR = f"FY{RELEASE}"
BASE_URL = (
    "https://www.abs.gov.au/statistics/economy/government/"
    f"government-finance-statistics-annual/{RELEASE}/"
)
FILES = {
    "key_tables.xlsx": "55120DO094_202425.xlsx",
    "table_000_all_sectors.xlsx": "55120DO001_202425.xlsx",
    "table_130_commonwealth.xlsx": "55120DO002_202425.xlsx",
    "table_239_total_state.xlsx": "55120DO011_202425.xlsx",
    "table_339_total_local.xlsx": "55120DO019_202425.xlsx",
    "table_939_all_levels.xlsx": "55120DO021_202425.xlsx",
}


def download(url: str, destination: Path) -> None:
    request = Request(url, headers={"User-Agent": "APET/1.0 (public data downloader)"})
    with urlopen(request, timeout=90) as response:
        content = response.read()
    if not content.startswith(b"PK"):
        raise ValueError(f"ABS response was not an XLSX workbook: {url}")
    destination.write_bytes(content)


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "abs_gfs" / "raw" / FINANCIAL_YEAR,
    )
    parser.add_argument("--force", action="store_true", help="Replace cached files")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for local_name, remote_name in FILES.items():
        destination = args.output_dir / local_name
        if destination.exists() and not args.force:
            print(f"Keeping cached file: {destination}")
            continue
        print(f"Downloading {remote_name} ...")
        download(BASE_URL + remote_name, destination)
        print(f"Saved: {destination}")


if __name__ == "__main__":
    main()
