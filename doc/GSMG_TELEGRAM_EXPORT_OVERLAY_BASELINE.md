# GSMG Telegram Export Overlay Baseline

The project's complete Telegram baseline remains
`ChatExport_2026-07-26`: 57,729 messages from 2019-04-20 through
2026-07-26. It must not be replaced by `ChatExport_2026-08-30`, because the
latter is only a partial window: 1,722 messages from 2026-08-09 through
2026-08-30.

The reproducible current view is instead a latest-copy-wins overlay of:

| Source | Rows | Message-ID span | Date span |
|---|---:|---:|---|
| `ChatExport_2026-07-26` | 57,729 | 1–67,267 | 2019-04-20–2026-07-26 |
| `ChatExport_2026-08-09 (1)` | 1,026 | 67,203–68,343 | 2026-07-25–2026-08-09 |
| `ChatExport_2026-08-30` | 1,722 | 68,280–70,186 | 2026-08-09–2026-08-30 |

The overlaps bridge both boundaries. After deduplication the overlay contains
60,375 messages through 2026-08-30. There are 102 repeated rows and ten IDs
whose exported dictionaries differ (`67203`, `67230`, `67232`, `67251`,
`67257`, `67259`, `68320`, `68332`, `68333`, `68342`), consistent with later
edits, reactions, or export metadata. The later export deterministically wins;
no conflicting row is silently counted twice.

This supplements rather than changes
`telegram_export_manifest.py`: old phase tests importing
`DEFAULT_EXPORT_DIR` continue to see the frozen full July archive. New work
that needs post-July messages should use:

```sh
python3 tools/gsmg/telegram_export_overlay_manifest.py --self-test
python3 tools/gsmg/telegram_export_overlay_manifest.py
```

The generated JSONL remains under `_work/` and is not a tracked evidence
artifact. The source exports remain external local evidence; phase documents
must cite the specific export date and message IDs they use.
