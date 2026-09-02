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

Annual figures are not divided into estimated quarters. If official quarterly
GFS is added later, APET will use its existing Australian financial-year mapping:

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
