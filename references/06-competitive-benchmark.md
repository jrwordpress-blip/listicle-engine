# Competitive benchmark

Run this after publishing, to answer "how does ours compare" with measurements
instead of impressions.

## Find the competitors that are actually useful

The top of a commercial SERP is often not benchmarkable. On the source keyword
the top three were a LinkedIn Pulse post, a vendor directory, and a member post
on a trade-association domain — all ranking on host authority, none a format you
can reproduce on your own site.

**Sort every result into:**

| Class | Benchmarkable? |
|---|---|
| Editorial listicle on a publisher | Yes — direct competitor |
| Company service page | Yes — the commercial competitor |
| Directory (Clutch, GoodFirms) | Reference only |
| Platform / UGC post (LinkedIn, Medium, community) | No — cannot be reproduced |
| Freelance marketplace | No |

Report the platform pages so nobody wonders why they were skipped, then benchmark
against the real ones.

## Get the SERP

`SERPAPI_SEARCH` returns five results and accepts only a query. Run the variant
set and combine — see `07-troubleshooting.md`. Record the best position each
domain achieves and on which query.

## Measure

```bash
curl -sL --compressed -A "<browser UA>" -H "Accept: text/html…" -o page.html "<url>"
python3 scripts/parse_html.py
```

`parse_html.py` strips `nav`, `header`, `footer` and `aside` so the word count
describes the page rather than the site, then measures words, headings, numbered
entries, keyword counts, links, images and alt coverage, tables, lists, schema
types, Flesch, words per sentence, and HTML source weight.

Measure **your own page the same way** in the same run. Do not compare a
browser-measured column against HTML-parsed ones.

## Score both totals

```bash
python3 scripts/score_services.py
```

Service pages and listicles are different content types. Three checks — spec
tables, numbered entries, extractable spec blocks — are listicle-format checks
a service page never attempts. So report two totals:

- **Full** — the whole rubric.
- **Format-neutral** — those three removed, the rest rescaled.

On the source comparison this mattered enormously: full score 86 vs 67, but
format-neutral **83 vs 82**. Reporting only the full score would have claimed a
lead that mostly measures format choice.

## Use the keyword family, not just the exact phrase

Service pages target the singular commercial variant ("company", "services").
Scoring them on a plural phrase they deliberately never use produces a zero that
teaches nothing. Score on the family; report the exact-phrase count separately.

The finding that comes out of doing this properly: on the source SERP, **all
three ranking service pages used the exact focus phrase zero times.**

## Say what the comparison cannot tell you

An on-page comparison cannot explain a ranking. Without domain rating and
backlinks, a page scoring 60 outranking one scoring 89 is unexplained, and the
honest report says so in those words. List which providers refused.
