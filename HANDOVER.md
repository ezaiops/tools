# tools.ezaiops.com — 双语改造交接文档

> 交接对象:接手 tools 仓库(模型定价站)的下一个工具 / 人。
> 本文记录 2026-10-30 的两次改动:**模型/定价页的中文版落地**(7af0d89)和**语言偏好持久化**(8c4926a)。
> 相关仓库:`github.com/ezaiops/tools`(本仓库,纯静态,GitHub Pages + Cloudflare)。

---

## 1. 一句话背景

tools 站是"英文优先 + 完整中文版"的双语站点。工具页、首页、关于/联系/隐私页在 `/zh/` 下早有完整的静态中文版;
但 **44 个模型定价页(`models/*.html`)和定价中心(`models/index.html`)只有英文**,没有字典、没有 `/zh/` 副本,
导致切换器在这些页面上"点了没反应 / 只有页头页脚变、内容不翻"。

本次改造:**为整个价格树生成 `zh/models/` 静态中文版**,并把切换器改成指向 `/zh/` 的链接;随后修复了"切换语言后不持久、点到别的页又跳回中文"的问题。

---

## 2. 站点的语言机制(必须理解,这是全部上下文)

### 2.1 引擎

- `assets/common.js` 在每页动态注入 `assets/i18n.js`(`?v=` 版本号防 Cloudflare 缓存)。
- `assets/i18n.js` 是核心引擎:
  - `DICT_FILES`:URL 路径 → 该页要加载的翻译字典。**有静态 `/zh/` 中文版的页面都在这里登记**,没有的走按钮式切换。
  - 语言判定优先级:`URL 在 /zh/ 路径下 → zh` > `?lang= 查询参数` > `localStorage.ez-lang` > `默认 en`。
  - `?lang=zh` 只在英文 URL 上"就地翻译页头页脚",并靠 `pointCanonicalAtStaticZh` 把 canonical 指到 `/zh/` 真正的中文页(防 SEO 重复收录)。
  - 字典文件在 `assets/i18n/*.js`;引擎按 DOM 文本节点精确匹配翻译(key 就是英文原文),`el:`/`ph:`/`title:` 前缀处理富文本/占位符/标题。
- 版本号:`scripts/bump_assets.py` 统一提升全站 `?v=YYYYMMDDx`,README 有约定(改共用 JS/CSS 必须 bump)。

### 2.2 现存的页面分类

| 类别 | 页面 | 切换器形态 | 中文形态 |
|---|---|---|---|
| 有完整中文版 | 首页 `/`、about/contact/privacy、18 个工具页 | 链接 → `/zh/...` | `/zh/` 静态文件(`zh-meta.json` + `generate_zh.mjs` 生成) |
| 本轮新增中文版 | 43 个模型页 + 定价中心 | 链接 → `/zh/models/...` | `zh/models/*`(由 `generate_models.py` 生成) |
| 无中文版(兜底) | 404 页 | 按钮 + `?lang=` 深链 | 无 |

---

## 3. 原问题(逐条根因)

1. **"模型页点「中文」只有页头页脚变,内容不翻"**
   模型页 + 定价中心不在 `DICT_FILES` 里 → 没有字典、没有 `/zh/` 静态版。按钮式切换只把 `common.js` 里的公共文案(导航/页脚)翻了,`<main>` 正文(价格表、FAQ、说明)全英文。旧交互测试甚至把这个"半翻"状态当设计断言过。

2. **"有些页切换没效果"**
   按钮式切换 + `?lang=zh` + `localStorage.ez-lang=zh` 三者的组合:模型页第一下跳转后内容没变,第二下点击 URL 只重复 query、页面无任何变化;写进 localStorage 的 `zh` 还会让所有英文 URL 就地变中文。**切换选择从不写入 localStorage(链接型不写,按钮型只写自身页)**,导致跨页状态分裂。

3. **"从中文入口点进工具又变回中文"**(第二个报障)
   用户曾点过「中文」→ `localStorage.ez-lang=zh` 永久记住;点「EN」只跳到 `?lang=en` 当前页,**不写回 localStorage**;进入不带 `?lang` 的新页时,又按 localStorage 回到中文。

