#!/usr/bin/env python3
"""Build masterbook.json — approved Spanish article text (translation memory).

For each PUBLISHED Spanish article (a url_index row with a urlES), pull its approved
fullText from the Apps Script (mode=full) and store it keyed by translationKey/topic.
The skill uses this to reuse approved phrasing, not just glossary terms.

Usage: build_masterbook.py <exec_url> <url_index.csv>
"""
import csv
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
endpoint = sys.argv[1]
csv_path = sys.argv[2] if len(sys.argv) > 2 else str(ROOT / "url_index.csv")

rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
# Published ES only: has a published urlES and a docIdES to fetch.
id2meta = {}
for r in rows:
    did = (r.get("docIdES") or "").strip()
    if (r.get("urlES") or "").strip() and did:
        id2meta.setdefault(did, {
            "translationKey": (r.get("translationKey") or "").strip(),
            "audience": (r.get("audience") or "").strip(),
            "titleES": (r.get("titleES") or "").strip(),
            "urlES": (r.get("urlES") or "").strip(),
        })

ids = list(id2meta)


def fetch_full(batch):
    q = urllib.parse.urlencode({"mode": "full", "ids": ",".join(batch)})
    req = urllib.request.Request(endpoint + "?" + q, headers={"User-Agent": "tt-masterbook-sync"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp).get("articles", [])


articles = []
BATCH = 15
for i in range(0, len(ids), BATCH):
    batch = ids[i:i + BATCH]
    for a in fetch_full(batch):
        meta = id2meta.get(a.get("docId"), {})
        articles.append({
            "translationKey": meta.get("translationKey") or (a.get("translationKey") or "").strip(),
            "audience": meta.get("audience") or (a.get("audience") or "").strip(),
            "titleES": meta.get("titleES") or (a.get("title") or "").strip(),
            "urlES": meta.get("urlES", ""),
            "topicId": (a.get("topicId") or "").strip(),
            "summary": (a.get("summary") or "").strip(),
            "fullText": (a.get("fullText") or "").strip(),
        })
    time.sleep(0.4)

out = {"ok": True, "count": len(articles), "articles": articles}
(ROOT / "masterbook.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
kb = len((ROOT / "masterbook.json").read_bytes()) / 1024
print(f"masterbook.json — {len(articles)} ES articles, {kb:.0f} KB")
