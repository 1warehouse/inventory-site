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

## Notes

- Fonts load from Google Fonts (Poppins).
- App Store / Google Play badge links are placeholders (`href="#"`) — swap in the real
  store URLs when the apps are published.
- The "Watch demo" button currently scrolls to the product section; point it at the demo
  video when available.