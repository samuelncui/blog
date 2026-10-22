# Deployment checks for blog.cui.to

The repository is public and the configured production origin is `https://blog.cui.to/`. The owner has approved binding this subdomain and its DNS to GitHub Pages. Verify the live Pages/domain/DNS state separately; `cui.to` and `samcui.com` are outside this cutover.

Configure Settings → Pages to use GitHub Actions and `blog.cui.to` as the custom domain. Preserve existing domain-verification TXT records. Run **Build Hugo** manually with **publish** selected and **preview** disabled (the default) to build, validate and deploy the site. Pushes and pull requests only validate; they never publish. Configure only the `blog` DNS record for this cutover, then verify the actual hostname and HTTPS. The old WordPress origin and samcui.com redirects remain a separate migration step.

GitHub Pages serves static files; it does not apply `_redirects`, Nginx rules or this JSON file. Configure `redirects.json` as actual HTTP redirects at the serving edge where applicable. In particular, `/feed/` must redirect to the real XML feed, rather than serving RSS as `text/html`. Preserve incoming query strings unless the specific endpoint requires otherwise.

Check these on the final public hostname:

- HTTPS works, HTTP redirects to HTTPS, the preferred hostname is `blog.cui.to`, and trailing-slash behavior does not create redirect loops.
- All 34 migrated content URLs, the original Public category and both original tag URLs return HTML with the expected canonical. The former Uncategorized path must return HTTP 301 to `/post/` (and `/en/post/` for its English counterpart); the static aliases provide a preview fallback. Homepage pagination `/page/2/` through `/page/4/` returns its own canonical and distinct article lists.
- `/robots.txt`, `/sitemap_index.xml`, `/sitemap.xml`, `/post-sitemap.xml`, `/page-sitemap.xml`, `/category-sitemap.xml`, `/index.xml`, and `/baidu_verify_9NJwD4K5q5.html` work with correct HTTP content types.
- Unknown paths return an actual HTTP 404. Excluded `/resume/` and `/ciba/` stay excluded; their SEO presence is deliberately not preserved.
- The old monthly `/post/YYYY/MM/` URLs already redirect to the homepage in the current WordPress site, so they are not recreated as invented archive pages. Review external/search links before deciding whether additional targeted redirects are warranted.
- Preserve Search Console ownership (prefer existing DNS verification), submit the sitemap, and check indexing, security issues and manual actions after cutover. The old domain’s Search Console was reviewed separately; ownership and indexing for the new hostname still need verification.
- Install giscus only for this repository when publication is approved, then verify actual comment loading and replies. Synchronize its iframe theme with Stack's manual dark-mode switch; the current `preferred_color_scheme` setting follows the OS preference only.

RSS currently contains post summaries and links; WordPress comment feeds and WordPress API/admin endpoints are not migrated. Native giscus comments are loaded separately and are not static article HTML; do not assume they contribute the same indexed text as the old WordPress comment section.

Production publication defaults to `preview=false`. For a temporary default-domain deployment without the custom hostname, enable `preview` to serve local links at `https://samuelncui.github.io/blog/` with `noindex`. The workflow does not change DNS.
