"""Download DFAT's current official IATI activity XML archive."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

DATASET_ID = "07136b9b-f877-4af8-b19b-b0cb9a76a7d0"
CKAN_URL = f"https://data.gov.au/data/api/3/action/package_show?id={DATASET_ID}"
LANDING_URL = "https://data.gov.au/data/dataset/dfat-australia-iati-activity-file"
USER_AGENT = "APET/1.0 (public data research; https://auspublicexp.org/)"
CODELISTS = {
    "country": "https://codelists.codeforiati.org/api/json/en/Country.json",
    "region": "https://codelists.codeforiati.org/api/json/en/Region.json",
    "sector": "https://codelists.codeforiati.org/api/json/en/Sector.json",
    "sector_category": "https://codelists.codeforiati.org/api/json/en/SectorCategory.json",
    "transaction_type": "https://codelists.codeforiati.org/api/json/en/TransactionType.json",
}


def open_url(url: str):
    return urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=180)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=project_root / "data/dfat_foreign_aid/raw")
    parser.add_argument("--force", action="store_true", help="Replace the cached XML file")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with open_url(CKAN_URL) as response:
        metadata = json.load(response)
    if not metadata.get("success"):
        raise RuntimeError("data.gov.au did not return successful dataset metadata")
    resources = [r for r in metadata["result"].get("resources", []) if str(r.get("format", "")).upper() == "XML"]
    if len(resources) != 1 or not resources[0].get("url"):
        raise RuntimeError(f"Expected one DFAT IATI XML resource; found {len(resources)}")
    resource = resources[0]
    destination = args.output_dir / "dfat_australia_iati_activity.xml"

    action = "cached"
    if args.force or not destination.exists():
        temporary = destination.with_suffix(".xml.part")
        with open_url(resource["url"]) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        temporary.replace(destination)
        action = "downloaded"

    codelist_files = []
    for name, url in CODELISTS.items():
        path = args.output_dir / f"iati_{name}_codelist.json"
        codelist_action = "cached"
        if args.force or not path.exists():
            with open_url(url) as response:
                content = response.read()
            json.loads(content.decode("utf-8"))
            path.write_bytes(content)
            codelist_action = "downloaded"
        codelist_files.append({
            "name": path.name,
            "url": url,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "action": codelist_action,
        })

    manifest = {
        "dataset": metadata["result"].get("title"),
        "dataset_id": DATASET_ID,
        "source_url": LANDING_URL,
        "metadata_url": CKAN_URL,
        "resource_url": resource["url"],
        "resource_last_modified": resource.get("last_modified"),
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "file": {
            "name": destination.name,
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
            "action": action,
        },
        "iati_codelists": codelist_files,
    }
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{action.title()}: {destination} ({destination.stat().st_size:,} bytes)")
    print(f"Saved manifest: {manifest_path}")


if __name__ == "__main__":
    main()
