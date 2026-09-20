#!/usr/bin/env python3
"""Render the Open Graph share card, one per language.

    python3 design/share-card/render.py            # all five
    python3 design/share-card/render.py --lang de
    python3 design/share-card/render.py --lang fr --out /tmp

English writes to img/og-cover-1200x630.png; the others to
img/<lang>/og-cover-1200x630.png, which tools/i18n_build.py points each
translated page's og:image and twitter:image at.

The board is the finished 1200 x 630, so this renders at scale 1 — unlike the
app screens, a share card is never displayed larger than it is.
"""

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "lib"))
from shoot import serve, shoot, require_chrome   # noqa: E402

LANGS = ["en", "de", "es", "fr", "pt"]
NAME = "og-cover-1200x630.png"
W, H = 1200, 630


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", action="append", choices=LANGS, help="default: all")
    ap.add_argument("--out", help="write here instead of img/ (to eyeball a change)")
    args = ap.parse_args()
    langs = args.lang or LANGS
    require_chrome()

    # Served from design/ so ../fonts and ../lib resolve.
    httpd, port = serve(HERE.parent)
    try:
        for lang in langs:
            if not (HERE / "content" / f"{lang}.json").exists():
                sys.exit(f"missing content/{lang}.json")
            if args.out:
                dest = Path(args.out) / (f"{lang}-{NAME}" if len(langs) > 1 else NAME)
            else:
                dest = ROOT / "img" / NAME if lang == "en" else ROOT / "img" / lang / NAME
            url = f"http://127.0.0.1:{port}/share-card/index.html?lang={lang}"
            shoot(url, W, H, dest, scale=1, label=f"share card/{lang}")
            print(f"{lang:>3}  -> {dest if args.out else dest.relative_to(ROOT)}")
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
