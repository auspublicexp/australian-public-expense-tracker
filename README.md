# Australian Public Expense Tracker

Australian Public Expense Tracker (APET) presents publicly available Australian government expenditure data in a clear, accessible and reusable format.

APET is an independent, politically neutral project. It does not advocate for or against any political party, parliamentarian or policy. Its purpose is to make official expenditure data easier to explore and understand so readers can draw their own conclusions.

## Current focus

The project is beginning with parliamentary expenditure data published by the Independent Parliamentary Expenses Authority (IPEA).

Official sources:

- [Independent Parliamentary Expenses Authority](https://www.ipea.gov.au/)
- [IPEA datasets on data.gov.au](https://data.gov.au/data/organization/ipea)

The project may later expand to other public spending datasets, including procurement, grants and government financial reporting.

## Published data pipelines

### GrantConnect

APET's GrantConnect pipeline produces quarterly summaries from publicly available Australian Government grant-award exports.

- [Methodology and limitations](docs/grantconnect-methodology.md)
- [Chart-generation script](scripts/generate_grantconnect_quarterly_charts.py)
- [Archive reconciliation script](scripts/reconcile_grantconnect_archive.py)
- [Shared chart helpers](scripts/chart_helpers.py)

## Transparency and methodology

APET aims to provide an auditable path from each published result back to its official source:

**Official government data → APET processing script → chart or table → published page**

This repository will contain the scripts and methodology used to download, clean, transform and present the data. Where practical, each published chart or table will identify:

- the official source dataset
- the relevant reporting period
- the processing script used
- important definitions, exclusions or limitations
- the date the data was retrieved or updated

The official government publisher remains the authoritative source. APET does not alter source records, estimate unreported expenditure or present its calculations as official government statistics.

## Reproducibility

As the project develops, this repository will include:

- documented data-processing scripts
- source links and retrieval notes
- chart-generation code
- methodology notes
- software requirements and instructions for reproducing outputs

Large source datasets may not be stored in this repository. Instead, APET will link to the official download page or API and record enough information for the analysis to be reproduced.

## Project status

APET is in early development. The repository structure, documentation and methodology will evolve as the first IPEA data pipeline and public website are built.

## Corrections and questions

Questions, corrections and reproducibility issues can be raised through this repository's [Issues](https://github.com/auspublicexp/australian-public-expense-tracker/issues) section. Please include the relevant dataset, reporting period and page or chart when possible.

## Licence

This project's original code is available under the [MIT License](LICENSE). Government source datasets remain subject to the terms specified by their original publishers.
