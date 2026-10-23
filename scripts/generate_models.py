#!/usr/bin/env python3
"""Part 2: per-model page rendering, comparison hub, sitemap."""
import datetime
import glob
import json
import os
from gen_common import (ROOT, BASE, TODAY, UPDATED, MODELS, SOURCES, BY_ID,
                        COMPARISONS, money, blended, esc, HEAD, CRUMBS, FOOT)

CALC_JS = """<script>
document.addEventListener("DOMContentLoaded", function () {
  var models = (window.EZ_MODELS || {}).models || [];
  var me = null;
  for (var i = 0; i < models.length; i++) if (models[i].id === "@@ID@@") me = models[i];
  if (!me) return;
  var inEl = document.getElementById("mc-in");
  var outEl = document.getElementById("mc-out");
  function fmt(n) {
    if (n <= 0) return "$0";
    if (n < 0.000001) return "<$0.000001";
    var d = n < 0.01 ? 6 : n < 1 ? 4 : 2;
    return "$" + n.toFixed(d);
  }
  function recalc() {
    var ti = Math.max(0, parseFloat(inEl.value || "0") || 0);
    var to = Math.max(0, parseFloat(outEl.value || "0") || 0);
    document.getElementById("mc-cost").textContent = fmt(ti * me.input / 1e6 + to * me.output / 1e6);
    document.getElementById("mc-1k").textContent = fmt((ti * me.input / 1e6 + to * me.output / 1e6) * 1000);
  }
  inEl.addEventListener("input", recalc);
  outEl.addEventListener("input", recalc);
  recalc();
});
</script>
"""


