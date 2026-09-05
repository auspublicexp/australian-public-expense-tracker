# APET public hospital funding prototype

This small prototype tests official National Health Funding Body (NHFB) data
before any public APET pages or charts are created.

It uses two CSV resources from the official [Website Report (Production
dataset)](https://data.gov.au/data/dataset/c4afb0c6-624b-4f4e-865d-14af55c6a311):

- national funding and payments for each state, five-year trend;
- state payments by service category, five-year trend.

Despite the resource names, the current files contain a longer historical
series. The normalizer automatically includes every completed financial year
and excludes the financial year that is still in progress.

## Run the test

From this folder, run these three commands in order:

```powershell
python .\fetch_public_hospital_funding.py
python .\normalize_public_hospital_funding.py
python .\validate_public_hospital_funding.py
python .\generate_public_hospital_funding_charts.py --all-financial-years
```

The fetch step preserves the original CSVs and records their source URLs,
download time, size and SHA-256 checksum in
`data/public_hospital_funding/raw/manifest.json`.
It looks up the current download URLs from data.gov.au using stable resource
IDs, because the published filenames change between monthly releases.

The normalization step converts financial-year columns into consistent monthly
rows. It creates:

- `data/public_hospital_funding/normalized/monthly_payments_by_state.csv`
- `data/public_hospital_funding/normalized/monthly_payments_by_service_category.csv`

The validation step writes both human-readable and machine-readable reports to
`output/validation` using the filenames `public_hospital_funding_latest.txt`
and `public_hospital_funding_latest.json`.

## What the figures mean

NHFB says its monthly reports are prepared on a cash basis. They describe money
flowing into and out of the National Health Funding Pool and State Managed
Funds. They do **not** represent every cost incurred by every public hospital.

The state totals and service-category totals are intentionally kept separate.
The category resource omits some payment types, so its total should not be
presented as total Australian public-hospital expenditure.

Some individual service-category entries are negative. These are retained
rather than silently converted or removed because they can represent official
adjustments or reversals. The complete state-level monthly totals remain
non-negative, and the validation report counts the negative component rows.

Chart generation writes PNG, SVG and supporting CSV files to
`output/public_hospital_funding`. It also copies the website-ready SVG and CSV
files to `website/public_html/charts/public_hospital_funding`; PNG files remain
in the main output archive for social-media use.

The public presentation focuses on change rather than repeating almost
identical quarterly rankings. The generator creates four long-term overview
charts in the main chart folder and annual comparison folders containing:

- each state or territory's share of reported payments;
- the change in each state or territory from the previous financial year; and
- the largest changes in service-category payments from the previous year.

The normalized files still retain monthly records, so quarters and other custom
periods can be analysed later without downloading the source data again.
