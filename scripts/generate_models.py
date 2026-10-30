#!/usr/bin/env python3
"""Part 2: per-model page rendering, comparison hub, sitemap."""
import datetime
import glob
import json
import os
from gen_common import (ROOT, BASE, TODAY, UPDATED, MODELS, SOURCES, BY_ID,
                        COMPARISONS, money, zh_money, blended, esc, HEAD, CRUMBS, FOOT,
                        ZH_HEAD, ZH_CRUMBS, ZH_FOOT)
from zh_models import (NOTES, SPEC_KEYS, SPEC_VALUES, FAQ_ZH, SECTIONS_ZH,
                       TABLES_ZH)

# Time-of-day windows as published in models.json, translated on the zh pages.
TIME_WINDOW_ZH = {
    "Weekday peak (UTC 01:00-04:00 and 06:00-10:00)": "工作日高峰(UTC 01:00-04:00 与 06:00-10:00)",
}


def window_label_zh(tp):
    label = tp.get("window_label", "Peak window")
    return TIME_WINDOW_ZH.get(label, label)


def en_hreflang(canonical, zh_url):
    """The <head> block EN model pages need once a /zh/ twin exists."""
    return ('<link rel="alternate" hreflang="zh-CN" href="%s">\n'
            '<link rel="alternate" hreflang="en" href="%s">\n'
            '<link rel="alternate" hreflang="x-default" href="%s">'
            % (zh_url, canonical, canonical))


def static_switch(zh_url, en_url):
    """The static 中文/EN pill, cloned from the /zh/ pages' nav."""
    return ('<div class="lang-switch"><a href="%s" hreflang="zh-CN" '
            'class="active" aria-current="page">中文</a>'
            '<a href="%s" hreflang="en">EN</a></div>'
            % (zh_url, en_url))


def spec_value_zh(v):
    """Spec cell values stay as data unless they are prose we have translated."""
    return SPEC_VALUES.get(v, v)

CALC_JS = """<script>
document.addEventListener("DOMContentLoaded", function () {
  var models = (window.EZ_MODELS || {}).models || [];
  var me = null;
  for (var i = 0; i < models.length; i++) if (models[i].id === "@@ID@@") me = models[i];
  if (!me) return;
  // Chinese pages bill in CNY where the provider publishes a mainland rate.
  // data-zh-static is a server-rendered attribute, so it is readable before the
  // i18n engine finishes loading; the language check is only a fallback.
  var zhPage = document.documentElement.hasAttribute("data-zh-static") ||
               !!(window.ezI18N && window.ezI18N.lang === "zh");
  var c = zhPage && me.cny ? me.cny : null;
  var inRate = c ? c.input : me.input;
  var outRate = c ? c.output : me.output;
  var sym = c ? "\u00a5" : "$";
  var inEl = document.getElementById("mc-in");
  var outEl = document.getElementById("mc-out");
  function fmt(n) {
    if (n <= 0) return sym + "0";
    if (n < 0.000001) return "<" + sym + "0.000001";
    var d = n < 0.01 ? 6 : n < 1 ? 4 : 2;
    return sym + n.toFixed(d);
  }
  function recalc() {
    var ti = Math.max(0, parseFloat(inEl.value || "0") || 0);
    var to = Math.max(0, parseFloat(outEl.value || "0") || 0);
    document.getElementById("mc-cost").textContent = fmt(ti * inRate / 1e6 + to * outRate / 1e6);
    document.getElementById("mc-1k").textContent = fmt((ti * inRate / 1e6 + to * outRate / 1e6) * 1000);
  }
  inEl.addEventListener("input", recalc);
  outEl.addEventListener("input", recalc);
  recalc();
});
</script>
"""


