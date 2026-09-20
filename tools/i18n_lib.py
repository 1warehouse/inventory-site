"""Shared machinery for the translated builds of 1inventory.io.

The English pages in the repo root are the source of truth. Everything under
/de/, /es/, /fr/ and /pt/ is generated from them plus a per-language catalog in
i18n/, so an English edit is re-applied rather than re-translated: run
tools/i18n_extract.py (refreshes i18n/strings.en.json and reports what changed)
then tools/i18n_build.py.

What counts as translatable:
  · the inner HTML of a leaf block element (p, h1-h4, li, td, th, dt, dd, …),
    kept whole so <em>, <a> and <br> stay where the language needs them;
  · <title>, and the content of the meta tags that carry prose;
  · alt / aria-label / aria-labelledby-free labels on elements;
  · the string fields of the JSON-LD blocks.
HTML comments are deliberately NOT translated: they are maintainer notes and
they stay in English in every build.
"""
import json, re, html
from html.parser import HTMLParser

VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
# Elements whose inner HTML is one translatable unit. The OUTERMOST one wins, so
# a <p> that contains a link is a single string with the link inside it, while a
# bare <a> in a nav — where there is no block around it — is a string of its own.
LEAF = {'p','h1','h2','h3','h4','h5','h6','li','td','th','dt','dd','figcaption','button',
        'blockquote','summary','caption','legend','label','address'}
# A bare text link — a nav or footer entry — is a unit too, but only when no
# block above it already covers it and it wraps nothing but text and inline
# markup. Without the second condition the brand <a> (icon + wordmark) and the
# six flow steps (heading + paragraph inside a link) would be swallowed whole.
LINK_STOP = {'img', 'svg', 'figure', 'picture', 'video'}
BLOCK = LEAF | {'div','section','header','footer','nav','main','ul','ol','dl','table','tbody',
                'thead','tr','figure','article','aside','form','span','a','em','strong','small'}
ATTRS = {'alt','aria-label','title','placeholder'}
META_PROSE = {'description','twitter:title','twitter:description'}
OG_PROSE = {'og:title','og:description','og:image:alt'}
LD_KEYS = {'name','description','text','headline','alternateName','caption'}


class Tok:
    __slots__ = ('kind','data','tag','attrs','selfclose')
    def __init__(self, kind, data='', tag='', attrs=None, selfclose=False):
        self.kind, self.data, self.tag, self.attrs, self.selfclose = kind, data, tag, attrs or [], selfclose


class Lexer(HTMLParser):
    """Loss-preserving tokenizer: convert_charrefs off so entities survive."""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.toks = []
    def handle_starttag(self, tag, attrs):
        self.toks.append(Tok('start', self.get_starttag_text(), tag, attrs))
    def handle_startendtag(self, tag, attrs):
        self.toks.append(Tok('start', self.get_starttag_text(), tag, attrs, True))
    def handle_endtag(self, tag):
        self.toks.append(Tok('end', f'</{tag}>', tag))
    def handle_data(self, data):
        self.toks.append(Tok('data', data))
    def handle_comment(self, data):
        self.toks.append(Tok('comment', f'<!--{data}-->'))
    def handle_decl(self, decl):
        self.toks.append(Tok('decl', f'<!{decl}>'))
    def handle_pi(self, data):
        self.toks.append(Tok('pi', f'<?{data}>'))
    def handle_entityref(self, name):
        self.toks.append(Tok('data', f'&{name};'))
    def handle_charref(self, name):
        self.toks.append(Tok('data', f'&#{name};'))


def lex(src):
    p = Lexer(); p.feed(src); p.close(); return p.toks


def render(toks):
    return ''.join(t.data for t in toks)


def has_text(toks):
    return any(t.kind == 'data' and t.data.strip() for t in toks)


def inside_block(toks, idx):
    """True when token idx sits inside an open LEAF element."""
    stack = []
    for t in toks[:idx]:
        if t.kind == 'start' and not t.selfclose and t.tag not in VOID:
            stack.append(t.tag)
        elif t.kind == 'end' and stack:
            if t.tag in stack:
                while stack and stack.pop() != t.tag:
                    pass
    return any(tag in LEAF for tag in stack)


def units(toks):
    """Yield (start_index, end_index, inner_html) for each translatable leaf block,
    plus attribute and <title> units, in document order."""
    out = []
    i = 0
    n = len(toks)
    while i < n:
        t = toks[i]
        if t.kind == 'start' and not t.selfclose and t.tag not in VOID:
            if t.tag == 'title':
                j = i + 1
                while j < n and not (toks[j].kind == 'end' and toks[j].tag == 'title'):
                    j += 1
                out.append(('title', i + 1, j, render(toks[i+1:j])))
                i = j + 1
                continue
            if t.tag in ('a', 'span') and not inside_block(toks, i):
                depth = 0
                j = i + 1
                ok = True
                while j < n:
                    tj = toks[j]
                    if tj.kind == 'start':
                        if tj.tag in LEAF or tj.tag in LINK_STOP: ok = False
                        if not tj.selfclose and tj.tag not in VOID: depth += 1
                    elif tj.kind == 'end':
                        if depth == 0 and tj.tag == t.tag: break
                        depth -= 1
                    j += 1
                if ok and j < n and has_text(toks[i+1:j]):
                    out.append(('link', i + 1, j, render(toks[i+1:j])))
                    i = j + 1
                    continue
            if t.tag in LEAF:
                depth = 0
                j = i + 1
                nested = False
                while j < n:
                    tj = toks[j]
                    if tj.kind == 'start' and not tj.selfclose and tj.tag not in VOID:
                        if tj.tag in LEAF: nested = True
                        depth += 1
                    elif tj.kind == 'end':
                        if depth == 0 and tj.tag == t.tag: break
                        depth -= 1
                    j += 1
                if j < n and not nested and has_text(toks[i+1:j]):
                    out.append(('block', i + 1, j, render(toks[i+1:j])))
                    i = j + 1
                    continue
        i += 1
    return out


