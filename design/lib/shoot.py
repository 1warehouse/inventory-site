#!/usr/bin/env python3
"""Photograph a local page with headless Chrome — shared by the render scripts.

Chrome is the renderer rather than a converter like rsvg because the artwork
uses webfonts and the fitting pass in lib/fit.js measures text, which needs a
real layout engine.
"""

import http.server
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(directory):
    """Chrome must fetch the template and the content JSON, which file:// forbids."""
    handler = lambda *a, **kw: _QuietHandler(*a, directory=str(directory), **kw)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def require_chrome():
    if not Path(CHROME).exists():
        sys.exit(f"Google Chrome not found at {CHROME}")


def shoot(url, width, height, dest, scale=2, label=""):
    """Capture `url` at width x height * scale into `dest` (.png or .webp)."""
    with tempfile.TemporaryDirectory() as profile:
        png = Path(profile) / "shot.png"
        cmd = [
            CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
            f"--user-data-dir={profile}",
            f"--screenshot={png}",
            f"--window-size={width},{height}",
            f"--force-device-scale-factor={scale}",
            "--default-background-color=00000000",
            "--virtual-time-budget=2000",
            # Chrome lingers after writing the file; these keep the run short
            # and stop it reaching the network on the way up.
            "--no-first-run", "--no-default-browser-check", "--disable-extensions",
            "--disable-background-networking", "--disable-sync", "--disable-component-update",
            "--disable-crash-reporter", "--disable-features=Translate,MediaRouter",
            url,
        ]
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
            sys.exit(f"chrome produced no image for {label or url}\n{(err or '')[-800:]}")

        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.suffix == ".webp":
            subprocess.run(["magick", str(png), "-quality", "92", str(dest)], check=True)
        else:
            shutil.move(str(png), dest)
