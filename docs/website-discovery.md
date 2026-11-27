# About page, footer and sitemap maintenance

Updated 13 November 2026.

The About page reads topic titles, descriptions and links from `website/public_html/includes/datasets.json` through the existing `dataset-info.php` helper. It no longer maintains a separate four-source list. The shared footer exposes About, methodology, code and issue-reporting links on every page.

## Regenerate the sitemap with a release

From the maintained project, using PHP with mbstring available:

```powershell
python scripts/website/build_sitemap.py --web-root website/public_html --php C:/path/to/php.exe --report output/validation/website-sitemap.json
```

The builder runs the website release check once, then writes `website/public_html/sitemap.xml` only if there are no errors or warnings. It includes the verified canonical URLs, retains reporting-period query strings and removes duplicate aliases. Non-success PHP response statuses fail the check. Raw chart/data files and unlinked query combinations are not sitemap entries. The crawler follows navigation from the homepage, transparency and search, so new public pages must also be linked in the site.

No last-modified dates are guessed from generation time or filesystem timestamps. A sitemap build date is not a source-data update date. The existing `robots.txt` already advertises the sitemap URL and does not need changing.

Upload the regenerated sitemap with the corresponding pages and data. Verify the live sitemap after normal website sync. A sitemap supports discovery but does not guarantee indexing or search ranking. See [Google's sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).

Run the small regression suite after changing sitemap behavior:

```powershell
python -m unittest discover -s scripts/website -p test_build_sitemap.py -v
```

The source repository does not contain the complete deployed PHP tree or generated chart assets. Running the release checker or sitemap builder requires the maintained website copy with those inputs. These commands are maintainer tools, not a promise that a bare public checkout recreates the live site.
