# tt-glossary

Public mirror of Thumbtack's approved **English → Spanish (US/Latin American)**
localization glossary, used by the **TT AI Translation Tool** skill.

## Why this exists

The glossary's source of truth is a Google Sheet, exposed through a public Apps Script
endpoint. The translation skill needs to read it at runtime — but the claude.ai
sandbox blocks outbound requests to `script.google.com` (it only allows a small
allowlist that includes GitHub). This repo mirrors the glossary to GitHub so the skill
can fetch it from an allowed host.

## Files

- **`glossary.json`** — machine-readable, fetched by the skill at runtime:
  `{ "ok": true, "count": N, "terms": [ { "en", "es", "context", "type" }, ... ] }`
- **`glossary.md`** — human-readable, grouped by term type; also the offline fallback
  bundled inside the skill.
- **`.github/workflows/sync-glossary.yml`** — runs daily (and on demand), pulls the
  latest terms from the Apps Script endpoint, and commits any changes.

## Editing

Do **not** edit `glossary.json` / `glossary.md` by hand — they are overwritten by the
sync job. Edit the source Google Sheet; changes appear here within a day (or trigger
the workflow manually from the Actions tab).

Maintainer: Jorge Cardona · jcardona@thumbtack.com
