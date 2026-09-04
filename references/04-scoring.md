# Scoring, and the keyword-density argument

## The rubric

`scripts/score.py` scores a draft out of 100 across five categories: Content 30,
SEO 25, E-E-A-T 15, Technical 15, AI-readiness 15.

Every check records how it was determined:

| Tag | Meaning |
|---|---|
| `M` | Measured from the draft |
| `V` | Verified earlier in the programme, with documented evidence |
| `S` | Site-level or publish-time — **not a property of the draft** |

The `S` tag matters. Six points per article sit in checks a draft cannot pass:
page-speed signals, OG/social meta, and site trust pages. A draft scoring 94/100
on everything it controls reports as 88. Do not chase those six in the content.

Batch expectation: **average 90, nothing below 85.** The source batch of ten
averaged 90.0 with nine rated Strong or Exceptional.

## The readability check is the one that actually bites

`Readability (professional band)` awards 2 of 7 at Flesch ease ~40. It is the
single largest recoverable content gap in the batch — 5 points × every article.

Reaching the band means shorter sentences, not simpler ideas. Target under 18
words per sentence. `scripts/longsent.py` lists every prose sentence over a
threshold with a generator line hint:

```bash
python3 scripts/longsent.py content/<id>.final.html 30
```

**Measure it correctly.** An early version of the scorer merged `<li>` items
into fake 106-word sentences, inflating words-per-sentence and reporting grade
11.4–13.2 when the real figure was 9.6–10.8. `plain()` in `score.py` terminates
each block so sentence splitting is honest:

```python
h = re.sub(r'</(li|p|h[1-6])>', '. ', h, flags=re.I)
```

If you write your own metric, terminate blocks or your numbers are fiction.

## Keyword density: two conventions, one argument

A reviewer will eventually tell you the density is "below 1%". Before you agree,
work out which convention they are using.

For a focus phrase of *n* words appearing *k* times in *W* total words:

| Convention | Formula | Example: 15 × 4-word phrase in 4,475 words |
|---|---|---|
| Occurrence basis | k ÷ W | **0.34%** |
| Word-share basis | (k × n) ÷ W | **1.34%** |

Both are legitimate and widely used. Rank Math's own on-page test reported
**1.09%** for one of these articles while a plain occurrence count gave 0.31%.
Same page, same keyword.

**What 1% on the occurrence basis would require.** For a four-word phrase in
4,475 words: 45 repetitions of "smart contract development companies" in one
article. That is textbook keyword stuffing and it is what Google's spam policies
name. Do not do it, and do not agree to it.

**What to deliver instead.** Get exact mentions to 12–16, put the phrase in the
title, H1, URL, first paragraph, two or more subheads, the conclusion, one FAQ
answer, and the hero image's alt text. Then quote the word-share figure, which
lands near 1%, and show the arithmetic above. On the source batch this took the
articles from 5–9 mentions to 10–16, and word-share density from ~0.15% to
~1.0–1.4%, with no sentence that reads as padded.

**A finding worth carrying into the argument.** On the SERP those articles
target, all three ranking commercial service pages use the exact focus phrase
**zero** times. They target the singular variant and rank on the plural anyway.
Density was not the lever holding them up.

## Correcting a reviewer's numbers

Check their word count before accepting their density. One review reported "8
keyword occurrences in this 1,000-word article" for a piece that was 4,475
words — off by 4.4×, probably from a truncated scrape. The occurrence count was
roughly right; the denominator was not, and the denominator is the whole claim.

Be specific and unemotional about it: give the measured word count, both density
figures, and the arithmetic. Then make the improvement they were actually
pointing at.