---

## 4. 改动详情

### 4.1 提交 `7af0d89` — Ship /zh/models/ (142 files)

1. **新增 `scripts/zh_models.py`(506 行)—— 中文文案数据层**,全部数字/日期/模型名与英文原文逐一保留:
   - `NOTES`:43 条模型 note(lead 段与定价中心"备注"列)
   - `SPEC_KEYS`(23 个规格键)+ `SPEC_VALUES`(5 个简短值,如 Supported→支持)
   - `FAQ_ZH`:10 款旗舰模型的 43 条 curated FAQ
   - `SECTIONS_ZH`:9 款模型的 21 段编辑章节
   - `TABLES_ZH`:8 款模型的 9 张成本用例表
   - **缺翻译自动回退英文,绝不破构建**(新增模型没翻译也能上线)

2. **`scripts/gen_common.py`** — 新增 `ZH_HEAD` / `ZH_CRUMBS` / `ZH_FOOT` 中文模板,结构逐一对齐现有 `/zh/` 页(`lang="zh-CN" data-zh-static`、canonical+hreflang 三件套、静态 中文/EN 切换器、`i18n.js+common.js`、`og:locale`)。

3. **`scripts/generate_models.py`** — 双语渲染:
   - 新增 `model_page_zh()` / `index_page_zh()`:同一份 `models.json` 数据渲染中英两棵树;中文页保留价格/模型名/URL,翻译周围文案标签。
   - EN 模型页 + 定价中心 `<head>` 增加 `hreflang zh-CN/en/x-default` 三件套。
   - `main()` 写入 `zh/models/*`,带字节级变更检测(不动 mtime,保持 sitemap lastmod 准确),`sitemap.xml` 纳入新树(88 → 132 条)。
   - 生成命令不变:`python scripts/generate_models.py`(一次生成 EN + ZH + models.js + sitemap)。

4. **`assets/i18n.js`** — `DICT_FILES` 增加 44 个路径(43 模型 + `/models/index.html`,值为 `[]`):
   **切换到这些页面后,`hasStaticZh` 为真 → 切换器从按钮变为链接**,直接跳到 `/zh/models/...`;`?lang=zh` 视图的 canonical 也收口到 `/zh/`。

5. **其他**:`scripts/test_interactive.mjs` 新增 `/zh/models/` 静态页断言、更新 `?lang=zh` canonical 断言;`README.md` 更新;`assets` 缓存版本 `20261029a → 20261030a`(542 处)。

### 4.2 提交 `8c4926a` — Persist the language choice (137 files)

**唯一逻辑改动在 `assets/i18n.js`**:`injectSwitcher` 重写,新增 `choiceFrom()` + `persistChoice()`:

- 链接式切换器的 `<a>` 增加 `data-lang="zh" | "en"`;
- 所有形态的切换器(`/zh/` 静态页、链接式、按钮式)点击时一律 `localStorage.setItem("ez-lang", ...)`;
- `/zh/` 静态页的硬编码切换器没有 `data-lang`,`choiceFrom` 就按 href 判定:`/^\/zh(\/|$)/` → zh,否则 en。
- **点 EN/中文即全局生效,跨页保持,除非用户再主动切换。**

版本号再提升:`20261030a → 20261030b`(全站)。

---

## 5. 当前线上状态(已部署)

- `https://tools.ezaiops.com/zh/models/index.html`(200,中文定价中心)
- `https://tools.ezaiops.com/zh/models/<id>.html`(43 页,200)
- EN 模型页 head 含 hreflang → `/zh/models/`
- 英语页切换器为链接:点「中文」跳到整页中文版
- 语言选择跨页持久,默认英文(新访客)
- `/zh/` 工具页与首页的模型链接已指向 `/zh/models/`(2026-10-30 修复)

---

## 6. 维护指南

### 6.1 改模型价格

`models.json`(唯一数据源)→ `python scripts/generate_models.py` → `python scripts/check_site.py`。
中英两棵树同时更新。**若改了共用 JS/CSS 还要 `python scripts/bump_assets.py` 再重新生成。**

