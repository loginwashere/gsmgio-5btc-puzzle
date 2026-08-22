#!/usr/bin/env python3
"""Build a directed phase-citation graph from tools/gsmg/FINDINGS.md.

Nodes are FINDINGS.md phases (by stable ID, reusing generate_phase_index.py's
numbering). An edge `A -> B` means phase A's body text mentions "Phase B"
(or "Phases B, C, ..."). This is a heuristic text-mining pass over inline
cross-references, not a semantic dependency analysis -- it does not know
whether a mention is load-bearing ("this result requires Phase 32's oracle")
or incidental ("as also noted in Phase 32"). It exists to answer one
practical question: which phases are cited by the most *other* phases, so a
follow-up code-vs-premise review (or any other re-audit) can start from the
most heavily built-upon phases and work outward toward leaves, instead of
working in raw numeric order.

Disambiguation: this project's own sequential "FINDINGS Phase N" numbering
collides with the unrelated, fixed "puzzle Phase 2/3/3.2" AES-256-CBC
boundary numbering used throughout the corpus (see
tools/gsmg/blob_chronology_dependency_graph.py's docstring for the same
distinction). "Phase 3.2" and "Phase 3.2.1" are never a FINDINGS heading and
are always dropped. A bare "Phase 2" / "Phase 3" (no "solved"/"puzzle"
prefix) is resolved by scanning a +-160 char window around the mention: an
explicit "FINDINGS Phase N" / "this project's Phase N" signal always wins;
otherwise puzzle-only vocabulary (ciphertext, chess FEN, SalPhaseIon, ...)
or co-occurrence with "Phase 3.2" marks it as the puzzle boundary. Manual
review of every mention in the 2026-08-22 pass found this resolves the
large majority correctly (see doc/GSMG_PHASE_CITATION_GRAPH.md); anything
neither signal touches is left in `ambiguous` for manual review rather than
guessed.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_phase_index import (  # noqa: E402
    HEADING_RE, parse_phases, assign_stable_ids, PhaseIdError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FINDINGS = REPO_ROOT / "tools" / "gsmg" / "FINDINGS.md"
GRAPH_JSON = REPO_ROOT / "tools" / "gsmg" / "phase_citation_graph.json"
REPORT_MD = REPO_ROOT / "doc" / "GSMG_PHASE_CITATION_GRAPH.md"

PUZZLE_PREFIX_RE = re.compile(r"(solved|puzzle)\s+$", re.IGNORECASE)
# "Phase" or "Phases" followed by a number cluster (list/range of numbers).
# Continuation numbers (after the first) may not start with "0": no FINDINGS
# phase is ever bare "0" (only "0.1"/"0.2"), so a comma/slash-continuation
# landing on "0" is always a false hit off an adjacent ratio/count like
# "(Phase 109, 0/3 candidates)" -- see self-test for the caught regression.
ANCHOR_RE = re.compile(
    r"\bPhases?\s+([0-9]+(?:\.[0-9]+)?"
    r"(?:\s*(?:,|/|&|-|and)\s*[1-9][0-9]*(?:\.[0-9]+)?)*)"
)
NUMBER_RE = re.compile(r"[0-9]+(?:\.[0-9]+)?")
ALWAYS_DROP = {"3.2", "3.2.1"}

# Vocabulary that only ever co-occurs with the *puzzle's* fixed Phase
# 2/3/3.2 AES boundary, never with this project's own FINDINGS phases, per
# manual review of every ambiguous mention in the 2026-08-22 pass (see
# doc/GSMG_PHASE_CITATION_GRAPH.md).
PUZZLE_VOCAB_RE = re.compile(
    r"ciphertext|plaintext|decrypt|\bAES\b|\bblob\b|textarea|chess\s+FEN|"
    r"URL\s+slug|checkerboard|SalPhaseIon|Cosmic\s+Duality|\bcausality\b|"
    r"\bSafenet\b|\bHSM\b|Merovingian|GSMG_PUZZLE|solve\s+chain|solved\s+chain|"
    r"already\s+solved|walkthrough|this\s+puzzle|seven\s+parts|seven\s+known",
    re.IGNORECASE,
)
PUZZLE_COOCCURRENCE_RE = re.compile(r"Phase\s+3\.2\b|\b3\.2\.\d\b")
# "Phases 1-2 of [some other doc]" is that other document's own internal
# step numbering riding the word "Phase", not a FINDINGS/puzzle reference at
# all (e.g. a plan doc's "Implemented Phases 1-2 of ..."). Treat as noise.
FOREIGN_DOC_STEP_RE = re.compile(r"^\s*of\s+(the\s+)?(plan\b|\[?doc/)", re.IGNORECASE)
# The corpus already sometimes spells this out explicitly; treat that as an
# authoritative override even if puzzle vocabulary also appears nearby.
FINDINGS_SIGNAL_RE = re.compile(
    r"FINDINGS\s+Phase|this\s+project'?s\s+Phase|this\s+project'?s\s+[\s\S]{0,20}writeup",
    re.IGNORECASE,
)
CONTEXT_WINDOW = 160


def expand_cluster(cluster_text):
    """Split a captured number cluster ("32, 58 and 97", "356-359",
    "106/94-95") into individual number-strings, expanding integer hyphen
    ranges (both sides plain integers, span <= 20) and leaving everything
    else as discrete tokens."""
    tokens = re.split(r"\s*(?:,|/|&|\band\b)\s*", cluster_text.strip())
    out = []
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        range_match = re.fullmatch(r"([0-9]+)\s*-\s*([0-9]+)", tok)
        if range_match:
            lo, hi = int(range_match.group(1)), int(range_match.group(2))
            if 0 <= hi - lo <= 20:
                out.extend(str(n) for n in range(lo, hi + 1))
                continue
        out.append(tok)
    return out


def build_line_spans(lines):
    """Return list of (start_line_idx, end_line_idx_exclusive) aligned 1:1
    with parse_phases()'s row order (both iterate headings in file order)."""
    heading_idxs = [i for i, line in enumerate(lines) if HEADING_RE.match(line)]
    spans = []
    for pos, start in enumerate(heading_idxs):
        end = heading_idxs[pos + 1] if pos + 1 < len(heading_idxs) else len(lines)
        spans.append((start, end))
    return spans


