// Generate the Chinese edition of every page that has a full dictionary.
//
// The English pages translate themselves at runtime from assets/i18n/*.js. Rather
// than reimplement that matching in Python, this loads each page in jsdom, lets
// the real engine do the work, and exports the resulting DOM. That keeps one
// translation implementation instead of two, and it covers the el: keys (mixed
// content with inline <code>/<strong>) that a text-node pass would miss.
//
// Run with the local server up:  python -m http.server 8901
// Then:  node scripts/generate_zh.mjs
import { createRequire } from "module";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { dirname, join, resolve } from "path";
import { fileURLToPath } from "url";

const require = createRequire("C:/Users/june_/.workbuddy-ai/binaries/node/workspace/");
const { JSDOM, VirtualConsole } = require("jsdom");

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const ORIGIN = process.env.EZ_ORIGIN || "http://127.0.0.1:8901";
const CANON = "https://tools.ezaiops.com";
const WAIT_MS = 15000;

const META = JSON.parse(readFileSync(join(ROOT, "scripts/zh-meta.json"), "utf8"));
const PAGES = Object.keys(META).filter((k) => !k.startsWith("_"));
const ZH_PATHS = new Set(PAGES.map((p) => "/" + p));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** The engine sets <html lang="zh-CN"> as its last act, so this is the signal. */
async function waitForTranslation(doc) {
  const t0 = Date.now();
  while (Date.now() - t0 < WAIT_MS) {
    if (doc.documentElement.getAttribute("lang") === "zh-CN") return true;
    await sleep(100);
  }
  return false;
}

function setAttr(doc, selector, attr, value) {
  const el = doc.querySelector(selector);
  if (el) el.setAttribute(attr, value);
}

function upsertMeta(doc, key, value) {
  for (const sel of [`meta[property="${key}"]`, `meta[name="${key}"]`]) {
    const el = doc.querySelector(sel);
    if (el) {
      el.setAttribute("content", value);
      return;
    }
  }
  const m = doc.createElement("meta");
  m.setAttribute("property", key);
  m.setAttribute("content", value);
  doc.head.appendChild(m);
}

function setHreflang(doc, zhUrl, enUrl) {
  doc.head.querySelectorAll('link[rel="alternate"][hreflang]').forEach((n) => n.remove());
  const anchor = doc.head.querySelector('link[rel="canonical"]');
  const frag = doc.createDocumentFragment();
  frag.appendChild(doc.createTextNode("\n"));
  for (const [lang, href] of [
    ["zh-CN", zhUrl],
    ["en", enUrl],
    ["x-default", enUrl],
  ]) {
    const l = doc.createElement("link");
    l.setAttribute("rel", "alternate");
    l.setAttribute("hreflang", lang);
    l.setAttribute("href", href);
    frag.appendChild(l);
    frag.appendChild(doc.createTextNode("\n"));
  }
  if (anchor) anchor.after(frag);
  else doc.head.appendChild(frag);
}

function rewriteJsonLd(doc, zhUrl) {
  doc.querySelectorAll('script[type="application/ld+json"]').forEach((s) => {
    try {
      const data = JSON.parse(s.textContent);
      const walk = (o) => {
        if (!o || typeof o !== "object") return;
        if (typeof o.url === "string" && o.url.startsWith(CANON)) o.url = zhUrl;
        Object.values(o).forEach(walk);
      };
      walk(data);
      s.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      /* leave malformed blocks alone */
    }
  });
}

/** Point internal links at the Chinese edition, but only where one exists. */
function rewriteLinks(doc, rel) {
  doc.querySelectorAll("a[href]").forEach((a) => {
    const href = a.getAttribute("href");
    if (!href) return;
    if (href === "/" || href === "/index.html") {
      a.setAttribute("href", "/zh/");
      return;
    }
    if (href.startsWith("/") && ZH_PATHS.has(href)) {
      a.setAttribute("href", "/zh" + href);
      return;
    }
    // The pricing tree has its own Chinese edition under /zh/models/, produced by
    // generate_models.py rather than this script. Route those links there too, or
    // a reader on a Chinese page lands on the English price table.
    if (href.startsWith("/models/")) {
      a.setAttribute("href", "/zh" + href);
    }
  });
}

