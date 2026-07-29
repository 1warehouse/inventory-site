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
