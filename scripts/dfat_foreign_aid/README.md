# APET DFAT foreign-aid pipeline

This pipeline downloads the Department of Foreign Affairs and Trade (DFAT) Australia IATI Activity File from data.gov.au, preserves the raw XML, normalises its transactions and produces Australian financial-year charts.

## Run the pipeline

```powershell
python .\fetch_dfat_iati.py
python .\normalize_dfat_iati.py
python .\validate_dfat_foreign_aid.py
python .\generate_dfat_foreign_aid_charts.py
```

Use `--force` with the fetcher to replace the cached XML and IATI code lists. Default outputs, relative to the repository root:

- `data/dfat_foreign_aid/raw` — official XML, IATI code lists and download manifest
- `data/dfat_foreign_aid/normalized/dfat_aid_transactions.csv` — stable transaction-level schema
- `output/foreign_aid` — overview and annual financial-year charts
- `output/validation/dfat_foreign_aid_latest.{txt,json}` — latest validation report
- `website/public_html/charts/foreign_aid` — website-ready SVG and chart-data CSV copies, when the website tree is available

## Interpretation

The public charts use IATI transaction type 3, **disbursement**. They do not add type-2 commitments, budgets or whole-of-project investment values. Negative disbursements are retained because DFAT uses adjustments for matters such as returned prior-year funds and conversion between accrual expenses and ODA cash reporting.

The source currently reports one transaction date at the end of each Australian financial year, so this dataset supports annual charts rather than meaningful quarterly charts. Country charts include only transactions carrying a recipient-country code; regional and unspecified transactions remain in total and sector figures.

Official sources:

- https://data.gov.au/data/dataset/dfat-australia-iati-activity-file
- https://adp.dfat.gov.au/data-downloads
- https://iatistandard.org/en/iati-standard/203/codelists/transactiontype/
