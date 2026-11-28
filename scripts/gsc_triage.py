#!/usr/bin/env python3
"""Triage the URLs Google reports under Page indexing > Crawled, not indexed.

The Coverage export in GSC only contains counts, not the URL list. Export the
URLs from the report itself (Page indexing -> click a reason -> Export), save
that CSV, then run:

    python scripts/gsc_triage.py path/to/exported-urls.csv

The script classifies every URL against the local site and tells you which ones
are genuinely fixable (dead URL, redirect chain, wrong canonical) versus which
are language variants that are working as designed.

Two modes:
  - default: triage a GSC URL export
  - --site:  show the full local URL inventory with canonical/redirect facts,
             useful when you have not exported the GSC list yet
"""
import csv
import os
import re
import sys
from collections import Counter
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "tools.ezaiops.com"

CANON_RE = re.compile(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)', re.I)


def local_path(url):
    """Map a tools.ezaiops.com URL to a local file path, or None."""
    u = urlparse(url)
    host = u.netloc or (u.path.split("/")[0] if url.startswith("/") else "")
    if host and BASE not in host:
        return None
    path = u.path or "/"
    if path == "/":
        path = "/index.html"
    elif path.endswith("/"):
        path += "index.html"
    return os.path.join(ROOT, path.lstrip("/"))


def canonical_of(path):
    try:
        with open(path, encoding="utf-8") as fh:
            m = CANON_RE.search(fh.read())
            return m.group(1) if m else None
    except OSError:
        return None


def classify(url):
    u = urlparse(url)
    qs = parse_qs(u.query)
    path = u.path

    if "lang" in qs:
        # The static file's canonical is the English self-reference. At runtime
        # assets/i18n.js rewrites it to the /zh/ sibling for pages that have one.
        # Derive the expected runtime target from the URL path instead.
        target = None
        parts = path.strip("/").split("/")
        if parts[0] != "zh":
            parts.insert(0, "zh")
        candidate = os.path.join(ROOT, *parts)
        if os.path.exists(candidate):
            target = "https://%s/%s" % (BASE, "/".join(parts))
        return ("language-variant",
                "?lang=zh view; JS points canonical at the static /zh/ page",
                target)

    p = local_path(url)
    if p is None:
        return ("external", "not a tools.ezaiops.com URL", None)

    if not os.path.exists(p):
        # common redirect shapes
        if path.endswith("/index.html") and os.path.exists(p[:-len("index.html")].rstrip("/\\")):
            return ("redirect", "/index.html -> directory form", None)
        return ("missing", "no local file; check if this URL was retired or renamed", None)

    canon = canonical_of(p)
    if canon:
        cp = urlparse(canon).path
        if cp != path and not (cp == "/" and path in ("/", "/index.html")):
            return ("canonical-differs", "canonical points at a different page", canon)

    return ("ok", "live page with self-canonical", canon)


def read_urls(path):
    urls = []
    if path.lower().endswith(".zip"):
        print("This is a zip. GSC's zipped Coverage export contains only counts,")
        print("not the URL list. Open the report, click the reason, and use")
        print("Export > Download CSV there; then feed that CSV to this script.")
        return []
    try:
        raw = open(path, "rb").read()
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("gbk")
        except UnicodeDecodeError:
            print("Could not decode %s as UTF-8 or GBK." % path)
            return []
    delim = ";" if text[:4096].count(";") > text[:4096].count(",") else ","
    for row in csv.reader(text.splitlines(), delimiter=delim):
        for cell in row:
            cell = cell.strip()
            if cell.startswith("http") or cell.startswith("/"):
                urls.append(cell)
                break
    # de-duplicate, keep order
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def show_site_inventory():
    rows = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "scripts")]
        for f in sorted(files):
            if not f.endswith(".html"):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            url = "https://%s/%s" % (BASE, rel)
            rows.append((url, canonical_of(full)))
    rows.sort()
    print("%-72s %s" % ("URL", "canonical"))
    for url, canon in rows:
        print("%-72s %s" % (url, canon or "(none)"))
    print("\ntotal local pages: %d" % len(rows))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    if sys.argv[1] == "--site":
        show_site_inventory()
        return 0

    urls = read_urls(sys.argv[1])
    if not urls:
        if not sys.argv[1].lower().endswith(".zip"):
            print("No URLs found in %s" % sys.argv[1])
        return 1

    results = [(u, classify(u)) for u in urls]
    counts = Counter(r[1][0] for r in results)
    print("URLs read: %d\n" % len(urls))
    print("classification summary:")
    for kind, n in counts.most_common():
        print("  %-18s %d" % (kind, n))

    print("\ndetail (fix these first):")
    for url, (kind, note, target) in results:
        if kind in ("missing", "redirect", "canonical-differs", "external"):
            print("  [%s] %s" % (kind, url))
            print("         %s%s" % (note, " -> %s" % target if target else ""))

    print("\nlanguage variants (expected, no action):")
    for url, (kind, note, target) in results:
        if kind == "language-variant":
            print("  %s -> %s" % (url, target or "(canonical not set in local file)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
