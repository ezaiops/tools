#!/usr/bin/env python3
"""Push scripts/chrome/{header,footer}.html into every hand-written tool page.

The tool pages are hand-written, so their chrome is copied in rather than
generated. That is fine for the page body but not for the chrome: the footer
drifted once already, leaving seven pages advertising models that had been
superseded everywhere else.

Run this after editing either file in scripts/chrome/. The generated pages
(models/, zh/) pick the change up automatically because they read the same
files through gen_common.chrome().

    python scripts/sync_chrome.py          # write changes
    python scripts/sync_chrome.py --check  # exit 1 if anything is out of date
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import ROOT, chrome

PAGES = sorted(glob.glob(os.path.join(ROOT, "tools", "*.html")))

# The root pages (about/contact/privacy/404) deliberately use a shorter footer
# and a slightly different header, so they are not touched here.

HEADER_RE = r'<header class="site-header">.*?</header>'
FOOTER_RE = r'<footer class="site-footer">.*?</footer>'


def main():
    check_only = "--check" in sys.argv
    header, footer = chrome("header"), chrome("footer")

    changed, broken = [], []
    for path in PAGES:
        name = os.path.relpath(path, ROOT).replace("\\", "/")
        html = open(path, encoding="utf-8").read()
        before = html

        html, n_head = re.subn(HEADER_RE, lambda m: header, html, count=1, flags=re.S)
        html, n_foot = re.subn(FOOTER_RE, lambda m: footer, html, count=1, flags=re.S)
        if n_head != 1 or n_foot != 1:
            broken.append("%s (header:%d footer:%d)" % (name, n_head, n_foot))
            continue

        if html != before:
            changed.append(name)
            if not check_only:
                open(path, "w", encoding="utf-8", newline="\n").write(html)

    print("pages: %d | %s: %d" % (len(PAGES), "out of date" if check_only else "updated", len(changed)))
    for name in changed:
        print("  " + name)

    if broken:
        print("\nCould not find the chrome block in:")
        for b in broken:
            print("  " + b)
        return 1

    if check_only and changed:
        print("\nRun `python scripts/sync_chrome.py` to apply.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
