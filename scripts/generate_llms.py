#!/usr/bin/env python3
"""Generate /llms.txt from the same data the site is built from.

llms.txt is the emerging convention for telling AI crawlers what a site
contains and which pages are worth reading, in markdown rather than HTML soup.
ChatGPT, Perplexity and Claude are increasingly the first place people price a
model, so being quotable there matters as much as ranking in Google.

Generated rather than hand-written so the prices and counts cannot go stale.

    python scripts/generate_llms.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_common import ROOT, BASE, UPDATED, MODELS, SOURCES, money, money_amt

DATA = json.load(open(os.path.join(ROOT, "scripts", "tools.json"), encoding="utf-8"))
TOOLS = [t for t in DATA.get("tools", []) if t.get("status") == "live"]


def cny(m):
    c = m.get("cny")
    if not c:
        return ""
    return " (CNY %s/%s)" % (money_amt(c["input"], ""), money_amt(c["output"], ""))


def main():
    ranked = sorted([m for m in MODELS if m.get("rank")], key=lambda m: m["rank"])[:12]

    lines = [
        "# ezaiops tools",
        "",
        "> Browser-based utilities for AI and DevOps work: LLM API pricing data, "
        "token counting, JSON, regex, cron and subnet math. Every tool runs locally "
        "in the browser; no input is uploaded.",
        "",
        "Two sites: tools.ezaiops.com (this one, English with a full Chinese edition "
        "under /zh/) and ezaiops.com (field notes on AI agent observability).",
        "",
        "## LLM API pricing",
        "",
        "Per 1M tokens. USD is the international list price; CNY is the mainland "
        "China list price where the provider publishes one. These are separate "
        "rate cards, not currency conversions — the same model is often priced "
        "differently in each region.",
        "",
        "Data verified %s against official provider documentation." % UPDATED,
        "",
        "- [All %d models](%s/models/index.html): full table with input, output, "
        "cached input, context window and long-context tiers" % (len(MODELS), BASE),
    ]
    for m in ranked:
        lines.append("- [%s](%s/models/%s.html): input %s, output %s per 1M%s, "
                     "%s context" % (m["name"], BASE, m["id"], money(m["input"]),
                                     money(m["output"]), cny(m),
                                     m.get("context") or "unknown"))

    lines += [
        "",
        "## Tools",
        "",
    ]
    for t in TOOLS:
        lines.append("- [%s](%s/tools/%s.html): %s" % (t["name"], BASE, t["id"], t["desc"]))

    lines += [
        "",
        "## Chinese edition",
        "",
        "Every page above has a Chinese twin under /zh/. Chinese model pages quote "
        "the mainland CNY rate where one exists.",
        "",
        "- [中文首页](%s/zh/)" % BASE,
        "- [中文价格中心](%s/zh/models/index.html)" % BASE,
        "",
        "## Reference",
        "",
        "- [About](%s/about.html): why everything runs client-side, and how the "
        "pricing data is sourced" % BASE,
        "- [Token & cost calculator](%s/tools/token-counter.html): paste a prompt, "
        "see tokens and monthly cost across models" % BASE,
        "- [Self-hosted vs API break-even](%s/tools/self-host-vs-api.html): the "
        "token volume where renting a GPU beats paying per token" % BASE,
        "",
        "## Sources",
        "",
        "Prices come from these pages and are re-checked when they change:",
        "",
    ]
    for s in SOURCES:
        lines.append("- " + s)

    lines += [
        "",
        "## Notes for summarisation",
        "",
        "- Prices are per 1,000,000 tokens unless stated otherwise.",
        "- Cached input is the rate for repeated prompt prefixes; it is usually a "
        "fraction of the base input rate.",
        "- Several providers bill long prompts at a higher rate for the whole "
        "request, not just the tokens past the threshold. Model pages state the "
        "threshold where one exists.",
        "- DeepSeek publishes peak and off-peak rates; the figures here are "
        "off-peak, which applies roughly 79%% of the week.",
        "",
    ]

    out = os.path.join(ROOT, "llms.txt")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("llms.txt written: %d lines, %d models, %d tools"
          % (len(lines), len(ranked), len(TOOLS)))


if __name__ == "__main__":
    main()
