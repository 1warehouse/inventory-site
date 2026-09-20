"""Refresh i18n/strings.en.json (id -> English) from the English root pages.

One id per unique English string, so the header, footer, store badges and CTA
are translated once and reused on all eight pages. Ids are stable across runs
as long as the English text is: they are assigned in document order and a
string that disappears from the site keeps its id until someone prunes it.
"""
import json, sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
from i18n_lib import *

old = {}
if os.path.exists('i18n/strings.en.json'):
    old = {v: k for k, v in json.load(open('i18n/strings.en.json')).items()}

strings, order = {}, []
def add(s):
    s = s.strip()
    if not s or not re.search(r'[A-Za-z]', re.sub(r'<[^>]+>', '', s)):
        return
    if s not in strings:
        strings[s] = None
        order.append(s)

for page in PAGES:
    toks = lex(LANGSWITCH_RE.sub('', open(page).read()))
    for kind, a, b, value in units(toks):
        add(value)
    for idx, name, value in attr_units(toks):
        add(value)
    for t in toks:
        if t.kind == 'data' and '"@context"' in t.data:
            try: obj = json.loads(t.data)
            except Exception: continue
            for path, s in ld_strings(obj):
                add(s)

cat, n = {}, 0
for s in order:
    if s in old:
        cat[old[s]] = s
    else:
        while True:
            n += 1
            sid = f's{n:03d}'
            if sid not in cat and sid not in old.values(): break
        cat[sid] = s
json.dump(cat, open('i18n/strings.en.json', 'w'), ensure_ascii=False, indent=1)
print(f'{len(cat)} unique strings, ~{sum(len(s.split()) for s in cat.values())} words')
