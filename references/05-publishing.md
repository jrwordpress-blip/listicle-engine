# Publishing to WordPress

Two things make this phase dangerous: the page you are overwriting may already
rank, and the transport between you and the server will silently corrupt what
you send. Both are solved below. Neither is optional.

## Before anything else: back up byte-exact

```php
// via the WP MCP execute-php ability
$c = get_post_field('post_content', <ID>);
$d = wp_upload_dir();
file_put_contents($d['basedir'].'/<ID>-prepublish-backup.txt', $c);
return array('bytes' => strlen($c), 'md5' => md5($c));
```

Download that file, hash it locally, and confirm the two md5s match. Only then
proceed. On the source batch this backup was the difference between a reversible
content update on a page carrying 6,197 impressions and an irreversible one.

Also capture, before writing: `post_status`, `post_author`, `featured_media`,
categories, tags, and the SEO plugin's title / description / focus keyword. A
direct database write does not preserve what you did not read.

## The transport problem

**Do not paste large content into an `execute-php` call.**

Measured failures, both silent:

- An 8,919-character base64 chunk of a WebP arrived with one flipped byte
  (`0xF5` instead of `0xF6`). The file still passed `getimagesize`, so WordPress
  accepted it and generated metadata — but a real decoder refused it, and the
  image would have rendered broken on the live page.
- An 8,000-character chunk of gzipped HTML arrived with a different md5 at the
  same byte length.

A probe confirmed the base64 alphabet itself survives the wire intact. The
corruption comes from reproducing thousands of high-entropy characters, not from
the transport. Which means **it will happen to you too**, and it will not
announce itself.

## The recipe that works

Nothing is retyped at any step, and the write refuses unless the hash matches.

1. **Locally**, base64-encode the file **URL-safe** (`-`/`_`, padding stripped).
   URL-safe alphanumerics survive intact; `+` and `/` risk mangling.

2. **Upload to Drive by file path** — the point is that `-d @file` reads from
   disk, so no content passes through a prompt:

   ```bash
   # create the metadata record
   composio proxy "https://www.googleapis.com/drive/v3/files?fields=id" \
     --toolkit googledrive -X POST -H 'content-type: application/json' \
     -d '{"name":"payload.txt","mimeType":"text/plain","parents":["<FOLDER_ID>"]}'

   # send the body from disk
   composio proxy "https://www.googleapis.com/upload/drive/v3/files/<ID>?uploadType=media&fields=id,size" \
     --toolkit googledrive -X PATCH -H 'content-type: text/plain' -d @payload.txt

   # link-share it
   composio proxy "https://www.googleapis.com/drive/v3/files/<ID>/permissions" \
     --toolkit googledrive -X POST -H 'content-type: application/json' \
     -d '{"role":"reader","type":"anyone"}'
   ```

   The proxy wraps an uploaded text body in JSON quotes, so the stored file is
   exactly two bytes larger. Strip with `trim($body, '"')` server-side.

3. **Fetch and verify server-side.** The write is inside the same call as the
   check, so a bad transfer cannot reach the database:

   ```php
   $r = wp_remote_get('https://drive.google.com/uc?export=download&id=<ID>', array('timeout'=>30));
   $b = trim(trim(wp_remote_retrieve_body($r)), '"');
   $b64 = strtr($b, '-_', '+/');
   if ($pad = strlen($b64) % 4) { $b64 .= str_repeat('=', 4 - $pad); }
   $html = base64_decode($b64, true);
   if ($html === false)                      return array('err' => 'decode failed');
   if (md5($html) !== '<LOCAL_MD5>')         return array('err' => 'transfer md5 mismatch');
   if (md5($current) !== '<EXPECTED_MD5>')   return array('err' => 'live content changed since audit');
   // only now write
   ```

   The second guard matters as much as the first: it refuses to overwrite a page
   somebody edited in the admin since you measured it.

4. **Write with `$wpdb->update`, not `wp_update_post`.**

   ```php
   $wpdb->update($wpdb->posts, array(
     'post_content'      => $html,
     'post_modified'     => current_time('mysql'),
     'post_modified_gmt' => current_time('mysql', 1),
   ), array('ID' => <ID>));
   clean_post_cache(<ID>);
   wp_cache_delete(<ID>, 'posts');
   wp_cache_flush();
   ```

   **Why.** `wp_update_post` runs content through kses when the acting user
   lacks `unfiltered_html`, and **kses strips HTML comments** — which are
   exactly what Gutenberg block markup is made of. It would silently destroy
   every block boundary in the article.

   A second benefit: a direct write fires no `transition_post_status` hooks, so
   nothing auto-tweets or re-sends the post to RSS subscribers as new.

5. **Verify by reading back.** `md5(get_post_field('post_content', <ID>))` must
   equal the local md5. Not "looks right" — equal.

## Hero images

The chart or hero image is an attachment, uploaded the same way. Two things to
expect:

- Hosts frequently cannot resize WebP: `imagecreatefromwebp(): gd-webp cannot
  allocate temporary buffer`. Intermediate sizes fail, so the image ships with
  no srcset. Acceptable for a 20KB 1024px hero; know that it happened.
- If a single byte does corrupt, you can patch in place rather than re-upload.
  Find the offset with `cmp -l local.webp downloaded.webp`, then:

  ```php
  $f = fopen($path, 'r+b'); fseek($f, <OFFSET-1>); fwrite($f, chr(0xF6)); fclose($f);
  return md5_file($path);   // must now equal the local md5
  ```

## Placeholders

Draft HTML holds `UPLOADED_URL` and `ATTACHMENT_ID` until the image exists on
the server. **Grep for both before every publish.** In the source batch, nine of
ten drafts still contained one; publishing any of them as-is would have rendered
a broken image on a live page.

## Changing the publish date on a refresh

Update `post_date`, `post_date_gmt`, `post_modified`, `post_modified_gmt`
together. Check the permalink structure first — if it is date-based, changing
the date changes the URL and you need a redirect. Where it is not, the URL and
its accumulated equity are untouched.

Keep "first published <original date>" in the byline. See rule 16 in
`03-structure-rules.md` for why.

## Caches

Check for a caching plugin and purge it. `rocket_clean_domain()`,
`do_action('litespeed_purge_all')`, `wp_cache_clear_cache()`, then
`wp_cache_flush()` and `clean_post_cache()` regardless. If the site has no
caching plugin, the core flush is enough.
