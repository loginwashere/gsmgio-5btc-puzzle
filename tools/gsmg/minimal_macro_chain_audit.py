#!/usr/bin/env python3
"""Audit the shortest creator-macro path from yellow/blue to yin-yang.

This is a dependency audit, not a password or cipher sweep.  It tests whether
the creator-authored macro prefix can already be consumed by the six-digit
yellow/blue prime reconstruction, without importing the later community
31-character DBBI selection as the operand of ``matrixsumlist``.
"""

import argparse
from pathlib import Path

from architect_choice_boundary_audit import audit as audit_choice
from first_piece_color_reconstruction import DEFAULT_IMAGE, reconstruct
from prime_matrixsum_reconstruction import matrixsumlist, mirror9
from salphaseion_title_rebus_audit import EXPECTED_MACRO, load_macro
from telegram_export_manifest import DEFAULT_EXPORT_DIR


MACRO_STEPS = (
    "yellowblueprimes",
    "matrixsumlist",
    "lastwordsbeforearchichoice",
    "yinyang",
)
MACRO_PREFIX = "".join(MACRO_STEPS)
SELECTED_31 = "ncsyangcahiriasogaleafayanestve"


def audit(export_path, image_path=DEFAULT_IMAGE):
    macro = load_macro(Path(export_path))
    if macro != EXPECTED_MACRO or not macro.startswith(MACRO_PREFIX):
        raise AssertionError("creator macro or its four-step prefix changed")

    colors = reconstruct(Path(image_path))
    if colors["prime_value"] != 574061:
        raise AssertionError("yellow-one polarity no longer gives prime 574061")

    matrix, sums = matrixsumlist(colors["prime_value"])
    if matrix != [[5, 7, 4], [0, 6, 1]] or sums != (23, 16, 7):
        raise AssertionError("minimal decimal-digit matrix reconstruction changed")

    choice = audit_choice()
    film = choice["sources"]["film"]["moment_to_choice"]["indexed"]["forward_one"]
    screenplay = choice["sources"]["screenplay"]["moment_to_choice"]["indexed"]["forward_one"]
    if film != screenplay:
        raise AssertionError("film/screenplay forward-one extraction drifted")
    if film["tokens"] != ("both", "ultimately", "the"):
        raise AssertionError("Architect word selection changed")
    if film["edges"] != ("but", "hye"):
        raise AssertionError("Architect edge rails changed")
    if not choice["boundary_checks"]["initials_equal_next_word"]:
        raise AssertionError("literal BUT boundary check failed")

    beginnings, endings = film["edges"]
    beginning_9 = "".join(char for char in beginnings if char in "abcdefghi")
    ending_9 = "".join(char for char in endings if char in "abcdefghi")
    mirror_state = {
        "beginning_a_i": beginning_9,
        "ending_a_i": ending_9,
        "b_mirrors_h": mirror9(beginning_9) == ending_9[0],
        "e_is_fixed": mirror9(ending_9[1]) == ending_9[1],
    }
    if mirror_state != {
        "beginning_a_i": "b",
        "ending_a_i": "he",
        "b_mirrors_h": True,
        "e_is_fixed": True,
    }:
        raise AssertionError("bounded mirror9 recognition state changed")

    return {
        "macro_steps": MACRO_STEPS,
        "prime": colors["prime_value"],
        "matrix": matrix,
        "sum_list": sums,
        "selected_words": film["tokens"],
        "edge_rails": film["edges"],
        "literal_next_word": choice["boundary_checks"]["next_word_after_choice"],
        "mirror_state": mirror_state,
        "source_stability": {
            "film_word_count": choice["sources"]["film"]["moment_to_choice"]["word_count"],
            "screenplay_word_count": choice["sources"]["screenplay"]["moment_to_choice"]["word_count"],
            "same_selected_output": film == screenplay,
        },
        "scope_comparison": {
            "minimal_prime_operand": {
                "reaches_macro_yinyang": True,
                "unconsumed_prefix_tokens": (),
                "remaining_judgment_calls": (
                    "read six decimal digits as a forward 2x3 matrix",
                    "take total followed by row sums",
                    "take beginnings and endings of the selected words",
                ),
            },
            "selected_31_operand": {
                "input": SELECTED_31,
                "reaches_macro_yinyang": False,
                "blocker": "no sourced matrix dimensions/value mapping/sum serialization",
            },
        },
        "verdict": (
            "The four-token macro prefix has a short candidate recognition "
            "path: yellow/blue -> 574061 -> [23,16,7] -> BOTH/ULTIMATELY/THE "
            "-> BUT/HYE -> the bounded b<->h, e-fixed mirror9 state. This does "
            "not prove every intermediate convention was creator-selected, but "
            "it reaches the macro's yinyang checkpoint while the 31-character "
            "operand hypothesis still stops before it. The next unresolved "
            "instruction is not fixed by this audit. VAT/SALVATION and the "
            "H|YE|BUT reading are deliberately excluded: the former is an "
            "already-known post-hoc, oracle-negative rebus and the latter has no "
            "source-selected initial-letter rule."
        ),
    }


def self_test(export_path, image_path=DEFAULT_IMAGE):
    report = audit(export_path, image_path)
    assert report["macro_steps"] == MACRO_STEPS
    assert report["prime"] == 574061
    assert report["sum_list"] == (23, 16, 7)
    assert report["selected_words"] == ("both", "ultimately", "the")
    assert report["edge_rails"] == ("but", "hye")
    assert report["literal_next_word"] == "but"
    assert report["source_stability"] == {
        "film_word_count": 69,
        "screenplay_word_count": 72,
        "same_selected_output": True,
    }
    print("[*] self-test OK: macro provenance, image prime, matrix sums, two-source Architect boundary, and mirror9 state")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export",
        type=Path,
        default=DEFAULT_EXPORT_DIR / "result.json",
    )
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test(args.export, args.image) if args.self_test else audit(args.export, args.image)

    print("[*] creator macro prefix:", " -> ".join(report["macro_steps"]))
    print(f"[*] yellow/blue prime: {report['prime']}")
    print(f"[*] decimal matrix: {report['matrix']} -> {report['sum_list']}")
    print(
        "[*] Architect selection: "
        f"{' / '.join(report['selected_words'])} -> "
        f"{report['edge_rails'][0].upper()}/{report['edge_rails'][1].upper()}"
    )
    print(f"[*] literal word after choice: {report['literal_next_word'].upper()}")
    print(f"[*] bounded mirror state: {report['mirror_state']}")
    print("[*] remaining judgment calls:")
    for item in report["scope_comparison"]["minimal_prime_operand"]["remaining_judgment_calls"]:
        print(f"    - {item}")
    print(f"[*] verdict: {report['verdict']}")


if __name__ == "__main__":
    main()
