#!/usr/bin/env python3
"""Audit the creator-grounded transition into the GSMG yin-yang phase."""

import argparse
import colorsys
from html.parser import HTMLParser
from pathlib import Path

from cb_common import (
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    answer_forms,
    keystr_forms,
)
from first_piece_color_reconstruction import BLUE, FEFE, WHITE, YELLOW, reconstruct

PROJECTS_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CHAT = PROJECTS_ROOT / "gsmgio-5btc-puzzle" / "_work" / "chat_transcript.txt"
DEFAULT_MIRROR = PROJECTS_ROOT / "gsmg-site-mirror"
DEFAULT_IMAGE = Path(__file__).resolve().parents[2] / "doc" / "img" / "gsmg_rabbit_hint.png"
DEFAULT_CANDIDATES = (
    Path(__file__).resolve().parents[2]
    / "wordlists"
    / "gsmg"
    / "looking_forward_candidates.txt"
)

SALPH_PAGE = "89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32.html"
SEED_PAGE = "theseedisplanted.html"
PHASE23_PAGE = "choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecialdessertiwroteitmyself.html"


class MechanicParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.inputs = []
        self.textareas = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag.lower() == "form":
            self.forms.append(
                {
                    "method": attributes.get("method", "GET").upper(),
                    "action": attributes.get("action", ""),
                }
            )
        elif tag.lower() == "input":
            self.inputs.append(
                {
                    "type": attributes.get("type", "text"),
                    "name": attributes.get("name", ""),
                }
            )
        elif tag.lower() == "textarea":
            self.textareas += 1


def page_mechanics(path):
    parser = MechanicParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return {
        "forms": parser.forms,
        "inputs": parser.inputs,
        "textareas": parser.textareas,
    }


def hue_degrees(rgb):
    red, green, blue = (channel / 255 for channel in rgb)
    hue, _, _ = colorsys.rgb_to_hsv(red, green, blue)
    return hue * 360


def circular_distance(left, right):
    difference = abs(left - right) % 360
    return min(difference, 360 - difference)


