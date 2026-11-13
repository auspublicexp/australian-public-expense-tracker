# Contributing to APET

APET helps people understand public spending through neutral explanations, source links and reproducible calculations. Contributions can be small: a clearer label or a well-documented discrepancy is useful even without a code change.

## Report a problem

Search [existing issues](https://github.com/auspublicexp/australian-public-expense-tracker/issues) first, then use the relevant [issue form](https://github.com/auspublicexp/australian-public-expense-tracker/issues/new/choose):

- **Possible data discrepancy:** include the collection, reporting period, APET page or chart, official source and figures that appear to differ. Check the measure and units first: contract and grant values, cash payments and accrual expenses are not interchangeable.
- **Website or script problem:** include the page or command, steps to reproduce, expected result and actual result. Browser/device details help with layout problems; Python version and a short error excerpt help with script problems.

Reports are public. Include public record identifiers and source URLs, but remove credentials, private records and personal information from logs or screenshots. It is fine to describe uncertainty rather than asserting that a figure is wrong.

## Make a focused change

1. Read the relevant methodology and script README linked from the [project README](README.md). For a practical starting point, see [Reproduce a chart](docs/reproduce-a-chart.md).
2. Work in a separate checkout or branch. Source downloads and generated outputs are excluded from version control. Some generators write into a local website tree, so inspect their arguments and use a separate output directory where supported.
3. Keep terminology, reporting periods and limitations with the figures. Explain changes to cleaning, aggregation, duplicate handling or publication eligibility. Retain negative adjustments unless the source methodology justifies another treatment.
4. Run checks appropriate to the change. For a data transformation, compare record counts, periods and totals and check a representative chart/CSV. For a website change, inspect links, narrow-screen layout and keyboard use. Documentation-only changes usually need a careful link and command review.
5. In the pull request, explain the problem, resulting behavior, validation performed and remaining limits. Identify source versions or checksums when data results are affected. Do not commit raw downloads, generated charts, local validation reports or access details.

New datasets or substantial changes are best discussed in an issue before implementation. Useful proposals identify the official source, what its values measure, reporting frequency, coverage, licence terms and likely overlap with existing collections.

## Reuse and project scope

APET's original code uses the [MIT License](LICENSE). Source datasets retain their publishers' terms. The code licence does not relicense government material.

The website is the public archive. A code change or local build does not establish that the live site was updated. APET is independently maintained; response and publication times vary. Contributions should support understandable, evidence-based public information and the project's non-partisan approach.
