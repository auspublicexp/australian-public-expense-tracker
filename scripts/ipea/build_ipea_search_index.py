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
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from validation_report import write_validation_report


PROJECT_DIR = Path(__file__).parents[2]
CHART_ROOT = Path(os.getenv(
    "APET_IPEA_CHART_ROOT",
    PROJECT_DIR / "website" / "public_html" / "charts" / "ipea",
))
DATA_ROOT = Path(os.getenv("APET_IPEA_DATA_ROOT", PROJECT_DIR / "data" / "ipea"))
INDEX_PATH = Path(os.getenv(
    "APET_IPEA_SEARCH_INDEX",
    PROJECT_DIR / "website" / "public_html" / "ipea" / "ipea-search-index.json",
))


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


def expense_category(csv_path: Path) -> str:
    stem = re.sub(r"_data$", "", csv_path.stem)
    if re.match(r"^0?4_", stem):
        return "All reported expenses"
    if re.match(r"^0?[5-9]_", stem):
        return "Travel"
    if re.match(r"^1[0-3]_", stem):
        return "Office expenses"
    return "Other"


def first_present(fieldnames: list[str], candidates: list[str]) -> str | None:
    lookup = {field.strip().lower(): field for field in fieldnames}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def normalise_name(value: str) -> str:
    return " ".join(value.casefold().split())


def canonical_party(value: str) -> str:
    cleaned = " ".join(value.split())
    aliases = {
        "alp": "Australian Labor Party",
        "australian labor party (alp)": "Australian Labor Party",
        "australian labor party": "Australian Labor Party",
        "australian greens party": "Australian Greens",
        "liberal party": "Liberal Party of Australia",
        "the nationals": "National Party of Australia",
        "one nation australia": "One Nation",
    }
    return aliases.get(cleaned.casefold(), cleaned)


def canonical_state(value: str) -> str:
    cleaned = " ".join(value.upper().split())
    return cleaned if cleaned in {"ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"} else ""


def load_person_metadata() -> dict[tuple[str, str], dict[str, set[str]]]:
    metadata: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(
        lambda: {"parties": set(), "states": set()}
    )
    if not DATA_ROOT.is_dir():
        return metadata

    for source_path in sorted(DATA_ROOT.glob("*q*_dataextract.csv")):
        info = period_info(source_path.stem)
        if info is None or info["type"] != "Quarterly":
            continue
        with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            name_field = first_present(fieldnames, ["FullNameWithTitle", "Name"])
            party_field = first_present(fieldnames, ["Party"])
            state_field = first_present(fieldnames, ["StateOrTerritory"])
            if name_field is None:
                continue
            for row in reader:
                name_key = normalise_name((row.get(name_field) or "").strip())
                if not name_key:
                    continue
                quarter_key = str(info["key"])
                keys = [quarter_key]
                match = re.fullmatch(r"quarter-(\d{4})-[1-4]", quarter_key)
                if match:
                    keys.append(f"annual-{match.group(1)}")
                for period_key in keys:
                    item = metadata[(period_key, name_key)]
                    party = canonical_party(row.get(party_field) or "") if party_field else ""
                    state = canonical_state(row.get(state_field) or "") if state_field else ""
                    if party:
                        item["parties"].add(party)
                    if state:
                        item["states"].add(state)
    return metadata


def build_index() -> dict[str, object]:
    if not CHART_ROOT.is_dir():
        raise FileNotFoundError(f"IPEA chart folder not found: {CHART_ROOT}")

    appearances: list[dict[str, object]] = []
    periods: dict[str, dict[str, str]] = {}
    person_metadata = load_person_metadata()
    parties: set[str] = set()
    states: set[str] = set()
    categories: set[str] = set()
    chart_types: set[str] = set()

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
                chart_name = chart_title(csv_path)
                category = expense_category(csv_path)
                chart_types.add(chart_name)
                categories.add(category)

                for row in reader:
                    name = (row.get(name_field) or "").strip()
                    normalised_name = normalise_name(name)
                    if not normalised_name or normalised_name in seen_names:
                        continue
                    seen_names.add(normalised_name)

                    amount_text = (row.get(amount_field) or "").strip() if amount_field else ""
                    try:
                        amount = round(float(amount_text), 2) if amount_text else None
                    except ValueError:
                        amount = None

                    metadata = person_metadata.get(
                        (str(info["key"]), normalised_name),
                        {"parties": set(), "states": set()},
                    )
                    row_party = canonical_party(row.get(party_field) or "") if party_field else ""
                    party_values = set(metadata["parties"])
                    if row_party:
                        party_values.add(row_party)
                    party = " / ".join(sorted(party_values))
                    state = " / ".join(sorted(metadata["states"]))
                    parties.update(party_values)
                    states.update(metadata["states"])

                    appearances.append(
                        {
                            "name": name,
                            "party": party,
                            "state": state,
                            "period_key": info["key"],
                            "period": info["label"],
                            "period_type": info["type"],
                            "period_sort": info["sort"],
                            "chart": chart_name,
                            "chart_type": chart_name,
                            "expense_category": category,
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
        "parties": sorted(parties),
        "states": sorted(states),
        "expense_categories": sorted(categories),
        "chart_types": sorted(chart_types),
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
    appearances = index["appearances"]
    write_validation_report(
        "ipea",
        {
            "chart_appearances": index["appearance_count"],
            "reporting_periods": len(index["periods"]),
            "parties_indexed": len(index["parties"]),
            "states_and_territories_indexed": len(index["states"]),
            "expense_categories_indexed": len(index["expense_categories"]),
            "chart_types_indexed": len(index["chart_types"]),
            "appearances_with_reported_amount": sum(
                1 for item in appearances if item.get("amount") is not None
            ),
            "search_index": INDEX_PATH,
        },
        checks=[
            "Only names appearing in published IPEA chart data were indexed.",
            "Each indexed appearance has a reporting period and direct chart link.",
            "Party, state, category and chart-type filter lists were rebuilt.",
        ],
    )


if __name__ == "__main__":
    main()
