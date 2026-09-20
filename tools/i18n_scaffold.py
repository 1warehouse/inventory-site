"""One-off, idempotent: put the language switcher and the <head> detector into
the English pages. The generated copies get theirs from i18n_build.py."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
from i18n_lib import *

for page in PAGES:
    s = open(page).read()
    changed = []

    if 'langswitch' not in s:
        block = langswitch_html('en', page)
        m = re.search(r'([ \t]*<nav class="nav-links".*?</nav>\n)', s, re.S)
        assert m, page
        s = s[:m.end()] + block + '\n' + s[m.end():]
        changed.append('switcher')

    if 'langAuto' not in s:
        m = re.search(r'<script>.{0,400}?documentElement\.className.*?</script>\n', s, re.S)
        assert m, page
        s = s[:m.end()] + DETECT_JS + '\n' + s[m.end():]
        changed.append('detector')

    if changed:
        open(page, 'w').write(s)
    print(f'{page:16} {", ".join(changed) or "already in place"}')
