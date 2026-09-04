"""Download a resumable sample or complete ARC NCGP Grants API archive."""
from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://dataportal.arc.gov.au/NCGP/API/grants"
SOURCE_URL = "https://www.arc.gov.au/funding-research/funding-outcomes/grants-dataset"


def fetch_page(page_number: int, page_size: int) -> tuple[bytes, dict]:
    query = urlencode({"page[number]": page_number, "page[size]": page_size})
    url = f"{API_URL}?{query}"
    request = Request(url, headers={"User-Agent": "APET/1.0 (public data research)", "Accept": "application/json"})
    with urlopen(request, timeout=90) as response:
        content = response.read()
    payload = json.loads(content.decode("utf-8-sig"))
    if not isinstance(payload.get("data"), list) or not isinstance(payload.get("meta"), dict):
        raise ValueError(f"Unexpected ARC API response structure: {url}")
    return content, payload


def load_or_fetch(output_dir: Path, page_number: int, page_size: int, force: bool) -> tuple[int, bytes, dict, str]:
    destination = output_dir / f"arc_ncgp_grants_page_{page_number:04d}.json"
    if destination.exists() and not force:
        content = destination.read_bytes()
        payload = json.loads(content.decode("utf-8-sig"))
        if payload.get("meta", {}).get("requested-page-size") == page_size:
            return page_number, content, payload, "Kept cached"
    content, payload = fetch_page(page_number, page_size)
    destination.write_bytes(content)
    return page_number, content, payload, "Downloaded"


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=project_root / "data" / "arc_grants" / "raw")
    parser.add_argument("--pages", type=int, default=2, help="Sample page count (default: 2)")
    parser.add_argument("--all", action="store_true", help="Download every page reported by the API")
    parser.add_argument("--page-size", type=int, default=1000, help="Records per page, maximum 1000")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent API requests (default: 4)")
    parser.add_argument("--force", action="store_true", help="Replace existing raw page files")
    args = parser.parse_args()
    if args.pages < 1 or not 1 <= args.page_size <= 1000 or not 1 <= args.workers <= 8:
        raise ValueError("Pages must be positive and page size must be between 1 and 1000")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "dataset": "ARC National Competitive Grants Program Grants Search",
        "source_url": SOURCE_URL,
        "api_url": API_URL,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "complete_collection": args.all,
        "requested_pages": None,
        "page_size": args.page_size,
        "files": [],
    }
    first = load_or_fetch(args.output_dir, 1, args.page_size, args.force)
    reported_total = first[2]["meta"].get("total-size")
    requested_pages = int(first[2]["meta"]["total-pages"]) if args.all else args.pages
    def task(page_number):
        return load_or_fetch(args.output_dir, page_number, args.page_size, args.force)
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        results = [first] + list(executor.map(task, range(2, requested_pages + 1)))
    for page_number, content, payload, action in sorted(results):
        if payload["meta"].get("total-size") != reported_total:
            raise ValueError("ARC API total changed while the archive was downloading")
        destination = args.output_dir / f"arc_ncgp_grants_page_{page_number:04d}.json"
        manifest["files"].append({
            "name": destination.name,
            "page_number": page_number,
            "records": len(payload["data"]),
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        })
        print(f"{action}: {destination} ({len(payload['data']):,} records)")
    manifest["requested_pages"] = requested_pages
    manifest["api_reported_total_records"] = reported_total
    manifest["records_downloaded"] = sum(item["records"] for item in manifest["files"])
    path = args.output_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Saved manifest: {path}")


if __name__ == "__main__":
    main()


