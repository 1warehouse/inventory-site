"""Turn the hand-written sNNN<TAB>text files into i18n/<lang>.json.

A line that does not start with an id is a continuation of the previous string,
so a translation may span lines the way the English source does."""
import json, re, sys, io
lang, out = sys.argv[1], {}
cur = None
for path in sys.argv[2:]:
    for line in io.open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        m = re.match(r'^(s\d{3})\t(.*)$', line)
        if m:
            cur = m.group(1); out[cur] = m.group(2)
        elif cur is not None and line.strip():
            out[cur] += '\n' + line
en = json.load(open('i18n/strings.en.json'))
extra = [k for k in out if k not in en]
missing = [k for k in en if k not in out]
json.dump(out, open(f'i18n/{lang}.json', 'w'), ensure_ascii=False, indent=1)
print(f'i18n/{lang}.json: {len(out)} strings'
      + (f' | unknown ids: {extra[:5]}' if extra else '')
      + (f' | still missing: {len(missing)} {missing[:6]}' if missing else ' | complete'))
