#!/usr/bin/env python3
"""One-off: add the el: keys that mixed-content paragraphs need.

A paragraph like "…with <code>pdf-lib</code>. Your documents…" is split into
several text nodes, so neither the plain-text dictionary nor a text-node walk
can translate it. The engine's el: prefix replaces the element's innerHTML
instead, which is the only thing that works for mixed content.

The keys must match textContent with whitespace collapsed, so they are derived
from the pages rather than typed by hand.
"""
import html
import json
import os
import re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRANSLATIONS = {
    "tools/cron-explainer.html": (
        "粘贴一条 cron 表达式，得到一句大白话说明，以及接下来 10 次的实际执行时间（按你的本地时区）。"
        "支持标准五字段 cron 和 <code>@daily</code> 这类特殊字符串。"
    ),
    "tools/cron-generator.html": (
        "用普通控件选好分钟、小时、日、星期，直接得到准确的 cron 表达式、一句说明和接下来的执行时间。"
        '它是 <a href="/tools/cron-explainer.html">cron 解释器</a> 的反向工具。'
    ),
    "tools/meta-tag-generator.html": (
        "填好字段，把生成的标签粘进页面的 <code>&lt;head&gt;</code>，同时实时预览它在 Google 搜索结果"
        "和社交对话里的样子——第一印象一次就做对。"
    ),
    "tools/mortgage-calculator.html": (
        "算出任意固定利率贷款的月供、总利息和还清日期，两种还款方式都支持。<strong>等额本息</strong>"
        "每月还款额相同；<strong>等额本金</strong>每月偿还固定本金，所以前期还款高、逐月递减。"
        "公积金加商贷这类两段利率的组合贷，按每期明细拆分。全部在浏览器本地计算。"
    ),
    "tools/password-generator.html": (
        "生成密码学级别的随机密码、易记短语和 RFC 4122 v4 UUID，支持批量生成，本地运行并实时评估强度。"
        "使用浏览器的 <code>crypto.getRandomValues</code>——与 TLS 密钥同一级别的随机源。"
    ),
    "tools/pdf-tools.html": (
        "把多个 PDF 合成一个文件，或从 PDF 里抽取指定页码范围——本地完成，基于 <code>pdf-lib</code>。"
        "文档在浏览器里读取、从不上传，处理机密文件才放心。"
    ),
    "tools/regex-tester.html": (
        "在实时文本上测试 JavaScript 正则表达式。输入时即高亮匹配，逐个列出捕获组，"
        "替换预览显示 <code>String.replace()</code> 的真实结果。"
    ),
    "tools/self-host-vs-api.html": (
        "调 API 方便，但不一定最便宜。输入每月 token 用量和 GPU 假设，算出盈亏平衡点——"
        "也就是从哪个用量开始，租 GPU 跑开源模型（vLLM、SGLang、llama.cpp）比按 token 付费更划算。"
        '价格取自我们的<a href="/models/index.html">模型价格表</a>，核实日期 2026-10-13。'
    ),
}

COMMON = {
    # The breadcrumb separator lives in the same text node as the label, so the
    # dictionary key has to include it.
    "/ Tools /": "/ 工具 /",
    "GPT-5.6 Sol pricing": "GPT-5.6 Sol 价格",
    "Claude Opus 5 pricing": "Claude Opus 5 价格",
    "Gemini 3.1 Pro pricing": "Gemini 3.1 Pro 价格",
    "DeepSeek V4.1 Flash pricing": "DeepSeek V4.1 Flash 价格",
}


class Lead(HTMLParser):
    """Capture the innerHTML of the first <p class="lead">."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.depth = 0
        self.buf = []
        self.done = False

    def handle_starttag(self, t, a):
        if self.done:
            return
        attrs = dict(a)
        if self.depth == 0 and t == "p" and "lead" in (attrs.get("class") or ""):
            self.depth = 1
            return
        if self.depth:
            self.depth += 1
            self.buf.append(self.get_starttag_text())

    def handle_endtag(self, t):
        if not self.depth or self.done:
            return
        self.depth -= 1
        if self.depth == 0:
            self.done = True
        else:
            self.buf.append("</%s>" % t)

    def handle_data(self, d):
        if self.depth:
            self.buf.append(d)

    def handle_entityref(self, n):
        if self.depth:
            self.buf.append("&%s;" % n)

    def handle_charref(self, n):
        if self.depth:
            self.buf.append("&#%s;" % n)


def text_content(markup):
    """Mirror the engine's el: matcher: strip tags, unescape, collapse space."""
    plain = re.sub(r"<[^>]+>", "", markup)
    return re.sub(r"\s+", " ", html.unescape(plain)).strip()


def dict_path_for(page):
    if page.startswith("tools/"):
        return os.path.join(ROOT, "assets", "i18n", "tools",
                            os.path.basename(page)[:-5] + ".js")
    return os.path.join(ROOT, "assets", "i18n", "common.js")


def load_dict(path):
    s = open(path, encoding="utf-8").read()
    return json.loads(s[s.index("push(") + 5:s.rindex(")")].strip())


def append_keys(path, new):
    """Append entries as text so the existing file keeps its grouping and comments."""
    have = load_dict(path)
    todo = [(k, v) for k, v in new.items() if k not in have]
    if not todo:
        return 0
    s = open(path, encoding="utf-8").read()
    cut = s.rindex("})")
    head, tail = s[:cut].rstrip(), s[cut:]
    if not head.endswith(("{", ",")):
        head += ","
    rows = ",\n".join(
        "  %s: %s" % (json.dumps(k, ensure_ascii=False), json.dumps(v, ensure_ascii=False))
        for k, v in todo)
    out = head + "\n\n  " + rows + "\n" + tail
    open(path, "w", encoding="utf-8", newline="\n").write(out)
    json.loads(out[out.index("push(") + 5:out.rindex(")")].strip())  # must stay valid
    return len(todo)


added = 0
for page, zh in TRANSLATIONS.items():
    p = Lead()
    p.feed(open(os.path.join(ROOT, page), encoding="utf-8").read())
    key = "el:" + text_content("".join(p.buf))
    n = append_keys(dict_path_for(page), {key: zh})
    added += n
    print("%-34s %s" % (page, "added" if n else "already there"))

added += append_keys(os.path.join(ROOT, "assets", "i18n", "common.js"), COMMON)
print("\n新增条目:", added)
