# GrantConnect methodology

## Purpose

The GrantConnect scripts prepare quarterly summary charts from publicly available Australian Government grant-award exports. They are designed to make the published records easier to explore without changing the underlying awards or treating APET calculations as official government statistics.

## Official source

- GrantConnect: <https://www.grants.gov.au/>

The official publisher remains the authoritative source. Source files are not committed to this repository; users should retrieve them from the official service and review the publisher's current terms and documentation.

## Expected local structure

```text
australian-public-expense-tracker/
├── branding/
│   └── APETLogo400x400.png       # optional
├── data/
│   └── grantconnect/             # local source workbooks; not committed
├── output/
│   └── grantconnect/             # generated charts and supporting files
└── scripts/
    ├── chart_helpers.py
    ├── generate_grantconnect_quarterly_charts.py
    └── reconcile_grantconnect_archive.py
```

Expected workbook names follow this pattern:

```text
grantconnect_FY2024-25_Q3_2025-01.xlsx
```

Split-month exports may add a suffix such as `a` or `b` before `.xlsx`.

## Processing and validation

The quarterly chart script:

1. Locates the GrantConnect table header in each workbook.
2. Checks that required columns are present.
3. Converts publish dates and reported values to consistent data types.
4. Removes rows with invalid publish dates and reports how many were removed.
5. Removes exact duplicate rows.
6. Stops if a Grant Award ID remains duplicated after exact deduplication.
7. Stops when a source file appears to have reached the 10,000-award export ceiling.
8. Assigns each record to an Australian financial year and quarter using its publish date.
9. Skips incomplete quarters by default.
10. Produces charts, chart-data CSV files and draft X post text.

The reconciliation script performs additional checks on archived workbooks, including date coverage, overlaps, duplicates and filename-to-quarter consistency.

## Outputs

For each complete quarter, the chart script produces summaries including:

- reported grant value by agency and category
- top recipients by reported value
- largest individual published awards
- award counts by agency and category
- top programs by reported value
- average award size by agency, limited to agencies with at least ten awards

The reported value is aggregated from the `Value (AUD)` field in the source export. Counts refer to published grant-award rows after validation and exact deduplication.

## Important limitations

- Publication date is used to assign financial quarters; it may differ from the award, commencement or payment date.
- Reported award value is not necessarily cash paid during the reporting period.
- A published record may later be corrected or updated by the official source.
- Rankings depend on the spelling and categorisation supplied in the source data, except for documented whitespace cleaning.
- APET outputs should always be interpreted alongside the official GrantConnect record and documentation.

## Running the scripts

Create a Python environment and install the dependencies:

```text
pip install -r requirements.txt
```

Place the source workbooks under `data/grantconnect`, then run:

```text
python scripts/generate_grantconnect_quarterly_charts.py
```

To point the reconciliation script at a non-standard downloads folder, set the `APET_DOWNLOAD_DIR` environment variable before running it.
