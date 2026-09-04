# APET ARC grants pipeline

This pipeline uses the Australian Research Council's public National Competitive Grants Program Grants Search API.

## Run the pipeline

```powershell
python .\fetch_arc_grants.py --all
python .\normalize_arc_grants.py
python .\validate_arc_grants.py
python .\generate_arc_grants_charts.py
```

For a small API test, omit `--all`; the fetcher downloads two pages by default. A complete download is paginated in batches of up to 1,000 records and can resume from compatible cached pages. Use `--force --all` to refresh every raw page.

Default outputs, relative to the repository root:

- `data/arc_grants/raw` — unmodified API pages and download manifest
- `data/arc_grants/normalized/arc_grants_projects.csv` — one consistent row per project
- `output/arc_grants` — overview and calendar-year chart files
- `output/validation/arc_grants_latest.{txt,json}` — latest validation report

The chart generator also copies website-ready SVG and CSV files when a compatible APET website chart directory is available.

## Interpretation

Funding values are whole-of-project ARC allocations, not cash payments made during the commencement year. `announced_funding_dollars` records the amount at announcement; `current_funding_dollars` can include post-award variations.

The source groups projects by calendar funding commencement year. The current incomplete year is excluded from charts by default; use `--include-current-year` only for explicitly provisional output.

ARC grants may also appear in GrantConnect, so ARC and GrantConnect totals must not be added together.

Official source: https://www.arc.gov.au/funding-research/funding-outcomes/grants-dataset

