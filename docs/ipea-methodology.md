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
- `chart_helpers.py` contains shared cleaning, formatting, colour and chart-layout functions.

## Expected local structure

```text
australian-public-expense-tracker/
├── branding/
│   └── APETLogo400x400.png       # optional
├── data/
│   └── ipea/                     # official CSV extracts; not committed
├── output/
│   └── ipea/                     # generated charts and supporting files
└── scripts/
    ├── chart_helpers.py
    └── ipea/
        ├── download_missing_ipea_data.py
        ├── generate_annual_charts.py
        └── generate_quarterly_charts.py
```

Quarterly source filenames follow this pattern:

```text
2025q01_dataextract.csv
```

## Processing

The chart scripts:

1. Load the official quarterly CSV extract or four extracts forming a complete financial year.
2. Strip whitespace from column names.
3. Convert the reported `Amount` field to a number, treating non-numeric values as zero.
4. Apply documented name and party-label cleaning from the shared helper.
5. Aggregate reported amounts by the relevant chart dimension.
6. Export chart-supporting CSV data alongside the generated chart.
7. Produce PNG and, where applicable, SVG outputs with APET source footers.

Quarterly outputs include spending summaries by high-level category, party and state or territory; selected expenditure categories; and changes from the preceding available quarter. Annual outputs cover equivalent summaries for complete Australian financial years.

## Website mirroring

Website asset mirroring is disabled by default. Set `APET_IPEA_WEBSITE_CHART_DIR` to an output folder if generated SVG and CSV files should also be copied into a website project.

## Important limitations

- Amounts are aggregated from the classifications and values supplied in the official extract.
- A reported expense is not necessarily cash paid during the displayed period.
- Negative amounts, adjustments or later corrections may appear in official records.
- Party, name, state and category summaries depend on the labels supplied by IPEA, apart from documented cleaning rules.
- Comparisons can be affected by membership changes, incomplete periods and changes in reporting classifications.
- Readers should consult the corresponding official IPEA dataset and reporting documentation before drawing conclusions.

## Running the pipeline

Install the dependencies:

```text
pip install -r requirements.txt
```

Download missing quarterly extracts:

```text
python scripts/ipea/download_missing_ipea_data.py
```

Generate quarterly and annual outputs:

```text
python scripts/ipea/generate_quarterly_charts.py
python scripts/ipea/generate_annual_charts.py
```
