#!/usr/bin/env python3
"""Add the el: keys that the prose paragraphs still need.

Every entry below is a paragraph whose English text is split by an inline
<code>/<strong>/<em>/<a>. The engine's text-node walk cannot translate those,
so they were rendering English on the /zh/ pages even where a plain-text
dictionary key existed. el: replaces the element's innerHTML instead.

Keys are derived from the English pages by prefix match rather than typed out,
so they cannot drift from the real textContent.
"""
import html
import json
import os
import re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LEAF = {"p", "li", "dd", "dt", "h2", "h3", "h4", "summary", "figcaption"}
NESTED = re.compile(r"<(p|li|div|ul|ol|table|section|nav|footer|header|h[1-6]|details)\b")

ENTRIES = {
    "cron-generator": [
        ("Share this expression with",
         '把这条表达式丢给 <a href="/tools/cron-explainer.html">cron 解释器</a> 复核含义，'
         '或者直接粘进你的 crontab。'),
        ("A cron line has five fields",
         "一行 cron 有五个字段——分、时、日、月、星期——用空格分隔。每个字段都接受通配符"
         "（<code>*</code>）、单值、列表（<code>1,15</code>）、区间（<code>1-5</code>）"
         "或步长（<code>*/5</code>）。这个生成器总是输出最短的等价写法，"
         "所以 <code>0 9 * * 1-5</code>（工作日 9 点）会保持简洁，而不是展开成一堆列表。"),
        ("One classic trap:",
         "一个经典陷阱：当「日」和「星期」都被限定，cron 会在<em>满足任意一个</em>的日子触发，"
         "而不是两个都满足。如果你选了「1 号」加「周一」，实际得到的是每月 1 号<em>加上</em>"
         "每个周一——通常不是你想要的意思。想让两个条件同时生效，其中一个必须留「每天」。"),
    ],
    "diff-checker": [
        ("Line differences come from",
         "行级差异用 Myers O(ND) 算法计算——和 <code>git diff</code> 同一族。"
         "它找出两个行序列之间最短的编辑脚本（插入与删除）。配对的修改行再做一次词级 Myers 比较，"
         "把行内改动的词高亮出来，小改动才能一眼看清。"),
    ],
    "image-compressor": [
        ("Your file is read with",
         "文件用 <code>FileReader</code> 读进 <code>&lt;img&gt;</code>，"
         "画到 <code>&lt;canvas&gt;</code> 上（缩放就在这一步），"
         "再用 <code>canvas.toBlob()</code> 按你选的质量重新编码。"
         "这就是浏览器自己的编解码路径——没有魔法，也没有服务器。"),
        ("WebP typically gives",
         "<strong>WebP</strong> 在同等画质下通常比 JPEG 小 25–40%，还支持 JPEG 做不到的透明通道。"
         "当前所有浏览器都支持。"),
        ("JPEG is the universal fallback",
         "<strong>JPEG</strong> 是通用兜底格式；照片用 80 质量最合适。"),
        ("PNG is lossless",
         "<strong>PNG</strong> 是无损格式——已经是 PNG 的文件再编码几乎不会变小，"
         "除非缩放或降到 8 位色，而本工具不做这两件事。"),
    ],
    "jwt-debugger": [
        ("A JWT is three base64url",
         "JWT 是三段 base64url 用点连接：<code>header.payload.signature</code>。"
         "header 说明用哪个算法签名（<code>alg</code>）以及令牌类型；payload 装声明——"
         "<code>sub</code>（主体）、<code>iat</code>（签发时间）、<code>exp</code>（过期时间）"
         "这类注册声明，加上签发方自定义的字段。签名覆盖前两段，所以光解码证明不了真实性——"
         "任何人都能改完 payload 再重新编码。验签一定要在服务端用签发方的密钥做。"),
        ("alg: none in the header",
         "header 里出现 <strong>alg: none</strong> 是危险信号——"
         "它在要求验证方完全跳过签名校验。永远不要接受。"),
        ("exp is in seconds",
         "<strong>exp</strong> 是 Unix 纪元秒数；过期令牌应当被拒绝，而不是悄悄刷新。"),
    ],
    "pdf-tools": [
        ("The whole operation uses",
         "整个过程用的是 <code>pdf-lib</code>——一个纯 JavaScript 的 PDF 库，首次使用时从 CDN 加载。"
         "文件由 <code>FileReader</code> 读入，在内存里合并或裁剪，"
         "再用 <code>URL.createObjectURL</code> 写回。"
         "服务端从来看不到这些字节，也没有大小或频率限制，因为没有东西需要计量。"),
        ("Merge concatenates",
         "<strong>合并</strong>按你列出的顺序把完整文档首尾相接。源文件里的书签和表单字段不会保留。"),
    ],
    "qr-generator": [
        ("L (7%)", "<strong>L (7%)</strong>——码面最小，适合干净的数字屏幕。"),
        ("M (15%)", "<strong>M (15%)</strong>——日常默认，海报和包装都够用。"),
        ("Q (25%)", "<strong>Q (25%)</strong>——户外标识，以及可能被磨损的场景。"),
        ("H (30%)", "<strong>H (30%)</strong>——叠加 logo、工业环境，以及会被折腾的二维码。"),
        ("The generator library",
         "生成库（<code>qrcode-generator</code>）在首次使用时从 CDN 加载；"
         "加载失败时页面会明确告诉你，而不是静默失败。加载完成后全部离线运行。"),
    ],
    "self-host-vs-api": [
        ("The catch is utilization",
         "关键在于<strong>利用率</strong>：GPU 只要开着就在烧钱，跟有没有请求无关。"
         "所以低于盈亏平衡点时你纯亏，接近时还要承担 API 替你兜住的运维风险"
         "（SLA、升级、安全补丁）。高于平衡点——通常是每月数亿 token——GPU 就赢了，"
         "而且常常赢 3–10 倍。对多数团队来说诚实的答案是：先用 API，"
         "等稳定的高用量部分明显越过平衡点再迁到自建，同时保留 API 应对突发。"),
        ("Model quality is the other half",
         "模型质量是等式的另一半——本工具只比<em>成本</em>。70B 的开源模型不是 GPT-6 级别的模型；"
         '公平的比较通常是开源模型对便宜的 API 档位（见<a href="/models/index.html">模型价格表</a>）。'),
    ],
    "subnet-calculator": [
        ("An IPv4 address is 32 bits",
         "IPv4 地址是 32 位，写成四段。前缀长度——斜杠后面那个数字——表示前多少位属于网络。"
         "<strong>网络地址</strong>保留这些位、其余置 0；<strong>广播地址</strong>把主机位全置 1。"
         "两者之间（去掉两端保留）就是可分配的主机地址，所以 <code>/24</code> 有 254 个可用地址，"
         "<code>/30</code> 有 2 个——经典的点对点链路。"),
        ("Two details trip people up",
         "有两个细节容易踩坑：可用主机数是 <code>2^(32-prefix) − 2</code>，但 <code>/31</code> 例外"
         "（RFC 3021，点对点链路两个地址都可用），<code>/32</code> 也只有单个主机。"
         "另外像 <code>192.168.1.37/26</code> 这样的主机地址，其实<em>属于</em>"
         "网络 <code>192.168.1.0/26</code>——计算器总是显示该地址所属的网络。"),
    ],
}


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []
        self.out = []
        self.found = []

    def handle_starttag(self, t, a):
        self.out.append(self.get_starttag_text())
        if t in LEAF:
            self.stack.append((t, len(self.out) - 1))

    def handle_startendtag(self, t, a):
        self.out.append(self.get_starttag_text())

    def handle_endtag(self, t):
        self.out.append("</%s>" % t)
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == t:
                _, start = self.stack.pop(i)
                seg = "".join(self.out[start + 1:-1])
                if not NESTED.search(seg):
                    self.found.append(seg)
                break

    def handle_data(self, d):
        self.out.append(d)

    def handle_entityref(self, n):
        self.out.append("&%s;" % n)

    def handle_charref(self, n):
        self.out.append("&#%s;" % n)


def text_content(markup):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", markup))).strip()


def load_dict(path):
    s = open(path, encoding="utf-8").read()
    return json.loads(s[s.index("push(") + 5:s.rindex(")")].strip())


def append_keys(path, new):
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
    json.loads(out[out.index("push(") + 5:out.rindex(")")].strip())
    return len(todo)


total = 0
for page, pairs in ENTRIES.items():
    src = os.path.join(ROOT, "tools", page + ".html")
    p = Paragraphs()
    p.feed(open(src, encoding="utf-8").read())
    by_text = {text_content(seg): seg for seg in p.found}
    new = {}
    for prefix, zh in pairs:
        match = [t for t in by_text if t.startswith(prefix)]
        if len(match) != 1:
            raise SystemExit("%s: prefix %r matched %d paragraphs" % (page, prefix, len(match)))
        new["el:" + match[0]] = zh
    n = append_keys(os.path.join(ROOT, "assets", "i18n", "tools", page + ".js"), new)
    total += n
    print("%-24s %d 段" % (page, n))
print("\n新增 el: 键:", total)
