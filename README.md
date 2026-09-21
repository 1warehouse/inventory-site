# 1inventory.io

Static marketing site for **1Inventory** — a Google Sheets–based inventory management app by
Sparkybit GmbH. Migrated from Wix Studio to a plain static site hosted on **GitHub Pages**.

## Structure

```
.
├── index.html          # Home (single-page marketing site)
├── terms.html          # Terms and conditions
├── privacy.html        # Privacy policy
├── 404.html            # Not-found page
├── css/style.css       # Design system + all styles
├── js/main.js          # Header, mobile menu, scroll reveals
├── js/analytics.js     # Cookieless GA4 — no cookies, so no consent banner
├── img/                # Optimised, clean-named images & icons
├── data/1inv_faq.json  # Bilingual FAQ data (en/es)
├── assets/             # Original raw asset download from Wix (source of truth)
├── .well-known/        # iOS/Android app deep-link verification files
├── CNAME               # Custom domain for GitHub Pages (1inventory.io)
├── .nojekyll           # Disables Jekyll so .well-known/ is published verbatim
├── robots.txt
└── sitemap.xml
```

## Local preview

Any static file server works, e.g.:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploy (GitHub Pages)

No-build static site served by GitHub Pages:

- **Source branch:** `main`, folder `/` (root) — configure under **Settings → Pages**.
- **Custom domain:** `1inventory.io`, set by the `CNAME` file (DNS points the apex at
  GitHub Pages: `185.199.108–111.153`).
- **`.nojekyll` is required.** Without it GitHub Pages runs a Jekyll build that strips any
  file or folder starting with `.` — which silently drops the entire `.well-known/` directory
  and 404s the app-link files. The marker file disables Jekyll and publishes the repo as-is.

### GitHub Pages limitations (vs. the old Cloudflare Pages setup)

GitHub Pages serves static files only — the Cloudflare `_headers` and `_redirects` files are
not supported and have been removed. As a result:

- **No custom response headers.** The former security headers (`X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`) and cache-control rules are gone.
  GitHub Pages applies its own caching. If these headers are required, front the site with a CDN
  (e.g. Cloudflare in front of Pages) that can inject them.
- **No forced `Content-Type` on the AASA file.** `.well-known/apple-app-site-association` has no
  extension, so Pages serves it without an explicit `application/json` type. This is fine for
  modern iOS Universal Links — Apple fetches and validates via its own CDN, which does not
  require a specific content type.
- **No server-side redirects.** The legacy Wix path redirects (`/1inventory → /`) are no longer
  active. Add HTML meta-refresh pages if those old URLs still need to resolve.

## App deep links (`.well-known/`)

The mobile app opens `https://1inventory.io/inventories/<id>/alerts` links (alert emails / pushes).
For iOS Universal Links and Android App Links to verify, this site serves:

- `/.well-known/apple-app-site-association` — app ID `7MBRQ3583S.com.sparkybit.oneinventory.prod`.
- `/.well-known/assetlinks.json` — package `com.sparkybit.oneinventory`. **Before this works**,
  replace the placeholder fingerprint with the SHA-256 from Play Console → Setup → App signing →
  "App signing key certificate" (colon-separated uppercase hex). If release builds are also
  installed directly (signed by the CI upload key), add that key's SHA-256 as a second array entry.

Both URLs must return 200 on `1inventory.io` **without redirects** (verification fetchers don't
follow them). Verify with
`curl https://app-site-association.cdn-apple.com/a/v1/1inventory.io` and
`adb shell pm get-app-links com.sparkybit.oneinventory`.

## Notes

- Fonts load from Google Fonts (Poppins).
- App Store / Google Play badge links are placeholders (`href="#"`) — swap in the real
  store URLs when the apps are published.
- The "Watch demo" button currently scrolls to the product section; point it at the demo
  video when available.

## Languages

The site is published in English (repo root) and German, Spanish, French and
Portuguese (`/de/`, `/es/`, `/fr/`, `/pt/`).

**The English pages in the root are the only source of truth.** Everything under
the four language folders is generated — never edit a file there by hand, it
will be overwritten.

```bash
# 1. edit the English page as usual, then:
python3 tools/i18n_extract.py     # refresh i18n/strings.en.json (id -> English)
# 2. add the new ids to i18n/de.json, es.json, fr.json, pt.json
python3 tools/i18n_build.py       # regenerate /de /es /fr /pt
python3 tools/i18n_check.py       # assert each copy matches English structurally
python3 tools/i18n_heads.py       # refresh hreflang on the English pages + sitemap.xml
```

A string with no translation falls back to English and is reported by the build,
so a half-translated release is visible rather than silent.

- **Catalog:** `i18n/strings.en.json` maps a short id to each unique English
  string; the shared header, footer and CTA are translated once for all pages.
- **Language switcher:** a `<details>` in the header, generated per page by
  `tools/i18n_lib.py` so the five copies cannot drift. It works without
  JavaScript; `js/main.js` only remembers the choice and closes the panel.
- **Detection:** an inline script in each `<head>` sends a first-time visitor to
  the version their browser asks for, once per session. An explicit choice in
  the switcher is stored in `localStorage` and always wins. Skipped for
  `?mobile=1`, which is the app embedding a legal page.
- **HTML comments are not translated** — they are notes for maintainers and stay
  in English in every build.
