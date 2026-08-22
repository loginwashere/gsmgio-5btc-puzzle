#!/usr/bin/env python3
"""Phase 367: bounded dependency-closure audit of the praised Git snapshot.

The audit does not infer that creator message 8352 endorses every conclusion
in the repository.  It freezes the repository state that was latest when the
message was posted, records the context of the unique ``everything`` token,
and asks the strictly narrower question whether the snapshot plus the
Jan--Feb 2023 creator messages leave exactly one unresolved opaque
payload/frontier.  The token check is descriptive and post-hoc, not a second
promotion test.
"""

import argparse
import json
import re
import subprocess
from pathlib import Path


SNAPSHOT = "fb92dd15487c6e2d275adb8c923698b7166c328e"
CUTOFF = "2023-01-12T13:07:00+00:00"

EXPECTED_TREE = {
    "README.md": "3b75f64dc0394c3a7174bf5783a2d3b5db168600",
    "SalPhaselonCosmicDuality.png": "49bf1e7268808fbba8f83ff04d1f524f30b9f795",
    "phase2.png": "eac4447c22d18438d2425cb5a934972be8971cea",
    "phase3.png": "5339319b8840072762dc73ed8941a0396698e603",
    "photo_2020-04-26_09-24-30.jpg": "72a41fcadbab3bedb22cebe4ea2f2bb9ee4d6173",
    "puzzle.png": "4e727182dc7cd07e5d3e6d999ed585d740ea891a",
    "theseedisplanted.png": "b9e050f426068914eb96c1ffc1a3466766d614f5",
}

# This is deliberately conservative: only opaque/raw payloads visibly present
# in the frozen snapshot and still unresolved are counted.  Ambiguous prose,
# X2SH4Y0QB15, the abstract yinyang transition, and later-derived artifacts are
# excluded.  Adding any of those can only increase the frontier count.
OPEN_PAYLOADS = (
    {
        "name": "P32TRAILING",
        "cluster": "phase32_trailing",
        "source": "README Phase 3.2 plaintext; OpenSSL Salted__ blob",
        "consumer": None,
    },
    {
        "name": "DBBI",
        "cluster": "salphaseion",
        "source": "SalPhaseIon textarea / README transcription",
        "consumer": None,
    },
    {
        "name": "FAED",
        "cluster": "salphaseion",
        "source": "SalPhaseIon textarea / README transcription",
        "consumer": None,
    },
    {
        "name": "SALPH",
        "cluster": "salphaseion",
        "source": "SalPhaseIon textarea; OpenSSL Salted__ blob",
        "consumer": None,
    },
    {
        "name": "COSMIC",
        "cluster": "cosmic_duality",
        "source": "Cosmic Duality textarea in frozen screenshot",
        "consumer": None,
    },
)

CREATOR_LICENSED_MACRO = (
    "yellowblueprimes",
    "matrixsumlist",
    "lastwordsbeforearchichoice",
    "yinyang",
)

SNAPSHOT_INSTRUCTION_TOKENS = (
    "matrixsumlist",
    "lastwordsbeforearchichoice",
    "thispassword",
)


def git(repo, *args):
    return subprocess.check_output(
        ["git", *args], cwd=repo, text=True, encoding="utf-8"
    ).strip()


def frozen_tree(repo):
    rows = git(repo, "ls-tree", "-r", SNAPSHOT).splitlines()
    result = {}
    for row in rows:
        metadata, name = row.split("\t", 1)
        _mode, kind, object_id = metadata.split()
        if kind != "blob":
            raise AssertionError(f"unexpected tree object type: {kind}")
        result[name] = object_id
    return result


def audit(repo=None):
    repo = Path(repo or Path(__file__).resolve().parents[2])
    if frozen_tree(repo) != EXPECTED_TREE:
        raise AssertionError("frozen snapshot tree drifted")

    latest_at_cutoff = git(repo, "rev-list", "-1", f"--before={CUTOFF}", "HEAD")
    if latest_at_cutoff != SNAPSHOT:
        raise AssertionError("snapshot is no longer latest at the praise cutoff")

    readme = git(repo, "show", f"{SNAPSHOT}:README.md")
    everything_matches = list(re.finditer(r"\beverything\b", readme, re.I))
    if len(everything_matches) != 1:
        raise AssertionError("the frozen README no longer has one everything token")
    anchor_line = next(
        line.strip() for line in readme.splitlines()
        if re.search(r"\beverything\b", line, re.I)
    )
    expected_anchor = "> Morpheus: Everything begins with choice."
    if anchor_line != expected_anchor:
        raise AssertionError("unique everything anchor drifted")

    # Only the page-derived instruction tokens belong to this 2021 snapshot.
    # ``yellowblueprimes`` and ``yinyang`` arrive in the external February
    # 2023 creator message and must not be projected backward into the tree.
    for token in SNAPSHOT_INSTRUCTION_TOKENS:
        if token not in readme.lower():
            raise AssertionError(f"snapshot lacks page instruction token {token}")

    clusters = sorted({row["cluster"] for row in OPEN_PAYLOADS})
    payloads_without_consumers = [
        row["name"] for row in OPEN_PAYLOADS if row["consumer"] is None
    ]
    unique_gap_gate = len(payloads_without_consumers) == 1
    if unique_gap_gate:
        raise AssertionError("unique-gap stop rule unexpectedly passed")

    return {
        "snapshot": SNAPSHOT,
        "cutoff": CUTOFF,
        "tree_file_count": len(EXPECTED_TREE),
        "everything_occurrences_in_readme": len(everything_matches),
        "everything_anchor": anchor_line,
        "everything_anchor_context": "already-solved Phase 2 explanation",
        "everything_lead_promoted": False,
        "tiny_hint_directional_reading": "plausible but non-operational",
        "creator_licensed_macro": list(CREATOR_LICENSED_MACRO),
        "open_payloads": list(OPEN_PAYLOADS),
        "open_payload_count": len(payloads_without_consumers),
        "frontier_clusters": clusters,
        "frontier_cluster_count": len(clusters),
        "unique_gap_gate": unique_gap_gate,
        "oracle_authorized": False,
        "disposition": "dependency closure rejected; tiny-hint thread parked",
    }


def self_test(repo=None):
    report = audit(repo)
    assert report["tree_file_count"] == 7
    assert report["everything_occurrences_in_readme"] == 1
    assert report["everything_anchor"] == "> Morpheus: Everything begins with choice."
    assert report["everything_anchor_context"] == "already-solved Phase 2 explanation"
    assert not report["everything_lead_promoted"]
    assert report["tiny_hint_directional_reading"] == "plausible but non-operational"
    assert report["open_payload_count"] == 5
    assert report["frontier_cluster_count"] == 3
    assert not report["unique_gap_gate"]
    assert not report["oracle_authorized"]
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test(args.repo) if args.self_test else audit(args.repo)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
