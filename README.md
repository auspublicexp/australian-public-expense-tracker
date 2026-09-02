# Australian Public Expense Tracker

Australian Public Expense Tracker (APET) presents publicly available Australian government expenditure data in a clear, accessible and reusable format.

APET is an independent, politically neutral project. It does not advocate for or against any political party, parliamentarian or policy. Its purpose is to make official expenditure data easier to explore and understand so readers can draw their own conclusions.

## Current coverage

The repository documents processing pipelines for parliamentary expenditure, Australian Government procurement, and grant-award data.

Official sources:

- [Independent Parliamentary Expenses Authority](https://www.ipea.gov.au/)
- [IPEA datasets on data.gov.au](https://data.gov.au/data/organization/ipea)
- [AusTender](https://www.tenders.gov.au/)
- [GrantConnect](https://www.grants.gov.au/)

## Published data pipelines

### IPEA parliamentary expenditure

APET's IPEA pipeline downloads official quarterly expenditure extracts and produces quarterly and Australian financial-year summaries.

- [Methodology and limitations](docs/ipea-methodology.md)
- [IPEA scripts](scripts/ipea)
- [Shared chart helpers](scripts/chart_helpers.py)

### AusTender

APET's AusTender pipeline combines official contract-notice exports, resolves amendments for historical reporting, and produces quarterly procurement summaries.

- [Methodology and limitations](docs/austender-methodology.md)
- [AusTender scripts](scripts/austender)
- [Shared chart helpers](scripts/chart_helpers.py)

### GrantConnect

APET's GrantConnect pipeline produces quarterly and annual summaries from publicly available Australian Government grant-award exports.

- [Methodology and limitations](docs/grantconnect-methodology.md)
- [GrantConnect scripts](scripts/grantconnect)
- [Shared chart helpers](scripts/chart_helpers.py)

## Repository structure

```text
scripts/
├── chart_helpers.py
├── austender/
├── grantconnect/
└── ipea/
```

Source datasets and generated outputs are kept outside version control. See the methodology document for each pipeline for its expected local structure, processing steps, limitations, and running instructions.

## Transparency and methodology

APET aims to provide an auditable path from each published result back to its official source:

**Official government data → APET processing script → chart or table → published page**

Where practical, each published chart or table will identify:

- the official source dataset
- the relevant reporting period
- the processing script used
- important definitions, exclusions or limitations
- the date the data was retrieved or updated

The official government publisher remains the authoritative source. APET does not alter source records, estimate unreported expenditure or present its calculations as official government statistics.

## Reproducibility

This repository includes documented data-processing scripts, source links, chart-generation code, methodology notes, and software requirements. Large source datasets are not stored here; users should obtain them from the official publisher.

## Project status

APET is in active development. Repository documentation and methodology will evolve as data pipelines and the public website expand.

## Corrections and questions

Questions, corrections and reproducibility issues can be raised through this repository's [Issues](https://github.com/auspublicexp/australian-public-expense-tracker/issues) section. Please include the relevant dataset, reporting period and page or chart when possible.

## Licence

This project's original code is available under the [MIT License](LICENSE). Government source datasets remain subject to the terms specified by their original publishers.
