#!/usr/bin/env python3
"""Audit oracle coverage for wordlists outside the historical 648 corpus.

The Phase-254 exclusion manifest explains why a file is outside
``extended_cipher_recheck.CURATED_FILES``.  This audit answers the separate
question: what actually consumed that file, which oracle families reached it,
and does the Phase-253 Blowfish/Camellia/SEED menu-gap remain open?

``--menu-gap-sweep`` runs that new family only over six small, candidate-like
excluded files.  It deliberately excludes raw corpora, generated medium-tier
outputs, and the one-line/1,326-word Architect scene cache.
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import BLOBS, OPENSSL_MENU_GAP_CIPHER_VARIANTS, answer_forms, keystr_forms  # noqa: E402
from curated_candidate_corpus_audit import (  # noqa: E402
    EXCLUDED_WORDLISTS,
    active_lines,
    build as build_curated_corpus,
    wordlist_manifest,
)
from extended_cipher_recheck import WORDLIST_DIR, candidate_list_digest, sweep  # noqa: E402


# These descriptions summarize completed, recorded runs.  "Derived" means the
# source fed a later generator/selector; it does not imply every raw line was
# tried verbatim.  File names and consumers are checked below so additions or
# renames cannot silently leave the table stale.
COVERAGE = {
    "anchor_x_vocab_combos.txt": ("medium Tier 2 input", "build_medium_curated_candidates.py", "Phases 90/144/164", "derived candidates: padded binary CBC/ECB, nopad windows, literal raw key"),
    "chat_mined_lines.txt": ("filtered medium Tier 3 input", "build_medium_curated_candidates.py", "Phase 164", "selected derivatives: literal raw key; raw lines not exhaustively swept"),
    "chat_mined_words.txt": ("filtered medium Tier 3 input", "build_medium_curated_candidates.py", "Phase 164", "selected derivatives: literal raw key"),
    "chat_theme_content_words.txt": ("medium Tier 2 input", "build_medium_curated_candidates.py", "Phases 90/144/164", "derived candidates: padded binary CBC/ECB, nopad windows, literal raw key"),
    "chat_theme_lines_raw.txt": ("intermediate source", "no direct candidate consumer", "none", "no claim that every raw line was swept"),
    "content_word_filtered.txt": ("medium Tier 2 input", "build_medium_curated_candidates.py", "Phases 90/144/164", "exact lines enter Tier 2; padded binary CBC/ECB, nopad windows, literal raw key"),
    "cosmic_duality_book_candidates.txt": ("medium Tier 2 input", "build_medium_curated_candidates.py", "Phases 90/144/164", "exact lines enter Tier 2; padded binary CBC/ECB, nopad windows, literal raw key"),
    "cosmic_duality_book_full_text.txt": ("primary-text source", "targeted book/checkerboard tools", "multiple targeted phases", "no claim that every raw line was a direct passphrase"),
    "cosmic_duality_book_p6_11_candidates.txt": ("medium Tier 2 input", "build_medium_curated_candidates.py", "Phases 90/144/164", "exact lines enter Tier 2; padded binary CBC/ECB, nopad windows, literal raw key"),
    "cosmic_duality_book_p8_9.txt": ("medium Tier 2 input", "build_medium_curated_candidates.py", "Phases 90/144/164", "exact lines enter Tier 2; padded binary CBC/ECB, nopad windows, literal raw key"),
    "cosmic_duality_book_screenshot_ocr.txt": ("medium Tier 1 input", "build_medium_curated_candidates.py", "Phases 83/94/164", "line/reduction derivatives: padded binary CBC/ECB, nopad windows, literal raw key"),
    "jacque_fresco_candidates.txt": ("dedicated exact list", "jacque_fresco_wordlist_audit.py", "Phases 88-90", "legacy/extended CBC, AES ECB, AES CFB/OFB/CTR, AES Key Wrap; newline forms"),
    "looking_forward_candidates.txt": ("dedicated exact list + medium Tier 2", "yin_yang_transition_audit.py", "Phases 44/90/144/164", "dedicated legacy/extended CBC and AES Key Wrap without newline forms; medium binary/raw-key coverage"),
    "matrix_architect_scene_through_choice_words.txt": ("selector source, not candidate list", "salt_selector_permutation_audit.py", "Phases 174/192", "salt-selected outputs: legacy/extended CBC, AES ECB/stream/Key Wrap"),
    "matrix_script_windows.txt": ("filtered medium Tier 3 input", "build_medium_curated_candidates.py", "Phase 164", "fixed-stride selected derivatives: literal raw key; full overlapping source not swept"),
    "matrix_scripts_words.txt": ("filtered medium Tier 3 input", "build_medium_curated_candidates.py", "Phase 164", "selected derivatives: literal raw key"),
    "medium_curated_all.txt": ("generated union", "literal_raw_key_material_audit.py", "Phase 164", "all medium tiers: literal raw-key oracle"),
    "medium_curated_provenance.txt": ("generated sidecar", "build_medium_curated_candidates.py", "Phase 81", "metadata only; not candidate input"),
    "medium_curated_tier1_primary.txt": ("generated Tier 1", "binary_key_material_backfill.py / nopad_window_sweep.py", "Phases 83/94/164", "padded binary CBC/ECB, nopad windows, literal raw key"),
    "medium_curated_tier2_derived.txt": ("generated Tier 2", "binary_key_material_backfill.py / nopad_window_sweep.py", "Phases 90/144/164", "padded binary CBC/ECB, nopad windows, literal raw key"),
    "medium_curated_tier3_broad.txt": ("generated Tier 3", "literal_raw_key_material_audit.py via combined union", "Phase 164", "literal raw key only as a complete tier"),
    "safenet_luna_hsm_candidates.txt": ("dedicated exact list", "safenet_luna_hsm_audit.py", "Phase 116", "legacy/extended CBC, AES ECB, AES CFB/OFB/CTR, AES Key Wrap; newline forms"),
    "session_combined_for_chain.txt": ("medium Tier 2 input", "build_medium_curated_candidates.py", "Phases 90/144/164", "derived candidates: padded binary CBC/ECB, nopad windows, literal raw key"),
    "curated_v2_core.txt": ("generated V2 registry output", "curated_candidate_registry.py", "Phase 256", "own dedicated V2 sweep and self-test, not this module's scope"),
    "curated_v2_bounded.txt": ("generated V2 registry output", "curated_candidate_registry.py", "Phase 256", "own dedicated V2 sweep and self-test, not this module's scope"),
    "curated_v2_full.txt": ("generated V2 registry output", "curated_candidate_registry.py", "Phase 256", "own dedicated V2 sweep and self-test, not this module's scope"),
}

MENU_GAP_FILES = (
    "content_word_filtered.txt",
    "cosmic_duality_book_p6_11_candidates.txt",
    "cosmic_duality_book_p8_9.txt",
    "jacque_fresco_candidates.txt",
    "looking_forward_candidates.txt",
    "safenet_luna_hsm_candidates.txt",
)
EXPECTED_MENU_GAP_CANDIDATES = 625
EXPECTED_MENU_GAP_DIGEST = "854bffab41ecb1ef"
EXPECTED_MENU_GAP_EVALUATIONS = 17163
EXPECTED_MENU_GAP_UNIQUE_PASSPHRASES = 16101
EXPECTED_NET_NEW_EXACT_CANDIDATES = 563
EXPECTED_NET_NEW_EXACT_DIGEST = "a5a3c95b8d8bb594"
EXPECTED_PRIOR_PASSPHRASE_OVERLAP = 2358
EXPECTED_NET_NEW_UNIQUE_PASSPHRASES = 13743


def menu_gap_candidates():
    seen = set()
    ordered = []
    source_rows = []
    for name in MENU_GAP_FILES:
        values = tuple(dict.fromkeys(active_lines(WORDLIST_DIR / name)))
        before = len(ordered)
        for value in values:
            if value not in seen:
                seen.add(value)
                ordered.append(value)
        source_rows.append({
            "source": name,
            "active_unique": len(values),
            "new_exact": len(ordered) - before,
            "duplicate_of_prior": len(values) - (len(ordered) - before),
        })
    return tuple(ordered), tuple(source_rows)


def generated_passphrases(candidates):
    generated = []
    for candidate in candidates:
        for form in answer_forms(candidate):
            generated.extend(keystr_forms(form, newline_variants=True))
    return tuple(generated)


def audit():
    manifest = {row["source"]: row for row in wordlist_manifest() if row["status"] == "excluded"}
    if set(COVERAGE) != set(EXCLUDED_WORDLISTS) or set(COVERAGE) != set(manifest):
        raise AssertionError("coverage table no longer matches the Phase-254 exclusion manifest")

    rows = []
    for source in sorted(COVERAGE):
        handling, consumer, last_phase, prior_coverage = COVERAGE[source]
        rows.append({
            "source": source,
            "active_lines": manifest[source]["active_lines"],
            "exclusion_category": manifest[source]["category"],
            "handling": handling,
            "consumer": consumer,
            "last_phase": last_phase,
            "prior_coverage": prior_coverage,
            "openssl_menu_gap": "selected for bounded run" if source in MENU_GAP_FILES else "not selected",
        })

    candidates, selected_sources = menu_gap_candidates()
    generated = generated_passphrases(candidates)
    selected_passphrases = set(generated)
    prior_candidates = tuple(
        row["candidate"] for row in build_curated_corpus(True)["candidates"]
    )
    prior_candidate_set = set(prior_candidates)
    prior_passphrases = set(generated_passphrases(prior_candidates))
    net_new_candidates = tuple(
        candidate for candidate in candidates if candidate not in prior_candidate_set
    )
    prior_scheduled_evaluations = sum(
        passphrase in prior_passphrases for passphrase in generated
    )
    net_new_passphrases = selected_passphrases - prior_passphrases
    operation_factor = len(OPENSSL_MENU_GAP_CIPHER_VARIANTS) * len(BLOBS)
    return {
        "excluded_wordlist_count": len(rows),
        "coverage_rows": tuple(rows),
        "menu_gap_scope": {
            "files": MENU_GAP_FILES,
            "source_rows": selected_sources,
            "candidate_count": len(candidates),
            "candidate_digest": candidate_list_digest(candidates),
            "prior_scope_candidate_count": len(prior_candidates),
            "prior_scope_candidate_digest": candidate_list_digest(prior_candidates),
            "prior_exact_candidate_overlap": len(candidates) - len(net_new_candidates),
            "net_new_exact_candidates": len(net_new_candidates),
            "net_new_exact_candidate_digest": candidate_list_digest(net_new_candidates),
            "candidate_form_evaluations": len(generated),
            "unique_generated_passphrases": len(selected_passphrases),
            "prior_scheduled_evaluations": prior_scheduled_evaluations,
            "net_new_scheduled_evaluations": len(generated) - prior_scheduled_evaluations,
            "prior_unique_passphrase_overlap": len(selected_passphrases & prior_passphrases),
            "net_new_unique_passphrases": len(net_new_passphrases),
            "cipher_kdf_variants": len(OPENSSL_MENU_GAP_CIPHER_VARIANTS),
            "blobs": tuple(BLOBS),
            "concrete_decryptions": len(generated) * operation_factor,
            "net_new_scheduled_decryptions": (
                len(generated) - prior_scheduled_evaluations
            ) * operation_factor,
            "net_new_unique_passphrase_decryptions": len(net_new_passphrases) * operation_factor,
        },
    }


def self_test():
    report = audit()
    scope = report["menu_gap_scope"]
    assert report["excluded_wordlist_count"] == 26
    assert (scope["candidate_count"], scope["candidate_digest"]) == (
        EXPECTED_MENU_GAP_CANDIDATES, EXPECTED_MENU_GAP_DIGEST,
    )
    assert scope["candidate_form_evaluations"] == EXPECTED_MENU_GAP_EVALUATIONS
    assert scope["unique_generated_passphrases"] == EXPECTED_MENU_GAP_UNIQUE_PASSPHRASES
    assert scope["prior_exact_candidate_overlap"] == 62
    assert (
        scope["net_new_exact_candidates"], scope["net_new_exact_candidate_digest"]
    ) == (EXPECTED_NET_NEW_EXACT_CANDIDATES, EXPECTED_NET_NEW_EXACT_DIGEST)
    assert scope["prior_unique_passphrase_overlap"] == EXPECTED_PRIOR_PASSPHRASE_OVERLAP
    assert scope["net_new_unique_passphrases"] == EXPECTED_NET_NEW_UNIQUE_PASSPHRASES
    assert scope["prior_scheduled_evaluations"] == 2358
    assert scope["net_new_scheduled_evaluations"] == 14805
    assert scope["cipher_kdf_variants"] == 20
    assert len(scope["blobs"]) == 4
    assert scope["concrete_decryptions"] == 1373040
    assert scope["net_new_scheduled_decryptions"] == 1184400
    assert scope["net_new_unique_passphrase_decryptions"] == 1099440
    print("[*] self-test OK: 26-source coverage matrix and bounded 625-candidate menu-gap scope")


def print_report(report):
    print("source\tactive\thandling\tconsumer\tlast phase\tmenu gap")
    for row in report["coverage_rows"]:
        print("\t".join(map(str, (
            row["source"], row["active_lines"], row["handling"],
            row["consumer"], row["last_phase"], row["openssl_menu_gap"],
        ))))
    print("\nmenu-gap scope:")
    for key, value in report["menu_gap_scope"].items():
        if key != "source_rows":
            print(f"{key}: {value}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--menu-gap-sweep", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = audit()
    if args.menu_gap_sweep:
        candidates, _rows = menu_gap_candidates()
        attempts, hits = sweep(
            candidates,
            newline_variants=True,
            blobs=BLOBS,
            kdf_variants=OPENSSL_MENU_GAP_CIPHER_VARIANTS,
        )
        print(
            f"[*] {len(candidates)} candidates / {attempts} evaluations / "
            f"{attempts * len(OPENSSL_MENU_GAP_CIPHER_VARIANTS) * len(BLOBS)} decryptions"
        )
        print(f"[*] hits: {len(hits)}")
        for hit in hits:
            print(json.dumps(hit, default=repr))
        return
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
