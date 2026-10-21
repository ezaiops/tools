#!/usr/bin/env python3
"""Bump the cache-busting ?v= version on shared assets across the site.

Cloudflare caches /assets/* for four hours, so a CSS/JS change does not reach
visitors until either the TTL expires or the version string changes. Run this
whenever you edit assets/style.css, assets/common.js, assets/i18n.js or any
dictionary under assets/i18n/:

    python scripts/bump_assets.py          # stamps a new version everywhere
    python scripts/generate_models.py      # model pages come from a template; regenerate so they pick it up
    node scripts/test_interactive.mjs

Version format: YYYYMMDD + a letter (a, b, c...) if run more than once per day.
"""
import datetime
import glob
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATTERN = re.compile(r"[?&]v=\d{8}[a-z]?")
ASSET_V = re.compile(r'ASSET_V = "\d{8}[a-z]?"')


def files():
    out = glob.glob(os.path.join(ROOT, "*.html"))
    out += glob.glob(os.path.join(ROOT, "tools", "*.html"))
    out += glob.glob(os.path.join(ROOT, "models", "*.html"))
    out.append(os.path.join(ROOT, "scripts", "gen_common.py"))
    out.append(os.path.join(ROOT, "assets", "common.js"))
    out.append(os.path.join(ROOT, "assets", "i18n.js"))
    return out


def next_version(current):
    today = datetime.date.today().strftime("%Y%m%d")
    if current and current.startswith(today):
        suffix = current[8:]
        letter = chr(ord(suffix) + 1) if suffix else "a"
        return today + letter
    return today + "a"


def main():
    current = None
    for f in files():
        m = PATTERN.search(io.open(f, encoding="utf-8").read())
        if m:
            current = m.group(0).split("=")[1]
            break
    new = next_version(current)
    refs = 0
    for f in files():
        s = io.open(f, encoding="utf-8").read()
        out, n = PATTERN.subn("?v=" + new, s)
        out, n2 = ASSET_V.subn('ASSET_V = "' + new + '"', out)
        if n or n2:
            io.open(f, "w", encoding="utf-8").write(out)
            refs += n + n2
    print("%s -> %s (%d references)" % (current or "none", new, refs))


if __name__ == "__main__":
    main()
