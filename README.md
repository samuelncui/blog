# SamCui Computing

Hugo source for https://samcui.com/. Public articles and referenced images only.

## Local use

Install Hugo **0.168.0** and the standalone Dart Sass **1.106.1** executable on `PATH`, then run:

```sh
hugo server --buildDrafts
```

Production build and checks:

```sh
hugo --panicOnWarning
python3 scripts/check_site.py public
python3 scripts/check_seo.py public
python3 scripts/check_languages.py public
```

The generated `public/` directory is not committed. GitHub Actions validates ordinary pushes and pull requests. Publication requires a manual **Build Hugo** run with **publish** selected after approval and Pages setup; domain cutover is separate.

## Content

- `content/post/`: 33 articles in both Chinese and English, with explicit original paths.
- `content/pages/`: one public biography in both languages.
- `static/wp-content/uploads/`: seven referenced images at their original paths; metadata removed.
- `themes/stack/`: vendored Stack v4.0.3, with its original GPL-3.0 license and source.
- `layouts/`, `assets/`: Stack adaptations, reviewed SEO, local avatar and legacy code styling. The theme uses its default Lato font and optional PhotoSwipe viewer; the existing giscus integration preserves historical discussions.
- `migration/urls.json`: original public URL mapping.
- `migration/seo.json`: reviewed original SEO metadata and taxonomy URL baseline.
- `deployment/`: required HTTP redirects and final-host checks; these are not applied automatically.

Imported articles are reviewed HTML to preserve code and rendered tables. New articles may use Markdown. Keep secrets, private posts, unpublished drafts, contact QR codes, database exports and server configuration outside this public repository and its Git history.

## Migration review (2026-10-22)

- Only published, password-free posts/pages were considered; users, comments, credentials and WordPress configuration were excluded.
- Two contact-heavy pages were excluded at the owner's request.
- Two obfuscated external-script loaders were removed from an old article. Event handlers and active embedded content were also excluded.
- One unavailable legacy third-party image is represented by a labeled link to its original location.
- Text, source links, code examples and all referenced image files were reviewed; image metadata was removed.
- No database, PHP runtime or background server is needed to serve the generated site.

## Comments

Comments use GitHub Discussions in this same repository through giscus; there is no local comment server or database. Public release has been approved. Visitors can use giscus after the owner installs the app.

- Reviewed historical comments are posted by the site owner's GitHub account. Each body names the original display author and original UTC+8 timestamp, and explicitly identifies the post as an archival import. GitHub's author and creation time reflect the importer and import time.
- Email addresses, IP addresses, browser information, spam and pending comments are not published. Import files and credentials stay outside this repository.
- Existing imported threads use an explicit `giscusDiscussion` number in page front matter. Other pages use strict pathname matching. Preserve that number if a page is renamed.
- Replies continue in the same giscus discussion. Deep historical reply chains use links to the immediate original parent when GitHub cannot retain the original depth.
- `params.giscus.enabled` enables the widget; a page can opt out with `comments: false`. The widget lazy-loads and links directly to GitHub as a fallback. Only public repository/category identifiers are embedded, never API credentials.
- This repository's `giscus.json` controls allowed embedding origins and default ordering. Installing the giscus GitHub App on that repository is required for the widget to work.

This source does not deploy to the current production site or change DNS. Legacy attachment pages and WordPress plugin/admin endpoints are not migrated. Original tag paths and homepage pagination are preserved. The old Public category URL now serves Site Updates; the former Uncategorized URL redirects to the post archive. Apply the HTTP feed/sitemap redirects and complete the final-host checks in `deployment/README.md` before domain cutover.

## Theme adaptation (2026-10-22)

