# Have your say on public spending

APET helps readers understand government expenditure and form their own views. The participation guide connects that purpose to a practical next step: identify the responsible representative, check the evidence, make a specific request and follow up.

The first version was implemented and installed in the maintained website source on 9 November 2026. This document and its linked source files preserve the feature independently of the original working discussion.

## Editorial and product decisions

- Use the title **Have your say on public spending** and the expenditure-page link **Ask your representative about this spending**.
- Support readers who want expenditure reduced, increased, redirected, protected or better explained. APET does not select a policy position or endorse a party.
- Distinguish federal, state/territory and council responsibilities, explain shared responsibilities, and account for the ACT's combined territory/local functions.
- Link to official representative directories and government or local-government-association council directories rather than maintaining individual politicians' names and email addresses. A postcode alone can identify more than one electorate.
- Explain that a large amount alone does not establish waste. Encourage questions about outcomes, alternatives, evaluations and value for money.
- Keep actual expenses/payments, budgets, forecasts, grant allocations and contract award values distinct. Preserve period, units, coverage, source and limitations. Do not add overlapping reporting periods or overlapping datasets. NDIS participant-state groupings are not state-government expenditure totals.
- Encourage one issue and one concrete request in the reader's own words. Include follow-up, council consultations, parliamentary inquiries and petitions. A letter does not guarantee a reply or policy change.
- The suggested two-to-four-week follow-up interval is practical advice, not an official response deadline.

## Preserved source

The public repository keeps reusable website code rather than the generated chart/site archive. Install these files into the **existing** PHP website:

| Repository source | Website destination |
| --- | --- |
| [`scripts/website/have-your-say/have-your-say.php`](../scripts/website/have-your-say/have-your-say.php) | `public_html/have-your-say.php` |
| [`scripts/website/have-your-say/have-your-say.css`](../scripts/website/have-your-say/have-your-say.css) | `public_html/have-your-say.css` |
| [`scripts/website/have-your-say/have-your-say.js`](../scripts/website/have-your-say/have-your-say.js) | `public_html/js/have-your-say.js` |

The page expects `includes/header.php`, `includes/footer.php`, the existing `/style.css` and branding assets. The shared header loads Bootstrap 5.3.7 CSS and uses `$pageTitle` and `$pageDescription`; the shared footer loads the Bootstrap JavaScript bundle. The tested local PHP version was 8.4.26. These files are an addition to the existing website, not a standalone copy of the entire site.

The browser editor has no server submission, tracking, draft persistence or automatic sending. Visitors must copy or download their draft before leaving and send it through the recipient's official contact method. Clipboard writing requires browser support and a secure context; otherwise the control selects the text for manual copying. The letter downloads as UTF-8 plain text. Without JavaScript, readers can edit and manually copy the textareas. Print handling expands disclosure sections and renders the current text of both editors.

The figures-and-source worksheet is manually completed. It does not automatically retrieve, verify or prefill a chart's values.

## Integration with the existing site

Apply the following additions to the current shared files. Preserve unrelated changes and do not replace a newer header, footer, homepage or sitemap with an old full-file snapshot. First check whether each addition is already present.

### Navigation

Add this item to the shared main navigation, after Search:

```html
<li class="nav-item"><a class="nav-link" href="/have-your-say.php">Have your say</a></li>
```

Add a visible link inside the shared footer:

```html
<p><a class="text-light" href="/have-your-say.php">Have your say on public spending</a></p>
```

### Expenditure-page callout

Insert this before the shared footer's `<footer>` element. It provides one callout for all ten expenditure sections, including nested annual/quarterly pages, without modifying each page generator. It uses only the request path, so a search query mentioning a dataset does not trigger the callout.

```php
<?php
$engagementPath = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
if (preg_match('~^/(ipea|austender|grantconnect|arc-grants|pbs|mbs|hospital-funding|ndis|foreign-aid|abs-gfs)(/|$)~', $engagementPath)):
?>
<aside class="container my-4" aria-label="Have your say on public spending">
    <div class="card border-start border-4 border-dark shadow-sm"><div class="card-body p-4">
        <h2 class="h4">Have a question about this spending?</h2>
        <p>Use the figures and original sources on this page to explain your priorities and ask for a clear response.</p>
        <a class="btn btn-outline-dark" href="/have-your-say.php">Ask your representative about this spending</a>
    </div></div>
</aside>
<?php endif; ?>
```

Standalone chart images and static chart-summary files do not gain navigation automatically. Include any future expenditure section in the route expression if it uses the same shared footer.

### Homepage

Add this below the dataset-card grid, inside the main content container:

```html
<section class="card shadow-sm mt-5" aria-labelledby="have-your-say-title"><div class="card-body p-4 p-md-5">
<h2 id="have-your-say-title" class="h3">Have your say on public spending</h2>
<p>Public money involves choices. Find the right representative, use the evidence, and write a clear request about what matters to you.</p>
<a class="btn btn-dark" href="/have-your-say.php">Read the practical guide</a>
</div></section>
```

### Sitemap

Add the guide to the existing XML `urlset`, using the date of the actual content update:

```xml
<url><loc>https://auspublicexp.org/have-your-say.php</loc><lastmod>2026-11-09</lastmod></url>
```

## Verification record and publication

The 9 November 2026 local implementation record reported:

| Check | Result |
| --- | --- |
| PHP and JavaScript syntax | Passed |
| PHP-rendered guide, internal links, fragment targets, unique IDs and editor labels | Passed |
| Shared-footer routing | 25 cases passed: 20 expenditure paths and five non-matching paths |
| Responsive layout | Inspected at 390, 1024 and 1280 pixels; no horizontal overflow reported |
| Homepage guide link and mobile navigation | Passed |
| Letter and evidence-note copy controls | Clipboard text matched the edited test text |
| Letter download | Downloaded plain-text content matched the edited test draft |
| Browser console | No errors observed during these checks |
| Local source installation | All seven changed/new website files byte-verified |

Print styling was implemented, but a physical printout was not tested. These are implementation checks, not an independent audit of expenditure data. The original local homepage matched the fetched live homepage apart from whitespace before the update.

The implementation session ended with the source installed locally and the upload prepared; it **did not deploy or verify publication of the new page**. Committing this source to GitHub does not publish it to the website. Confirm the current live state before deciding whether an upload is still needed.

For publication, back up the four existing shared files, copy the three new assets first, then apply the shared-header/footer, homepage and sitemap additions. Follow the [website operations guidance](website-operations.md) and existing WinSCP/SFTP process. Do not replace the entire site tree or enable remote deletion for this change. After upload, check `/have-your-say.php`, the homepage link, a dataset-page callout and the copy/download controls on the live site.

## Maintenance and possible later improvements

- Review representative/council directories and official participation guidance periodically; update the visible review date after checking them. The initial links were reviewed on 9 November 2026.
- Preserve neutral wording, accessibility labels, manual-copy fallback and the absence of draft collection.
- A future chart-level copy feature could carry the selected amount, units, reporting period, coverage, original source and APET link into a draft. It must preserve the distinction between payment, estimate and award values and be reviewed by the reader before sending.
- A future electorate finder must handle ambiguous postcodes and boundary changes. The first version intentionally delegates lookup to official services.
- Keep local installers, personal filesystem paths, test downloads, rendered HTML, screenshots, backups and deployment ZIPs outside the public source repository. The source and integration instructions above are sufficient to recreate this feature without the chat.
