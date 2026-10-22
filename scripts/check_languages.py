"""Check bilingual routes, metadata, language switching, code, feeds and sitemaps."""
import json
import hashlib
import pathlib
import sys
import subprocess
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import unquote

repo = pathlib.Path(__file__).resolve().parents[1]
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'public')
pairs = json.loads((repo / 'migration/translations.json').read_text())
origin = json.loads(subprocess.run(
    ['hugo', 'config', '--format', 'json'], cwd=repo,
    check=True, capture_output=True, text=True,
).stdout)['baseurl'].rstrip('/')

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.locale, self.meta, self.links, self.options, self.anchors = '', {}, [], [], []
        self.in_switch, self.in_pre, self.code, self.current_code = False, False, [], ''
        self.legacy, self.inline, self.div_depth, self.in_inline = [], [], 0, False
        self.widget = None
        self.feed(path.read_text())
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html': self.locale = a.get('lang')
        if tag == 'meta': self.meta[a.get('name') or a.get('property')] = a.get('content')
        if tag == 'link': self.links.append(a)
        if tag == 'a': self.anchors.append(a.get('href', ''))
        if tag == 'select' and a.get('name') == 'language': self.in_switch = True
        if tag == 'option' and self.in_switch: self.options.append(a)
        if tag == 'pre': self.in_pre, self.current_code = True, ''
        if tag == 'div':
            if self.div_depth: self.div_depth += 1
            elif 'dp-highlighter' in a.get('class', '').split(): self.div_depth = 1; self.legacy.append('')
        if tag == 'code' and not self.in_pre: self.in_inline = True; self.inline.append('')
        if tag == 'script' and a.get('src') == 'https://giscus.app/client.js': self.widget = a
    def handle_data(self, value):
        if self.in_pre: self.current_code += value
        if self.div_depth: self.legacy[-1] += value
        if self.in_inline: self.inline[-1] += value
    def handle_endtag(self, tag):
        if tag == 'select': self.in_switch = False
        if tag == 'pre': self.code.append(self.current_code); self.in_pre = False
        if tag == 'div' and self.div_depth: self.div_depth -= 1
        if tag == 'code': self.in_inline = False

def page(path):
    return Page(root / unquote(path).lstrip('/') / 'index.html')

def canonical(p):
    return [unquote(a['href']) for a in p.links if a.get('rel') == 'canonical']

assert len(pairs) == 34 and len({r['id'] for r in pairs}) == 34
english_posts = set()
for pair in pairs:
    expected_alternates = {('zh-CN' if lang == 'zh' else 'en-US'): origin + unquote(path) for lang, path in pair['paths'].items()}
    pages = {}
    tag_sets = []
    category_sets = []
    for lang, path in pair['paths'].items():
        p = page(path); pages[lang] = p
        front, _ = json.JSONDecoder().raw_decode((repo / pair['sources'][lang]).read_text())
        tag_sets.append(front.get('tags', []))
        category_sets.append(front.get('categories', []))
        for category in front.get('categories', []):
            term_file = repo / 'content/categories' / category / ('_index.md' if lang == 'zh' else '_index.en.md')
            term = json.loads(term_file.read_text())
            assert term['url'] in {unquote(a) for a in p.anchors}, (pair['id'], lang, category)
        for tag in front.get('tags', []):
            term_file = repo / 'content/tags' / tag / ('_index.md' if lang == 'zh' else '_index.en.md')
            term = json.loads(term_file.read_text())
            assert term['url'] in {unquote(a) for a in p.anchors}, (pair['id'], lang, tag)
        assert p.locale == ('zh-CN' if lang == 'zh' else 'en-US'), path
        assert canonical(p) == [origin + unquote(path)], path
        assert p.meta['description'] == front['description'], path
        assert p.meta['og:title'] == front['seoTitle'], path
        assert {a['hreflang']: unquote(a['href']) for a in p.links if a.get('rel') == 'alternate' and 'hreflang' in a} == expected_alternates, path
        assert {unquote(o['value']) for o in p.options} == set(pair['paths'].values()), path
        assert [unquote(o['value']) for o in p.options if 'selected' in o] == [path], path
        digest = hashlib.sha256(json.dumps(p.code + p.legacy + p.inline, ensure_ascii=False).encode()).hexdigest()
        assert digest == pair['codeSha256'], (pair['id'], lang, 'source code changed')
    if pages['zh'].widget:
        assert pages['en'].widget
        for key in ['data-mapping', 'data-term']:
            assert pages['zh'].widget[key] == pages['en'].widget[key], (pair['id'], key)
    if pair['id'].startswith('post-'):
        assert tag_sets[0] == tag_sets[1] and 2 <= len(tag_sets[0]) <= 4, pair['id']
        assert category_sets[0] == category_sets[1] and len(category_sets[0]) == 1, pair['id']
        english_posts.add(unquote(pair['paths']['en']))
assert len(english_posts) == 33
seen = []
for n in range(1, 5):
    path = '/en/' if n == 1 else f'/en/page/{n}/'
    p = page(path)
    assert canonical(p) == [origin + path]
    seen.append(english_posts & {unquote(a) for a in p.anchors})
assert [len(s) for s in seen] == [10, 10, 10, 3]
assert set.union(*seen) == english_posts
rss = ET.parse(root / 'en/index.xml').getroot()
assert rss.findtext('channel/language') == 'en-US'
assert {unquote(i.findtext('link')) for i in rss.findall('channel/item')} == {origin + p for p in english_posts}
ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
zh = {unquote(x.text) for x in ET.parse(root / 'zh/sitemap.xml').findall('s:url/s:loc', ns)}
en = {unquote(x.text) for x in ET.parse(root / 'en/sitemap.xml').findall('s:url/s:loc', ns)}
assert en == {origin + '/en' + x.removeprefix(origin) for x in zh}
for prefix in ['', '/en']:
    alias = page(prefix + '/post/category/uncategorized/')
    assert canonical(alias) == [origin + prefix + '/post/']
print('OK: 34 bilingual pairs, reciprocal language switches/hreflang, unchanged code blocks, 4 English index pages, English RSS and mirrored sitemaps')
