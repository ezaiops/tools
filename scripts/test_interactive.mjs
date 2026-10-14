// Interactive DOM tests for tools.ezaiops.com using jsdom.
// Run: node scripts/test_interactive.mjs   (with the local http server on :8901)
import { createRequire } from "module";
import { readFileSync } from "fs";

const require = createRequire("C:/Users/june_/.workbuddy-ai/binaries/node/workspace/");
const { JSDOM, VirtualConsole } = require("jsdom");

const manifest = JSON.parse(readFileSync(new URL("./tools.json", import.meta.url), "utf8"));
const liveN = manifest.tools.filter((t) => (t.status || "live") === "live").length;
const plannedN = manifest.tools.filter((t) => t.status === "planned").length;

const BASE = "http://127.0.0.1:8901";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OPEN_DOMS = [];

let passed = 0;
let failed = 0;
function check(label, cond, extra) {
  if (cond) { passed++; console.log("  ok   " + label); }
  else { failed++; console.log("  FAIL " + label + (extra ? " -- " + extra : "")); }
}

async function load(rel) {
  const errors = [];
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => {
    const s = String((e && e.message) || e);
    if (/dynamic import|Could not load|not implemented|css|stylesheet/i.test(s)) return;
    errors.push(s);
  });
  vc.on("error", (...a) => errors.push(a.map(String).join(" ")));
  const dom = await JSDOM.fromURL(BASE + "/" + rel, {
    runScripts: "dangerously",
    resources: "usable",
    pretendToBeVisual: true,
    virtualConsole: vc,
  });
  await new Promise((resolve) => {
    const t = setTimeout(resolve, 6000);
    dom.window.addEventListener("load", () => { clearTimeout(t); resolve(); }, { once: true });
  });
  await sleep(200);
  OPEN_DOMS.push(dom);
  return { dom, win: dom.window, doc: dom.window.document, errors };
}

