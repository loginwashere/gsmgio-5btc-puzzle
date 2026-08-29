#!/usr/bin/env python3
"""Phase 449 -- oracle-free G-ESC-001 selector/contradiction audit."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from checkerboard_code_ic_oracle import (
    code_ic,
    ic_by_escape_pair,
    rank_of_pair,
    segment_codes,
)
from data import DBBI, FAED
from faed_letter_frequency_chi_square import (
    chi_square_p_value,
    per_symbol_contributions,
)
from prime_matrixsum_reconstruction import mirror9


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_FILES = {
    "open_gap_registry": REPO_ROOT / "doc/GSMG_OPEN_GAP_REGISTRY.md",
    "object_faed": REPO_ROOT / "doc/GSMG_OBJECT_FAED.md",
    "phase34": REPO_ROOT / "tools/gsmg/findings/P00034.md",
    "phase43": REPO_ROOT / "tools/gsmg/findings/P00043.md",
    "phase112": REPO_ROOT / "tools/gsmg/findings/P00112.md",
    "phase113": REPO_ROOT / "tools/gsmg/findings/P00113.md",
    "phase123": REPO_ROOT / "tools/gsmg/findings/P00123.md",
    "phase225": REPO_ROOT / "tools/gsmg/findings/P00225.md",
    "phase236": REPO_ROOT / "tools/gsmg/findings/P00236.md",
    "phase243": REPO_ROOT / "tools/gsmg/findings/P00243.md",
    "phase244": REPO_ROOT / "tools/gsmg/findings/P00244.md",
    "phase249": REPO_ROOT / "tools/gsmg/findings/P00249.md",
    "phase293": REPO_ROOT / "tools/gsmg/findings/P00293.md",
    "phase425": REPO_ROOT / "tools/gsmg/findings/P00425.md",
    "phase426_428": REPO_ROOT / "tools/gsmg/findings/P00425.md",
}

CANDIDATES = {"GI": ("g", "i"), "HE": ("h", "e")}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_evidence_anchors():
    anchors = {
        "open_gap_registry": (
            "FAED's independently-best `{g,i}` escape pair",
            "Architect-mirror-predicted `{h,e}` pair remain unreconciled",
        ),
        "phase34": ("deriving the mirrored `{b,e}` and `{h,e}` escape hypotheses",),
        "phase43": (
            "FAED's best pair `{g,i}` only reaches\n31.9%",
            "`(h,e)` specifically is one of the weaker fits at 22.28%",
            "empirical p = (63+1)/(100+1) = 0.63366",
        ),
        "phase112": (
            "FAED: `{g,i}` ranks **1/36**",
            "FAED's `{h,e}` mirror hypothesis ranks 16th",
        ),
        "phase113": ("empirical p=0.0396",),
        "phase123": ("`338,905/338,905` alphabet candidates completed",),
        "phase225": (
            "there are no clues in the puzzle's typos",
            "do not promote it to a recovered\nbinding",
        ),
        "phase236": (
            "The complete fixed table is:",
            "This is a real descriptive asymmetry, not a decoder selector",
        ),
        "phase243": ("same* `<textarea>`'s text content",),
        "phase244": ("all 3 fetched captures matched their pinned sha256/byte_count",),
        "phase249": ("No new HTML variant exists",),
        "phase293": ("**Result: 0/96 hits",),
        "phase425": ("family_corrected_positive_checkpoint_only",),
        "phase426_428": ("digraph_mechanical_attribution",),
    }
    for key, needles in anchors.items():
        text = EVIDENCE_FILES[key].read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                raise AssertionError(f"evidence anchor drifted: {key}: {needle!r}")


def candidate_metrics(label, pair):
    ic_map = ic_by_escape_pair(FAED)
    rank, ic, _ranked, tied = rank_of_pair(ic_map, pair)
    codes = segment_codes(FAED, *pair)
    counts = Counter(FAED)
    chi2, p_value = chi_square_p_value(counts)
    contributions = per_symbol_contributions(counts)
    return {
        "label": label,
        "pair": list(pair),
        "valid_on_faed": codes is not None,
        "faed_code_count": len(codes),
        "faed_code_type_count": len(set(codes)),
        "code_ic": ic,
        "code_ic_distance_from_0_067": abs(ic - 0.067),
        "code_ic_rank_among_valid_pairs": rank,
        "rank_tie_count": tied,
        "escape_character_count": sum(counts[symbol] for symbol in pair),
        "escape_character_fraction": sum(counts[symbol] for symbol in pair) / len(FAED),
        "share_of_faed_uniform_chi_square_deviation": (
            sum(contributions[symbol] for symbol in pair) / chi2
        ),
        "faed_uniform_chi_square": chi2,
        "faed_uniform_chi_square_p": p_value,
    }


def comparison_rows(metrics):
    return [
        {
            "constraint": "complete FAED segmentation",
            "class": "raw_admissibility",
            "independence_group": "FAED-tokenization",
            "GI": "passes: 436 codes, all 25 types",
            "HE": "passes: 469 codes, all 25 types",
            "disposition": "tie; neither candidate contradicted",
        },
        {
            "constraint": "code IC near English 0.067",
            "class": "internal_statistic",
            "independence_group": "English-checkerboard-profile",
            "GI": f"rank 1/29 valid; IC {metrics['GI']['code_ic']:.5f}",
            "HE": f"rank 16/29 valid; IC {metrics['HE']['code_ic']:.5f}",
            "disposition": "supports GI conditionally on the checkerboard/English model",
        },
        {
            "constraint": "raw escape-frequency/profile fit",
            "class": "internal_statistic",
            "independence_group": "English-checkerboard-profile",
            "GI": "31.93% escape characters; rare but English-reachable profile",
            "HE": "22.28%; 78.46% top-code profile outside audited English corpora",
            "disposition": "supports GI and weighs against HE under the same model; correlated with code IC",
        },
        {
            "constraint": "raw non-uniformity contribution",
            "class": "internal_statistic",
            "independence_group": "FAED-symbol-frequency",
            "GI": f"{metrics['GI']['share_of_faed_uniform_chi_square_deviation']:.2%} of chi-square",
            "HE": f"{metrics['HE']['share_of_faed_uniform_chi_square_deviation']:.2%} of chi-square",
            "disposition": "strong descriptive GI ranking, not a sourced escape rule",
        },
        {
            "constraint": "Architect BUT/HYE mirror derivation",
            "class": "rule_derivation",
            "independence_group": "Architect-macro-mirror",
            "GI": "not produced",
            "HE": "produced exactly as mirror9({b,e})",
            "disposition": "supports HE only conditionally; mirror operation remains G-ARCH-001",
        },
        {
            "constraint": "creator YING/YANG native-letter parse",
            "class": "rule_derivation",
            "independence_group": "creator-spelling",
            "GI": "YING -> IG exactly; FAED-specific rank alignment",
            "HE": "not produced",
            "disposition": "rejected as selector: creator disclaimed typo clues and authenticated macro says YINYANG",
        },
        {
            "constraint": "page boundary and archive provenance",
            "class": "presentation_or_provenance",
            "independence_group": "SalPhaseIon-page",
            "GI": "no selector",
            "HE": "no selector",
            "disposition": "tie; page branch exhausted across 16 successful capture events",
        },
        {
            "constraint": "pair-specific decoder/consumer trials",
            "class": "downstream_model",
            "independence_group": "decoder-model-negatives",
            "GI": "monoalphabetic p=0.0396; full chain-addition 0 hits",
            "HE": "monoalphabetic p=0.63366; curated chain/autokey and direct seeds 0 hits",
            "disposition": "GI is less null-like, but neither negative falsifies its pair because no decoder/consumer was independently fixed",
        },
        {
            "constraint": "escape-independent FAED Bifid BTCSEED checkpoint",
            "class": "cross_representation",
            "independence_group": "Bifid-full-block",
            "GI": "not used",
            "HE": "not used",
            "disposition": "non-discriminating; no sourced bridge from Bifid square to escape grammar",
        },
    ]


def audit():
    require_evidence_anchors()
    metrics = {label: candidate_metrics(label, pair) for label, pair in CANDIDATES.items()}
    if mirror9("b") != "h" or mirror9("e") != "e":
        raise AssertionError("mirror9 derivation drifted")
    rows = comparison_rows(metrics)
    gates = {
        "GI": {
            "valid_on_faed": True,
            "independent_selector": False,
            "rival_excluded_or_reconciled": False,
            "no_load_bearing_open_dependency": True,
        },
        "HE": {
            "valid_on_faed": True,
            "independent_selector": False,
            "rival_excluded_or_reconciled": False,
            "no_load_bearing_open_dependency": False,
        },
    }
    selected = [label for label, values in gates.items() if all(values.values())]
    return {
        "phase": 449,
        "gap": "G-ESC-001",
        "candidate_metrics": metrics,
        "comparison_rows": rows,
        "decision_gates": gates,
        "selected_candidates": selected,
        "working_ranking": ["GI", "HE"],
        "ranking_scope": (
            "GI is the stronger working prior for a FAED checkerboard decoder; "
            "this is not an authenticated selector and does not close G-ESC-001."
        ),
        "contradiction_audit": {
            "GI_pair_level_contradicted": False,
            "HE_pair_level_contradicted": False,
            "HE_english_checkerboard_profile_strongly_disfavored": True,
            "decoder_level_negatives_are_pair_level_falsifications": False,
            "rationale": (
                "Both pairs tokenize all of FAED. HE's profile mismatch is conditional "
                "on ordinary-English checkerboard plaintext; GI/HE oracle failures are "
                "conditional on unfixed decoders and consumers."
            ),
        },
        "independence_summary": {
            "GI_positive_groups": [
                "English-checkerboard-profile",
                "FAED-symbol-frequency",
                "creator-spelling (authorship gate failed)",
            ],
            "HE_positive_groups": ["Architect-macro-mirror (G-ARCH-001 dependency)"],
            "neutral_groups": ["FAED-tokenization", "SalPhaseIon-page", "Bifid-full-block"],
            "warning": (
                "Code IC, escape density, and profile reachability are related views of "
                "one checkerboard/English assumption and are not three independent votes."
            ),
        },
        "reopen_evidence": (
            "A creator clue or primary artifact outside the unchanged SalPhaseIon page "
            "must name/select one pair, or must explain that GI and HE serve different "
            "roles. A clue-fixed decoder with a pair-independent validator could also "
            "turn the existing statistical ranking into a decisive test."
        ),
        "decision": "remain_unreconciled_with_gi_as_working_prior",
        "new_compute_authorized": False,
        "password_materials_generated": 0,
        "oracle_calls": 0,
        "gpu_touched": False,
        "docker_touched": False,
        "network_touched": False,
        "external_agents_used": False,
        "evidence_sha256": {key: sha256(path) for key, path in EVIDENCE_FILES.items()},
    }


def self_test():
    result = audit()
    gi = result["candidate_metrics"]["GI"]
    he = result["candidate_metrics"]["HE"]
    assert gi["faed_code_count"] == 436 and gi["faed_code_type_count"] == 25
    assert he["faed_code_count"] == 469 and he["faed_code_type_count"] == 25
    assert gi["code_ic_rank_among_valid_pairs"] == 1
    assert he["code_ic_rank_among_valid_pairs"] == 16
    assert gi["share_of_faed_uniform_chi_square_deviation"] > 0.70
    assert he["share_of_faed_uniform_chi_square_deviation"] < 0.05
    assert not result["selected_candidates"]
    assert result["decision"] == "remain_unreconciled_with_gi_as_working_prior"
    assert not result["new_compute_authorized"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = self_test() if args.self_test else audit()
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    if args.json or not args.output:
        print(rendered, end="")
    if args.self_test:
        print("[*] self-test OK: G-ESC candidates ranked without false selection")


if __name__ == "__main__":
    main()
