# Website operations and first-release decisions

This document preserves website setup choices from APET's June 2026 rollout. It is a **historical operations note**, not a representation of every aspect of the current live site. See the [README](../README.md), dataset methodology files and [chart-download documentation](chart-downloads.md) for current behavior.

## Hosting and architecture

- Public site: https://auspublicexp.org/ ; X account: https://x.com/auspublicexp.
- Domain registered with Cloudflare, which handles DNS; the website was hosted through Hostinger Premium Web Hosting.
- Initial frontend: custom PHP/HTML with Bootstrap 5, without WordPress or a database-backed web application.
- Shared includes (includes/header.php and includes/footer.php) supplied the document head, navbar, branding and footer across pages. Nested pages used relative filesystem include paths, while web assets used root-relative URLs such as /style.css and /images/logo.png.
- Charts and reporting-period navigation were rendered from PHP arrays/loops rather than repeated hand-written cards.
- Project navigation had IPEA, AusTender, GrantConnect, About and X; the footer linked official sources and displayed a concise independent-project disclaimer.
- The original chart gallery used responsive two-column Bootstrap cards opening full-size PNGs. The site later gained SVG/PNG/CSV downloads: use [chart-download documentation](chart-downloads.md) for that newer implementation.

## Reporting period conventions

- Australian financial-year quarters: Q1 = July–September, Q2 = October–December, Q3 = January–March, Q4 = April–June.
- IPEA source CSV filenames encode calendar quarters. 2024q03_dataextract.csv (July–September 2024) corresponds to FY2024-25 Q1; 2026q01_dataextract.csv (January–March 2026) corresponds to FY2025-26 Q3.
- The first site used financial-year paths such as /ipea/fy2024_25/q1.php and matching chart directories under /charts/ipea/fy2024_25/q1/.
- Annual reporting must be labelled according to the period actually represented by the source and script. Early calendar-year annual pages should not be assumed equivalent to financial-year annual reports. The current [IPEA methodology](ipea-methodology.md) describes the subsequent annual pipeline.
- Do not force every dataset into both quarterly and annual pages or show unavailable historical periods as 'Coming Soon'. Only link to available, published pages.

## Local editing and publishing

- Original deployment used WinSCP over SFTP/SSH, with Hostinger-provided host, port, username and authentication settings. Never commit server access details or credentials.
- Keep a local website copy, edit and test locally, review a synchronization preview, then transfer local changes to Hostinger. Use local-to-remote synchronization and leave remote deletion disabled unless intentional.
- Source datasets, chart-generation outputs and X post-caption archives are separate from the deployable web assets. The original publishing archive grouped charts, supporting CSV and captions by Post ID; site assets were copied into a separate website tree.
- A browser hard refresh (Ctrl+F5) may be needed after CSS updates because of caching. Intentional stylesheet query-version changes can help with releases.
- For current chart mirroring and downloads, consult [chart-download documentation](chart-downloads.md).

## Search discovery and social cards

- Google Search Console domain ownership was verified via Cloudflare DNS in June 2026; the first sitemap.xml was submitted successfully, and the homepage and selected landing pages were requested for indexing. These actions do not guarantee indexing.
- The original robots.txt configuration was:

```text
User-agent: *
Allow: /

Sitemap: https://auspublicexp.org/sitemap.xml
```

- The shared head included a page description, Open Graph tags, X summary-large-image metadata and a PNG favicon. The initial image used for previews was /images/banner.png.
- Page-specific HTML titles and descriptions were identified as a future improvement because one shared header otherwise gives every page the same title. When implementing, pass metadata to the header before including it and escape dynamic HTML output. Verify whether the current website already implements this before creating work.
- A responsive collapsed Bootstrap navigation menu used the Bootstrap JavaScript bundle.

## Data integrity and editorial policy

The website is the primary public archive; social media posts and replies are manually reviewed rather than automatically published. Include source citations and material reporting limitations, particularly the difference between reported contract/grant amounts and actual payments. See [editorial and social-media policy](editorial-social-media-policy.md) and dataset-specific methodology documents.

These notes preserve the original implementation decisions for future maintainers. They are not a substitute for inspecting current hosting configuration, live website files or source-processing scripts.

## Historical AusTender quarterly publication checklist

The July 2026 manual sequence for checking weekly exports, generating quarterly charts, allocating Buffer Post IDs, synchronising PNGs with WinSCP, copying a quarter PHP page and enabling the yearly navigation link is preserved in the [AusTender quarterly publishing workflow — July 2026 reference](austender-quarterly-publishing-workflow-2026-07.md). That note is historical; use current scripts, templates and chart-download support for new releases.
