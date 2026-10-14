/* Base64 / URL / hash page dictionary. Chrome strings live in common.js. */
window.I18N_DICTS = window.I18N_DICTS || [];
window.I18N_DICTS.push({
  "Base64 / URL encoder & hash generator": "Base64 / URL 编码与哈希生成器",
  "Encode and decode text with Base64 or URL encoding, escape HTML entities, or compute cryptographic checksums — including a pure-JavaScript SHA-256 that works even in non-secure contexts. UTF-8 safe throughout.": "Base64 与 URL 编解码、HTML 实体转义，或计算加密校验值——其中的 SHA-256 为纯 JavaScript 实现，在非安全上下文也能用。全程 UTF-8 安全。",
  "HTML entities": "HTML 实体",
  "Hash": "哈希",
  "Input": "输入",
  "Output": "输出",
  "Algorithm": "算法",
  "Output format": "输出格式",
  "Hexadecimal": "十六进制",
  "Encode": "编码",
  "Decode": "解码",
  "Encode component": "编码（组件）",
  "Decode component": "解码（组件）",
  "Encode full URL": "编码完整 URL",
  "Escape": "转义",
  "Unescape": "还原",
  "Compute hash": "计算哈希",
  "Copy output": "复制输出",
  "Move output to input": "输出转为输入",
  "Clear": "清空",
  "SHA-256 falls back to a built-in implementation; other algorithms need a secure context (https or localhost)": "SHA-256 使用内置实现；其他算法需要安全上下文（https 或 localhost）",

  "Encoding notes": "编码说明",
  "el:Base64 turns binary or UTF-8 text into ASCII using a 64-character alphabet. Encoding is UTF-8 safe here, so CJK text and emoji round-trip correctly.": "<strong>Base64</strong> 用 64 个字符的字母表把二进制或 UTF-8 文本编码为 ASCII。这里的编码是 UTF-8 安全的，CJK 文本和 emoji 都能正确往返。",
  "el:URL encoding percent-encodes characters that are not allowed in URLs. \"Component\" mode (encodeURIComponent) escapes more aggressively — use it for query parameter values, not whole URLs.": "<strong>URL 编码</strong>把 URL 中不允许的字符百分号转义。「组件」模式（encodeURIComponent）转义更彻底——用于查询参数值，不要用于整个 URL。",
  "el:HTML entities prevent injection: & for &, < for < and so on.": "<strong>HTML 实体</strong>用于防注入：<code>&amp;</code> 表示 &amp;，<code>&lt;</code> 表示 &lt;，以此类推。",
  "el:SHA-256 is computed by a built-in implementation in JavaScript, so it works everywhere. SHA-1/384/512 use the browser's native crypto.subtle, which requires a secure context (https:// or localhost) — and SHA-1 is cryptographically broken, use it only for legacy checksums.": "<strong>SHA-256</strong> 由内置的 JavaScript 实现计算，任何环境都能用。SHA-1/384/512 使用浏览器原生的 <code>crypto.subtle</code>，需要安全上下文（https:// 或 localhost）——另外 SHA-1 在密码学上已被破解，仅建议用于兼容旧校验和。",

  "Why does Base64 encoding make my file bigger?": "为什么 Base64 编码会让文件变大？",
  "Are my inputs uploaded?": "我的输入会被上传吗？",
  "Base64 or hex for tokens?": "令牌用 Base64 还是 hex？",
  "Base64 encodes 3 bytes as 4 characters, so output is about 33% larger. That is the cost of being able to carry binary data over text-only channels (JSON, URLs, email).": "Base64 把 3 字节编码为 4 个字符，所以输出大约大 33%。这是让二进制数据能穿过纯文本通道（JSON、URL、邮件）的代价。",
  "No. Every conversion runs locally. Nothing is transmitted.": "不会。所有转换都在本地运行，没有任何传输。",
  "Hex is more common for hashes (it is what most checksum tools output); Base64 is more compact. This page outputs hex by default for hashes and can switch to Base64.": "哈希更常用 hex（大多数校验和工具的输出格式）；Base64 更紧凑。本页哈希默认输出 hex，可切换为 Base64。"
});
