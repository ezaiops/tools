#!/usr/bin/env python3
"""Screenshot the key pages and compare them against a stored baseline.

Catches the class of bug that markup validators miss: a stylesheet that stops
loading, a layout that collapses, a table that loses its grid. Text edits also
show up as diffs, so treat a failure as "look at this", not "it is broken".

    python scripts/visual_check.py            # compare against baselines
    python scripts/visual_check.py --update   # (re)record baselines
    python scripts/visual_check.py --page models/deepseek-v4-pro.html

Baselines live in .visual/ and are gitignored: PNG output depends on the local
font stack, so they only mean anything on the machine that recorded them.
"""
import argparse
import functools
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / ".visual"

PAGES = [
    "index.html",
    "models/index.html",
    "models/deepseek-v4-pro.html",
    "models/deepseek-v4-1-flash.html",
    "models/claude-opus-5.html",
    "tools/token-counter.html",
    "tools/subnet-calculator.html",
    "about.html",
]

WIDTH, HEIGHT = 1280, 2400
# Rendering is deterministic on a given machine and browser build, so baseline
# noise is zero and the threshold can be an absolute pixel count rather than a
# percentage. A percentage hides small regressions: the broken <dl> that
# flattened "Cached input" moved only 0.02% of the page, about 600 pixels.
MAX_CHANGED_PIXELS = 500
CHANNEL_DELTA = 12  # ignore sub-perceptual antialiasing noise

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def find_browser():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    for name in ("google-chrome", "chromium", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    sys.exit("no Chrome/Edge found — install one or add its path to CHROME_CANDIDATES")


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(Quiet, directory=str(ROOT))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def shoot(browser, url, dest):
    tmp = Path(tempfile.mkdtemp()) / "shot.png"
    subprocess.run(
        [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=1", "--no-first-run", "--no-default-browser-check",
         f"--window-size={WIDTH},{HEIGHT}", f"--screenshot={tmp}", url],
        capture_output=True, timeout=90,
    )
    if not tmp.exists():
        return False
    shutil.move(str(tmp), str(dest))
    return True


def diff_ratio(a, b):
    """Return (changed pixel count, total pixels, note) for two screenshots."""
    from PIL import Image, ImageChops

    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if ia.size != ib.size:
        return ia.size[0] * ia.size[1], ia.size[0] * ia.size[1], \
            "size changed %s -> %s" % (ia.size, ib.size)
    chans = ImageChops.difference(ia, ib).split()
    f = lambda v: 255 if v > CHANNEL_DELTA else 0
    mask = ImageChops.lighter(ImageChops.lighter(chans[0].point(f), chans[1].point(f)),
                              chans[2].point(f))
    changed = mask.histogram()[255]
    return changed, ia.size[0] * ia.size[1], ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="record new baselines")
    ap.add_argument("--page", action="append", help="only this page (repeatable)")
    args = ap.parse_args()

    try:
        import PIL  # noqa: F401
    except ImportError:
        sys.exit("Pillow is required: pip install Pillow")

    pages = args.page or PAGES
    missing = [p for p in pages if not (ROOT / p).exists()]
    if missing:
        sys.exit("page(s) not found: %s" % ", ".join(missing))

    BASELINE.mkdir(exist_ok=True)
    browser = find_browser()
    httpd, port = serve()
    print("serving %s on 127.0.0.1:%d" % (ROOT.name, port))

    failures, recorded, skipped = [], 0, 0
    try:
        with tempfile.TemporaryDirectory() as td:
            for page in pages:
                url = "http://127.0.0.1:%d/%s" % (port, page)
                shot = Path(td) / (page.replace("/", "_") + ".png")
                if not shoot(browser, url, shot):
                    failures.append((page, 0, "screenshot failed"))
                    continue

                base = BASELINE / (page.replace("/", "_") + ".png")
                if args.update or not base.exists():
                    shutil.copy(str(shot), str(base))
                    recorded += 1
                    print("  %-42s baseline %s" % (page, "updated" if args.update else "created"))
                    continue

                changed, total, note = diff_ratio(base, shot)
                pct = 100.0 * changed / total if total else 0
                if changed > MAX_CHANGED_PIXELS:
                    failures.append((page, changed, note))
                    print("  %-42s CHANGED  %d px (%.2f%%)" % (page, changed, pct))
                    keep = BASELINE / ("_new_" + page.replace("/", "_") + ".png")
                    shutil.copy(str(shot), str(keep))
                    print("      current render kept at %s" % keep.relative_to(ROOT))
                else:
                    skipped += 1
                    print("  %-42s ok       %d px (%.2f%%)" % (page, changed, pct))
    finally:
        httpd.shutdown()

    print("\n%d unchanged, %d baselines written, %d changed" % (skipped, recorded, len(failures)))
    if failures and not args.update:
        print("Pages that moved — open the _new_ file next to the baseline and compare.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
