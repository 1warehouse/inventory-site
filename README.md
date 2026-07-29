# 1inventory.io

Static marketing site for **1Inventory** — a Google Sheets–based inventory management app by
Sparkybit GmbH. Migrated from Wix Studio to a plain static site for **Cloudflare Pages**.

## Structure

```
.
├── index.html          # Home (single-page marketing site)
├── terms.html          # Terms and conditions
├── privacy.html        # Privacy policy
├── 404.html            # Not-found page
├── css/style.css       # Design system + all styles
├── js/main.js          # Header, mobile menu, scroll reveals
├── img/                # Optimised, clean-named images & icons
├── data/1inv_faq.json  # Bilingual FAQ data (en/es)
├── assets/             # Original raw asset download from Wix (source of truth)
├── _headers            # Cloudflare Pages caching & security headers
├── _redirects          # Legacy Wix path redirects
├── .well-known/        # iOS/Android app deep-link verification files
├── robots.txt
└── sitemap.xml
```

## Local preview

Any static file server works, e.g.:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploy to Cloudflare Pages

This is a no-build static site — point Cloudflare Pages at the repository:

- **Build command:** *(leave empty)*
- **Build output directory:** `/` (repository root)

Direct upload alternative:

```bash
npx wrangler pages deploy . --project-name 1inventory
```

`_headers` and `_redirects` are picked up automatically by Cloudflare Pages.

## App deep links (`.well-known/`)

The mobile app opens `https://1inventory.io/inventories/<id>/alerts` links (alert emails / pushes).
For iOS Universal Links and Android App Links to verify, this site serves:

- `/.well-known/apple-app-site-association` — app ID `7MBRQ3583S.com.sparkybit.oneinventory.prod`.
  The file has no extension; `_headers` forces `Content-Type: application/json`.
- `/.well-known/assetlinks.json` — package `com.sparkybit.oneinventory`. **Before this works**,
  replace `REPLACE_WITH_PLAY_APP_SIGNING_CERT_SHA256` with the SHA-256 from Play Console →
  Setup → App signing → "App signing key certificate" (colon-separated uppercase hex). If release
  builds are also installed directly (signed by the CI upload key), add that key's SHA-256 as a
  second array entry.

Both URLs must return 200 on `1inventory.io` **without redirects** (verification fetchers don't
follow them) — keep that in mind for any www ↔ apex redirect rules in Cloudflare. Verify with
`curl https://app-site-association.cdn-apple.com/a/v1/1inventory.io` and
`adb shell pm get-app-links com.sparkybit.oneinventory`.

## Notes

- Fonts load from Google Fonts (Poppins).
- App Store / Google Play badge links are placeholders (`href="#"`) — swap in the real
  store URLs when the apps are published.
- The "Watch demo" button currently scrolls to the product section; point it at the demo
  video when available.