def extract_citations(body_text):
    """Return (confident_numbers, ambiguous_numbers) mentioned in body_text."""
    confident, ambiguous = [], []
    for match in ANCHOR_RE.finditer(body_text):
        prefix = body_text[max(0, match.start() - 12):match.start()]
        suffix = body_text[match.end():match.end() + 40]
        window = body_text[max(0, match.start() - CONTEXT_WINDOW):
                            match.end() + CONTEXT_WINDOW]
        if FOREIGN_DOC_STEP_RE.match(suffix):
            continue  # another document's own step numbering, not a citation
        is_findings_signal = bool(FINDINGS_SIGNAL_RE.search(window))
        is_puzzle_idiom = (
            not is_findings_signal
            and bool(
                PUZZLE_PREFIX_RE.search(prefix)
                or PUZZLE_VOCAB_RE.search(window)
                or PUZZLE_COOCCURRENCE_RE.search(window)
            )
        )
        for num in expand_cluster(match.group(1)):
            if num in ALWAYS_DROP:
                continue
            if is_puzzle_idiom:
                continue
            if num in ("2", "3") and "." not in num and not is_findings_signal:
                ambiguous.append(num)
                continue
            confident.append(num)
    return confident, ambiguous


def build_graph():
    text = FINDINGS.read_text(encoding="utf-8")
    lines = text.splitlines()
    rows = parse_phases(text)
    rows = assign_stable_ids(rows)
    spans = build_line_spans(lines)
    assert len(spans) == len(rows), (
        f"heading/row count mismatch: {len(spans)} spans vs {len(rows)} rows"
    )

    number_to_ids = defaultdict(list)
    for row in rows:
        number_to_ids[row["number"]].append(row["stable_id"])

    edges = []  # (from_id, to_id, count)
    ambiguous_by_phase = {}
    dangling = Counter()

    for row, (start, end) in zip(rows, spans):
        body = "\n".join(lines[start + 1:end])
        confident, ambiguous = extract_citations(body)
        counts = Counter(confident)
        edge_counts = defaultdict(int)
        for num, count in counts.items():
            targets = number_to_ids.get(num)
            if not targets:
                dangling[num] += count
                continue
            for target_id in targets:
                if target_id == row["stable_id"]:
                    continue  # self-citation
                edge_counts[target_id] += count
        for target_id, count in edge_counts.items():
            edges.append((row["stable_id"], target_id, count))
        if ambiguous:
            ambiguous_by_phase[row["stable_id"]] = dict(Counter(ambiguous))

    return rows, edges, ambiguous_by_phase, dangling


