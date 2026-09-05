"""Normalize DFAT IATI transactions into a stable APET CSV schema."""
from __future__ import annotations

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path

FIELDS = [
    "activity_id", "activity_title", "activity_description", "activity_status_code",
    "activity_start_date", "activity_end_date", "implementing_organisation",
    "transaction_type_code", "transaction_type", "transaction_date", "financial_year",
    "value_dollars", "currency", "recipient_country_code", "recipient_country",
    "recipient_region_code", "recipient_region", "sector_code", "sector",
    "sector_category_code", "sector_category", "source_dataset_url",
]
SOURCE_URL = "https://data.gov.au/data/dataset/dfat-australia-iati-activity-file"


def narrative(parent) -> str:
    item = parent.find("narrative") if parent is not None else None
    return " ".join("".join(item.itertext()).split()) if item is not None else ""


def codelist(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(item["code"]): str(item["name"]) for item in payload.get("data", [])}


def financial_year(date_text: str) -> str:
    year, month = (int(value) for value in date_text[:7].split("-"))
    start = year if month >= 7 else year - 1
    return f"FY{start}-{str(start + 1)[-2:]}"


def date_by_type(activity, type_code: str) -> str:
    for item in activity.findall("activity-date"):
        if item.get("type") == type_code:
            return item.get("iso-date", "")[:10]
    return ""


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parents[1] if script_dir.parent.name == "scripts" else script_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=project_root / "data/dfat_foreign_aid/raw")
    parser.add_argument("--output-dir", type=Path, default=project_root / "data/dfat_foreign_aid/normalized")
    args = parser.parse_args()

    countries = codelist(args.input_dir / "iati_country_codelist.json")
    regions = codelist(args.input_dir / "iati_region_codelist.json")
    sectors = codelist(args.input_dir / "iati_sector_codelist.json")
    sector_categories = codelist(args.input_dir / "iati_sector_category_codelist.json")
    transaction_types = codelist(args.input_dir / "iati_transaction_type_codelist.json")
    source = args.input_dir / "dfat_australia_iati_activity.xml"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.output_dir / "dfat_aid_transactions.csv"

    count = 0
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for event, activity in ET.iterparse(source, events=("end",)):
            if activity.tag != "iati-activity":
                continue
            activity_id = (activity.findtext("iati-identifier") or "").strip()
            title = narrative(activity.find("title"))
            description = narrative(activity.find("description"))
            status = activity.find("activity-status")
            implementers = [
                narrative(org) for org in activity.findall("participating-org")
                if org.get("role") == "4" and narrative(org)
            ]
            for transaction in activity.findall("transaction"):
                type_element = transaction.find("transaction-type")
                value_element = transaction.find("value")
                date_element = transaction.find("transaction-date")
                if type_element is None or value_element is None or date_element is None:
                    continue
                date_text = date_element.get("iso-date", "")[:10]
                country = transaction.find("recipient-country")
                region = transaction.find("recipient-region")
                sector = transaction.find("sector")
                country_code = country.get("code", "") if country is not None else ""
                region_code = region.get("code", "") if region is not None else ""
                sector_code = sector.get("code", "") if sector is not None else ""
                category_code = sector_code[:3] if len(sector_code) >= 3 else ""
                type_code = type_element.get("code", "")
                writer.writerow({
                    "activity_id": activity_id,
                    "activity_title": title,
                    "activity_description": description,
                    "activity_status_code": status.get("code", "") if status is not None else "",
                    "activity_start_date": date_by_type(activity, "2") or date_by_type(activity, "1"),
                    "activity_end_date": date_by_type(activity, "4") or date_by_type(activity, "3"),
                    "implementing_organisation": " | ".join(dict.fromkeys(implementers)),
                    "transaction_type_code": type_code,
                    "transaction_type": transaction_types.get(type_code, "Unknown"),
                    "transaction_date": date_text,
                    "financial_year": financial_year(date_text),
                    "value_dollars": value_element.text or "0",
                    "currency": value_element.get("currency") or activity.get("default-currency", ""),
                    "recipient_country_code": country_code,
                    "recipient_country": countries.get(country_code, ""),
                    "recipient_region_code": region_code,
                    "recipient_region": regions.get(region_code, ""),
                    "sector_code": sector_code,
                    "sector": sectors.get(sector_code, ""),
                    "sector_category_code": category_code,
                    "sector_category": sector_categories.get(category_code, ""),
                    "source_dataset_url": SOURCE_URL,
                })
                count += 1
            activity.clear()
    if not count:
        raise ValueError("The DFAT IATI archive contained no usable transactions")
    print(f"Saved {count:,} normalized DFAT aid transactions: {destination}")


if __name__ == "__main__":
    main()
