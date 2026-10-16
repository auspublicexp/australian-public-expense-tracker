# NDIS financial-year pages

Run from the repository root:

    python scripts/ndis/build_ndis.py --raw data/ndis/raw --out website/public_html/ndis

This standard-library build generates all three reviewed annual snapshots, year navigation, CSV/JSON downloads and validation records. It writes files in place; use a staging output directory for review before publishing.

| Financial year | June snapshot | Payments CSV media ID | National report media ID | Comparison tables |
|---|---|---|---|---|
| 2023-24 | June 2024 | 4480 | 4029 | E.116 and E.117 |
| 2024-25 | June 2025 | 4476 | 4359 | E.111 and E.112 |
| 2025-26 | June 2026 | 4577 | 4560 | E.109 and E.110 |

Official download URL pattern: `https://dataresearch.ndis.gov.au/media/ID/download?attachment`.
Downloads verified 16 October 2026. The live payments page currently lists June 2025 and June 2026; the indexed official listing also linked June 2024, whose original CSV remains downloadable. No earlier comparable CSV was located. These pages cover 1 July 2023 to 30 June 2026. Do not imply that this is the start of the NDIS or the earliest government reporting.

Raw CSVs are named `payments_YYYY-06.csv`; report workbooks `national_YYYY-YY_Q4.xlsx`. Retain source files separately from generated website files. The XLSX reader supports transitional and strict OOXML and reads stored values without executing formulas. Report totals are taken from column B, the preceding-year payments, not committed supports or service-year payments. Underlying workbook values are dollars, even where the display is millions.

The national dataset totals are $41,254,223,000; $45,853,407,000; and $51,451,547,000 respectively. Their differences from the matching report table pairs are $17,673,921.72; $9,314,661.10; and $5,611,821.40. Reasons are not established; each page discloses its comparison without forcing a match. Category sums differ from class sums by $1,000, $2,000 and $2,000 respectively.

National amounts sum the four published class aggregates once. The eight named states/territories use one row per class. OT has suppression. Missing location has repeated keys and suppression; its total is not inferred. Participant counts overlap and are not summed. June 2024 has four suppressed class-0 detail rows but no class-0 national aggregate; those rows are not added to the national class totals. June 2026 has a negative $3,000 Missing class entry preserved as published.

Successive quarterly snapshots cover overlapping 12-month periods: never sum them as separate quarters. For new annual releases, add a reviewed June snapshot, verify source structure and relevant report tables, extend the year configuration and date template logic, then validate before syncing. Older years are original snapshots; no inflation adjustment or revision harmonisation is applied.

The main build compares all three report workbooks directly. Retain downloaded source files and the publisher's rules document separately from generated output.

## Setup and charts

Install the repository requirements with `python -m pip install -r requirements.txt`. The annual build uses Python's standard library; the chart build requires matplotlib. Download the six official files identified in the table above into `data/ndis/raw`, using the CSV and XLSX filenames described above. Downloads are manual; this package does not automatically fetch new releases.

Run from the repository root:

```sh
python scripts/ndis/build_ndis.py --raw data/ndis/raw --out website/public_html/ndis
python scripts/ndis/build_charts.py --out website/public_html/ndis
```

Copy `scripts/ndis/charts-template.php` to `website/public_html/ndis/charts.php` after generation. The annual builder reads `page-template.php` beside the script. It generates the three annual PHP pages; the chart builder generates 15 SVG/PNG/CSV sets and `charts/manifest.json`. Chart selectors accept only fixed year and comparison choices.

The PHP pages are APET integration templates. Rendering them requires the existing website's shared header, footer, styles and images; these website assets are not distributed in this scripts repository. JSON, CSV and chart generation can run without a PHP server. The generated annual pages link to `charts.php`, so install that template with the chart assets. Preserve the existing site's navigation and add the annual/chart URLs to its sitemap during deployment.

Before publishing, check the three annual validation JSON files and the chart manifest. Verify periods, eight available jurisdictions, unavailable location groups, source checksums and disclosed report differences. Inspect the rendered pages and chart labels. Do not publish partial output after an assertion failure. Generated outputs and downloaded sources remain outside version control.

See [NDIS methodology](../../docs/ndis-methodology.md) and the [live chart explorer](https://auspublicexp.org/ndis/charts.php).
