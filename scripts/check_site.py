#!/usr/bin/env python3
"""Static site checks for tools.ezaiops.com: links, titles, h1, JSON-LD, sitemap."""
import glob
import json
import os
import re
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://tools.ezaiops.com"

problems = []
pages = sorted(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True))
titles = {}


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def local_target(href, page_dir):
    u = urlparse(href)
    if u.scheme or u.netloc or href.startswith(("mailto:", "tel:", "data:", "#")):
        return None
    p = u.path
    if not p:
        return None
    if p.startswith("/"):
        return os.path.join(ROOT, p.lstrip("/"))
    return os.path.normpath(os.path.join(page_dir, p))


for page in pages:
    text = open(page, encoding="utf-8").read()
    name = rel(page)
    page_dir = os.path.dirname(page)

    m = re.search(r"<title>(.*?)</title>", text, re.S)
    title = m.group(1).strip() if m else ""
    if not title:
        problems.append("%s: missing <title>" % name)
    if title in titles:
        problems.append("%s: duplicate title (also on %s): %s" % (name, titles[title], title[:50]))
    titles[title] = name

    h1 = re.findall(r"<h1[ >]", text)
    if len(h1) != 1:
        problems.append("%s: expected exactly 1 <h1>, found %d" % (name, len(h1)))

    desc = re.search(r'<meta name="description" content="([^"]*)"', text)
    if not desc or len(desc.group(1)) < 40:
        problems.append("%s: missing or too short meta description" % name)

    if "<html lang=\"en\">" not in text:
        problems.append("%s: missing <html lang=\"en\">" % name)

    text_no_scripts = re.sub(r"<script.*?</script>", "", text, flags=re.S)
    for href in re.findall(r'(?:href|src)="([^"]+)"', text_no_scripts):
        tgt = local_target(href, page_dir)
        if tgt and not os.path.exists(tgt):
            problems.append("%s: broken reference %s" % (name, href))

    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
        try:
            json.loads(block)
        except Exception as e:
            problems.append("%s: invalid JSON-LD: %s" % (name, e))

    if name.startswith("models/") and name != "models/index.html":
        slug = os.path.basename(name)[:-5]
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', text)
        if not canon or not canon.group(1).endswith("/models/%s.html" % slug):
            problems.append("%s: canonical URL does not point at itself" % name)

expected = [BASE + "/"]
for page in pages:
    # The home page is listed once, as "/" — listing /index.html as well would ask
    # crawlers to index the same page under two URLs.
    if rel(page) in ("index.html", "404.html"):
        continue
    expected.append(BASE + "/" + rel(page))

sitemap_path = os.path.join(ROOT, "sitemap.xml")
if not os.path.exists(sitemap_path):
    problems.append("sitemap.xml missing")
else:
    sm = open(sitemap_path, encoding="utf-8").read()
    locs = re.findall(r"<loc>(.*?)</loc>", sm)
    loc_set = set(locs)
    if len(locs) != len(loc_set):
        problems.append("sitemap.xml has duplicate URLs")
    for u in expected:
        if u not in loc_set:
            problems.append("sitemap.xml missing %s" % u)
    for u in locs:
        if u not in set(expected):
            problems.append("sitemap.xml has unknown URL %s" % u)

for extra in ["robots.txt", "ads.txt", "CNAME", ".nojekyll"]:
    if not os.path.exists(os.path.join(ROOT, extra)):
        problems.append("%s missing" % extra)

# The hub search and the tool toggles hide elements with the hidden attribute,
# which only works because style.css overrides author flex/grid display rules.
css_text = open(os.path.join(ROOT, "assets", "style.css"), encoding="utf-8").read()
if "[hidden] { display: none" not in css_text:
    problems.append("assets/style.css lost the [hidden] display rule — JS-driven hiding (search filter, tool toggles) will silently stop working")

print("pages checked: %d" % len(pages))
print("sitemap entries: %d" % len(locs))
if problems:
    print("\nPROBLEMS (%d):" % len(problems))
    for p in problems:
        print("  - %s" % p)
    sys.exit(1)
print("static checks: ALL PASS")
