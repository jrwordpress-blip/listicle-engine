---
name: listicle-engine
description: Research, write, verify, score and publish vendor-comparison listicles ("10 Best X Companies") at bulk, to a WordPress site, with every figure checked against a directory profile rather than vendor marketing. Use when asked to write, rewrite or bulk-produce "top/best N companies" guides, refresh an existing ranking listicle, or run the review gates on a batch of drafts. Covers the whole pipeline: brief to live post to competitive benchmark.
---

# Listicle Engine

A vendor-comparison listicle earns its ranking on **verified figures and category
honesty**, not on word count. This skill is the pipeline that produces them at
bulk without the failures that a hand-written batch always develops: vendor
figures copied from marketing, phantom companies, a firm ranked #1 that no
longer sells the product, hourly rates invented for firms that do not bill
hourly.

Everything here was derived from producing ten of these for a live crypto
publisher, publishing one, and then having it reviewed twice — once by the site
owner and once by an SEO reviewer. **Every rule in `references/03-structure-rules.md`
exists because a specific defect was found.** Do not treat that file as advice.

## Do not use this for

News posts, press releases, single-vendor service pages, GBP posts, or opinion
pieces. This is for multi-vendor comparison guides only.

## Required inputs before you start

| Input | Why it is non-negotiable |
|---|---|
| Target list: post ID (if a rewrite), URL, focus keyword | The gates key off the focus keyword |
| A directory of record (Clutch, GoodFirms, or equivalent) | Every vendor figure is read from it, one profile at a time |
| Site context files: `project.yaml`, `BRAND.md`, `VOICE.md` | Copy from `templates/` and fill for the target site |
| WordPress access (MCP `execute-php`, or REST with an app password) | Publishing and the byte-exact backup |
| Author records: real names, slugs, bios, original publish dates | Fabricated bylines fail E-E-A-T and are dishonest |

If a directory of record is not available for the category, **stop and say so**.
The whole method rests on figures that can be attributed to a third party.

## The pipeline

Nine phases. Each has a gate that must pass before the next begins. Run them in
order; the mechanical passes are idempotent so re-running is free.

### Phase 1 — Site context

Copy `templates/project.yaml`, `templates/BRAND.md` and `templates/VOICE.md`
into the working directory and fill them from the target site's existing
published work. Do not invent a house style — read fifteen of the site's own
posts and write down what is already true.

`references/01-house-style.md` explains what each field controls.

**Gate:** VOICE.md states a sentence-length ceiling, a paragraph ceiling, and
the punctuation convention (spaced hyphen vs em dash). Without those three the
readability gate in Phase 6 has nothing to measure against.

### Phase 2 — Vendor verification

For each vendor named in the target keyword's SERP or the existing post: open
its directory profile and record founding year, headcount band, hourly rate
band, minimum project size and headquarters into `content/vendor_cache.json`.

**One profile at a time.** Not a bulk scrape, not the vendor's own about page.
About 80% of published figures in this category are wrong, and the corrections
are the article's main value.

`references/02-research-and-verification.md` covers source tiers, what to do
when sources disagree, and the category test that catches the most common error
in this genre.

**Gate:** every vendor has either a verified figure or an explicit
"not published" — never an estimate, never a blank.

### Phase 3 — Category split

Sort the vendors into what they actually sell: build partners, auditors,
protocol/research firms, infrastructure platforms. Firms that do not sell hourly
development get **no hourly rate column value** — they get "no public hourly
rate", with the reason.

**Gate:** the article's own count adds up. If the title says ten, the intro's
breakdown, the key-takeaways bullets, and the comparison table must all total
ten. This gate has caught a dropped vendor and a phantom vendor.

### Phase 4 — Research layer

