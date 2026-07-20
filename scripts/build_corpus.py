#!/usr/bin/env python3
"""
build_corpus.py — regenerate corpus_full.json from the "corpus" tab of the
Content Audit — Corpus Cache sheet, enriched with a published-article URL per row.

Reads the sheet directly as CSV (the tabs the Apps Script refreshes every night),
so the mirror stays in sync with daily HC/KA changes. Consumed by the
tt-content-index-auditor skill via raw.githubusercontent.

Every record gets a `publishedUrl` (the live article) so the skill can show two
links per article — published + Drive doc — without any runtime joins:
  * Drive doc  = the corpus `url` field (docs.google.com/document/...). NEVER the live link.
  * HC live    = url_index (articles.json) by translationKey + language (urlEN/ES/PT).
  * KA live    = ka_url_index tab by docId → salesforceUrl (Salesforce Lightning).
KA rows carry `publishedUrlNote` when ka_url_index flags a missing/absent link.
No timestamp is written, so "commit if changed" only fires on real changes.
"""

import csv
import io
import json
import os
import sys
import urllib.request

SHEET_ID = "16X-I4oT-W96XTwx1qs7ErqTAT6sJI7du3_vnYFp9MIo"
GVIZ = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet="
CORPUS_CSV_URL = os.environ.get("CORPUS_CSV_URL", GVIZ + "corpus")
KA_URL_INDEX_CSV = os.environ.get("KA_URL_INDEX_CSV", GVIZ + "ka_url_index")
ARTICLES_JSON = os.environ.get("ARTICLES_JSON", "articles.json")  # url_index mirror (HC live URLs)
OUT_PATH = os.environ.get("CORPUS_OUT", "corpus_full.json")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
INT_FIELDS = ("wordCount", "lastUpdated")
LANG_COL = {"EN": "urlEN", "ES": "urlES", "PT": "urlPT"}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read().decode("utf-8", errors="replace")
    if data.lstrip().startswith("<!DOCTYPE") or data.lstrip().startswith("<html"):
        raise SystemExit("ERROR: got an HTML page, not CSV (sheet not accessible?).")
    return data


def load_csv(url):
    return list(csv.DictReader(io.StringIO(fetch(url))))


def norm(s):
    return (s or "").strip().lower()


def main():
    # 1) corpus
    rows = load_csv(CORPUS_CSV_URL)
    if not rows or "docId" not in rows[0] or "fullText" not in rows[0]:
        raise SystemExit("ERROR: unexpected columns — is this the 'corpus' tab?")

    # 2) HC live URLs from url_index (articles.json), keyed by translationKey
    hc_idx = {}
    try:
        with open(ARTICLES_JSON, encoding="utf-8") as fh:
            for e in json.load(fh).get("articles", []):
                tk = norm(e.get("translationKey"))
                if tk:
                    hc_idx.setdefault(tk, e)
    except FileNotFoundError:
        print(f"WARN: {ARTICLES_JSON} not found — HC publishedUrl will be blank",
              file=sys.stderr)

    # 3) KA live URLs from ka_url_index, keyed by docId (and title as fallback)
    ka_by_id, ka_by_title = {}, {}
    for r in load_csv(KA_URL_INDEX_CSV):
        did = (r.get("docId") or "").strip()
        if did:
            ka_by_id[did] = r
        t = norm(r.get("title"))
        if t:
            ka_by_title.setdefault(t, r)

    articles = []
    for r in rows:
        did = (r.get("docId") or "").strip()
        if not did:
            continue
        rec = {k: (v if v is not None else "") for k, v in r.items()}
        for f in INT_FIELDS:
            if str(rec.get(f, "")).strip().isdigit():
                rec[f] = int(rec[f])

        pub, note = "", ""
        lane = (rec.get("lane") or "").strip().upper()
        if lane == "HC":
            e = hc_idx.get(norm(rec.get("translationKey")))
            if e:
                pub = (e.get(LANG_COL.get((rec.get("language") or "EN").upper(), "urlEN")) or "").strip()
        elif lane == "KA":
            e = ka_by_id.get(did) or ka_by_title.get(norm(rec.get("title")))
            if e:
                pub = (e.get("salesforceUrl") or "").strip()
                note = (e.get("notes") or "").strip()
        rec["publishedUrl"] = pub
        if note:
            rec["publishedUrlNote"] = note
        articles.append(rec)

    hc = [a for a in articles if (a.get("lane") or "").upper() == "HC"]
    ka = [a for a in articles if (a.get("lane") or "").upper() == "KA"]
    out = {"ok": True, "mode": "full", "count": len(articles), "articles": articles}
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    print(f"wrote {OUT_PATH}: {len(articles)} articles "
          f"(HC live {sum(1 for a in hc if a['publishedUrl'])}/{len(hc)}, "
          f"KA live {sum(1 for a in ka if a['publishedUrl'])}/{len(ka)})", file=sys.stderr)


if __name__ == "__main__":
    main()
