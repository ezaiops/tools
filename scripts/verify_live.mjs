import { createRequire } from "module";
const require = createRequire("C:/Users/june_/.workbuddy-ai/binaries/node/workspace/");
const { JSDOM, VirtualConsole } = require("jsdom");

const LIVE = "https://tools.ezaiops.com";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function load(path) {
  const vc = new VirtualConsole();
  const errs = [];
  vc.on("jsdomError", (e) => { const s = String(e && e.message || e); if (!/css|stylesheet|Could not load|not implemented/i.test(s)) errs.push(s); });
  vc.on("error", (...a) => errs.push(a.map(String).join(" ")));
  const dom = await JSDOM.fromURL(LIVE + path, {
    runScripts: "dangerously", resources: "usable", pretendToBeVisual: true, virtualConsole: vc,
  });
  await new Promise((r) => {
    const t = setTimeout(r, 15000);
    dom.window.addEventListener("load", () => { clearTimeout(t); setTimeout(r, 1800); }, { once: true });
  });
  return { win: dom.window, doc: dom.window.document, errs };
}

let pass = 0, fail = 0;
const ok = (label, cond, extra) => {
  if (cond) { pass++; console.log("  ok   " + label); }
  else { fail++; console.log("  FAIL " + label + (extra ? "  -> " + extra : "")); }
};

console.log("== live: mortgage calculator (zh) ==");
{
  const { win, doc, errs } = await load("/tools/mortgage-calculator.html?lang=zh");
  const q = (s) => doc.querySelector(s);
  ok("页面中文（标题已翻译）", /房贷与贷款计算器/.test(q("h1").textContent), q("h1").textContent);
  ok("默认 100万 / 3.2%", q("#mo-amount").value === "1000000" && q("#mo-rate").value === "3.2",
    q("#mo-amount").value + " / " + q("#mo-rate").value);
  ok("贷款类型可见", q("#mo-type-field").hidden === false);
  ok("组合贷行隐藏", q("#mo-combo-row").hidden === true);
  ok("商贷标签明确", /^商贷金额$/.test(q("#mo-amount-label").textContent), q("#mo-amount-label").textContent);

  const type = q("#mo-type");
  q("#mo-amount").value = "1500000";
  q("#mo-amount").dispatchEvent(new win.Event("input", { bubbles: true }));
  await sleep(300);

  type.value = "fund";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(300);
  ok("切公积金后商贷金额归零", q("#mo-comm-amount").value === "0", q("#mo-comm-amount").value);

  type.value = "comm";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(300);
  ok("往返后仍是 150万", q("#mo-amount").value === "1500000", q("#mo-amount").value);
  ok("月供按 150万 计算", /^¥6,487/.test(q("#mo-payment").textContent), q("#mo-payment").textContent);

  type.value = "combo";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(300);
  const head = [...doc.querySelectorAll("#mo-head th")].map((t) => t.textContent.trim());
  ok("组合贷 7 列", head.length === 7, String(head.length));
  q("#mo-fund-amount").value = "800000";
  q("#mo-fund-amount").dispatchEvent(new win.Event("input", { bubbles: true }));
  await sleep(300);

  type.value = "comm";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(300);
  type.value = "combo";
  type.dispatchEvent(new win.Event("change", { bubbles: true }));
  await sleep(300);
  ok("组合贷往返保留 80万", q("#mo-fund-amount").value === "800000", q("#mo-fund-amount").value);
  ok("无 JS 报错", errs.length === 0, errs.join(" | "));
  win.close();
}

console.log("\n== live: english defaults ==");
{
  const { doc } = await load("/tools/mortgage-calculator.html");
  const q = (s) => doc.querySelector(s);
  ok("英文 40万 / 7.4%", q("#mo-amount").value === "400000" && q("#mo-rate").value === "7.4");
  ok("英文隐藏贷款类型", q("#mo-type-field").hidden === true);
  ok("月供 $2,769.52", /^\$2,769\.52$/.test(q("#mo-payment").textContent), q("#mo-payment").textContent);
}

console.log("\n== live: hub search ==");
{
  const { win, doc } = await load("/");
  const input = doc.querySelector("#tool-search");
  input.value = "cron";
  input.dispatchEvent(new win.Event("input", { bubbles: true }));
  await sleep(200);
  const visible = [...doc.querySelectorAll("#tool-groups .tool-card-item:not([hidden])")];
  ok("搜索 cron 只剩 2 个工具", visible.length === 2, String(visible.length));
  ok("空分组被隐藏", doc.querySelectorAll("#tool-groups .tool-group:not([hidden])").length === 1,
    String(doc.querySelectorAll("#tool-groups .tool-group:not([hidden])").length));
  win.close();
}

console.log("\n== live: misc ==");
{
  const r = await fetch(LIVE + "/this-does-not-exist");
  ok("404 返回 404 状态", r.status === 404, String(r.status));
  const html = await r.text();
  ok("404 页面是自定义的", /This page doesn't exist/.test(html));
  const ads = await (await fetch(LIVE + "/ads.txt")).text();
  ok("ads.txt 授权 pub id", ads.includes("pub-8810200627517885"));
}

console.log("\n" + (fail === 0 ? "ALL " + pass + " LIVE CHECKS PASSED" : pass + " passed, " + fail + " FAILED"));
process.exit(fail === 0 ? 0 : 1);
