(function () {
  "use strict";

  var ez = {
    $: function (sel, root) { return (root || document).querySelector(sel); },
    $$: function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); },
    escapeHtml: function (s) {
      return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
    },
    copy: function (text) {
      var done = function () {
        ez.toast(window.ezI18N ? window.ezI18N.t("Copied to clipboard") : "Copied to clipboard");
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { ez.copyFallback(text); done(); });
      } else {
        ez.copyFallback(text); done();
      }
    },
    copyFallback: function (text) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); } catch (e) { /* noop */ }
      document.body.removeChild(ta);
    },
    toast: function (msg) {
      var t = ez.$(".toast");
      if (!t) {
        t = document.createElement("div");
        t.className = "toast";
        document.body.appendChild(t);
      }
      t.textContent = msg;
      t.classList.add("show");
      clearTimeout(t._timer);
      t._timer = setTimeout(function () { t.classList.remove("show"); }, 1800);
    }
  };
  window.ezTools = ez;

  document.addEventListener("click", function (ev) {
    var btn = ev.target.closest("[data-copy-target],[data-copy]");
    if (!btn) return;
    var text = btn.getAttribute("data-copy");
    if (!text && btn.getAttribute("data-copy-target")) {
      var el = document.querySelector(btn.getAttribute("data-copy-target"));
      if (el) text = el.value !== undefined && el.tagName !== "PRE" && el.tagName !== "DIV" ? el.value : el.textContent;
    }
    if (text) ez.copy(text);
  });

  document.addEventListener("DOMContentLoaded", function () {
    ez.$$("[data-year]").forEach(function (el) { el.textContent = String(new Date().getFullYear()); });
  });

  // boot the i18n engine on every page (safe no-op when dictionaries miss)
  (function () {
    var s = document.createElement("script");
    s.src = "/assets/i18n.js?v=20261022a";
    s.async = false;
    document.head.appendChild(s);
  })();
})();