function staticSwitcher(doc, rel) {
  const sw = doc.querySelector(".lang-switch");
  if (!sw) return;
  // The English link carries ?lang=en so the switch actually lands on English:
  // the engine treats /zh/ paths as Chinese regardless of the stored preference.
  sw.innerHTML =
    `<a href="${rel === "index.html" ? "/zh/" : "/zh/" + rel}" hreflang="zh-CN" class="active" aria-current="page">中文</a>` +
    `<a href="/${rel}?lang=en" hreflang="en">EN</a>`;
}

function postProcess(doc, rel) {
  const meta = META[rel];
  const zhUrl = rel === "index.html" ? `${CANON}/zh/` : `${CANON}/zh/${rel}`;
  const enUrl = rel === "index.html" ? `${CANON}/` : `${CANON}/${rel}`;

  doc.title = meta.title;
  upsertMeta(doc, "description", meta.desc);
  upsertMeta(doc, "og:title", meta.title.replace(/\s+[—-]\s+ezaiops tools$/, ""));
  upsertMeta(doc, "og:description", meta.desc);
  upsertMeta(doc, "og:locale", "zh_CN");
  setAttr(doc, 'link[rel="canonical"]', "href", zhUrl);
  setHreflang(doc, zhUrl, enUrl);
  rewriteJsonLd(doc, zhUrl);
  rewriteLinks(doc, rel);
  staticSwitcher(doc, rel);
  // Tells assets/i18n.js the DOM is already Chinese, so it loads dictionaries
  // for t()/tf() but skips a pointless second walk of the tree.
  doc.documentElement.setAttribute("data-zh-static", "1");
  doc.documentElement.setAttribute("lang", "zh-CN");
}

function serialize(doc) {
  return "<!DOCTYPE html>\n" + doc.documentElement.outerHTML + "\n";
}

/** Insert hreflang into an English page without re-serialising it. Idempotent. */
function addHreflangToEnglish(rel) {
  const file = join(ROOT, rel);
  if (!existsSync(file)) return false;
  let html = readFileSync(file, "utf8");
  if (html.includes('hreflang="zh-CN"')) return false;
  const block =
    `<link rel="alternate" hreflang="zh-CN" href="${CANON}/zh/${rel}">\n` +
    `<link rel="alternate" hreflang="en" href="${CANON}/${rel}">\n` +
    `<link rel="alternate" hreflang="x-default" href="${CANON}/${rel}">\n`;
  const idx = html.indexOf("</head>");
  if (idx === -1) return false;
  html = html.slice(0, idx) + block + html.slice(idx);
  writeFileSync(file, html, "utf8");
  return true;
}

async function renderPage(rel) {
  const errors = [];
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => errors.push(String(e.message).slice(0, 100)));

  const dom = await JSDOM.fromURL(`${ORIGIN}/${rel}?lang=zh`, {
    runScripts: "dangerously",
    resources: "usable",
    pretendToBeVisual: true,
    virtualConsole: vc,
  });

  const ok = await waitForTranslation(dom.window.document);
  const doc = dom.window.document;
  if (!ok) {
    dom.window.close();
    throw new Error(`${rel}: translation never applied (no zh-CN on <html>)`);
  }
  postProcess(doc, rel);
  const html = serialize(doc);
  dom.window.close();

  const out = join(ROOT, "zh", rel);
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, html, "utf8");

  const zhChars = (html.match(/[\u4e00-\u9fff]/g) || []).length;
  return { rel, bytes: html.length, zhChars, errors: errors.length };
}

async function main() {
  const results = [];
  for (const rel of PAGES) {
    process.stdout.write(`  ${rel} … `);
    try {
      const r = await renderPage(rel);
      results.push(r);
      console.log(`${r.bytes} bytes, ${r.zhChars} 汉字${r.errors ? `, ${r.errors} 个脚本错误` : ""}`);
    } catch (e) {
      console.log("FAILED: " + e.message);
      results.push({ rel, failed: true });
    }
  }

  let touched = 0;
  for (const rel of PAGES) if (addHreflangToEnglish(rel)) touched++;

  const failed = results.filter((r) => r.failed);
  console.log(`\n生成 ${results.length - failed.length}/${PAGES.length} 个中文页；英文页注入 hreflang：${touched} 个`);
  if (failed.length) {
    console.log("失败：" + failed.map((f) => f.rel).join(", "));
    process.exitCode = 1;
  }
}

main();
