# Deployment checks before DNS cutover

Public release is approved. Pages setup and deployment do not change DNS, Cloudflare rules or the live WordPress origin.

After the owner approves publication, make the reviewed repository public and configure Settings → Pages to use GitHub Actions. Add `samcui.com` as the custom domain and preserve any existing domain-verification TXT records. Run **Build Hugo** manually with **publish** selected to build, validate and deploy the site. Pushes and pull requests only validate; they never publish. Keep the production DNS unchanged until the Pages deployment is ready, then configure the edge redirects and point the domain to Pages. Verify the actual domain and HTTPS before retiring the WordPress origin.

GitHub Pages serves static files; it does not apply `_redirects`, Nginx rules or this JSON file. Configure `redirects.json` as actual HTTP redirects at the existing Cloudflare edge before cutover. In particular, `/feed/` must redirect to the real XML feed, rather than serving RSS as `text/html`. Preserve incoming query strings unless the specific endpoint requires otherwise.

Check these on the final public hostname:

- HTTPS works, HTTP redirects to HTTPS, the preferred hostname stays `samcui.com`, and trailing-slash behavior does not create redirect loops.
- All 34 migrated content URLs, the original Public category and both original tag URLs return HTML with the expected canonical. The former Uncategorized path must return HTTP 301 to `/post/` (and `/en/post/` for its English counterpart); the static aliases provide a preview fallback. Homepage pagination `/page/2/` through `/page/4/` returns its own canonical and distinct article lists.
- `/robots.txt`, `/sitemap_index.xml`, `/sitemap.xml`, `/post-sitemap.xml`, `/page-sitemap.xml`, `/category-sitemap.xml`, `/index.xml`, and `/baidu_verify_9NJwD4K5q5.html` work with correct HTTP content types.
- Unknown paths return an actual HTTP 404. Excluded `/resume/` and `/ciba/` stay excluded; their SEO presence is deliberately not preserved.
- The old monthly `/post/YYYY/MM/` URLs already redirect to the homepage in the current WordPress site, so they are not recreated as invented archive pages. Review external/search links before deciding whether additional targeted redirects are warranted.
- Preserve Search Console ownership (prefer existing DNS verification), submit the sitemap, and check indexing, security issues and manual actions after cutover. No Search Console access or indexing/ranking verification has been performed.
- Install giscus only for this repository when publication is approved, then verify actual comment loading and replies. Synchronize its iframe theme with Stack's manual dark-mode switch; the current `preferred_color_scheme` setting follows the OS preference only.

RSS currently contains post summaries and links; WordPress comment feeds and WordPress API/admin endpoints are not migrated. Native giscus comments are loaded separately and are not static article HTML; do not assume they contribute the same indexed text as the old WordPress comment section.

Until a custom domain is configured, publish with `preview` enabled (the default) to serve working local links at `https://samuelncui.github.io/blog/` with `noindex`. After custom-domain setup, disable `preview` for the production deployment. Neither option changes DNS.
