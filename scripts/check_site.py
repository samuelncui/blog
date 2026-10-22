"""Check migrated URLs, images, canonical URLs and executable content using stdlib."""
import json
import pathlib
import sys
import subprocess
import re
import hashlib
import base64
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'public')
repo = pathlib.Path(__file__).resolve().parents[1]
errors = []
config = json.loads(subprocess.run(
    ['hugo', 'config', '--format', 'json'], cwd=repo,
    check=True, capture_output=True, text=True,
).stdout)['params']['giscus']
widget_attrs = {
    'src': 'https://giscus.app/client.js',
    'data-repo': config['repo'],
    'data-repo-id': config['repoid'],
    'data-category': config['category'],
    'data-category-id': config['categoryid'],
    'data-strict': '1',
    'data-reactions-enabled': '1',
    'data-emit-metadata': '0',
    'data-input-position': 'bottom',
    'data-theme': 'preferred_color_scheme',
    'data-lang': 'zh-CN',
    'data-loading': 'lazy',
    'crossorigin': 'anonymous',
    'async': None,
}

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonical = []
        self.images = []
        self.links = []
        self.h1 = 0
        self.backlinks = []
        self.widgets = []
        self.videos = []
        self.script = None
        self.pagination_dialog = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1':
            self.h1 += 1
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical.append(attrs.get('href'))
        if tag == 'meta' and attrs.get('name') == 'giscus:backlink':
            self.backlinks.append(attrs.get('content'))
        if tag == 'img':
            self.images.append(attrs.get('src', ''))
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        if tag == 'dialog':
            self.pagination_dialog = attrs == {'id': 'pagination-jump-dialog', 'aria-labelledby': 'pagination-jump-title'}
        if tag == 'form' and not (self.pagination_dialog and attrs == {'method': 'dialog', 'class': 'pagination-jump-form'}):
            errors.append('Unexpected active HTML: form')
        if tag == 'iframe':
            self.videos.append(attrs)
        if tag in {'object', 'embed'}:
            errors.append(f'Unexpected active HTML: {tag}')
        if tag == 'script':
            self.script = 'other'
            if attrs == {'type': 'application/ld+json'}:
                self.script = 'json'
            elif attrs.get('src') == 'https://giscus.app/client.js':
                self.script = 'giscus'
                self.widgets.append(attrs)
            elif re.fullmatch(r'/(?:ts/(?:main|scheme)|js/photoswipe\.min)\.[0-9a-f]{64}\.js', attrs.get('src', '')):
                # Only the reviewed, local Stack UI entry points are allowed.
                src = attrs['src']
                script_file = root / src.lstrip('/')
                if not script_file.is_file():
                    errors.append(f'Missing local theme script: {src}')
                    return
                digest = hashlib.sha256(script_file.read_bytes()).digest()
                integrity = 'sha256-' + base64.b64encode(digest).decode()
                expected = {'src': src, 'integrity': integrity}
                if src.startswith('/ts/main.'):
                    expected.update({'type': 'text/javascript', 'defer': None})
                elif src.startswith('/js/photoswipe.min.'):
                    expected['type'] = 'module'
                if attrs != expected or digest.hex() not in src:
                    errors.append(f'Invalid local theme script fingerprint or attributes: {src}')
                self.script = 'theme'
            else:
                errors.append('Unexpected executable script')
        language_switch = tag == 'select' and attrs == {
            'name': 'language', 'title': 'language',
            'onchange': 'window.location.href = this.selectedOptions[0].value',
        }
        if any(k.startswith('on') for k in attrs) and not language_switch:
            errors.append('Unexpected event handler')
        for k in ('href', 'src'):
            if urlsplit(attrs.get(k, '')).scheme.lower() in {'javascript', 'data', 'vbscript'}:
                errors.append('Unexpected URL scheme')

    def handle_data(self, data):
        if self.script in {'giscus', 'theme'} and data.strip():
            errors.append('Unexpected inline script body')

    def handle_endtag(self, tag):
        if tag == 'dialog':
            self.pagination_dialog = False
        if tag == 'script':
            self.script = None

mapping = json.loads((repo / 'migration/urls.json').read_text())
translations = json.loads((repo / 'migration/translations.json').read_text())
mapping += [{'path': row['paths']['en'], 'source': row['sources']['en']} for row in translations]
expected_widgets = {}
expected_videos = {}
for row in mapping:
    target = root / row['path'].strip('/') / 'index.html'
    if not target.is_file():
        errors.append(f'Missing migrated route: {row["path"]}')
        continue
    page = Page()
    page.feed(target.read_text())
    front, _ = json.JSONDecoder().raw_decode((repo / row['source']).read_text())
    if front.get('youku'):
        assert front['youku'] in {'XNjAxNDc0NTE2', 'XNDA5MDY0ODE2', 'XNjI5MzQzNjg0'}
        expected_videos[target] = [{
            'src': 'https://player.youku.com/embed/' + front['youku'],
            'title': front['title'],
            'allow': 'fullscreen; encrypted-media; picture-in-picture',
            'allowfullscreen': None,
            'referrerpolicy': 'strict-origin-when-cross-origin',
        }]
        if 'https://v.youku.com/v_show/id_' + front['youku'] + '.html' not in page.links:
            errors.append(f'Missing Youku fallback link: {row["path"]}')
    if config['enabled'] and front.get('comments') is not False:
        attrs = dict(widget_attrs)
        number = front.get('giscusDiscussion')
        attrs['data-lang'] = 'en' if row['path'].startswith('/en/') else 'zh-CN'
        attrs['data-mapping'] = 'number' if number else ('specific' if front.get('giscusPath') else 'pathname')
        if number:
            attrs['data-term'] = str(number)
        elif front.get('giscusPath'):
            attrs['data-term'] = front['giscusPath']
        expected_widgets[target] = attrs
    expected = 'https://samcui.com' + row['path']
    if page.backlinks != page.canonical:
        errors.append(f'Giscus backlink mismatch: {row["path"]}')
    if len(page.canonical) != 1 or unquote(page.canonical[0]) != expected:
        errors.append(f'Canonical mismatch: {row["path"]}')
    if page.h1 != 1:
        errors.append(f'Heading mismatch: {row["path"]}')

for target in root.rglob('*.html'):
    page = Page()
    page.feed(target.read_text())
    if page.videos != expected_videos.get(target, []):
        errors.append(f'Unexpected video iframe: {target.relative_to(root)}')
    expected_widget = expected_widgets.get(target)
    if page.widgets != ([expected_widget] if expected_widget else []):
        errors.append(f'Giscus widget mismatch: {target.relative_to(root)}')
    for src in page.images:
        url = urlsplit(src)
        if url.scheme or url.netloc:
            errors.append(f'External image remains: {target.relative_to(root)}')
        elif not (root / unquote(url.path).lstrip('/')).is_file():
            errors.append(f'Missing image: {target.relative_to(root)}')
    for link in page.links:
        url = urlsplit(link)
        if url.scheme or url.netloc or not url.path.startswith('/'):
            continue
        path = root / unquote(url.path).lstrip('/')
        if not path.is_file() and not (path / 'index.html').is_file():
            errors.append(f'Broken internal link in {target.relative_to(root)}: {url.path}')

for required in ('index.html', 'index.xml', 'sitemap.xml', 'robots.txt', '404.html'):
    if not (root / required).is_file():
        errors.append(f'Missing {required}')

if errors:
    print('\n'.join(sorted(set(errors))), file=sys.stderr)
    sys.exit(1)
print(f'OK: {len(mapping)} migrated URLs, internal links, images, canonical URLs, giscus configuration and active HTML checks')
