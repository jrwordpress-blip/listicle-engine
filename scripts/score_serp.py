#!/usr/bin/env python3
"""Score the four SERP pages on one rubric.

Only checks that were measured identically on all four rendered pages are
included, so the columns are comparable. Nothing here credits work that cannot
be read off a live page - no sourcing verification, no backlinks, no authority.
That is a deliberate limit, not an omission: see `excluded` at the foot.
"""
import json

def _load(p='competitive/serp_9689.json'):
    import os, sys
    if not os.path.exists(p):
        sys.exit(f'No SERP data at {p}. See references/06-competitive-benchmark.md.')
    return json.load(open(p, encoding='utf-8'))


D = None
MONTHS_OLD = {'OURS': 0.0, '#1': 8.2, '#2': 0.0, '#3': 2.3}   # from each page's own date stamp


def band(v, table, default=0):
    """table: list of (threshold, points), highest threshold first."""
    for thresh, pts in table:
        if v >= thresh:
            return pts
    return default


def score(p):
    r = {}
    # ---------------------------------------------------- content & structure /30
    r['Depth (words)']            = (band(p['words'], [(3000, 8), (2000, 6), (1000, 4), (1, 2)]), 8)
    r['Spec tables']              = (band(p['tables'], [(5, 7), (2, 5), (1, 3)]), 7)
    r['Numbered entries']         = (band(p['numberedEntries'], [(5, 5), (1, 3)]), 5)
    r['Readability band']         = (band(p['flesch'], [(50, 6), (40, 5), (30, 3), (20, 2)]), 6)
    r['Sentence control']         = (4 if p['wordsPerSentence'] <= 18 else
                                     3 if p['wordsPerSentence'] <= 22 else
                                     2 if p['wordsPerSentence'] <= 26 else 0, 4)
    # ---------------------------------------------------- seo /25
    r['Keyword in title']         = (4 if p['kwInTitle'] else 0, 4)
    r['Keyword in H1']            = (4 if p['kwInH1'] else 0, 4)
    r['Keyword in URL']           = (3 if p['kwInUrl'] else 0, 3)
    tl = p['titleLen']
    r['Title length']             = (3 if 45 <= tl <= 62 else 2 if 30 <= tl <= 70 else 1, 3)
    md = p['metaDescLen']
    r['Meta description']         = (0 if md == 0 else 4 if 120 <= md <= 165 else
                                     3 if 80 <= md <= 185 else 2, 4)
    r['Keyword presence']         = (band(p['kwCount'], [(10, 4), (5, 3), (2, 2), (1, 1)]), 4)
    r['Heading hierarchy']        = (3 if p['h2'] >= 5 and p['h3'] >= 5 else
                                     2 if p['h2'] >= 3 or p['h3'] >= 3 else 1, 3)
    # ---------------------------------------------------- trust signals on page /15
    r['Distinct sources cited']   = (band(p['externalHosts'], [(8, 5), (4, 4), (2, 3), (1, 2)]), 5)
    r['Internal link support']    = (band(p['internalLinks'], [(15, 4), (8, 3), (3, 2), (1, 1)]), 4)
    m = MONTHS_OLD[p['label']]
    r['Freshness']                = (6 if m <= 6 else 4 if m <= 12 else 2, 6)
    # ---------------------------------------------------- technical /15
    r['Schema breadth']           = (band(len(p['schemaTypes']), [(5, 4), (3, 3), (2, 2), (1, 1)]), 4)
    r['FAQPage schema']           = (3 if p['faqSchema'] else 0, 3)
    alt = p['imagesWithAlt'] / p['images'] if p['images'] else 0
    r['Image alt coverage']       = (0 if not p['images'] else
                                     4 if alt >= .95 else 3 if alt >= .70 else
                                     2 if alt >= .40 else 1, 4)
    kb = p['transferKB']
    r['Page weight']              = (4 if kb <= 800 else 3 if kb <= 1500 else
                                     2 if kb <= 3000 else 1, 4)
    # ---------------------------------------------------- ai extractability /15
    r['Extractable spec blocks']  = (band(p['tables'], [(5, 5), (1, 3)]), 5)
    r['Entity clarity']           = (band(p['kwCount'], [(10, 4), (5, 3), (1, 2)]), 4)
    r['Passage segmentation']     = (band(p['h2'] + p['h3'], [(20, 3), (10, 2)], default=1), 3)
    r['FAQ entities exposed']     = (3 if p['faqSchema'] else 0, 3)
    return r


CATS = {
    'Content':   ['Depth (words)', 'Spec tables', 'Numbered entries', 'Readability band', 'Sentence control'],
    'SEO':       ['Keyword in title', 'Keyword in H1', 'Keyword in URL', 'Title length',
                  'Meta description', 'Keyword presence', 'Heading hierarchy'],
    'Trust':     ['Distinct sources cited', 'Internal link support', 'Freshness'],
    'Technical': ['Schema breadth', 'FAQPage schema', 'Image alt coverage', 'Page weight'],
    'AI-ready':  ['Extractable spec blocks', 'Entity clarity', 'Passage segmentation', 'FAQ entities exposed'],
}

def main():
    global D
    D = _load()
    rows = {p['label']: score(p) for p in D['pages']}
    labels = ['OURS', '#1', '#2', '#3']
    names = {p['label']: p['url'].split('/')[2].replace('www.', '') for p in D['pages']}

    print(f"{'':26}" + ''.join(f'{l:>12}' for l in labels))
    print('-' * (26 + 12 * 4))
    out = {}
    for cat, checks in CATS.items():
        mx = sum(rows['OURS'][c][1] for c in checks)
        line = f'{cat + " /" + str(mx):26}'
        for l in labels:
            got = sum(rows[l][c][0] for c in checks)
            out.setdefault(l, {})[cat] = got
            line += f'{str(got) + "/" + str(mx):>12}'
        print(line)
    print('-' * (26 + 12 * 4))
    tot = {l: sum(out[l].values()) for l in labels}
    print(f"{'TOTAL /100':26}" + ''.join(f'{str(tot[l]):>12}' for l in labels))
    print()
    grade = lambda s: ('Exceptional' if s >= 90 else 'Strong' if s >= 80 else
                       'Adequate' if s >= 70 else 'Weak' if s >= 55 else 'Poor')
    for l in labels:
        print(f'  {l:5} {names[l]:24} {tot[l]:3}/100  {grade(tot[l])}')
    print()
    print('per-check detail where the four differ most:')
    for check in rows['OURS']:
        vals = [rows[l][check][0] for l in labels]
        if max(vals) - min(vals) >= 3:
            mx = rows['OURS'][check][1]
            print(f'  {check:26} /{mx:<3}' + ''.join(f'{v:>6}' for v in vals))

    json.dump({'totals': tot, 'cats': out,
               'detail': {l: {k: v[0] for k, v in rows[l].items()} for l in labels},
               'max': {k: v[1] for k, v in rows['OURS'].items()},
               'excluded': ['domain rating', 'referring domains', 'page backlinks',
                            'organic traffic', 'ranking history', 'Core Web Vitals field data',
                            'source verification / factual accuracy']},
              open('competitive/scores_serp.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
