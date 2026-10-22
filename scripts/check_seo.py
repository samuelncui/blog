"""Verify SEO output against the reviewed WordPress public-page baseline."""
import datetime
import hashlib
import json
import pathlib
import sys
import subprocess
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

repo = pathlib.Path(__file__).resolve().parents[1]
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'public').resolve()
baseline = json.loads((repo / 'migration/seo.json').read_text())
translations = json.loads((repo / 'migration/translations.json').read_text())
originals = {unquote(row['paths']['zh']): row['originalLanguage'] for row in translations}
pair_by_path = {unquote(row['paths']['zh']): row for row in translations}
config = json.loads(subprocess.run(
    ['hugo', 'config', '--format', 'json'], cwd=repo,
    check=True, capture_output=True, text=True,
).stdout)
origin = config['baseurl'].rstrip('/')
ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'i': 'http://www.google.com/schemas/sitemap-image/1.1'}

class Head(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta, self.links, self.schemas = {}, [], []
        self.title, self.title_open, self.schema_text = '', False, None
        self.alias, self.h1, self.anchors = False, 0, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'title':
            self.title_open = True
        if tag == 'h1':
            self.h1 += 1
        if tag == 'meta':
            key = a.get('name') or a.get('property')
            if key:
                assert key not in self.meta, f'Duplicate metadata: {key}'
                self.meta[key] = a.get('content', '')
            self.alias |= a.get('http-equiv', '').lower() == 'refresh'
        if tag == 'link':
            self.links.append(a)
        if tag == 'a':
            self.anchors.append(a.get('href', ''))
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.schema_text = ''

    def handle_data(self, text):
        if self.title_open:
            self.title += text
        if self.schema_text is not None:
            self.schema_text += text

    def handle_endtag(self, tag):
        if tag == 'title':
            self.title_open = False
        if tag == 'script' and self.schema_text is not None:
            self.schemas.append(json.loads(self.schema_text))
            self.schema_text = None

def read(path):
    p = Head()
    p.feed(path.read_text())
    return p

def target(url):
    path = root / unquote(urlsplit(url).path).lstrip('/')
    return path if path.is_file() else path / 'index.html'

def canonical(p):
    links = [a['href'] for a in p.links if a.get('rel') == 'canonical']
    assert len(links) == 1
    return unquote(links[0])

def directives(text):
    return {x.strip() for x in text.split(',')}

category_redirects = {'/post/category/uncategorized/': '/post/'}

for row in baseline['pages']:
    language = originals[unquote(urlsplit(row['url']).path)]
    original_url = origin + ('/en' if language == 'en' else '') + urlsplit(row['url']).path
    p = read(target(original_url))
    pair = pair_by_path[unquote(urlsplit(row['url']).path)]
    front, _ = json.JSONDecoder().raw_decode((repo / pair['sources'][language]).read_text())
    # The owner requested newly authored abstracts; preserve original titles/dates,
    # but validate descriptions against the current reviewed content instead.
    description = front['description']
    assert p.title == row['title'], f'Title changed: {row["url"]}'
    assert p.meta['description'] == description, f'Description mismatch: {row["url"]}'
    assert canonical(p) == unquote(original_url) and p.h1 == 1
    assert directives(p.meta['robots']) == directives(row['robots'])
    for prefix in ('og:', 'twitter:'):
        assert p.meta[prefix + 'title'] == row['title']
        assert p.meta[prefix + 'description'] == description
    assert p.meta['og:locale'] == ('en_US' if language == 'en' else 'zh_CN')
    assert unquote(p.meta['og:url']) == unquote(original_url)
    assert len(p.schemas) == 1 and isinstance(p.schemas[0], dict)
    schema = p.schemas[0]
    assert schema['description'] == description
    assert schema['@type'] == ('BlogPosting' if row['type'] == 'post' else 'WebPage')
    assert schema['datePublished'] == row['published'] and schema['dateModified'] == row['modified']
    assert datetime.datetime.fromisoformat(schema['dateModified']) >= datetime.datetime.fromisoformat(schema['datePublished'])
    assert schema['inLanguage'] == ('en-US' if language == 'en' else 'zh-CN') and schema['url'] == p.meta['og:url']
    if row['type'] == 'post':
        assert schema['headline'] and schema['author']['name'] and schema['author']['url']
        assert schema['mainEntityOfPage']['@id'] == p.meta['og:url']
    images = [origin + path for path in front.get('images', [])]
    assert [unquote(u) for u in schema.get('image', [])] == images
    if images:
        assert p.meta['og:image'] == images[0] and p.meta['twitter:image'] == images[0]
    for image in images:
        assert target(image).is_file()

home = read(root / 'index.html')
assert home.meta['google-site-verification'] == config['params']['googlesiteverification']
assert home.title == baseline['home']['title']
assert home.meta['description'] == baseline['home']['description']
assert home.schemas[0]['@type'] == 'WebSite'
article_pages = []
for n in range(1, 5):
    p = home if n == 1 else read(root / f'page/{n}/index.html')
    assert canonical(p) == origin + ('/' if n == 1 else f'/page/{n}/')
    assert 'noindex' not in directives(p.meta['robots'])
    links = {unquote(u) for u in p.anchors}
    article_pages.append({unquote(urlsplit(r['url']).path) for r in baseline['pages'] if r['type'] == 'post'} & links)
assert [len(p) for p in article_pages] == [10, 10, 10, 3]
assert sum(map(len, article_pages)) == len(set.union(*article_pages)) == 33

for term in baseline['terms']:
    p = read(target(term['path']))
    if term['path'] in category_redirects:
        assert p.alias and canonical(p) == origin + category_redirects[term['path']]
        continue
    assert canonical(p) == origin + term['path']
    assert ('noindex' in directives(p.meta['robots'])) == term['noindex']
assert not (root / 'pages/index.html').exists()
assert 'noindex' in directives(read(root / '404.html').meta['robots'])

sitemap = ET.parse(root / 'zh/sitemap.xml').getroot()
locations = [unquote(n.text) for n in sitemap.findall('s:url/s:loc', ns)]
assert len(locations) == len(set(locations))
assert {origin + unquote(urlsplit(r['url']).path) for r in baseline['pages']} <= set(locations)
for url in locations:
    assert url.startswith(origin + '/') and target(url).is_file()
    p = read(target(url))
    assert canonical(p) == url and 'noindex' not in directives(p.meta['robots'])
for term in baseline['terms']:
    if term['path'] in category_redirects:
        assert origin + term['path'] not in locations
        continue
    assert ((origin + term['path']) in locations) != term['noindex']
for image in sitemap.findall('s:url/i:image/i:loc', ns):
    assert image.text.startswith(origin + '/') and target(image.text).is_file()
for name, count in [('post-sitemap.xml', 33), ('page-sitemap.xml', 1), ('category-sitemap.xml', 7)]:
    child = ET.parse(root / name).getroot()
    assert len(child.findall('s:url', ns)) == count
    assert {unquote(n.text) for n in child.findall('s:url/s:loc', ns)} <= set(locations)
index = ET.parse(root / 'sitemap_index.xml').getroot()
assert {n.text for n in index.findall('s:sitemap/s:loc', ns)} == {origin + '/zh/sitemap.xml', origin + '/en/sitemap.xml'}
automatic_index = ET.parse(root / 'sitemap.xml').getroot()
assert {n.text for n in automatic_index.findall('s:sitemap/s:loc', ns)} == {origin + '/zh/sitemap.xml', origin + '/en/sitemap.xml'}

feed = ET.parse(root / 'index.xml').getroot()
items = feed.findall('channel/item')
assert len(items) == 33
assert {unquote(i.findtext('link')) for i in items} == {origin + unquote(urlsplit(r['url']).path) for r in baseline['pages'] if r['type'] == 'post'}
assert all(i.findtext('description') and i.findtext('pubDate') for i in items)
robots = (root / 'robots.txt').read_text()
assert 'Sitemap: ' + origin + '/sitemap_index.xml' in robots
assert 'Content-Signal: search=yes, ai-input=no, ai-train=no' in robots
assert 'Disallow: /\n' not in robots
for file in baseline['verificationFiles']:
    expected_hash = hashlib.sha256((repo / 'static/favicon.png').read_bytes()).hexdigest() if file['path'] == '/favicon.png' else file['sha256']
    assert hashlib.sha256(target(file['path']).read_bytes()).hexdigest() == expected_hash
print(f'OK: 34 original SEO headers, 4 homepage pages, 4 taxonomy routes, {len(locations)} sitemap URLs, images, JSON-LD, 33 RSS items and public verification files')
