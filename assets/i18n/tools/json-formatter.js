/* JSON formatter page dictionary. Chrome strings live in common.js. */
window.I18N_DICTS = window.I18N_DICTS || [];
window.I18N_DICTS.push({
  "JSON formatter & validator": "JSON 格式化与校验",
  "Paste JSON to format it with proper indentation, minify it for transport, or validate it — with the exact line and column of the first syntax error. Everything runs locally; large API payloads never leave the page.": "粘贴 JSON，用规范的缩进格式化、压缩以便传输，或进行校验——并给出第一处语法错误的精确行列。全部本地运行，大型 API 报文也不会离开页面。",
  "Input JSON": "输入 JSON",
  "Format": "格式化",
  "Minify": "压缩",
  "Validate": "校验",
  "Copy result": "复制结果",
  "Sample": "示例",
  "Clear": "清空",
  "Indent": "缩进",
  "2 spaces": "2 空格",
  "4 spaces": "4 空格",
  "Tab": "制表符",

  "What this JSON formatter does": "这个 JSON 格式化工具能做什么",
  "Formatting (also called beautifying) re-serializes your document with consistent indentation, which makes deeply nested API responses readable. Minifying does the opposite — it strips all optional whitespace, which is what you want when shipping payloads over the wire or embedding data in a config file.": "格式化（也称美化）用一致的缩进重新序列化文档，让深层嵌套的 API 响应变得可读。压缩则相反——去掉所有非必需空白，适合在线传输负载或嵌入配置文件。",
  "Validation parses the document strictly according to the JSON spec (RFC 8259) and reports the precise location of the first problem: the line, the column, and the parser's own message. That single position is usually enough to spot a trailing comma, an unescaped quote or a mismatched bracket.": "校验严格按照 JSON 规范（RFC 8259）解析文档，并报告第一处问题的精确位置：行号、列号以及解析器本身的报错。这一个位置通常就足以定位尾随逗号、未转义引号或括号不匹配。",

  "Common JSON errors and what they mean": "常见 JSON 错误及含义",
  "el:Trailing commas — {\"a\": 1,} is invalid JSON, though legal in JavaScript objects.": "<strong>尾随逗号</strong>——<code>{\"a\": 1,}</code> 是无效 JSON，尽管在 JavaScript 对象中合法。",
  "el:Single quotes — JSON strings require double quotes; {'a': 1} fails.": "<strong>单引号</strong>——JSON 字符串必须用双引号，<code>{'a': 1}</code> 会报错。",
  "el:Comments — // and /* */ are not allowed in strict JSON (use JSONC if you need comments in config).": "<strong>注释</strong>——严格 JSON 不允许 <code>//</code> 和 <code>/* */</code>（配置里需要注释就用 JSONC）。",
  "el:Unquoted keys — {a: 1} fails; keys must be strings.": "<strong>未加引号的键</strong>——<code>{a: 1}</code> 会失败，键必须是字符串。",
  "el:NaN / Infinity / undefined — none exist in JSON; use null or a string.": "<strong>NaN / Infinity / undefined</strong>——JSON 中都不存在，请用 <code>null</code> 或字符串。",

  "Is there a size limit?": "有大小限制吗？",
  "Is my JSON uploaded anywhere?": "我的 JSON 会被上传吗？",
  "Why does the formatted output reorder my keys?": "为什么格式化后键的顺序变了？",
  "The only limit is your browser's memory. Documents of several megabytes format instantly because everything happens on your device with no upload step.": "唯一限制是你浏览器的内存。几 MB 的文档也能瞬间格式化，因为一切都发生在你的设备上，没有上传环节。",
  "No. Parsing, formatting and validation are done with the browser's built-in JSON.parse / JSON.stringify. Nothing is transmitted.": "不会。解析、格式化和校验都由浏览器内置的 JSON.parse / JSON.stringify 完成，没有任何传输。",
  "el:It doesn't — JSON.stringify preserves insertion order. If order changed, the input had duplicate keys and the parser kept the last occurrence, exactly as JSON.parse does.": "不会——<code>JSON.stringify</code> 保持插入顺序。如果顺序变了，说明输入里有重复键，解析器保留了最后一次出现的值，与 <code>JSON.parse</code> 的行为一致。",

  "Heads up: ": "注意：",
  "%s number(s) (%s) exceed JavaScript's range and were written as null.": "%s 个数值（%s）超出 JavaScript 的表示范围，已被写成 null。",
  "Integers longer than 15 digits (e.g. %s…) lose precision — JSON numbers are IEEE-754 doubles. Keep IDs as strings.": "超过 15 位的整数（如 %s…）会丢失精度——JSON 数字是 IEEE-754 双精度浮点。ID 类字段请用字符串。"
});
