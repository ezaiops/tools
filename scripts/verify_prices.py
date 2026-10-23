#!/usr/bin/env python3
"""Cross-check scripts/models.json prices against OpenRouter's public model feed.

Read-only: never writes models.json. Exit code 1 when drift is found, so it can
be wired into CI later without changing anything today.

Usage:
    python scripts/verify_prices.py          # report only
    python scripts/verify_prices.py --strict # also fail on unmatched models
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "scripts" / "models.json"
FEED = "https://openrouter.ai/api/v1/models"

# Our slug -> OpenRouter slug, for models whose naming differs.
ALIASES = {
    "gpt-6-1-sol": "openai/gpt-6.1-sol",
    "gpt-5-6-sol": "openai/gpt-5.6-sol",
    "gpt-5-6-terra": "openai/gpt-5.6-terra",
    "gpt-5-6-luna": "openai/gpt-5.6-luna",
    "claude-fable-5-1": "anthropic/claude-fable-5.1",
    "claude-opus-5-5": "anthropic/claude-opus-5.5",
    "claude-sonnet-5-5": "anthropic/claude-sonnet-5.5",
    "claude-haiku-4-5": "anthropic/claude-haiku-4.5",
    "claude-haiku-5-5": "anthropic/claude-haiku-5.5",
    "gemini-3-1-pro": "google/gemini-3.1-pro",
    "gemini-3-8-flash": "google/gemini-3.8-flash",
    "gemini-3-5-flash-lite": "google/gemini-3.5-flash-lite",
    "grok-4-7": "x-ai/grok-4.7",
    "grok-4-5": "x-ai/grok-4.5",
    "grok-4-3": "x-ai/grok-4.3",
    "deepseek-v4-1-flash": "deepseek/deepseek-v4.1-flash",
    "deepseek-v4-pro": "deepseek/deepseek-v4-pro",
    "glm-5-3": "z-ai/glm-5.3",
    "glm-5-3-flash": "z-ai/glm-5.3-flash",
    "glm-5-3-flashx": "z-ai/glm-5.3-flashx",
    "kimi-k3": "moonshotai/kimi-k3",
    "kimi-k2-7-code": "moonshotai/kimi-k2.7-code",
    "minimax-m3": "minimax/minimax-m3",
    "mimo-v2-6-pro": "xiaomi/mimo-v2.6-pro",
    "mimo-v2-6-flash": "xiaomi/mimo-v2.6-flash",
    "mistral-large-4": "mistralai/mistral-large-4-0",
    "mistral-large-3": "mistralai/mistral-large-3",
    "mistral-medium-3-5": "mistralai/mistral-medium-3-5",
    "mistral-small-4": "mistralai/mistral-small-4",
}

# Tolerances: cents per 1M tokens. Outputs move in coarser steps than inputs.
TOL_IN = 0.02
TOL_OUT = 0.05


def fetch():
    with urllib.request.urlopen(FEED, timeout=30) as r:
        return json.load(r)["data"]


def build_index(feed):
    idx = {}
    for m in feed:
        mid = m["id"]
        if mid.endswith(":batch") or mid.endswith(":free"):
            continue
        idx[mid] = m
        idx.setdefault(mid.split("/", 1)[-1], m)
    return idx


def price(m):
    p = m.get("pricing") or {}
    return float(p.get("prompt") or 0) * 1e6, float(p.get("completion") or 0) * 1e6


def main():
    strict = "--strict" in sys.argv
    data = json.loads(MODELS.read_text(encoding="utf-8"))
    feed = build_index(fetch())

    drift, missing, ok = [], [], 0
    for m in data["models"]:
        key = ALIASES.get(m["id"], m["id"])
        hit = feed.get(key)
        if not hit:
            missing.append(m["id"])
            continue
        pin, pout = price(hit)
        # Aggregators often quote the peak rate for time-priced models, so accept
        # either the off-peak or the peak pair instead of flagging a false drift.
        mult = (m.get("time_pricing") or {}).get("peak_multiplier", 2)
        candidates = [(m["input"], m["output"]), (m["input"] * mult, m["output"] * mult)]
        if not any(abs(pin - ci) <= TOL_IN and abs(pout - co) <= TOL_OUT
                   for ci, co in candidates):
            drift.append((m["id"], m["input"], m["output"], pin, pout))

    total = len(data["models"])
    print(f"models.json: {total} models, verified {data.get('updated')}")
    print(f"matched {total - len(missing)}, drifted {len(drift)}, unmatched {len(missing)}")

    if drift:
        print("\nDRIFT (ours -> feed, USD per 1M):")
        for mid, i, o, pi, po in drift:
            print(f"  {mid:<24} in {i:>7.2f} -> {pi:>7.2f}   out {o:>7.2f} -> {po:>7.2f}")
    if missing:
        print("\nNOT FOUND in feed (add an alias or check the slug):")
        for mid in missing:
            print(f"  {mid}")

    if drift or (strict and missing):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
