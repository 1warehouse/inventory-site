# App screen mockups

Every app screenshot on the site is generated from this folder. The artwork is
not a photograph of the app — it is a drawing of it, so it stays legible at
small sizes and can be produced in each language the site speaks.

```
templates/*.svg     the design, one file per screen, with {{tokens}} for text
content/<lang>.json the strings behind those tokens
index.html          browse it: ?lang=de, or ?lang=de&screen=6a for one screen
screens.js          fills the tokens
render.py           photographs each screen into img/
../fonts/           Poppins, so a render does not depend on the machine
../lib/fit.js       shrinks anything a translation made too wide
../lib/shoot.py     the headless Chrome capture
```

`../share-card/` is the site's Open Graph image, built the same way. Both are
served from `design/` when rendering, so `../fonts` and `../lib` resolve — a
static server will not follow a path out of its root.

## Where the design comes from

The templates were exported from the Claude Design project
**Product illustration design project** →
<https://claude.ai/design/p/2154a00b-6104-4f7f-9348-c1b8f973bac4>
(`App Illustrations.dc.html`). The ids below are that document's option ids, so
`6a` here is `6a` there.

To change a design: change it in that document, export the bundle, copy the new
`<svg>` over `templates/<id>.svg`, re-apply the tokens (the strings are listed
in `content/en.json`), then re-render. Do not redraw a screen by hand here —
the two would drift apart immediately.

`support.js` in the export is the Claude Design canvas runtime. The artwork does
not use it, so it is not vendored.

## What each template becomes

| template | ships as | |
|---|---|---|
| `2c`  | `img/app-home.png`               | hero: the list phone inside the cloud scene |
| `3a`  | `img/scan-barcode-wt.png`        | camera, brackets, caption |
| `3b`  | `img/scan-search-wt.png`         | looking the barcode up |
| `3c`  | `img/scan-search-results-wt.png` | found in the global database |
| `4a`  | `img/search-wt.png`              | search, match highlighted |
| `4b`  | `img/locations-list-wt.png`      | locations |
| `5a`  | `img/edit-count-wt.png`          | quantity sheet |
| `6a`  | `img/dashboard-wt.png`           | dashboard |
| `6b`  | `img/history-wt.png`             | history |
| `6c`  | `img/alert-wt.png`               | new alert rule |
| `7a`  | `img/custom-fields-wt.png`       | edit fields |
| `7b`  | `img/users-wt.png`               | users |
| `10a` | `img/gsheet.webp`                | the Google Sheet |

`2a`, `2b`, `8a`, `8b`, `9a`–`9c` and `10b` are drawn in the design doc but not
used by the site. They stay in `templates/` and show up in the gallery so the
set is complete. `img/secure.webp` predates this project and has no words in
it, so it is not generated here.

A phone board is 348 × 721 and renders at device-scale-factor 2, which is the
696 × 1442 the pages declare. Change the board and you change every page's
`width`/`height` attributes with it.

## Rendering

```bash
python3 design/app-screens/render.py                      # every screen, every language
python3 design/app-screens/render.py --lang de            # one language
python3 design/app-screens/render.py --screen 6a --out /tmp   # one screen, somewhere safe
```

English writes to `img/<name>`; the other languages write to `img/<lang>/<name>`,
which is where `tools/i18n_build.py` points the translated pages — it rewrites
`/img/x.png` to `/img/de/x.png` for any file that exists. So a screen that has
not been rendered in a language simply keeps the English picture, and the site
never shows a broken image.

Rendering needs Google Chrome and ImageMagick (`magick`), both already required
by nothing else here — it is a manual step, not part of a build.

## Strings

`content/en.json` holds the exact English of the design doc, so an English
render is byte-identical to the design. The other four files take the app's own
UI wording from `inventory-mobile-app/assets/i18n/<lang>.json` — a screenshot
should say what that language's user really sees in the app — and carry demo
data (product names, locations, dates) written for the site.

Two things to know before editing them:

- **SVG does not wrap.** A paragraph is several `<text>` lines in the design, so
  those strings are arrays and the line breaks are yours to choose. Keep the
  same number of lines as English.
- **Long words shrink rather than collide.** `../lib/fit.js` reads two
  annotations in the templates: `data-fit="112"` shrinks a label until it fits
  that width, and `data-pill="saveBtn"` grows a button's pill around its word.
  An app bar marked `data-bar-title` / `data-bar-action` re-centres its title in
  whatever room the action leaves. All of this is a no-op for English. The
  browser console, and `document.body.dataset.shrunk`, lists anything that
  shrank. Fitting waits on `document.fonts.ready` — measuring before Poppins
  lands sizes the text against a fallback font and gets the answer wrong.

Untranslated tokens are left visible in the artwork as `{{path}}` and reported
in `document.body.dataset.missing`, so a half-translated language is obvious
rather than silent.

## Note on the 2026-09 refresh

The images this folder replaced were exported from an earlier revision of the
same design. Adopting the current one changed three things on the English site,
all deliberate:

- the dashboard now says 5 custom fields and 3 users, which is what the custom
  fields and users screens have always shown;
- three barcodes were invalid EAN-13 (`…3005`, `…2048`, `…3018`) and are now
  the real check digits (`…3000`, `…2047`, `…3015`);
- the sheet shows the columns the app actually writes — Name, Quantity,
  Barcode, Location, Description — instead of a tidied-up four.
