# DFAT foreign-aid methodology and limitations

## Scope

APET uses the official DFAT Australia International Aid Transparency Initiative (IATI) Activity File. The current file contains detailed activities, commitments and reported disbursements from FY2022-23 onward.

## Processing

1. `fetch_dfat_iati.py` discovers the current XML resource through the data.gov.au CKAN API, downloads the XML and official IATI code lists, and records file hashes and source metadata.
2. `normalize_dfat_iati.py` produces one stable row per IATI transaction and adds readable country, region, sector and transaction-type labels.
3. `validate_dfat_foreign_aid.py` checks required fields, currencies, transaction types and financial-year totals and records negative adjustment rows.
4. `generate_dfat_foreign_aid_charts.py` selects IATI type-3 disbursements and creates overview and annual financial-year charts.

## Meaning of the values

The charted values are DFAT's IATI **disbursements**. IATI distinguishes these from commitments and budgets. APET therefore does not add type-2 commitments to type-3 disbursements.

Negative values are not automatically errors. DFAT uses negative aid flows for adjustments, including returned prior-year funds and reconciliation between accrual expenses and ODA cash reporting. APET retains these values in net totals.

## Important limitations

- The current activity file covers only recent financial years. Longer historical comparisons require DFAT's separate official ODA standard time series.
- Transactions are dated at financial-year end in the current file. They should not be interpreted as payments made specifically on 30 June, and quarterly charts would be misleading.
- Country charts omit transactions coded only to a region or to an unspecified/multilateral destination. Consequently, the displayed country bars do not sum to total Australian aid.
- Sector and country classifications describe DFAT's reporting categories. A single activity can contain separately coded transactions across destinations or sectors.
- Disbursements do not by themselves measure effectiveness, value for money or waste. Project purpose, results, local conditions and humanitarian circumstances need separate assessment.
- DFAT may revise or republish source data. APET charts are point-in-time reproductions and the download manifest identifies the file used.

Official publisher data remains authoritative. Significant findings should be checked against the current [AusDevPortal downloads](https://adp.dfat.gov.au/data-downloads) and [DFAT IATI dataset](https://data.gov.au/data/dataset/dfat-australia-iati-activity-file).
