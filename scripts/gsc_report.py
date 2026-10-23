#!/usr/bin/env python3
"""Summarise Google Search Console CSV exports (English or Chinese UI).

    python scripts/gsc_report.py ~/Downloads/gsc-export
    python scripts/gsc_report.py ~/Downloads/Pages.csv

Buckets page rows by URL prefix so you can see which content type earns
impressions, flags ?lang= parameter duplicates, lists striking-distance
queries (rank 5-20), and shows the daily impression trend.
"""
import csv
import sys
from pathlib import Path

BUCKETS = [
    ("/models/", "model pages"),
    ("/tools/", "tool pages"),
    ("/en/posts/", "blog posts (en)"),
    ("/posts/", "blog posts (zh)"),
]

EN = {
    "clicks": ("click",),
    "impressions": ("impression",),
    "ctr": ("ctr",),
    "position": ("position",),
    "page": ("page", "url"),
    "query": ("quer", "keyword"),
    "date": ("date",),
    "country": ("countr",),
    "device": ("device",),
}
ZH = {
    "clicks": ("点击",),
    "impressions": ("展示", "曝光"),
    "ctr": ("点击率",),
    "position": ("排名",),
    "page": ("网页", "页面"),
    "query": ("查询", "关键词"),
    "date": ("日期",),
    "country": ("国家",),
    "device": ("设备",),
}


def num(value):
    s = str(value or "").strip().replace(",", "").replace("%", "")
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def read_rows(path):
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with open(path, newline="", encoding=enc) as f:
                return list(csv.reader(f))
        except UnicodeDecodeError:
            continue
    return []


DISTINCT = [
    ("page", EN["page"] + ZH["page"]),
    ("query", EN["query"] + ZH["query"]),
    ("date", EN["date"] + ZH["date"]),
    ("country", EN["country"] + ZH["country"]),
    ("device", EN["device"] + ZH["device"]),
]
METRICS = [
    ("impressions", EN["impressions"] + ZH["impressions"]),
    ("clicks", EN["clicks"] + ZH["clicks"]),
    ("ctr", EN["ctr"] + ZH["ctr"]),
    ("position", EN["position"] + ZH["position"]),
]


def classify(header):
    """Return (kind, index map, dimension label).

    Two passes: distinctive columns first, because a Chinese header such as
    "排名靠前的网页" contains both "排名" (position) and "网页" (page), and a
    naive scan would claim it as the position column.
    """
    if not header:
        return None, {}, ""
    low = [h.strip().lower() for h in header]
    idx, used = {}, set()
    for field, keys in DISTINCT + METRICS:
        for i, h in enumerate(low):
            if i in used:
                continue
            if any(k in h for k in keys):
                idx[field] = i
                used.add(i)
                break
    if "clicks" not in idx and "impressions" not in idx:
        return None, idx, header[0]
    if "query" in idx:
        return "query", idx, "query"
    if "page" in idx:
        return "page", idx, "page"
    for dim in ("date", "country", "device"):
        if dim in idx:
            return dim, idx, dim
    return None, idx, header[0]


def bucket(url):
    for prefix, name in BUCKETS:
        if prefix in url:
            return name
    return "hub / other pages"


