# Structure rules

Every rule below exists because a defect was found in a real draft or on a live
page. The "found as" column is the actual failure, so you can recognise it
rather than trusting a checklist you did not write.

Two of the passes are automated. Where a rule says **auto**, `scripts/polish.py`
enforces it and you only need to read the report. Where it says **config**, you
write the edit into `polish2.json` and the script asserts it applied.

---

## 1. Internal link in the first paragraph — config

**Rule.** The first body paragraph carries exactly one contextual internal link,
on a phrase a reader would click.

**Found as.** All ten drafts had zero internal links in the first paragraph. The
first internal link did not appear until the third or fourth section.

**How.** Pick a phrase already in the paragraph that names a sibling guide's
subject. Do not append a "see also" sentence unless nothing in the paragraph
fits — and if you do append one, it must carry real information, not just the
link.

**Do not** link the focus keyword itself to another page. The anchor for your
own primary keyword should not point away from the page ranking for it.

---

## 2. H2 count at or below nine — config

**Rule.** Nine H2 sections. Ten is acceptable where the structure genuinely
demands it, and you say so.

**Found as.** Drafts ran to 12 H2s, with three of them non-content sections
("Key Takeaways", "About the author", "Disclosure").

**How.** Demote in this order:
1. The "…at a Glance" comparison-table section becomes an H3 at the end of the
   vendor section it summarises.
2. "About the author" and "Disclosure" fold into one "Sources, Method and
   Author" H2, with the author as an H3 inside it.
3. Secondary market-commentary sections become H3s under the section they
   elaborate.

**Never** demote a heading into a parent it does not belong under just to hit the
number. An illogical nesting is worse than a tenth H2.

---

## 3. No H4 label headings — auto

**Rule.** Zero H4 elements. Repeated in-entry labels are bold paragraphs.

**Found as.** Every vendor entry carried
`<h4><strong>Contract services in scope:</strong></h4>` and
`<h4><strong>Why choose X:</strong></h4>` — bold inside a heading, with a
trailing colon. Twenty per article. They inflated the heading outline from 34 to
54 entries and rendered mid-paragraph at heading size, which is what the site
owner reported as a "font size issue".

**Fix.** `<p><strong>Label:</strong></p>`. The transform is mechanical and
reversible.

---

## 4. Inline heading sizes — auto

**Rule.** H2 at 26px / line-height 1.3, H3 at 22px / 1.35, set on the block.

**Found as.** The SEO reviewer flagged "H2 headings appear too large". The cause
was the theme: `reset.css` sets bare `h1 {2.5rem}`, `h2 {2rem}`, `h3 {1.75rem}`
with no typographic scale, so H2 rendered at 32px against a 38px H1 — nearly
indistinguishable on screen.

**Fix.** Gutenberg block attributes plus a matching inline style:

```
<!-- wp:heading {"style":{"typography":{"fontSize":"26px","lineHeight":"1.3"}}} -->
<h2 class="wp-block-heading" style="font-size:26px;line-height:1.3">…</h2>
<!-- /wp:heading -->
```

**Check first** whether the theme uses `!important` on heading font-size. If it
does, inline styles lose and the fix belongs in theme CSS instead. It did not on
the source site — verify on yours.

**Note.** This is a per-post fix. If the whole site has the collision, the real
fix is four lines of theme CSS. Say that rather than silently patching post by
post.

---

## 5. One numbered H3 series — auto

**Rule.** Only the vendor entries are numbered.

**Found as.** The "How to Evaluate" steps were numbered 1–5 and the vendors
1–10, producing two independent numbered sequences in one outline. A reader
scanning the page sees "4." twice.

**Fix.** Strip numbers from the non-vendor series. A vendor entry is detected by
a spec table appearing before the next H3 — reliable, because evaluation steps
never carry one.

---

## 6. No `Q1.` prefixes on FAQ headings — auto

**Rule.** The FAQ H3 is the question, nothing else.

**Found as.** `<h3>Q1. What does a smart contract development company do?</h3>`.
The prefix is noise in the outline and in any extracted answer.

---

## 7. One external link per URL — auto

**Rule.** Each distinct external URL is linked once, at first mention. Later
mentions are plain text.

**Found as.** `clutch.co` linked **four times** with the same "Clutch" anchor;
two other URLs doubled. The SEO reviewer's exact words: "avoid adding external
links to the same keyword multiple times".

**Fix.** Keep the first occurrence, unwrap the rest. Run this **after** the
Sources section is generated, or the section's own citation link becomes a
duplicate.

---

## 8. At most two links per paragraph — config

**Rule.** No paragraph carries three or more links.

**Found as.** One paragraph held three consecutive X citations; another held
three internal links in a single closing sentence.

**Fix.** Split into separate paragraphs, or convert a run of "go here instead"
links into a list with one link per item. A three-item list of alternatives is
legitimate; three links in one sentence is not.

