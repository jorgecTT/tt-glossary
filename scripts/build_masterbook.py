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


# The Apps Script /exec 302-redirects to googleusercontent, and that target rejects
# non-browser clients — which is why a plain "tt-masterbook-sync" UA intermittently got
# HTTP 404 and killed the whole sync. corpus_client.py has always used a browser UA,
# retried, and batched `full` by 8 for the same reason; match it.
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
RETRIES = 2


def fetch_full(batch):
    q = urllib.parse.urlencode({"mode": "full", "ids": ",".join(batch)})
    url = endpoint + "?" + q
    last = None
    for attempt in range(RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": BROWSER_UA,
                "Accept": "application/json, text/plain, */*",
            })
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            if raw.lstrip().startswith("<"):
                raise RuntimeError("endpoint returned HTML instead of JSON")
            return json.loads(raw).get("articles", [])
        except Exception as e:  # noqa: BLE001
            last = e
            if attempt < RETRIES:
                time.sleep(2.0 * (attempt + 1))
    raise RuntimeError("giving up on batch after %d tries: %s" % (RETRIES + 1, last))


articles = []
failed_batches = 0
BATCH = 8  # >8 makes the endpoint return a 1MB HTML error page instead of JSON
for i in range(0, len(ids), BATCH):
    batch = ids[i:i + BATCH]
    try:
        got = fetch_full(batch)
    except Exception as e:  # noqa: BLE001
        failed_batches += 1
        print("WARNING: batch %d failed, skipping it: %s" % (i // BATCH + 1, e))
        continue
    for a in got:
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

# NEVER fail the sync over this. masterbook is translation memory — nice to have, and
# stale is far better than blocking glossary.json, articles.json and index.json from
# publishing at all, which is what a hard exit here used to do (the commit step runs
# after this one, so one flaky fetch stopped everything).
target = len(ids)
dest = ROOT / "masterbook.json"
enough = target == 0 or len(articles) >= 0.8 * target

if enough:
    out = {"ok": True, "count": len(articles), "articles": articles}
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    kb = len(dest.read_bytes()) / 1024
    print(f"masterbook.json — {len(articles)}/{target} ES articles, {kb:.0f} KB"
          + (f" ({failed_batches} batches skipped)" if failed_batches else ""))
elif dest.exists():
    print(f"WARNING: only got {len(articles)}/{target} ES articles "
          f"({failed_batches} batches failed) — keeping the existing masterbook.json "
          f"rather than replacing it with a partial one. The rest of the sync continues.")
else:
    print(f"WARNING: only got {len(articles)}/{target} and there is no existing "
          f"masterbook.json — writing the partial build so the sync can continue.")
    out = {"ok": True, "count": len(articles), "partial": True, "articles": articles}
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2))
