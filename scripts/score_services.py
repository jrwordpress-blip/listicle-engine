#!/usr/bin/env python3
"""Score our listicle against the service pages that rank for the same intent.

Two totals, because the pages are different content types:
  full            - the whole rubric, including three listicle-format checks
  format-neutral  - those three checks removed and the rest rescaled, so a
                    service page is not penalised for not being a listicle
Keyword checks use the keyword FAMILY (company / companies / services), since
the service pages target the singular commercial variant. The exact-phrase count
is reported separately rather than scored.
Freshness is excluded: service pages carry no date stamp, so it is unmeasurable
on three of the four.
"""
import json

def _load(p='competitive/service_pages.json'):
    import os, sys
    if not os.path.exists(p):
        sys.exit(f'No measurements at {p}. Run parse_html.py first '
                 '- see references/06-competitive-benchmark.md.')
    return {x['label']: x for x in json.load(open(p, encoding='utf-8'))}


P = {}
LABELS = ['OURS', 'Webkul', 'ScienceSoft', 'Itransition']

FORMAT_CHECKS = {'Spec tables', 'Numbered entries', 'Extractable spec blocks'}


def band(v, table, default=0):
    for t, pts in table:
        if v >= t:
            return pts
    return default


def score(p):
    alt = p['imagesWithAlt'] / p['images'] if p['images'] else 0
    kb = p['htmlKB']
    tl = p['titleLen']
    md = p['metaDescLen']
    return {
        'Depth (words)':           (band(p['words'], [(3000, 8), (2000, 6), (1000, 4), (1, 2)]), 8),
        'Spec tables':             (band(p['tables'], [(5, 7), (2, 5), (1, 3)]), 7),
        'Numbered entries':        (band(p['numberedEntries'], [(5, 5), (1, 3)]), 5),
        'Readability band':        (band(p['flesch'], [(50, 6), (40, 5), (30, 3), (20, 2)]), 6),
        'Sentence control':        (4 if p['wordsPerSentence'] <= 18 else 3 if p['wordsPerSentence'] <= 22
                                    else 2 if p['wordsPerSentence'] <= 26 else 0, 4),
        'Keyword in title':        (4 if p['kwFamilyInTitle'] else 0, 4),
        'Keyword in H1':           (4 if p['kwInH1'] else 0, 4),
        'Keyword in URL':          (3 if p['kwInUrl'] else 0, 3),
        'Title length':            (3 if 45 <= tl <= 62 else 2 if 30 <= tl <= 70 else 1, 3),
        'Meta description':        (0 if md == 0 else 4 if 120 <= md <= 165 else 3 if 80 <= md <= 185 else 2, 4),
        'Keyword presence':        (band(p['kwFamilyCount'], [(10, 4), (5, 3), (2, 2), (1, 1)]), 4),
        'Heading hierarchy':       (3 if p['h2'] >= 5 and p['h3'] >= 5 else 2 if p['h2'] >= 3 or p['h3'] >= 3 else 1, 3),
        'Distinct sources cited':  (band(p['externalHosts'], [(8, 5), (4, 4), (2, 3), (1, 2)]), 5),
        'Internal link support':   (band(p['internalLinks'], [(15, 4), (8, 3), (3, 2), (1, 1)]), 4),
        'Schema breadth':          (band(len(p['schemaTypes']), [(5, 4), (3, 3), (2, 2), (1, 1)]), 4),
        'FAQPage schema':          (3 if p['faqSchema'] else 0, 3),
        'Image alt coverage':      (0 if not p['images'] else 4 if alt >= .95 else 3 if alt >= .70
                                    else 2 if alt >= .40 else 1, 4),
        'HTML source weight':      (4 if kb <= 200 else 3 if kb <= 350 else 2 if kb <= 600 else 1, 4),
        'Extractable spec blocks': (band(p['tables'], [(5, 5), (1, 3)]), 5),
        'Entity clarity':          (band(p['kwFamilyCount'], [(10, 4), (5, 3), (1, 2)]), 4),
        'Passage segmentation':    (band(p['h2'] + p['h3'], [(20, 3), (10, 2)], default=1), 3),
        'FAQ entities exposed':    (3 if p['faqSchema'] else 0, 3),
    }


CATS = {
    'Content':   ['Depth (words)', 'Spec tables', 'Numbered entries', 'Readability band', 'Sentence control'],
    'SEO':       ['Keyword in title', 'Keyword in H1', 'Keyword in URL', 'Title length',
                  'Meta description', 'Keyword presence', 'Heading hierarchy'],
    'Trust':     ['Distinct sources cited', 'Internal link support'],
    'Technical': ['Schema breadth', 'FAQPage schema', 'Image alt coverage', 'HTML source weight'],
    'AI-ready':  ['Extractable spec blocks', 'Entity clarity', 'Passage segmentation', 'FAQ entities exposed'],
}

def main():
    global P
    P = _load()
    rows = {l: score(P[l]) for l in LABELS}
    w = 14
    print(f"{'':26}" + ''.join(f'{l:>{w}}' for l in LABELS))
    print('-' * (26 + w * len(LABELS)))
    cat_tot = {l: {} for l in LABELS}
    for cat, checks in CATS.items():
        mx = sum(rows['OURS'][c][1] for c in checks)
        line = f'{cat + " /" + str(mx):26}'
        for l in LABELS:
            got = sum(rows[l][c][0] for c in checks)
            cat_tot[l][cat] = got
            line += f'{f"{got}/{mx}":>{w}}'
        print(line)
    print('-' * (26 + w * len(LABELS)))

    full_max = sum(v[1] for v in rows['OURS'].values())
    neu_max = sum(v[1] for k, v in rows['OURS'].items() if k not in FORMAT_CHECKS)
    res = {}
    for l in LABELS:
        full = sum(v[0] for v in rows[l].values())
        neu = sum(v[0] for k, v in rows[l].items() if k not in FORMAT_CHECKS)
        res[l] = {'full_raw': full, 'full_max': full_max, 'full_100': round(100 * full / full_max),
                  'neutral_raw': neu, 'neutral_max': neu_max, 'neutral_100': round(100 * neu / neu_max),
                  'cats': cat_tot[l]}
    print(f"{f'RAW /{full_max}':26}" + ''.join(f'{res[l]["full_raw"]:>{w}}' for l in LABELS))
    print(f"{'SCORE /100 (full)':26}" + ''.join(f'{res[l]["full_100"]:>{w}}' for l in LABELS))
    print(f"{f'SCORE /100 (format-neutral)':26}" + ''.join(f'{res[l]["neutral_100"]:>{w}}' for l in LABELS))
    print()
    print(f"{'exact-phrase mentions':26}" + ''.join(f'{P[l]["kwCount"]:>{w}}' for l in LABELS))
    print(f"{'keyword-family mentions':26}" + ''.join(f'{P[l]["kwFamilyCount"]:>{w}}' for l in LABELS))
    print()
    print('checks with a 3+ point spread:')
    for c in rows['OURS']:
        vals = [rows[l][c][0] for l in LABELS]
        if max(vals) - min(vals) >= 3:
            print(f'  {c:26} /{rows["OURS"][c][1]:<3}' + ''.join(f'{v:>7}' for v in vals))

    json.dump(res, open('competitive/scores_services.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
