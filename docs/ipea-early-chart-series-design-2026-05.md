# Historical IPEA chart-series design decisions (May 2026)

This note preserves the decisions and lessons from the initial APET IPEA quarterly chart-development session on 21 May 2026. **It is historical context, not a description of the current production implementation.** For current commands, output conventions, limitations and editorial guidance, see [IPEA methodology](ipea-methodology.md) and [editorial/social-media policy](editorial-social-media-policy.md).

## Why the high-level overview charts were added

The initial charts ranked individual parliamentarians by reported expense amounts and changes. A complementary view was needed to answer broader descriptive questions: what types of expenditure were reported, how totals were distributed across party labels, and how totals grouped by state or territory.

An initial manually defined category chart used keyword matching against expense labels and placed unmatched amounts into an **Other** bar. That produced a disproportionately large and poorly explained remainder. A second experiment grouped by `MinorSubCategory`, but its numerous blank entries were labelled **Uncategorised** and dominated the chart. These prototypes were superseded, not accepted as reliable category taxonomies.

Inspection of the official extract established the hierarchy `HighLevelCategory`, `MajorSubCategory` and `MinorSubCategory`, with amounts in `Amount`; `HighLevelCategory` was selected for the quarterly overview. The recommendation is to use the source's explicit classification instead of guessing categories with substring rules, retain and disclose genuinely missing labels, and avoid using a large residual grouping without explaining what it contains.

Two further overview charts aggregate reported `Amount` by `Party` and `StateOrTerritory`. The party chart uses the shared party-colour mapping. These group totals are **descriptive sums, not a fair per-member or per-role comparison**: party sizes, officeholder duties, reporting coverage and adjustments can differ. State/territory values reflect the extract's classification, not a claim about where the expenditure occurred or who ultimately benefited.

## Original 23-chart quarterly sequence

The adopted filename ordering followed the intended presentation sequence: first broad context, then top-spender detail, then changes from the previous quarter.

| Number | Chart |
| --- | --- |
| 01 | Spending by High-Level Category |
| 02 | Spending by Party |
| 03 | Spending by State or Territory |
| 04 | Top Parliamentary Expense Totals |
| 05 | Top Travel Spending |
| 06 | Top Domestic Travel |
| 07 | Top International Travel |
| 08 | Top COMCAR Spending |
| 09 | Top Travel Allowance |
| 10 | Top Printing and Communications |
| 11 | Top Publications |
| 12 | Top Telecommunications |
| 13 | Top Office Consumables and Services |
| 14 | Biggest Parliamentary Expense Increase |
| 15 | Biggest Travel Spending Increase |
| 16 | Biggest Domestic Travel Increase |
| 17 | Biggest International Travel Increase |
| 18 | Biggest COMCAR Increase |
| 19 | Biggest Travel Allowance Increase |
| 20 | Biggest Printing and Communications Increase |
| 21 | Biggest Publications Increase |
| 22 | Biggest Telecommunications Increase |
| 23 | Biggest Office Consumables and Services Increase |

The first 10 individual-spender charts were renumbered 04–13 after the three overviews were added. The 10 quarter-on-quarter increase charts therefore became 14–23. The sequence was also used for a spreadsheet validation dropdown and an initial social-posting plan. The old one-quarter generator and its pasted revisions were development artifacts; the maintained source is now `scripts/ipea/generate_quarterly_charts.py`, alongside shared helpers and the annual generator. Do not restore the prototype script over the maintained code.

## Presentation details worth retaining

- Use a horizontal bar chart for category labels: it is easier to scan than a many-slice pie/donut chart.
- Derive chart period labels from the source quarter rather than hard-coding a single reporting period.
- Place value labels inside bars when there is enough room; place them outside short bars and reserve axis margin so text does not clip. The original experiment used a width threshold of approximately 12% of the largest bar.
- Produce a supporting CSV for each generated chart so totals can be checked independently of the image.
- Use consistent source/period attribution and existing APET branding and party colours.
- Preserve the source column meaning. In particular, avoid treating every numeric column as a spending amount or subtracting arbitrary numeric totals to manufacture an 'Other' category.

## Historical posting proposal and subsequent policy

The May 2026 idea was to publish backlogged quarter charts in broad-to-specific order, potentially around three posts a day, then slow down after catching up. This was **an exploratory proposal, not a permanent publishing requirement**. The maintained editorial policy now prioritises selective, verified, contextual posts instead of publishing every generated chart or meeting a rigid quota. The public website is the complete chart archive; X is a curated distribution channel. Neutral wording, official-source attribution and human review remain essential.

## Retrospective cautions

The development session relied on iterative CSV inspection to correct two erroneous assumptions about column names and category levels. It also initially calculated `Other` by subtracting named sums from *all numeric columns*, which is unsound and must not be reused. Earlier chart prototypes may have swallowed nonnumeric amounts as zero, or grouped personnel by combined name/party keys; current production logic should be audited against official fields and its own documented handling of corrections and missing values. Historical chart series names are working presentation labels, not evidence that quarter-to-quarter increases reflect inappropriate spending.

This record is for design provenance and continuity. Revalidate category definitions, comparability and chart outputs using the current pipeline and source files before making substantive public claims.

## Initial chart branding and X-caption workflow (21 May 2026)

The first published IPEA chart series was created as 16:9 Matplotlib horizontal bar charts, with readable names and currency labels, restrained party colours, a small APET logo at lower left, and a larger grey attribution footer. The logo was loaded from the local `branding/APETLogo400x400.png` asset, and the footer included **@auspublicexp** plus IPEA/data.gov.au source attribution. The purpose was recognisable, reusable branding even when images were shared without their original X posts.

Adding the logo through `fig.add_axes(...)` produced Matplotlib's `tight_layout` compatibility warning. The historical fix was to use explicit `fig.subplots_adjust(left=..., right=..., top=..., bottom=...)` instead of `plt.tight_layout(...)`. The current implementation centralises this in `scripts/chart_helpers.py` through `add_brand_logo`, `add_standard_footer` and `apply_chart_layout`; do not copy the old standalone script back into production.

The original script exported 10 top-amount and 10 previous-quarter-increase charts (with supporting CSV files) for a manually selected source quarter, for example `2024q01_dataextract.csv`. The screenshot-reviewed output included domestic and international travel, COMCAR, travel allowance, printing and communications, publications, telecommunications and office consumables/services. This initial 20-chart series was later superseded by the 23-chart sequence documented above.

For early X posts, the user chose **short neutral captions** summarising the source category and period, usually with official source domains (`ipea.gov.au` and `data.gov.au`) and `#auspol`. Caption drafts had to fit X's character limit, and there was no need to repeat every value already visible in the image. Example template (a historical drafting convention, not an instruction to auto-post):

> Biggest increases in reported [category] spending from Oct–Dec 2023 to Jan–Mar 2024 based on official IPEA expenditure data.\n>\n> Source data: ipea.gov.au / data.gov.au\n>\n> #auspol

These are **rankings of reported amounts or their changes**, not claims of improper spending or like-for-like behavioural changes. In particular, a quarter-on-quarter increase may reflect adjustments, reporting dates, changing officeholders or unmatched names/party labels. Follow the current [IPEA methodology](ipea-methodology.md), [comparison caveats](ipea-party-normalisation-and-quarterly-comparisons.md) and [editorial policy](editorial-social-media-policy.md) before publishing.
