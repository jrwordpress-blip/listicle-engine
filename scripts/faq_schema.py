#!/usr/bin/env python3
"""Emit FAQPage JSON-LD for a draft, from the FAQ questions already written.

Why this exists: across six pages measured on the "smart contract development
companies" SERP (3 Sep 2026), three shipped FAQPage schema - the #2 directory
and two of the ranking service pages. Our own draft was the only page in the set
with FAQ content written and no FAQ markup emitted. This closes that.

What it does
  Finds the "Frequently Asked Questions" H2, pairs each following H3 with the
  paragraph(s) beneath it, and appends a wp:html block holding a FAQPage graph.

Usage
  python3 faq_schema.py --content draft.html --inplace
  python3 faq_schema.py --content draft.html --print      # inspect only
  python3 faq_schema.py --content draft.html --strip      # remove a previous block

Rules this enforces
  - Answers are the paragraph text as written. It never rewrites an answer to
    suit the markup: if an answer is unsuitable, fix the prose, not the schema.
  - Minimum two Q&A pairs, or it refuses - a one-question FAQPage is not
    eligible for the rich result and reads as markup for its own sake.
  - Idempotent. Running twice replaces the block rather than stacking a second.
  - Emits nothing if the answer text is empty, and names the question that failed.

Google's requirement worth remembering: FAQPage is for content the site author
wrote, where the answer is visible on the page. Do not mark up questions the
page does not answer in its own body text.
"""
import argparse, json, re, sys, html as H

MARK_OPEN = '<!-- faq-schema:start -->'
MARK_CLOSE = '<!-- faq-schema:end -->'


def strip_tags(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()


def find_faq_pairs(doc):
    """Return [(question, answer_html), ...] from the FAQ section."""
    m = re.search(r'<h2[^>]*>\s*(?:Frequently Asked Questions|FAQs?|Common Questions)[^<]*</h2>',
                  doc, re.I)
    if not m:
        return []
    tail = doc[m.end():]
    # stop at the next H2 - anything after it is a different section
    nxt = re.search(r'<h2[^>]*>', tail)
    if nxt:
        tail = tail[:nxt.start()]

    pairs = []
    heads = list(re.finditer(r'<h3[^>]*>(.*?)</h3>', tail, re.S | re.I))
    for i, h in enumerate(heads):
        q = strip_tags(h.group(1))
        q = re.sub(r'^Q\d+[.):]\s*', '', q)          # tolerate a legacy "Q1." prefix
        end = heads[i + 1].start() if i + 1 < len(heads) else len(tail)
        body = tail[h.end():end]
        paras = re.findall(r'<p>(.*?)</p>', body, re.S)
        answer = ' '.join(strip_tags(p) for p in paras).strip()
        if not answer:
            print(f'  ! no answer paragraph under: "{q[:70]}"', file=sys.stderr)
            continue
        pairs.append((q, answer))
    return pairs


def build_block(pairs, page_url=None):
    graph = {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {'@type': 'Question',
             'name': q,
             'acceptedAnswer': {'@type': 'Answer', 'text': a}}
            for q, a in pairs
        ],
    }
    if page_url:
        graph['@id'] = page_url.rstrip('/') + '/#faq'
    payload = json.dumps(graph, ensure_ascii=False, indent=1)
    return (f'{MARK_OPEN}\n'
            '<!-- wp:html -->\n'
            f'<script type="application/ld+json">\n{payload}\n</script>\n'
            '<!-- /wp:html -->\n'
            f'{MARK_CLOSE}')


def strip_block(doc):
    return re.sub(re.escape(MARK_OPEN) + r'.*?' + re.escape(MARK_CLOSE) + r'\n?',
                  '', doc, flags=re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--content', required=True)
    ap.add_argument('--url', help='canonical URL, used for the @id')
    ap.add_argument('--inplace', action='store_true')
    ap.add_argument('--print', dest='show', action='store_true')
    ap.add_argument('--strip', action='store_true')
    a = ap.parse_args()

    doc = open(a.content, encoding='utf-8').read()

    if a.strip:
        out = strip_block(doc)
        if a.inplace:
            open(a.content, 'w', encoding='utf-8').write(out)
        print(f'removed FAQ schema block ({len(doc) - len(out)} bytes)')
        return

    pairs = find_faq_pairs(doc)
    if len(pairs) < 2:
        sys.exit(f'FAIL: found {len(pairs)} usable Q&A pair(s); need at least 2. '
                 'Check that the FAQ H2 is present and each H3 is followed by a paragraph.')

    block = build_block(pairs, a.url)
    if a.show:
        print(block)
        print(f'\n{len(pairs)} questions:', file=sys.stderr)
        for q, ans in pairs:
            print(f'  - {q[:78]}  ({len(ans.split())}w answer)', file=sys.stderr)
        return

    out = strip_block(doc).rstrip('\n') + '\n\n' + block + '\n'
    if a.inplace:
        open(a.content, 'w', encoding='utf-8').write(out)
        print(f'FAQPage schema written: {len(pairs)} questions, {len(block)} bytes')
    else:
        sys.stdout.write(out)


if __name__ == '__main__':
    main()
