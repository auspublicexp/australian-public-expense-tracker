"""Build the public IPEA chart-appearance search index.

The index is created from the supporting CSV files beside APET's published
charts. It therefore describes names that actually appear in charts, rather
than every row in the original IPEA extracts.
"""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).parents[2]
CHART_ROOT = Path(
    os.getenv("APET_IPEA_CHART_ROOT", str(PROJECT_DIR / "output" / "ipea"))
)
INDEX_PATH = Path(
    os.getenv(
        "APET_IPEA_SEARCH_INDEX_PATH",
        str(PROJECT_DIR / "output" / "ipea" / "ipea-search-index.json"),
    )
)


def quarter_from_calendar(year: int, quarter: int) -> tuple[int, int, int]:
    mapping = {
        1: (year - 1, year, 3),
        2: (year - 1, year, 4),
        3: (year, year + 1, 1),
        4: (year, year + 1, 2),
    }
    return mapping[quarter]


def period_info(folder_name: str) -> dict[str, object] | None:
    annual = re.fullmatch(r"FY(\d{4})-(\d{2})_annual", folder_name, re.I)
    if annual:
        start = int(annual.group(1))
        label = f"FY{start}-{str(start + 1)[-2:]} annual"
        return {
            "key": f"annual-{start}",
            "label": label,
            "type": "Annual",
            "sort": f"{start:04d}5",
            "page": f"/ipea/annual.php?period={folder_name}",
            "legacy": False,
        }

    financial = re.fullmatch(r"FY(\d{4})-(\d{2})_Q([1-4])", folder_name, re.I)
    if financial:
        start = int(financial.group(1))
        quarter = int(financial.group(3))
        return {
            "key": f"quarter-{start}-{quarter}",
            "label": f"FY{start}-{str(start + 1)[-2:]} Q{quarter}",
            "type": "Quarterly",
            "sort": f"{start:04d}{quarter}",
            "page": f"/ipea/quarter.php?period={folder_name}",
            "legacy": False,
        }

    calendar = re.fullmatch(r"(\d{4})q0?([1-4])_dataextract", folder_name, re.I)
    if calendar:
        year = int(calendar.group(1))
        source_quarter = int(calendar.group(2))
        start, end, quarter = quarter_from_calendar(year, source_quarter)
        return {
            "key": f"quarter-{start}-{quarter}",
            "label": f"FY{start}-{str(end)[-2:]} Q{quarter}",
            "type": "Quarterly",
            "sort": f"{start:04d}{quarter}",
            "page": f"/ipea/quarter.php?period={folder_name}",
            "legacy": True,
        }

    return None


def choose_period_folders() -> list[tuple[Path, dict[str, object]]]:
    chosen: dict[str, tuple[Path, dict[str, object]]] = {}
    for folder in sorted(path for path in CHART_ROOT.iterdir() if path.is_dir()):
        info = period_info(folder.name)
        if info is None:
            continue
        existing = chosen.get(str(info["key"]))
        if existing is None or (existing[1]["legacy"] and not info["legacy"]):
            chosen[str(info["key"])] = (folder, info)
    return sorted(chosen.values(), key=lambda item: str(item[1]["sort"]), reverse=True)


def chart_title(csv_path: Path) -> str:
    title = re.sub(r"^\d+_", "", csv_path.stem)
    title = re.sub(r"_data$", "", title)
    title = title.replace("annual_", "").replace("_", " ").title()
    return title.replace("Comcar", "COMCAR")


def chart_anchor(csv_path: Path) -> str:
    svg_stem = re.sub(r"_data$", "", csv_path.stem)
    slug = re.sub(r"[^a-z0-9]+", "-", svg_stem.lower()).strip("-")
    return f"chart-{slug}"


def first_present(fieldnames: list[str], candidates: list[str]) -> str | None:
    lookup = {field.strip().lower(): field for field in fieldnames}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def build_index() -> dict[str, object]:
    if not CHART_ROOT.is_dir():
        raise FileNotFoundError(f"IPEA chart folder not found: {CHART_ROOT}")

    appearances: list[dict[str, object]] = []
    periods: dict[str, dict[str, str]] = {}

    for folder, info in choose_period_folders():
        periods[str(info["key"])] = {
            "key": str(info["key"]),
            "label": str(info["label"]),
            "type": str(info["type"]),
            "sort": str(info["sort"]),
        }

        for csv_path in sorted(folder.glob("*_data.csv")):
            svg_path = csv_path.with_name(re.sub(r"_data\.csv$", ".svg", csv_path.name))
            if not svg_path.is_file():
                continue

            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = reader.fieldnames or []
                name_field = first_present(
                    fieldnames,
                    ["Name", "FullNameWithTitle", "Full Name With Title", "DisplayName"],
                )
                if name_field is None:
                    continue

                party_field = first_present(fieldnames, ["Party"])
                amount_field = first_present(
                    fieldnames, ["Amount", "Amount_Current", "Increase", "Value"]
                )
                seen_names: set[str] = set()

                for row in reader:
                    name = (row.get(name_field) or "").strip()
                    normalised_name = " ".join(name.casefold().split())
                    if not normalised_name or normalised_name in seen_names:
                        continue
                    seen_names.add(normalised_name)

                    amount_text = (row.get(amount_field) or "").strip() if amount_field else ""
                    try:
                        amount = round(float(amount_text), 2) if amount_text else None
                    except ValueError:
                        amount = None

                    appearances.append(
                        {
                            "name": name,
                            "party": (row.get(party_field) or "").strip() if party_field else "",
                            "period_key": info["key"],
                            "period": info["label"],
                            "period_type": info["type"],
                            "period_sort": info["sort"],
                            "chart": chart_title(csv_path),
                            "amount": amount,
                            "url": f"{info['page']}#{chart_anchor(csv_path)}",
                        }
                    )

    appearances.sort(
        key=lambda item: (
            str(item["name"]).casefold(),
            str(item["period_sort"]),
            str(item["chart"]),
        ),
        reverse=True,
    )
    period_list = sorted(periods.values(), key=lambda item: item["sort"], reverse=True)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "description": "Names appearing in published APET IPEA charts.",
        "appearance_count": len(appearances),
        "periods": period_list,
        "appearances": appearances,
    }


def main() -> None:
    index = build_index()
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Saved {index['appearance_count']:,} chart appearances to {INDEX_PATH}")


if __name__ == "__main__":
    main()
