import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
CATEGORY_SLUG = __import__('os').environ.get('CATEGORY_SLUG', 'crypto')
from site_config import SITE_URL, SITE_HOST, SITE_NAME, CONTENT_DIR, ENGINE_DIR, content, load_json
# -*- coding: utf-8 -*-
"""Shared Gutenberg block emitters + the audit that mirrors enrich.py exactly."""
import re, html, json, os

CACHE = content("vendor_cache.json")

def vendors():
    d = json.load(open(CACHE))
    return {k: v for k, v in d.items() if not k.startswith("_")}

def P(t):   return "<!-- wp:paragraph -->\n<p>%s</p>\n<!-- /wp:paragraph -->\n" % t
def H(l, t):
    a = "" if l == 2 else ' {"level":%d}' % l
    return ("<!-- wp:heading%s -->\n<h%d class=\"wp-block-heading\">%s</h%d>\n"
            "<!-- /wp:heading -->\n" % (a, l, t, l))
def UL(items):
    li = "".join("<!-- wp:list-item -->\n<li>%s</li>\n<!-- /wp:list-item -->\n" % i for i in items)
    return "<!-- wp:list -->\n<ul class=\"wp-block-list\">%s</ul>\n<!-- /wp:list -->\n" % li
def TBL(rows, header=None):
    h = "<thead><tr>%s</tr></thead>" % "".join("<th>%s</th>" % c for c in header) if header else ""
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return ("<!-- wp:table -->\n<figure class=\"wp-block-table\"><table class=\"has-fixed-layout\">"
            "%s<tbody>%s</tbody></table></figure>\n<!-- /wp:table -->\n" % (h, body))
def EXT(url, anchor):
    return '<a href="%s" target="_blank" rel="noreferrer noopener nofollow">%s</a>' % (url, anchor)
def INT(slug, anchor):
    return '<a href="%s/%s/">%s</a>' % (SITE_URL, slug, anchor)

CLUTCH = EXT("https://clutch.co", "Clutch")

def detail_table(v, minp_label="Minimum project size"):
    return TBL([["Established", v["est"]], ["Employees", v["emp"]],
                ["Hourly rate", v["rate"]], [minp_label, v["minp"]],
                ["Headquarters", v["hq"]]], header=["Detail", "Information"])

def IMG(filename, alt, caption, lcp=True):
    """Gutenberg image block. ATTACHMENT_ID / UPLOADED_URL are the documented
    house-style placeholders, replaced when the media is uploaded at publish time.
    The hero is the LCP element, so it is not lazy-loaded."""
    lazy = '' if lcp else ' loading="lazy"'
    return ('<!-- wp:image {"id":ATTACHMENT_ID,"sizeSlug":"large","linkDestination":"none"} -->\n'
            '<figure class="wp-block-image size-large"><img src="UPLOADED_URL" '
            'alt="%s" class="wp-image-ATTACHMENT_ID" width="1200"%s/>'
            '<figcaption class="wp-element-caption">%s</figcaption></figure>\n'
            '<!-- /wp:image -->\n' % (alt, lazy, caption))

AUTHORS = load_json("authors.json")
POSTMETA = load_json("post_meta.json")
REVIEWED = "2 September 2026"

def byline(pid):
    """Visible byline: author, original publication date, and the review date.
    datePublished is preserved from the live post; only the review date is new."""
    m = POSTMETA[str(pid)]; a = AUTHORS[m["author"]]
    pub = _fmt(m["published"])
    return P('By <a href=%s/author/%s/">%s</a>  ·  Published %s  ·  '
             'Reviewed and updated %s' % (a["slug"], a["name"], pub, REVIEWED))

def author_box(pid):
    m = POSTMETA[str(pid)]; a = AUTHORS[m["author"]]
    return (H(2, "About the author")
            + P('<strong><a href=%s/author/%s/">%s</a></strong>, '
                '%s. %s' % (SITE_URL, a["slug"], a["name"], SITE_NAME, a["bio"]))
            + P("<em>Method:</em> every firm's founding year, headcount, rate, minimum project "
                "size and headquarters came from its own %s profile, checked individually rather "
                "than taken from its marketing. Where sources disagreed, the entry says so." % CLUTCH))

def _fmt(d):
    y, m_, dd = d.split("-")
    months = ["January","February","March","April","May","June","July","August",
              "September","October","November","December"]
    return "%d %s %s" % (int(dd), months[int(m_)-1], y)

