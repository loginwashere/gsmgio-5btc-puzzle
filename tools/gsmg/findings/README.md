# Canonical Findings Store

Each `P*.md` file is one canonical findings entry. Integer phase filenames use
five digits (`P00025.md`, `P00446.md`). Historical fractional phases use a
hyphen (`P00000-1.md` for Phase 0.1), and duplicate phase numbers retain their
stable suffix (`P00008-A.md`, `P00008-B.md`). Missing phase numbers do not get
placeholder files.

`_PREAMBLE.md` contains the text before the first phase. `manifest.json` is the
authoritative document order; filename sorting is not sufficient because the
historical log contains duplicate and out-of-sequence phase numbers.

`../FINDINGS.md` remains tracked as a generated compatibility artifact so old
links, GitHub heading anchors, and external tools continue to work. Do not edit
it directly.

## Add a new phase

1. Create the next five-digit file, including exactly one `## Phase N ...`
   heading.
2. Register it and rebuild the compatibility file:

   ```bash
   python3 tools/gsmg/findings_store.py register P00447.md
   python3 tools/gsmg/findings_store.py build
   python3 tools/gsmg/generate_phase_index.py
   ```

3. Verify drift and structure:

   ```bash
   python3 tools/gsmg/findings_store.py validate
   python3 tools/gsmg/findings_store.py build --check
   python3 tools/gsmg/generate_phase_index.py --check
   ```

Adding another occurrence of an existing phase number is intentionally not
automatic. It requires explicit `phase_id` markers and reviewed `-A`/`-B`
filenames so an existing stable identifier cannot silently change.
