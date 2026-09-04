#!/usr/bin/env python3
"""List a draft's over-long prose sentences and where they live in the generator."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_config import SITE_URL, SITE_HOST, SITE_NAME, CONTENT_DIR, ENGINE_DIR, content, load_json
import sys, re, os
pass
import score, importlib; importlib.reload(score)

def main():
    DIR=CONTENT_DIR
    GEN={'5416':'/private/tmp/claude-501/-Users-chandan-Claude/7869f302-ccfb-4e9b-9c41-da5ce32c49ae/scratchpad/gen_5416.py',
         '5094':'row02_5094.py','9689':'row03_9689.py','9571':'row04_9571.py','24300':'row05_24300.py',
         '5074':'row06_5074.py','9724':'row07_9724.py','24334':'row08_24334.py','23605':'row09_23605.py',
         '5418':'row10_5418.py'}
    pid=sys.argv[1]; floor=int(sys.argv[2]) if len(sys.argv)>2 else 33
    t=score.prose_only(open(f"{DIR}/{pid}.draft.html").read())
    ss=[s.strip() for s in re.split(r'(?<=[.!?])\s+', t) if s.strip()]
    g=GEN[pid]
    if not g.startswith('/'): g=os.path.join(ENGINE_DIR, g)
    src=open(g).read().split('\n')
    longs=sorted(((len(s.split()),s) for s in ss if len(s.split())>floor), reverse=True)
    print(f"{pid}: {len(longs)} sentences over {floor} words   generator={os.path.basename(g)}\n")
    for n,s in longs:
        words=s.split()
        # locate by a distinctive 4-word probe from the middle
        probe=' '.join(words[len(words)//2:len(words)//2+4]).strip('.,:;')
        hit=[i+1 for i,l in enumerate(src) if probe and probe in l]
        print(f"### {n}w  (gen line ~{hit[0] if hit else '?'})")
        print(s); print()


if __name__ == '__main__':
    main()
