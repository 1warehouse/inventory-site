#!/usr/bin/env python3
"""Render the app screen mockups to the PNGs the marketing site ships.

    python3 design/app-screens/render.py              # every screen, every language
    python3 design/app-screens/render.py --lang de    # one language
    python3 design/app-screens/render.py --screen 6a --out /tmp   # one screen, elsewhere

English writes to img/<name>; the other languages write to img/<lang>/<name>,
which is where tools/i18n_build.py points the translated pages.

A phone board is 348 x 721 and is photographed at device-scale-factor 2, which
is the 696 x 1442 the pages declare. The files are transparent outside the
phone's rounded corners.
"""

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "lib"))
from shoot import serve, shoot, require_chrome   # noqa: E402

LANGS = ["en", "de", "es", "fr", "pt"]

# template id -> (output file name, svg width, svg height). The PNG is twice this.
SCREENS = {
    "2c":  ("app-home.png", 620, 820),
    "3a":  ("scan-barcode-wt.png", 348, 721),
    "3b":  ("scan-search-wt.png", 348, 721),
    "3c":  ("scan-search-results-wt.png", 348, 721),
    "4a":  ("search-wt.png", 348, 721),
    "4b":  ("locations-list-wt.png", 348, 721),
    "5a":  ("edit-count-wt.png", 348, 721),
    "6a":  ("dashboard-wt.png", 348, 721),
    "6b":  ("history-wt.png", 348, 721),
    "6c":  ("alert-wt.png", 348, 721),
    "7a":  ("custom-fields-wt.png", 348, 721),
    "7b":  ("users-wt.png", 348, 721),
    "10a": ("gsheet.webp", 572, 400),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", action="append", choices=LANGS, help="default: all")
    ap.add_argument("--screen", action="append", choices=list(SCREENS), help="default: all")
    ap.add_argument("--out", help="write everything here instead of img/ (to eyeball a change)")
    args = ap.parse_args()

    langs = args.lang or LANGS
    screens = args.screen or list(SCREENS)
    require_chrome()

    # Served from design/, not design/app-screens/, so ../fonts and ../lib
    # resolve — a static server will not follow a path out of its root.
    httpd, port = serve(HERE.parent)
    try:
        for lang in langs:
            if not (HERE / "content" / f"{lang}.json").exists():
                sys.exit(f"missing content/{lang}.json")
            for screen in screens:
                name, w, h = SCREENS[screen]
                if args.out:
                    dest = Path(args.out) / (f"{lang}-{name}" if len(langs) > 1 else name)
                else:
                    dest = ROOT / "img" / name if lang == "en" else ROOT / "img" / lang / name
                url = f"http://127.0.0.1:{port}/app-screens/index.html?lang={lang}&screen={screen}"
                shoot(url, w, h, dest, label=f"{screen}/{lang}")
                print(f"{lang:>3}  {screen:<4} -> {dest if args.out else dest.relative_to(ROOT)}")
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
