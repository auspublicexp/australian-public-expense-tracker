# Australian Public Expense Tracker

Australian Public Expense Tracker (APET) presents publicly available Australian government expenditure data in a clear, accessible and reusable format.

APET is an independent, politically neutral project. It does not advocate for or against any political party, parliamentarian or policy. Its purpose is to make official expenditure data easier to explore and understand so readers can draw their own conclusions.

**[View the published charts at auspublicexp.org](https://auspublicexp.org/)**

## Current coverage

The repository documents processing pipelines for parliamentary expenditure, Australian Government procurement, grant-award data, and Australian Government Finance Statistics.

Official sources:

- [Independent Parliamentary Expenses Authority](https://www.ipea.gov.au/)
- [IPEA datasets on data.gov.au](https://data.gov.au/data/organization/ipea)
- [AusTender](https://www.tenders.gov.au/)
- [GrantConnect](https://www.grants.gov.au/)
- [Australian Bureau of Statistics — Government](https://www.abs.gov.au/statistics/economy/government)

## Understanding the figures

The four sources measure different things and their values should not be treated as interchangeable.

| Dataset | What the value represents |
| --- | --- |
| IPEA | Reported parliamentary expenses for the relevant reporting period. |
| AusTender | Reported contract value, not necessarily cash paid during the period. |
| GrantConnect | Published grant-award value, not necessarily cash paid during the period. |
| ABS GFS | Aggregate government expenses recorded on an accrual basis, not individual transactions or inflation-adjusted growth. |


## Data quality and validation

APET keeps downloaded source files and generated outputs outside version control. Before derived search indexes or charts are published, the processing workflows check the fields they depend on, parse dates and monetary values, and apply source-specific duplicate or amendment handling.

Each source pipeline writes a small latest-run validation report to `output/validation` on the maintainer's computer:

- a readable `*_latest.txt` summary
- a structured `*_latest.json` summary

These reports record the run time, coverage, record and period counts, output locations, and the checks completed. They are working records for the maintainer, are replaced by the next successful run, and are not published on the website or committed to this repository.

Important source-specific limitations remain:

- **IPEA:** transactions generally appear in the period when they were paid, which may differ from when travel or other activity occurred; later adjustments or repayments may also be published.
- **AusTender:** values describe reported contract commitments over the contract's life, not cash paid in a quarter. Reporting thresholds apply, and entities can amend, vary or cancel notices.
- **GrantConnect:** APET groups awards by publication date. Published award values are not necessarily payments made in that period, and recipient names may vary between records.
- **ABS GFS:** figures are aggregate accrual estimates in current prices and original series. They are not individual transactions or inflation-adjusted growth, and historical estimates may be revised.

Validation can identify structural problems such as missing required fields, invalid dates or duplicate identifiers. It cannot independently verify whether an official source record is factually correct. The government publisher remains authoritative, and significant findings should be checked against the linked official record.

## Published data pipelines

### IPEA parliamentary expenditure

APET's IPEA pipeline downloads official quarterly expenditure extracts and produces quarterly and Australian financial-year summaries. Quarterly source filenames retain IPEA's calendar-quarter convention, while generated output folders use APET's Australian financial-year quarter labels.

The public chart-appearance search indexes parliamentarians displayed in person-level chart CSV files. It supports party, state or territory, expense category, period, minimum reported amount and chart-type filters, with links to the relevant chart. A chart appearance is not a count of expenses, transactions or payments.

- [Published IPEA chart-appearance search](https://auspublicexp.org/ipea/search.php)
- [Methodology and limitations](docs/ipea-methodology.md)
- [IPEA scripts](scripts/ipea)
- [Shared chart helpers](scripts/chart_helpers.py)

### AusTender

APET's AusTender pipeline combines official contract-notice exports, resolves amendments for historical reporting, and produces quarterly procurement summaries. Its public search supports supplier, agency, contract description, CN ID, period and reported-value filters, with links to APET charts and official AusTender records.

- [Published AusTender supplier and contract search](https://auspublicexp.org/austender/search.php)
- [Methodology and limitations](docs/austender-methodology.md)
- [AusTender scripts](scripts/austender)
- [Shared chart helpers](scripts/chart_helpers.py)

### GrantConnect

APET's GrantConnect pipeline produces quarterly and annual summaries from publicly available Australian Government grant-award exports. Its public search supports recipient, activity, agency, category, period, location, identifier and reported-value filters, with links to APET charts and official GrantConnect records.

- [Published GrantConnect award search](https://auspublicexp.org/grantconnect/search.php)
- [Methodology and limitations](docs/grantconnect-methodology.md)
- [GrantConnect scripts](scripts/grantconnect)
- [Shared chart helpers](scripts/chart_helpers.py)

### ABS Government Finance Statistics

APET's ABS Government Finance Statistics (GFS) pipeline produces annual summaries using Australian financial years (July to June). The figures describe All Australia general government expenses on an accrual basis and are presented in current prices, original series. The topic explorer compares expenditure purposes and government levels across available financial years in dollars or as a share of the selected total.

- [Published ABS GFS topic explorer](https://auspublicexp.org/abs-gfs/explorer.php)
- [Methodology and limitations](docs/abs-gfs-methodology.md)
- [ABS GFS scripts and workflow](scripts/abs_gfs)
- [Published ABS GFS charts](https://auspublicexp.org/abs-gfs/)
- [Official ABS government statistics](https://www.abs.gov.au/statistics/economy/government)

## Repository structure

```text
scripts/
├── chart_helpers.py
├── abs_gfs/
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

APET is an independently maintained hobby project. Updates are published when time and official source data permit; no fixed publication schedule is promised. Repository documentation and methodology may evolve as the project develops.

## Corrections and questions

Questions, corrections and reproducibility issues can be raised through this repository's [Issues](https://github.com/auspublicexp/australian-public-expense-tracker/issues) section. Please include the relevant dataset, reporting period and page or chart when possible.

## Licence

This project's original code is available under the [MIT License](LICENSE). Government source datasets remain subject to the terms specified by their original publishers.
