"""Download the current official PBS/RPBS Date of Supply workbook and notes."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

LANDING_URL = "https://www.pbs.gov.au/statistics/dos-and-dop/dos-and-dop"
USER_AGENT = "APET/1.0 (public data research)"


def download(url: str, destination: Path) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    size = 0
    with urlopen(request, timeout=120) as response, destination.open("wb") as output:
        while block := response.read(1024 * 1024):
            output.write(block)
            digest.update(block)
            size += len(block)
    return {"name": destination.name, "url": url, "bytes": size, "sha256": digest.hexdigest()}


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=project_root / "data/pbs/raw")
    parser.add_argument("--force", action="store_true", help="Download again even when the current file is cached")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    request = Request(LANDING_URL, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        html = response.read().decode("utf-8", errors="replace")
    workbook_matches = re.findall(r'href=["\']([^"\']*dos-jul-[^"\']+\.xlsx)["\']', html, flags=re.I)
    notes_matches = re.findall(r'href=["\']([^"\']*explanatory-notes\.docx)["\']', html, flags=re.I)
    if not workbook_matches:
        raise RuntimeError("Could not find the Date of Supply workbook on the official PBS page")

    urls = [urljoin(LANDING_URL, workbook_matches[0])]
    if notes_matches:
        urls.append(urljoin(LANDING_URL, notes_matches[0]))
    files = []
    for url in urls:
        destination = args.output_dir / url.rsplit("/", 1)[-1]
        if destination.exists() and not args.force:
            content = destination.read_bytes()
            files.append({"name": destination.name, "url": url, "bytes": len(content),
                          "sha256": hashlib.sha256(content).hexdigest(), "action": "cached"})
            print(f"Kept cached: {destination}")
        else:
            item = download(url, destination)
            item["action"] = "downloaded"
            files.append(item)
            print(f"Downloaded: {destination} ({item['bytes']:,} bytes)")

    manifest = {
        "dataset": "PBS and RPBS Date of Supply Data",
        "source_url": LANDING_URL,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }
    path = args.output_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Saved manifest: {path}")


if __name__ == "__main__":
    main()
