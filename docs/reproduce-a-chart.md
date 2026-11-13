# Reproduce an NDIS chart from official source files

This example rebuilds APET's annual NDIS payments chart from the three reviewed June snapshots, including the comparison with the corresponding NDIA report workbooks. The same command produces the supporting category and state charts. It writes to a separate directory and does not update a live website.

These are snapshots for FY2023–24, FY2024–25 and FY2025–26, not a request to use the latest rolling quarterly file. Successive quarterly snapshots overlap and must not be added together. Read the [NDIS methodology](ndis-methodology.md) and [pipeline notes](../scripts/ndis/README.md) before interpreting the results.

## 1. Use a separate checkout and Python environment

The following commands use PowerShell, Git and Python 3.12. On another platform, use that environment's Python executable and equivalent download commands.

```powershell
git clone https://github.com/auspublicexp/australian-public-expense-tracker.git apet-reproduction
Set-Location apet-reproduction
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
New-Item -ItemType Directory -Force data/ndis/raw, output/reproduction/ndis | Out-Null
git rev-parse HEAD | Set-Content output/reproduction/code-commit.txt
.\.venv\Scripts\python.exe -m pip freeze | Set-Content output/reproduction/python-packages.txt
```

Use an unused checkout directory name. Recording the commit and installed packages matters because the repository's requirements specify minimum versions, not a locked environment.

## 2. Obtain the six official inputs

The [NDIA payments datasets page](https://dataresearch.ndis.gov.au/datasets/payments-datasets) describes the payment data. The reviewed source IDs and required local filenames are listed below. Downloads remain subject to the publisher's terms.

| Snapshot | Payments CSV | National quarterly report workbook |
| --- | --- | --- |
| June 2024 | [Media 4480](https://dataresearch.ndis.gov.au/media/4480/download?attachment) → `payments_2024-06.csv` | [Media 4029](https://dataresearch.ndis.gov.au/media/4029/download?attachment) → `national_2023-24_Q4.xlsx` |
| June 2025 | [Media 4476](https://dataresearch.ndis.gov.au/media/4476/download?attachment) → `payments_2025-06.csv` | [Media 4359](https://dataresearch.ndis.gov.au/media/4359/download?attachment) → `national_2024-25_Q4.xlsx` |
| June 2026 | [Media 4577](https://dataresearch.ndis.gov.au/media/4577/download?attachment) → `payments_2026-06.csv` | [Media 4560](https://dataresearch.ndis.gov.au/media/4560/download?attachment) → `national_2025-26_Q4.xlsx` |

Save them in `data/ndis/raw`. The commands below download those specific files into the new checkout:

```powershell
$ndisInputs = @{
    'payments_2024-06.csv' = 4480
    'national_2023-24_Q4.xlsx' = 4029
    'payments_2025-06.csv' = 4476
    'national_2024-25_Q4.xlsx' = 4359
    'payments_2026-06.csv' = 4577
    'national_2025-26_Q4.xlsx' = 4560
}
foreach ($name in $ndisInputs.Keys) {
    $sourceUrl = 'https://dataresearch.ndis.gov.au/media/' + $ndisInputs[$name] + '/download?attachment'
    Invoke-WebRequest -Uri $sourceUrl -OutFile (Join-Path 'data/ndis/raw' $name)
}
(Get-Date).ToUniversalTime().ToString('o') | Set-Content output/reproduction/downloaded-at-utc.txt
Get-FileHash data/ndis/raw/* -Algorithm SHA256 | Export-Csv output/reproduction/source-sha256.csv -NoTypeInformation
```

Use these commands only in the new reproduction checkout; they replace files with the same names. If a download fails or its structure has changed, resolve that against the official source rather than substituting another quarter. A current download may differ from APET's original source version; retain its checksum and retrieval date.

## 3. Build into the isolated output directory

Run without Python's `-O` option because the pipeline uses assertions for source checks.

```powershell
.\.venv\Scripts\python.exe scripts/ndis/build_ndis.py --raw data/ndis/raw --out output/reproduction/ndis
.\.venv\Scripts\python.exe scripts/ndis/build_charts.py --out output/reproduction/ndis
```

The first command checks the reviewed snapshot structures, calculates annual payment totals and compares them with the report tables. The second creates 15 charts with PNG, SVG and CSV outputs. No PHP server is needed to inspect the chart images or CSVs.

Open `output/reproduction/ndis/charts/annual.png` and `annual.csv`. The CSV contains the exact payment values used in the annual chart:

| Financial year | Payments (AUD), original reviewed snapshot |
| --- | ---: |
| FY2023–24 | 41,254,223,000 |
| FY2024–25 | 45,853,407,000 |
| FY2025–26 | 51,451,547,000 |

Compare with the [published annual chart data](https://auspublicexp.org/ndis/charts/annual.csv) and the [chart page](https://auspublicexp.org/ndis/charts.php). Numbers can be compared exactly; image bytes may differ across software or font versions.

## 4. Review the checks and explain differences

Inspect the generated `validation.json`, `fy2023-24-validation.json` and `fy2024-25-validation.json`, and the corresponding payments JSON files. The build preserves and discloses differences from the NDIA quarterly-report totals; a successful build does not mean those independent source totals reconcile exactly.

The national payment measure sums the four published support-class aggregates once. State amounts describe participant residence, not state-government expenditure. Values are nominal and are not adjusted for participant numbers. Suppression and category/class rounding differences are described in the methodology.

If your results differ, record the source hashes, code commit, installed package versions, affected period and exact values in a [data-discrepancy issue](https://github.com/auspublicexp/australian-public-expense-tracker/issues/new/choose). Do not edit the data merely to force agreement.

## Verification record

The build commands were exercised on 13 November 2026 using Python 3.12.10 and matplotlib 3.10.9, the public NDIS scripts, and the maintainer's preserved official source files. All three annual totals and all 15 chart CSVs matched the maintained website outputs. This was an isolated reproduction of preserved inputs, not a new source download or live deployment. Download availability and publisher revisions must be checked when repeating the example.
