"""Generate /de/, /es/, /fr/ and /pt/ from the English root pages + i18n/<lang>.json.

Never edit a file under those folders by hand: this script overwrites them.
Edit the English page, run tools/i18n_extract.py, fill in the new ids in each
i18n/<lang>.json, then run this.

Per language it rewrites, in the copy only:
  · <html lang>, the canonical and og:url, og:locale, and a full hreflang set
    (the four translations, English, and x-default pointing at English);
  · asset paths to absolute (/css, /js, /img) since the copy sits one level down,
    and any app screenshot that exists under img/<lang>/ to that translated copy;
  · page-to-page links stay relative, so they resolve inside the language folder;
  · the JSON-LD prose fields and inLanguage.
HTML comments stay English on purpose — they are notes for whoever maintains
the site, not content.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from i18n_lib import *

EN = json.load(open('i18n/strings.en.json'))
BY_TEXT = {v: k for k, v in EN.items()}
OG_LOCALE = {'de': 'de_DE', 'es': 'es_ES', 'fr': 'fr_FR', 'pt': 'pt_PT', 'en': 'en'}
BASE = 'https://1inventory.io'

def url_for(lang, page):
    slug = '' if page == 'index.html' else page
    return f'{BASE}/{slug}' if lang == 'en' else f'{BASE}/{lang}/{slug}'

def alternates(page, indent='  '):
    out = []
    for l in ['en'] + list(LANGS):
        out.append(f'{indent}<link rel="alternate" hreflang="{l}" href="{url_for(l, page)}" />')
    out.append(f'{indent}<link rel="alternate" hreflang="x-default" href="{url_for("en", page)}" />')
    return '\n'.join(out)

def build_page(page, lang, tr, report):
    src = open(page).read()
    toks = lex(src)

    def T(s):
        key = BY_TEXT.get(s.strip())
        if key and tr.get(key):
            return tr[key]
        if key:
            report['missing'].add(key)
        return None

    # 1. leaf blocks and <title>, back to front so indices stay valid
    for kind, a, b, value in reversed(units(toks)):
        new = T(value)
        if new is None:
            continue
        lead = re.match(r'\s*', value).group(0)
        tail = re.search(r'\s*$', value).group(0)
        toks[a:b] = [Tok('data', lead + new.strip() + tail)]

    # 2. attributes
    for idx, name, value in attr_units(toks):
        new = T(value)
        if new is not None:
            set_attr(toks[idx], name, new)

    # 3. JSON-LD
    for t in toks:
        if t.kind == 'data' and '"@context"' in t.data:
            try: obj = json.loads(t.data)
            except Exception: continue
            for path, s in list(ld_strings(obj)):
                new = T(s)
                if new is not None:
                    ld_set(obj, path, new)
            if isinstance(obj, dict) and 'inLanguage' in obj:
                obj['inLanguage'] = lang
            t.data = '\n' + json.dumps(obj, ensure_ascii=False, indent=2) + '\n  '

    out = render(toks)

    # 4. head plumbing
    out = out.replace('<html lang="en">', f'<html lang="{lang}">', 1)
    out = re.sub(r'<link rel="canonical" href="[^"]*" />',
                 f'<link rel="canonical" href="{url_for(lang, page)}" />', out, count=1)
    out = re.sub(r'<meta property="og:url" content="[^"]*" />',
                 f'<meta property="og:url" content="{url_for(lang, page)}" />', out, count=1)
    out = re.sub(r'<meta property="og:locale" content="[^"]*" />',
                 f'<meta property="og:locale" content="{OG_LOCALE[lang]}" />', out, count=1)
    out = re.sub(r'(\n[ \t]*<link rel="alternate" hreflang="[^"]*" href="[^"]*" />)+', '', out)
    if '<link rel="canonical"' in out:
        out = re.sub(r'(<link rel="canonical"[^>]*/>)', r'\1\n' + alternates(page), out, count=1)

    # 5. assets absolute, absolute page links into the language folder
    out = re.sub(r'(?<=")(css/|js/|img/)', r'/\1', out)

    # 5b. app screenshots carry words, so each language has its own set under
    #     img/<lang>/ (design/app-screens/render.py writes them). A file that
    #     has no translated version keeps pointing at the English one.
    out = re.sub(r'/img/([A-Za-z0-9._-]+)',
                 lambda m: (f'/img/{lang}/{m.group(1)}'
                            if os.path.exists(f'img/{lang}/{m.group(1)}') else m.group(0)),
                 out)
    out = re.sub(r'(?<=")/(?=(plans|faq|support|privacy|terms|impressum|index)\.html)', f'/{lang}/', out)
    # "/" and "/#anchor" both mean the home page — the language's home page here.
    out = out.replace('href="/"', f'href="/{lang}/"').replace('href="/#', f'href="/{lang}/#')

    # 6. the switcher is regenerated rather than rewritten: its five links are
    #    per-language by nature and must survive the path rules above.
    out = LANGSWITCH_RE.sub(lambda m: langswitch_html(lang, page), out)
    return out

def main():
    langs = sys.argv[1:] or list(LANGS)
    for lang in langs:
        path = f'i18n/{lang}.json'
        if not os.path.exists(path):
            print(f'{lang}: no {path}, skipped'); continue
        tr = json.load(open(path))
        report = {'missing': set()}
        os.makedirs(lang, exist_ok=True)
        for page in PAGES:
            open(f'{lang}/{page}', 'w').write(build_page(page, lang, tr, report))
        done = sum(1 for k in EN if tr.get(k))
        print(f'{lang}: {len(PAGES)} pages, {done}/{len(EN)} strings translated'
              + (f', {len(report["missing"])} falling back to English' if report['missing'] else ''))
        if report['missing']:
            print('   missing:', ' '.join(sorted(report['missing'])[:12]), '…' if len(report['missing']) > 12 else '')

if __name__ == '__main__':
    main()
