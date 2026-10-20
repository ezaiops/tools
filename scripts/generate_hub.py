#!/usr/bin/env python3
"""Regenerate the hub tool grid from scripts/tools.json.

Adding a new tool:
  1. build the page under tools/
  2. add an entry to scripts/tools.json (status: live, group, icon)
  3. run this script, then commit (the post-commit hook pushes)

Icons are inline SVG on a 24x24 grid with 1.5px strokes. They live here rather
than in the manifest so the JSON stays readable and every icon shares the same
geometry. Add a new id to ICONS when you add a tool.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GROUPS = [
    ("ai", "AI &amp; LLM"),
    ("text", "Text &amp; data"),
    ("time", "Time &amp; scheduling"),
    ("net", "Network &amp; security"),
    ("files", "Files &amp; media"),
    ("calc", "Calculators"),
]

ICONS = {
    "token-counter": '<circle cx="9" cy="9" r="5.5"/><path d="M18.2 11.4A5.5 5.5 0 1 1 11.4 18.2"/><path d="M8 6.8v4.4M6.2 9h3.6"/>',
    "self-host-vs-api": '<rect x="2.5" y="3.5" width="19" height="7" rx="2"/><rect x="2.5" y="13.5" width="19" height="7" rx="2"/><path d="M6 7h.01M6 17h.01"/>',
    "json-formatter": '<path d="M8.5 3H7a2 2 0 0 0-2 2v4a2 2 0 0 1-2 2 2 2 0 0 1 2 2v4a2 2 0 0 0 2 2h1.5"/><path d="M15.5 3H17a2 2 0 0 1 2 2v4a2 2 0 0 0 2 2 2 2 0 0 0-2 2v4a2 2 0 0 1-2 2h-1.5"/>',
    "regex-tester": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M20.5 20.5 15.6 15.6"/><path d="M7.5 10.5h6M10.5 7.5v6"/>',
    "diff-checker": '<path d="M6 3v18M18 3v18"/><path d="M2.5 8h7M2.5 16h7M14.5 8h7M14.5 16h7"/>',
    "encode-decode": '<path d="M3 8h15l-3.5-3.5M21 16H6l3.5 3.5"/>',
    "meta-tag-generator": '<path d="M20.6 13.4 12.6 21.4a2 2 0 0 1-2.8 0L2.6 14.2a2 2 0 0 1-.6-1.4V4a2 2 0 0 1 2-2h8.8a2 2 0 0 1 1.4.6l6.4 6.4a2 2 0 0 1 0 2.8z"/><circle cx="7.5" cy="7.5" r="1.4"/>',
    "timestamp-converter": '<circle cx="12" cy="12" r="9"/><path d="M12 6.5V12l3.5 2"/>',
    "cron-explainer": '<rect x="3" y="4.5" width="18" height="16.5" rx="2"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4"/><path d="M9 14h.01M12 14h.01M15 14h.01M9 17h.01M12 17h.01"/>',
    "cron-generator": '<rect x="3" y="4.5" width="18" height="16.5" rx="2"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4M12 13v5M9.5 15.5h5"/>',
    "subnet-calculator": '<circle cx="12" cy="4.5" r="2.2"/><circle cx="4.8" cy="19" r="2.2"/><circle cx="19.2" cy="19" r="2.2"/><path d="M12 6.7v5.6M12 12.3 6.4 16.9M12 12.3l5.6 4.6"/>',
    "jwt-debugger": '<circle cx="8" cy="15.5" r="4.5"/><path d="M11.2 12.3 20 3.5M16.5 7l2.2 2.2M13.8 9.7l2.2 2.2"/>',
    "password-generator": '<rect x="4" y="10" width="16" height="11" rx="2.5"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/><path d="M12 14.5v2.5"/>',
    "image-compressor": '<rect x="3" y="3.5" width="18" height="17" rx="2.5"/><circle cx="8.5" cy="9" r="1.6"/><path d="m21 15.5-4.5-4.5L5.5 20.5"/>',
    "pdf-tools": '<path d="M14 2.5H6.5a2 2 0 0 0-2 2v15a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V8z"/><path d="M14 2.5V8h5.5"/><path d="M8.5 13h7M8.5 16.5h4.5"/>',
    "qr-generator": '<rect x="3" y="3" width="7" height="7" rx="1.2"/><rect x="14" y="3" width="7" height="7" rx="1.2"/><rect x="3" y="14" width="7" height="7" rx="1.2"/><path d="M14 14h3.5v3.5H14zM20.5 14h.5M14 20.5h3.5M20.5 20.5h.5"/>',
    "unit-converter": '<path d="M3 12h18M7.5 7.5 3 12l4.5 4.5M16.5 7.5 21 12l-4.5 4.5"/>',
    "mortgage-calculator": '<path d="M19.5 4.5 4.5 19.5"/><circle cx="7.5" cy="7.5" r="2.6"/><circle cx="16.5" cy="16.5" r="2.6"/>',
}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def icon_svg(tid):
    path = ICONS.get(tid)
    if not path:
        path = '<rect x="4" y="4" width="16" height="16" rx="3"/>'
    return ('<span class="tool-icon" aria-hidden="true"><svg viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
            'stroke-linejoin="round">%s</svg></span>' % path)


def card(t):
    search = " ".join([t["name"], t.get("desc", ""), t.get("group", "")]).lower()
    return ('<a class="tool-card-item" href="%s" data-name="%s">%s'
            '<span class="tool-card-body"><span class="tool-card-title">%s</span>'
            '<span class="tool-card-desc">%s</span></span></a>'
            % (t["url"], esc(search), icon_svg(t["id"]), esc(t["name"]), esc(t.get("desc", ""))))


def section(group_id, label, items):
    cards = "\n      ".join(card(t) for t in items)
    return ('<section class="tool-group" data-group="%s">\n'
            '    <h2 class="group-title">%s</h2>\n'
            '    <div class="tool-grid">\n      %s\n    </div>\n'
            '  </section>' % (group_id, label, cards))


def fill(path, start_marker, end_marker, block):
    with open(path, encoding="utf-8") as fh:
        s = fh.read()
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
    if not pattern.search(s):
        raise SystemExit("markers not found in %s (%s)" % (path, start_marker))
    s = pattern.sub(lambda m: start_marker + "\n  " + block + "\n  " + end_marker, s, count=1)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(s)


def main():
    with open(os.path.join(ROOT, "scripts", "tools.json"), encoding="utf-8") as fh:
        tools = json.load(fh)["tools"]
    live = [t for t in tools if t.get("status", "live") == "live"]

    order = {gid: i for i, (gid, _) in enumerate(GROUPS)}
    blocks = []
    for gid, label in GROUPS:
        items = [t for t in live if t.get("group") == gid]
        if items:
            blocks.append(section(gid, label, items))
    other = [t for t in live if t.get("group") not in order]
    if other:
        blocks.append(section("other", "More", other))

    idx = os.path.join(ROOT, "index.html")
    fill(idx, "<!-- TOOLS-GRID:START -->", "<!-- TOOLS-GRID:END -->", "\n  ".join(blocks))
    print("hub grid: %d tools in %d groups" % (len(live), len(blocks)))


if __name__ == "__main__":
    main()
