import { createRequire } from "module";
const require = createRequire("C:/Users/june_/.workbuddy-ai/binaries/node/workspace/");
const { JSDOM, VirtualConsole } = require("jsdom");

const BASE = "http://127.0.0.1:8901";
const pages = ["about.html", "contact.html", "privacy.html"];

for (const p of pages) {
  const vc = new VirtualConsole();
  const dom = await JSDOM.fromURL(BASE + "/" + p + "?lang=zh", {
    runScripts: "dangerously", resources: "usable", pretendToBeVisual: true, virtualConsole: vc,
  });
  await new Promise((r) => {
    const t = setTimeout(r, 6000);
    dom.window.addEventListener("load", () => { clearTimeout(t); setTimeout(r, 600); }, { once: true });
  });
  const doc = dom.window.document;
  const skip = new Set(["SCRIPT", "STYLE", "CODE", "PRE", "KBD", "NOSCRIPT"]);
  const misses = [];
  const walker = doc.createTreeWalker(doc.body, dom.window.NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode;
    const t = (n.nodeValue || "").trim();
    if (!t || t.length < 3) continue;
    if (skip.has(n.parentNode.nodeName)) continue;
    if (/^[\d\s$%·—–\-+×/().,:]+$/.test(t)) continue;          // numbers and punctuation
    if (/[\u4e00-\u9fff]/.test(t)) continue;                      // already Chinese
    if (!/[A-Za-z]{3,}/.test(t)) continue;                        // not prose
    misses.push(t.slice(0, 90) + "  <" + n.parentNode.nodeName + ">");
  }
  console.log("\n== " + p + " : " + misses.length + " untranslated ==");
  misses.forEach((m) => console.log("  " + m));
  dom.window.close();
}
process.exit(0);
