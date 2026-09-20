"""Structural check: a translated page must have exactly the same tag skeleton
as its English source. Catches a translation that dropped a <strong>, unbalanced
a <span>, or lost a link."""
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from i18n_lib import PAGES, LANGS

def skeleton(path):
    s = open(path).read()
    # <body> only: the head legitimately differs (hreflang links, canonical).
    s = s[s.index('<body'):]
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    s = re.sub(r'<script.*?</script>', '<script/>', s, flags=re.S)
    return [t.lower() for t in re.findall(r'</?([a-zA-Z0-9]+)', s)]

bad = 0
for lang in sys.argv[1:] or list(LANGS):
    for page in PAGES:
        p = f'{lang}/{page}'
        if not os.path.exists(p):
            print(f'  MISSING {p}'); bad += 1; continue
        a, b = skeleton(page), skeleton(p)
        if a != b:
            bad += 1
            i = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            print(f'  {p}: tag skeleton differs at #{i}: en={a[i-2:i+3]} {lang}={b[i-2:i+3]}')
    print(f'{lang}: {"structure matches English on all pages" if not bad else "see above"}')
sys.exit(1 if bad else 0)
