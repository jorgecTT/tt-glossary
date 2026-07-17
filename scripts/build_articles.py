#!/usr/bin/env python3
"""Build articles.json — a faithful mirror of the url_index tab (EN/ES/PT published
URLs per translationKey+audience group), so the skill can resolve Help Center links
from GitHub (claude.ai's sandbox blocks docs.google.com and script.google.com).

Every row is kept (an ES-only or PT-only article has no urlEN but is still a valid
lookup target). Empty urlES on a row that HAS urlEN means: no published Spanish
translation (meaningful, not an error).

Usage: build_articles.py <url_index.csv>
"""
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "url_index.csv")

rows = list(csv.DictReader(open(src, encoding="utf-8")))


def g(r, k):
    return (r.get(k) or "").strip()


articles = [{
    "translationKey": g(r, "translationKey"),
    "audience": g(r, "audience"),
    "titleEN": g(r, "titleEN"),
    "titleES": g(r, "titleES"),
    "urlEN": g(r, "urlEN"),
    "urlES": g(r, "urlES"),
    "urlPT": g(r, "urlPT"),
    "notes": g(r, "notes"),
} for r in rows if g(r, "translationKey")]

out = {"ok": True, "count": len(articles), "articles": articles}
(ROOT / "articles.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
en = sum(1 for a in articles if a["urlEN"])
es = sum(1 for a in articles if a["urlEN"] and a["urlES"])
print(f"articles.json — {len(articles)} rows, {en} with urlEN, {es} EN+ES pairs")
