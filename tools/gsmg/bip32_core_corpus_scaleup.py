#!/usr/bin/env python3
"""Phase 346: scale Phase 340's BIP32-paths-c1 detector to the two larger
core candidate corpora Phase 343's coverage ledger surfaced as genuinely
untested (cheap, ~495k checks, never scoped, not compute-blocked -- unlike
the AES-body detectors this needs no GPU port).

Per the user's explicit 2026-08-20 instruction: deduplicate the two
overlapping corpora before running, rather than running both
independently. `648_core_candidates`
(extended_cipher_recheck.load_curated_candidates()) is a proven literal
subset of `14551_core_expanded` (curated_candidate_corpus_audit.build()'s
deduped answer_forms()/keystr_forms(newline_variants=True) expansion):
cb_common.answer_forms(s) always includes `s` itself unmodified, and
cb_common.keystr_forms(form)'s first output element is always the
unmodified `form` -- so every one of the 648 base candidate strings
appears verbatim inside the 14,551-item expanded set. Proven mechanically
in self_test() (a real subset check against the live corpora), not just
asserted by citation.

Given that proof, a single BIP32 run against the 14,551-item corpus
already subsumes every derivation the 648-item corpus alone would
produce -- running both separately would recompute the same ~22,032 of
~494,734 checks for zero additional coverage. This phase therefore runs
bip32_authenticated_number_paths_audit.run() against the 14,551-item
corpus only; tools/gsmg/coverage_ledger.py's Phase 346 row declares
coverage of both corpus cells on that basis.

No decoding, no new KDF/cipher work, no scoring change -- reuses Phase
340's run(), check_key(), and PATH_REGISTRY exactly as-is. The only thing
new here is the larger `candidates` argument.
"""
import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import answer_forms, keystr_forms  # noqa: E402
from extended_cipher_recheck import load_curated_candidates  # noqa: E402
import bip32_authenticated_number_paths_audit as bip32_audit  # noqa: E402

EXPECTED_648_COUNT = 648
EXPECTED_14551_COUNT = 14551


def expanded_keystring_corpus():
    """The exact 14,551-item corpus coverage_ledger.py's `14551_core_expanded`
    refers to: 648 base candidates x answer_forms() x
    keystr_forms(newline_variants=True), deduplicated -- Phase 327's scope,
    identical to curated_candidate_corpus_audit.build(include_seed=False)'s
    own generation loop. Deliberately replicated here rather than importing
    that function's return value, since build() does not expose the raw
    generated set, only its count; self_test() cross-checks against that
    independently-computed count to prove this isn't a drifted
    reimplementation. self_test() cross-checks both determinism/digest
    stability directly and curated_candidate_corpus_audit.build()'s
    independently-computed count."""
    base = load_curated_candidates()
    generated = set()
    for candidate in base:
        for form in answer_forms(candidate):
            generated.update(keystr_forms(form, newline_variants=True))
    return base, generated


def run(known_targets=None):
    base, expanded = expanded_keystring_corpus()
    assert len(base) == EXPECTED_648_COUNT
    assert len(expanded) == EXPECTED_14551_COUNT
    assert set(base) <= expanded

    ordered = sorted(expanded)
    report = bip32_audit.run(candidates=ordered, known_targets=known_targets)
    report["base_648_count"] = len(base)
    report["expanded_14551_count"] = len(expanded)
    report["base_subset_of_expanded"] = True
    return report


