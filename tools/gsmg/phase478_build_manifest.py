"""Phase 478 manifest builder.

Usage: phase478_build_manifest.py <raw_capture_jsonl> <annotations_json>
           <discovery_lock_json> <output_manifest_jsonl>

Consumes the RAW CAPTURE artifact (bytes_b64 + call_sites per candidate,
produced by phase478_run_harvest.py -- see its own docstring) and a
structural annotation file (phase / construction_label / transformation /
eligible / eligible_reason per source file, keyed by which caller lines a
construction applies to -- written by manual review of the pinned source,
never by running or re-deriving anything from the candidates themselves)
and produces the canonical candidate MANIFEST described by the protocol's
"Manifest schema" section: one entry per distinct (source_file, bytes)
pair, structurally annotated, still carrying no SHA-256 of any candidate
byte string. Computing that digest is the matcher's job, after the oracle
lock -- this script must never do it, so that manifest-building itself
stays on the discovery side of the two-lock design.

Matching a candidate to a construction is done ONLY by caller line number
(never by candidate content) -- checked against the exact classification
this protocol has already frozen: this project's own review confirmed
that, within a single source file, each construction's caller lines are
disjoint from every other construction's, including the one file
(salph_cosmic_phase341_eligibility_audit.py) whose second construction is
attributed to a transitively-invoked helper module. A call site whose line
is not covered by any construction for its source file is a gap in the
annotation, not a candidate to guess about -- this raises rather than
silently dropping or mis-tagging it. A candidate whose call sites span
more than one construction (the same bytes legitimately produced by two
different historical code paths) is retained as a single manifest entry
recording all matched constructions, never arbitrarily collapsed to one.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


class ManifestBuildError(Exception):
    pass


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _strip_snapshot_prefix(caller_file: str) -> str:
    """Reduce an absolute snapshot-subprocess path to its repo-relative
    tail, e.g. '/tmp/phase478_snapshot_xyz/tools/gsmg/foo.py' ->
    'tools/gsmg/foo.py'. Falls back to the input unchanged if no
    'tools/gsmg/' segment is found (synthetic-fixture call sites may
    already be repo-relative)."""
    idx = caller_file.find("tools/gsmg/")
    return caller_file[idx:] if idx >= 0 else caller_file


def load_raw_capture(path):
    """Returns (header, {source_file: source_record}, {source_file: [candidate_record, ...]})."""
    header = None
    sources = {}
    candidates = {}
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            rt = rec["record_type"]
            if rt == "header":
                if header is not None:
                    raise ManifestBuildError("raw capture has more than one header record")
                header = rec
            elif rt == "source":
                sources[rec["source_file"]] = rec
            elif rt == "candidate":
                candidates.setdefault(rec["source_file"], []).append(rec)
            else:
                raise ManifestBuildError(f"unknown record_type {rt!r} in raw capture")
    if header is None:
        raise ManifestBuildError("raw capture has no header record")
    return header, sources, candidates


def verify_provenance(header, sources, discovery_lock, discovery_lock_path) -> None:
    """Fail-closed cross-checks between the raw capture and the discovery
    lock it claims to have been produced under. Never inspects any
    candidate content."""
    actual_lock_sha = sha256_file(discovery_lock_path)
    claimed_lock_sha = header["discovery_lock_sha256"]
    if actual_lock_sha != claimed_lock_sha:
        raise ManifestBuildError(
            "raw capture's discovery_lock_sha256 does not match the actual "
            f"discovery lock file: claimed {claimed_lock_sha}, actual {actual_lock_sha}"
        )

    classification_by_path = {
        entry["path"]: entry for entry in discovery_lock["eligible_py_file_classification"]
    }
    for source_file, source_rec in sources.items():
        if source_rec["status"] != "ok":
            raise ManifestBuildError(
                f"{source_file}: raw capture status is {source_rec['status']!r}, not 'ok' "
                "-- a manifest must never be built over a non-ok harvest result"
            )
        entry = classification_by_path.get(source_file)
        if entry is None:
            raise ManifestBuildError(f"{source_file}: no discovery-lock classification entry found")
        if entry["blob_sha"] != source_rec["source_blob_sha"]:
            raise ManifestBuildError(
                f"{source_file}: raw capture source_blob_sha {source_rec['source_blob_sha']!r} "
                f"does not match discovery lock blob_sha {entry['blob_sha']!r}"
            )


def _constructions_matching_line(constructions, line: int):
    return [i for i, c in enumerate(constructions) if line in c["applies_to_lines"]]


def classify_candidate(source_file, candidate_rec, constructions):
    """Returns the sorted list of distinct construction indices (into
    `constructions`) matched by this candidate's call sites, by line
    number alone. Raises if any call site's line is uncovered."""
    matched = set()
    for call_site in candidate_rec["call_sites"]:
        line = call_site["caller_line"]
        hits = _constructions_matching_line(constructions, line)
        if not hits:
            raise ManifestBuildError(
                f"{source_file}: candidate call site at line {line} "
                f"(function {call_site['caller_function']!r}) is not covered by any "
                "annotated construction -- annotation is incomplete, not a guessable gap"
            )
        matched.update(hits)
    return sorted(matched)


