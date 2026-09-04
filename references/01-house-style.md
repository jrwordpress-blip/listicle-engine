# Site context files

Three files, copied from `templates/` and filled per site. They exist so the
gates have something concrete to measure and so a batch of ten articles reads
like one publication.

**Fill them by reading the target site's own published work — at least fifteen
posts. Do not invent a house style.** If the site has a style guide, that wins.

## project.yaml

Site identity and the mechanical facts the scripts need: domain, permalink
shape, the WordPress access route, image dimensions the theme expects, the
directory of record for the category, and the internal-link map (which sibling
guides exist and what each covers).

The internal-link map is the field people skip and then regret. `polish2.json`
needs real URLs to link to, and every link is asserted against the live site
before publish.

## BRAND.md

Audience, positioning, and the editorial do/don't list. Two things it must carry:

- **Taboo phrases.** The words the site does not print. Scored in the grammar
  check.
- **Who the reader is.** "A founder choosing a vendor" and "a developer
  evaluating a stack" produce different articles from the same research.

## VOICE.md

The measurable half. Three fields are load-bearing because gates read them:

| Field | Used by |
|---|---|
| Sentence-length ceiling | `longsent.py`, readability gate |
| Paragraph-length ceiling | Structure check |
| Punctuation convention | Grammar check |

The source site's values: 30-word sentence ceiling, 75-word paragraph ceiling,
spaced hyphens rather than em dashes, reading grade 9–12.

Also record the verdict convention. Every vendor entry on the source site closes
with a bolded "wrong fit" line — a named buyer for whom this vendor is the wrong
choice. It is the most distinctive thing about the format and the reason the
guides read as advice rather than a directory. If you adopt it, adopt it for
every entry.
