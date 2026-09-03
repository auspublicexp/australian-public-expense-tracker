# IPEA parliamentary expenditure methodology

## Purpose

The IPEA scripts download and summarise publicly available parliamentary expenditure records published by the Independent Parliamentary Expenses Authority. APET presents these records in a more accessible form without treating its calculations as official IPEA statistics.

## Official sources

- Independent Parliamentary Expenses Authority: <https://www.ipea.gov.au/>
- IPEA datasets on data.gov.au: <https://data.gov.au/data/organization/ipea>

The official publisher remains the authoritative source. Source CSV files are stored locally under `data/ipea` and are excluded from this repository.

## Scripts

- `download_missing_ipea_data.py` discovers quarterly IPEA datasets through the data.gov.au CKAN API, downloads missing CSV resources and validates their required columns.
- `generate_quarterly_charts.py` creates quarterly charts and supporting CSV files from each available extract.
- `generate_annual_charts.py` combines four calendar-quarter extracts into a complete Australian financial year and creates annual charts and supporting CSV files.
- `build_ipea_search_index.py` indexes names appearing in the supporting CSV files for published person-level charts.
- `chart_helpers.py` contains shared cleaning, formatting, colour and chart-layout functions.

## Expected local structure

```text
australian-public-expense-tracker/
├── branding/
│   └── APETLogo400x400.png        # optional
├── data/
│   └── ipea/                      # official CSV extracts; not committed
├── output/
│   └── ipea/                      # generated charts and supporting files
└── scripts/
    ├── chart_helpers.py
    └── ipea/
        ├── build_ipea_search_index.py
        ├── download_missing_ipea_data.py
        ├── generate_annual_charts.py
        └── generate_quarterly_charts.py
```

Quarterly source filenames retain IPEA's calendar-quarter convention, for example `2026q02_dataextract.csv`. Generated output folders use APET's Australian financial-year convention: that example becomes `FY2025-26_Q4` because April–June 2026 is the fourth quarter of FY2025–26.

## Processing

The chart scripts:

1. Load the official quarterly CSV extract or four extracts forming a complete financial year.
2. Strip whitespace from column names.
3. Convert the reported `Amount` field to a number, treating non-numeric values as zero.
4. Apply documented name and party-label cleaning from the shared helper.
5. Aggregate reported amounts by the relevant chart dimension.
6. Export chart-supporting CSV data alongside the generated chart.
7. Produce PNG and SVG outputs with APET source footers.
8. Refresh the chart-appearance search index after generation.

Quarterly and annual outputs include spending summaries by high-level category, party and state or territory, plus selected person-level expenditure categories.

## Chart-appearance search

The public [IPEA name search](https://auspublicexp.org/ipea/search.php) is built from the supporting CSV files for person-level charts. Each indexed result means that a person's name is displayed in one published chart. It is not a count of expense records, transactions or payments.

The search supports annual and quarterly period filters and links to the relevant chart. Its results include historical charts and may therefore contain former parliamentarians. The linked [Parliament of Australia Senators and Members directory](https://www.aph.gov.au/Senators_and_Members/) lists current parliamentarians only.

The generated JSON index is a website output and is not committed to this repository.

## Website mirroring and search configuration

Website asset mirroring is disabled by default. Set `APET_IPEA_WEBSITE_CHART_DIR` if generated SVG and CSV files should also be copied into a website project.

By default, `build_ipea_search_index.py` reads chart-supporting files from `output/ipea` and writes `output/ipea/ipea-search-index.json`. These locations can be changed with `APET_IPEA_CHART_ROOT` and `APET_IPEA_SEARCH_INDEX_PATH`.

## Important limitations

- Amounts are aggregated from the classifications and values supplied in the official extract.
- A reported expense is not necessarily cash paid during the displayed period.
- Negative amounts, adjustments or later corrections may appear in official records.
- Party, name, state and category summaries depend on the labels supplied by IPEA, apart from documented cleaning rules.
- Comparisons can be affected by membership changes, incomplete periods and changes in reporting classifications.
- A person absent from search results may still appear in the underlying IPEA records but not in one of APET's published rankings.
- Readers should consult the corresponding official IPEA dataset and reporting documentation before drawing conclusions.

## Running the pipeline

Install the dependencies:

```bash
pip install -r requirements.txt
```

Download missing quarterly extracts:

```bash
python scripts/ipea/download_missing_ipea_data.py
```

Generate quarterly and annual outputs. Each generator refreshes the search index when it finishes:

```bash
python scripts/ipea/generate_quarterly_charts.py
python scripts/ipea/generate_annual_charts.py
```

The search index can also be rebuilt independently:

```bash
python scripts/ipea/build_ipea_search_index.py
```