LIVE_IMGS = load_json("live_images.json", {})

def vendor_img(pid, vendor, kw):
    """Re-place the existing live screenshot for this vendor. The file already exists in
    the WordPress media library at this URL, so nothing needs re-uploading and no
    accumulated image-SEO is lost. Alt text is rewritten to be descriptive."""
    for r in LIVE_IMGS.get(str(pid), []):
        if r.get("vendor") == vendor:
            alt = "%s website homepage, reviewed among %s" % (vendor, kw)
            return ('<!-- wp:image {"sizeSlug":"large","linkDestination":"none"} -->\n'
                    '<figure class="wp-block-image size-large"><img src="%s" alt="%s" '
                    'loading="lazy" width="1024"/></figure>\n<!-- /wp:image -->\n'
                    % (r["src"], alt))
    return ""

def plain(h):
    h = re.sub(r'<!--.*?-->', '', h, flags=re.S)
    h = re.sub(r'<[^>]+>', ' ', h)
    return html.unescape(h)

def audit(content, kw, meta_title, meta_desc, lo=2800, hi=4200):
    """Mirrors blockopedia-gsc-blog-index/scripts/enrich.py."""
    txt = plain(content); wc = len(txt.split()); low = txt.lower()
    occ = low.count(kw.lower())
    dens = occ * len(kw.split()) / wc * 100
    h2 = re.findall(r'<h2[^>]*>(.*?)</h2>', content, flags=re.I | re.S)
    h3 = re.findall(r'<h3[^>]*>(.*?)</h3>', content, flags=re.I | re.S)
    heads = ' '.join(plain(x) for x in h2 + h3).lower()
    ext = re.findall(r'<a\s+[^>]*href="https?://(?!(?:www\.)?' + re.escape(SITE_HOST) + r')[^"]+"[^>]*>',
                     content, flags=re.I)
    bad = [t for t in ext if 'nofollow' not in t or '_blank' not in t]
    internal = re.findall(r'href="https?://(?:www\.)?' + re.escape(SITE_HOST) + r'[^"]*"', content, flags=re.I)
    years = sorted({int(y) for y in re.findall(r'\b(20[12]\d)\b', txt)})
    rows = [
        ("word_count", wc, "%d-%d" % (lo, hi), lo <= wc <= hi),
        ("keyword_occurrences", occ, "-", True),
        ("keyword_density_pct", round(dens, 2), "0.5-1.5", 0.5 <= dens <= 1.5),
        ("keyword_in_headings", heads.count(kw.lower()), ">=2", heads.count(kw.lower()) >= 2),
        ("h2/h3", "%d/%d" % (len(h2), len(h3)), "-", True),
        ("real_lists", len(re.findall(r'<(ul|ol)[^>]*>', content, flags=re.I)), ">0", True),
        ("fake_bullets", content.count("• "), "0", content.count("• ") == 0),
        ("tables", len(re.findall(r'<table', content, flags=re.I)), ">0", True),
        ("em_dashes", content.count("—"), "0", content.count("—") == 0),
        ("internal_links", len(internal), "3-6", 3 <= len(internal) <= 6),
        ("external_links", len(ext), "-", True),
        ("ext_bad_rel", len(bad), "0", len(bad) == 0),
        ("max_year", max(years) if years else 0, ">=2026", bool(years) and max(years) >= 2026),
        ("meta_title_len", len(meta_title), "<=60", len(meta_title) <= 60),
        ("meta_desc_len", len(meta_desc), "140-160", 140 <= len(meta_desc) <= 160),
    ]
    ok = all(r[3] for r in rows)
    print("=== AUDIT (enrich.py formulas) ===")
    for n, val, band, good in rows:
        print("%-22s %-10s %-10s %s" % (n, val, band, "ok" if good else "FAIL"))
    print("ALL GATES:", "PASS" if ok else "FAIL")
    return ok

