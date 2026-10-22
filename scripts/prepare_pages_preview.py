"""Adapt checked production HTML for the default GitHub Pages subdirectory."""
import pathlib
import re
import sys
from html.parser import HTMLParser

root = pathlib.Path(sys.argv[1])
prefix = sys.argv[2]
assert re.fullmatch(r'/[A-Za-z0-9_-]+/', prefix)


class Preview(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.lines = source.splitlines(keepends=True)
        self.edits = []
        self.has_robots = False
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        original = self.get_starttag_text()
        updated = re.sub(
            r'\b(href|src|value)=(\"|\')(/(?!/)[^\"\']*)(\2)',
            lambda m: f'{m[1]}={m[2]}{prefix.rstrip("/")}{m[3]}{m[4]}',
            original,
        )
        if tag == 'meta' and dict(attrs).get('name') == 'robots':
            self.has_robots = True
            updated = re.sub(r'content=(\"|\')[^\"\']*\1', 'content="noindex, follow"', updated)
        if tag == 'meta' and dict(attrs).get('http-equiv', '').lower() == 'refresh':
            updated = updated.replace('https://samcui.com/', prefix)
        if updated != original:
            line, col = self.getpos()
            start = sum(map(len, self.lines[:line - 1])) + col
            self.edits.append((start, start + len(original), updated))

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        if tag == 'head' and not self.has_robots:
            line, col = self.getpos()
            start = sum(map(len, self.lines[:line - 1])) + col
            self.edits.append((start, start, '<meta name="robots" content="noindex, follow">'))


for path in root.rglob('*.html'):
    source = path.read_text()
    parsed = Preview(source)
    for start, end, replacement in reversed(parsed.edits):
        source = source[:start] + replacement + source[end:]
    path.write_text(source)
print(f'Prepared Pages preview at {prefix}; production canonicals retained, robots set to noindex')
