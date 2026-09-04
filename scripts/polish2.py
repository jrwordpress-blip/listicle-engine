#!/usr/bin/env python3
"""Judgement pass: the edits that need to know what the article says.

Reads content/<pid>.polished.html (output of polish.py) and applies a
per-article config: H2 demotions, a first-paragraph internal link, focus
keyword lifts, and article-specific corrections. Every edit is asserted, so a
config that has drifted from the text fails loudly instead of silently.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_config import SITE_URL, SITE_HOST, SITE_NAME, CONTENT_DIR, ENGINE_DIR, content, load_json
import re, json, sys, collections

def load_cfg():
    p = os.environ.get('POLISH2_CONFIG', os.path.join(ENGINE_DIR, 'polish2.json'))
    if not os.path.exists(p):
        sys.exit(f'No judgement config at {p}. Copy '
                 'templates/polish2.config.example.json there and edit it '
                 '- see references/03-structure-rules.md.')
    return json.load(open(p, encoding='utf-8'))


CFG = {}
SITE = SITE_URL


def apply(pid):
    src = f'content/{pid}.polished.html'
    h = open(src, encoding='utf-8').read()
    cfg = CFG[pid]
    done = []

    def rep(old, new, label, count=1):
        nonlocal h
        n = h.count(old)
        if n != count:
            raise SystemExit(f'{pid} FAIL [{label}]: expected {count}, found {n}\n  {old[:120]}')
        h = h.replace(old, new)
        done.append(label)

    # 1. demote H2 -> H3 (sized, since polish.py already applied inline sizes)
    for text in cfg.get('demote', []):
        old_open = ('<!-- wp:heading {"style":{"typography":{"fontSize":"26px","lineHeight":"1.3"}}} -->\n'
                    f'<h2 class="wp-block-heading" style="font-size:26px;line-height:1.3">{text}</h2>')
        new_open = ('<!-- wp:heading {"level":3,"style":{"typography":{"fontSize":"22px","lineHeight":"1.35"}}} -->\n'
                    f'<h3 class="wp-block-heading" style="font-size:22px;line-height:1.35">{text}</h3>')
        rep(old_open, new_open, f'demote H2 "{text[:38]}"')

    # 2. plain string edits: first-paragraph link, keyword lifts, corrections
    for item in cfg.get('edits', []):
        rep(item['old'], item['new'], item['label'], item.get('count', 1))

    # 3. referent -> keyword substitutions (first N occurrences only)
    for sub in cfg.get('subs', []):
        old, new, k = sub['old'], sub['new'], sub.get('n', 1)
        n = h.count(old)
        if n < k:
            raise SystemExit(f'{pid} FAIL [sub "{old}"]: wanted {k}, found {n}')
        h = h.replace(old, new, k)
        done.append(f'sub {k}x "{old}" -> keyword')

    open(f'content/{pid}.final.html', 'w', encoding='utf-8').write(h)

    # report
    meta = json.load(open(f'content/{pid}.meta.json'))
    focus = meta['focus_keyword']
    t = re.sub(r'<[^>]+>', ' ', re.sub(r'<!--.*?-->', '', h, flags=re.S))
    words = re.sub(r'\s+', ' ', t).strip().split()
    w = len(words)
    kwc = len(re.findall(re.escape(focus), ' '.join(words), re.I))
    paras = re.findall(r'<p>(.*?)</p>', h, re.S)
    ext = collections.Counter(u for u, _ in re.findall(r'<a href="(https?://[^"]+)"[^>]*>(.*?)</a>', h, re.S)
                              if SITE_HOST not in u)
    bad = []
    for blk in ('paragraph', 'heading', 'list', 'table', 'image', 'list-item'):
        o = len(re.findall(r'<!-- wp:' + blk + r'[ >]', h))
        c = len(re.findall(r'<!-- /wp:' + blk + ' -->', h))
        if o != c:
            bad.append(f'{blk} {o}/{c}')
    print(f'\n{pid}  {meta["title"][:56]}')
    for d in done:
        print('    + ' + d)
    print(f'    words {w} | kw x{kwc} ({100*kwc/w:.2f}%) | H2 {len(re.findall(r"<h2 class", h))} '
          f'| H3 {len(re.findall(r"<h3 class", h))} | H4 {len(re.findall(r"<h4 class", h))} '
          f'| ext {sum(ext.values())}/{len(ext)} uniq '
          f'| p1 internal link {"YES" if SITE in paras[0] else "NO"} '
          f'| 3+link paras {sum(1 for p in paras if len(re.findall(r"<a ", p)) >= 3)}')
    if bad:
        print('    !! unbalanced: ' + ', '.join(bad))


if __name__ == '__main__':
    CFG = load_cfg()
    for pid in (sys.argv[1:] or list(CFG)):
        apply(pid)