def neighbor_table(m, limit=5, zh=False):
    ordered = sorted(MODELS, key=lambda x: blended(x, 0.25))
    idx = next(i for i, x in enumerate(ordered) if x["id"] == m["id"])
    lo = max(0, idx - limit // 2)
    hi = min(len(ordered), lo + limit)
    lo = max(0, hi - limit)
    window = ordered[lo:hi]
    stem = "/zh/models/" if zh else "/models/"
    out = []
    for x in window:
        sel = x["id"] == m["id"]
        hi_attr = ' style="background:var(--accent-soft)"' if sel else ""
        if sel:
            name_cell = "<strong>%s</strong>" % esc(x["name"])
        else:
            name_cell = '<a href="%s%s.html">%s</a>' % (stem, x["id"], esc(x["name"]))
        price = (lambda mm, k: zh_money(mm, k)) if zh else (lambda mm, k: money(mm.get(k)))
        out.append(
            "<tr%s><td>%s</td><td>%s</td><td class=\"num\">%s</td><td class=\"num\">%s</td>"
            "<td class=\"num\">%s</td><td>%s</td></tr>" % (
                hi_attr, name_cell, esc(x["provider"]), price(x, "input"),
                price(x, "output"), price(x, "cached_input"),
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


def time_row_zh(m):
    tp = m.get("time_pricing")
    if not tp:
        return ""
    mult = tp.get("peak_multiplier", 2)
    label = esc(window_label_zh(tp))
    return ('<tr><td>非高峰价格(默认)</td><td class="num">%s</td><td class="num">%s</td></tr>'
            '<tr><td>%s</td><td class="num">%s</td><td class="num">%s</td></tr>'
            % (money(m["input"]), money(m["output"]), label,
               money(m["input"] * mult), money(m["output"] * mult)))


def detail_tables_zh(detail, model_id):
    """Chinese worked-example tables via TABLES_ZH; untranslated tables fall
    back to their English source so a table never silently disappears."""
    out = []
    for t in detail.get("tables", []):
        t_zh = (TABLES_ZH.get(model_id) or {}).get(t["title"], t)
        head = "".join(
            '<th class="num">%s</th>' % esc(h) if i else "<th>%s</th>" % esc(h)
            for i, h in enumerate(t_zh["head"]))
        rows = ""
        for r in t_zh["rows"]:
            cells = "".join(
                '<td class="num">%s</td>' % esc(c) if i else "<td>%s</td>" % esc(c)
                for i, c in enumerate(r))
            rows += "<tr>%s</tr>" % cells
        block = ('  <section class="panel">\n'
                 '    <h2 style="margin-top:0;font-size:16px">%s</h2>\n'
                 '    <table class="data">\n'
                 '      <thead><tr>%s</tr></thead>\n'
                 '      <tbody>%s</tbody>\n'
                 '    </table>\n' % (esc(t_zh["title"]), head, rows))
        if t_zh.get("note"):
            block += '    <p class="note">%s</p>\n' % esc(t_zh["note"])
        block += "  </section>\n\n"
        out.append(block)
    return "".join(out)


def generic_faqs_zh(m):
    """Fallback FAQ set, mirroring generic_faqs() but in Chinese."""
    name = m["name"]
    price = "每 1M 输入 tokens %s、每 1M 输出 tokens %s" % (
        money(m["input"]), money(m["output"]))
    if m.get("time_pricing"):
        mult = m["time_pricing"].get("peak_multiplier", 2)
        price += (" 按时段计费:表中费率是非高峰价;%s费率翻倍至 %s/%s。"
                  % (window_label_zh(m["time_pricing"]),
                     money(m["input"] * mult), money(m["output"] * mult)))
    if m.get("cached_input"):
        price += " 支持缓存的场景下,缓存输入按 %s/1M tokens 计费。" % money(m["cached_input"])

    if m.get("tier_threshold"):
        ctx = "超过 %s tokens 的长 prompt 会切换到更高档位(输入 %s / 输出 %s);低于该阈值费率保持不变。" % (
            "{:,}".format(m["tier_threshold"]), money(m.get("input_high")), money(m.get("output_high")))
    else:
        ctx = "公布的上下文窗口按统一的每 token 费率计费。"
        if m.get("note"):
            ctx += " " + NOTES.get(m["id"], m["note"])

    cache_clause = (";缓存输入按 %s/1M 计费" % money(m["cached_input"])) if m.get("cached_input") else ""
    return [
        ("%s 每 1M token 多少钱?" % name, price),
        ("%s 的上下文窗口要额外收费吗?" % name, ctx),
        ("规模化运行 %s 最省钱的方式是什么?" % name,
         "保持稳定的 prompt 前缀以命中缓存%s,限制输出长度,把异步任务安排进厂商按时间计价的非高峰窗口,"
         "并把容易处理的约 80%% 流量切到更低档位。" % cache_clause),
    ]


def generic_prose_zh(m):
    name = m["name"]
    multiple = m["output"] / m["input"]
    cache_note = (" 缓存命中按 %s 计费,未命中则按 %s,因此被复用的前缀是你买过的最便宜的 token。"
                  % (money(m["cached_input"]), money(m["input"]))
                  if m.get("cached_input") else "")
    return (
        "<h2>如何看待 %s 的价格</h2>"
        "<p>输出 token 的计费倍率是输入的 %.1f 倍,这个数字决定一项工作负载是否负担得起:摘要与分类是输入密集型,"
        "而 agent、思维链推理和长篇写作是输出密集型。在比较宣传价格之前,先从自己的日志中测量真实的 token 比例,"
        "再用混合公式 <code>(输入占比 × 输入价格) + (输出占比 × 输出价格)</code> 计算。</p>"
        "<p>除了头条费率,通常还有三个杠杆决定真实账单:厂商提供的批量折扣、稳定 prompt 前缀的缓存命中,"
        "以及合理选型——把简单步骤交给 mini 或 flash 类模型而不是旗舰。并非所有厂商都同时提供这三项,"
        "先逐项确认哪些适用,而不是想当然。%s</p>"
        % (esc(name), multiple, cache_note))


def pair_panel_zh(m):
    """Chinese head-to-head panels; every link stays inside the /zh/ tree."""
    blocks = []
    for c in COMPARISONS:
        ids = [i for i in c.get("models", []) if i in BY_ID]
        if m["id"] not in ids or len(ids) < 2:
            continue
        other = BY_ID[next(i for i in ids if i != m["id"])]
        suffix = "（非高峰）" if (m.get("time_pricing") or other.get("time_pricing")) else ""
        # Only bill in CNY when BOTH sides publish a mainland rate; otherwise the
        # row would mix ¥ and $ in a head-to-head, which reads as a comparison
        # between things priced in different currencies.
        both_cny = bool(m.get("cny")) and bool(other.get("cny"))
        price = (lambda mm, k: zh_money(mm, k)) if both_cny else (lambda mm, k: money(mm.get(k)))
        rows = [
            ("输入 / 1M%s" % suffix, price(m, "input"), price(other, "input")),
            ("输出 / 1M%s" % suffix, price(m, "output"), price(other, "output")),
        ]
        if m.get("cached_input") or other.get("cached_input"):
            rows.append(("缓存命中 / 1M", price(m, "cached_input"),
                         price(other, "cached_input")))
        if m.get("context") or other.get("context"):
            rows.append(("上下文窗口", m.get("context") or "—", other.get("context") or "—"))

        keys = list((m.get("specs") or {}).keys())
        for k in (other.get("specs") or {}):
            if k not in keys:
                keys.append(k)
        for k in keys:
            a_zh = spec_value_zh((m.get("specs") or {}).get(k, "—"))
            b_zh = spec_value_zh((other.get("specs") or {}).get(k, "—"))
            rows.append((SPEC_KEYS.get(k, k), a_zh, b_zh))

        a, b = m["name"], other["name"]
        if m["provider"] == other["provider"] and b.startswith(other["provider"]):
            b = b[len(other["provider"]):].strip()
        body = "".join(
            "<tr><td>%s</td><td class=\"num\">%s</td><td class=\"num\">%s</td></tr>"
            % (esc(label), esc(x), esc(y)) for label, x, y in rows)
        blocks.append(
            '  <section class="panel">\n'
            '    <h2 style="margin-top:0;font-size:16px">%s</h2>\n'
            '    <table class="data">\n'
            '      <thead><tr><th></th><th>%s</th><th>%s</th></tr></thead>\n'
            '      <tbody>%s</tbody>\n'
            '    </table>\n'
            '    <p class="note">完整对比:'
            '<a href="/zh/models/%s.html">%s 价格</a>。</p>\n'
            '  </section>\n\n'
            % (esc("%s 对比 %s" % (a, b)), esc(m["name"]), esc(other["name"]), body,
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
                 % zh_money(m, "cached_input")) if m.get("cached_input") else \
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
    html = html.replace(
        '<link rel="canonical" href="%s">' % canonical,
        '<link rel="canonical" href="%s">\n%s' % (
            canonical, en_hreflang(canonical, BASE + "/zh/models/%s.html" % slug)))
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


def model_page_zh(m):
    """Chinese twin of model_page(): same data, zh chrome + zh editorial copy.
    Numeric cells, model/provider names and URLs are identical to the EN page;
    the surrounding copy comes from zh_models with an English fallback."""
    name = m["name"]
    slug = m["id"]
    detail = m.get("detail") or {}
    verified = detail.get("verified") or UPDATED
    canonical = "%s/zh/models/%s.html" % (BASE, slug)
    en_url = "%s/models/%s.html" % (BASE, slug)
    if m.get("cny"):
        price_note = ('<p class="note">价格为<strong>中国大陆官方定价</strong>（人民币），'
                      '取自厂商国内站。国际站美元价见 <a href="%s">英文页</a>。</p>' % en_url)
    else:
        price_note = ('<p class="note">该模型在中国大陆没有官方 API，此处显示的是'
                      '<strong>国际站美元定价</strong>，不是人民币换算。</p>')
    title = "%s API 价格(2026)——每 1M token 成本 | ezaiops tools" % name
    desc = ("%s 每 1M 输入 tokens %s、每 1M 输出 tokens %s。包含上下文窗口、"
            "缓存费率、快速成本计算器与邻近模型对比。"
            % (name, zh_money(m, "input"), zh_money(m, "output")))

    faqs = ([(f["q"], f["a"]) for f in detail["faq"]] if detail.get("faq")
            else generic_faqs(m))
    faq_zh = ([(q_zh, a_zh) for (q_zh, a_zh) in FAQ_ZH[slug]]
              if slug in FAQ_ZH else generic_faqs_zh(m))

    # Schema stays with the curated (English) FAQ, matching the convention on
    # the /zh/ tool pages where visible copy is Chinese and metadata is English.
    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}}
                       for q, a in faqs],
    }, ensure_ascii=False, indent=2)

    tier_row = ""
    if m.get("tier_threshold"):
        tier_row = ("<tr><td>单次请求超过 %s tokens</td><td class=\"num\">%s</td>"
                    "<td class=\"num\">%s</td></tr>" % (
                        "{:,}".format(m["tier_threshold"]),
                        zh_money(m, "input_high"), zh_money(m, "output_high")))
    cache_row = ("<dt>缓存输入</dt><dd>%s</dd>"
                 % zh_money(m, "cached_input")) if m.get("cached_input") else \
                "<dt>缓存输入</dt><dd>不提供</dd>"
    base_row = ""
    if not m.get("time_pricing"):
        base_row = ('<tr><td>标准价格</td><td class="num">%s</td>'
                    '<td class="num">%s</td></tr>' % (zh_money(m, "input"), zh_money(m, "output")))

    price_mode = "（非高峰）" if m.get("time_pricing") else ""
    multiple = m["output"] / m["input"]
    note_zh = NOTES.get(slug, m["note"])

    if detail.get("sections") and slug in SECTIONS_ZH:
        prose = "".join(
            "<h2>%s</h2>" % esc(s["h2"]) + "".join("<p>%s</p>" % esc(p) for p in s["paras"])
            for s in SECTIONS_ZH[slug])
    else:
        prose = generic_prose_zh(m)

    faq_html = "".join(
        '<details class="faq"><summary>%s</summary>\n      <div class="faq-body">%s</div></details>\n    '
        % (esc(q), esc(a)) for q, a in faq_zh)

    sibling = ""
    if detail.get("sibling") and detail["sibling"] in BY_ID:
        sib = BY_ID[detail["sibling"]]
        sibling = ('    <p class="note">完整对比: <a href="/zh/models/%s.html">%s 价格</a>。</p>\n'
                   % (sib["id"], esc(sib["name"])))

    switch = static_switch("/zh/models/%s.html" % slug, "/models/%s.html?lang=en" % slug)
    html = ZH_HEAD
    html = html.replace("@@TITLE@@", esc(title)).replace("@@DESC@@", esc(desc))
    html = html.replace("@@CANON@@", canonical).replace("@@ENURL@@", en_url)
    html = html.replace("@@LD@@", ld).replace("@@SWITCH@@", switch)
    html += ZH_CRUMBS.replace("@@NAME@@", esc(name))
    html += f"""
  <h1>{esc(name)} API 价格:每 1M token 成本</h1>
  <p class="lead">{name} 通过 {esc(m['provider'])} API 的价格:每 1M 输入 tokens
  <strong>{zh_money(m, 'input')}</strong>{price_mode}、每 1M 输出 tokens
  <strong>{zh_money(m, 'output')}</strong>。{esc(note_zh)}。
  以下价格已于 {verified} 对照官方定价文档核实。</p>

  <section class="panel">
    <div class="stats-grid">
      <div class="stat"><div class="k">输入 / 1M tokens</div><div class="v">{zh_money(m, 'input')}</div></div>
      <div class="stat"><div class="k">输出 / 1M tokens</div><div class="v">{zh_money(m, 'output')}</div></div>
      <div class="stat"><div class="k">输出倍率</div><div class="v">{multiple:.1f}×</div></div>
      <div class="stat"><div class="k">上下文窗口</div><div class="v">{esc(m.get('context') or '—')}</div></div>
    </div>
    {price_note}

    <table class="data">
      <thead><tr><th>档位</th><th class="num">输入 / 1M</th><th class="num">输出 / 1M</th></tr></thead>
      <tbody>
        {base_row}
        {tier_row}{time_row_zh(m)}
      </tbody>
    </table>
    <dl class="kv-list">{cache_row}</dl>
    <p class="note">在承诺预算之前,请务必到 {esc(m['provider'])} 官方价格页核实当前费率——厂商调价频繁,
    长上下文或缓存折扣也可能不会体现在头条数字里。</p>
  </section>

  <section class="panel">
    <h2 style="margin-top:0;font-size:16px">{esc(name)} 快速成本计算器</h2>
    <div class="field-row">
      <div class="field">
        <label class="field-label" for="mc-in">输入 tokens</label>
        <input type="number" id="mc-in" class="mono" value="1000000" min="0">
      </div>
      <div class="field">
        <label class="field-label" for="mc-out">输出 tokens</label>
        <input type="number" id="mc-out" class="mono" value="100000" min="0">
      </div>
    </div>
    <div class="stats-grid">
      <div class="stat"><div class="k">单次请求(此用量)</div><div class="v" id="mc-cost">—</div></div>
      <div class="stat"><div class="k">× 1,000 次此类请求</div><div class="v" id="mc-1k">—</div></div>
    </div>
  </section>

{pair_panel_zh(m)}{detail_tables_zh(detail, slug)}  <section class="panel">
    <h2 style="margin-top:0;font-size:16px">{esc(name)} 与邻近模型对比(按输入:输出 3:1 混合)</h2>
    <table class="data">
      <thead><tr><th>模型</th><th>提供商</th><th class="num">输入</th><th class="num">输出</th><th class="num">缓存输入</th><th>上下文</th></tr></thead>
      <tbody>{neighbor_table(m, zh=True)}</tbody>
    </table>
    <p class="note">完整的 @@MODELCOUNT@@ 款模型对比见<a href="/zh/models/index.html">价格中心</a>,
    而<a href="/zh/tools/token-counter.html">分词与成本计算器</a>可为你的真实 prompt 计价。</p>
{sibling}  </section>

  <section class="prose">
    {prose}

    <h2>常见问题</h2>
    {faq_html}
  </section>
"""
    html = html.replace("@@MODELCOUNT@@", str(len(MODELS)))

    html += ZH_FOOT.replace("</body>", CALC_JS.replace("@@ID@@", slug) + "\n</body>")
    return html


