#!/usr/bin/env python3
"""Regenerate glossary.md (human-readable, grouped) from glossary.json.

glossary.json is the machine-readable mirror the skills fetch at runtime.
glossary.md is the offline fallback bundled inside the skill's zip.
Both are kept in sync by the sync-glossary GitHub Action.

Since Nov 16, 2026 each term may also carry (from the glossary_extra tab):
kind (product / ui / term / category), app (exact UI form), variations,
doNotUse and contextEn. They are shown when present.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "glossary.json").read_text())
terms = [t for t in data["terms"] if (t.get("status") or "").lower() not in ("rejected", "conflict")]


def esc(s):
    return (s or "").strip().replace("\n", " ")


def kind(t):
    k = (t.get("kind") or "").lower()
    if k in ("product", "ui", "term", "category"):
        return k
    ty = (t.get("type") or "").lower()
    return ty if ty in ("product", "ui") else "term"


def extras(t):
    parts = []
    if esc(t.get("app")) and kind(t) == "term":
        parts.append(f"In the app: `{esc(t['app'])}`")
    if esc(t.get("variations")):
        parts.append(f"Variations: {esc(t['variations'])}")
    if esc(t.get("doNotUse")):
        parts.append(f"Do not use: {esc(t['doNotUse'])}")
    return ("  " + " · ".join(parts)) if parts else ""


def ctx(t):
    return f"  — _{esc(t.get('context'))}_" if esc(t.get("context")) else ""


def by(k):
    return sorted([t for t in terms if kind(t) == k], key=lambda t: (t.get("en") or "").lower())


prod, ui, spec, cat = by("product"), by("ui"), by("term"), by("category")

out = []
out.append(
    "<!-- GENERATED FILE — DO NOT EDIT. Produced by scripts/build_md.py from "
    "glossary.json on every sync; hand edits are silently overwritten. "
    "Add NEW terms as rows in the manual glossary Sheet (tab gid=1113586630); "
    "change EXISTING terms in the Localization Auditor app, whose value wins; "
    "app labels, variations, do-not-use and English context live in the "
    "glossary_extra tab of the corpus sheet. -->"
)
out.append("")
out.append("# Thumbtack ES-US Glossary (approved)")
out.append("")
out.append(
    f"Offline fallback snapshot of {len(terms)} approved terms (machine source: "
    "`glossary.json`, synced from the Apps Script endpoint). Product/UI/specific "
    "terms must stay consistent; ordinary words not listed here vary by context. "
    "\"Do not use\" versions are never allowed, even if older articles have them."
)
out.append("")
out.append("")
out.append(f"## PRODUCT — never translate, keep English exactly ({len(prod)})")
out.append("")
for t in prod:
    out.append(f"- **{esc(t['en'])}** → keep as `{esc(t['en'])}`{ctx(t)}{extras(t)}")
out.append("")
out.append(f'## UI — render as EnglishLabel (“Traducción”) ({len(ui)})')
out.append("")
for t in ui:
    form = esc(t.get("app")) or f"{esc(t['en'])} (“{esc(t['es'])}”)"
    out.append(f"- **{esc(t['en'])}** → `{form}`{ctx(t)}{extras(t)}")
out.append("")
out.append(f"## TERMS / specific vocabulary — canonical ES when used in the sense in Context ({len(spec)})")
out.append("")
for t in spec:
    out.append(f"- **{esc(t['en'])}** → {esc(t['es'])}{ctx(t)}{extras(t)}")
out.append("")
if cat:
    out.append(f"## SERVICE CATEGORIES — names of types of service ({len(cat)})")
    out.append("")
    for t in cat:
        out.append(f"- **{esc(t['en'])}** → {esc(t['es'])}{extras(t)}")
    out.append("")

(ROOT / "glossary.md").write_text("\n".join(out))
print(f"wrote glossary.md — product:{len(prod)} ui:{len(ui)} terms:{len(spec)} categories:{len(cat)}")