def neighbor_table(m, limit=5):
    ordered = sorted(MODELS, key=lambda x: blended(x, 0.25))
    idx = next(i for i, x in enumerate(ordered) if x["id"] == m["id"])
    lo = max(0, idx - limit // 2)
    hi = min(len(ordered), lo + limit)
    lo = max(0, hi - limit)
    window = ordered[lo:hi]
    out = []
    for x in window:
        sel = x["id"] == m["id"]
        hi_attr = ' style="background:var(--accent-soft)"' if sel else ""
        if sel:
            name_cell = "<strong>%s</strong>" % esc(x["name"])
        else:
            name_cell = '<a href="/models/%s.html">%s</a>' % (x["id"], esc(x["name"]))
        out.append(
            "<tr%s><td>%s</td><td>%s</td><td class=\"num\">%s</td><td class=\"num\">%s</td>"
            "<td class=\"num\">%s</td><td>%s</td></tr>" % (
                hi_attr, name_cell, esc(x["provider"]), money(x["input"]),
                money(x["output"]), money(x.get("cached_input")),
                x.get("context") or "—"))
    return "".join(out)


def time_row(m):
    tp = m.get("time_pricing")
    if not tp:
        return ""
    mult = tp.get("peak_multiplier", 2)
    label = esc(tp.get("window_label", "Peak window"))
    return ('<tr><td>Off-peak rate (default)</td><td class="num">%s</td><td class="num">%s</td></tr>'
            '<tr><td>%s</td><td class="num">%s</td><td class="num">%s</td></tr>'
            % (money(m["input"]), money(m["output"]), label,
               money(m["input"] * mult), money(m["output"] * mult)))


def detail_tables(detail):
    """Optional per-model tables, used for worked cost examples and head-to-heads."""
    out = []
    for t in detail.get("tables", []):
        head = "".join(
            '<th class="num">%s</th>' % esc(h) if i else "<th>%s</th>" % esc(h)
            for i, h in enumerate(t["head"]))
        rows = ""
        for r in t["rows"]:
            cells = "".join(
                '<td class="num">%s</td>' % esc(c) if i else "<td>%s</td>" % esc(c)
                for i, c in enumerate(r))
            rows += "<tr>%s</tr>" % cells
        block = ('  <section class="panel">\n'
                 '    <h2 style="margin-top:0;font-size:16px">%s</h2>\n'
                 '    <table class="data">\n'
                 '      <thead><tr>%s</tr></thead>\n'
                 '      <tbody>%s</tbody>\n'
                 '    </table>\n' % (esc(t["title"]), head, rows))
        if t.get("note"):
            block += '    <p class="note">%s</p>\n' % esc(t["note"])
        block += "  </section>\n\n"
        out.append(block)
    return "".join(out)


def generic_faqs(m):
    """Fallback FAQ set. Kept identical in structure to the curated ones so the
    visible copy and the FAQPage markup are always generated from one list."""
    name = m["name"]
    price = "%s per 1M input tokens, %s per 1M output tokens" % (
        money(m["input"]), money(m["output"]))
    if m.get("time_pricing"):
        mult = m["time_pricing"].get("peak_multiplier", 2)
        price += (" Time-based pricing: the listed rate is the off-peak rate; %s the rate "
                  "doubles to %s/%s." % (m["time_pricing"].get("window_label", "during peak windows"),
                                         money(m["input"] * mult), money(m["output"] * mult)))
    if m.get("cached_input"):
        price += " Cached input is billed at %s per 1M tokens where caching is supported." % (
            money(m["cached_input"]))

    if m.get("tier_threshold"):
        ctx = "Long prompts above %s tokens switch to the higher tier (%s in / %s out). Below that the rate is flat." % (
            "{:,}".format(m["tier_threshold"]), money(m.get("input_high")), money(m.get("output_high")))
    else:
        ctx = "The published context window is charged at a flat per-token rate."
        if m.get("note"):
            ctx += " " + m["note"]

    cache_clause = ("; cached input runs at %s per 1M" % money(m["cached_input"])) if m.get("cached_input") else ""
    return [
        ("How much does %s cost per 1M tokens?" % name, price),
        ("Does the %s context window cost extra?" % name, ctx),
        ("What is the cheapest way to run %s at scale?" % name,
         "Keep a stable prompt prefix so it caches%s, cap output length, schedule asynchronous "
         "work into off-peak windows where the provider prices by time, and move the easy 80%% "
         "of traffic to a lower tier." % cache_clause),
    ]


def short_title(own, other):
    """'DeepSeek V4 Pro vs V4.1 Flash' — drop the shared provider prefix on the
    second name so the heading does not repeat it."""
    a, b = own["name"], other["name"]
    if own["provider"] == other["provider"] and b.startswith(other["provider"]):
        b = b[len(other["provider"]):].strip()
    return "%s vs %s" % (a, b)


def pair_panel(m):
    """Render every curated comparison that involves this model, with the model
    being viewed always in the first column. Prices come from the model records,
    so the same table on the sibling's page cannot drift out of sync."""
    blocks = []
    for c in COMPARISONS:
        ids = [i for i in c.get("models", []) if i in BY_ID]
        if m["id"] not in ids or len(ids) < 2:
            continue
        other = BY_ID[next(i for i in ids if i != m["id"])]
        suffix = " (off-peak)" if (m.get("time_pricing") or other.get("time_pricing")) else ""
        rows = [
            ("Input / 1M%s" % suffix, money(m["input"]), money(other["input"])),
            ("Output / 1M%s" % suffix, money(m["output"]), money(other["output"])),
        ]
        if m.get("cached_input") or other.get("cached_input"):
            rows.append(("Cache hit / 1M", money(m.get("cached_input")),
                         money(other.get("cached_input"))))
        if m.get("context") or other.get("context"):
            rows.append(("Context window", m.get("context") or "—", other.get("context") or "—"))

        # Non-price facts live on each model as `specs`; render the union so a key
        # present on only one side still shows up, with a dash on the other.
        keys = list((m.get("specs") or {}).keys())
        for k in (other.get("specs") or {}):
            if k not in keys:
                keys.append(k)
        for k in keys:
            rows.append((k, (m.get("specs") or {}).get(k, "—"),
                         (other.get("specs") or {}).get(k, "—")))

        body = "".join(
            "<tr><td>%s</td><td class=\"num\">%s</td><td class=\"num\">%s</td></tr>"
            % (esc(label), esc(a), esc(b)) for label, a, b in rows)
        blocks.append(
            '  <section class="panel">\n'
            '    <h2 style="margin-top:0;font-size:16px">%s</h2>\n'
            '    <table class="data">\n'
            '      <thead><tr><th></th><th>%s</th><th>%s</th></tr></thead>\n'
            '      <tbody>%s</tbody>\n'
            '    </table>\n'
            '    <p class="note">Full breakdown: '
            '<a href="/models/%s.html">%s pricing</a>.</p>\n'
            '  </section>\n\n'
            % (esc(short_title(m, other)), esc(m["name"]), esc(other["name"]), body,
               other["id"], esc(other["name"])))
    return "".join(blocks)


def model_page(m):
    name = m["name"]
    slug = m["id"]
    detail = m.get("detail") or {}
    verified = detail.get("verified") or UPDATED
    canonical = "%s/models/%s.html" % (BASE, slug)
    title = "%s API pricing in 2026: cost per 1M tokens | ezaiops tools" % name
    desc = ("%s costs %s per 1M input tokens and %s per 1M output tokens. "
            "Context window, caching rates, a quick cost calculator and "
            "comparisons with nearby models." % (name, money(m["input"]), money(m["output"])))

    # One FAQ list drives both the visible <details> blocks and the FAQPage
    # markup, so the two can never drift apart.
    faqs = ([(f["q"], f["a"]) for f in detail["faq"]] if detail.get("faq")
            else generic_faqs(m))

    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}}
                       for q, a in faqs],
    }, ensure_ascii=False, indent=2)

    tier_row = ""
    if m.get("tier_threshold"):
        tier_row = ("<tr><td>Above %s tokens per request</td><td class=\"num\">%s</td>"
                    "<td class=\"num\">%s</td></tr>" % (
                        "{:,}".format(m["tier_threshold"]),
                        money(m.get("input_high")), money(m.get("output_high"))))

    # .kv-list is a two-column grid built on <dt>/<dd>; emitting table rows here
    # produced invalid markup that browsers flatten into "Cached input$0.022".
    cache_row = ("<dt>Cached input</dt><dd>%s</dd>"
                 % money(m["cached_input"])) if m.get("cached_input") else \
                "<dt>Cached input</dt><dd>not offered</dd>"

    # A time-priced model already renders "Off-peak (default)" and "Peak" rows.
    # Emitting a "Standard rate" row on top of those duplicated the same numbers.
    base_row = ""
    if not m.get("time_pricing"):
        base_row = ('<tr><td>Standard rate</td><td class="num">%s</td>'
                    '<td class="num">%s</td></tr>' % (money(m["input"]), money(m["output"])))

    price_mode = " (off-peak)" if m.get("time_pricing") else ""
    multiple = m["output"] / m["input"]

    if detail.get("sections"):
        prose = "".join(
            "<h2>%s</h2>" % esc(s["h2"]) + "".join("<p>%s</p>" % esc(p) for p in s["paras"])
            for s in detail["sections"])
    else:
        cache_note = (" A cache hit bills at %s against %s for a miss, so a reused prefix is the "
                      "cheapest tokens you will ever buy." % (money(m["cached_input"]), money(m["input"]))
                      if m.get("cached_input") else "")
        prose = (
            "<h2>How to think about %s pricing</h2>"
            "<p>Output tokens bill at %.1f× the input rate, which is the number that decides whether a "
            "workload is affordable: summarization and classification are input-heavy, while agents, "
            "chain-of-thought reasoning and long-form drafting are output-heavy. Before comparing "
            "headline prices, measure the real token mix from your own logs, then apply the blended "
            "formula <code>(input share × input price) + (output share × output price)</code>.</p>"
            "<p>Beyond the headline rate, three levers usually decide a real bill: batch discounts where "
            "the provider offers one, cache hits on a stable prompt prefix, and right-sizing — routing "
            "simple steps to a mini or flash-class model instead of the flagship. Not every provider "
            "offers all three, so confirm which apply rather than assuming them.%s</p>"
            % (esc(name), multiple, cache_note))

    faq_html = "".join(
        '<details class="faq"><summary>%s</summary>\n      <div class="faq-body">%s</div></details>\n    '
        % (esc(q), esc(a)) for q, a in faqs)

    sibling = ""
    if detail.get("sibling") and detail["sibling"] in BY_ID:
        sib = BY_ID[detail["sibling"]]
        sibling = ('    <p class="note">Full breakdown: <a href="/models/%s.html">%s pricing</a>.</p>\n'
                   % (sib["id"], esc(sib["name"])))

    html = HEAD
    html = html.replace("@@TITLE@@", esc(title)).replace("@@DESC@@", esc(desc))
    html = html.replace("@@CANON@@", canonical).replace("@@LD@@", ld)
    html += CRUMBS.replace("@@NAME@@", esc(name))
    html += f"""
  <h1>{esc(name)} API pricing: cost per 1M tokens</h1>
  <p class="lead">{name} currently costs <strong>{money(m['input'])} per 1M input tokens</strong>{price_mode} and
  <strong>{money(m['output'])} per 1M output tokens</strong> through the {esc(m['provider'])} API. {esc(m['note'].rstrip('. '))}.
  Prices below were verified against official pricing documentation on {verified}.</p>

  <section class="panel">
    <div class="stats-grid">
      <div class="stat"><div class="k">Input / 1M tokens</div><div class="v">{money(m['input'])}</div></div>
      <div class="stat"><div class="k">Output / 1M tokens</div><div class="v">{money(m['output'])}</div></div>
      <div class="stat"><div class="k">Output multiple</div><div class="v">{multiple:.1f}×</div></div>
      <div class="stat"><div class="k">Context window</div><div class="v">{esc(m.get('context') or '—')}</div></div>
    </div>

    <table class="data">
      <thead><tr><th>Tier</th><th class="num">Input / 1M</th><th class="num">Output / 1M</th></tr></thead>
      <tbody>
        {base_row}
        {tier_row}{time_row(m)}
      </tbody>
    </table>
    <dl class="kv-list">{cache_row}</dl>
    <p class="note">Verify current rates on the {esc(m['provider'])} pricing page before committing budget —
    providers adjust prices frequently, and long-context or caching discounts may not show up
    in the headline numbers.</p>
  </section>

  <section class="panel">
    <h2 style="margin-top:0;font-size:16px">Quick cost calculator for {esc(name)}</h2>
    <div class="field-row">
      <div class="field">
        <label class="field-label" for="mc-in">Input tokens</label>
        <input type="number" id="mc-in" class="mono" value="1000000" min="0">
      </div>
      <div class="field">
        <label class="field-label" for="mc-out">Output tokens</label>
        <input type="number" id="mc-out" class="mono" value="100000" min="0">
      </div>
    </div>
    <div class="stats-grid">
      <div class="stat"><div class="k">One request (this volume)</div><div class="v" id="mc-cost">—</div></div>
      <div class="stat"><div class="k">× 1,000 such requests</div><div class="v" id="mc-1k">—</div></div>
    </div>
  </section>

{pair_panel(m)}{detail_tables(detail)}  <section class="panel">
    <h2 style="margin-top:0;font-size:16px">{esc(name)} vs nearby models (blended at a 3:1 input:output ratio)</h2>
    <table class="data">
      <thead><tr><th>Model</th><th>Provider</th><th class="num">Input</th><th class="num">Output</th><th class="num">Cached in</th><th>Context</th></tr></thead>
      <tbody>{neighbor_table(m)}</tbody>
    </table>
    <p class="note">The full @@MODELCOUNT@@-model comparison lives on the <a href="/models/index.html">pricing hub</a>,
    and the <a href="/tools/token-counter.html">token &amp; cost calculator</a> will price your actual prompt.</p>
{sibling}  </section>

  <section class="prose">
    {prose}

    <h2>Frequently asked questions</h2>
    {faq_html}
  </section>
"""
    html = html.replace("@@MODELCOUNT@@", str(len(MODELS)))

    html += FOOT.replace("</body>", CALC_JS.replace("@@ID@@", slug) + "\n</body>")
    return html


