#!/usr/bin/env python3
"""Site-wide audit for things check_site.py does not cover.

check_site.py guards per-page invariants (one <h1>, description length, no broken
references). This covers cross-page and cross-language invariants, which is where
bilingual sites actually break:

  - dead internal links (href/src pointing at files that do not exist)
  - English/Chinese page pairing (a page with only one edition)
  - duplicate <title> / meta description across the whole site
  - canonical self-reference
  - hreflang that disagrees with the target page's canonical
  - orphan pages (no inbound internal link)
  - asset references that 404, and mixed cache-busting versions
  - outlier page weight

Exit code is non-zero when anything fails, so it can gate a commit.

    python scripts/audit.py
"""
import glob
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON = "https://tools.ezaiops.com"
SKIP_DIRS = ("scripts", ".git", "zh_meta")

problems = []


def rel(p):
    return p.replace("\\", "/")


def pages():
    out = []
    for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        r = rel(os.path.relpath(p, ROOT))
        if any(r.startswith(d) for d in SKIP_DIRS):
            continue
        out.append(r)
    return sorted(out)


def read(r):
    return open(os.path.join(ROOT, r), encoding="utf-8").read()


def canon_of(html):
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    return m.group(1) if m else None


def hreflang_of(html):
    return {m.group(1): m.group(2)
            for m in re.finditer(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', html)}


def url_to_rel(url):
    """https://tools.ezaiops.com/zh/ -> zh/index.html ; /about.html -> about.html"""
    if not url.startswith(CANON):
        return None
    path = url[len(CANON):].lstrip("/")
    if path == "" or path.endswith("/"):
        path += "index.html"
    return path


def check_dead_links(all_pages):
    seen = set()
    for pg in all_pages:
        html = re.sub(r"<script.*?</script>", "", read(pg), flags=re.S)
        base = os.path.dirname(os.path.join(ROOT, pg))
        for href in re.findall(r'(?:href|src)="([^"]+)"', html):
            if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "javascript:", "data:")):
                continue
            path = href.split("#")[0].split("?")[0]
            if not path:
                continue
            target = (path.lstrip("/") if path.startswith("/")
                      else rel(os.path.normpath(os.path.join(base, path))))
            if target == "" or target.endswith("/"):
                target += "index.html"
            if not os.path.exists(os.path.join(ROOT, target)):
                key = (href, target)
                if key not in seen:
                    seen.add(key)
                    problems.append("dead link  %s -> %s (missing %s)" % (pg, href, target))


def check_pairing(all_pages):
    en = [p for p in all_pages if not p.startswith("zh/") and p != "404.html"]
    zh = [p[3:] for p in all_pages if p.startswith("zh/")]
    for p in en:
        if p not in zh:
            problems.append("no Chinese edition: %s" % p)
    for p in zh:
        if p not in en:
            problems.append("no English edition: zh/%s" % p)


def check_head(all_pages):
    titles, descs = defaultdict(list), defaultdict(list)
    for pg in all_pages:
        if pg == "404.html":
            continue
        html = read(pg)
        t = re.search(r"<title>(.*?)</title>", html, re.S)
        d = re.search(r'<meta name="description" content="([^"]*)"', html)
        if t:
            titles[t.group(1).strip()].append(pg)
        if d:
            descs[d.group(1).strip()].append(pg)

        want = CANON + "/" + ("" if pg == "index.html" else pg)
        if pg == "zh/index.html":
            want = CANON + "/zh/"
        got = canon_of(html)
        if got != want:
            problems.append("canonical  %s has %s, expected %s" % (pg, got, want))

    for t, pgs in titles.items():
        if len(pgs) > 1:
            problems.append("duplicate <title> %r: %s" % (t[:60], pgs))
    for d, pgs in descs.items():
        if len(pgs) > 1:
            problems.append("duplicate description %r: %s" % (d[:60], pgs))


def check_hreflang(all_pages):
    """Every hreflang must point at the canonical URL of the page it names."""
    for pg in all_pages:
        if pg == "404.html":
            continue
        for lang, href in hreflang_of(read(pg)).items():
            target = url_to_rel(href)
            if target is None:
                problems.append("hreflang  %s: %s points off-site (%s)" % (pg, lang, href))
                continue
            if not os.path.exists(os.path.join(ROOT, target)):
                problems.append("hreflang  %s: %s -> %s (no such page)" % (pg, lang, href))
                continue
            tc = canon_of(read(target))
            if tc != href:
                problems.append("hreflang  %s: %s=%s but that page canonicalises to %s"
                                % (pg, lang, href, tc))


def check_orphans(all_pages):
    linked = set()
    for pg in all_pages:
        html = re.sub(r"<script.*?</script>", "", read(pg), flags=re.S)
        for href in re.findall(r'href="(/[^"#?]*\.html)"', html):
            linked.add(href.lstrip("/"))
    for pg in all_pages:
        if pg == "404.html" or pg.endswith("index.html"):
            continue
        if pg not in linked:
            problems.append("orphan page (no inbound link): %s" % pg)


def check_assets(all_pages):
    versions = Counter()
    for pg in all_pages:
        html = read(pg)
        for m in re.finditer(r'/assets/([a-z.]+)\?v=([0-9a-z]+)', html):
            versions[m.group(2)] += 1
            if not os.path.exists(os.path.join(ROOT, "assets", m.group(1))):
                problems.append("missing asset: %s (referenced by %s)" % (m.group(1), pg))
    if len(versions) > 1:
        problems.append("mixed asset versions: %s" % dict(versions))


def check_chrome(all_pages):
    """The footer must be identical across the hand-written tool pages.

    Tool pages copy the footer into each file, and it has drifted once already:
    seven pages kept recommending models that had been superseded everywhere
    else. Anything that has to change in eighty places falls out of sync.

    Only the tool pages are compared. Header markup carries the breadcrumb, so
    it legitimately differs per page, and the root pages (about/contact/404)
    use a shorter chrome on purpose.
    """
    import hashlib
    for prefix, lang in (("tools/", "en"), ("zh/tools/", "zh")):
        groups = defaultdict(list)
        for pg in all_pages:
            if not pg.startswith(prefix):
                continue
            m = re.search(r"<footer.*?</footer>", read(pg), re.S)
            if m:
                groups[hashlib.md5(m.group(0).encode()).hexdigest()[:8]].append(pg)
        if len(groups) > 1:
            biggest = max(groups.values(), key=len)
            odd = [pg for g in groups.values() if g is not biggest for pg in g]
            problems.append("footer (%s) has %d variants; outliers: %s"
                            % (lang, len(groups), odd[:5]))


def check_weight(all_pages):
    sizes = [(os.path.getsize(os.path.join(ROOT, p)), p) for p in all_pages]
    avg = sum(s for s, _ in sizes) / len(sizes)
    for size, pg in sizes:
        if size > 120 * 1024:
            problems.append("heavy page %.0f KB: %s" % (size / 1024, pg))
    return avg


def main():
    all_pages = pages()
    check_dead_links(all_pages)
    check_pairing(all_pages)
    check_head(all_pages)
    check_hreflang(all_pages)
    check_orphans(all_pages)
    check_assets(all_pages)
    check_chrome(all_pages)
    avg = check_weight(all_pages)

    print("pages: %d (average %.1f KB)" % (len(all_pages), avg / 1024))
    if problems:
        print("\nPROBLEMS (%d):" % len(problems))
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("audit: ALL PASS")


if __name__ == "__main__":
    main()