def transcript_evidence(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    required = {
        "2023_yin_yang": 'Once you hit a "ying yang", you\'ll be able to solve it the same day.',
        "2024_microstep": "If you guys got 1 microstep further, the puzzle will likely be solved the same day.",
        "2025_next_phase": "It’s the next phase, but I await the day someone finally gets there.",
        "2026_looking_forward_question": (
            'Wasn\'t "it\'s in front of your eyes but you\'re not seing it" '
            'a recomendation to read "Looking forward" btw.? Was it a plan?'
        ),
        "2026_looking_forward_response": (
            "Maybe, Cartman's quote about chatroulette fits too."
        ),
        "2026_creator_pointer": "Looks at gnomad. 👀",
        "2026_community_pointer": 'Looks at DG\'s comment "its in front of your eyes but you\'re not seeing it"',
    }
    positions = {}
    for label, message in required.items():
        position = text.find(message)
        if position < 0:
            raise AssertionError(f"missing transcript evidence {label}: {message!r}")
        positions[label] = position

    march_start = text.find("=== [03.03.2026 20:22:29 UTC-05:00] Denis Golovkin")
    march_end = text.find("=== [03.03.2026 20:30:47 UTC-05:00] Jrk Bgrt", march_start)
    if march_start < 0 or march_end < 0:
        raise AssertionError("missing bounded 2026 Looking Forward / Bingo exchanges")
    march_exchange = text[march_start:march_end]
    looking_forward_question = march_exchange.find(
        'a recomendation to read "Looking forward" btw.?'
    )
    hedged_response = march_exchange.find(
        "Maybe, Cartman's quote about chatroulette fits too."
    )
    zipped_response = march_exchange.find("🤐")
    creator_pointer = march_exchange.find("Looks at gnomad. 👀")
    community_pointer = march_exchange.find(
        'Looks at DG\'s comment "its in front of your eyes but you\'re not seeing it"'
    )
    confirmation = march_exchange.find("Bingo")
    if not (
        0
        <= looking_forward_question
        < hedged_response
        < zipped_response
        < creator_pointer
        < community_pointer
        < confirmation
    ):
        raise AssertionError("2026 exchanges are absent or out of order")
    gnomad_message = march_exchange[community_pointer:confirmation]
    if "Looking forward" in gnomad_message or "Looking Forward" in gnomad_message:
        raise AssertionError("gnomad's Bingo-triggering message unexpectedly names the book")

    return {
        "required_messages": positions,
        "looking_forward_exchange": [
            "community asks whether the phrase recommends Looking Forward",
            "creator replies with a hedged Maybe and a Cartman comparison",
            "creator posts a zipped-mouth emoji",
        ],
        "march_2026_order": [
            "creator looks at gnomad",
            "gnomad repeats only the in-front-of-your-eyes phrase",
            "creator says Bingo to the phrase-level pointer",
        ],
    }


def audit(chat_path, mirror_root, image_path):
    transcript = transcript_evidence(chat_path)
    seed = page_mechanics(mirror_root / SEED_PAGE)
    phase23 = page_mechanics(mirror_root / PHASE23_PAGE)
    salph = page_mechanics(mirror_root / SALPH_PAGE)

    if len(seed["forms"]) != 1 or seed["forms"][0]["method"] != "POST":
        raise AssertionError("the seed page no longer reproduces its hidden POST mechanic")
    if phase23["forms"] or phase23["textareas"] != 2:
        raise AssertionError("the Phase 2/3 archive does not match the expected offline-cipher layout")
    if salph["forms"] or salph["inputs"] or salph["textareas"] != 2:
        raise AssertionError("the SalPhaseIon/Cosmic archive does not match the expected static layout")

    first_piece = reconstruct(image_path)
    if first_piece["fefe"]["value"] != 0 or FEFE == WHITE:
        raise AssertionError("the unique near-white zero cell was not reproduced")

    blue_hue = hue_degrees(BLUE)
    yellow_hue = hue_degrees(YELLOW)
    hue_distance = circular_distance(blue_hue, yellow_hue)
    if abs(hue_distance - 180) >= 1:
        raise AssertionError("the archived blue/yellow colors are not approximately opposite hues")

    return {
        "transcript": transcript,
        "page_mechanics": {
            "seed_page": seed,
            "phase_2_3_page": phase23,
            "salphaseion_cosmic_page": salph,
        },
        "first_piece": {
            "blue_rgb": BLUE,
            "yellow_rgb": YELLOW,
            "blue_hue_degrees": blue_hue,
            "yellow_hue_degrees": yellow_hue,
            "minimal_hue_distance": hue_distance,
            "white_rgb": WHITE,
            "near_white_rgb": FEFE,
            "near_white_channel_difference": tuple(
                white - near_white for white, near_white in zip(WHITE, FEFE)
            ),
            "fefe": first_piece["fefe"],
        },
    }


def print_report(report):
    print("creator transcript:")
    for item in report["transcript"]["looking_forward_exchange"]:
        print(f"  - {item}")
    for item in report["transcript"]["march_2026_order"]:
        print(f"  - {item}")

    print("demonstrated transition mechanics:")
    for name, mechanics in report["page_mechanics"].items():
        print(
            f"  - {name}: forms={len(mechanics['forms'])} "
            f"inputs={len(mechanics['inputs'])} textareas={mechanics['textareas']}"
        )

    first_piece = report["first_piece"]
    print("first-piece polarity:")
    print(
        f"  - blue {first_piece['blue_rgb']} hue={first_piece['blue_hue_degrees']:.6f}°"
    )
    print(
        f"  - yellow {first_piece['yellow_rgb']} hue={first_piece['yellow_hue_degrees']:.6f}°"
    )
    print(f"  - minimal hue distance={first_piece['minimal_hue_distance']:.6f}°")
    print(
        f"  - white={first_piece['white_rgb']} near-white={first_piece['near_white_rgb']} "
        f"difference={first_piece['near_white_channel_difference']}"
    )
    print(
        "verdict: Bingo confirms that the in-front-of-your-eyes phrase matters, "
        "not that Looking Forward is its intended expansion. The book remains "
        "a hedged community-suggested lead; the archived SalPhaseIon/Cosmic "
        "page exposes no form or route mechanic."
    )


def load_candidates(path):
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def oracle_sanity_check(candidate_path):
    candidates = load_candidates(candidate_path)
    blobs = {**BLOBS, **QUARANTINED_BLOBS}
    tested_keystrings = set()
    cbc_hits = []
    wrap_hits = []

    for candidate in candidates:
        for answer in sorted(answer_forms(candidate)):
            for keystr in keystr_forms(answer):
                if keystr in tested_keystrings:
                    continue
                tested_keystrings.add(keystr)
                for variants in (None, EXTENDED_CIPHER_VARIANTS):
                    result = aes_try_open(keystr, kdf_variants=variants, blobs=blobs)
                    if result:
                        cbc_hits.append((candidate, keystr, result))
                for result in aes_keywrap_try_open_bytes(keystr.encode(), blobs=blobs):
                    wrap_hits.append((candidate, keystr, result))

    return {
        "candidate_count": len(candidates),
        "unique_keystrings": len(tested_keystrings),
        "blob_count": len(blobs),
        "cbc_hits": cbc_hits,
        "keywrap_hits": wrap_hits,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chat", type=Path, default=DEFAULT_CHAT)
    parser.add_argument("--mirror", type=Path, default=DEFAULT_MIRROR)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument(
        "--oracle",
        action="store_true",
        help="run the bounded exact-title/passage phrase sanity check",
    )
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    args = parser.parse_args()
    print_report(audit(args.chat, args.mirror, args.image))
    if args.oracle:
        result = oracle_sanity_check(args.candidates)
        print("bounded exact-phrase oracle sanity check:")
        print(
            f"  - candidates={result['candidate_count']} "
            f"unique_keystrings={result['unique_keystrings']} "
            f"blobs={result['blob_count']}"
        )
        print(
            f"  - CBC hits={len(result['cbc_hits'])} "
            f"Key-Wrap hits={len(result['keywrap_hits'])}"
        )


if __name__ == "__main__":
    main()
