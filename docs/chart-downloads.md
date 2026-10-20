# Reusable chart downloads

The NDIS charts page established a consistent choice of PNG image, SVG image and
CSV data. The 19 October 2026 update extended this approach to ABS Government
Finance Statistics, ARC grants, AusTender, foreign aid, GrantConnect, public
hospital funding, IPEA parliamentary expenses, Medicare MBS and PBS/RPBS.

PNG files are intended for straightforward online sharing. They preserve the
chart title, reporting period, units, source and APET attribution already present
in the figure. SVG remains available for scalable graphics and CSV for reuse of
the chart's underlying values. This update does not change dataset definitions,
reporting coverage, historical values or source limitations.

## Chart generation and publication

The chart builders already save PNG/SVG pairs. Their website-copy steps now
include PNGs as well as SVGs and CSVs, preserving the existing period subfolders.
IPEA's optional website-directory environment settings and other existing public
script configuration are retained. ARC's generator accepts `--website-dir` to
select its website chart destination. Its existing search-index refresh remains.

Run the usual dataset builder after source validation; no separate image
conversion or browser-side export is needed. For example, a Medicare overview
refresh can be checked without modifying the published site:

```text
python scripts/mbs/generate_mbs_charts.py --overview-only --output-root /path/to/check/output --website-dir /path/to/check/website
```

The normal source-file and logo defaults apply unless overridden with
`--data-file` and `--logo`. Both output folders should contain the matching PNG,
SVG and CSV files. The existing data fetch, normalization, validation and
search-index workflows are unchanged.

## Website integration

The public repository records processing scripts and reusable templates rather
than the generated website or chart archive. The reusable helper is maintained
at [`scripts/website/chart-downloads.php`](../scripts/website/chart-downloads.php).

1. Copy the helper to `website/public_html/includes/chart-downloads.php` in the
   website checkout. Its filesystem root is resolved relative to that installed
   location.
2. Load it once from the shared header:

   ```php
   require_once __DIR__ . '/chart-downloads.php';
   ```

3. Under each displayed SVG chart, render the download row:

   ```php
   renderChartDownloads($basePath . $file);
   ```

   URLs must be rooted at `/charts/`. The helper offers the sibling `.png`,
   `.svg` and `_data.csv` files only when they are present and readable. It
   escapes URLs and filenames and checks resolved files remain inside the
   website root. Downloaded filenames include the dataset and period folders.

4. Where a chart uses a shared or differently named CSV, pass that URL explicitly.
   The two historical AusTender overview charts share the official annual
   statistics file:

   ```php
   renderChartDownloads($trendBasePath . $file, $trendBasePath . $trendCsvFile);
   ```

5. Retain the existing underlying-value tables and source notes. Remove the
   superseded standalone CSV button where the new row already supplies it.
   Download buttons wrap on narrow screens. The installed site also constrains
   chart-grid gutters on mobile:

   ```css
   @media (max-width: 575.98px) {
       .row.g-5:has(.card-img-top) { --bs-gutter-x: 1.5rem; }
   }
   ```

ABS's quarterly-derived summary is stored as static HTML. Its generator,
`scripts/abs_gfs/quarterly_gfs.py`, writes equivalent PNG/SVG/CSV links directly
into the summary rather than placing PHP calls in a file read as static content.
The NDIS page retains its existing download controls.

## Implementation and validation record

The maintained website checkout was updated and byte-verified on 19 October
2026. The archive backfill covered 1,343 displayed charts across the nine dataset
collections, plus two assets in an existing duplicate folder. All existing SVG
and CSV contents were preserved. One ARC program chart's stored output PNG
differed from the displayed SVG; its PNG was exported from that exact SVG.

| Check | Result |
| --- | --- |
| Local routes visited | 263 |
| Available chart pages checked | 249 |
| Displayed chart instances checked | 1,343 |
| Unique local download targets checked | 4,030, all present |
| Representative HTTP exports retrieved and byte-checked | 27, spanning PNG/SVG/CSV in all nine collections |
| PHP syntax and edited Python syntax | Passed |
| Desktop layout and 390px mobile layout | Passed |
| Actual browser PNG download and file comparison | Passed |
| Medicare overview rebuild and PNG/SVG/CSV website copy | Passed |
| Installed file verification | 1,379 files byte-verified |

These are local implementation checks, not an independent audit of each source
dataset or proof of a production deployment. The temporary PHP 8.4 preview
enabled `mbstring` and suppressed existing CSV-escape deprecation notices. Three
existing GrantConnect financial-year routes returned 404: FY2026-27, FY2018-19
and FY2017-18. The update did not change those navigation routes or their source
coverage rules.

The local installation receipt is
`output/validation/chart_downloads_latest.json`. Generated assets and local
reports remain outside GitHub. Website publication follows the maintainer's
existing staging and sync workflow; include PNG files in the transfer filter.
