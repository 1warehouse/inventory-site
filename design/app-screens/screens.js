/* =========================================================================
   1inventory — app screen mockups.

   The artwork in templates/*.svg is the design source, exported from the
   "Product illustration design project" Claude Design doc. Every string a
   reader can see has been replaced with a {{token}}; content/<lang>.json
   holds the strings. Nothing else about a template may be edited here —
   change the design doc, re-export, re-tokenise.

   A token is a path into the content file: {{dashboard.title}}. Arrays are
   indexed: {{fields.names.0}}. A line of a wrapped paragraph is its own
   <text> in the SVG, so translations carry their own line breaks.

   Used two ways:
     index.html?lang=de            browse every screen
     index.html?lang=de&screen=6a  one screen, bare, for render.py

   Anything a translation makes too wide is handled by fitAll() in
   ../lib/fit.js, which index.html loads first.
   ========================================================================= */

/* Template id -> the file the site ships. Sizes are the SVG's own viewBox;
   render.py photographs at 2x, which is what the pages declare. */
const SHOTS = {
  '2c':  { file: 'app-home.png',              w: 620, h: 820 },
  '3a':  { file: 'scan-barcode-wt.png',       w: 348, h: 721 },
  '3b':  { file: 'scan-search-wt.png',        w: 348, h: 721 },
  '3c':  { file: 'scan-search-results-wt.png',w: 348, h: 721 },
  '4a':  { file: 'search-wt.png',             w: 348, h: 721 },
  '4b':  { file: 'locations-list-wt.png',     w: 348, h: 721 },
  '5a':  { file: 'edit-count-wt.png',         w: 348, h: 721 },
  '6a':  { file: 'dashboard-wt.png',          w: 348, h: 721 },
  '6b':  { file: 'history-wt.png',            w: 348, h: 721 },
  '6c':  { file: 'alert-wt.png',              w: 348, h: 721 },
  '7a':  { file: 'custom-fields-wt.png',      w: 348, h: 721 },
  '7b':  { file: 'users-wt.png',              w: 348, h: 721 },
  '10a': { file: 'gsheet.webp',               w: 572, h: 400 },
};

/* Drawn in the design doc but not used by the site today: the bare product
   list (2a), the scene without the cloud (2b), the privacy band (8a/8b) and
   the trust marks (9a-9c). Kept so the gallery shows the whole set. */
const EXTRAS = ['2a', '2b', '8a', '8b', '9a', '9b', '9c', '10b'];

function reach(obj, path) {
  return path.split('.').reduce((o, k) => (o == null ? o : o[k]), obj);
}

/* Substitutes {{a.b.0}} tokens. A token with no string behind it is left in
   place and reported, so a half-translated locale is visible, never silent. */
function fill(svg, content, onMissing) {
  return svg.replace(/\{\{([\w.]+)\}\}/g, (whole, path) => {
    const value = reach(content, path);
    if (value == null || typeof value === 'object') {
      onMissing(path);
      return whole;
    }
    return String(value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  });
}

async function load(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: ${res.status}`);
  return res.headers.get('content-type')?.includes('json') ? res.json() : res.text();
}

async function render(id, content, missing) {
  const svg = await load(`templates/${id}.svg`);
  return fill(svg, content, path => missing.push(`${id}: ${path}`));
}

async function boot() {
  const q = new URLSearchParams(location.search);
  const lang = q.get('lang') || 'en';
  const only = q.get('screen');
  const content = await load(`content/${lang}.json`);
  const missing = [];
  document.documentElement.lang = lang;

  if (only) {
    document.body.className = 'shot';
    document.body.innerHTML = await render(only, content, missing);
  } else {
    document.body.className = 'gallery';
    const langs = ['en', 'de', 'es', 'fr', 'pt'];
    const ids = [...Object.keys(SHOTS), ...EXTRAS];
    const cards = await Promise.all(ids.map(async id => {
      const art = await render(id, content, missing);
      const used = SHOTS[id] ? `img/${SHOTS[id].file}` : 'not used on the site';
      return `<figure class="gallery__item">${art}
        <figcaption>${id} — ${used}</figcaption></figure>`;
    }));
    document.body.innerHTML = `
      <div class="gallery__bar">
        ${langs.map(l => `<a href="?lang=${l}" aria-current="${l === lang}">${l.toUpperCase()}</a>`).join('')}
      </div>
      <div class="gallery__grid">${cards.join('')}</div>`;
  }

  // Poppins must be in before anything is measured, or a fallback font's
  // metrics decide whether a translation fits.
  await document.fonts.ready;
  const shrunk = fitAll(document.body);
  if (shrunk.length) {
    document.body.dataset.shrunk = shrunk.map(s => `${s.text} ${s.from}->${s.to}`).join(' | ');
    console.warn('shrunk to fit:', shrunk);
  }
  const clashes = [...auditOverlaps(document), ...auditFit(document)];
  if (clashes.length) {
    document.body.dataset.overlaps = clashes
      .map(c => `${c.screen}: "${c.a}" x "${c.b}" ${c.overlap}`).join(' | ');
    console.warn('overlapping text:', clashes);
  }
  if (missing.length) {
    document.body.dataset.missing = missing.join(' | ');
    console.warn('untranslated tokens:', missing);
  }
  document.body.dataset.ready = '1';
}

boot();
