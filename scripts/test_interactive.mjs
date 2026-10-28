// Interactive DOM tests for tools.ezaiops.com using jsdom.
// Run: node scripts/test_interactive.mjs   (with the local http server on :8901)
import { createRequire } from "module";
import { readFileSync, readdirSync } from "fs";

const require = createRequire("C:/Users/june_/.workbuddy-ai/binaries/node/workspace/");
const { JSDOM, VirtualConsole } = require("jsdom");

const manifest = JSON.parse(readFileSync(new URL("./tools.json", import.meta.url), "utf8"));
const liveN = manifest.tools.filter((t) => (t.status || "live") === "live").length;
const plannedN = manifest.tools.filter((t) => t.status === "planned").length;
// Read the live model count instead of hardcoding it, so adding a model does not
// require touching every assertion.
const modelData = JSON.parse(readFileSync(new URL("./models.json", import.meta.url), "utf8"));
const modelN = modelData.models.length;

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
  const { win, doc, errors } = await load("index.html");
  check("title set", /ezaiops tools/.test(doc.title), doc.title);
  check("hub renders every live tool", $$(doc, '.tool-grid a.tool-card-item[href^="/tools/"]').length === liveN,
    $$(doc, '.tool-grid a.tool-card-item[href^="/tools/"]').length + " vs " + liveN);
  check("tools are grouped", $$(doc, "#tool-groups .tool-group").length >= 4,
    String($$(doc, "#tool-groups .tool-group").length));
  check("every card has an inline icon", $$(doc, "#tool-groups .tool-card-item .tool-icon svg").length === liveN,
    String($$(doc, "#tool-groups .tool-card-item .tool-icon svg").length));
  check("no leaked taxonomy badges on cards", $$(doc, "#tool-groups .tool-card-item .badge").length === 0);
  check("model hub linked", $$(doc, 'a[href="/models/index.html"]').length >= 2);
  check("footer year rendered", /\d{4}/.test($(doc, "[data-year]").textContent));
  check("hub links to the blog", $$(doc, 'a[href^="https://ezaiops.com"]').length >= 1);

  const search = $("#tool-search", doc);
  check("search box present", !!search);
  search.value = "cron";
  search.dispatchEvent(new win.Event("input", { bubbles: true }));
  await sleep(80);
  const visible = $$(doc, "#tool-groups .tool-card-item:not([hidden])");
  check("search narrows to cron tools", visible.length === 2, String(visible.length));
  check("empty groups hidden", $$(doc, "#tool-groups .tool-group:not([hidden])").length === 1,
    String($$(doc, "#tool-groups .tool-group:not([hidden])").length));
  search.value = "zzzz";
  search.dispatchEvent(new win.Event("input", { bubbles: true }));
  await sleep(80);
  check("no-match message shown", !$("#search-empty", doc).hidden);
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== token-counter.html ==");
{
  const { win, doc, errors } = await load("tools/token-counter.html");
  const opts = $$(doc, "#tc-model option");
  check("model selector matches data", opts.length === modelN, String(opts.length));
  // Derive from the data so adding a provider does not silently break this.
  const providerN = new Set(modelData.models.map((m) => m.provider)).size;
  check("provider groups", $$(doc, "#tc-model optgroup").length === providerN,
    String($$(doc, "#tc-model optgroup").length) + " vs " + providerN);
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
  check("monthly rows = model count", $$(doc, "#mc-rows tr").length === modelN, String($$(doc, "#mc-rows tr").length));
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
  check("switcher marks zh active", /active/.test((doc.querySelector('.lang-switch [data-lang="zh"]') || {}).className || ""));
  check("switcher emits no crawlable ?lang= link", doc.querySelector('.lang-switch a[href*="lang="]') === null);
  check("nav translated", /工具/.test(doc.querySelector(".site-nav").textContent));
  check("footer translated", /输入内容|不会离开/.test(doc.querySelector(".site-footer").textContent));
  check("brand label translated", /工具/.test(doc.querySelector(".brand").textContent),
    doc.querySelector(".brand").textContent);
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

console.log("\n== cron-generator.html ==");
{
  const { win, doc } = await load("tools/cron-generator.html");
  check("default expression every minute", $("#cg-expr", doc).value === "* * * * *", $("#cg-expr", doc).value);
  check("5 next runs listed", $$(doc, "#cg-runs li").length === 5);
  check("per-period stat set", /43,200/.test($("#cg-perday", doc).textContent), $("#cg-perday", doc).textContent);
  click(win, $('[data-cg-preset="weekday"]', doc));
  check("weekday preset expr", $("#cg-expr", doc).value === "0 9 * * 1-5", $("#cg-expr", doc).value);
  click(win, $('[data-cg-preset="monthly"]', doc));
  check("monthly preset expr", $("#cg-expr", doc).value === "0 6 1 * *", $("#cg-expr", doc).value);
  click(win, $('[data-cg-preset="health"]', doc));
  $("#cg-minute", doc).value = "custom";
  $("#cg-minute", doc).dispatchEvent(new win.Event("change", { bubbles: true }));
  check("custom row visible", !$("#cg-custom-row", doc).classList.contains("hidden"));
  setInput(win, $("#cg-custom", doc), "99");
  check("custom value rejected", !$("#cg-err", doc).classList.contains("hidden"), $("#cg-err", doc).textContent);
  check("expr cleared on invalid", $("#cg-expr", doc).value === "—", $("#cg-expr", doc).value);
  setInput(win, $("#cg-custom", doc), "*/0");
  check("step zero rejected", !$("#cg-err", doc).classList.contains("hidden"), $("#cg-err", doc).textContent);
  check("step zero not in expr", $("#cg-expr", doc).value === "—");
  setInput(win, $("#cg-custom", doc), "5");
  check("custom value accepted", $("#cg-expr", doc).value === "5 * * * *", $("#cg-expr", doc).value);
  setInput(win, $("#cg-custom", doc), "1-5/2");
  await sleep(120);
  check("range+step honoured in count", $("#cg-perday", doc).textContent === "2,160", $("#cg-perday", doc).textContent);
  const runMins = $$(doc, "#cg-runs li").map((li) => (li.textContent.match(/\d\d:(\d\d)/) || [])[1]).join(",");
  check("range+step run minutes", /^(01|03|05)(,(01|03|05))*$/.test(runMins), runMins);
  setInput(win, $("#cg-custom", doc), "5-1");
  check("descending range rejected", !$("#cg-err", doc).classList.contains("hidden"), $("#cg-err", doc).textContent);
}

console.log("\n== subnet-calculator.html ==");
{
  const { win, doc } = await load("tools/subnet-calculator.html");
  const txt = $("#sn-results", doc).textContent;
  check("network address", /192\.168\.1\.0\/26/.test(txt), txt.slice(0, 120));
  check("broadcast address", /192\.168\.1\.63/.test(txt));
  check("usable host range", /192\.168\.1\.1 – 192\.168\.1\.62/.test(txt));
  check("usable hosts 62", /62/.test(txt));
  check("mask shown", /255\.255\.255\.192/.test(txt));
  check("binary rows", $$(doc, "#sn-binary tr").length === 3);
  check("prefix table 7 rows", $$(doc, "#sn-table tr").length === 7);
  setInput(win, $("#sn-input", doc), "999.1.1.1/24");
  click(win, $("#sn-calc", doc));
  check("invalid address error", !$("#sn-err", doc).classList.contains("hidden"));
  click(win, $('[data-sn="203.0.113.42/30"]', doc));
  const t2 = $("#sn-results", doc).textContent;
  check("/30 point-to-point", /203\.0\.113\.40\/30/.test(t2) && /Usable hosts2/.test(t2), t2.slice(0, 100));
}

console.log("\n== self-host-vs-api.html ==");
{
  const { win, doc } = await load("tools/self-host-vs-api.html");
  const opts = $$(doc, "#sh-model option");
  check("model selector populated", opts.length === modelN, String(opts.length));
  check("api cost $30,000", $("#sh-api-cost", doc).textContent === "$30,000", $("#sh-api-cost", doc).textContent);
  check("gpu fixed cost $252.00 (24x7 @ $0.35)", $("#sh-gpu-cost", doc).textContent === "$252.00", $("#sh-gpu-cost", doc).textContent);
  check("verdict self-host", /Self-hosting|自托管/.test($("#sh-verdict", doc).textContent), $("#sh-verdict", doc).textContent);
  check("breakeven any volume", /Any volume/.test($("#sh-breakeven", doc).textContent), $("#sh-breakeven", doc).textContent);
  check("note explains", /saves/.test($("#sh-note", doc).textContent));
  check("no capacity warning at low volume", $("#sh-cap-warn", doc).classList.contains("hidden"));
  setInput(win, $("#sh-out", doc), "50000000000");
  await sleep(300);
  check("multi-GPU capacity warning", !$("#sh-cap-warn", doc).classList.contains("hidden"));
  check("multi-GPU cost scaled", $("#sh-gpu-cost", doc).textContent === "$1,764", $("#sh-gpu-cost", doc).textContent);
}

console.log("\n== mortgage-calculator.html ==");
{
  const { win, doc } = await load("tools/mortgage-calculator.html");
  check("US default is 400k @ 7.4%", $("#mo-amount", doc).value === "400000" && $("#mo-rate", doc).value === "7.4");
  check("monthly payment $2,769.52", /^\$2,769\.52$/.test($("#mo-payment", doc).textContent), $("#mo-payment", doc).textContent);
  check("no provident-fund selector in English", $("#mo-type-field", doc).hidden === true);
  check("total interest set", /^\$/.test($("#mo-interest", doc).textContent), $("#mo-interest", doc).textContent);
  check("payoff 30 years", /30 years/.test($("#mo-payoff", doc).textContent), $("#mo-payoff", doc).textContent);
  check("12 amortization rows", $$(doc, "#mo-rows tr").length === 12);
  check("5 columns now", $$(doc, "#mo-rows tr")[0] && $$(doc, "#mo-rows tr")[0].querySelectorAll("td").length === 5);
  check("extra stats hidden by default", $("#mo-extra-stats", doc).style.display === "none");
  check("final-payment stat hidden in installment mode", $("#mo-last-stat", doc).style.display === "none");
  setInput(win, $("#mo-extra", doc), "200");
  await sleep(250);
  check("extra stats appear", $("#mo-extra-stats", doc).style.display !== "none");
  check("interest saved positive", /^\$[\d,]+\.\d\d$/.test($("#mo-saved", doc).textContent), $("#mo-saved", doc).textContent);
  check("time saved positive", /\d/.test($("#mo-timesaved", doc).textContent), $("#mo-timesaved", doc).textContent);
  setInput(win, $("#mo-extra", doc), "0");

  // switch to equal principal
  const method = $("#mo-method", doc);
  method.value = "principal";
  method.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(250);
  check("first payment label", /First payment/.test($("#mo-payment-label", doc).textContent), $("#mo-payment-label", doc).textContent);
  check("final payment stat visible", $("#mo-last-stat", doc).style.display !== "none");
  const first = parseFloat($("#mo-payment", doc).textContent.replace(/[$,]/g, ""));
  const last = parseFloat($("#mo-last", doc).textContent.replace(/[$,]/g, ""));
  check("equal principal declines", first > last, first + " vs " + last);
  check("equal principal total interest lower", true); // covered by decline check
  method.value = "installment";
  method.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(250);
  check("payoff date rendered", /^[A-Z][a-z]{2} \d{4}$/.test($("#mo-payoff-date", doc).textContent), $("#mo-payoff-date", doc).textContent);
  setInput(win, $("#mo-rate", doc), "0");
  setInput(win, $("#mo-years", doc), "1");
  setInput(win, $("#mo-amount", doc), "12000");
  setInput(win, $("#mo-extra", doc), "11000");
  await sleep(250);
  check("singular month label", /1 month/.test($("#mo-payoff", doc).textContent), $("#mo-payoff", doc).textContent);
}

console.log("\n== mortgage bilingual currency ==");
{
  const { doc } = await load("tools/mortgage-calculator.html?lang=zh");
  await sleep(400);
  check("zh uses RMB symbol", /^¥/.test($("#mo-payment", doc).textContent), $("#mo-payment", doc).textContent);
  check("zh prefix symbol", $$(doc, ".mo-cur").every((el) => el.textContent === "¥"));
  check("zh method options", /等额本息/.test($("#mo-method", doc).textContent));
  check("zh defaults to 100万 @ 3.2%", $("#mo-amount", doc).value === "1000000" && $("#mo-rate", doc).value === "3.2",
    $("#mo-amount", doc).value + " / " + $("#mo-rate", doc).value);
  check("commercial payment ¥4,324.67", /^¥4,324\.67$/.test($("#mo-payment", doc).textContent), $("#mo-payment", doc).textContent);
  check("provident-fund selector visible in Chinese", $("#mo-type-field", doc).hidden === false);
}

console.log("\n== mortgage provident fund and combined loans (zh) ==");
{
  const { win, doc } = await load("tools/mortgage-calculator.html?lang=zh");
  await sleep(400);

  // pure provident fund loan
  const type = $("#mo-type", doc);
  type.value = "fund";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(300);
  check("fund switch sets the 2.6% rate", $("#mo-rate", doc).value === "2.6", $("#mo-rate", doc).value);
  check("fund amount label", /^公积金金额$/.test($("#mo-amount-label", doc).textContent), $("#mo-amount-label", doc).textContent);
  check("fund mode zeroes the commercial amount", $("#mo-comm-amount", doc).value === "0", $("#mo-comm-amount", doc).value);
  check("fund payment ¥2,402.04", /^¥2,402\.04$/.test($("#mo-payment", doc).textContent), $("#mo-payment", doc).textContent);

  // combined loan: two portions, itemised per payment
  type.value = "combo";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(300);
  check("combo hides the single-amount row", $("#mo-single-row", doc).hidden === true);
  check("combo seeds both portions", $("#mo-fund-amount", doc).value === "600000" && $("#mo-comm-amount", doc).value === "400000",
    $("#mo-fund-amount", doc).value + " + " + $("#mo-comm-amount", doc).value);
  check("combo shows both amount rows", $("#mo-combo-row", doc).hidden === false);
  const head = $$(doc, "#mo-head th").map((th) => th.textContent.trim());
  check("combo table has 7 columns", head.length === 7, String(head.length));
  check("combo head itemises fund and commercial", /公积金本金/.test(head[1]) && /商贷本金/.test(head[3]), head.join("|"));
  check("combo payment is the sum of both portions", /^¥4,131\.91$/.test($("#mo-payment", doc).textContent), $("#mo-payment", doc).textContent);
  check("combo shows the per-portion split", /公积金 ¥2,402\.04/.test($("#mo-split", doc).textContent) && /商贷 ¥1,729\.87/.test($("#mo-split", doc).textContent), $("#mo-split", doc).textContent);

  const cells = [...$$(doc, "#mo-rows tr")[0].children].map((td) => td.textContent);
  check("first row itemises both portions", cells.length === 7 && /^¥1,102\.04$/.test(cells[1]) && /^¥663\.20$/.test(cells[3]), cells.join(" | "));
  check("first row interest matches each rate", /^¥1,300\.00$/.test(cells[2]) && /^¥1,066\.67$/.test(cells[4]), cells.join(" | "));

  // extra payments attack the commercial portion first
  setInput(win, $("#mo-extra", doc), "3000");
  await sleep(300);
  check("extra payment shows savings", $("#mo-extra-stats", doc).style.display !== "none" && /^¥[\d,]+\.\d\d$/.test($("#mo-saved", doc).textContent), $("#mo-saved", doc).textContent);
  setInput(win, $("#mo-extra", doc), "0");
  await sleep(300);
  check("combo returns to the base payment", /^¥4,131\.91$/.test($("#mo-payment", doc).textContent), $("#mo-payment", doc).textContent);

  // leaving combo must clear the portion that no longer applies
  type.value = "comm";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(300);
  check("commercial mode zeroes the fund amount", $("#mo-fund-amount", doc).value === "0", $("#mo-fund-amount", doc).value);
  check("commercial mode hides the combo row", $("#mo-combo-row", doc).hidden === true);
  check("commercial label is explicit", /^商贷金额$/.test($("#mo-amount-label", doc).textContent), $("#mo-amount-label", doc).textContent);
  check("commercial payment ignores the fund portion", /^¥4,324\.67$/.test($("#mo-payment", doc).textContent), $("#mo-payment", doc).textContent);
  check("no fund split line in commercial mode", $("#mo-split", doc).textContent === "", $("#mo-split", doc).textContent);

  // switching away and back must restore the user's numbers, not the defaults
  setInput(win, $("#mo-amount", doc), "1500000");
  await sleep(250);
  type.value = "fund";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(250);
  check("fund still zeroes the commercial amount", $("#mo-comm-amount", doc).value === "0");
  type.value = "comm";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(250);
  check("round-trip keeps the typed amount", $("#mo-amount", doc).value === "1500000",
    $("#mo-amount", doc).value);
  check("restored payment uses the typed amount", /^¥6,487/.test($("#mo-payment", doc).textContent),
    $("#mo-payment", doc).textContent);

  // combo round-trip: both portions come back
  type.value = "combo";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(250);
  setInput(win, $("#mo-fund-amount", doc), "800000");
  await sleep(250);
  type.value = "comm";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(250);
  type.value = "combo";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(250);
  check("combo round-trip keeps both portions", $("#mo-fund-amount", doc).value === "800000" && $("#mo-comm-amount", doc).value !== "0",
    $("#mo-fund-amount", doc).value + " + " + $("#mo-comm-amount", doc).value);
}

console.log("\n== mortgage: amount carries across loan types (zh) ==");
{
  const { win, doc } = await load("tools/mortgage-calculator.html?lang=zh");
  await sleep(400);
  const type = $("#mo-type", doc);

  setInput(win, $("#mo-amount", doc), "500000");
  await sleep(250);
  type.value = "fund";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(300);
  check("typed amount carries into the fund loan", $("#mo-amount", doc).value === "500000", $("#mo-amount", doc).value);
  check("rate still follows the product", $("#mo-rate", doc).value === "2.6", $("#mo-rate", doc).value);
  check("payment uses 50万 at 2.6%", /^¥2,001\.70$/.test($("#mo-payment", doc).textContent), $("#mo-payment", doc).textContent);

  setInput(win, $("#mo-amount", doc), "1500000");
  await sleep(300);
  check("cap hint appears above 120万", $("#mo-amount-hint", doc).hidden === false && /上限/.test($("#mo-amount-hint", doc).textContent), $("#mo-amount-hint", doc).textContent);
  setInput(win, $("#mo-amount", doc), "800000");
  await sleep(300);
  check("cap hint hides under the cap", $("#mo-amount-hint", doc).hidden === true);

  // an untouched default still gets the target product's own seed
  const fresh = await load("tools/mortgage-calculator.html?lang=zh");
  await sleep(400);
  const t2 = $("#mo-type", fresh.doc);
  t2.value = "fund";
  t2.dispatchEvent(new fresh.win.Event("change", { bubbles: true }));
  await sleep(300);
  check("untouched amount uses the fund seed", $("#mo-amount", fresh.doc).value === "600000", $("#mo-amount", fresh.doc).value);
  fresh.win.close();
}

console.log("\n== image-compressor.html ==");
{
  const { win, doc } = await load("tools/image-compressor.html");
  check("compress disabled without file", $("#ic-run", doc).disabled === true);
  check("download disabled without file", $("#ic-download", doc).disabled === true);
  $("#ic-quality", doc).value = "50";
  $("#ic-quality", doc).dispatchEvent(new win.Event("input", { bubbles: true }));
  check("quality label syncs", $("#ic-quality-val", doc).textContent === "50%");
}

console.log("\n== jwt-debugger.html ==");
{
  const { win, doc } = await load("tools/jwt-debugger.html");
  setInput(win, $("#jwt-input", doc), "not-a-jwt");
  check("invalid jwt flagged", /invalid/.test($("#jwt-state", doc).textContent), $("#jwt-state", doc).textContent);
  check("error shown", !$("#jwt-err", doc).classList.contains("hidden"));
  click(win, $("#jwt-sample", doc));
  await sleep(100);
  check("sample decoded", /decoded/.test($("#jwt-state", doc).textContent), $("#jwt-state", doc).textContent);
  check("alg HS256", $("#jwt-alg", doc).textContent === "HS256");
  check("header JSON", /"alg": "HS256"/.test($("#jwt-header", doc).textContent));
  check("payload has sub", /"sub"/.test($("#jwt-payload", doc).textContent));
  check("expiry rendered", /\d/.test($("#jwt-exp", doc).textContent), $("#jwt-exp", doc).textContent);
  const h2 = btoa(JSON.stringify({ alg: "none", typ: "JWT" })).replace(/=+$/, "");
  const p2 = btoa(JSON.stringify({ sub: "x" })).replace(/=+$/, "");
  setInput(win, $("#jwt-input", doc), h2 + "." + p2 + ".sig.extra");
  await sleep(80);
  check("four segments flagged malformed", /malformed/.test($("#jwt-state", doc).textContent), $("#jwt-state", doc).textContent);
  check("malformed error shown", !$("#jwt-err", doc).classList.contains("hidden"));
}

console.log("\n== diff-checker.html ==");
{
  const { win, doc } = await load("tools/diff-checker.html");
  check("two lines changed", $("#df-changed", doc).textContent === "2", $("#df-changed", doc).textContent);
  check("nothing added", $("#df-added", doc).textContent === "0");
  check("nothing removed", $("#df-removed", doc).textContent === "0");
  check("total 4 lines", $("#df-total", doc).textContent === "4");
  check("rows rendered", $$(doc, "#df-output .df-row").length >= 6);
  click(win, $("#df-swap", doc));
  check("swap keeps changes", $("#df-changed", doc).textContent === "2");
  setInput(win, $("#df-a", doc), "a\nb\nc");
  setInput(win, $("#df-b", doc), "a\nx\nc");
  await sleep(400);
  check("one line changed after edit", $("#df-changed", doc).textContent === "1", $("#df-changed", doc).textContent);
  setInput(win, $("#df-a", doc), "x");
  setInput(win, $("#df-b", doc), "");
  await sleep(400);
  check("line removed not changed", $("#df-removed", doc).textContent === "1" && $("#df-changed", doc).textContent === "0",
    "removed=" + $("#df-removed", doc).textContent + " changed=" + $("#df-changed", doc).textContent);
  setInput(win, $("#df-a", doc), "");
  await sleep(400);
  check("both empty shows empty state", /both sides empty/.test($("#df-output", doc).textContent) && $("#df-total", doc).textContent === "0");
}

console.log("\n== unit-converter.html ==");
{
  const { win, doc } = await load("tools/unit-converter.html");
  check("default length conversion", /39,370/.test($("#uc-result", doc).textContent), $("#uc-result", doc).textContent);
  check("all-units table", $$(doc, "#uc-all tr").length === 11);
  $("#uc-cat", doc).value = "temp";
  $("#uc-cat", doc).dispatchEvent(new win.Event("change", { bubbles: true }));
  setInput(win, $("#uc-value", doc), "212");
  await sleep(50);
  check("212F to K = 373.15", /373\.15/.test($("#uc-result", doc).textContent), $("#uc-result", doc).textContent);
  check("temp formula shown", /K =/.test($("#uc-formula", doc).textContent), $("#uc-formula", doc).textContent);
}

console.log("\n== qr-generator.html ==");
{
  const { win, doc } = await load("tools/qr-generator.html");
  click(win, $("#qr-gen", doc));
  await sleep(300);
  check("generate gives feedback", /encoder|Done|blocked|network/i.test($("#qr-note", doc).textContent), $("#qr-note", doc).textContent);
  check("quality/EC options present", $$(doc, "#qr-ec option").length === 4);
}

console.log("\n== pdf-tools.html ==");
{
  const { win, doc } = await load("tools/pdf-tools.html");
  check("merge panel default", !$("#pdf-panel-merge", doc).classList.contains("hidden"));
  check("split panel hidden", $("#pdf-panel-split", doc).classList.contains("hidden"));
  click(win, $('[data-pdftab="split"]', doc));
  check("tab switches", $("#pdf-panel-split", doc).classList.contains("hidden") === false);
  click(win, $("#pdf-merge", doc));
  check("merge without files warns", /at least one PDF/.test($("#pdf-merge-note", doc).textContent), $("#pdf-merge-note", doc).textContent);
  check("download disabled", $("#pdf-download", doc).disabled === true);
}

console.log("\n== bilingual: main-site link localization ==");
{
  // The English tools site is the default, so the raw HTML must already point at the
  // English blog — correct even if the i18n script never runs (stale cache, JS off).
  const raw = await JSDOM.fromURL(BASE + "/tools/token-counter.html", { resources: "usable", pretendToBeVisual: true });
  const rawDoc = raw.window.document;
  check("no-JS HTML points at English blog",
    rawDoc.querySelector(".main-site-link").getAttribute("href") === "https://ezaiops.com/en/",
    rawDoc.querySelector(".main-site-link").getAttribute("href"));
  check("no-JS header Blog link English",
    rawDoc.querySelector('.site-nav a[href^="https://ezaiops.com"]').getAttribute("href") === "https://ezaiops.com/en/");
  raw.window.close();

  const en = await load("tools/token-counter.html");
  await sleep(400);
  check("EN page links to English blog", en.doc.querySelector(".main-site-link").getAttribute("href") === "https://ezaiops.com/en/",
    en.doc.querySelector(".main-site-link").getAttribute("href"));
  const blogLink = en.doc.querySelector('.site-nav a[href^="https://ezaiops.com"]');
  check("EN blog tooltip says English", /in English/.test(blogLink.getAttribute("title") || ""), blogLink.getAttribute("title"));

  const zh = await load("tools/token-counter.html?lang=zh");
  await sleep(400);
  check("ZH page links to Chinese blog", /^https:\/\/ezaiops\.com\/?$/.test(zh.doc.querySelector(".main-site-link").getAttribute("href")),
    zh.doc.querySelector(".main-site-link").getAttribute("href"));
  check("ZH blog tooltip stays Chinese", /中文/.test(zh.doc.querySelector('.site-nav a[href^="https://ezaiops.com"]').getAttribute("title") || ""),
    zh.doc.querySelector('.site-nav a[href^="https://ezaiops.com"]').getAttribute("title"));
}

console.log("\n== json-formatter.html ==");
{
  const { win, doc, errors } = await load("tools/json-formatter.html");
  check("output pane shows a hint before any input", /appears here/.test($("#jf-out", doc).textContent),
    $("#jf-out", doc).textContent);
  check("output pane is not hidden on load", !$("#jf-out", doc).classList.contains("hidden"));
  setInput(win, $("#jf-input", doc), '{"b":1,"a":[1,2]}');
  click(win, $("#jf-format", doc));
  check("hint replaced by real output", !$("#jf-out", doc).classList.contains("placeholder"));
  check("format indents", /\n    "a"/.test($("#jf-out", doc).textContent), $("#jf-out", doc).textContent);
  check("format meta stats", /bytes/.test($("#jf-meta", doc).textContent), $("#jf-meta", doc).textContent);
  check("keys counted", /2 keys/.test($("#jf-meta", doc).textContent), $("#jf-meta", doc).textContent);
  click(win, $("#jf-minify", doc));
  check("minify", $("#jf-out", doc).textContent === '{"b":1,"a":[1,2]}', $("#jf-out", doc).textContent);
  setInput(win, $("#jf-input", doc), '{"bad":}');
  click(win, $("#jf-validate", doc));
  check("error visible", !$("#jf-err", doc).classList.contains("hidden"));
  check("error has line/col", /line \d+, column \d+/.test($("#jf-err", doc).textContent), $("#jf-err", doc).textContent);
  setInput(win, $("#jf-input", doc), '{"a":1e999}');
  click(win, $("#jf-format", doc));
  check("overflow warning shown", !$("#jf-warn", doc).classList.contains("hidden"), $("#jf-warn", doc).textContent.slice(0, 80));
  check("overflow warning names path", /\$\.a/.test($("#jf-warn", doc).textContent), $("#jf-warn", doc).textContent);
  setInput(win, $("#jf-input", doc), '{"id":123456789012345678901234567890}');
  click(win, $("#jf-format", doc));
  check("precision warning shown", /lose precision/.test($("#jf-warn", doc).textContent), $("#jf-warn", doc).textContent.slice(0, 80));
  setInput(win, $("#jf-input", doc), '{"a":1}');
  click(win, $("#jf-format", doc));
  check("no warning for normal numbers", $("#jf-warn", doc).classList.contains("hidden"));
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
  check("names the 1017 snapshot", /1017 snapshot released 2026-10-17/.test(doc.body.textContent));
}

console.log("\n== models: October 2026 release wave ==");
{
  const argon = await load("models/gemini-4-argon.html");
  const aText = argon.doc.body.textContent;
  check("argon shows $2 in / $10 out", /\$2\b/.test(aText) && /\$10\b/.test(aText));
  check("argon notes the promo end date", /2026-11-30/.test(aText));
  check("argon flat-rate FAQ (no tier)", /flat per-token rate/.test(aText));
  check("argon cache read rate published", /\$0\.10/.test(aText));
  check("no dangling cache price when caching has no rate", !/billed at —/.test(aText), aText.match(/billed at [^.]*\./)?.[0]);

  const haiku = await load("models/claude-haiku-5-5.html");
  const hText = haiku.doc.body.textContent;
  check("haiku 5.5 tier threshold shown", /100K/.test(hText));
  check("haiku 5.5 high-tier prices shown", /\$0\.50/.test(hText) && /\$2\.50/.test(hText));

  const pro = await load("models/deepseek-v4-pro.html");
  const pText = pro.doc.body.textContent;
  check("v4 pro off-peak lead", /\$0\.66/.test(pText) && /\$1\.98/.test(pText));
  check("v4 pro peak row doubles", /Weekday peak/.test(pText) && /\$1\.32/.test(pText) && /\$3\.96/.test(pText));

  const large4 = await load("models/mistral-large-4.html");
  const mText = large4.doc.body.textContent;
  check("mistral large 4 sale price", /\$0\.68/.test(mText) && /\$2\.09/.test(mText));
  check("mistral large 4 notes list price", /\$1\.36/.test(mText));

  const terra = await load("models/gpt-6-1-terra.html");
  const tText = terra.doc.body.textContent;
  check("terra standard price", /\$1 per 1M input/.test(tText) && /\$5 per 1M output/.test(tText));
  check("terra long-context tier shown", /272,000/.test(tText) && /\$7\.50/.test(tText));
  check("terra cached input rate", /\$0\.05/.test(tText));

  const kimi31 = await load("models/kimi-k3-1-pro.html");
  const kText = kimi31.doc.body.textContent;
  check("kimi k3.1 pro price", /\$2 per 1M input/.test(kText) && /\$10 per 1M output/.test(kText));
  check("kimi k3.1 pro shows highspeed variant", /\$20/.test(kText) && /Highspeed/.test(kText));

  const m3f = await load("models/minimax-m3-1-flash.html");
  const m3Text = m3f.doc.body.textContent;
  check("m3.1 flash price", /\$0\.15 per 1M input/.test(m3Text) && /\$0\.60 per 1M output/.test(m3Text));
  check("m3.1 flash cache rate", /\$0\.015/.test(m3Text));

  const qmax = await load("models/qwen3-8-max.html");
  const qText = qmax.doc.body.textContent;
  check("qwen3.8 max price", /\$1\.65 per 1M input/.test(qText));
  check("qwen3.8 max regional table", /US \(Virginia\)/.test(qText) && /CNY 12/.test(qText));
  check("qwen3.8 max cache rates", /\$0\.206/.test(qText) && /\$0\.137/.test(qText));

  const qflash = await load("models/qwen3-8-flash.html");
  const qfText = qflash.doc.body.textContent;
  check("qwen3.8 flash price", /\$0\.113 per 1M input/.test(qfText) && /\$0\.382 per 1M output/.test(qfText));

  const dturbo = await load("models/doubao-seed-2-1-turbo.html");
  const dText = dturbo.doc.body.textContent;
  check("doubao 2.1 turbo price", /\$0\.50 per 1M input/.test(dText) && /\$2\.50 per 1M output/.test(dText));
  check("doubao 2.1 turbo is flat-rate", /One flat rate/.test(dText) && /no long-context tier/i.test(dText));

  const dpro = await load("models/doubao-seed-2-0-pro.html");
  const dpText = dpro.doc.body.textContent;
  check("doubao 2.0 pro tier break shown", /131,072/.test(dpText) && /\$6/.test(dpText));
  check("doubao 2.0 pro cache rate", /\$0\.10/.test(dpText));


  const tc = await load("tools/token-counter.html");
  await sleep(400);
  const ids = $$(tc.doc, "#tc-model option").map((o) => o.value);
  for (const id of ["gemini-4-argon", "claude-haiku-5-5", "deepseek-v4-pro", "mistral-large-4", "mimo-v2-6-pro", "kimi-k2-7-code"]) {
    check("token counter lists " + id, ids.includes(id));
  }
  check("retired deepseek-v4-flash gone", !ids.includes("deepseek-v4-flash"));
}

console.log("\n== models/index.html ==");
{
  const { doc, errors } = await load("models/index.html");
  check("one row per model", $$(doc, "table.data tbody tr").length === modelN, String($$(doc, "table.data tbody tr").length));
  check("links to model pages", $$(doc, 'a[href^="/models/"]').length >= modelN);
  check("sources listed", $$(doc, ".prose ul li").length === modelData.sources.length,
    String($$(doc, ".prose ul li").length));
  check("main site link in crumbs", $$(doc, ".main-site-link").length === 1);
  check("main site banner", $$(doc, ".main-site-banner a").length >= 1);
  check("no console errors", errors.length === 0, errors.join(" | "));
}

console.log("\n== pages: about / contact / privacy ==");
{
  // Brand names and URLs are the only strings allowed to stay Latin in Chinese mode.
  const ALLOWED = /^(ezaiops|tools|GitHub|ezaiops\.com ↗|github\.com\/ezaiops\/tools)$/;
  async function untranslated(rel) {
    const { win, doc } = await load(rel + "?lang=zh");
    await sleep(500);
    const skip = new Set(["SCRIPT", "STYLE", "CODE", "PRE", "KBD", "NOSCRIPT"]);
    const out = [];
    const walker = doc.createTreeWalker(doc.body, win.NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const n = walker.currentNode;
      const t = (n.nodeValue || "").trim();
      if (!t || t.length < 3 || skip.has(n.parentNode.nodeName)) continue;
      if (/^[\d\s$%·—–\-+×/().,:]+$/.test(t)) continue;
      if (/[\u4e00-\u9fff]/.test(t)) continue;
      if (!/[A-Za-z]{3,}/.test(t)) continue;
      if (ALLOWED.test(t)) continue;
      out.push(t.slice(0, 60));
    }
    return out;
  }

  for (const p of ["about.html", "contact.html", "privacy.html"]) {
    const left = await untranslated(p);
    check(p + " fully translated", left.length === 0, left.join(" | "));
  }

  const about = await load("about.html");
  check("about has one h1", $$(about.doc, "h1").length === 1);
  check("about links to contact", $$(about.doc, 'a[href="/contact.html"]').length >= 1);
  check("about names the tool and model counts", /18 browser-based tools/.test(about.doc.body.textContent) && new RegExp(modelN + " LLM models").test(about.doc.body.textContent));

  const contact = await load("contact.html");
  check("contact links to the issue tracker", $$(contact.doc, 'a[href="https://github.com/ezaiops/tools/issues"]').length >= 1);
  check("contact links to privacy", $$(contact.doc, 'a[href="/privacy.html"]').length >= 1);

  const privacy = await load("privacy.html");
  const pText = privacy.doc.body.textContent;
  check("privacy covers consent for EEA/UK", /European Economic Area/.test(pText));
  check("privacy covers hosting logs", /GitHub Pages/.test(pText) && /Server logs/.test(pText));
  check("privacy covers user rights", /Your choices and rights/.test(pText));
  check("privacy dated today", /October 18, 2026/.test(pText));

  // Every page in the site must be able to reach these three pages.
  const hub = await load("index.html");
  const footerLinks = $$(hub.doc, '.site-footer a[href^="/about.html"], .site-footer a[href^="/contact.html"], .site-footer a[href^="/privacy.html"]');
  check("hub footer links to about/contact/privacy", footerLinks.length === 3, String(footerLinks.length));
}

console.log("\n== data / copy consistency ==");
{
  // Guards the two ways this repo has silently drifted before: copy that quotes a
  // stale model count, and model pages left behind after a model is removed.
  const data = JSON.parse(readFileSync(new URL("./models.json", import.meta.url), "utf8"));
  const n = data.models.length;
  const idx = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  const tc = readFileSync(new URL("../tools/token-counter.html", import.meta.url), "utf8");

  const counts = (s) => [...s.matchAll(/(\d+)\s+models\b/g)].map((m) => Number(m[1]));
  check("hub copy quotes the live model count", counts(idx).every((c) => c === n), counts(idx).join(",") + " vs " + n);
  check("token-counter copy quotes the live count", counts(tc).every((c) => c === n), counts(tc).join(",") + " vs " + n);
  check("token-counter quotes 1M-context flagship", /Gemini 4 Argon/.test(tc));

  const dir = new URL("../models/", import.meta.url);
  const pages = readdirSync(dir).filter((f) => f.endsWith(".html") && f !== "index.html").map((f) => f.slice(0, -5));
  const ids = data.models.map((m) => m.id);
  const orphans = pages.filter((p) => !ids.includes(p));
  const missing = ids.filter((id) => !pages.includes(id));
  check("no orphan model pages", orphans.length === 0, orphans.join(","));
  check("every model has a page", missing.length === 0, missing.join(","));
  check("models.js carries the data date", readFileSync(new URL("../assets/models.js", import.meta.url), "utf8").includes('"updated": "' + data.updated + '"'));
}

console.log("\n" + (failed === 0 ? "ALL " + passed + " CHECKS PASSED" : passed + " passed, " + failed + " FAILED"));
OPEN_DOMS.forEach((d) => { try { d.window.close(); } catch (e) { /* already closed */ } });
setTimeout(() => process.exit(failed === 0 ? 0 : 1), 100).unref();
