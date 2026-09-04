# Troubleshooting

Every entry is a failure that actually occurred in production, with what it
looked like and what fixed it.

## Content silently corrupted between you and the server

**Symptom.** Byte length matches, md5 does not. Or an image WordPress accepts
that a real decoder rejects.

**Cause.** Large high-entropy payloads reproduced into a tool call. Not the wire
— a probe confirmed the base64 alphabet survives intact.

**Fix.** The Drive → `wp_remote_get` → md5-gate recipe in `05-publishing.md`.
Never hand-paste base64.

**If already uploaded:** locate the differing byte with `cmp -l` and patch in
place with `fopen('r+b')` + `fseek` + `fwrite`, then re-check `md5_file`.

## `wp_update_post` destroys Gutenberg markup

**Symptom.** Blocks vanish; the post renders as one wall of text.

**Cause.** kses strips HTML comments when the acting user lacks
`unfiltered_html`, and Gutenberg block boundaries *are* HTML comments.

**Fix.** `$wpdb->update` on the posts table, then `clean_post_cache`.

## Composio proxy quirks

- **`-d @file` is the whole point** — it reads from disk, so nothing is retyped.
- **Uploaded text bodies come back wrapped in JSON quotes**, exactly two bytes
  larger. `trim($body, '"')`.
- **`alt=media` GET through the proxy returns an empty body.** Verify uploads by
  hashing from the destination server, never by downloading back through the
  proxy.
- **Binary uploads are corrupted and multipart is stripped.** JSON and plain
  text only.
- **~5MB body cap**, and a ~9MB overall proxy limit.
- **`COMPOSIO_SECURITY=allow`** is required to unlock write tools.
- **Sheets API returns `400 Root element must be a message`** unless the
  `content-type` header is lowercase.

## Drive uploads land in the wrong place

**Symptom.** Files appear in My Drive root named "Untitled".

**Cause.** A media `PATCH` with `uploadType=media` overwrites the metadata,
clearing name and parents.

**Fix.** Two steps: create metadata first, PATCH the body second. Then **list the
folder** to confirm, rather than trusting the upload response.

## Every SEO data provider refuses at once

Observed simultaneously on one account:

| Provider | Error |
|---|---|
| Ahrefs | `401 Unauthorized` |
| Semrush | `ERROR 132 :: API UNITS BALANCE IS ZERO` |
| DataForSEO | `40100` — account not authorised |
| Moz | quota exhausted for the period |
| Open PageRank | `Invalid API key` |
| PageSpeed Insights (no key) | `429` |
| Search Console | no permission on the property |

**What still works:** SerpAPI for SERP order, and direct HTML parsing for
on-page metrics. **What becomes impossible:** domain rating, backlinks,
referring domains, traffic — i.e. the most likely explanation for any ranking
order.

**Do not paper over this.** State which providers refused and what the missing
data would have settled. An on-page comparison cannot explain a ranking.

## SerpAPI through Composio takes only a query

The `SERPAPI_SEARCH` tool exposes `query` and nothing else — no `gl`, no
`location`, no `num`, and it returns five results. Hitting SerpAPI directly
through the proxy fails because it wants the key as a URL parameter, not a
header.

**Work around it** by running several commercial-intent query variants and
combining: `"<keyword>"`, `"<keyword> services"`, `"<keyword> company"`,
`"hire <role>"`, `"best <keyword> 2026"`, `"<keyword> agency"`.

**Say what that gives you:** `google.com` defaults, which is the standard global
reference — not a country-targeted result set, and not a controlled worldwide
sample either.

## Google blocks direct SERP scraping

`https://www.google.com/search?q=…` in an automated browser returns an unusual-
traffic interstitial. **Do not attempt to solve it.** Use a SERP API.

## Competitor pages that will not fetch

Some sites 403 every route — curl, WebFetch, and the browser pane alike.

**Escalation order:** curl with full browser headers → Tavily extract (its own
fetcher often succeeds) → report the page as unmeasured.

Where only rendered text is available, report the text metrics and mark schema,
meta description and alt coverage as unobtainable. **Do not score a page on
partial data** — say it is unscored and why.

## Rendered DOM and HTML source disagree

Same page, different numbers: 4,465 words rendered vs 4,658 from HTML source;
11 images in-article vs 24 including theme chrome.

Both are correct for their question. HTML source is what a crawler sees first;
the rendered DOM is what a reader gets. **Pick one method and use it for every
page in a comparison.** Never mix them across columns.

## Lazy-loaded images look broken and are not

In the browser pane, off-screen images report `complete: false,
naturalWidth: 0`. Confirm with a direct `fetch()` before concluding an image is
broken. One site also serves every upload as `image/webp` regardless of the
extension, so content-type is not evidence of a wrong file.

## Host GD cannot resize WebP

`imagecreatefromwebp(): gd-webp cannot allocate temporary buffer`, then
`is not a valid WEBP file`. Metadata still records width and height, so the
image works — it just gets no intermediate sizes or srcset.

## An edit script silently breaks the generator

**Symptom.** A generator that ran yesterday now emits a paragraph with no
subject, or loses a list.

**Cause.** Line-range edits into generator source, and a re-wrap helper that
re-emitted its prefix on every wrapped line.

**Fix.** Whitespace-insensitive replacement keyed on the sentence text, never
line numbers. Assert every edit applied — both `polish.py` and `polish2.py` exit
non-zero when a count is wrong, which is the whole reason they are safe to run
across a batch.

## Theme typography collides with your headings

**Symptom.** A reviewer says the H2s look too large.

**Cause.** Many themes ship bare `h1/h2/h3` font sizes from a reset stylesheet
with no scale — 32px H2 against a 38px H1.

**Check** for `!important` on heading font-size before patching inline. If the
whole site has the collision, the honest fix is theme CSS, and you should say so
rather than patching post by post forever.
