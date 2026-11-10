# GrantConnect methodology and maintenance

Reviewed against the repository scripts on 10 November 2026. This document describes current code behaviour; it is not evidence of a fresh successful data run.

## Purpose and official source

APET prepares annual and quarterly charts from [GrantConnect grant-award exports](https://www.grants.gov.au/). Awards are assigned by **Publish Date** to Australian financial years (July–June) and financial-year quarters, not calendar publication years or payment periods. Reported award values are not necessarily cash paid during the period. The official publisher remains authoritative.

The chart generators remain the chart-processing workflow. Website PHP pages display their generated PNG/SVG/CSV assets; they do not run Python on each visit. A separate search-index builder produces JSON for the award search and supplements rather than replaces the charts.

## Files and dependencies

- [Annual generator](../scripts/grantconnect/generate_grantconnect_annual_charts.py)
- [Quarterly generator](../scripts/grantconnect/generate_grantconnect_quarterly_charts.py)
- [Shared chart helpers](../scripts/chart_helpers.py)
- [Search-index builder](../scripts/grantconnect/build_grantconnect_search_index.py)
- [Archive reconciliation utility](../scripts/grantconnect/reconcile_grantconnect_archive.py) — known limitations below
- [Python requirements](../requirements.txt)

Expected paths relative to the project root:

| Path | Purpose |
| --- | --- |
| `data/grantconnect/` | Original Excel exports; not committed |
| `branding/APETLogo400x400.png` | Optional chart logo |
| `output/grantconnect/FY2025-26_annual/` | Example annual chart outputs |
| `output/grantconnect/FY2026-27_Q1/` | Example quarterly chart outputs |
| `website/public_html/charts/grantconnect/` | Website chart assets; see destination warning below |
| `website/public_html/grantconnect/search-data/` | Search manifest and quarterly JSON files |
| `output/validation/` | Latest search-build validation reports |

Source workbooks and generated assets are maintained outside Git. Preserve the source exports, export criteria and retrieval dates separately; a code checkout alone does not reproduce a particular historical snapshot.

## Preparing source exports

Export awards using **Date Type: Publish Date** and retain the workbook's criteria rows and table header. Use date ranges that cover the intended period without gaps. For large ranges, download smaller date slices and name each file consistently, for example:

```text
grantconnect_FY2024-25_Q3_2025-01.xlsx
grantconnect_FY2024-25_Q3_2025-02a.xlsx
grantconnect_FY2024-25_Q3_2025-02b.xlsx
grantconnect_FY2024-25_Q3_2025-02c.xlsx
```

Both chart generators read **all** files matching `grantconnect_FY????-??_Q?_????-??*.xlsx` directly under `data/grantconnect`, not just the newest file. Date-range filenames with the same prefix also match. Subfolders such as `archive_incomplete` are excluded. A name such as `Q3_A.xlsx` does not match.

The suffix allows multiple exports for the same month; it does not itself establish completeness. Keep each export below the approximately 10,000-record ceiling. The chart loaders stop at **10,000 or more unique GA IDs per file** and require smaller exports. This is a safeguard, not proof that every sub-cap export is complete. Archive superseded exports outside the active input folder after preserving them; do not mix old and refreshed versions indiscriminately.

Required columns are `GA ID`, `Grant Activity`, `Agency`, `Category`, `Recipient Name`, `GO ID`, `Publish Date` and `Value (AUD)`. The loaders search the first 40 rows for the header.

## Processing and completeness checks

Both chart generators:

1. Read all matching exports and check required columns.
2. Parse publication dates and monetary values; remove invalid-date rows with a warning.
3. Clean whitespace in the main text fields and replace missing text with `Not specified`.
4. Convert missing or non-numeric monetary values to zero.
5. Remove exact duplicate rows across the combined data.
6. Stop if a GA ID still appears more than once, requiring manual review of overlaps or changed copies.
7. Assign periods from each award's publication date and aggregate the chart data.

Different version-suffixed GA IDs are not automatically consolidated into a single base award. The pipeline does not choose the latest amendment when conflicting records remain.

**Quarterly:** with `COMPLETE_QUARTERS_ONLY = True`, the generator requires a closed quarter and gap-free coverage of every day using the workbook's `Date Type` and `Date Range` criteria. A selected `TARGET_FY_QUARTER` still receives this check. Observed award dates alone do not establish coverage. Criteria coverage does not independently prove that the export contains every source award or that no other search filters excluded records.

**Annual:** with the default `TARGET_FINANCIAL_YEAR = None` and `COMPLETE_YEARS_ONLY = True`, the generator requires observed awards in all 12 calendar months of the financial year. It does **not** apply the quarterly export-range coverage check or a separate year-closure check. Setting a specific `TARGET_FINANCIAL_YEAR` bypasses the 12-month filter. Before publishing an annual result, independently establish complete export coverage for all four closed quarters.

## Eight chart definitions

Both generators define the following charts for each selected period:

| Number | Summary | Selection |
| --- | --- | --- |
| 01 | Reported award value administered by agency | Top 10 by summed value |
| 02 | Reported award value by category | Top 10 by summed value |
| 03 | Recipients by reported award value | Top 10 by summed value |
| 04 | Largest individual award records | Top 5 by value |
| 05 | Number of awards administered by agency | Top 10 by count |
| 06 | Number of awards by category | Top 10 by count |
| 07 | Grant activity groups by reported value | Top 10 exact GO ID + Grant Activity combinations |
| 08 | Average reported award value by agency | Top 10 means, restricted to agencies with at least 10 records |

Activity groups are not necessarily whole programs. Agency labels describe administration, not payments received by the agency. Counts represent retained award records, not necessarily the number of underlying grants represented by an aggregate award record.

Each non-empty chart produces PNG, SVG and a matching `*_data.csv`. CSV files contain the selected chart data, not a complete period export. Empty selections are skipped, so eight files per format are not guaranteed for every dataset.

**X captions are not currently generated.** Although `chart_helpers.py` contains `save_x_post`, neither current GrantConnect generator calls it. Any manually prepared caption should identify the publication period, say “reported award value” rather than “payments” or “savings”, and link to the source or chart. Automated neutral captions remain an unimplemented requirement.

## Regeneration procedure

Run commands from the project root in a Python environment with the repository dependencies:

```text
python -m pip install -r requirements.txt
```

Before running either generator, review its settings and destinations:

- `TARGET_FY_QUARTER = None` selects all eligible quarters; `TARGET_FINANCIAL_YEAR = None` selects years using the annual filter described above.
- Both generators currently hard-code `GRANTCONNECT_WEBSITE_CHART_DIR` to `C:\dev\australian-public-expense-tracker\website\public_html\charts\grantconnect` and automatically copy PNG/SVG/CSV files there.
- There is no implemented `APET_GRANTCONNECT_WEBSITE_CHART_DIR` environment override or disabled-by-default mirror mode. On another machine or for an isolated trial, adjust that constant in both working copies to an intended staging directory before executing them.
- Both generators invoke the search builder at the end when it exists. Search output is configured separately, so redirect it too for an isolated run. A failed search build can occur after chart files have already been written.

After checking source coverage and destinations, run:

```text
python scripts/grantconnect/generate_grantconnect_quarterly_charts.py
python scripts/grantconnect/generate_grantconnect_annual_charts.py
```

The search builder supports `--data-dir` and `--website-dir`; the latter is the GrantConnect website directory, under which it creates `search-data`. Its environment equivalents are `APET_GRANTCONNECT_DATA_DIR` and `APET_GRANTCONNECT_SEARCH_DIR`. These settings affect the search builder only, not the chart loaders or chart-mirroring destination.

For an independent search rebuild:

```text
python scripts/grantconnect/build_grantconnect_search_index.py --data-dir data/grantconnect --website-dir website/public_html/grantconnect
```

The search build replaces quarterly JSON files in its target search-data directory and writes `manifest.json`. It excludes rows missing an ID, valid date or numeric value, removes exact duplicates and stops on remaining repeated IDs. Unlike the chart generators, it does not check the export ceiling or date-range coverage. Its annual manifest entries require all four quarter labels, not verified complete quarters. Consequently, search and chart counts can differ when invalid values or incomplete periods are present.

## Verification and publication

After regeneration:

1. Review all warnings, skipped periods, input-file counts, retained counts and duplicate errors. Investigate invalid values and dates against the original exports.
2. Confirm export-date coverage independently for annual results and search periods. Compare totals and counts against the complete retained source data; top-10 chart bars are not whole-period totals.
3. Check each expected chart, its CSV and its PNG/SVG pair. Verify the five-award selection and the minimum-ten-record agency filter against source data, and visually inspect labels and footers.
4. Read `output/validation/grantconnect_latest.txt` and `grantconnect_latest.json`. These are reports from the search builder, not a certification of chart correctness or complete export coverage; subsequent successful runs overwrite them.
5. Preview the website annual, quarterly and search pages and test downloads. Review existing assets for periods now skipped by a generator; skipping does not remove an older published chart.
6. Transfer the verified chart folders and search-data files through the maintained website deployment process. Include PNG, SVG, CSV and JSON files and preserve period folder names. The documented local deployment route is APET tree → Google Drive → the usual WinSCP sync; confirm the actual destination and then check the public pages. Running Python or committing documentation does not deploy the website.

See [chart download documentation](chart-downloads.md) for the shared download integration.

## Known maintenance issues

The following remain unresolved code issues, not completed fixes:

- Annual completeness is weaker than quarterly completeness, and explicit annual selection bypasses its month-presence filter.
- Chart and search loaders differ in invalid-value and missing-ID handling, and search lacks export-ceiling/coverage checks.
- Chart mirroring uses a hard-coded machine path. Generation and search replacement are not an atomic publication process.
- Automated X caption generation is absent.
- `reconcile_grantconnect_archive.py` currently uses `Path(__file__).resolve().parents[1]`, which resolves to `scripts`, so its default data path is incorrectly `scripts/data/grantconnect`. Its expected coverage is also fixed to 1 January 2020–31 August 2026. Correct the project root and intended coverage window before relying on it for a current audit. `APET_DOWNLOAD_DIR` only controls its raw-download inventory, not the data-directory bug. The utility reports findings; its printed error list is not an enforced validation gate.

Source records can be revised after publication. Recipient spellings and categorisation affect rankings. Preserve original snapshots and review significant findings against the official record.

This maintenance guide records the implementation and known gaps without requiring a development conversation. Actual-data regeneration, total reconciliation and visual/download checks are still needed to validate a particular release; documentation review alone does not provide that assurance.
