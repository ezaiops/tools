# tools.ezaiops.com

AI & DevOps micro-tools that run entirely in the browser. Pure static site — no build step, no backend, no data collection. Deployed on GitHub Pages at https://tools.ezaiops.com.

**Live locally:** `python -m http.server 8901` in this directory, then open http://localhost:8901

## What's inside

| Path | What |
|---|---|
| `index.html` | Tool hub / landing page |
| `tools/token-counter.html` | LLM token counter + cost calculator (34 models, official BPE tokenizer via CDN with heuristic fallback) |
| `tools/json-formatter.html` | Format / minify / validate JSON with error line+column |
| `tools/regex-tester.html` | Live JS regex tester: highlighting, capture groups, replacement preview |
| `tools/cron-explainer.html` | Cron → plain English + next 10 runs in local timezone |
| `tools/encode-decode.html` | Base64 / URL / HTML entities / SHA-1..512 (built-in pure-JS SHA-256) |
| `tools/timestamp-converter.html` | Unix ↔ ISO 8601 ↔ local, live clock |
| `tools/password-generator.html` | Passwords, passphrases, UUID v4, strength estimate |
| `tools/meta-tag-generator.html` | Title/OG/Twitter tags with SERP + social preview |
| `tools/cron-generator.html` | Visual cron builder — the reverse of the explainer |
| `tools/subnet-calculator.html` | IPv4 CIDR: network/broadcast/hosts, masks, binary view |
| `tools/self-host-vs-api.html` | GPU rental vs per-token API break-even |
| `tools/mortgage-calculator.html` | 等额本息 / 等额本金 amortization + extra payments |
| `tools/image-compressor.html` | Canvas-based JPG/PNG compression and WebP conversion |
| `tools/jwt-debugger.html` | JWT decode + HS256 verification (crypto.subtle) |
| `tools/diff-checker.html` | Myers line + word diff |
| `tools/unit-converter.html` | Six unit categories incl. GiB vs GB |
| `tools/qr-generator.html` | QR as SVG/PNG, four ECC levels |
| `tools/pdf-tools.html` | PDF merge/split/reorder via pdf-lib |
| `models/*.html` | 34 per-model SEO pricing pages (generated) |
| `models/index.html` | Full pricing comparison hub |
| `privacy.html`, `about.html`, `contact.html` | Privacy policy, about and contact pages |
| `robots.txt`, `ads.txt`, `sitemap.xml` | Crawler + monetization files (`ads.txt` has a commented placeholder) |

## Local development

```bash
# 1. serve
cd tools
python -m http.server 8901

# 2. static checks (links, titles, h1, JSON-LD, sitemap)
python scripts/check_site.py

# 3. interactive tests (jsdom; needs jsdom in the managed node workspace)
node scripts/test_interactive.mjs        # 277 checks

# 4. regenerate model pages + calculator data + sitemap after editing models.json
python scripts/generate_models.py
```

## Deploy to GitHub Pages (chosen path)

1. **Repo name: `tools`** — `github.com/ezaiops/tools` mirrors the subdomain, and because it is org-scoped there is no collision. Create it under the `ezaiops` account/org.
2. Push this folder's contents to the repo **root**:
   ```bash
   cd tools
   git init && git add -A && git commit -m "init"
   git branch -M main
   git remote add origin git@github.com:ezaiops/tools.git
   git push -u origin main
   ```
3. Repo → **Settings → Pages → Source: Deploy from a branch → main / (root) → Save**.
   The `CNAME` file in the repo root already binds `tools.ezaiops.com`.
4. Cloudflare DNS: `CNAME tools → ezaiops.github.io`, proxied (orange cloud).
   Enabled HTTPS in Pages settings once the certificate check passes (usually minutes).
5. Verify https://tools.ezaiops.com, then submit the sitemap in Search Console.

Notes: `.nojekyll` is committed so Pages serves every file verbatim. Keep `scripts/`
and `README.md` in the repo — they are ignored by Pages and document the workflow.

## Alternative: Cloudflare Pages

Cloudflare dashboard → Workers & Pages → Create → Pages → Upload assets, drag this
folder in, then add the custom domain `tools.ezaiops.com`. Or connect the same
GitHub repo: Pages → Connect to Git → framework "None", build command empty,
output directory `/`. Every push to `main` auto-deploys.

## Turning on AdSense

1. Site live on its own domain with original content pages (done — every tool page has an explanation section + FAQ)
2. Apply at adsense.google.com with `tools.ezaiops.com`
3. After approval: replace the placeholder in `ads.txt` with your `pub-` ID and uncomment the line
4. Replace each `<div class="ad-slot">…</div>` placeholder with your AdSense unit, or add the Auto ads snippet to `<head>`
5. At ~10k monthly sessions, evaluate Ezoic as a higher-paying alternative

