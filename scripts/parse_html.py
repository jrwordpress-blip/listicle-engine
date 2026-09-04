#!/usr/bin/env python3
"""Measure a saved HTML page on the same checks used for the SERP comparison.

Chrome-level metrics (page weight, rendered text) are not available here, so the
figures are HTML-source metrics: what a crawler sees before JavaScript.
"""
import re, sys, json, os, html as H

KW = 'smart contract development companies'
KW_ALT = r'smart\s+contract\s+development\s+(?:compan(?:y|ies)|services)'

def clean(doc):
    for tag in ('script', 'style', 'noscript', 'svg', 'iframe', 'template'):
        doc = re.sub(rf'<{tag}\b.*?</{tag}>', ' ', doc, flags=re.S | re.I)
    return doc

def body_only(doc):
    """Drop obvious chrome so word counts describe the page, not the site."""
    d = doc
    for tag in ('nav', 'header', 'footer', 'aside'):
        d = re.sub(rf'<{tag}\b.*?</{tag}>', ' ', d, flags=re.S | re.I)
    return d

def text_of(doc):
    t = re.sub(r'<[^>]+>', ' ', doc)
    return re.sub(r'\s+', ' ', H.unescape(t)).strip()

def syllables(w):
    w = re.sub(r'[^a-z]', '', w.lower())
    if not w: return 0
    if len(w) <= 3: return 1
    w = re.sub(r'(?:[^laeiouy]es|ed|[^laeiouy]e)$', '', w)
    w = re.sub(r'^y', '', w)
    return max(len(re.findall(r'[aeiouy]{1,2}', w)), 1)

def measure(path, label, url):
    raw = open(path, encoding='utf-8', errors='replace').read()
    doc = clean(raw)
    core = body_only(doc)
    text = text_of(core)
    words = text.split()
    w = len(words)
    sents = [s for s in re.split(r'[.!?]+(?=\s|$)', text) if len(s.split()) > 2]
    wps = w / max(len(sents), 1)
    spw = sum(syllables(x) for x in words) / max(w, 1)

    title = (re.search(r'<title[^>]*>(.*?)</title>', raw, re.S | re.I) or [None, ''])[1]
    title = re.sub(r'\s+', ' ', H.unescape(title)).strip()
    md = re.search(r'<meta[^>]+name=["\']description["\'][^>]*content=["\'](.*?)["\']', raw, re.S | re.I)
    md = H.unescape(md.group(1)).strip() if md else ''
    canon = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\'](.*?)["\']', raw, re.I)

    host = re.sub(r'^www\.', '', url.split('/')[2])
    hrefs = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\']', core, re.I)
    internal = [h for h in hrefs if h.startswith('/') or host in h]
    external = [h for h in hrefs if h.startswith('http') and host not in h]
    ext_hosts = {h.split('/')[2].replace('www.', '') for h in external if len(h.split('/')) > 2}

    imgs = re.findall(r'<img\b[^>]*>', core, re.I)
    with_alt = [i for i in imgs if re.search(r'\balt=["\'][^"\']+["\']', i)]

    schema = []
    for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', raw, re.S | re.I):
        try:
            j = json.loads(m.group(1).strip())
        except Exception:
            schema += re.findall(r'"@type"\s*:\s*"([^"]+)"', m.group(1))
            continue
        stack = j.get('@graph', j if isinstance(j, list) else [j])
        for n in stack:
            if isinstance(n, dict) and n.get('@type'):
                schema.append('/'.join([n['@type']] if isinstance(n['@type'], str) else n['@type']))

    h1 = [text_of(x) for x in re.findall(r'<h1\b[^>]*>(.*?)</h1>', core, re.S | re.I)]
    kw_count = len(re.findall(KW.replace(' ', r'\s+'), text, re.I))
    kw_family = len(re.findall(KW_ALT, text, re.I))

    return {
        'label': label, 'url': url, 'title': title, 'titleLen': len(title),
        'metaDescLen': len(md),
        'kwInTitle': bool(re.search(KW.replace(' ', r'\s+'), title, re.I)),
        'kwFamilyInTitle': bool(re.search(KW_ALT, title, re.I)),
        'kwInH1': any(re.search(KW_ALT, x, re.I) for x in h1),
        'kwInUrl': bool(re.search(r'smart-contract-development', url, re.I)),
        'h1Text': h1[:1],
        'words': w,
        'h2': len(re.findall(r'<h2\b', core, re.I)),
        'h3': len(re.findall(r'<h3\b', core, re.I)),
        'h4': len(re.findall(r'<h4\b', core, re.I)),
        'numberedEntries': len([x for x in re.findall(r'<h[23]\b[^>]*>(.*?)</h[23]>', core, re.S | re.I)
                                if re.match(r'^\s*\d+[.).]\s', text_of(x))]),
        'kwCount': kw_count, 'kwFamilyCount': kw_family,
        'kwDensityOcc': round(100 * kw_count / max(w, 1), 2),
        'kwDensityWordShare': round(100 * kw_count * 4 / max(w, 1), 2),
        'internalLinks': len(internal), 'externalLinks': len(external), 'externalHosts': len(ext_hosts),
        'images': len(imgs), 'imagesWithAlt': len(with_alt),
        'tables': len(re.findall(r'<table\b', core, re.I)),
        'lists': len(re.findall(r'<[uo]l\b', core, re.I)),
        'listItems': len(re.findall(r'<li\b', core, re.I)),
        'faqSchema': any('FAQPage' in s for s in schema),
        'schemaTypes': sorted(set(schema)),
        'flesch': round(206.835 - 1.015 * wps - 84.6 * spw, 1),
        'fkGrade': round(0.39 * wps + 11.8 * spw - 15.59, 1),
        'wordsPerSentence': round(wps, 1), 'sentences': len(sents),
        'htmlKB': round(len(raw) / 1024),
        'canonical': canon.group(1) if canon else None,
    }

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--targets':
        targets = [tuple(x.split('::')) for x in sys.argv[2:]]
    else:
        cfg = 'competitive/targets.json'
        if not os.path.exists(cfg):
            sys.exit('Pass targets as path::label::url triples, or create '
                     'competitive/targets.json as [[path,label,url], ...]')
        targets = [tuple(t) for t in json.load(open(cfg))]
    out = [measure(*t) for t in targets]
    os.makedirs('competitive', exist_ok=True)
    json.dump(out, open('competitive/service_pages.json', 'w'), indent=1)
    keys = ['words','h2','h3','numberedEntries','kwCount','kwFamilyCount','kwDensityWordShare',
            'titleLen','metaDescLen','internalLinks','externalLinks','externalHosts',
            'images','imagesWithAlt','tables','lists','faqSchema','flesch','wordsPerSentence','htmlKB']
    print(f"{'metric':22}" + ''.join(f'{o["label"]:>14}' for o in out))
    print('-' * (22 + 14 * len(out)))
    for k in keys:
        print(f'{k:22}' + ''.join(f'{str(o[k]):>14}' for o in out))
    print()
    for o in out:
        print(f'{o["label"]:12} kwInTitle={o["kwInTitle"]} kwFamilyInTitle={o["kwFamilyInTitle"]} '
              f'kwInH1={o["kwInH1"]} schema={len(o["schemaTypes"])} {o["schemaTypes"][:5]}')
        print(f'{"":12} title: {o["title"][:88]}')
