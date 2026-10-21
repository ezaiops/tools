#!/usr/bin/env python3
"""Generate LLM model pricing landing pages + calculator dataset + sitemap for tools.ezaiops.com.

Single source of truth: scripts/models.json
Outputs:
  assets/models.js          window.EZ_MODELS = {...}  (consumed by the token counter)
  models/<id>.html           one SEO landing page per model
  models/index.html          comparison hub
  sitemap.xml
"""
import json
import os
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://tools.ezaiops.com"
import datetime

with open(os.path.join(ROOT, "scripts", "models.json"), encoding="utf-8") as fh:
    DATA = json.load(fh)
MODELS = DATA["models"]
# Derive both dates from the data file so the pages can never claim a different
# "last updated" date than the prices they show.
TODAY = datetime.date.today().isoformat()
UPDATED = DATA.get("updated") or TODAY
SOURCES = DATA.get("sources", [])
BY_ID = {m["id"]: m for m in MODELS}


def money(x):
    if x is None:
        return "—"
    if float(x) == int(float(x)):
        return "$" + str(int(float(x)))
    s = ("%f" % float(x)).rstrip("0").rstrip(".")
    return "$" + s


def blended(m, out_ratio):
    """Blended per-1M rate at a given output share, used only for sorting."""
    return (1 - out_ratio) * m["input"] + out_ratio * m["output"]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITLE@@</title>
<meta name="description" content="@@DESC@@">
<link rel="canonical" href="@@CANON@@">
<meta property="og:type" content="website">
<meta property="og:title" content="@@TITLE@@">
<meta property="og:description" content="@@DESC@@">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="stylesheet" href="/assets/style.css?v=20261022b">
<script type="application/ld+json">
@@LD@@
</script>
</head>
<body>

<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/"><span class="logo">ez</span>ezaiops <small>tools</small></a>
    <nav class="site-nav">
      <a href="/">Tools</a>
      <a href="/models/index.html">LLM pricing</a>
      <a href="https://ezaiops.com/en/" title="ezaiops.com — AI agent observability &amp; LLMOps field notes (in English)">Blog</a>
      <a href="https://github.com/ezaiops">GitHub</a>
    </nav>
  </div>
</header>
"""

CRUMBS = """
<main class="wrap tool-page">
  <nav class="crumbs"><a href="/">Home</a> / <a href="/models/index.html">LLM pricing</a> / @@NAME@@<a class="main-site-link" href="https://ezaiops.com/en/">ezaiops.com \u2197</a></nav>
"""

FOOT = """
<div class="ad-slot">
  <strong>Ad slot</strong>
  Google AdSense placeholder — activated once the site is approved and has steady traffic.
</div>
</main>

<footer class="site-footer">
  <div class="wrap">
    <div class="cols">
      <div>
        <h4>Popular tools</h4>
        <ul>
          <li><a href="/tools/token-counter.html">LLM token &amp; cost calculator</a></li>
          <li><a href="/tools/json-formatter.html">JSON formatter</a></li>
          <li><a href="/tools/regex-tester.html">Regex tester</a></li>
          <li><a href="/tools/cron-explainer.html">Cron explainer</a></li>
          <li><a href="/tools/encode-decode.html">Base64 / URL / hash</a></li>
        </ul>
      </div>
      <div>
        <h4>LLM pricing</h4>
        <ul>
          <li><a href="/models/index.html">All models</a></li>
          <li><a href="/models/gpt-5-6-sol.html">GPT-5.6 Sol pricing</a></li>
          <li><a href="/models/claude-opus-5.html">Claude Opus 5 pricing</a></li>
          <li><a href="/models/gemini-3-1-pro.html">Gemini 3.1 Pro pricing</a></li>
          <li><a href="/models/deepseek-v4-1-flash.html">DeepSeek V4.1 Flash pricing</a></li>
        </ul>
      </div>
      <div>
        <h4>More</h4>
        <ul>
          <li><a href="https://ezaiops.com/en/">ezaiops.com</a></li>
          <li><a href="/about.html">About</a></li>
          <li><a href="/contact.html">Contact</a></li>
          <li><a href="/privacy.html">Privacy policy</a></li>
          <li><a href="https://github.com/ezaiops">GitHub</a></li>
        </ul>
      </div>
    </div>
    <div class="legal">&copy; <span data-year>2026</span> ezaiops &middot; your input never leaves your browser</div>
  </div>
</footer>

<script src="/assets/common.js?v=20261022b" defer></script>
<script src="/assets/models.js?v=20261022b" defer></script>
</body>
</html>
"""