def write_outputs(rows, edges, ambiguous_by_phase, dangling):
    in_degree = Counter()
    out_degree = Counter()
    citers = defaultdict(set)
    for src, dst, _count in edges:
        in_degree[dst] += 1
        out_degree[src] += 1
        citers[dst].add(src)

    by_id = {row["stable_id"]: row for row in rows}

    graph = {
        "nodes": [
            {
                "stable_id": row["stable_id"],
                "number": row["number"],
                "subject": row["subject"],
                "date": row["date"],
                "in_degree": in_degree[row["stable_id"]],
                "out_degree": out_degree[row["stable_id"]],
            }
            for row in rows
        ],
        "edges": [
            {"from": src, "to": dst, "count": count} for src, dst, count in edges
        ],
        "ambiguous_low_number_mentions": ambiguous_by_phase,
        "dangling_number_mentions": dict(dangling),
    }
    GRAPH_JSON.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")

    ranked = sorted(
        rows,
        key=lambda row: (-in_degree[row["stable_id"]], int(float(row["number"]))),
    )

    lines_out = [
        "---",
        "type: index",
        "status: live",
        "generated_from: tools/gsmg/FINDINGS.md",
        "generator: tools/gsmg/phase_citation_graph.py",
        "---",
        "",
        "# GSMG Phase Citation Graph",
        "",
        "Ranks FINDINGS.md phases by **in-degree**: the number of *other*",
        "phases whose body text cites them (`Phase N` / `Phases N, M`). This",
        "is a heuristic text-mining pass over inline cross-references, not a",
        "semantic dependency analysis -- an edge means \"phase A's text",
        "mentions phase B\", not necessarily \"phase A's result requires",
        "phase B's result\". Use it to sequence review work (start from the",
        "most heavily cited phases and work outward to leaves), not as a",
        "citation-accuracy claim.",
        "",
        f"Regenerate with `python3 tools/gsmg/phase_citation_graph.py` after",
        "adding phases. Raw graph data: "
        "[phase_citation_graph.json](../tools/gsmg/phase_citation_graph.json).",
        "",
        "## Hub phases (highest in-degree first)",
        "",
        "| Rank | Phase | Stable ID | Subject | In-degree | Out-degree | Cited by |",
        "|---|---|---|---|---|---|---|",
    ]
    for rank, row in enumerate(ranked, start=1):
        sid = row["stable_id"]
        deg = in_degree[sid]
        if deg == 0:
            break
        cited_by = ", ".join(sorted(citers[sid], key=lambda s: by_id[s]["number"]))
        lines_out.append(
            f"| {rank} | {row['number']} | {sid} | {row['subject'] or row['heading_text']} "
            f"| {deg} | {out_degree[sid]} | {cited_by} |"
        )

    leaf_count = sum(1 for row in rows if in_degree[row["stable_id"]] == 0)
    lines_out += [
        "",
        f"**{leaf_count}** of **{len(rows)}** phases have in-degree 0 (leaves: not "
        "cited by any other phase's body text -- terminal work, or work whose "
        "citations use phrasing this heuristic missed).",
        "",
        "## Ambiguous mentions (excluded from the graph above)",
        "",
        "Bare `Phase 2` / `Phase 3` (no `solved`/`puzzle` prefix) collide with",
        "the unrelated puzzle Phase 2/3/3.2 AES boundary numbering and are not",
        "resolved automatically. Manually check these before trusting any",
        "in-degree count for Phase 2 or Phase 3 themselves.",
        "",
    ]
    if ambiguous_by_phase:
        lines_out.append("| Citing phase | Ambiguous numbers mentioned |")
        lines_out.append("|---|---|")
        for sid, counts in sorted(ambiguous_by_phase.items()):
            desc = ", ".join(f"{num}×{n}" for num, n in sorted(counts.items()))
            lines_out.append(f"| {sid} | {desc} |")
    else:
        lines_out.append("None found.")
    lines_out.append("")

    if dangling:
        lines_out += [
            "## Dangling number mentions (no matching phase heading)",
            "",
            "`Phase N` text where N does not match any FINDINGS.md heading "
            "(likely a typo, a sub-numbered reference like \"Phase 8's second "
            "half\", or a mention of a non-FINDINGS numbering scheme).",
            "",
            "| Number | Mentions |",
            "|---|---|",
        ]
        for num, count in sorted(dangling.items(), key=lambda kv: -kv[1]):
            lines_out.append(f"| {num} | {count} |")
        lines_out.append("")

    REPORT_MD.write_text("\n".join(lines_out), encoding="utf-8")
    return ranked, in_degree, leaf_count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        rows, edges, ambiguous_by_phase, dangling = build_graph()
    except PhaseIdError as error:
        print(f"[!] {error}", file=sys.stderr)
        return 1

    if args.self_test:
        confident, ambiguous = extract_citations(
            "As established in Phase 32 and Phases 58, 97, this reproduces "
            "earlier results."
        )
        assert confident == ["32", "58", "97"], confident
        assert ambiguous == [], ambiguous

        confident, ambiguous = extract_citations(
            "This reproduces the solved Phase 2 boundary and Phase 3.2's "
            "ciphertext."
        )
        assert confident == [], confident
        assert ambiguous == [], ambiguous

        confident, ambiguous = extract_citations(
            "The chess FEN embedded in Phase 2 and the AES ciphertext in "
            "Phase 3 are already documented."
        )
        assert confident == [], confident
        assert ambiguous == [], ambiguous

        confident, ambiguous = extract_citations(
            "This project's Phase 2 writeup already covers this, and "
            "FINDINGS Phase 3 confirmed the same result."
        )
        assert confident == ["2", "3"], confident
        assert ambiguous == [], ambiguous

        confident, ambiguous = extract_citations(
            "A follow-up check in Phase 2 revisited an earlier open "
            "question, while Phase 3 remained untouched."
        )
        assert confident == [], confident
        assert ambiguous == ["2", "3"], ambiguous

        confident, ambiguous = extract_citations(
            "The operational half is already closed: literal passphrase "
            "(Phase 109, 0/3 candidates), done."
        )
        assert confident == ["109"], confident
        assert ambiguous == [], ambiguous

        confident, ambiguous = extract_citations(
            "the same date as the already-confirmed Times headline this\n"
            "puzzle uses for Phase 3 part 6."
        )
        assert confident == [], confident
        assert ambiguous == [], ambiguous

        confident, ambiguous = extract_citations(
            "Implemented Phases 1-2 of\n"
            "[doc/GSMG_YINYANG_ARTIFACT_PLAN.md](../../doc/GSMG_YINYANG_ARTIFACT_PLAN.md)."
        )
        assert confident == [], confident
        assert ambiguous == [], ambiguous

        assert expand_cluster("356-359") == ["356", "357", "358", "359"]
        assert expand_cluster("106/94-95") == ["106", "94", "95"]
        node_ids = {row["stable_id"] for row in rows}
        for src, dst, _count in edges:
            assert src in node_ids and dst in node_ids
        print(f"[*] self-test OK: {len(rows)} phases, {len(edges)} edges, "
              f"{sum(len(v) for v in ambiguous_by_phase.values())} ambiguous "
              f"mentions, {sum(dangling.values())} dangling mentions")
        return 0

    ranked, in_degree, leaf_count = write_outputs(rows, edges, ambiguous_by_phase, dangling)
    top = [r for r in ranked if in_degree[r["stable_id"]] > 0][:10]
    print(f"[*] wrote {GRAPH_JSON} and {REPORT_MD}")
    print(f"[*] {len(rows)} phases, {len(edges)} edges, {leaf_count} leaves (in-degree 0)")
    print("[*] top hubs:")
    for row in top:
        print(f"    Phase {row['number']} ({row['stable_id']}): "
              f"in-degree {in_degree[row['stable_id']]} -- {row['subject']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
