# ABS Government Finance Statistics methodology

## Source and scope

APET uses official Australian Bureau of Statistics Government Finance Statistics data. The current charts cover the **All Australia general government sector** and present annual results using Australian financial years from July to June.

Official source: [Australian Bureau of Statistics — Government Finance Statistics](https://www.abs.gov.au/statistics/economy/government)

## What the figures represent

The charts describe government **expenses recorded on an accrual basis**. Accrual accounting records economic activity when it occurs rather than only when cash is paid.

The figures are:

- current-price values
- original series
- aggregate statistical measures
- expressed using Australian financial-year labels

They are not adjusted for inflation and do not identify individual contracts, grants or payments.

## APET presentation

APET normalises selected ABS observations into a consistent chart schema and presents:

- expenses by purpose
- where every $100 of expenses went
- expenses by level of government

The source values are not altered. Supporting CSV files contain the figures used in each chart.

## Limitations and interpretation

Changes between years may reflect price movements as well as changes in the volume or composition of government activity. The charts should therefore not be described as showing inflation-adjusted growth.

Components may differ slightly from published totals because ABS values are rounded. ABS GFS is also conceptually different from APET's transaction-level and award-level sources:

- AusTender reports contract notices and reported contract values
- GrantConnect reports published grant awards
- IPEA reports parliamentary expenses
- ABS GFS reports aggregate government expenses

These measures should not be added together or treated as directly equivalent.

## Authority and corrections

The Australian Bureau of Statistics remains the authoritative source. If an APET chart differs from the official publication, readers should rely on the ABS release and report the discrepancy through the repository's [Issues](https://github.com/auspublicexp/australian-public-expense-tracker/issues) section.

## FY2025–26 quarterly-derived extension

The separate `fetch_quarterly_gfs.py` and `quarterly_gfs.py` workflow uses all four quarters from the June 2026 publication. It retains source URLs, retrieval times and SHA-256 hashes, and validates sector, units, quarter order, unique measures and published totals. `test_quarterly_gfs.py` exercises reconciliation and rejection of invalid or mixed-vintage inputs.

These results stay in `FY2025-26_quarterly_derived`, separate from annual output. They do not provide annual expense-by-purpose or separate government-level breakdowns. Selected income-tax, company-tax and GST figures come from the ABS insights article and are labelled as published totals. All figures are current-price, original-series, general-government accrual estimates. See the [workflow instructions](../scripts/abs_gfs/README.md) and [published summary](https://auspublicexp.org/abs-gfs/fy2025-26-quarterly.php).

