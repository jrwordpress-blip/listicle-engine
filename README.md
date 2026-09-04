# Listicle Engine

A pipeline for producing vendor-comparison listicles — "10 Best X Companies" —
at bulk, where every figure is checked against a directory profile rather than
copied from vendor marketing.

Built from producing ten of these for a live crypto publisher, publishing one,
and taking two rounds of review on it. The rules in
[`references/03-structure-rules.md`](references/03-structure-rules.md) each
exist because a specific defect was found on a real page.

## Install as a Claude Code skill

```bash
git clone <this repo> ~/.claude/skills/listicle-engine
```

Claude picks it up from `SKILL.md`. Invoke it by asking for the work —
"write a top-10 X companies guide", "rewrite <slug>", "run the review gates on
these drafts" — or explicitly with `/listicle-engine`.

To use it as a plain toolkit instead, clone anywhere and run the scripts
directly; they have no dependency on the skill loader.

## What is in here

```
SKILL.md                     the pipeline: 9 phases, each with a gate
references/
  01-house-style.md          what project.yaml / BRAND.md / VOICE.md control
  02-research-and-verification.md   source tiers, the category test
  03-structure-rules.md      the 17-rule defect checklist  ← read this
  04-scoring.md              the 100-point rubric + density arithmetic
  05-publishing.md           WordPress transport, md5 gate, revert path
  06-competitive-benchmark.md   finding real competitors, scoring fairly
  07-troubleshooting.md      every production failure, with the fix
scripts/
  blocks.py                  Gutenberg block emitters (P/H/UL/TBL/EXT/INT/IMG)
  polish.py                  mechanical review pass, idempotent
  polish2.py                 judgement pass, per-article config, asserts edits
  faq_schema.py              FAQPage JSON-LD from the FAQ already written
  score.py                   100-point rubric
  longsent.py                lists over-long sentences
  tomd.py                    Markdown deliverable
  parse_html.py              measure a competitor page from HTML source
  score_serp.py              score the SERP set
  score_services.py          score against service pages, two totals
templates/
  project.yaml               site identity, access, internal-link map
  BRAND.md                   audience, positioning, taboo phrases
  VOICE.md                   sentence/paragraph ceilings, punctuation
  polish2.config.example.json   a real 9-article config
```

## Quickstart

```bash
# 1. site context, once per site
cp templates/{project.yaml,BRAND.md,VOICE.md} .
#    fill them from 15 of the target site's own posts

# 2-5. verify vendors, split categories, research, generate drafts
#      → content/<id>.draft.html   (see SKILL.md phases 2-5)

# 6. the review passes
python3 scripts/polish.py                      # all drafts, mechanical
python3 scripts/polish2.py                     # judgement, from your config
for f in content/*.final.html; do
  python3 scripts/faq_schema.py --content "$f" --inplace
done
python3 scripts/score.py                       # batch scoreboard

# 7-8. publish and verify — see references/05-publishing.md
# 9.  benchmark
python3 scripts/parse_html.py && python3 scripts/score_services.py
```

## The gates

Nothing publishes until all of these pass. `polish.py` and `score.py` report
them; both exit non-zero on a failed assertion.

| Gate | Threshold |
|---|---|
| Internal link in first paragraph | present |
| H2 count | ≤ 9 |
| H4 label headings | 0 |
| Paragraphs with 3+ links | 0 |
| Duplicate external URLs | 0 |
| Exact focus-keyword mentions | ≥ 12 |
| Sources / Method / Author section | present |
| FAQPage schema | present, ≥ 2 pairs |
| Images without width+height | 0 |
| Placeholders on the page | 0 |
| Blocks balanced | yes |
| Score | ≥ 85 |

## Three rules that carry the rest

1. **Never invent a figure.** "Not published" is a finding.
2. **Never publish over a live page without a verified byte-exact backup.**
3. **State what you could not verify.** The limitations paragraph is part of the
   deliverable.

## Requirements

Python 3.9+, standard library only. WordPress access for publishing. A directory
of record (Clutch or equivalent) for the vendor category. Optional: a SERP API
for the benchmark phase.
