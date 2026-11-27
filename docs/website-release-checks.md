# Website release checks

Added 13 November 2026. Run from the maintained project using its Python environment and a PHP CLI with mbstring available:

```powershell
python scripts/website/check_release.py --web-root website/public_html --php C:/path/to/php.exe --output output/validation/website-release.json
```

The checker renders PHP routes reachable from the homepage, transparency and search pages. It checks runtime failures, local link/asset targets, same-page fragments, duplicate IDs, page titles/descriptions, image alternative-text attributes and the skip-link target. Review warnings as well as the exit code. The report records all rendered URLs. The route limit is 600; review growth before raising it.

This is a local release check, not a live-site, accessibility or data-accuracy certification. It does not run JavaScript, validate external links, test search interactions or judge alternative-text quality. Test keyboard navigation and representative small-screen layouts in a browser, then verify the live site after upload. Existing PHP 8.4 fgetcsv escape-parameter deprecations are excluded; other runtime errors fail the check.

Run the checker only against a trusted local site tree. It executes the site's PHP as the local user; rejecting entry points that resolve outside the website root is not a PHP sandbox.

## Period titles and shared metadata

`website/public_html/includes/period-metadata.php` derives titles, descriptions and canonical URLs from supported period queries and existing chart folders. The shared header uses these defaults only when a page has not supplied its own metadata. Canonical URLs retain the selected period, and Open Graph/Twitter metadata use the same values.

`includes/datasets.json` has an optional `partial_periods` list using folder keys, for example `FY2026-27_Q2`. Review this list with every relevant refresh. It labels period metadata as partial; it does not decide whether charts are eligible for publication.

GrantConnect's financial-year navigation discovers the available quarter folders rather than maintaining a separate hardcoded year list. Source completeness is determined by the data pipeline, not by the presence of a folder.

## Keyboard and table access

The header's first focusable link skips repeated navigation and the banner. Visible focus outlines are defined in `style.css`. The ABS overview reads its existing chart CSVs through `abs-gfs/_overview-data.php`, with table captions, column/row headings and horizontally scrollable regions. Fractions in purpose shares and growth are displayed as percentages; amounts retain the CSV's AUD-million unit. These changes add no chart controls or JavaScript.

The November 2026 package passed 278 rendered routes, including repaired GrantConnect financial-year links. Browser checks covered the skip link and an expanded ABS table at narrow widths, plus the repaired FY2026–27 summary. Full desktop, screen-reader and all-device testing remain separate checks.

## Sitemap and discovery

Use `scripts/website/build_sitemap.py` when preparing a publication. It runs the release check and writes the sitemap only after an error-free and warning-free result. See [Website discovery](website-discovery.md) for the command and scope. The checker now rejects non-success PHP HTTP status codes, including pages that render an error message without a PHP exception.