def index_page():
    rows = []
    for m in sorted(MODELS, key=lambda x: (x["provider"], x["input"])):
        rows.append(
            "<tr><td><a href=\"/models/%s.html\">%s</a></td><td>%s</td><td class=\"num\">%s</td>"
            "<td class=\"num\">%s</td><td class=\"num\">%s</td><td>%s</td><td>%s</td></tr>" % (
                m["id"], esc(m["name"]), esc(m["provider"]), money(m["input"]),
                money(m["output"]), money(m.get("cached_input")),
                m.get("context") or "—", esc(m["note"])))
    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "LLM API pricing comparison 2026",
        "numberOfItems": len(MODELS),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "name": m["name"],
             "url": "%s/models/%s.html" % (BASE, m["id"])}
            for i, m in enumerate(MODELS)]
    }, ensure_ascii=False)
    canonical = BASE + "/models/index.html"
    html = HEAD.replace("@@TITLE@@", esc("LLM API pricing comparison 2026 — %d models per 1M tokens | ezaiops tools" % len(MODELS)))
    html = html.replace("@@DESC@@", esc("Side-by-side input/output pricing per 1M tokens for GPT-5.6, Claude Opus 5, Gemini 3.1 Pro, DeepSeek V4, Grok 4.5 and Mistral — with context windows and cache rates."))
    html = html.replace("@@CANON@@", canonical)
    html = html.replace("@@LD@@", ld)
    html += """
<main class="wrap tool-page">
  <nav class="crumbs"><a href="/">Home</a> / LLM pricing<a class="main-site-link" href="https://ezaiops.com/en/">ezaiops.com \u2197</a></nav>
  <h1>LLM API pricing, model by model</h1>
  <p class="lead">Every major frontier model, priced per 1M tokens, side by side. Data verified
  against official provider documentation on @@UPD@@. Pick a row for the full breakdown, a
  calculator and neighbor comparisons — or jump straight to the
  <a href="/tools/token-counter.html">token &amp; cost calculator</a>.</p>
  <p class="main-site-banner">Part of <a href="https://ezaiops.com/en/">ezaiops.com</a> — field notes on AI agent observability, LLMOps and production AI ops.</p>

  <section class="panel">
    <table class="data">
      <thead><tr><th>Model</th><th>Provider</th><th class="num">Input / 1M</th><th class="num">Output / 1M</th><th class="num">Cached input</th><th>Context</th><th>Notes</th></tr></thead>
      <tbody>@@ROWS@@</tbody>
    </table>
  </section>

  <section class="prose">
    <h2>How to read this table</h2>
    <p>Two numbers do the work: <strong>input price</strong> (what you send) and <strong>output
    price</strong> (what the model generates). Output is billed at 2–8× the input rate depending on
    the provider, so the headline input price alone tells you almost nothing about a real bill.
    Cached input — repeating the same long system prompt or context prefix — usually costs a
    fraction of the base input rate.</p>
    <h2>Sources</h2>
    <ul>@@SOURCES@@</ul>
  </section>
</main>
"""
    html += FOOT
    html = html.replace("@@UPDATED@@", UPDATED)
    html = html.replace("@@ROWS@@", "".join(rows))
    html = html.replace("@@SOURCES@@", "".join("<li>%s</li>" % s for s in SOURCES))
    html = html.replace("@@UPD@@", UPDATED)
    return html


