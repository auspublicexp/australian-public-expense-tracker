# ABS Government Finance Statistics for APET

This isolated folder does not change the existing AusTender, GrantConnect or
IPEA scripts. Because GFS is not currently in the ABS Data API catalogue,
`fetch_abs_gfs.py` downloads the official XLSX files linked from the annual
release.

Run from the APET project root:

```powershell
python scripts/abs_gfs/fetch_abs_gfs.py
python scripts/abs_gfs/normalize_abs_gfs.py
python scripts/abs_gfs/generate_abs_gfs_charts.py
```

The scripts create three normalized CSV files, landing-page trend charts, and
one chart folder for every available Australian financial year.
Values stay in AUD millions until the chart layer converts them to billions.
Labels state that the figures are current-price, original-series and accrual
data. Level-of-government figures remain separate because transfers mean they
must not be added to reproduce the consolidated All Australia total.

Charts use the shared `scripts/chart_helpers.py` logo function and expect the
standard APET logo at `branding/APETLogo400x400.png`.

## APET period convention

Annual GFS records and output folders use labels such as `FY2024-25`, covering
1 July 2024 to 30 June 2025. The normalized CSVs include explicit period start
and end dates as well as the website-friendly slug `fy2024_25`.

Annual figures are not divided into estimated quarters. The separate official
quarterly GFS workflow uses the existing Australian financial-year mapping:

- Q1: July to September
- Q2: October to December
- Q3: January to March
- Q4: April to June

## Main output and optional mirroring

By default, charts are written to `output/abs_gfs`. This includes PNG images
for sharing on X, SVG images for the website, and the supporting CSV files.

If a workflow uses a temporary `--output-root`, set `APET_ABS_GFS_OUTPUT_DIR`
to the project's main `output/abs_gfs` directory. The generator will then keep
a complete copy there, including the financial-year subfolders.

```powershell
$env:APET_ABS_GFS_OUTPUT_DIR = "C:\dev\australian-public-expense-tracker\output\abs_gfs"
```

### Website copy

The generator automatically copies SVG and supporting CSV files to
`website/public_html/charts/abs_gfs`, including the matching financial-year
subfolders. PNG files remain in the main `output/abs_gfs` collection for use
on social media.

`APET_ABS_GFS_WEBSITE_CHART_DIR` can still be set when testing against a
different website copy, but it is not required for a normal APET run.

Source: https://www.abs.gov.au/statistics/economy/government/government-finance-statistics-annual/latest-release

## FY2025–26 results derived from quarterly GFS

The June 2026 workbook is a different publication from the annual workbooks.
Use the separate parser; do not feed it to `normalize_abs_gfs.py` or append its
results to the annual CSVs. The annual tables and explorer remain unchanged.

```powershell
python scripts/abs_gfs/fetch_quarterly_gfs.py
python scripts/abs_gfs/quarterly_gfs.py
python scripts/abs_gfs/test_quarterly_gfs.py
```

The downloader archives the pinned June 2026 workbook and ABS insights article
under `data/abs_gfs/raw/quarterly/jun-2026`, with URLs, retrieval times and SHA256
hashes. It never overwrites cached sources. To check a later revision, pass a
new `--output-dir` and compare it before rebuilding with `--raw-dir`.
The parser deliberately rejects other release periods; a later release needs
review of its schema, validation targets and labels before reuse.

The builder sums all four FY2025–26 quarters from Table 1 of the June release.
It uses Table 15 from the same release for both years of the taxation-growth
comparison, and cross-checks overlapping Table 1/15 totals. It rejects missing
quarters, wrong units/sector, non-numeric values, duplicates and reconciliation
failures. Official one-decimal billion-dollar figures are checked at their
published precision; rounded million-dollar cells remain unchanged.

Personal income tax, company income tax and GST are extracted from the accessible
ABS article table. They are labelled as ABS-published totals, not independent
quarterly reconstructions. The workbook does not contain those tax components.

Output is `output/abs_gfs/FY2025-26_quarterly_derived`: PNG/SVG charts, supporting
CSVs, `summary.json` with validation/provenance, and `summary.html`. Validation
also goes to `output/validation/abs_gfs_quarterly_latest.*`. No website copying,
cloud mirroring or deployment runs from the new builder. After review/approval,
the SVG/CSV/JSON/HTML assets belong in the matching website chart folder. The
review website wrapper uses the existing shared header/footer and Bootstrap
classes. PNG files remain in the output collection for social use.

This folder deliberately does not match `FY*_annual`: the existing annual topic
explorer requires purpose and separate government-level tables, which this
quarterly source cannot supply. Never estimate those breakdowns or silently
join annual and quarterly-derived values into one time series.