# Provider order for the hub table, most-searched first. Alphabetical order put
# Alibaba above OpenAI, which is not what anyone arrives looking for.
PROVIDER_ORDER = ["OpenAI", "Anthropic", "Google", "DeepSeek", "xAI", "Alibaba",
                  "ByteDance", "Moonshot", "Z.AI", "MiniMax", "Xiaomi", "Mistral"]


def hub_order(m):
    """Ranked models first, then everything else grouped by provider popularity.

    `rank` is an editorial field in models.json for the models people actually
    look up. Unranked models fall below all of them, so a newly added model
    never jumps the queue by accident.
    """
    r = m.get("rank")
    if r is not None:
        return (0, r, 0, "")
    try:
        p = PROVIDER_ORDER.index(m["provider"])
    except ValueError:
        p = len(PROVIDER_ORDER)
    return (1, p, m["input"], m["name"])


def note_preview(m, limit=110):
    """Shorten the note on the hub table only.

    Full notes run to 40 words and turn each row into a six-line block, which
    defeats the point of a comparison table — you can only see five models per
    screen. The full text stays on the model page.
    """
    n = m["note"].rstrip(". ")
    if len(n) <= limit:
        return n
    return n[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def index_page():
    ordered = sorted(MODELS, key=hub_order)
    rows = []
    for m in ordered:
        rows.append(
            "<tr><td><a href=\"/models/%s.html\">%s</a></td><td>%s</td><td class=\"num\">%s</td>"
            "<td class=\"num\">%s</td><td class=\"num\">%s</td><td>%s</td><td>%s</td></tr>" % (
                m["id"], esc(m["name"]), esc(m["provider"]), zh_money(m, "input"),
                zh_money(m, "output"), zh_money(m, "cached_input"),
                m.get("context") or "—", esc(note_preview(m))))
    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "LLM API pricing comparison 2026",
        "numberOfItems": len(MODELS),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "name": m["name"],
             "url": "%s/models/%s.html" % (BASE, m["id"])}
            for i, m in enumerate(ordered)]
    }, ensure_ascii=False)
    canonical = BASE + "/models/index.html"
    html = HEAD.replace("@@TITLE@@", esc("LLM API pricing comparison 2026 — %d models per 1M tokens | ezaiops tools" % len(MODELS)))
    html = html.replace("@@DESC@@", esc("Side-by-side input/output pricing per 1M tokens for GPT-5.6, Claude Opus 5, Gemini 3.1 Pro, DeepSeek V4, Grok 4.5 and Mistral — with context windows and cache rates."))
    html = html.replace("@@CANON@@", canonical)
    html = html.replace(
        '<link rel="canonical" href="%s">' % canonical,
        '<link rel="canonical" href="%s">\n%s' % (
            canonical, en_hreflang(canonical, BASE + "/zh/models/index.html")))
    html = html.replace("@@LD@@", ld)
    html += """
<main class="wrap tool-page">
  <nav class="crumbs"><a href="/">Home</a> / LLM pricing<a class="main-site-link" href="https://ezaiops.com/en/">ezaiops.com \u2197</a></nav>
  <h1>LLM API pricing, model by model</h1>
  <p class="lead">Every major frontier model, priced per 1M tokens, side by side. Data verified
  against official provider documentation on @@UPD@@. Rows are ordered by how often people look
  them up, not alphabetically — the flagship tiers sit at the top, older and cheaper tiers below.
  Pick a row for the full breakdown, a calculator and neighbor comparisons — or jump straight to the
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


def index_page_zh():
    ordered = sorted(MODELS, key=hub_order)
    rows = []
    for m in ordered:
        note = NOTES.get(m["id"], m["note"]).rstrip(". ")
        if len(note) > 110:
            note = note[:110].rsplit(" ", 1)[0].rstrip(",;:") + "…"
        rows.append(
            "<tr><td><a href=\"/zh/models/%s.html\">%s</a></td><td>%s</td><td class=\"num\">%s</td>"
            "<td class=\"num\">%s</td><td class=\"num\">%s</td><td>%s</td><td>%s</td></tr>" % (
                m["id"], esc(m["name"]), esc(m["provider"]), zh_money(m, "input"),
                zh_money(m, "output"), zh_money(m, "cached_input"),
                m.get("context") or "—", esc(note)))
    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "LLM API pricing comparison 2026",
        "numberOfItems": len(MODELS),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "name": m["name"],
             "url": "%s/zh/models/%s.html" % (BASE, m["id"])}
            for i, m in enumerate(ordered)]
    }, ensure_ascii=False)
    canonical = BASE + "/zh/models/index.html"
    en_url = BASE + "/models/index.html"
    title = "LLM API 价格对比 2026——每 1M tokens 共 %d 款模型 | ezaiops tools" % len(MODELS)
    desc = ("GPT-5.6、Claude Opus 5、Gemini 3.1 Pro、DeepSeek V4、Grok 4.5 与 Mistral 等模型的"
            "每 1M tokens 输入/输出价格并列对比——含上下文窗口与缓存费率。")
    switch = static_switch("/zh/models/index.html", "/models/index.html?lang=en")
    html = ZH_HEAD
    html = html.replace("@@TITLE@@", esc(title)).replace("@@DESC@@", esc(desc))
    html = html.replace("@@CANON@@", canonical).replace("@@ENURL@@", en_url)
    html = html.replace("@@LD@@", ld).replace("@@SWITCH@@", switch)
    html += """