Market statistics with the publishing firm and report year named. Primary-source
statements (a company's own post, an official account) where a claim is
contested. Community signal from Reddit and X where buyer experience matters.

**Gate:** every statistic resolves to a named source with a year. A statistic
you cannot attribute does not go in.

### Phase 5 — Draft generation

Use `scripts/blocks.py` emitters so the block markup is correct by construction:
`P` paragraph, `H` heading, `UL` list, `TBL` table, `EXT` external link, `INT`
internal link, `IMG` image, plus `byline`, `author_box`, `vendor_img` and
`schema_graph`.

Write one generator per article. It is more code than writing HTML by hand and
it is the reason the mechanical gates can run at all.

**Gate:** Gutenberg block comments balance — every `wp:x` has a `/wp:x`.
`scripts/polish.py` reports this.

### Phase 6 — The two review passes

This is where the batch actually gets its quality. Both passes assert every
edit, so a config that has drifted from the text fails loudly rather than
mis-editing silently.

```bash
python3 scripts/polish.py                    # mechanical, all drafts, idempotent
python3 scripts/polish2.py                   # judgement, driven by a per-article config
python3 scripts/faq_schema.py --content content/<id>.final.html --inplace
python3 scripts/score.py                     # 100-point rubric
python3 scripts/longsent.py content/<id>.final.html 30
```

`polish.py` applies eight transforms: image-src variants, H4 label headings to
bold paragraphs, FAQ Q-prefix stripping, non-vendor H3 un-numbering, image
height attributes, the Sources/Method/Author section, external-link
de-duplication, and inline heading sizes.

`polish2.py` takes a per-article config (`templates/polish2.config.example.json`)
for the edits that need to know what the article says: H2 demotions, the
first-paragraph internal link, keyword lifts, and link thinning.

`references/03-structure-rules.md` is the full checklist with the defect each
rule fixes. **Read it before writing the config.**

**Gates, all of which must pass:**

| Gate | Threshold |
|---|---|
| Internal link in first paragraph | present |
| H2 count | ≤ 9 (10 acceptable where structure demands, stated) |
| H4 label headings | 0 |
| Paragraphs with 3+ links | 0 |
| Duplicate external URLs | 0 |
| Exact focus-keyword mentions | ≥ 12, and ~1% on the word-share basis |
| Sources / Method / Author section | present |
| FAQPage schema | present, ≥ 2 Q&A pairs |
| Images without width+height | 0 |
| Every vendor entry has an image | yes |
| Blocks balanced | yes |
| Score | ≥ 85 |

### Phase 7 — Publish

**A live page with existing impressions is not a draft.** Back it up byte-exact
and verify the md5 before writing.

`references/05-publishing.md` has the full recipe, including the transport
problem that will silently corrupt your content if you ignore it, and why
`$wpdb->update` is used instead of `wp_update_post`.

**Gate:** the md5 of the content read back from the database equals the md5 of
the local file. Not "looks right" — equal.

### Phase 8 — Verify live

Load the published URL and check, in the rendered DOM: heading counts, keyword
count, internal links resolve, every image decodes, schema types present, no
placeholder text survived.

**Gate:** zero `UPLOADED_URL` / `ATTACHMENT_ID` placeholders on the live page.
Nine of ten drafts in the source batch still held one; publishing one as-is
would have rendered a broken image.

### Phase 9 — Competitive benchmark

```bash
python3 scripts/parse_html.py           # measure competitor pages from HTML source
python3 scripts/score_services.py       # score them on the same rubric
```

`references/06-competitive-benchmark.md` covers finding the *useful*
competitors — platform posts and directories rank but cannot be copied — and
the two-total scoring that stops a service page being penalised for not being
a listicle.

## Running a batch

```bash
# once per site
cp templates/{project.yaml,BRAND.md,VOICE.md} .

# per article: phases 2-5 produce content/<id>.draft.html
python3 scripts/polish.py                       # all drafts at once
# write engine/polish2.json for the batch, then
python3 scripts/polish2.py
for f in content/*.final.html; do python3 scripts/faq_schema.py --content "$f" --inplace; done
python3 scripts/score.py                        # batch scoreboard
python3 scripts/tomd.py <ids>                   # markdown deliverables
```

Ten articles is a comfortable batch. The mechanical pass takes seconds; the
judgement config is the work, roughly 30 minutes per article.

## Hard rules

- **Never invent a figure.** "Not published" is a finding, not a gap.
- **Never let a vendor's own marketing be the source** for its own headcount,
  founding year or rate.
- **Never publish a `status=publish` change without a verified byte-exact backup.**
- **Never rewrite an FAQ answer to suit the schema.** Fix the prose instead.
- **Never chase keyword density past what reads naturally.** For a four-word
  focus phrase, 1% density means ~45 repetitions in 4,500 words, which is
  keyword stuffing. See `references/04-scoring.md` for the two conventions and
  what to tell a reviewer who quotes the wrong one.
- **State what you could not verify.** The limitations paragraph is part of the
  deliverable, not an apology.

## Reference files

| File | What it answers |
|---|---|
| `references/01-house-style.md` | What project.yaml / BRAND.md / VOICE.md control |
| `references/02-research-and-verification.md` | Source tiers, disagreement handling, the category test |
| `references/03-structure-rules.md` | **The full defect checklist — read before every batch** |
| `references/04-scoring.md` | The 100-point rubric, and keyword-density arithmetic |
| `references/05-publishing.md` | WordPress transport, the md5 gate, revert path |
| `references/06-competitive-benchmark.md` | Finding real competitors and scoring them fairly |
| `references/07-troubleshooting.md` | Every failure hit in production, with the fix |
