# AusTender quarterly publishing workflow — July 2026 reference

This note preserves the **manual publication procedure used for FY2025–26 Q4 (April–June 2026)**. It is a historical handover aid, not a guarantee that every file, setting or deployment step is unchanged. Before using it, consult the current [AusTender methodology](austender-methodology.md), [website operations](website-operations.md), [chart-download implementation](chart-downloads.md) and the actual scripts and PHP files. The current pipeline has since added explicit original/amendment handling, quarter-end historical views, coverage warnings and optional chart asset mirroring.

## Local source ingestion and checking

1. Download weekly AusTender contract-notice XLSX exports from <https://www.tenders.gov.au/>.
2. Store them locally in `data/austender/` using the export date range in the filename, for example `12-Jul-26 to 18-Jul-26.xlsx`.
3. In the original manual workflow, edit the filename in `scripts/austender/check_austender_files.py` and run it separately for each new workbook. Check expected column headings, nonzero plausible row counts, representative sample records, dates and numeric values. Optional blanks (`NaN`/`NaT`) are not automatically errors. This checker may not exist or have the same interface in newer versions.
4. Run `python scripts/austender/combine_austender_files.py` from the repository root. Review the reported file and row totals, quarters and validation results; do not assume a successful exit alone proves complete coverage or correct handling of amendments.
5. Set `TARGET_FY_QUARTER` in `scripts/austender/generate_austender_quarterly_charts.py` to the intended **completed** reporting period, then run the script from the repository root. In the July 2026 example this was `FY2025-26_Q4`, not the newly emerging partial `FY2026-27_Q1`.

Quarter convention: Q1 July–September; Q2 October–December; Q3 January–March; Q4 April–June.

**Historical diagnostic:** the July 2026 local combine run read 85 weekly workbooks and printed 146,223 rows and quarters extending into FY2026–27 Q1. These are one-time observations, **not** expected current totals or a validated unique-contract count. The July quarter was incomplete, even though present in the quarter list.

## Review and social scheduling (manual)

The historical quarterly generator produced seven chart types: leading suppliers by reported contract value; largest individual contracts; Defence suppliers; procurement methods; overseas supplier countries; non-Defence agencies; and suppliers by contract count. Each chart had a PNG, a supporting `_data.csv`, and a `_post.txt` caption in a period-specific output folder such as `output/austender/FY2025-26_Q4/`.

1. Inspect the chart titles, values, labels, source attribution, CSVs and post captions before release.
2. Open the post-tracking spreadsheet and find the last AusTender quarterly post identifier; allocate the next **unused** ID (the example format was `AUSTENQ0036`). Do not infer today's next ID from this example.
3. Manually create a folder for each Post ID in the social-post archive and keep its matching PNG, CSV and caption together.
4. Upload the chart image and review/paste the caption in Buffer. Choose a publishing slot.
5. **Only after the post is visibly scheduled** tick its Scheduled checkbox in the tracking spreadsheet. Record the date or eventual post URL when appropriate. Do not treat an archived file as evidence of publication.

## Hostinger deployment through WinSCP (manual)

The historical website was a PHP/Bootstrap site deployed using WinSCP to Hostinger. Do not commit credentials, authentication configuration or private host details.

1. Copy the **approved** charts into the corresponding local deployable website tree. For Q4 FY2025–26, PNG paths followed:
   - Local: `website/public_html/charts/austender/fy2025_26/q4/`
   - Remote: `/public_html/charts/austender/fy2025_26/q4/`
2. In WinSCP, connect to the saved Hostinger session, confirm local and remote roots, and use **local → remote** synchronization. Inspect the preview, confirming that new PNGs go to the intended period and that unrelated files are not removed; avoid automatic remote deletion.
3. The July 2026 gallery linked PNGs from a sibling quarter page. Copy `website/public_html/austender/fy2025_26/q3.php` to `q4.php`, then edit:
   - Title: `AusTender FY2025-26 Q4 Summary`
   - Subtitle: `April to June 2026`
   - PHP image base path: `$basePath = "/charts/austender/fy2025_26/q4/";`
   - Chart list/filenames to match the generated assets, typically the same seven numbered names as the previous quarter.
   - Keep the appropriate shared header/footer include paths, escaping and download links used by the **current** template. Do not blindly restore the older PNG-only gallery over newer SVG/CSV functionality.
4. Upload/synchronize `website/public_html/austender/fy2025_26/q4.php` into remote `/public_html/austender/fy2025_26/`. The historical published URL was <https://auspublicexp.org/austender/fy2025_26/q4.php>, **not** a `q4/index.php` route.
5. In the financial-year overview page (historically <https://auspublicexp.org/austender/fy2025_26/>), enable or unhide the Q4 link and upload the modified file. Verify page links rather than assuming a specific overview filename or flag remains in use.
6. Open the public page in a browser, check every chart/download, click to view the full-size image, test the financial-year navigation, and inspect mobile layout and a private/hard-refresh browser session for stale cache or missing files.
7. Reconcile the live site with the tracking spreadsheet and Buffer queue; retain the local archived source and post assets as appropriate. The website is the public archive and chart values are **reported contract values**, not cash spent in the quarter.

## Future improvement ideas from the conversation

Potential conveniences, **not claimed as implemented here**: automatically generate per-Post-ID archive folders; generate quarter PHP pages from a maintained template; update financial-year navigation automatically; introduce a pre-deployment link/asset checklist; and show latest dataset releases on the homepage. Prioritise low-maintenance improvements and first verify what the newer repository already implements.