### 6.2 改/加中文文案

只改 `scripts/zh_models.py` → 重新 `generate_models.py`。模型没有翻译条目时自动回退英文。

### 6.3 新增模型

1. `models.json` 加条目 → `generate_models.py` 自动产出 EN + `zh/models/<id>.html`(note 无中文翻译则英文回退);
2. `assets/i18n.js` 的 `DICT_FILES` **要手动补一行** `"/models/<id>.html": [],`(否则切换器不会变链接);
3. 可选:在 `zh_models.py` 补该模型的 note/规格翻译。

### 6.4 删除模型

`generate_models.py` 会自动清理 EN 与 `zh/models/` 下的孤儿页(有 pruned 逻辑)。

### 6.5 其它注意

- 给 `/zh/` 工具页加新中文页走老流程:`zh-meta.json` + `node scripts/generate_zh.mjs`(**需作者机器上的 jsdom**),与模型页机制不同,别混。
- 模型中文页是 Python 直接渲染的静态页(`data-zh-static`),不带运行时字典;`i18n.js` 在 `/zh/models/` 上只做 `finish(0)`,不会再去翻译。

---

## 7. 验证

- 静态:`python scripts/check_site.py`(现 133 页全过,sitemap 132 条)
- 交互:`node scripts/test_interactive.mjs` —— **354 项全过**(2026-10-30 在作者 Windows 机器实跑;jsdom 位于 `C:/Users/june_/.workbuddy-ai/binaries/node/workspace/`)。跑之前必须先起本地服务 `python -m http.server 8901`,否则 jsdom 加载不到页面会直接抛 ECONNREFUSED。
- 浏览器手动清单:
  - 英文页点工具/模型 → 全英文;点「中文」→ 整页中文;再点工具/模型 → 全中文
  - `/zh/models/index.html` 行内链接 → `/zh/models/*`,点「EN」→ 英文页
  - 刷新/换页后语言不跳变;控制台 `localStorage.removeItem("ez-lang")` 模拟新访客(默认英文)

---

## 8. 回滚

两个提交可独立回退:

```bash
git revert 8c4926a   # 语言持久化 —— 若想保留中文版、恢复"点了不持久"
git revert 7af0d89   # 整套 zh/models 中文版(会同时还原 i18n.js 的 DICT_FILES 与 EN hreflang)
git push origin main
```

注意:`7af0d89` 之后全站资源版本号已推进为 `20261030b`,回退提交不会自动还原版本号,如需彻底还原请自行处理 `?v=`(不还原也不影响功能,只是多一次缓存刷新)。

---

## 9. 遗留 / 已知项

- ~~`/zh/` 工具页与首页的模型链接指向英文树~~ —— **已修复(2026-10-30 状态同步时)**。`scripts/generate_zh.mjs` 的 `rewriteLinks()` 增加 `/models/` → `/zh/models/` 规则,22 个中文页的页脚「模型价格」和首页模型卡片现在全部指向中文定价树;对应交互断言也从「保持英文树」反转为「路由到中文树」。
- 404 页仍是按钮式切换(无静态中文版,保持现状)。
- `scripts/generate_zh.mjs` 依赖 jsdom,执行环境只有作者机器;接手方如要重生成 `/zh/` 工具页,需要自行准备 jsdom 环境或改写成能跑的路径。

## 10. 姊妹仓库提醒

- **blogpages 站(ezaiops.com)另有 `blogpages/HANDOVER.md`**,记录 ads.txt / robots.txt / Cloudflare 运维要点(Bot Preference Sync 启用曾导致 Google 报"找不到 ads.txt",详见该文档)。
- 两个域名共用同一 AdSense publisher ID,但 **`ads.txt` 按域名独立读取**:`tools/HANDOVER.md` 所在仓库根目录的 `ads.txt` 与 `blogpages/docs/ads.txt` 必须同步维护。

---

*记录时间:2026-10-30;同日状态同步(补记交互测试结果、关闭模型链接遗留项)。`main` 的最新提交以 `git log -1 -- HANDOVER.md` 为准 —— 写死 commit 号必然落后一个提交。*