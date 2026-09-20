#!/usr/bin/env python3
"""Check every screen, in every language, before rendering.

    python3 design/check.py

Three things go wrong when a translation lands, and none of them are visible
in a diff:

  missing    a token with no string behind it — the artwork shows {{a.b}}
  overlap    two texts on the same line collide; fitting keeps a string inside
             its own box but knows nothing about its neighbour
  shrunk     a label had to shrink to fit; not a failure, but worth reading,
             and a size at the 9.5 floor is usually a sign the string is too
             long for its box rather than slightly too long

Exits non-zero if anything is missing or overlapping, so it can gate a render.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
from shoot import serve, require_chrome, CHROME   # noqa: E402

import subprocess   # noqa: E402
import tempfile     # noqa: E402
import time        # noqa: E402

LANGS = ["en", "de", "es", "fr", "pt"]
PAGES = [("app-screens", "screens"), ("share-card", "card")]


def read_state(port, folder, lang):
    """Load a gallery page headless and read what it reported on <body>."""
    with tempfile.TemporaryDirectory() as profile:
        dump = Path(profile) / "page.html"
        url = f"http://127.0.0.1:{port}/{folder}/index.html?lang={lang}"
        # Chrome prints the DOM and then sits there, exactly as --screenshot
        # does, so wait for the page to say it is finished and kill it.
        with dump.open("w") as out:
            proc = subprocess.Popen([
                CHROME, "--headless", "--disable-gpu", f"--user-data-dir={profile}",
                "--dump-dom", "--virtual-time-budget=6000", "--no-first-run",
                "--disable-extensions", "--disable-background-networking",
                "--disable-sync", "--disable-component-update", "--disable-crash-reporter",
                url,
            ], stdout=out, stderr=subprocess.DEVNULL)
            deadline = time.time() + 60
            while time.time() < deadline:
                if 'data-ready="1"' in dump.read_text(errors="replace"):
                    break
                if proc.poll() is not None:
                    break
                time.sleep(0.25)
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        html = dump.read_text(errors="replace")

    def attr(name):
        m = re.search(rf'data-{name}="([^"]*)"', html)
        return m.group(1).replace("&amp;", "&").replace("&quot;", '"') if m else ""

    return {"ready": 'data-ready="1"' in html, "missing": attr("missing"),
            "overlaps": attr("overlaps"), "shrunk": attr("shrunk")}


def main():
    require_chrome()
    httpd, port = serve(HERE)
    problems = 0
    try:
        for folder, _ in PAGES:
            for lang in LANGS:
                if not (HERE / folder / "content" / f"{lang}.json").exists():
                    continue
                s = read_state(port, folder, lang)
                head = f"{folder}/{lang}"
                if not s["ready"]:
                    print(f"{head}: page did not finish rendering")
                    problems += 1
                    continue
                for kind in ("missing", "overlaps"):
                    if s[kind]:
                        problems += 1
                        print(f"{head}: {kind.upper()}")
                        for item in s[kind].split(" | "):
                            print(f"    {item}")
                if s["shrunk"]:
                    for item in s["shrunk"].split(" | "):
                        print(f"{head}: shrunk  {item}")
                if not (s["missing"] or s["overlaps"] or s["shrunk"]):
                    print(f"{head}: clean")
    finally:
        httpd.shutdown()

    print()
    print("problems:", problems or "none")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
