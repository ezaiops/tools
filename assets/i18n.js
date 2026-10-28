/* ezaiops tools — client-side i18n engine.
 * Usage: append ?lang=zh (or click 中文 in the header). Choice persists in
 * localStorage and <html lang> is updated. Translation dictionaries live in
 * assets/i18n/*.js and are matched by DOM text nodes, so no page markup needs
 * data-i18n attributes. Dynamic JS strings use window.ezI18N.t()/tf().
 */
var ASSET_V = "20261028g";

(function () {
  "use strict";

  var LANG_KEY = "ez-lang";

  // pathname -> dictionary files (common.js is always loaded first)
  var DICT_FILES = {
    "/": ["i18n/hub.js"],
    "/index.html": ["i18n/hub.js"],
    "/privacy.html": ["i18n/privacy.js"],
    "/about.html": ["i18n/about.js"],
    "/contact.html": ["i18n/contact.js"],
    "/tools/token-counter.html": ["i18n/tools/token-counter.js"],
    "/tools/json-formatter.html": ["i18n/tools/json-formatter.js"],
    "/tools/regex-tester.html": ["i18n/tools/regex-tester.js"],
    "/tools/cron-explainer.html": ["i18n/tools/cron-explainer.js"],
    "/tools/cron-generator.html": ["i18n/tools/cron-generator.js"],
    "/tools/subnet-calculator.html": ["i18n/tools/subnet-calculator.js"],
    "/tools/self-host-vs-api.html": ["i18n/tools/self-host-vs-api.js"],
    "/tools/mortgage-calculator.html": ["i18n/tools/mortgage-calculator.js"],
    "/tools/image-compressor.html": ["i18n/tools/image-compressor.js"],
    "/tools/jwt-debugger.html": ["i18n/tools/jwt-debugger.js"],
    "/tools/diff-checker.html": ["i18n/tools/diff-checker.js"],
    "/tools/unit-converter.html": ["i18n/tools/unit-converter.js"],
    "/tools/qr-generator.html": ["i18n/tools/qr-generator.js"],
    "/tools/pdf-tools.html": ["i18n/tools/pdf-tools.js"],
    "/tools/encode-decode.html": ["i18n/tools/encode-decode.js"],
    "/tools/timestamp-converter.html": ["i18n/tools/timestamp-converter.js"],
    "/tools/password-generator.html": ["i18n/tools/password-generator.js"],
    "/tools/meta-tag-generator.html": ["i18n/tools/meta-tag-generator.js"]
  };

  var dicts = [];
  var lang = "en";

  // The static Chinese edition lives under /zh/. The path is authoritative
  // there: someone who chose English on the English page must still get Chinese
  // content when they land on a /zh/ URL.
  function isZhPath() { return /^\/zh(\/|$)/.test(location.pathname); }
  function stripZh(p) { return p.indexOf("/zh/") === 0 ? p.slice(3) : p; }

  function getLang() {
    if (isZhPath()) return "zh";
    var v = null;
    try { v = new URLSearchParams(location.search).get("lang"); } catch (e) { /* file:// */ }
    if (v !== "zh" && v !== "en") {
      try { v = localStorage.getItem(LANG_KEY); } catch (e) { /* storage off */ }
    }
    return v === "zh" ? "zh" : "en";
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src;
      s.async = false;
      s.onload = resolve;
      s.onerror = function () { reject(new Error("failed: " + src)); };
      document.head.appendChild(s);
    });
  }

  function mergeDicts() {
    var out = {};
    dicts.forEach(function (d) {
      Object.keys(d).forEach(function (k) { out[k] = d[k]; });
    });
    return out;
  }

  var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1, NOSCRIPT: 1, OPTGROUP: 1 };

  function applyDict(dict) {
    var texts = {};
    var placeholders = {};
    var titles = {};
    var elements = {};
    Object.keys(dict).forEach(function (k) {
      if (k.indexOf("el:") === 0) elements[k.slice(3)] = dict[k];
      else if (k.indexOf("ph:") === 0) placeholders[k.slice(3)] = dict[k];
      else if (k.indexOf("title:") === 0) titles[k.slice(6)] = dict[k];
      else texts[k] = dict[k];
    });

    // element-level replacement first (mixed content with inline tags)
    if (Object.keys(elements).length) {
      document.querySelectorAll("body *").forEach(function (el) {
        if (!el || !el.nodeName) return;
        if (SKIP_TAGS[el.nodeName]) return;
        var txt = el.textContent.replace(/\s+/g, " ").trim();
        if (Object.prototype.hasOwnProperty.call(elements, txt)) {
          el.innerHTML = elements[txt];
        }
      });
    }

    var SKIP = { TEXTAREA: 1, SCRIPT: 1, STYLE: 1, CODE: 1, PRE: 1, KBD: 1, NOSCRIPT: 1 };
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        if (!n.nodeValue || !n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        var p = n.parentNode;
        if (!p || !p.nodeName || SKIP[p.nodeName]) return NodeFilter.FILTER_REJECT;
        return Object.prototype.hasOwnProperty.call(texts, n.nodeValue.trim())
          ? NodeFilter.FILTER_ACCEPT
          : NodeFilter.FILTER_REJECT;
      }
    });
    var hits = [];
    while (walker.nextNode()) hits.push(walker.currentNode);
    hits.forEach(function (n) {
      var v = n.nodeValue;
      var lead = v.slice(0, v.length - v.replace(/^\s+/, "").length);
      var trailMatch = v.match(/\s+$/);
      n.nodeValue = lead + texts[v.trim()] + (trailMatch ? trailMatch[0] : "");
    });

    document.querySelectorAll("[placeholder]").forEach(function (el) {
      var v = el.getAttribute("placeholder");
      if (Object.prototype.hasOwnProperty.call(placeholders, v)) el.setAttribute("placeholder", placeholders[v]);
    });
    document.querySelectorAll("[title]").forEach(function (el) {
      var v = el.getAttribute("title");
      if (Object.prototype.hasOwnProperty.call(titles, v)) el.setAttribute("title", titles[v]);
    });
    return hits.length;
  }

  function injectSwitcher() {
    var nav = document.querySelector(".site-nav");
    if (!nav || nav.querySelector(".lang-switch")) return;
    var wrap = document.createElement("div");
    wrap.className = "lang-switch";

    // Pages with a static Chinese edition link straight to it: one canonical URL
    // per language, and the anchor hands crawlers a path to the /zh/ copy.
    // Pages without one keep the ?lang= deep link behind a button, so Googlebot
    // never discovers a parameterised duplicate.
    var clean = stripZh(location.pathname);
    var hasStaticZh = !!(DICT_FILES[clean] || DICT_FILES[clean.replace(/\/$/, "/index.html")]);
    if (hasStaticZh) {
      // lang can still be "zh" on an English URL (?lang=zh deep link), so the
      // highlight follows the active language, not the path.
      var zhActive = lang === "zh";
      var zhHref = clean === "/" ? "/zh/" : "/zh" + clean;
      var enHref = zhActive ? clean + "?lang=en" : clean;
      wrap.innerHTML =
        '<a href="' + zhHref + '" hreflang="zh-CN"' +
        (zhActive ? ' class="active" aria-current="page"' : "") + ">中文</a>" +
        '<a href="' + enHref + '" hreflang="en"' +
        (zhActive ? "" : ' class="active" aria-current="page"') + ">EN</a>";
      nav.appendChild(wrap);
      return;
    }

    wrap.innerHTML =
      '<button type="button" data-lang="zh"' + (lang === "zh" ? ' class="active" aria-current="page"' : "") + ">中文</button>" +
      '<button type="button" data-lang="en"' + (lang === "en" ? ' class="active" aria-current="page"' : "") + ">EN</button>";
    wrap.addEventListener("click", function (ev) {
      var a = ev.target.closest ? ev.target.closest("[data-lang]") : null;
      if (!a) return;
      ev.preventDefault();
      var next = a.getAttribute("data-lang");
      try { localStorage.setItem(LANG_KEY, next); } catch (e) { /* storage off */ }
      try {
        var url = new URL(location.href);
        url.searchParams.set("lang", next);
        location.href = url.toString();
      } catch (e) {
        location.search = "?lang=" + next;
      }
    });
    nav.appendChild(wrap);
  }

  // Outbound links to the main site follow the UI language: the English tools UI
  // points at the English blog (/en/), the Chinese UI at the Chinese root.
  function localizeMainSiteLinks() {
    var anchors = document.querySelectorAll('a[href^="https://ezaiops.com"]');
    Array.prototype.forEach.call(anchors, function (a) {
      var href = a.getAttribute("href");
      if (lang === "en") {
        if (/^https:\/\/ezaiops\.com\/?$/.test(href)) {
          a.setAttribute("href", "https://ezaiops.com/en/");
        }
        if (/in Chinese/.test(a.getAttribute("title") || "")) {
          a.setAttribute("title", "ezaiops.com — AI agent observability & LLMOps field notes (in English)");
        }
      } else {
        if (/^https:\/\/ezaiops\.com\/en\/?$/.test(href)) {
          a.setAttribute("href", "https://ezaiops.com/");
        }
        if (/in English/.test(a.getAttribute("title") || "")) {
          a.setAttribute("title", "ezaiops.com — AI agent observability & LLMOps field notes (in Chinese)");
        }
      }
    });
  }

  function finish(count) {
    document.documentElement.setAttribute("lang", lang === "zh" ? "zh-CN" : "en");
    injectSwitcher();
    localizeMainSiteLinks();
    window.dispatchEvent(new CustomEvent("ez:i18n", { detail: { lang: lang, replaced: count } }));
  }

  function init() {
    lang = getLang();
    var clean = stripZh(location.pathname);
    var path = clean.replace(/\/$/, "/index.html");
    var files = ["i18n/common.js"].concat(DICT_FILES[clean] || DICT_FILES[path] || []);
    Promise.all(files.map(function (f) {
      return loadScript("/assets/" + f + "?v=" + ASSET_V).catch(function () { /* dictionary missing: keep English */ });
    })).then(function () {
      dicts = (window.I18N_DICTS || []).slice();
      if (lang !== "zh") { injectSwitcher(); localizeMainSiteLinks(); return; }
      // The /zh/ pages ship pre-translated. Load the dictionaries so t()/tf()
      // can serve dynamic strings, but skip the walk: the keys are English and
      // cannot match a DOM that is already Chinese.
      if (document.documentElement.hasAttribute("data-zh-static")) { finish(0); return; }
      var count = applyDict(mergeDicts());
      finish(count);
    }).catch(function () { /* never break the page over i18n */ });
  }

  window.ezI18N = {
    get lang() { return lang; },
    t: function (key) {
      if (lang !== "zh") return key;
      var d = mergeDicts();
      return Object.prototype.hasOwnProperty.call(d, key) ? d[key] : key;
    },
    tf: function (key) {
      if (lang !== "zh") {
        var out = key;
        for (var j = 1; j < arguments.length; j++) out = out.replace("%s", String(arguments[j]));
        return out;
      }
      var s = this.t(key);
      for (var i = 1; i < arguments.length; i++) {
        s = s.replace("%s", String(arguments[i]));
      }
      return s;
    },
    init: init
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
