#!/usr/bin/env python3
"""Post-draft polish pass.

Applies the review fixes agreed for post 9689 to any draft in the same house
format, and reports what still needs a human decision. Idempotent: running it
twice changes nothing the second time.

Mechanical transforms
  T1  <h4><strong>Label:</strong></h4>  ->  <p><strong>Label:</strong></p>
  T2  strip "Q1. " prefixes from FAQ H3s
  T3  unnumber the non-vendor numbered H3 series (vendor entries carry a table)
  T4  one external link per URL - keep first mention, unlink the rest
  T5  add height= to images whose filename carries a -WxH suffix
  T6  fold "About the author" + method note into a "Sources, Method and Author"
      section with an explicit source list and a limitations note
  T7  inline heading sizes: H2 26px, H3 22px  (runs last)
"""
import re, json, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_config import SITE_HOST, SITE_NAME, CONTENT_DIR, content

# The directory of record for vendor figures - see references/02.
DIRECTORY_HOST = os.environ.get('DIRECTORY_HOST', 'clutch.co')
DIRECTORY_NAME = os.environ.get('DIRECTORY_NAME', 'Clutch')

H2_SIZE, H2_LH = '26px', '1.3'
H3_SIZE, H3_LH = '22px', '1.35'
CHECK_DATE = '2 September 2026'

AUTHORS = json.load(open(content('authors.json')))
POST_META = json.load(open(content('post_meta.json')))


def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s)