def sitemap(entries):
    """entries: list of (url, absolute_path). lastmod comes from the file itself so
    unchanged pages stop claiming they were updated on every regeneration."""
    rows = []
    for url, path in entries:
        try:
            stamp = datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
        except OSError:
            stamp = TODAY
        rows.append("  <url><loc>%s</loc><lastmod>%s</lastmod>"
                    "<changefreq>monthly</changefreq></url>\n" % (url, stamp))
    return ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
            + "".join(rows) + "</urlset>\n")


def main():
    with open(os.path.join(ROOT, "assets", "models.js"), "w", encoding="utf-8") as fh:
        fh.write("window.EZ_MODELS = " + json.dumps(
            {"updated": UPDATED, "models": MODELS, "sources": SOURCES},
            ensure_ascii=False, indent=2) + ";\n")

    pages = []
    os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)
    for m in MODELS:
        path = os.path.join(ROOT, "models", m["id"] + ".html")
        html = model_page(m)
        # Only touch the file when the bytes actually differ: sitemap lastmod is
        # read from mtime, so rewriting every page on every run would claim all
        # 34 pages changed whenever one price moved.
        try:
            with open(path, encoding="utf-8") as fh:
                if fh.read() == html:
                    pages.append(("%s/models/%s.html" % (BASE, m["id"]), path))
                    continue
        except OSError:
            pass
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        pages.append(("%s/models/%s.html" % (BASE, m["id"]), path))

    # Prune pages for models that were removed from models.json, otherwise a
    # deleted model keeps a live, orphaned pricing page.
    live = {m["id"] + ".html" for m in MODELS} | {"index.html"}
    for p in sorted(glob.glob(os.path.join(ROOT, "models", "*.html"))):
        if os.path.basename(p) not in live:
            os.remove(p)
            print("removed stale page: models/%s" % os.path.basename(p))

    index_path = os.path.join(ROOT, "models", "index.html")
    index_html = index_page()
    try:
        with open(index_path, encoding="utf-8") as fh:
            unchanged = fh.read() == index_html
    except OSError:
        unchanged = False
    if not unchanged:
        with open(index_path, "w", encoding="utf-8") as fh:
            fh.write(index_html)
    pages.append((BASE + "/models/index.html", index_path))

    # "/" is the canonical home page, so index.html is deliberately not listed
    # again here — a sitemap that lists both asks Google to crawl a duplicate.
    static_pages = [(BASE + "/", os.path.join(ROOT, "index.html"))]
    for p in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        if os.path.basename(p) in ("index.html", "404.html"):
            continue
        static_pages.append((BASE + "/" + os.path.basename(p), p))
    for p in sorted(glob.glob(os.path.join(ROOT, "tools", "*.html"))):
        static_pages.append((BASE + "/tools/" + os.path.basename(p), p))
    allurls = static_pages + pages

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(sitemap(allurls))

    print("models.js written (%d models)" % len(MODELS))
    print("model pages written: %d" % len(MODELS))
    print("sitemap entries: %d" % len(allurls))


if __name__ == "__main__":
    main()
