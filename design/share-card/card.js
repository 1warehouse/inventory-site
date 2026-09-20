/* =========================================================================
   1inventory — the Open Graph share card.

   One template, the strings per language in content/<lang>.json. The headline
   is the site's own s081 (the same sentence as og:title), so the card and the
   page it previews always say the same thing.

     index.html?lang=de   the card for one language
     index.html           all five, to compare

   Long translations are handled by fitAll() in ../lib/fit.js.
   ========================================================================= */

const LANGS = ['en', 'de', 'es', 'fr', 'pt'];

function reach(obj, path) {
  return path.split('.').reduce((o, k) => (o == null ? o : o[k]), obj);
}

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

async function card(lang, missing) {
  const [svg, content] = await Promise.all([
    load('template.svg'), load(`content/${lang}.json`),
  ]);
  return fill(svg, content, path => missing.push(`${lang}: ${path}`));
}

async function boot() {
  const lang = new URLSearchParams(location.search).get('lang');
  const missing = [];

  if (lang) {
    document.documentElement.lang = lang;
    document.body.className = 'shot';
    document.body.innerHTML = await card(lang, missing);
  } else {
    document.body.className = 'gallery';
    const all = await Promise.all(LANGS.map(async l =>
      `<figure class="gallery__item">${await card(l, missing)}
         <figcaption>${l.toUpperCase()} — img/${l === 'en' ? '' : l + '/'}og-cover-1200x630.png</figcaption>
       </figure>`));
    document.body.innerHTML = `<div class="gallery__grid">${all.join('')}</div>`;
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
