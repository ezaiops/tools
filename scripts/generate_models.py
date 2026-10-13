#!/usr/bin/env python3
"""Part 2: per-model page rendering, comparison hub, sitemap."""
import json
import os
import glob
from gen_common import (ROOT, BASE, TODAY, UPDATED, MODELS, SOURCES, BY_ID,
                        money, blended, esc, HEAD, CRUMBS, FOOT)

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


def model_page(m):
    name = m["name"]
    slug = m["id"]
    canonical = "%s/models/%s.html" % (BASE, slug)
    title = "%s API pricing in 2026: cost per 1M tokens | ezaiops tools" % name
    desc = ("%s costs %s per 1M input tokens and %s per 1M output tokens. "
            "Context window, caching rates, a quick cost calculator and "
            "comparisons with nearby models." % (name, money(m["input"]), money(m["output"])))

    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": "How much does %s cost per 1M tokens?" % name,
             "acceptedAnswer": {"@type": "Answer", "text":
             "%s: %s per 1M input tokens, %s per 1M output tokens. "
             "Cached input is billed at %s per 1M tokens where caching is supported."
             % (name, money(m["input"]), money(m["output"]), money(m.get("cached_input")))}},
            {"@type": "Question", "name": "Is the %s context window charged at a flat rate?" % name,
             "acceptedAnswer": {"@type": "Answer", "text":
             ("Context window: %s. %s" % (m.get("context") or "not published", m["note"]))
             if m.get("tier_threshold") else
             "The %s context window is charged at a flat per-token rate with no length tier. %s"
             % (m.get("context") or "maximum", m["note"])}},
            {"@type": "Question", "name": "How can I reduce my %s bill?" % name,
             "acceptedAnswer": {"@type": "Answer", "text":
             "Use the batch API for a 50% discount, reuse a stable prompt prefix to get cache-hit "
             "rates (often around 0.1x the input price), cap max output tokens, and route "
             "classification or extraction tasks to a cheaper model tier."}},
        ]
    }, ensure_ascii=False, indent=2)

    tier_row = ""
    if m.get("tier_threshold"):
        tier_row = ("<tr><td>Above %s tokens per request</td><td class=\"num\">%s</td>"
                    "<td class=\"num\">%s</td></tr>" % (
                        "{:,}".format(m["tier_threshold"]),
                        money(m.get("input_high")), money(m.get("output_high"))))

    cache_row = ("<tr><td>Cached input</td><td class=\"num\">%s</td></tr>"
                 % money(m["cached_input"])) if m.get("cached_input") else \
                "<tr><td>Cached input</td><td>not offered</td></tr>"

    html = HEAD
    html = html.replace("@@TITLE@@", esc(title)).replace("@@DESC@@", esc(desc))
    html = html.replace("@@CANON@@", canonical).replace("@@LD@@", ld)
    html += CRUMBS.replace("@@NAME@@", esc(name))
    html += """
  <h1>%s API pricing: cost per 1M tokens</h1>
  <p class="lead">%s currently costs <strong>%s per 1M input tokens</strong> and
  <strong>%s per 1M output tokens</strong> through the %s API. %s
  Prices below were verified against official pricing documentation on %s.</p>

  <section class="panel">
    <div class="stats-grid">
      <div class="stat"><div class="k">Input / 1M tokens</div><div class="v">%s</div></div>
      <div class="stat"><div class="k">Output / 1M tokens</div><div class="v">%s</div></div>
      <div class="stat"><div class="k">Output multiple</div><div class="v">%.1f×</div></div>
      <div class="stat"><div class="k">Context window</div><div class="v">%s</div></div>
    </div>

    <table class="data">
      <thead><tr><th>Tier</th><th class="num">Input / 1M</th><th class="num">Output / 1M</th></tr></thead>
      <tbody>
        <tr><td>Standard rate</td><td class="num">%s</td><td class="num">%s</td></tr>
        %s
      </tbody>
    </table>
    <dl class="kv-list">%s</dl>
    <p class="note">Verify current rates on the %s pricing page before committing budget —
    providers adjust prices frequently, and long-context or caching discounts may not show up
    in the headline numbers.</p>
  </section>

  <section class="panel">
    <h2 style="margin-top:0;font-size:16px">Quick cost calculator for %s</h2>
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

  <section class="panel">
    <h2 style="margin-top:0;font-size:16px">%s vs nearby models (blended at a 3:1 input:output ratio)</h2>
    <table class="data">
      <thead><tr><th>Model</th><th>Provider</th><th class="num">Input</th><th class="num">Output</th><th class="num">Cached in</th><th>Context</th></tr></thead>
      <tbody>%s</tbody>
    </table>
    <p class="note">The full @@MODELCOUNT@@-model comparison lives on the <a href="/models/index.html">pricing hub</a>,
    and the <a href="/tools/token-counter.html">token &amp; cost calculator</a> will price your actual prompt.</p>
  </section>

  <section class="prose">
    <h2>How to think about %s pricing</h2>
    <p>Output tokens bill at %.1f× the input rate, which is the number that decides whether a
    workload is affordable: summarization and classification are input-heavy, while agents,
    chain-of-thought reasoning and long-form drafting are output-heavy. Before comparing
    headline prices, measure the real token mix from your own logs, then apply the blended
    formula <code>(input share × input price) + (output share × output price)</code>.</p>
    <p>Three discounts stack on top of list prices on most providers: a 50%% batch-API discount for
    asynchronous workloads, cache-hit pricing that can drop cached input to around 0.1× the base
    rate%s, and right-sizing — routing simple steps to a mini or flash-class model instead of the
    flagship is usually the largest single saving available.</p>

    <h2>Frequently asked questions</h2>
    <details class="faq"><summary>How much does %s cost per 1M tokens?</summary>
      <div class="faq-body">%s per 1M input and %s per 1M output tokens%s.</div></details>
    <details class="faq"><summary>Does the %s context window cost extra?</summary>
      <div class="faq-body">%s</div></details>
    <details class="faq"><summary>What is the cheapest way to run %s at scale?</summary>
      <div class="faq-body">Batch async jobs for the 50%% discount, keep a stable prefix so it
      caches%s, cap output length, and move the easy 80%% of traffic to a lower tier.</div></details>
  </section>
""" % (
        esc(name), name, money(m["input"]), money(m["output"]), esc(m["provider"]), esc(m["note"]),
        UPDATED,
        money(m["input"]), money(m["output"]), m["output"] / m["input"],
        esc(m.get("context") or "—"),
        money(m["input"]), money(m["output"]), tier_row,
        cache_row, esc(m["provider"]), esc(name),
        esc(name),
        neighbor_table(m),
        esc(name), m["output"] / m["input"],
        " — and Claude-class cache writes cost 1.25×–2× the input rate" if m.get("cached_input") else "",
        esc(name), money(m["input"]), money(m["output"]),
        ("; cached input runs at %s per 1M" % money(m["cached_input"])) if m.get("cached_input") else "",
        esc(name),
        (("Long prompts above %s tokens switch to the higher tier (%s in / %s out). "
          "Below that the rate is flat." % (
              "{:,}".format(m["tier_threshold"]), money(m.get("input_high")), money(m.get("output_high"))))
         if m.get("tier_threshold") else
         "The published context window is charged at a flat per-token rate; %s" % esc(m["note"])),
        esc(name),
        (" (Claude also charges a multi-tier cache write premium)" if m.get("cached_input") else ""),
    )
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
  <nav class="crumbs"><a href="/">Home</a> / LLM pricing</nav>
  <h1>LLM API pricing, model by model</h1>
  <p class="lead">Every major frontier model, priced per 1M tokens, side by side. Data verified
  against official provider documentation on @@UPD@@. Pick a row for the full breakdown, a
  calculator and neighbor comparisons — or jump straight to the
  <a href="/tools/token-counter.html">token &amp; cost calculator</a>.</p>

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
"""
    html += FOOT
    html = html.replace("@@UPDATED@@", UPDATED)
    html = html.replace("@@ROWS@@", "".join(rows))
    html = html.replace("@@SOURCES@@", "".join("<li>%s</li>" % s for s in SOURCES))
    html = html.replace("@@UPD@@", UPDATED)
    return html


def sitemap(paths):
    body = "".join(
        "  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq></url>\n"
        % (p, TODAY) for p in paths)
    return ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
            + body + "</urlset>\n")


def main():
    with open(os.path.join(ROOT, "assets", "models.js"), "w", encoding="utf-8") as fh:
        fh.write("window.EZ_MODELS = " + json.dumps(
            {"updated": UPDATED, "models": MODELS, "sources": SOURCES},
            ensure_ascii=False, indent=2) + ";\n")

    pages = []
    os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)
    for m in MODELS:
        path = os.path.join(ROOT, "models", m["id"] + ".html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(model_page(m))
        pages.append("%s/models/%s.html" % (BASE, m["id"]))

    with open(os.path.join(ROOT, "models", "index.html"), "w", encoding="utf-8") as fh:
        fh.write(index_page())
    pages.append(BASE + "/models/index.html")

    static_pages = [BASE + "/"]
    for p in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        static_pages.append(BASE + "/" + os.path.basename(p))
    for p in sorted(glob.glob(os.path.join(ROOT, "tools", "*.html"))):
        static_pages.append(BASE + "/tools/" + os.path.basename(p))
    allurls = static_pages + pages

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(sitemap(allurls))

    print("models.js written (%d models)" % len(MODELS))
    print("model pages written: %d" % len(MODELS))
    print("sitemap entries: %d" % len(allurls))


if __name__ == "__main__":
    main()