def self_test():
    base, expanded = expanded_keystring_corpus()

    # 1. Corpus sizes match the frozen ledger contract exactly.
    assert len(base) == EXPECTED_648_COUNT
    assert len(expanded) == EXPECTED_14551_COUNT

    # 2. The subset proof this phase's dedup decision rests on: every one
    #    of the 648 base candidates appears verbatim in the expanded set.
    assert set(base) <= expanded, "648-item corpus is not a literal subset of the 14,551-item corpus"

    # 3. Determinism: rebuilding the corpus from scratch and re-digesting it
    #    produces the exact same set both times (not order-dependent, not
    #    accidentally stateful).
    from extended_cipher_recheck import candidate_list_digest
    base2, expanded2 = expanded_keystring_corpus()
    assert base2 == base and expanded2 == expanded
    assert candidate_list_digest(sorted(expanded)) == candidate_list_digest(sorted(expanded2))

    # 3b. Cross-check against curated_candidate_corpus_audit.build()'s own,
    #    independently-computed count (read-only call, no shared state) --
    #    proves this isn't a drifted reimplementation of the same idea.
    #    Re-added now that the manifest drift blocking this (an unrelated
    #    concurrent session's then-unclassified wordlist files) is fixed.
    import curated_candidate_corpus_audit
    live = curated_candidate_corpus_audit.build(include_seed=False)
    assert live["unique_generated_passphrases"] == len(expanded) == EXPECTED_14551_COUNT
    assert live["candidate_count"] == len(base) == EXPECTED_648_COUNT

    # 4. Planted positive control: a synthetic probe string's SHA-256-seed
    #    BIP32 master key is used to build a synthetic known-target, then
    #    run through the real bip32_audit.run() driver end-to-end -- proves
    #    the driver call this phase's run() makes is wired correctly.
    #    Deliberately a single-item candidate list, matching
    #    bip32_authenticated_number_paths_audit.py's own self_test pattern
    #    -- corpus-construction correctness is already proven by checks
    #    1-3 above without needing a second full ~494k-check pass here.
    probe_text = "bip32-scaleup-self-test-probe"
    probe_master_key, _ = bip32_audit.key_shape_classifier.bip32_master(
        bip32_audit.seed_bytes(probe_text, "sha256"))
    probe_addrs = bip32_audit.private_key_details(probe_master_key)
    synthetic_target = {bytes.fromhex(probe_addrs["compressed"]["hash160"]): "self_test_probe"}

    probe_report = bip32_audit.run(candidates=[probe_text], known_targets=synthetic_target)
    assert probe_report["total_hits"] >= 1, "planted BIP32 hit not found end-to-end"
    hit = next(h for h in probe_report["hits"]
               if h["candidate_index"] == 0 and h["check_point"] == "master_control"
               and h["seed_form"] == "sha256")
    assert hit["address_type"] == "compressed"

    # 5. Wrong-password control: an unrelated single-candidate corpus
    #    against the same synthetic target finds nothing.
    wrong_report = bip32_audit.run(candidates=["definitely-not-the-probe"], known_targets=synthetic_target)
    assert wrong_report["total_hits"] == 0

    # 6. Real-target sanity: the 42-candidate frozen corpus (cheap, already
    #    covered by Phase 340) against the real KNOWN_TARGET_HASH160S still
    #    finds nothing -- no regression introduced by this module.
    from half_better_half_algebra_audit import frozen_candidates
    control_report = bip32_audit.run(candidates=frozen_candidates())
    assert control_report["total_hits"] == 0

    print(f"[*] self-test OK: {EXPECTED_648_COUNT}-item base corpus proven a literal subset of the "
          f"{EXPECTED_14551_COUNT}-item expanded corpus, determinism/digest-stable across a rebuild, "
          f"cross-checked against curated_candidate_corpus_audit.build()'s independent count; "
          f"planted synthetic-target BIP32 master-key hit recovered end-to-end via the real driver "
          f"with correct provenance; wrong-password control clean; 42-candidate real-target control "
          f"unchanged (Phase 340's existing negative)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return
    if args.run:
        report = run()
        summary = {k: v for k, v in report.items() if k != "hits"}
        summary["hit_count"] = len(report["hits"])
        print(json.dumps(summary, indent=2, default=repr))
        if report["hits"]:
            print("!!! HITS FOUND -- see report['hits'] (not printed by default; contains candidate text)")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