def main():
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").expanduser()
    files = [target] if target.is_file() else sorted(target.glob("*.csv"))
    if not files:
        print(f"no CSV files in {target}")
        return 1

    data = {}
    for f in files:
        rows = read_rows(f)
        if len(rows) < 2:
            continue
        kind, idx, _ = classify(rows[0])
        if kind:
            data.setdefault(kind, (rows[1:], idx))

    print(f"{target.name}: {len(files)} file(s), sections: {', '.join(sorted(data)) or 'none'}")

    if "page" in data:
        rows, idx = data["page"]
        stats, param = {}, {"with": 0, "without": 0}
        for r in rows:
            if len(r) <= max(idx.values()):
                continue
            url = r[idx["page"]]
            b = bucket(url)
            s = stats.setdefault(b, {"impr": 0.0, "clicks": 0.0, "pos": [], "n": 0})
            impr = num(r[idx["impressions"]])
            s["impr"] += impr
            s["clicks"] += num(r[idx["clicks"]])
            if impr > 0 and "position" in idx:
                s["pos"].append((num(r[idx["position"]]), impr))
            s["n"] += 1
            param["with" if "?lang=" in url else "without"] += 1

        total = sum(s["impr"] for s in stats.values()) or 1
        print("\nBY CONTENT TYPE")
        print(f"  {'bucket':<22}{'urls':>5}{'impr':>8}{'share':>7}{'clicks':>7}{'avg pos':>9}")
        for name, s in sorted(stats.items(), key=lambda kv: -kv[1]["impr"]):
            pos = "-"
            if s["pos"]:
                w = sum(x for _, x in s["pos"])
                pos = f"{sum(p * x for p, x in s['pos']) / w:.1f}" if w else "-"
            print(f"  {name:<22}{s['n']:>5}{int(s['impr']):>8}{s['impr'] / total:>6.0%}"
                  f"{int(s['clicks']):>7}{pos:>9}")

        if param["with"]:
            print(f"\n  ?lang= URLs in report: {param['with']} "
                  f"(indexed separately from {param['without']} clean URLs)")

        zero = [r for r in rows if len(r) > max(idx.values())
                and num(r[idx["impressions"]]) == 0]
        if zero:
            print(f"  pages with zero impressions: {len(zero)}")

        print("\nTOP PAGES")
        ranked = [r for r in rows if len(r) > max(idx.values())]
        ranked.sort(key=lambda r: -num(r[idx["impressions"]]))
        for r in ranked[:12]:
            print(f"  {int(num(r[idx['impressions']])):>6} impr  pos {num(r[idx['position']]):>5.1f}"
                  f"  {r[idx['page']].replace('https://', '')[:62]}")

    if "query" in data:
        rows, idx = data["query"]
        qs = []
        for r in rows:
            if len(r) <= max(idx.values()):
                continue
            q = r[idx["query"]].replace("\n", " ").strip()
            if q:
                qs.append((num(r[idx["impressions"]]), num(r[idx["position"]]), q))
        qs.sort(key=lambda t: (-t[0], t[1]))

        print("\nTOP QUERIES")
        for impr, pos, q in qs[:12]:
            print(f"  {int(impr):>6} impr  pos {pos:>5.1f}  {q[:58]}")

        near = [(i, p, q) for i, p, q in qs if 4.5 <= p <= 20.5]
        near.sort(key=lambda t: (-t[0], t[1]))
        print(f"\nSTRIKING DISTANCE (rank 5-20): {len(near)} queries")
        for impr, pos, q in near[:15]:
            print(f"  {int(impr):>6} impr  pos {pos:>5.1f}  {q[:58]}")

    if "date" in data:
        rows, idx = data["date"]
        series = [(r[idx["date"]], num(r[idx["impressions"]])) for r in rows
                  if len(r) > max(idx.values())]
        series.sort()
        if series:
            half = max(1, len(series) // 2)
            first = sum(v for _, v in series[:half])
            second = sum(v for _, v in series[half:])
            print(f"\nTREND {series[0][0]} to {series[-1][0]}")
            print(f"  first half {int(first)} impr, second half {int(second)} impr", end="")
            if first:
                print(f"  ({(second - first) / first:+.0%})")
            else:
                print("  (no baseline)")

    if "country" in data:
        rows, idx = data["country"]
        rows = [r for r in rows if len(r) > max(idx.values())]
        rows.sort(key=lambda r: -num(r[idx["impressions"]]))
        print("\nTOP COUNTRIES")
        for r in rows[:5]:
            print(f"  {int(num(r[idx['impressions']])):>6} impr  {r[0][:30]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
