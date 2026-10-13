#!/usr/bin/env python3
"""Regenerate the hub tool grid and the roadmap section from scripts/tools.json.

Adding a new tool:
  1. build the page under tools/
  2. add an entry to scripts/tools.json (status: live)
  3. run this script, then commit (the post-commit hook pushes)
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def card(t):
    inner = ('<h3><span class="icon">%s</span>%s</h3><p>%s</p>'
             % (esc(t.get("icon", "*")), esc(t["name"]), esc(t.get("desc", ""))))
    if t.get("status", "live") == "live":
        tags = "".join('<span class="badge%s">%s</span>' % (" blue" if b == "featured" else "", esc(b))
                       for b in t.get("tags", []))
        if tags:
            inner += '<div class="tags">%s</div>' % tags
        return '<a class="tool-card-item" href="%s">%s</a>' % (t["url"], inner)

    badge = '<span class="badge amber">roadmap</span>'
    if t.get("effort"):
        badge += '<span class="badge">%s build</span>' % esc(t["effort"])
    inner += '<div class="tags">%s</div>' % badge
    return '<div class="tool-card-item planned">%s</div>' % inner


def fill(path, start_marker, end_marker, items):
    with open(path, encoding="utf-8") as fh:
        s = fh.read()
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
    if not pattern.search(s):
        raise SystemExit("markers not found in %s (%s)" % (path, start_marker))
    block = start_marker + "\n    " + "\n    ".join(card(t) for t in items) + "\n    " + end_marker
    s = pattern.sub(lambda m: block, s, count=1)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(s)


def main():
    with open(os.path.join(ROOT, "scripts", "tools.json"), encoding="utf-8") as fh:
        tools = json.load(fh)["tools"]
    live = [t for t in tools if t.get("status", "live") == "live"]
    planned = sorted((t for t in tools if t.get("status") == "planned"),
                     key=lambda t: (t.get("priority", 9), t.get("effort", "L")))
    idx = os.path.join(ROOT, "index.html")
    fill(idx, "<!-- TOOLS-GRID:START -->", "<!-- TOOLS-GRID:END -->", live)
    fill(idx, "<!-- ROADMAP:START -->", "<!-- ROADMAP:END -->", planned)
    print("hub grid: %d live tools, %d on the roadmap" % (len(live), len(planned)))


if __name__ == "__main__":
    main()
