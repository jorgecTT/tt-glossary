# tt-glossary

Public mirror of the data the Thumbtack content skills read at runtime — the approved
**English → Spanish (US/Latin American)** localization glossary **and** the full content
index (Help Center articles + internal KAs).

> The repo name is historical. It started as glossary-only and now mirrors the corpus
> too. It isn't renamed because every consumer hardcodes these URLs, and renaming would
> break all of them at once.

## Start here: `index.json`

**One URL to remember:**

```
https://raw.githubusercontent.com/jorgecTT/tt-glossary/main/index.json
```

It lists every dataset with its URL, record count, byte size, and sha256, plus which
system is authoritative for it. Resolve the manifest first, then fetch the dataset you
need. That way files can be added or renamed without editing every consumer.

The manifest has **no timestamp on purpose.** A generated-at field would change every
run, so it would commit daily even when nothing moved — which destroys the "commit only
if changed" property that makes this repo's history a real change log. Counts and hashes
change only when the data changes, and the commit date then gives you freshness for
free.

## Why this mirror exists

Both stores live behind Google — a Google Sheet for the corpus, and an Apps Script
endpoint for the glossary. The skills need to read them at runtime, but **claude.ai's
sandbox blocks `script.google.com` and `docs.google.com`** (its egress allowlist permits
GitHub). Mirroring here is what makes the skills work on claude.ai as well as in Claude
Code.

## Datasets

| File | What it is |
|---|---|
| `glossary.json` | Approved EN→ES terms: `en`, `es`, `context`, `type` (`product` / `ui` / `term`), `status`. Fetched by the translation skills at runtime |
| `glossary.md` | The same glossary, human-readable and grouped by type. Also the offline fallback bundled in the translation skill's zip |
| `corpus_full.json` | The content index — every HC article and internal KA, EN/ES/PT, with `fullText` and `publishedUrl`. Read by `tt-content-index-auditor` |
| `articles.json` | `translationKey` → published EN/ES/PT Help Center URLs |
| `aliases.json` | Help Center slugs that changed, so old links can be rewritten |
| `masterbook.json` | Translation memory — previously approved Spanish, keyed by `translationKey` |
| `index.json` | The manifest above |

## Authority — where each thing is actually edited

This is the part that matters, and it is easy to get wrong because there are legacy
inputs lying around that look editable.

| Store | The one place it's edited |
|---|---|
| **Glossary** | **The Localization Auditor app.** It builds terms from audited articles, assigns each term's `type`, resolves conflicts, and accepts pasted batches. It is the authority — not the legacy manual Sheet |
| **Corpus** | The **corpus Sheet**, fed nightly from the Google Docs content index |

**Do not edit anything in this repo by hand.** `glossary.json`, `glossary.md`,
`corpus_full.json`, `articles.json`, `aliases.json`, `masterbook.json` and `index.json`
are all generated and will be silently overwritten on the next sync. `glossary.json`
carries a `_generated` field and `glossary.md` a `GENERATED` comment saying so.

**Do not edit the legacy manual glossary Sheet either.** It was the original seed import
and the Localization Auditor has since overridden several of its values — including
reclassifying terms as `product` and correcting Spanish. Editing it now produces changes
that appear to work and then don't.

## Syncs

| Workflow | When | What it rebuilds |
|---|---|---|
| `sync-glossary.yml` | daily 13:00 UTC + manual | `glossary.json`, `glossary.md`, `articles.json`, `aliases.json`, `masterbook.json`, `index.json` |
| `sync-corpus.yml` | daily 12:00 UTC (5am Pacific, after the nightly sheet update) + manual | `corpus_full.json`, `index.json` |

Both commit only if something changed. `glossary.json` drops any term with
`status=rejected` at sync time, so a rejected term never reaches a skill.

To publish a change immediately instead of waiting for the schedule: Actions tab → the
workflow → **Run workflow**.

## Consumers

- `tt-ai-translation-tool` and `tt-ai-translation-tool-alex` — glossary, articles,
  aliases, masterbook
- `tt-content-index-auditor` — corpus (via `scripts/corpus_client.py`, mirror-first with
  the Apps Script endpoint as fallback)
- The Localization Auditor app itself

Maintainer: Jorge Cardona · jcardona@thumbtack.com