def build_manifest_entries(sources, candidates, annotations):
    """Returns the list of manifest entry dicts, NOT yet sorted."""
    entries = []
    for source_file, candidate_list in candidates.items():
        source_rec = sources[source_file]
        if not candidate_list:
            continue
        file_annotation = annotations.get(source_file)
        if file_annotation is None:
            raise ManifestBuildError(
                f"{source_file}: has {len(candidate_list)} raw candidates but no "
                "manifest annotation entry -- every candidate-bearing source file must "
                "be annotated before a manifest can be built over it"
            )
        constructions = file_annotation["constructions"]
        phase = file_annotation["phase"]

        for cand in candidate_list:
            matched_idxs = classify_candidate(source_file, cand, constructions)
            matched = [constructions[i] for i in matched_idxs]

            construction_label = "; ".join(c["construction_label"] for c in matched)
            transformation = "; ".join(c["transformation"] for c in matched)
            eligible = all(c["eligible"] for c in matched)
            eligible_reasons = [c["eligible_reason"] for c in matched if c["eligible_reason"]]
            eligible_reason = "; ".join(eligible_reasons) if eligible_reasons else None

            call_sites_out = sorted(
                (
                    {
                        "entrypoint": cs["entrypoint"],
                        "caller_file": _strip_snapshot_prefix(cs["caller_file"]),
                        "caller_line": cs["caller_line"],
                        "caller_function": cs["caller_function"],
                    }
                    for cs in cand["call_sites"]
                ),
                key=lambda cs: (cs["caller_file"], cs["caller_line"]),
            )

            entries.append(
                {
                    "bytes_b64": cand["bytes_b64"],
                    "source_file": source_file,
                    "source_blob_sha": source_rec["source_blob_sha"],
                    "call_sites": call_sites_out,
                    "phase": phase,
                    "construction_label": construction_label,
                    "transformation": transformation,
                    "eligible": eligible,
                    "eligible_reason": eligible_reason,
                }
            )
    return entries


def write_manifest_jsonl(entries, output_path) -> None:
    entries_sorted = sorted(entries, key=lambda e: (e["source_file"], e["bytes_b64"]))
    with open(output_path, "w") as f:
        for entry in entries_sorted:
            f.write(json.dumps(entry, sort_keys=True, separators=(",", ":")))
            f.write("\n")


def run(raw_capture_path, annotations_path, discovery_lock_path, output_path) -> dict:
    with open(discovery_lock_path) as f:
        discovery_lock = json.load(f)
    with open(annotations_path) as f:
        annotations = json.load(f)

    header, sources, candidates = load_raw_capture(raw_capture_path)
    verify_provenance(header, sources, discovery_lock, discovery_lock_path)
    entries = build_manifest_entries(sources, candidates, annotations)
    write_manifest_jsonl(entries, output_path)

    return {
        "total_entries": len(entries),
        "eligible_entries": sum(1 for e in entries if e["eligible"]),
        "ineligible_entries": sum(1 for e in entries if not e["eligible"]),
        "source_files_with_candidates": sorted(candidates.keys()),
        "manifest_sha256": sha256_file(output_path),
    }


def main() -> int:
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    raw_capture_path, annotations_path, discovery_lock_path, output_path = sys.argv[1:5]
    summary = run(raw_capture_path, annotations_path, discovery_lock_path, output_path)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