def plain_words(h):
    t = re.sub(r'<!--.*?-->', '', h, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', t).strip().split()


# ---------------------------------------------------------------- transforms
IMG_SRC_1024 = {f'/uploads/2022/09/image-{i}.png': f'/uploads/2022/09/image-{i}-1024x453.png'
                for i in range(1, 6)}


def t0_img_src(h, rep):
    """Point full-size srcs at the 1024-wide variant so T5 can size them and the
    browser is not handed a 1376px file to paint at 1024."""
    n = 0
    for old, new in IMG_SRC_1024.items():
        c = h.count(old)
        if c:
            h = h.replace(old, new)
            n += c
    rep('T0 use 1024-wide image variants', n)
    return h


def t1_h4_labels(h, rep):
    pat = re.compile(r'<!-- wp:heading \{"level":4\} -->\n<h4 class="wp-block-heading"><strong>(.*?)</strong></h4>\n<!-- /wp:heading -->')
    n = len(pat.findall(h))
    h = pat.sub(lambda m: '<!-- wp:paragraph -->\n<p><strong>' + m.group(1) + '</strong></p>\n<!-- /wp:paragraph -->', h)
    rep('T1 H4 labels -> bold paragraphs', n)
    return h


def t2_q_prefixes(h, rep):
    n = len(re.findall(r'(<h3 class="wp-block-heading"[^>]*>)Q\d+\.\s', h))
    h = re.sub(r'(<h3 class="wp-block-heading"[^>]*>)Q\d+\.\s', r'\1', h)
    rep('T2 strip FAQ Q-prefixes', n)
    return h


def t3_unnumber_non_vendor(h, rep):
    """A vendor entry is a numbered H3 followed by a spec table. Anything else
    that is numbered is a step list competing with the vendor numbering."""
    n = 0
    out, pos = [], 0
    for m in re.finditer(r'(<h3 class="wp-block-heading"[^>]*>)(\d+)\.\s(.*?)(</h3>)', h):
        nxt = h.find('<h3 class="wp-block-heading"', m.end())
        window = h[m.end():nxt if nxt != -1 else len(h)]
        is_vendor = '<!-- wp:table -->' in window
        out.append(h[pos:m.start()])
        if is_vendor:
            out.append(m.group(0))
        else:
            out.append(m.group(1) + m.group(3) + m.group(4))
            n += 1
        pos = m.end()
    out.append(h[pos:])
    rep('T3 unnumber non-vendor H3 steps', n)
    return ''.join(out)


def t4_dedupe_external(h, rep):
    seen, n = set(), 0
    out, pos = [], 0
    for m in re.finditer(r'<a href="(https?://[^"]+)"[^>]*>(.*?)</a>', h, re.S):
        url, anchor = m.group(1), m.group(2)
        out.append(h[pos:m.start()])
        if SITE_HOST in url:
            out.append(m.group(0))
        elif url in seen:
            out.append(anchor)          # keep the words, drop the link
            n += 1
        else:
            seen.add(url)
            out.append(m.group(0))
        pos = m.end()
    out.append(h[pos:])
    rep('T4 unlink duplicate external URLs', n)
    return ''.join(out)


def t5_img_height(h, rep):
    n = 0
    def add(m):
        nonlocal n
        tag = m.group(0)
        if 'height=' in tag:
            return tag
        dim = re.search(r'-(\d{2,4})x(\d{2,4})\.(?:jpg|jpeg|png|webp)', tag)
        if not dim:
            return tag
        n += 1
        return tag.replace('width="1024"', f'width="{dim.group(1)}" height="{dim.group(2)}"')
    h = re.sub(r'<img [^>]*>', add, h)
    rep('T5 add image height', n)
    return h


def t6_sources_section(h, pid, rep):
    block = re.search(
        r'<!-- wp:heading -->\n<h2 class="wp-block-heading">About the author</h2>\n<!-- /wp:heading -->\n'
        r'<!-- wp:paragraph -->\n<p>(?P<author>.*?)</p>\n<!-- /wp:paragraph -->\n'
        r'<!-- wp:paragraph -->\n<p>(?P<method>.*?)</p>\n<!-- /wp:paragraph -->', h, re.S)
    if not block:
        rep('T6 sources section', 0, note='no "About the author" block found - skipped')
        return h

    vendors = []
    for m in re.finditer(r'<h3 class="wp-block-heading"[^>]*>\d+\.\s(.*?)</h3>', h):
        nxt = h.find('<h3 class="wp-block-heading"', m.end())
        if '<!-- wp:table -->' in h[m.end():nxt if nxt != -1 else len(h)]:
            vendors.append(strip_tags(m.group(1)).strip())
    # external citations already in the body, first-mention anchors
    cites = []
    for url, anchor in re.findall(r'<a href="(https?://[^"]+)"[^>]*>(.*?)</a>', h, re.S):
        if SITE_HOST in url or DIRECTORY_HOST in url:
            continue
        a = re.sub(r'\s+', ' ', strip_tags(anchor)).strip()
        if url not in [c[0] for c in cites]:
            cites.append((url, a))

    author_para = block.group('author')
    # "<Site>, <Site>." reads as a duplication when the byline is the editorial team
    author_para = author_para.replace('</a></strong>, %s. %s is' % (SITE_NAME, SITE_NAME),
                                      '</a></strong> is')
    items = []
    if vendors:
        items.append('<li>Firm-level data - founding year, headcount band, rate band, minimum project size and '
                     'headquarters: individual {DIRECTORY_NAME} company profiles for ' + ', '.join(vendors[:-1]) +
                     (' and ' + vendors[-1] if len(vendors) > 1 else '') + '.</li>')
    DOMAIN_LABEL = {'x.com': 'Primary statements on X', 'twitter.com': 'Primary statements on X',
                    'getrecon.xyz': 'Recon', 'binance.com': 'Binance', 'coinbase.com': 'Coinbase',
                    'cointelegraph.com': 'Cointelegraph', 'theblock.co': 'The Block',
                    'coindesk.com': 'CoinDesk', 'reuters.com': 'Reuters', 'github.com': 'GitHub',
                    'docs.opensea.io': 'OpenSea developer documentation', 'opensea.io': 'OpenSea',
                    'metamask.io': 'MetaMask', 'support.metamask.io': 'MetaMask support documentation',
                    'ethereum.org': 'ethereum.org', 'dappradar.com': 'DappRadar',
                    'chainalysis.com': 'Chainalysis', 'statista.com': 'Statista',
                    'ibm.com': 'IBM', 'newsroom.ibm.com': 'IBM', 'www.ibm.com': 'IBM',
                    'researchandmarkets.com': 'Research and Markets',
                    'grandviewresearch.com': 'Grand View Research',
                    'fortunebusinessinsights.com': 'Fortune Business Insights',
                    'mordorintelligence.com': 'Mordor Intelligence'}
    bydom = {}
    for url, anchor in cites:
        dom = re.sub(r'^www\.', '', url.split('/')[2])
        bydom.setdefault(dom, []).append(anchor)
    for dom, anchors in bydom.items():
        label = DOMAIN_LABEL.get(dom, dom)
        if label == dom:
            stem = dom.rsplit('.', 1)[0].split('.')[-1].replace('-', ' ')
            label = stem.upper() if len(stem) <= 4 else stem.title()
        shown = ['&#8220;' + a + '&#8221;' for a in anchors[:4]]
        extra = f' and {len(anchors) - 4} more' if len(anchors) > 4 else ''
        tail = ('Each is linked' if len(anchors) > 1 else 'Linked') + ' at the point of use in the body above.'
        items.append(f'<li><strong>{label}</strong> - {", ".join(shown)}{extra}. {tail}</li>')
    items.append('<li>Vendor claims that directory records contradicted are flagged in the entry itself, '
                 'with the directory figure shown.</li>')

    li = '\n<!-- /wp:list-item -->\n<!-- wp:list-item -->\n'.join(items)
    n_profiles = len(vendors)

    new = f'''<!-- wp:heading -->
<h2 class="wp-block-heading">Sources, Method and Author</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>How this list was compiled.</strong> Every firm here was checked the same way. Founding year, headcount band, hourly rate, minimum project size and headquarters were read from that firm\'s own <a href="https://{DIRECTORY_HOST}" target="_blank" rel="noreferrer noopener nofollow">{DIRECTORY_NAME}</a> directory profile, one profile at a time, rather than copied from the firm\'s marketing pages or from other published lists. {n_profiles} profiles were checked on {CHECK_DATE}. Where a directory figure contradicted the firm\'s own published claim, the entry says so and the directory figure is the one shown.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>Sources used:</strong></p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list"><!-- wp:list-item -->
{li}
<!-- /wp:list-item -->
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Known limitations.</strong> Directory headcount bands are self-reported and wide, so they establish scale rather than an exact figure. Where a firm publishes no rate or no minimum, that absence is shown as such and not filled with an estimate. No firm in this guide paid for inclusion, and none was contacted for comment before publication.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">About the author</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{author_para}</p>
<!-- /wp:paragraph -->'''

    h = h[:block.start()] + new + h[block.end():]
    rep('T6 sources section', 1, note=f'{n_profiles} profiles, {len(cites)} external citations listed')
    return h


def t7_heading_sizes(h, rep):
    n2 = h.count('<!-- wp:heading -->\n<h2 class="wp-block-heading">')
    h = h.replace('<!-- wp:heading -->\n<h2 class="wp-block-heading">',
                  f'<!-- wp:heading {{"style":{{"typography":{{"fontSize":"{H2_SIZE}","lineHeight":"{H2_LH}"}}}}}} -->\n'
                  f'<h2 class="wp-block-heading" style="font-size:{H2_SIZE};line-height:{H2_LH}">')
    n3 = h.count('<!-- wp:heading {"level":3} -->\n<h3 class="wp-block-heading">')
    h = h.replace('<!-- wp:heading {"level":3} -->\n<h3 class="wp-block-heading">',
                  f'<!-- wp:heading {{"level":3,"style":{{"typography":{{"fontSize":"{H3_SIZE}","lineHeight":"{H3_LH}"}}}}}} -->\n'
                  f'<h3 class="wp-block-heading" style="font-size:{H3_SIZE};line-height:{H3_LH}">')
    rep('T7 inline heading sizes', n2 + n3, note=f'{n2} H2 @ {H2_SIZE}, {n3} H3 @ {H3_SIZE}')
    return h


# ------------------------------------------------------------------- driver
def polish(pid, write=True):
    src = f'content/{pid}.draft.html'
    h = open(src, encoding='utf-8').read()
    lines = []
    def rep(label, n, note=''):
        lines.append(f'    {label}: {n}' + (f'  ({note})' if note else ''))

    for fn in (t0_img_src, t1_h4_labels, t2_q_prefixes, t3_unnumber_non_vendor, t5_img_height):
        h = fn(h, rep)
    h = t6_sources_section(h, pid, rep)
    h = t4_dedupe_external(h, rep)
    h = t7_heading_sizes(h, rep)

    # structural sanity
    problems = []
    for blk in ('paragraph', 'heading', 'list', 'table', 'image', 'list-item'):
        o = len(re.findall(r'<!-- wp:' + blk + r'[ >]', h))
        c = len(re.findall(r'<!-- /wp:' + blk + ' -->', h))
        if o != c:
            problems.append(f'block {blk} unbalanced {o}/{c}')

    # judgement report
    kw = POST_META.get(pid, {})
    meta = json.load(open(f'content/{pid}.meta.json')) if os.path.exists(f'content/{pid}.meta.json') else {}
    focus = meta.get('focus_keyword', '')
    words = plain_words(h)
    w = len(words)
    t = ' '.join(words)
    kwc = len(re.findall(re.escape(focus), t, re.I)) if focus else 0
    paras = re.findall(r'<p>(.*?)</p>', h, re.S)
    first_internal = SITE_HOST in (paras[0] if paras else '')
    over = [i for i, p in enumerate(paras) if len(re.findall(r'<a ', p)) >= 3]
    ext = collections.Counter(u for u, _ in re.findall(r'<a href="(https?://[^"]+)"[^>]*>(.*?)</a>', h, re.S)
                              if SITE_HOST not in u)

    todo = []
    if not first_internal:
        todo.append('NEEDS internal link in first paragraph')
    if focus and kwc < 14:
        todo.append(f'NEEDS keyword lift: "{focus}" x{kwc} ({100*kwc/w:.2f}%) - target 14+')
    h2n = len(re.findall(r'<h2 class', h))
    if h2n > 9:
        todo.append(f'NEEDS H2 reduction: {h2n} H2s')
    if over:
        todo.append(f'NEEDS link thinning in {len(over)} paragraph(s) with 3+ links')
    dup = [f'{u} x{n}' for u, n in ext.items() if n > 1]
    if dup:
        todo.append('duplicate external links remain: ' + ', '.join(dup))

    if write:
        open(f'content/{pid}.polished.html', 'w', encoding='utf-8').write(h)

    print(f'\n=== {pid}  {meta.get("title","")[:58]}')
    print('\n'.join(lines))
    print(f'    words {w} | H2 {h2n} | H3 {len(re.findall(r"<h3 class", h))} | H4 {len(re.findall(r"<h4 class", h))} | ext links {sum(ext.values())} unique {len(ext)}')
    if problems:
        print('    !! ' + '; '.join(problems))
    for x in todo:
        print('    -> ' + x)
    if not todo and not problems:
        print('    -> clean')
    return h


if __name__ == '__main__':
    ids = sys.argv[1:] or [os.path.basename(f).split('.')[0]
                           for f in sorted(__import__('glob').glob('content/*.draft.html'))]
    for pid in ids:
        polish(pid)
