#!/usr/bin/env python3
"""
build_corpus.py — regenerate corpus_full.json from the "corpus" tab of the
Content Audit — Corpus Cache sheet.

Reads the sheet directly as CSV (the tab the Apps Script refreshes every night),
so the mirror stays in sync with daily HC/KA changes. One request, no /exec
batching. Run by .github/workflows/sync-corpus.yml; consumed by the
tt-content-index-auditor skill via raw.githubusercontent.

No timestamp is written into the file, so "commit if changed" only commits when
the corpus content actually changes.
"""

import csv
import io
import json
import os
import sys
import urllib.request

SHEET_ID = "16X-I4oT-W96XTwx1qs7ErqTAT6sJI7du3_vnYFp9MIo"
DEFAULT_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    "/gviz/tq?tqx=out:csv&sheet=corpus"
)
CSV_URL = os.environ.get("CORPUS_CSV_URL", DEFAULT_CSV_URL)
OUT_PATH = os.environ.get("CORPUS_OUT", "corpus_full.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
INT_FIELDS = ("wordCount", "lastUpdated")


def fetch_csv(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read().decode("utf-8", errors="replace")
    if data.lstrip().startswith("<!DOCTYPE") or data.lstrip().startswith("<html"):
        raise SystemExit("ERROR: got an HTML page, not CSV (sheet not accessible?).")
    return data


def main():
    text = fetch_csv(CSV_URL)
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or "docId" not in rows[0] or "fullText" not in rows[0]:
        raise SystemExit("ERROR: unexpected columns — is this the 'corpus' tab?")

    articles = []
    for r in rows:
        if not (r.get("docId") or "").strip():
            continue
        rec = {k: (v if v is not None else "") for k, v in r.items()}
        for f in INT_FIELDS:
            val = str(rec.get(f, "")).strip()
            if val.isdigit():
                rec[f] = int(val)
        articles.append(rec)

    with_bodies = sum(1 for a in articles if str(a.get("fullText", "")).strip())
    out = {"ok": True, "mode": "full", "count": len(articles), "articles": articles}
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    print(f"wrote {OUT_PATH}: {len(articles)} articles, {with_bodies} with bodies",
          file=sys.stderr)


if __name__ == "__main__":
    main()
