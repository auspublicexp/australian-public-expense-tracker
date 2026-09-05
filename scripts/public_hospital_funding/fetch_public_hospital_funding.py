"""Download a small, reproducible NHFB public-hospital funding prototype.

The files are official CSV extracts published by the National Health Funding
Body on data.gov.au.  Raw files are never modified after download unless the
user explicitly supplies --force.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


RESOURCES = {
    "payments_by_state_trend": {
        "resource_id": "a8b2f649-bed2-479b-a461-bb6ab8fdf52e",
    },
    "payments_by_service_category_trend": {
        "resource_id": "e5530a6c-aab3-4e88-96a9-38f881b1dd52",
    },
}
PACKAGE_ID = "c4afb0c6-624b-4f4e-865d-14af55c6a311"
PACKAGE_API = f"https://data.gov.au/data/api/3/action/package_show?id={PACKAGE_ID}"


def download(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "APET/1.0 (public data research)"})
    with urlopen(request, timeout=90) as response:
        content = response.read()
    first_line = content.decode("utf-8-sig", errors="replace").splitlines()[0]
    if "State/Territory" not in first_line:
        raise ValueError(f"Downloaded file does not look like the expected CSV: {url}")
    return content


def current_resource_urls() -> dict[str, str]:
    request = Request(PACKAGE_API, headers={"User-Agent": "APET/1.0 (public data research)"})
    with urlopen(request, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload.get("success"):
        raise ValueError("data.gov.au package metadata request was unsuccessful")
    return {resource["id"]: resource["url"] for resource in payload["result"]["resources"]}


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path,
        default=project_root / "data" / "public_hospital_funding" / "raw",
    )
    parser.add_argument("--force", action="store_true", help="Replace existing raw files")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    resource_urls = current_resource_urls()

    manifest = {
        "dataset": "NHFB Website Report (Production dataset)",
        "dataset_url": "https://data.gov.au/data/dataset/c4afb0c6-624b-4f4e-865d-14af55c6a311",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": [],
    }
    for name, resource in RESOURCES.items():
        resource_id = resource["resource_id"]
        if resource_id not in resource_urls:
            raise ValueError(f"Expected data.gov.au resource is missing: {resource_id}")
        source_url = resource_urls[resource_id]
        destination = args.output_dir / f"{name}.csv"
        if destination.exists() and not args.force:
            content = destination.read_bytes()
            action = "kept cached"
        else:
            content = download(source_url)
            destination.write_bytes(content)
            action = "downloaded"
        manifest["files"].append(
            {
                "name": destination.name,
                "resource_id": resource_id,
                "source_url": source_url,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
        print(f"{action.title()}: {destination}")

    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Saved manifest: {manifest_path}")


if __name__ == "__main__":
    main()
