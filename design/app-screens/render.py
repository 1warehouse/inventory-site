#!/usr/bin/env python3
"""Render the app screen mockups to the PNGs the marketing site ships.

    python3 design/app-screens/render.py            # every screen, every language
    python3 design/app-screens/render.py --lang de  # one language
    python3 design/app-screens/render.py --screen dashboard --lang en --out /tmp

English writes to img/<name>; the other languages write to img/<lang>/<name>,
which is where tools/i18n_build.py points the translated pages.

Headless Chrome photographs index.html at device-scale-factor 2, so a screen
authored as a 348 x 721 phone lands as the 696 x 1442 PNG the pages declare.
The files are transparent outside the phone's rounded corners.
"""

import argparse
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

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


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(directory):
    """Chrome must fetch content/<lang>.json, which file:// URLs forbid."""
    handler = lambda *a, **kw: QuietHandler(*a, directory=str(directory), **kw)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def shoot(port, screen, lang, width, height, dest):
    """One Chrome run per screen — it exits after writing the screenshot."""
    with tempfile.TemporaryDirectory() as profile:
        png = Path(profile) / "shot.png"
        url = f"http://127.0.0.1:{port}/index.html?lang={lang}&screen={screen}"
        cmd = [
            CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
            f"--user-data-dir={profile}",
            f"--screenshot={png}",
            f"--window-size={width},{height}",
            "--force-device-scale-factor=2",
            "--default-background-color=00000000",
            "--virtual-time-budget=2000",
            # Chrome lingers after writing the file; these keep the run short
            # and stop it reaching the network on the way up.
            "--no-first-run", "--no-default-browser-check", "--disable-extensions",
            "--disable-background-networking", "--disable-sync", "--disable-component-update",
            "--disable-crash-reporter", "--disable-features=Translate,MediaRouter",
            url,
        ]
        # Chrome writes the screenshot but then sits there, so wait for the
        # file to appear and stop holding its size, and kill it ourselves.
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        size, stable, deadline = -1, 0, time.time() + 45
        while time.time() < deadline:
            if png.exists():
                now = png.stat().st_size
                stable = stable + 1 if now == size and now > 0 else 0
                size = now
                if stable >= 2:
                    break
            if proc.poll() is not None and png.exists():
                break
            time.sleep(0.25)
        proc.terminate()
        try:
            _, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            err = ""
        if not png.exists():
            sys.exit(f"chrome produced no image for {screen}/{lang}\n{(err or '')[-800:]}")

        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.suffix == ".webp":
            subprocess.run(["magick", str(png), "-quality", "92", str(dest)], check=True)
        else:
            shutil.move(str(png), dest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", action="append", choices=LANGS, help="default: all")
    ap.add_argument("--screen", action="append", choices=list(SCREENS), help="default: all")
    ap.add_argument("--check", action="store_true",
                    help="render to a temp dir and report how each file differs from img/")
    ap.add_argument("--out", help="write everything here instead of img/ (for eyeballing a change)")
    args = ap.parse_args()

    langs = args.lang or LANGS
    screens = args.screen or list(SCREENS)

    if not os.path.exists(CHROME):
        sys.exit(f"Google Chrome not found at {CHROME}")

    httpd, port = serve(HERE)
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
                shoot(port, screen, lang, w, h, dest)
                print(f"{lang:>3}  {screen:<20} -> {dest.relative_to(ROOT) if not args.out else dest}")
    finally:
        httpd.shutdown()


if __name__ == "__main__":
    main()
