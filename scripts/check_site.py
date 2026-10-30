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
# scripts/chrome/ holds HTML fragments (header, footer), not pages: they have no
# <head>, no title and must not be checked as standalone documents.
pages = sorted(p for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)
               if not os.path.relpath(p, ROOT).replace("\\", "/").startswith("scripts/"))
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

    is_zh = name.startswith("zh/")
    # Chinese carries more meaning per character, so the floor is lower than the
    # English one. Both still have to clear a minimum to be useful in a SERP.
    min_desc = 30 if is_zh else 40
    desc = re.search(r'<meta name="description" content="([^"]*)"', text)
    if not desc or len(desc.group(1)) < min_desc:
        problems.append("%s: missing or too short meta description" % name)

    want_lang = "zh-CN" if is_zh else "en"
    # Match the attribute, not the exact tag: the /zh/ pages carry extra
    # attributes on <html> (data-zh-static).
    if not re.search(r'<html[^>]*\blang="%s"' % want_lang, text):
        problems.append('%s: missing <html lang="%s">' % (name, want_lang))

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

    # <dl> may only contain <dt>/<dd> (or a wrapping <div>). Table rows inside a
    # definition list are silently flattened by browsers, which is how "Cached
    # input$0.022" ended up rendered as one run of text on every model page.
    for dl in re.findall(r"<dl[^>]*>(.*?)</dl>", text, re.S):
        inner = dl.strip()
        if not inner:
            continue  # populated at runtime, e.g. #sn-results on the subnet page
        stray = re.findall(r"<(tr|td|th|li|p)[ >]", inner)
        if stray:
            problems.append("%s: invalid <%s> inside <dl> — use <dt>/<dd>"
                            % (name, stray[0]))
        elif not re.search(r"<d[td][ >]", inner):
            problems.append("%s: <dl> with no <dt>/<dd> children" % name)

expected = [BASE + "/"]
for page in pages:
    # Each home page is listed once, as a directory URL — listing /index.html as
    # well would ask crawlers to index the same page under two URLs.
    r = rel(page)
    if r == "zh/index.html":
        expected.append(BASE + "/zh/")
        continue
    if r in ("index.html", "404.html"):
        continue
    expected.append(BASE + "/" + r)

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