---

## 9. Keyword lift and honest density — config

**Rule.** The exact focus phrase appears at least 12 times, and in the title,
H1, URL, first paragraph, at least two subheads, the conclusion and one FAQ
answer.

**Found as.** Drafts sat at 5–9 exact mentions, 0.13–0.22% density. A reviewer
flagged it as "below 1%".

**How to lift naturally.** Convert generic referents already in the text —
"these firms", "the ten firms", "firms here", "these studios" — into the keyword
phrase. Three to five of those per article, not all of them: converting every
one reads worse than leaving them generic.

**Watch for the collision this creates.** One substitution produced "Of the ten
blockchain development companies most often named as leading blockchain
development companies". Scan for the phrase twice in one sentence after lifting.

Read `references/04-scoring.md` before promising a reviewer a density number.

---

## 10. Logical keyword bolding — config

**Rule.** Roughly nine first-mention bolds per article, on definitions, verified
figures and the load-bearing claims.

**Found as.** "No logical keyword bold is found in the paragraph."

**Do not** bold the focus keyword on every occurrence, inside a heading, or
inside a link anchor.

---

## 11. Sources, Method and Author section — auto

**Rule.** One H2 carrying four things: how the list was compiled (with the
profile count and the check date), a sources list, a known-limitations
paragraph, and the author as an H3.

**Found as.** "EEAT Source note Missing". Drafts had a one-line method note
buried under an "About the author" H2 and no source list at all.

The limitations paragraph is the part people want to cut. Keep it. Stating that
directory headcount bands are self-reported, that no firm paid for inclusion,
and that none was contacted for comment is what separates a verified guide from
a confident one.

---

## 12. FAQPage schema — script

**Rule.** `scripts/faq_schema.py --inplace` on every draft with two or more
FAQ pairs.

**Found as.** Across six pages measured on one SERP, three shipped FAQPage
schema — the #2 directory and two of the ranking service pages. Our page was the
only one in the set with FAQ content written and no FAQ markup emitted.

**Rules.** Answers are the paragraph text as written. If an answer is unsuitable
for markup, fix the prose. Never mark up a question the body does not answer.

---

## 13. Every image sized, every entry illustrated — auto

**Rule.** Every `<img>` carries width and height. Every vendor entry has an
image. Every image has descriptive alt text naming the vendor and the category.

**Found as.** Nine vendor images carried `width="1024"` and no height, causing
layout shift. One vendor entry — restored late in the edit — had no image at
all, leaving a visible gap in an otherwise uniform list. Five images pointed at
1376px originals being painted at 1024px.

**Also.** Check alt coverage across the whole page, not just your own images.
One page had 11/11 in-article images described but only 16 of 24 total, the gap
being theme chrome. That is a template fix.

---

## 14. Preserve existing images on a rewrite — manual

**Rule.** When rewriting a live post, re-place the existing image URLs rather
than dropping them.

**Why.** Those files have accumulated image-search equity. On the source batch
this preserved 78 of 80 existing vendor screenshots.

**How.** Map live image URLs to vendors before you write, and pass them through
`vendor_img()`.

---

## 15. Internal consistency of counts and superlatives — manual

**Rule.** Any superlative or range in the prose must match the tables.

**Found as, all on one article:**
- "the second-lowest rate band" — three firms shared the *lowest* band, and the
  conclusion said "lowest" two screens later.
- "minimum project sizes from $10,000 to $50,000" — one vendor's minimum was
  $1,000. Wrong in two places.
- "the highest minimum of the build group after Appinventiv at $50,000" — both
  were $50,000.
- A title saying ten with nine vendors profiled, after one was dropped in edit.

**How.** After the final edit, re-derive every range and superlative from the
comparison table rather than trusting the prose you wrote earlier.

---

## 16. Byline and dates — manual

**Rule.** Real author, original publish date preserved, review date added.

**Found as.** The theme printed "Published on: December 24, 2022" while the
content byline said something different.

**On a refresh** that changes `post_date` to today: keep "first published
<original date>" in the byline. A 2022 post that suddenly claims a 2026
first-publication date on the same URL is the pattern that reads as date
manipulation.

**Author fit is an E-E-A-T requirement, not a formality.** One live page carries
a trading-analyst bio on a guide about contract engineering procurement, which
directly contradicts the method section's own claim. Reassign or write a bio
that fits the subject.

---

## 17. Grammar and phrasing artefacts from editing — manual

**Rule.** Read the paragraphs you edited, in full, after editing them.

**Found as.**
- "most published lists of crypto consultant companies **lists** in this
  category rank them" — duplication from an earlier keyword insertion.
- "and in practice means three layers of work" — subject lost to a density edit.
- "up to *the largest unconditional pool on record was $500,000*" — an anchor
  wrapping a full clause, leaving the sentence ungrammatical.

Automated passes cannot catch these. Budget a read-through.
