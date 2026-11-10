# AusTender procurement methodology

## Purpose

The AusTender scripts combine publicly available Australian Government contract-notice exports and produce quarterly summary charts. APET reorganises the published records to make them easier to explore without treating its calculations as official government statistics.

## Official source

- AusTender: <https://www.tenders.gov.au/>

The official publisher remains the authoritative source. Source workbooks are stored locally and are not committed to this repository. Users should retrieve them from the official service and review its current documentation and terms.

## Expected local structure

```text
australian-public-expense-tracker/
├── branding/
│   └── APETLogo400x400.png       # optional
├── data/
│   └── austender/                # official exports; not committed
├── output/
│   └── austender/                # combined data and generated charts
└── scripts/
    ├── chart_helpers.py
    └── austender/
        ├── combine_austender_files.py
        └── generate_austender_quarterly_charts.py
```

## Processing

The combine script:

1. Reads the AusTender Excel exports placed under `data/austender`.
2. Converts publication and amendment dates to consistent date values.
3. Assigns records to Australian financial years and quarters using publication date.
4. Links amendments to their original contract using `Parent CN ID`.
5. Saves a full historical master file containing originals and amendments.
6. Saves a current-state file retaining the latest published version of each underlying contract.
7. Reports file, row, amendment, contract and value totals for review.

For a historical quarter, the chart script resolves each contract to the latest version published on or before that quarter's end. This prevents a later amendment from retrospectively changing an earlier quarterly chart and prevents original and amended values from being added together.

Quarterly outputs include summaries of supplier and agency contract value, the largest individual contracts, procurement methods, overseas supplier countries, and supplier contract counts. Supporting CSV files are generated alongside the charts.

## Supplier-name standardisation

AusTender supplier labels can differ in spelling or company-suffix conventions even when they refer to the same named supplier. For example, `DELL AUSTRALIA PTY LIMITED` and `DELL AUSTRALIA PTY LTD` would otherwise appear as separate categories in a top-suppliers chart.

The reusable `clean_supplier_name()` function lives in `scripts/chart_helpers.py`. The quarterly generator retains the original `Supplier Name` field and creates a separate `Supplier Clean` field before splitting Defence/non-Defence data and grouping supplier-based charts. The current helper uppercases names, trims and collapses whitespace, standardises selected suffixes (including `LIMITED` to `LTD` and `PROPRIETARY` to `PTY`), and applies an explicit override dictionary for known variants. Supplier value and count summaries group by the cleaned name.

**Interpretation and auditability:** This is label standardisation, not a verified corporate-entity resolution process. Similar names may belong to different entities; distinct trading names or subsidiaries should not automatically be merged. Confirm any more ambitious manual mapping against authoritative evidence, and record the mapping and reason in version-controlled code. Do not overwrite the raw supplier label or change the number or monetary value of underlying notices. Charts should state that supplier names have been standardised, especially when displaying aggregated supplier rankings.

When debugging quarterly generation, keep reusable cleaning logic in `chart_helpers.py`, while quarter-specific grouping, chart wrappers and chart calls remain available in the generator. Ensure a requested quarter is nonempty before cleaning; construct `Supplier Clean` before producing Defence/non-Defence subsets; and use the same cleaned column for both grouping and chart labels. Avoid duplicating the cleaning function or removing unrelated helper functions during edits.

## Important limitations

- Reported contract value is not necessarily expenditure paid during the displayed quarter.
- Publication date determines the reporting quarter and may differ from contract start, end or payment dates.
- Contract notices may be amended, corrected or removed after publication.
- Supplier, agency, category and country summaries depend on the labels supplied by AusTender, apart from documented cleaning.
- Readers should consult the corresponding official AusTender notice and documentation before drawing conclusions.

## Running the pipeline

Install the dependencies:

```text
pip install -r requirements.txt
```

Place source workbooks under `data/austender`, then run:

```text
python scripts/austender/combine_austender_files.py
python scripts/austender/generate_austender_quarterly_charts.py
```

Website asset mirroring is disabled by default. Set `APET_AUSTENDER_WEBSITE_CHART_DIR` if generated SVG and CSV files should also be copied into a website project.

## Partial export coverage labels

The quarterly chart generator marks a period as partial when the latest end date encoded in weekly XLSX export filenames precedes the quarter end. The warning includes that export date so the coverage limit remains visible on standalone charts. This is an end-date warning, not a gap-free completeness test: it does not prove that every intervening day or notice was collected. Reported contract values remain commitments, not quarterly cash expenditure.