def attr_units(toks):
    """(token_index, attr_name, value) for translatable attributes and meta prose."""
    out = []
    for idx, t in enumerate(toks):
        if t.kind != 'start':
            continue
        d = dict(t.attrs)
        if t.tag == 'meta':
            key = d.get('name') or d.get('property')
            if key in META_PROSE or key in OG_PROSE:
                out.append((idx, 'content', d.get('content', '')))
            continue
        for a in ATTRS:
            if a in d and d[a] and d[a].strip():
                out.append((idx, a, d[a]))
    return out


def set_attr(tok, name, value):
    """Rewrite one attribute inside a raw start tag, leaving the rest byte-identical."""
    pat = re.compile(r'(\s' + re.escape(name) + r'=")([^"]*)(")')
    if pat.search(tok.data):
        tok.data = pat.sub(lambda m: m.group(1) + value.replace('\\', '\\\\') + m.group(3), tok.data, count=1)
    tok.attrs = [(k, value if k == name else v) for k, v in tok.attrs]


def ld_strings(obj, path=()):
    """Walk a JSON-LD object yielding (path, string) for the prose fields."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and k in LD_KEYS:
                yield path + (k,), v
            else:
                yield from ld_strings(v, path + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from ld_strings(v, path + (i,))


def ld_set(obj, path, value):
    cur = obj
    for p in path[:-1]:
        cur = cur[p]
    cur[path[-1]] = value


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


PAGES = ['index.html','plans.html','faq.html','support.html','privacy.html','terms.html','impressum.html','404.html']
LANGS = {'de':'German','es':'Spanish','fr':'French','pt':'Portuguese'}


# --- language switcher ------------------------------------------------------
# Rendered from here for every language INCLUDING English, so the five copies
# can never drift apart. i18n_build.py replaces the whole block in each copy.
NATIVE = {'en': 'English', 'de': 'Deutsch', 'es': 'Español', 'fr': 'Français', 'pt': 'Português'}
LABEL  = {'en': 'Language', 'de': 'Sprache', 'es': 'Idioma', 'fr': 'Langue', 'pt': 'Idioma'}
ORDER  = ['en', 'de', 'es', 'fr', 'pt']

def langswitch_html(lang, page, indent='      '):
    slug = '' if page == 'index.html' else page
    rows = []
    for l in ORDER:
        href = f'/{slug}' if l == 'en' else f'/{l}/{slug}'
        cur = ' aria-current="true"' if l == lang else ''
        rows.append(f'{indent}    <a href="{href}" hreflang="{l}" data-lang="{l}"{cur}>{NATIVE[l]}</a>')
    return (
f'''{indent}<!-- Language. A <details> so it opens with no JavaScript and the five
{indent}     entries stay real links a crawler can follow; main.js stores the
{indent}     click so the detector in <head> stops guessing on later pages.
{indent}     Generated by tools/i18n_build.py — edit it there, not here. -->
{indent}<details class="langswitch">
{indent}  <summary aria-label="{LABEL[lang]}"><span aria-hidden="true">{lang.upper()}</span></summary>
{indent}  <div class="langswitch__menu">
''' + '\n'.join(rows) + f'''
{indent}  </div>
{indent}</details>''')

LANGSWITCH_RE = re.compile(
    r'[ \t]*<!-- Language\. A <details>.*?</details>', re.S)

# The detector. Inline in <head> so a redirect happens before anything paints.
DETECT_JS = '''  <script>
  /* Language. Sends a first-time visitor to the version their browser asks for,
     once, and never again after that: an explicit choice in the switcher is
     stored and wins, and the session flag stops a second guess inside one
     visit. Skipped for ?mobile=1, which is the app embedding a legal page and
     linking to the language it already knows the user is in. */
  (function () {
    try {
      if (/[?&]mobile(=(1|true))?(&|$)/i.test(location.search)) return;
      var SUP = ['de', 'es', 'fr', 'pt'];
      var path = location.pathname;
      var cur = (path.match(/^\\/(de|es|fr|pt)\\//) || [])[1] || 'en';
      var go = function (l) {
        var rest = path.replace(/^\\/(de|es|fr|pt)\\//, '/');
        location.replace((l === 'en' ? rest : '/' + l + rest) + location.search + location.hash);
      };
      var stored = null;
      try { stored = localStorage.getItem('lang'); } catch (e) {}
      if (stored) { if (stored !== cur) go(stored); return; }
      try { if (sessionStorage.getItem('langAuto')) return; sessionStorage.setItem('langAuto', '1'); } catch (e) {}
      var want = null, langs = navigator.languages || [navigator.language || ''];
      for (var i = 0; i < langs.length && !want; i++) {
        var base = String(langs[i]).toLowerCase().split('-')[0];
        if (base === 'en') want = 'en';
        else if (SUP.indexOf(base) > -1) want = base;
      }
      if (want && want !== cur) go(want);
    } catch (e) {}
  })();
  </script>'''
