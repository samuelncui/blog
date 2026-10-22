# Deployment checks for blog.cui.to

The repository is public and the configured production origin is `https://blog.cui.to/`. GitHub Pages uses this custom domain with HTTPS enforced. The Cloudflare `blog` CNAME is proxied to `samuelncui.github.io`.

Configure Settings → Pages to use GitHub Actions and `blog.cui.to` as the custom domain. Preserve existing domain-verification TXT records. Run **Build Hugo** manually with **publish** selected and **preview** disabled (the default) to build, validate and deploy the site. Pushes and pull requests only validate; they never publish.

On 2026-10-23, six ordered Cloudflare Single Redirects were enabled in the `samcui.com` zone; their exact settings are recorded in `cloudflare-redirects.json`. They match only the HTTP host `samcui.com` or `www.samcui.com`, preserve query strings, and return HTTP 301 directly to the final destination. Exceptions handle legacy feeds, sitemaps, Uncategorized archives, and the two originally English posts. All other paths retain their path on the new domain. The rules do not match NAS subdomains or requests addressed to `cui.to`. Keep the old domain and redirects for at least one year, preferably longer while old links receive traffic; the Cloudflare edge redirect does not require the old WordPress process.

The existing `cui.to` homepage itself redirects to `https://samcui.com/`; that configuration was left unchanged, so its homepage now follows the additional hop to the new blog.

Live verification covered 89 old-URL cases, including all 34 migrated content paths, both protocols and host variants, query strings, pagination, images, feeds, and sitemaps. All returned the expected 301. The new site's 68 bilingual content URLs returned HTTP 200 with the new canonical, reciprocal language links, and indexable metadata. Excluded `/resume/` and `/ciba/` still return a real 404 at the new origin.

GitHub Pages serves static files; it does not apply `_redirects`, Nginx rules or this JSON file. Configure `redirects.json` as actual HTTP redirects at the serving edge where applicable. In particular, `/feed/` must redirect to the real XML feed, rather than serving RSS as `text/html`. Preserve incoming query strings unless the specific endpoint requires otherwise.

Check these on the final public hostname:

- HTTPS works, HTTP redirects to HTTPS, the preferred hostname is `blog.cui.to`, and trailing-slash behavior does not create redirect loops.
- All 34 migrated content URLs, the original Public category and both original tag URLs return HTML with the expected canonical. On the old domain, the former Uncategorized path returns HTTP 301 to `/post/` (and `/en/post/` for its English counterpart); the new host's static aliases provide a fallback. Homepage pagination `/page/2/` through `/page/4/` returns its own canonical and distinct article lists.
- `/robots.txt`, `/sitemap_index.xml`, `/sitemap.xml`, `/post-sitemap.xml`, `/page-sitemap.xml`, `/category-sitemap.xml`, `/index.xml`, and `/baidu_verify_9NJwD4K5q5.html` work with correct HTTP content types.
- Unknown paths return an actual HTTP 404. Excluded `/resume/` and `/ciba/` stay excluded; their SEO presence is deliberately not preserved.
- The old monthly `/post/YYYY/MM/` URLs already redirect to the homepage in the current WordPress site, so they are not recreated as invented archive pages. Review external/search links before deciding whether additional targeted redirects are warranted.
- Preserve Search Console ownership: the old domain retains DNS verification; `https://blog.cui.to/` is verified using the public HTML meta tag configured in `hugo.toml`. Do not remove it. The new `sitemap_index.xml` was submitted and successfully read on 2026-10-23. Google accepted separate Change of Address requests from `samcui.com` and `www.samcui.com` to `blog.cui.to`; these cover both source protocols without moving other subdomains. Indexing and ranking updates are asynchronous. The root-domain pre-check passed, although Google temporarily could not fetch three optional sample URLs; independent requests followed all three to HTTP 200 destinations.
- Install giscus only for this repository when publication is approved, then verify actual comment loading and replies. Synchronize its iframe theme with Stack's manual dark-mode switch; the current `preferred_color_scheme` setting follows the OS preference only.

RSS currently contains post summaries and links; WordPress comment feeds and WordPress API/admin endpoints are not migrated. Native giscus comments are loaded separately and are not static article HTML; do not assume they contribute the same indexed text as the old WordPress comment section.

Production publication defaults to `preview=false`. For a temporary default-domain deployment without the custom hostname, enable `preview` to serve local links at `https://samuelncui.github.io/blog/` with `noindex`. The workflow does not change DNS.
