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
# Curated head-to-head pairs. Defined once at the top level so both model pages
# render the same numbers from the same source instead of two hand-kept copies.
COMPARISONS = DATA.get("comparisons", [])


def money(x):
    """Prices read as prices: whole dollars stay bare ($5), anything with cents
    keeps at least two decimals ($0.60 rather than $0.6), and sub-cent cache
    rates keep the digits they need ($0.003)."""
    if x is None:
        return "—"
    v = float(x)
    if v == int(v):
        return "$" + str(int(v))
    whole, _, frac = ("%.4f" % v).rstrip("0").partition(".")
    return "$%s.%s" % (whole, frac.ljust(2, "0"))


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
<link rel="stylesheet" href="/assets/style.css?v=20261030b">
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

<script src="/assets/common.js?v=20261030b" defer></script>
<script src="/assets/models.js?v=20261030b" defer></script>
</body>
</html>
"""

# The Chinese edition lives under /zh/. These templates mirror the /zh/ pages
# generated by scripts/generate_zh.mjs: same <head> shape (lang="zh-CN"
# data-zh-static, canonical + hreflang, i18n.js + common.js, og:locale zh_CN),
# same chrome labels, and a static lang-switch inside the nav. @@SWITCH@@ is the
# 中文/EN pill for the specific page.
ZH_HEAD = """<!DOCTYPE html>
<html lang="zh-CN" data-zh-static="1"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITLE@@</title>
<meta name="description" content="@@DESC@@">
<link rel="canonical" href="@@CANON@@">
<link rel="alternate" hreflang="zh-CN" href="@@CANON@@">
<link rel="alternate" hreflang="en" href="@@ENURL@@">
<link rel="alternate" hreflang="x-default" href="@@ENURL@@">

<meta property="og:type" content="website">
<meta property="og:title" content="@@TITLE@@">
<meta property="og:description" content="@@DESC@@">
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="stylesheet" href="/assets/style.css?v=20261030b">
<script type="application/ld+json">
@@LD@@
</script>

<script src="/assets/i18n.js?v=20261030b"></script><script src="/assets/i18n/common.js?v=20261030b"></script><meta property="og:locale" content="zh_CN"></head>
<body>

<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/zh/"><span class="logo">ez</span>ezaiops <small>工具</small></a>
    <nav class="site-nav">
      <a href="/zh/">工具</a>
      <a href="/zh/models/index.html">模型价格</a>
      <a href="https://ezaiops.com/" title="ezaiops.com — AI Agent 可观测性与 LLMOps 实战笔记（中文）">博客</a>
      <a href="https://github.com/ezaiops">GitHub</a>
    @@SWITCH@@</nav>
  </div>
</header>
"""

ZH_CRUMBS = """
<main class="wrap tool-page">
  <nav class="crumbs"><a href="/zh/">首页</a> / <a href="/zh/models/index.html">模型价格</a> / @@NAME@@<a class="main-site-link" href="https://ezaiops.com/">ezaiops.com \u2197</a></nav>
"""

ZH_FOOT = """
<div class="ad-slot">
  <strong>广告位</strong>
  Google AdSense 占位——网站通过审批并有稳定流量后启用。
</div>
</main>

<footer class="site-footer">
  <div class="wrap">
    <div class="cols">
      <div>
        <h4>常用工具</h4>
        <ul>
          <li><a href="/zh/tools/token-counter.html">LLM 分词与成本计算器</a></li>
          <li><a href="/zh/tools/json-formatter.html">JSON 工具</a></li>
          <li><a href="/zh/tools/regex-tester.html">正则测试</a></li>
          <li><a href="/zh/tools/cron-explainer.html">Cron 解释</a></li>
          <li><a href="/zh/tools/encode-decode.html">Base64 / URL / 哈希</a></li>
        </ul>
      </div>
      <div>
        <h4>模型价格</h4>
        <ul>
          <li><a href="/zh/models/index.html">全部模型</a></li>
          <li><a href="/zh/models/gpt-6-astra.html">GPT-6 Astra 价格</a></li>
          <li><a href="/zh/models/claude-fable-5-1.html">Claude Fable 5.1 价格</a></li>
          <li><a href="/zh/models/gemini-3-8-flash.html">Gemini 3.8 Flash 价格</a></li>
          <li><a href="/zh/models/deepseek-v4-1-flash.html">DeepSeek V4.1 Flash 价格</a></li>
        </ul>
      </div>
      <div>
        <h4>更多</h4>
        <ul>
          <li><a href="https://ezaiops.com/">ezaiops.com</a></li>
          <li><a href="/zh/about.html">关于</a></li>
          <li><a href="/zh/contact.html">联系</a></li>
          <li><a href="/zh/privacy.html">隐私政策</a></li>
          <li><a href="https://github.com/ezaiops">GitHub</a></li>
        </ul>
      </div>
    </div>
    <div class="legal">© <span data-year>2026</span> ezaiops · 输入内容不会离开你的浏览器</div>
  </div>
</footer>

<script src="/assets/common.js?v=20261030b" defer></script>
<script src="/assets/models.js?v=20261030b" defer></script>
</body>
</html>
"""
