#!/usr/bin/env python3
"""Build aliases.json — mirror of the slug_aliases tab (old Help Center slug → current
slug), so the skill can resolve renamed/stale links from GitHub.

Rows with an empty currentSlug are FAILED resolution attempts (soft-404 etc.) — kept
so the skill can recognize a known-unresolvable slug and not retry it.

Usage: build_aliases.py <slug_aliases.csv>
"""
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
src = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "slug_aliases.csv")

rows = list(csv.DictReader(open(src, encoding="utf-8")))


def g(r, k):
    return (r.get(k) or "").strip()


aliases = [{
    "oldSlug": g(r, "oldSlug"),
    "currentSlug": g(r, "currentSlug"),
    "notes": g(r, "notes"),
} for r in rows if g(r, "oldSlug")]

out = {"ok": True, "count": len(aliases), "aliases": aliases}
(ROOT / "aliases.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
resolved = sum(1 for a in aliases if a["currentSlug"])
print(f"aliases.json — {len(aliases)} rows, {resolved} resolved, {len(aliases) - resolved} failed/logged")
