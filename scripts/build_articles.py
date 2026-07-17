#!/usr/bin/env python3
"""Build articles.json (EN↔ES published-URL link map) from the url_index CSV export.

The skill reads articles.json to swap English help.thumbtack.com links for their
Spanish equivalent when translating. Source: the `url_index` tab of the Corpus Cache,
rebuilt nightly by the Apps Script `buildUrlIndex`.
"""
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "url_index.csv")

rows = list(csv.DictReader(open(src, encoding="utf-8")))
articles = []
for r in rows:
    url_en = (r.get("urlEN") or "").strip()
    if not url_en:
        continue  # no English published URL → nothing to match on
    articles.append({
        "translationKey": (r.get("translationKey") or "").strip(),
        "audience": (r.get("audience") or "").strip(),
        "titleEN": (r.get("titleEN") or "").strip(),
        "titleES": (r.get("titleES") or "").strip(),
        "urlEN": url_en,
        "urlES": (r.get("urlES") or "").strip(),
        "notes": (r.get("notes") or "").strip(),
    })

out = {"ok": True, "count": len(articles), "articles": articles}
(ROOT / "articles.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
with_es = sum(1 for a in articles if a["urlES"])
print(f"wrote articles.json — {len(articles)} with urlEN, {with_es} with an ES pair")
