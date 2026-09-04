#!/usr/bin/env python3
"""Render a house-format Gutenberg draft to the Markdown shape used for the
Drive deliverables. Mirrors the original .draft.md conventions."""
import re, sys, html as htmlmod, json, os

def inline(s):
    s = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', s, flags=re.S)
    s = re.sub(r'</?strong>', '**', s)
    s = re.sub(r'</?em>', '*', s)
    s = re.sub(r'<br\s*/?>', ' ', s)
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'[ \t]+', ' ', htmlmod.unescape(s)).strip()

def convert(h, title):
    out = [f'# {title}', '']
    # strip block comments, keep the HTML
    body = re.sub(r'<!--\s*/?wp:[^>]*?-->', '\x00', h)
    for chunk in body.split('\x00'):
        c = chunk.strip()
        if not c:
            continue
        m = re.match(r'<h([234])[^>]*>(.*?)</h\1>', c, re.S)
        if m:
            out += ['#' * (int(m.group(1))) + ' ' + inline(m.group(2)), '']
            continue
        if c.startswith('<p>'):
            out += [inline(re.sub(r'^<p>|</p>$', '', c, flags=re.S)), '']
            continue
        if c.startswith('<li>'):
            out += ['- ' + inline(re.sub(r'^<li>|</li>$', '', c, flags=re.S)), '']
            continue
        if '<figure class="wp-block-table">' in c:
            rows = re.findall(r'<tr>(.*?)</tr>', c, re.S)
            md = []
            for i, r in enumerate(rows):
                cells = [inline(x) for x in re.findall(r'<t[hd]>(.*?)</t[hd]>', r, re.S)]
                md.append('| ' + ' | '.join(cells) + ' |')
                if i == 0:
                    md.append('|' + '|'.join([' --- '] * len(cells)) + '|')
            out += md + ['']
            continue
        if '<figure class="wp-block-image' in c:
            src = re.search(r'src="([^"]+)"', c)
            alt = re.search(r'alt="([^"]*)"', c)
            cap = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', c, re.S)
            url = src.group(1) if src else 'IMAGE_TO_UPLOAD'
            if url == 'UPLOADED_URL':
                url = 'IMAGE_TO_UPLOAD'
            out += [f'![{alt.group(1) if alt else ""}]({url})', '']
            if cap:
                out += ['*' + inline(cap.group(1)) + '*', '']
            continue
        if c.startswith('<ul') or c.startswith('</ul'):
            continue
    md = '\n'.join(out)
    return re.sub(r'\n{3,}', '\n\n', md).strip() + '\n'

if __name__ == '__main__':
    for pid in sys.argv[1:]:
        meta = json.load(open(f'content/{pid}.meta.json'))
        h = open(f'content/{pid}.final.html', encoding='utf-8').read()
        md = convert(h, meta['title'])
        open(f'content/{pid}.final.md', 'w', encoding='utf-8').write(md)
        print(f'{pid}: {len(md)} bytes, {len(md.split())} words')