Uses [Stack v4.0.3](https://github.com/CaiJimmy/hugo-theme-stack/releases/tag/v4.0.3) by Jimmy Cai. The upstream theme and derived template/style adaptations retain GPL-3.0 licensing; this does not assign that license to the blog articles or photographs. Corresponding theme and adaptation source is included here. The official layout, typography and pagination are used directly. Technical overrides preserve reviewed SEO and per-article historical comment mappings, externalize theme initialization into fingerprinted local scripts, and compile the original styling with Dart Sass. Legacy WordPress code listings retain a small compatibility stylesheet. The sidebar avatar is a metadata-stripped local copy of the original public blog avatar.

Stack's stylesheet is compiled with Dart Sass. The style override silences only upstream Sass syntax deprecations (`import`, `global-builtin`, `color-functions`, `if-function`); other build warnings remain fatal.

## SEO verification (2026-10-22)

Compared all 34 migrated public pages with the live WordPress output. Original SEO titles are preserved in each article's original-language version; article timestamps are preserved in both versions. Chinese and English descriptions are manually authored summaries, reviewed against each article, and shared by article cards and SEO metadata. The output includes Open Graph/Twitter metadata, reviewed local share images, valid Article/WebPage/WebSite JSON-LD, multilingual sitemaps plus compatible old child-sitemap paths, image sitemap entries, robots crawl preferences and the public Baidu verification file. Each language's feed contains only the 33 posts.

The original Public category and both tag URLs are preserved; the former Uncategorized category has an archive redirect. Tags retain the source site's `noindex` policy. The homepage has four pages with distinct self-canonical URLs. Internal `/pages/` is not published; the two excluded contact pages are absent from sitemaps. `scripts/check_seo.py` validates these facts during every build.

This verifies generated files, not indexing or rankings. The `/feed/` HTTP redirect and final serving headers require deployment configuration; giscus comments are dynamically loaded and do not guarantee the same search indexing as WordPress's server-rendered comments.

## Chinese and English

Chinese pages retain the original unprefixed paths. English counterparts use `/en/` plus the same path. The two originally English posts keep their English source under `/en/` and have Chinese translations at the old paths. Stack's native language selector and article translation links connect the two versions. Menus, taxonomy labels, dates and comment interface follow the selected language; historical comment bodies retain their original wording.

Paired files use a common `translationKey`; migrated English files have the `.en.html` suffix. Update both versions when editing. Code, commands, links, measurements and model identifiers are preserved. The German quotation in the Chinese memorial post retains its original text with a separate Chinese rendering. `migration/translations.json` records language pairing and original code digests; preparation and review work stays outside the public repository.

Each post has one main category: Systems & Networking, Hardware & Devices, NAS & Storage, Development & Open Source, Campus Life, Life & Reflections, or Site Updates. Categories use the same bilingual-key convention under `content/categories/`. The legacy Uncategorized path aliases to the full post archive; deploy its actual HTTP 301 from `deployment/redirects.json`.

Each post has 2–4 subject tags. Both languages use identical taxonomy keys; files under `content/tags/` provide Chinese/English labels and stable URLs. Preserve existing keys when editing, and update tags on both language files. Tag indexes retain the source site's `noindex, follow` policy.

Both languages have self-canonical URLs, reciprocal `hreflang`, correct language metadata, RSS and sitemap entries. Both versions of an article use the same giscus discussion number or the same explicit source-path term; they never create separate language threads. `check_languages.py` validates the pairs, switching, code digests, shared comment mapping, feeds and sitemaps. Publication is approved; real giscus verification still requires the app installation.

The three historical Youku posts use Stack’s responsive video wrapper with HTTPS embeds and a direct watch link. Playback depends on Youku retaining and serving the original videos.

Image captions use semantic figure/figcaption markup. The favicon is a teal S monogram.

## Final public-release review (2026-10-22)

Reviewed all tracked files, reachable Git history and prior local revisions for secrets; gitleaks reported no findings. Checked image metadata and all 12 imported discussion threads. The original bilingual About page, photographs and contact address are retained at the owner’s request; the resume and lost-cat pages remain excluded. Publication is approved; production DNS cutover remains separate.

When publishing without a custom domain, the workflow’s default `preview` option prefixes local HTML links with `/blog/` and sets `noindex`. Production canonicals stay on samcui.com. Disable `preview` when deploying to the configured custom domain.
