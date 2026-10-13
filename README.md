# tools.ezaiops.com

Free AI & DevOps micro-tools that run entirely in the browser. Pure static site — no build step, no backend, no data collection. Ready to deploy to Cloudflare Pages.

**Live locally:** `python -m http.server 8901` in this directory, then open http://localhost:8901

## What's inside

| Path | What |
|---|---|
| `index.html` | Tool hub / landing page |
| `tools/token-counter.html` | LLM token counter + cost calculator (22 models, official BPE tokenizer via CDN with heuristic fallback) |
| `tools/json-formatter.html` | Format / minify / validate JSON with error line+column |
| `tools/regex-tester.html` | Live JS regex tester: highlighting, capture groups, replacement preview |
| `tools/cron-explainer.html` | Cron → plain English + next 10 runs in local timezone |
| `tools/encode-decode.html` | Base64 / URL / HTML entities / SHA-1..512 (built-in pure-JS SHA-256) |
| `tools/timestamp-converter.html` | Unix ↔ ISO 8601 ↔ local, live clock |
| `tools/password-generator.html` | Passwords, passphrases, UUID v4, strength estimate |
| `tools/meta-tag-generator.html` | Title/OG/Twitter tags with SERP + social preview |
| `models/*.html` | 29 per-model SEO pricing pages (generated) |
| `models/index.html` | Full pricing comparison hub |
| `privacy.html` | AdSense-ready privacy policy placeholder |
| `robots.txt`, `ads.txt`, `sitemap.xml` | Crawler + monetization files (`ads.txt` has a commented placeholder) |

## Local development

```bash
# 1. serve
cd tools-ezaiops
python -m http.server 8901

# 2. static checks (links, titles, h1, JSON-LD, sitemap)
python scripts/check_site.py

# 3. interactive tests (jsdom; needs jsdom in the managed node workspace)
node scripts/test_interactive.mjs        # 86 checks

# 4. regenerate model pages + calculator data + sitemap after editing models.json
python scripts/generate_models.py
```

## Deploy to GitHub Pages (chosen path)

1. **Repo name: `tools`** — `github.com/ezaiops/tools` mirrors the subdomain, and because it is org-scoped there is no collision. Create it under the `ezaiops` account/org.
2. Push this folder's contents to the repo **root**:
   ```bash
   cd tools-ezaiops
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

Prices were sourced from official provider pricing docs on 2026-10-13 (OpenAI, Anthropic, Google, DeepSeek, xAI, Z.AI, Moonshot, MiniMax, Xiaomi, Mistral). Providers change rates often — re-verify before publishing.

## Design notes

- Light theme, system font stack, zero JS framework; every page is one HTML file with one inline script
- Shared chrome: `assets/style.css` (design system) + `assets/common.js` (copy-to-clipboard, footer year, toast)
- JSON-LD on every page (SoftwareApplication / FAQPage / ItemList) for rich results
- The token counter loads `gpt-tokenizer` from esm.sh at runtime; if the CDN is unreachable it falls back to a documented approximation, so the tool never breaks