def schema_graph(headline, desc, url, faq, pid=None):
    """Article + Person + Organization + BreadcrumbList + FAQPage.
    datePublished is the live post's original date; dateModified is this rewrite."""
    org = {"@type": "Organization", "@id": SITE_URL + "/#organization",
           "name": SITE_NAME, "url": SITE_URL}
    graph = [org]
    art = {"@type": "Article", "headline": headline, "description": desc,
           "mainEntityOfPage": {"@type": "WebPage", "@id": url},
           "publisher": {"@id": SITE_URL + "/#organization"}}
    if pid is not None and str(pid) in POSTMETA:
        m = POSTMETA[str(pid)]; a = AUTHORS[m["author"]]
        person = {"@type": "Person",
                  "@id": SITE_URL + "/author/%s/#person" % a["slug"],
                  "name": a["name"], "description": a["bio"],
                  "url": SITE_URL + "/author/%s/" % a["slug"],
                  "worksFor": {"@id": SITE_URL + "/#organization"}}
        graph.append(person)
        art["author"] = {"@id": person["@id"]}
        art["datePublished"] = m["published"]
        art["dateModified"] = "2026-09-02"
    graph.append(art)
    graph.append({"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
        {"@type": "ListItem", "position": 2, "name": "Crypto",
         "item": SITE_URL + "/category/" + CATEGORY_SLUG + "/"},
        {"@type": "ListItem", "position": 3, "name": headline, "item": url}]})
    graph.append({"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q,
         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    return {"@context": "https://schema.org", "@graph": graph}

def to_markdown(content, h1):
    c = re.sub(r'<!--.*?-->', '', content, flags=re.S)
    cell = lambda x: re.sub(r'<[^>]+>', '', x).strip()
    def tbl(m):
        t = m.group(0)
        head = re.findall(r'<th>(.*?)</th>', t, flags=re.S)
        rows = [re.findall(r'<td>(.*?)</td>', r, flags=re.S)
                for r in re.findall(r'<tr>(.*?)</tr>', t, flags=re.S)]
        rows = [r for r in rows if r]; L = []
        if head:
            L.append('| ' + ' | '.join(cell(x) for x in head) + ' |')
            L.append('|' + '---|' * len(head))
        elif rows:
            L.append('| ' + ' | '.join([''] * len(rows[0])) + ' |')
            L.append('|' + '---|' * len(rows[0]))
        for r in rows:
            L.append('| ' + ' | '.join(cell(x) for x in r) + ' |')
        return '\n' + '\n'.join(L) + '\n'
    c = re.sub(r'<figure class="wp-block-table">.*?</figure>', tbl, c, flags=re.S)
    def img(m):
        blk = m.group(0)
        alt = (re.search(r'alt="([^"]*)"', blk) or [None,''])[1]
        cap = (re.search(r'<figcaption[^>]*>(.*?)</figcaption>', blk, re.S) or [None,''])[1]
        cap = re.sub(r'<[^>]+>', '', cap).strip()
        return '\n![%s](IMAGE_TO_UPLOAD)\n\n*%s*\n' % (alt, cap)
    c = re.sub(r'<figure class="wp-block-image.*?</figure>', img, c, flags=re.S)
    c = re.sub(r'<h2[^>]*>(.*?)</h2>', lambda m: '\n## ' + cell(m.group(1)) + '\n', c, flags=re.S)
    c = re.sub(r'<h3[^>]*>(.*?)</h3>', lambda m: '\n### ' + cell(m.group(1)) + '\n', c, flags=re.S)
    c = re.sub(r'<h4[^>]*>(.*?)</h4>', lambda m: '\n**' + cell(m.group(1)) + '**\n', c, flags=re.S)
    c = re.sub(r'<li>(.*?)</li>', lambda m: '- ' + m.group(1).strip(), c, flags=re.S)
    c = re.sub(r'</?(ul|ol)[^>]*>', '', c)
    c = re.sub(r'<p>(.*?)</p>', lambda m: '\n' + m.group(1).strip() + '\n', c, flags=re.S)
    c = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', c, flags=re.S)
    c = c.replace('<strong>', '**').replace('</strong>', '**')
    c = html.unescape(re.sub(r'<[^>]+>', '', c))
    return "# %s\n\n%s\n" % (h1, re.sub(r'\n{3,}', '\n\n', c).strip())

def write_all(pid, content, h1, meta, faq, outdir=CONTENT_DIR):
    open(os.path.join(outdir, "%d.draft.html" % pid), "w").write(content)
    open(os.path.join(outdir, "%d.draft.md" % pid), "w").write(to_markdown(content, h1))
    open(os.path.join(outdir, "%d.meta.json" % pid), "w").write(json.dumps(meta, indent=2))
    open(os.path.join(outdir, "%d.schema.json" % pid), "w").write(json.dumps(
        schema_graph(h1, meta["seo_description"], meta["url"], faq, pid), indent=2))
