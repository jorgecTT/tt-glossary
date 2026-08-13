#!/usr/bin/env python3
"""Regenerate index.json — the manifest every consumer resolves through.

This is the one URL a skill, an app, or a person should have to remember:

    https://raw.githubusercontent.com/jorgecTT/tt-glossary/main/index.json

Everything else in this repo is discoverable from it, so files can be renamed or
added without editing every consumer.

DELIBERATELY NO TIMESTAMP. A generated-at field would change on every run, so the
manifest would commit daily even when nothing moved — which destroys the
"commit only if changed" property that makes the git history a real change log.
Counts and hashes only change when the data changes, and the commit date then
gives you freshness for free.
"""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

# file -> (label, the key holding the records, one-line description)
DATASETS = {
    "glossary.json": (
        "glossary",
        "terms",
        "Approved EN->ES terms with type (product/ui/term), context and status. "
        "Authority: the Localization Auditor app. status=rejected is dropped at sync.",
    ),
    "corpus_full.json": (
        "corpus",
        "articles",
        "The full content index: Help Center articles + internal KAs, EN/ES/PT, "
        "including fullText and publishedUrl. Authority: the corpus Sheet.",
    ),
    "articles.json": (
        "articles",
        "articles",
        "translationKey -> published EN/ES/PT Help Center URLs.",
    ),
    "aliases.json": (
        "aliases",
        "aliases",
        "Old Help Center slugs that changed, so links can be rewritten.",
    ),
    "masterbook.json": (
        "masterbook",
        "articles",
        "Translation memory: previously approved ES content keyed by translationKey.",
    ),
    "glossary.md": (
        "glossary_md",
        None,
        "Human-readable glossary, grouped by type. Generated from glossary.json; "
        "also the offline fallback bundled in the translation skill.",
    ),
}

BASE = "https://raw.githubusercontent.com/jorgecTT/tt-glossary/main"


def count_records(path, key):
    """Number of records, or None for non-JSON files."""
    if key is None:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    if isinstance(data, dict):
        recs = data.get(key)
        if isinstance(recs, list):
            return len(recs)
        # fall back to a declared count if the key isn't a list
        if isinstance(data.get("count"), int):
            return data["count"]
        return None
    if isinstance(data, list):
        return len(data)
    return None


datasets = {}
for filename, (label, key, description) in sorted(DATASETS.items()):
    path = ROOT / filename
    if not path.exists():
        continue
    raw = path.read_bytes()
    entry = {
        "file": filename,
        "url": f"{BASE}/{filename}",
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "description": description,
    }
    n = count_records(path, key)
    if n is not None:
        entry["count"] = n
    datasets[label] = entry

manifest = {
    "name": "tt-glossary",
    "note": (
        "Manifest of every dataset mirrored here. Resolve this file first, then read "
        "the URL of the dataset you need. No timestamp by design -- see "
        "scripts/build_index.py. Repo name is historical: it mirrors the content "
        "corpus too, not just the glossary."
    ),
    "authorities": {
        "glossary": "The Localization Auditor app. Do not edit the legacy manual Sheet or these files by hand.",
        "corpus": "The corpus Sheet, fed by the Google Docs content index.",
    },
    "datasets": datasets,
}

out = ROOT / "index.json"
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"index.json: {len(datasets)} datasets")
for label, entry in datasets.items():
    n = entry.get("count")
    print(f"  {label:12} {entry['file']:20} {'' if n is None else str(n) + ' records':>14}  {entry['bytes']:>9,} bytes")