## Updating model prices

Edit `scripts/models.json` (single source of truth), then:

```bash
python scripts/generate_models.py    # rewrites models/*.html, assets/models.js, sitemap.xml
python scripts/check_site.py         # verify everything still resolves
```

Prices were sourced from official provider pricing docs on 2026-10-18 (OpenAI, Anthropic, Google, DeepSeek, xAI, Z.AI, Moonshot, MiniMax, Xiaomi, Mistral). Providers change rates often — re-verify before publishing. `models.json`'s `updated` field drives the "last updated" date on every generated page, so bump it whenever prices change.

## Adding a new tool

The hub grid is generated from `scripts/tools.json` — never hand-edit it in `index.html` (it sits between the `<!-- TOOLS-GRID:START -->` markers). Cards are grouped by `group`, and each card's icon comes from the `ICONS` map in `scripts/generate_hub.py` (24x24 grid, 1.5px stroke, inline SVG — no icon font, no image requests).

1. Build the page: `tools/<id>.html`, copying the header/footer, SEO meta, explanation section and FAQ pattern from an existing tool page (see `tools/json-formatter.html` for a minimal template).
2. Add an entry to `scripts/tools.json`. `desc` should fit two lines on a card (~90 characters), `group` is one of `ai | text | time | net | files | calc`:
   ```json
   { "id": "<id>", "name": "...", "url": "/tools/<id>.html",
     "desc": "One sentence on the card.", "group": "text", "status": "live" }
   ```
3. Add an icon for the new id to `ICONS` in `scripts/generate_hub.py` (a fallback square is drawn if you forget, which is the tell that you forgot).
4. Regenerate the hub and sitemap, then test and commit (the post-commit hook pushes automatically):
   ```bash
   python scripts/generate_hub.py
   python scripts/check_site.py
   node scripts/test_interactive.mjs
   git add -A && git commit -m "Add <tool>"
   ```

Backlog lives in the same file with `"status": "planned"` plus `priority` (1 = next) and `effort` (S/M/L). Planned entries are no longer rendered on the hub — the empty roadmap block was removed in the redesign — so the manifest is now a private backlog. Keep it that way until there are enough planned tools to justify a public roadmap again.

## Bilingual (EN / 中文)

The site is English-first for global traffic, with a full Chinese toggle in the
same 中文/EN pattern as ezaiops.com:

- Switcher lives in the header (injected by `assets/i18n.js`); `?lang=zh` is a
  shareable deep link, the choice persists in localStorage, and `<html lang>`
  updates with it
- Engine: `assets/i18n.js` — translates by matching DOM text nodes, so no page
  markup needs `data-i18n` attributes. Dictionaries: `assets/i18n/common.js`
  (header/footer/crumbs), `assets/i18n/hub.js`, `assets/i18n/privacy.js`,
  `assets/i18n/about.js`, `assets/i18n/contact.js`, `assets/i18n/tools/*.js`
- Key forms: plain (a text node), `ph:` (placeholder), `title:` (attribute
  value), `el:` (whole-element innerHTML — for paragraphs that contain
  `<code>`/`<strong>` markup)
- Dynamic JS strings go through `window.ezI18N.t()` / `.tf()`; pages re-render
  on the `ez:i18n` event after the dictionary applies
- The 34 generated pricing pages translate the chrome but keep their content
  (numbers, model names, provider terms) in English
- Both languages are covered by the test suite (the English suite plus a
  `?lang=zh` suite that asserts static and dynamic translations)

To fix or extend a translation, edit the matching file in `assets/i18n/` — the
English text is the key, so a missing key simply stays English.

## Design notes

- Light theme, system font stack, zero JS framework; every page is one HTML file with one inline script
- Hub: client-side search (`/` focuses it), six category groups, inline SVG icons, no badges
- Text tools use a two-pane workbench (`.workbench`): input left, output right, both always visible; it stacks below 900px
- Shared chrome: `assets/style.css` (design system) + `assets/common.js` (copy-to-clipboard, footer year, toast)
- JSON-LD: `SoftwareApplication` + `Offer` on tool pages, `FAQPage` + `ItemList` on model pages, `WebSite` on the hub. Tool pages carry visible FAQ sections but no FAQPage schema — Google retired FAQ rich results, so it would add nothing
- The token counter loads `gpt-tokenizer` from esm.sh at runtime; if the CDN is unreachable it falls back to a documented approximation, so the tool never breaks
