#!/usr/bin/env python3
"""Site config loader. Every other script imports from here.

Reads project.yaml from the working directory (or $LISTICLE_PROJECT) so nothing
in scripts/ is hard-wired to one website. Deliberately parses only the flat
`key: value` lines it needs rather than requiring PyYAML - the whole toolkit is
standard library.

Exposes
  SITE_URL      e.g. https://example.com   (no trailing slash)
  SITE_HOST     e.g. example.com           (no www.)
  SITE_NAME
  CONTENT_DIR   where <id>.draft.html and the json caches live
  ENGINE_DIR    where the per-article generators live
  TARGETS       [(post_id, focus_keyword, slug), ...] read from content/*.meta.json

Override any of them with the matching environment variable.
"""
import json, os, re, glob, sys

PROJECT = os.environ.get('LISTICLE_PROJECT', 'project.yaml')


def _scan(path):
    """Pull the handful of scalars we need out of project.yaml."""
    vals = {}
    if not os.path.exists(path):
        return vals
    for line in open(path, encoding='utf-8'):
        m = re.match(r'\s*(name|url)\s*:\s*"?([^"#\n]+)"?', line)
        if m and m.group(1) not in vals:
            vals[m.group(1)] = m.group(2).strip()
    return vals


_cfg = _scan(PROJECT)

SITE_URL = os.environ.get('SITE_URL', _cfg.get('url', '')).rstrip('/')
SITE_NAME = os.environ.get('SITE_NAME', _cfg.get('name', ''))
SITE_HOST = re.sub(r'^https?://(?:www\.)?', '', SITE_URL)

CONTENT_DIR = os.environ.get('CONTENT_DIR', 'content')
ENGINE_DIR = os.environ.get('ENGINE_DIR', 'engine')


def require_site():
    if not SITE_URL:
        sys.exit(f'No site URL. Create {PROJECT} with a site.url, or set SITE_URL. '
                 'Copy templates/project.yaml to start.')
    return SITE_URL


def content(*parts):
    return os.path.join(CONTENT_DIR, *parts)


def load_json(name, default=None):
    """Load a content/ json file, or return default if absent."""
    p = content(name)
    if not os.path.exists(p):
        if default is None:
            sys.exit(f'missing {p} - see SKILL.md phase 2')
        return default
    return json.load(open(p, encoding='utf-8'))


def targets():
    """[(post_id, focus_keyword, slug)] for every article with a meta.json."""
    out = []
    for f in sorted(glob.glob(content('*.meta.json'))):
        d = json.load(open(f, encoding='utf-8'))
        out.append((str(d['post_id']), d.get('focus_keyword', ''), d.get('slug', '')))
    return out


TARGETS = targets() if os.path.isdir(CONTENT_DIR) else []
