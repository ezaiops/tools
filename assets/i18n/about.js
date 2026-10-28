/* About page dictionary. Chrome strings live in common.js. */
window.I18N_DICTS = window.I18N_DICTS || [];
window.I18N_DICTS.push({
  "title:About — ezaiops tools": "关于 — ezaiops tools",
  "About ezaiops tools": "关于 ezaiops 工具站",
  "Free utilities for LLM cost math and everyday engineering work. No accounts, no uploads, no backend that could store what you type.": "免费的 LLM 成本测算与日常工程工具。没有账号，没有上传，也没有任何后端可以存下你输入的内容。",

  "What this site is": "这是什么",
  "tools.ezaiops.com is a collection of 18 browser-based tools and a pricing database covering 43 LLM models. Everything is static HTML, CSS and JavaScript served from GitHub Pages — there is no application server behind it, which is why the tools can promise that your input stays on your device: there is nowhere for it to go.": "tools.ezaiops.com 包含 18 个浏览器端工具，以及覆盖 43 个 LLM 模型的价格数据库。整站是托管在 GitHub Pages 上的静态 HTML、CSS 与 JavaScript——背后没有应用服务器，所以这些工具才敢承诺输入不出本机：根本没有地方可去。",

  "Why the tools run locally": "为什么全部在本地运行",
  "Most free online utilities work by posting your input to a server, processing it there, and sending back the result. That is fine for a colour picker and not fine for a prompt containing customer data, a JWT, a contract PDF or a private key. These tools parse, hash, compress and render in the tab you already have open. Three of them (the token counter, QR generator and PDF tools) download a library from a CDN the first time you use them; the library runs locally and your content is never part of that request.": "大多数免费在线工具的做法是：把你的输入发到服务器、在那边处理、再把结果送回来。选个颜色无所谓，但一段含客户数据的 prompt、一个 JWT、一份合同 PDF 或一把私钥就不行了。这里的工具全部在你已打开的这个标签页里完成解析、哈希、压缩和渲染。其中三个（分词计数、二维码生成、PDF 工具）会在首次使用时从 CDN 下载一个库；库在本地运行，你的内容从不包含在那个请求里。",

  "How the pricing data is maintained": "价格数据怎么维护",
  "Every price on the site comes from a single data file, and each pricing page shows the date it was last verified. Rates are read from the providers' own documentation — OpenAI, Anthropic, Google, DeepSeek, xAI, Z.AI, Moonshot, MiniMax, Xiaomi and Mistral — rather than from aggregator blogs, because aggregators lag. Long-context tiers, cached-input rates, batch discounts and peak/off-peak windows are modelled explicitly rather than averaged into one number.": "站上每一个价格都来自同一个数据文件，每个价格页都会标注最后核对日期。费率直接读各家官方文档——OpenAI、Anthropic、Google、DeepSeek、xAI、Z.AI、Moonshot、MiniMax、小米和 Mistral——而不是抄聚合博客，因为聚合站总是慢半拍。长上下文档位、缓存命中价、Batch 折扣和峰谷时段都按规则显式建模，不会糊成一个平均值。",

  "el:Pricing changes constantly. If you spot a figure that no longer matches the provider's page, tell us and it gets corrected — that is the single most useful thing a reader can send.": "价格一直在变。如果你发现某个数字和厂商页面已经对不上，<a href=\"/contact.html\">告诉我们</a>，我们会改——这是读者能发来的最有价值的一条消息。",

  "What we do not do": "我们不做什么",
  "No accounts, no email capture, no newsletter gate.": "不做账号，不收邮箱，不用订阅墙拦人。",
  "No paid placement: nobody can buy a position in a comparison table or a \"cheapest\" label.": "不卖位置：没有人能花钱买对比表里的排序或「最便宜」标签。",
  "No selling or sharing of data, because the tools never collect it.": "不卖也不共享数据，因为工具根本不收集。",

  "Who is behind it": "谁在做这件事",
  "el:ezaiops publishes field notes on AI agent observability, LLMOps and production AI operations at ezaiops.com. The tools grew out of that work — the cost calculator exists because estimating an agent's monthly bill from a pricing page is genuinely annoying, and the subnet and cron utilities exist because we kept needing them. Source code and issue tracker live on GitHub.": "ezaiops 在 ezaiops.com 写 AI Agent 可观测性、LLMOps 与生产级 AI 运维的实战笔记。这些工具是那些工作的副产品——成本计算器之所以存在，是因为照着价格页估算 agent 的月账单实在烦人；子网和 cron 工具则是因为我们自己一直在用。源码和 issue 都在 <a href=\"https://github.com/ezaiops\">GitHub</a> 上。",

  "Get in touch": "联系我们",
  "el:Corrections, bug reports and feature requests are all welcome — see the contact page for the fastest route. The privacy policy explains what little data the site touches.": "纠错、报 bug、提需求都欢迎——最快的方式见<a href=\"/contact.html\">联系页</a>。<a href=\"/privacy.html\">隐私政策</a>说明了本站会接触到的那一点点数据。"
});
