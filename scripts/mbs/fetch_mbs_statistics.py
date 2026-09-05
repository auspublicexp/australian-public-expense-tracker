"""Download the latest official quarterly Medicare statistics workbook."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

COLLECTION_URL = "https://www.health.gov.au/resources/collections/medicare-statistics-collection"
SOURCE_URL = "https://www.health.gov.au/sites/default/files/2026-08/medicare-quarterly-statistics-state-and-territory-june-quarter-2025-26.xlsx"
USER_AGENT = "APET/1.0 (public data research)"


def read_url(url: str, attempts: int = 3) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, attempts + 1):
        try:
            with urlopen(request, timeout=300) as response:
                return response.read()
        except (TimeoutError, OSError) as error:
            if attempt == attempts:
                raise RuntimeError(
                    f"The official Medicare download did not respond after {attempts} attempts. "
                    "Please try the fetch script again later."
                ) from error
            print(f"Download attempt {attempt} timed out; trying again...")
            time.sleep(2 * attempt)
    raise RuntimeError("Medicare download failed")


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=project_root / "data/mbs/raw")
    parser.add_argument("--source-url", default=SOURCE_URL,
                        help="Official quarterly Medicare Excel workbook URL")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    workbook_url = args.source_url
    destination = args.output_dir / workbook_url.rsplit("/", 1)[-1]
    if destination.exists() and not args.force:
        content = destination.read_bytes()
        action = "cached"
    else:
        content = read_url(workbook_url)
        destination.write_bytes(content)
        action = "downloaded"

    manifest = {
        "dataset": "Medicare quarterly statistics – State and territory",
        "collection_url": COLLECTION_URL,
        "source_url": workbook_url,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "file": destination.name,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{action.title()}: {destination} ({len(content):,} bytes)")


if __name__ == "__main__":
    main()