function setInput(win, el, value) {
  el.value = value;
  el.dispatchEvent(new win.Event("input", { bubbles: true }));
}
function mcBatchOn(win, doc) {
  const el = $("#mc-batch", doc);
  el.checked = true;
  el.dispatchEvent(new win.Event("change", { bubbles: true }));
}
function mcBatchOff(win, doc) {
  const el = $("#mc-batch", doc);
  el.checked = false;
  el.dispatchEvent(new win.Event("change", { bubbles: true }));
}
function mcCache(win, doc, pct) {
  const el = $("#mc-cache", doc);
  el.value = String(pct);
  el.dispatchEvent(new win.Event("input", { bubbles: true }));
}
function click(win, el) {
  el.dispatchEvent(new win.MouseEvent("click", { bubbles: true }));
}
function $(a, b) {
  const sel = typeof a === "string" ? a : b;
  const doc = typeof a === "string" ? b : a;
  return doc.querySelector(sel);
}
function $$(a, b) {
  const sel = typeof a === "string" ? a : b;
  const doc = typeof a === "string" ? b : a;
  return Array.from(doc.querySelectorAll(sel));
}
console.log("\n== index.html ==");
{
  const { doc, errors } = await load("index.html");
  check("title set", /ezaiops tools/.test(doc.title), doc.title);
  check("hub renders every live tool", $$(doc, '.tool-grid a.tool-card-item[href^="/tools/"]').length === liveN,
    $$(doc, '.tool-grid a.tool-card-item[href^="/tools/"]').length + " vs " + liveN);
  check("roadmap cards", $$(doc, "#roadmap .tool-card-item").length === plannedN,
    $$(doc, "#roadmap .tool-card-item").length + " vs " + plannedN);
  check("planned cards are not links", $$(doc, "#roadmap a.tool-card-item").length === 0);
  check("model hub linked", $$(doc, 'a[href="/models/index.html"]').length >= 2);
  check("footer year rendered", /\d{4}/.test($(doc, "[data-year]").textContent));
  check("main site banner", $$(doc, "a.main-site-banner, .main-site-banner a").length >= 1);
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== token-counter.html ==");
{
  const { win, doc, errors } = await load("tools/token-counter.html");
  const opts = $$(doc, "#tc-model option");
  check("29 models in selector", opts.length === 29, String(opts.length));
  check("provider groups", $$(doc, "#tc-model optgroup").length === 10);
  setInput(win, $("#tc-input", doc), "hello world");
  await sleep(500);
  check("chars counted", $("#tc-chars", doc).textContent === "11", $("#tc-chars", doc).textContent);
  check("words counted", $("#tc-words", doc).textContent === "2");
  check("tokens numeric", /^\d+$/.test($("#tc-tokens", doc).textContent.replace(/,/g, "")), $("#tc-tokens", doc).textContent);
  check("tokenizer badge honest", /tokenizer/i.test($("#tc-token-mode", doc).textContent));
  setInput(win, $("#tc-output-tokens", doc), "0");
  await sleep(300);
  check("cost prefix $", /^\$/.test($("#tc-cost", doc).textContent), $("#tc-cost", doc).textContent);
  check("per-1k cost $", /^\$/.test($("#tc-cost-1k", doc).textContent));
  const rows = $$(doc, "#tc-compare-body tr");
  check("compare table has 8 rows", rows.length === 8, String(rows.length));
  check("compare sorted asc", /GPT-6 Luna/.test(rows[0].textContent), rows[0].textContent.slice(0, 60));
  click(win, $("#tc-sample", doc));
  await sleep(400);
  check("sample loads tokens", Number($("#tc-tokens", doc).textContent.replace(/,/g, "")) > 50);
  click(win, $("#tc-clear", doc));
  await sleep(300);
  check("clear zeroes tokens", $("#tc-tokens", doc).textContent === "0");
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== token-counter monthly projection ==");
{
  const { win, doc } = await load("tools/token-counter.html");
  const sel = (v) => {
    const el = $("#tc-model", doc);
    el.value = v;
    el.dispatchEvent(new win.Event("change", { bubbles: true }));
  };
  setInput(win, $("#mc-in", doc), "1500");
  setInput(win, $("#mc-out", doc), "500");
  setInput(win, $("#mc-req", doc), "10000");
  mcBatchOff(win, doc);
  mcCache(win, doc, 0);
  sel("claude-sonnet-5-5");
  await sleep(250);
  check("monthly per request", $("#mc-cost-req", doc).textContent === "$0.008000", $("#mc-cost-req", doc).textContent);
  check("monthly total", $("#mc-cost-month", doc).textContent === "$2400.00", $("#mc-cost-month", doc).textContent);
  check("monthly rows 29", $$(doc, "#mc-rows tr").length === 29, String($$(doc, "#mc-rows tr").length));
  check("cheapest row first", /DeepSeek V4-Flash|MiMo V2.6 Flash/.test($$(doc, "#mc-rows tr")[0].textContent) &&
    /\$0\.000350/.test($$(doc, "#mc-rows tr")[0].textContent),
    $$(doc, "#mc-rows tr")[0].textContent.slice(0, 60));

  sel("deepseek-v4-1-flash");
  await sleep(250);
  check("time pricing live badge", /Off-peak|Peak/.test($("#tc-sel-time", doc).textContent), $("#tc-sel-time", doc).textContent);
  check("monthly time note visible", !$("#mc-time-note", doc).classList.contains("hidden"));
  check("monthly time note range", /off-peak/.test($("#mc-time-note", doc).textContent) && /peak/.test($("#mc-time-note", doc).textContent),
    $("#mc-time-note", doc).textContent);
  sel("claude-sonnet-5-5");

  mcBatchOn(win, doc);
  await sleep(250);
  check("batch halves cost", /^\$0\.004/.test($("#mc-cost-req", doc).textContent), $("#mc-cost-req", doc).textContent);
  mcBatchOff(win, doc);

  sel("gpt-6-1-sol");
  setInput(win, $("#mc-in", doc), "1000");
  setInput(win, $("#mc-out", doc), "0");
  mcCache(win, doc, 50);
  await sleep(250);
  check("cache mix math", $("#mc-cost-req", doc).textContent === "$0.001050", $("#mc-cost-req", doc).textContent);
  mcCache(win, doc, 0);

  sel("gpt-6-astra");
  setInput(win, $("#mc-in", doc), "300000");
  await sleep(250);
  check("long-context tier warning", !$("#mc-warn", doc).classList.contains("hidden"));
  check("tier rate applied", $("#mc-cost-req", doc).textContent === "$6.00", $("#mc-cost-req", doc).textContent);
  setInput(win, $("#mc-in", doc), "1500");

  click(win, $('[data-preset="rag"]', doc));
  check("RAG preset fills", $("#mc-in", doc).value === "3000" && $("#mc-req", doc).value === "5000",
    $("#mc-in", doc).value + "/" + $("#mc-req", doc).value);

  click(win, $("#mc-from-text", doc));
  check("sync from text", $("#mc-in", doc).value === String(Number($("#tc-tokens", doc).textContent.replace(/,/g, ""))),
    $("#mc-in", doc).value + " vs " + $("#tc-tokens", doc).textContent);

  click(win, $("#mc-share", doc));
  check("share url built", /m=gpt-6-astra/.test($("#mc-share-url", doc).value), $("#mc-share-url", doc).value);
  check("share url in address bar", /m=gpt-6-astra/.test(win.location.search), win.location.search);
}

console.log("\n== token-counter share link prefill ==");
{
  const { doc } = await load("tools/token-counter.html?m=gpt-6-1-sol&i=2000&o=300&r=500&b=1&c=50");
  check("prefill model", $("#tc-model", doc).value === "gpt-6-1-sol", $("#tc-model", doc).value);
  check("prefill tokens", $("#mc-in", doc).value === "2000");
  check("prefill volume", $("#mc-req", doc).value === "500");
  check("prefill batch", $("#mc-batch", doc).checked === true);
  check("prefill cache", $("#mc-cache", doc).value === "50");
  check("prefill cost", $("#mc-cost-req", doc).textContent === "$0.002600", $("#mc-cost-req", doc).textContent);
  check("prefill monthly", $("#mc-cost-month", doc).textContent === "$39.00", $("#mc-cost-month", doc).textContent);
}

console.log("\n== bilingual mode (?lang=zh) ==");
{
  const { doc, errors } = await load("tools/token-counter.html?lang=zh");
  await sleep(400);
  check("html lang is zh-CN", doc.documentElement.getAttribute("lang") === "zh-CN",
    String(doc.documentElement.getAttribute("lang")));
  check("switcher injected", doc.querySelector(".lang-switch") !== null);
  check("switcher marks zh active", /active/.test(doc.querySelector('.lang-switch a[data-lang="zh"]').className || ""));
  check("nav translated", /工具/.test(doc.querySelector(".site-nav").textContent));
  check("footer translated", /无需注册|本地运行/.test(doc.querySelector(".site-footer").textContent));
  check("h1 translated", /成本计算器/.test($("h1", doc).textContent), $("h1", doc).textContent);
  check("field label translated", /Prompt 或文本/.test(doc.querySelector('label[for="tc-input"]').textContent));
  check("placeholder translated", doc.querySelector("#mc-share-url") !== null);
  check("dynamic badge translated", /分词器/.test($("#tc-token-mode", doc).textContent), $("#tc-token-mode", doc).textContent);
  check("stats translated", /单次请求预估成本/.test(doc.body.textContent));
  check("monthly section translated", /月度成本投射/.test(doc.body.textContent));
  check("faq translated", /常见问题/.test(doc.body.textContent));
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== bilingual: dynamic strings ==");
{
  const { win, doc } = await load("tools/timestamp-converter.html?lang=zh");
  await sleep(400);
  setInput(win, $("#ts-input", doc), "0");
  check("relative time zh", /年前/.test($("#ts-rel", doc).textContent), $("#ts-rel", doc).textContent);
  check("kv labels zh", /本地时间/.test(doc.body.textContent));
  check("lead zh", /互转/.test(doc.body.textContent));

  const pw = await load("tools/password-generator.html?lang=zh");
  await sleep(400);
  check("strength line zh", /位/.test($("#pw-strength", pw.doc).textContent), $("#pw-strength", pw.doc).textContent);
  check("tabs zh", /密码/.test(pw.doc.body.textContent));
}

console.log("\n== bilingual: model pages keep data in EN, chrome in ZH ==");
{
  const { doc } = await load("models/gpt-6-astra.html?lang=zh");
  await sleep(400);
  check("model nav translated", /工具/.test(doc.querySelector(".site-nav").textContent));
  check("model h1 stays EN", /GPT-6 Astra API pricing/.test($("h1", doc).textContent));
  check("crumb crumb main-site link kept", doc.querySelector(".main-site-link") !== null);
}

console.log("\n== json-formatter.html ==");
{
  const { win, doc, errors } = await load("tools/json-formatter.html");
  setInput(win, $("#jf-input", doc), '{"b":1,"a":[1,2]}');
  click(win, $("#jf-format", doc));
  check("format indents", /\n    "a"/.test($("#jf-out", doc).textContent), $("#jf-out", doc).textContent);
  check("format meta stats", /bytes/.test($("#jf-meta", doc).textContent), $("#jf-meta", doc).textContent);
  check("keys counted", /2 keys/.test($("#jf-meta", doc).textContent), $("#jf-meta", doc).textContent);
  click(win, $("#jf-minify", doc));
  check("minify", $("#jf-out", doc).textContent === '{"b":1,"a":[1,2]}', $("#jf-out", doc).textContent);
  setInput(win, $("#jf-input", doc), '{"bad":}');
  click(win, $("#jf-validate", doc));
  check("error visible", !$("#jf-err", doc).classList.contains("hidden"));
  check("error has line/col", /line \d+, column \d+/.test($("#jf-err", doc).textContent), $("#jf-err", doc).textContent);
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== regex-tester.html ==");
{
  const { win, doc, errors } = await load("tools/regex-tester.html");
  check("auto-run matches", $("#rt-count", doc).textContent === "2", $("#rt-count", doc).textContent);
  check("highlight marks", /<mark>/.test($("#rt-highlight", doc).innerHTML));
  setInput(win, $("#rt-pattern", doc), "(\\w+@\\w+\\.\\w+)");
  await sleep(50);
  check("replacement preview", $("#rt-replace-out", doc).textContent ===
    "Ping me at [ops@ezaiops.com] or backup+[alerts@ezaiops.io].\nNot-an-email: broken@, @missing, spaces in@address.",
    JSON.stringify($("#rt-replace-out", doc).textContent));
  check("groups table rows", $$(doc, "#rt-rows tr").length === 2);
  setInput(win, $("#rt-pattern", doc), "[");
  check("invalid regex error", !$("#rt-err", doc).classList.contains("hidden"));
  setInput(win, $("#rt-pattern", doc), "(\\w+)@(\\w+)");
  await sleep(100);
  check("capture groups counted", Number($("#rt-groups", doc).textContent) >= 4, $("#rt-groups", doc).textContent);
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== cron-explainer.html ==");
{
  const { win, doc, errors } = await load("tools/cron-explainer.html");
  check("desc has time", /09:00/.test($("#ce-desc", doc).textContent), $("#ce-desc", doc).textContent);
  check("desc has weekday", /Monday/.test($("#ce-desc", doc).textContent));
  check("10 next runs", $$(doc, "#ce-runs li").length === 10);
  check("field table rows", $$(doc, "#ce-fields tr").length === 5);
  click(win, $('[data-cron="*/5 * * * *"]', doc));
  check("step description", /every 5 minutes/.test($("#ce-desc", doc).textContent), $("#ce-desc", doc).textContent);
  click(win, $('[data-cron="@daily"]', doc));
  check("special string", /00:00/.test($("#ce-desc", doc).textContent));
  setInput(win, $("#ce-expr", doc), "99 * * * *");
  click(win, $("#ce-explain", doc));
  check("range error", /out of range/.test($("#ce-err", doc).textContent), $("#ce-err", doc).textContent);
  setInput(win, $("#ce-expr", doc), "0 0 29 2 *");
  click(win, $("#ce-explain", doc));
  check("leap-day schedule", /February/.test($("#ce-desc", doc).textContent), $("#ce-desc", doc).textContent);
  check("feb29 has next runs", $$(doc, "#ce-runs li").length === 10);
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== encode-decode.html ==");
{
  const { win, doc, errors } = await load("tools/encode-decode.html");
  setInput(win, $("#ed-input", doc), "hi");
  click(win, $("#ed-b64-enc", doc));
  check("base64 encode", $("#ed-output", doc).value === "aGk=", $("#ed-output", doc).value);
  click(win, $("#ed-swap", doc));
  click(win, $("#ed-b64-dec", doc));
  check("base64 decode round trip", $("#ed-output", doc).value === "hi", $("#ed-output", doc).value);
  setInput(win, $("#ed-input", doc), "a b&c");
  click(win, $('[data-tab="url"]', doc));
  click(win, $("#ed-url-enc", doc));
  check("url encode", $("#ed-output", doc).value === "a%20b%26c", $("#ed-output", doc).value);
  setInput(win, $("#ed-input", doc), "hi");
  click(win, $('[data-tab="hash"]', doc));
  click(win, $("#ed-hash-run", doc));
  await sleep(400);
  check("sha256 pure js", $("#ed-output", doc).value === "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
    $("#ed-output", doc).value);
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== timestamp-converter.html ==");
{
  const { win, doc, errors } = await load("tools/timestamp-converter.html");
  check("live clock ticks", /^\d{10}$/.test($("#ts-now-s", doc).textContent), $("#ts-now-s", doc).textContent);
  setInput(win, $("#ts-input", doc), "0");
  check("epoch iso", $("#ts-iso", doc).textContent === "1970-01-01T00:00:00Z", $("#ts-iso", doc).textContent);
  check("epoch rfc", /Thu, 01 Jan 1970/.test($("#ts-rfc", doc).textContent));
  setInput(win, $("#ts-input", doc), "1000000000");
  check("ms vs s detect", $("#ts-detected", doc).textContent === "unix s");
  check("2001 iso", $("#ts-iso", doc).textContent === "2001-09-09T01:46:40Z", $("#ts-iso", doc).textContent);
  setInput(win, $("#ts-input", doc), "1735689600000");
  check("ms detect", $("#ts-detected", doc).textContent === "unix ms");
  check("2025 iso", /^2025-01-01T/.test($("#ts-iso", doc).textContent), $("#ts-iso", doc).textContent);
  setInput(win, $("#ts-input", doc), "now");
  check("now keyword", $("#ts-detected", doc).textContent === "now");
  setInput(win, $("#ts-input", doc), "not a date");
  check("bad input dashed", $("#ts-iso", doc).textContent === "—");
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== password-generator.html ==");
{
  const { win, doc, errors } = await load("tools/password-generator.html");
  const pw = $("#pw-out", doc).value.trim();
  check("default length 20", pw.length === 20, pw);
  check("printable ascii only", /^[\x21-\x7e]{20}$/.test(pw), pw);
  check("entropy shown", /bits/.test($("#pw-strength", doc).textContent), $("#pw-strength", doc).textContent);
  check("strength bar width", /%/.test($("#pw-bar", doc).style.width));
  setInput(win, $("#pw-len", doc), "32");
  click(win, $("#pw-gen", doc));
  check("regen length 32", $("#pw-out", doc).value.trim().length === 32);
  click(win, $('[data-pwtab="pass"]', doc));
  click(win, $("#pp-gen", doc));
  check("passphrase shape", /^[A-Z][a-z]+-[A-Z][a-z]+/.test($("#pp-out", doc).value), $("#pp-out", doc).value);
  check("passphrase entropy", /\d+ bits/.test($("#pp-strength", doc).textContent));
  click(win, $('[data-pwtab="uuid"]', doc));
  click(win, $("#uuid-gen", doc));
  const uuids = $("#uuid-out", doc).value.trim().split("\n");
  check("one uuid by default", uuids.length === 1);
  check("uuid v4 shape", /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(uuids[0]), uuids[0]);
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== meta-tag-generator.html ==");
{
  const { win, doc, errors } = await load("tools/meta-tag-generator.html");
  const code = $("#mt-code", doc).value;
  check("title tag", /<title>ezaiops tools/.test(code));
  check("og tags", /property="og:title"/.test(code) && /property="og:site_name"/.test(code));
  check("twitter card", /name="twitter:card" content="summary"/.test(code));
  check("canonical", /rel="canonical" href="https:\/\/tools.ezaiops.com\/"/.test(code));
  setInput(win, $("#mt-image", doc), "https://example.com/img.png");
  check("large image card", /summary_large_image/.test($("#mt-code", doc).value));
  setInput(win, $("#mt-title", doc), "x".repeat(70));
  check("title counter amber", $("#mt-title-count", doc).className.includes("amber"), $("#mt-title-count", doc).textContent);
  check("serp warning", /truncated/.test($("#mt-serp-note", doc).textContent));
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== models/claude-opus-5.html ==");
{
  const { doc, errors } = await load("models/claude-opus-5.html");
  check("h1 has model", /Claude Opus 5 API pricing/.test($("h1", doc).textContent), $("h1", doc).textContent);
  check("price in lead", /\$5 per 1M input/.test($(".lead", doc).textContent), $(".lead", doc).textContent.slice(0, 120));
  check("calc default", $("#mc-cost", doc).textContent === "$7.50", $("#mc-cost", doc).textContent);
  check("calc x1000", $("#mc-1k", doc).textContent === "$7500.00", $("#mc-1k", doc).textContent);
  check("neighbors 5 rows", $$(doc, ".data tbody tr").length >= 5);
  check("faq present", $$(doc, "details.faq").length === 3);
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== models/deepseek-v4-1-flash.html ==");
{
  const { doc } = await load("models/deepseek-v4-1-flash.html");
  check("off-peak row", /Off-peak rate \(default\)/.test(doc.body.textContent));
  check("peak window row", /Weekday peak \(UTC 01:00-04:00 and 06:00-10:00\)/.test(doc.body.textContent));
  check("peak prices shown", /\$0\.30/.test(doc.body.textContent) && /\$1\.20/.test(doc.body.textContent));
  check("lead marks off-peak", /\(off-peak\)/.test($(".lead", doc).textContent), $(".lead", doc).textContent.slice(0, 100));
}

console.log("\n== models/index.html ==");
{
  const { doc, errors } = await load("models/index.html");
  check("29 rows", $$(doc, "table.data tbody tr").length === 29, String($$(doc, "table.data tbody tr").length));
  check("links to model pages", $$(doc, 'a[href^="/models/"]').length >= 29);
  check("sources listed", $$(doc, ".prose ul li").length === 10, String($$(doc, ".prose ul li").length));
  check("main site link in crumbs", $$(doc, ".main-site-link").length === 1);
  check("main site banner", $$(doc, ".main-site-banner a").length >= 1);
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n" + (failed === 0 ? "ALL " + passed + " CHECKS PASSED" : passed + " passed, " + failed + " FAILED"));
OPEN_DOMS.forEach((d) => { try { d.window.close(); } catch (e) { /* already closed */ } });
setTimeout(() => process.exit(failed === 0 ? 0 : 1), 100).unref();
