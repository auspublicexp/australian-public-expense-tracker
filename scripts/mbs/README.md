# Medicare Benefits Schedule expenditure

This pipeline uses the Australian Government Department of Health, Disability
and Ageing's official quarterly Medicare statistics workbook. It reports
Medicare benefits paid and services processed from FY2009-10 onward.

Run the scripts in this order:

```powershell
python fetch_mbs_statistics.py
python normalize_mbs_statistics.py
python validate_mbs_statistics.py
python generate_mbs_charts.py
python build_mbs_explorer.py
```

The full chart archive (PNG, SVG and supporting CSV files) is written to
`output/mbs/`. Website-ready SVG and CSV files are also copied to
`website/public_html/charts/mbs/`.

The explorer builder creates `mbs-explorer.json` for the website's service,
location, period and metric filters.

The charts use Australian financial years and financial quarters. Annual charts
are produced only for financial years containing all four quarters.

## Interpretation

The `Benefits ($)` field is used as the expenditure measure. It records MBS
benefits for claims processed by Medicare. It is not total Australian health
expenditure, and it excludes services provided by hospital doctors to public
patients in public hospitals. State or territory is based on the patient's
address. Consult the official Medicare explanatory notes before interpreting
the figures.

Sources:

- https://www.health.gov.au/resources/collections/medicare-statistics-collection
- https://www.health.gov.au/resources/publications/explanatory-notes-for-medicare-statistics
