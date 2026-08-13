#!/usr/bin/env python3
"""Regenerate glossary.md (human-readable, grouped) from glossary.json.

glossary.json is the machine-readable mirror the skill fetches at runtime.
glossary.md is the offline fallback bundled inside the skill's zip.
Both are kept in sync by the sync-glossary GitHub Action.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "glossary.json").read_text())
terms = data["terms"]


def esc(s):
    return (s or "").strip().replace("\n", " ")


prod = sorted([t for t in terms if t.get("type") == "product"], key=lambda t: (t.get("en") or "").lower())
ui = sorted([t for t in terms if t.get("type") == "ui"], key=lambda t: (t.get("en") or "").lower())
spec = sorted([t for t in terms if t.get("type") not in ("product", "ui")], key=lambda t: (t.get("en") or "").lower())

out = []
out.append(
    "<!-- GENERATED FILE — DO NOT EDIT. Produced by scripts/build_md.py from "
    "glossary.json on every sync; hand edits are silently overwritten. "
    "The glossary's authority is the Localization Auditor app — add or change terms "
    "there (including via its \"Paste terms from Claude\" input). -->"
)
out.append("")
out.append("# Thumbtack ES-US Glossary (approved)")
out.append("")
out.append(
    f"Offline fallback snapshot of {len(terms)} approved terms (machine source: "
    "`glossary.json`, synced from the Apps Script endpoint). Product/UI/specific "
    "terms must stay consistent; ordinary words not listed here vary by context."
)
out.append("")
out.append("")
out.append(f"## PRODUCT — never translate, keep English exactly ({len(prod)})")
out.append("")
for t in prod:
    out.append(f"- **{esc(t['en'])}** → keep as `{esc(t['en'])}`  — _{esc(t.get('context'))}_")
out.append("")
out.append(f'## UI — render as EnglishLabel ("Traducción") ({len(ui)})')
out.append("")
for t in ui:
    out.append(f"- **{esc(t['en'])}** → `{esc(t['en'])} (\"{esc(t['es'])}\")`  — _{esc(t.get('context'))}_")
out.append("")
out.append(f"## TERMS / specific vocabulary — canonical ES when used in the sense in Context ({len(spec)})")
out.append("")
for t in spec:
    out.append(f"- **{esc(t['en'])}** → {esc(t['es'])}  — _{esc(t.get('context'))}_")
out.append("")

(ROOT / "glossary.md").write_text("\n".join(out))
print(f"wrote glossary.md — product:{len(prod)} ui:{len(ui)} terms:{len(spec)}")