<main class="wrap tool-page">
  <nav class="crumbs"><a href="/zh/">首页</a> / 模型价格<a class="main-site-link" href="https://ezaiops.com/">ezaiops.com \u2197</a></nav>
  <h1>LLM API 价格:逐模型对比</h1>
  <p class="lead">所有主流前沿模型,按每 1M tokens 定价并排对比。数据已于 @@UPD@@ 对照各厂商
  官方文档核实。行序按被查看的频率而非字母顺序排列——旗舰档位在顶部,更老更便宜的档位在下。
  点击任意一行可查看完整明细、计算器与邻近模型对比——或直接跳转到
  <a href="/zh/tools/token-counter.html">分词与成本计算器</a>。</p>
  <p class="main-site-banner">属于 <a href="https://ezaiops.com/">ezaiops.com</a> — AI agent 可观测性、LLMOps 与生产 AI 运维实战笔记。</p>

  <section class="panel">
    <table class="data">
      <thead><tr><th>模型</th><th>提供商</th><th class="num">输入 / 1M</th><th class="num">输出 / 1M</th><th class="num">缓存输入</th><th>上下文</th><th>备注</th></tr></thead>
      <tbody>@@ROWS@@</tbody>
    </table>
    <p class="note">标 <strong>¥</strong> 的是中国大陆官方定价（取自各厂商国内站）；标 <strong>$</strong> 的模型在中国大陆没有官方 API，显示的是国际站美元价。两套价目由厂商分别制定，<strong>不是汇率换算</strong>——同一模型在不同区域的价格本来就不一样。</p>
  </section>

  <section class="prose">
    <h2>如何阅读这张表</h2>
    <p>两个数字说明一切:<strong>输入价格</strong>(你发送的内容)与<strong>输出价格</strong>(模型生成的内容)。
    输出按输入的 2–8 倍计费,具体取决于厂商,因此仅看头条输入价几乎无法判断真实账单。
    缓存输入——重复发送同一段长系统提示或上下文前缀——通常只为基础输入费率的一小部分。</p>
    <h2>资料来源</h2>
    <ul>@@SOURCES@@</ul>
  </section>
</main>
"""
    html += ZH_FOOT
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

    # The Chinese edition of the pricing tree. Generated here (not by
    # generate_zh.mjs — the model pages have no runtime dictionary), with the
    # same change-detection so sitemap lastmod reflects real edits only.
    zh_models_dir = os.path.join(ROOT, "zh", "models")
    os.makedirs(zh_models_dir, exist_ok=True)
    zh_pages = []
    for m in MODELS:
        path = os.path.join(zh_models_dir, m["id"] + ".html")
        html = model_page_zh(m)
        try:
            with open(path, encoding="utf-8") as fh:
                if fh.read() == html:
                    zh_pages.append(("%s/zh/models/%s.html" % (BASE, m["id"]), path))
                    continue
        except OSError:
            pass
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        zh_pages.append(("%s/zh/models/%s.html" % (BASE, m["id"]), path))

    for p in sorted(glob.glob(os.path.join(zh_models_dir, "*.html"))):
        if os.path.basename(p) not in live:
            os.remove(p)
            print("removed stale page: zh/models/%s" % os.path.basename(p))

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

    zh_index_path = os.path.join(zh_models_dir, "index.html")
    zh_index_html = index_page_zh()
    try:
        with open(zh_index_path, encoding="utf-8") as fh:
            unchanged = fh.read() == zh_index_html
    except OSError:
        unchanged = False
    if not unchanged:
        with open(zh_index_path, "w", encoding="utf-8") as fh:
            fh.write(zh_index_html)
    zh_pages.append((BASE + "/zh/models/index.html", zh_index_path))

    # "/" is the canonical home page, so index.html is deliberately not listed
    # again here — a sitemap that lists both asks Google to crawl a duplicate.
    static_pages = [(BASE + "/", os.path.join(ROOT, "index.html"))]
    for p in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        if os.path.basename(p) in ("index.html", "404.html"):
            continue
        static_pages.append((BASE + "/" + os.path.basename(p), p))
    for p in sorted(glob.glob(os.path.join(ROOT, "tools", "*.html"))):
        static_pages.append((BASE + "/tools/" + os.path.basename(p), p))

    # The Chinese edition (generated by scripts/generate_zh.mjs) is a separate
    # URL tree, so it gets its own entries. hreflang pairing lives in each page's
    # <head>; listing both trees here is what lets Baidu find the Chinese copy.
    zh_meta = os.path.join(ROOT, "scripts", "zh-meta.json")
    if os.path.exists(zh_meta):
        with open(zh_meta, encoding="utf-8") as fh:
            meta = json.load(fh)
        for rel in meta:
            if rel.startswith("_"):
                continue
            path = os.path.join(ROOT, "zh", rel)
            if not os.path.exists(path):
                continue
            url = BASE + ("/zh/" if rel == "index.html" else "/zh/" + rel)
            zh_pages.append((url, path))

    allurls = static_pages + zh_pages + pages

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write(sitemap(allurls))

    print("models.js written (%d models)" % len(MODELS))
    print("model pages written: %d" % len(MODELS))
    print("sitemap entries: %d" % len(allurls))


if __name__ == "__main__":
    main()
