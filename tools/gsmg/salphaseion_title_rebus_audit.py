#!/usr/bin/env python3
"""Audit the case-sensitive ``SalPhaseIon -> SalVATIon -> SALVATION`` rebus.

This is intentionally a small provenance and falsification audit, not a
dictionary search.  The target replacement ``VAT`` is fixed by the difference
between the archived heading ``SalPhaseIon`` and the independently motivated
word ``SALVATION``.  The creator-authored macro clue is then checked for one
bounded, self-referential reading:

    Very + A True Giveaway -> VATG
    "give away" G          -> VAT

The script also verifies the relevant Architect-scene phrases and can test
only the resulting fixed candidate family against the existing validated
oracles.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    EXTENDED_CIPHER_VARIANTS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open,
    aes_try_open_ecb,
    aes_try_open_stream,
    answer_forms,
    keystr_forms,
)
from data import DBBI  # noqa: E402
from page_structure_audit import DEFAULT_HTML  # noqa: E402
from prime_matrixsum_reconstruction import PDF_PATH  # noqa: E402
from telegram_export_manifest import DEFAULT_EXPORT_DIR  # noqa: E402

CREATOR_ID = "user9815232"
MACRO_MESSAGE_ID = 8446
RECOGNITION_MESSAGE_ID = 6497
EXPECTED_TITLE = "SalPhaseIon"
SPOKEN_PHASE_WORD = "SALPHATION"
EXPECTED_MACRO = (
    "yellowblueprimesmatrixsumlistlastwordsbeforearchichoiceyinyang"
    "wewontgiveawaythepassworditsinfrontofyoureyesbutyourenotseeingit"
    "verylaststepisatruegiveawaypromised"
)
FINAL_CLAUSE_TOKENS = (
    "very", "last", "step", "is", "a", "true", "giveaway",
)
TARGET_WORD = "SALVATION"
EXPECTED_OLD_MIDDLE = "PHASE"
EXPECTED_NEW_MIDDLE = "VAT"
EXPECTED_SUM_LIST = (23, 16, 7)
SCRABBLE_VALUES = {
    **dict.fromkeys("AEILNORSTU", 1),
    **dict.fromkeys("DG", 2),
    **dict.fromkeys("BCMP", 3),
    **dict.fromkeys("FHVWY", 4),
    **dict.fromkeys("K", 5),
    **dict.fromkeys("JX", 8),
    **dict.fromkeys("QZ", 10),
}
PHONE_VALUES = {
    letter: digit
    for letters, digit in (
        ("ABC", 2),
        ("DEF", 3),
        ("GHI", 4),
        ("JKL", 5),
        ("MNO", 6),
        ("PQRS", 7),
        ("TUV", 8),
        ("WXYZ", 9),
    )
    for letter in letters
}
ELEMENT_SYMBOLS = (
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca",
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
    "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn",
    "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd",
    "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb",
    "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th",
    "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm",
    "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds",
    "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og",
)
ATOMIC_NUMBER = {
    symbol.lower(): number
    for number, symbol in enumerate(ELEMENT_SYMBOLS, 1)
}


class HeadingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_h1 = False
        self.current = []
        self.headings = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "h1":
            self.in_h1 = True
            self.current = []

    def handle_data(self, data):
        if self.in_h1:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "h1" and self.in_h1:
            self.headings.append("".join(self.current).strip())
            self.in_h1 = False


def flatten_text(value):
    if isinstance(value, str):
        return value
    return "".join(
        item if isinstance(item, str) else item.get("text", "")
        for item in value
    )


def load_title(html_path):
    parser = HeadingParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    if not parser.headings:
        raise AssertionError("archived page has no H1 heading")
    return parser.headings[0]


def decode_reversed_bitstream(value):
    bits = "".join(value.split())
    if not bits or set(bits) != {"0", "1"} or len(bits) % 8:
        raise ValueError("creator message is not a complete binary bitstream")
    forward = bits[::-1]
    return bytes(
        int(forward[offset:offset + 8], 2)
        for offset in range(0, len(forward), 8)
    ).decode("ascii")


def load_macro(export_path):
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    messages = {
        message["id"]: message
        for message in payload["messages"]
    }
    message = messages[MACRO_MESSAGE_ID]
    if message.get("from_id") != CREATOR_ID:
        raise AssertionError("macro-clue message is not creator-authored")
    return decode_reversed_bitstream(flatten_text(message.get("text", "")))


def load_creator_message(export_path, message_id):
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    messages = {
        message["id"]: message
        for message in payload["messages"]
    }
    message = messages[message_id]
    if message.get("from_id") != CREATOR_ID:
        raise AssertionError(f"message {message_id} is not creator-authored")
    return flatten_text(message.get("text", ""))


def split_replacement(source, target):
    source_upper = source.upper()
    target_upper = target.upper()
    prefix_length = 0
    while (
        prefix_length < min(len(source_upper), len(target_upper))
        and source_upper[prefix_length] == target_upper[prefix_length]
    ):
        prefix_length += 1

    suffix_length = 0
    while (
        suffix_length < len(source_upper) - prefix_length
        and suffix_length < len(target_upper) - prefix_length
        and source_upper[-suffix_length - 1] == target_upper[-suffix_length - 1]
    ):
        suffix_length += 1

    source_end = len(source_upper) - suffix_length if suffix_length else len(source_upper)
    target_end = len(target_upper) - suffix_length if suffix_length else len(target_upper)
    return {
        "prefix": source_upper[:prefix_length],
        "source_middle": source_upper[prefix_length:source_end],
        "target_middle": target_upper[prefix_length:target_end],
        "suffix": source_upper[source_end:],
    }


def initials(tokens):
    return "".join(token[0].upper() for token in tokens)


def finals(tokens):
    return "".join(token[-1].upper() for token in tokens)


def clue_readings():
    payload_tokens = (
        FINAL_CLAUSE_TOKENS[0],
        *FINAL_CLAUSE_TOKENS[4:],
    )
    payload_initials = initials(payload_tokens)
    return {
        "full_clause_initials": initials(FINAL_CLAUSE_TOKENS),
        "full_clause_finals": finals(FINAL_CLAUSE_TOKENS),
        "very_plus_a_true_giveaway_initials": payload_initials,
        "give_away_g": payload_initials[:-1],
    }


def element_parses(value):
    lower = value.lower()
    parses = []

    def visit(offset, current):
        if offset == len(lower):
            parses.append(tuple(current))
            return
        for width in (1, 2):
            symbol = lower[offset:offset + width]
            if symbol in ATOMIC_NUMBER:
                canonical = ELEMENT_SYMBOLS[ATOMIC_NUMBER[symbol] - 1]
                visit(offset + width, (*current, canonical))

    visit(0, ())
    return tuple(parses)


def creator_element_base_rate(export_path):
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    token_counts = Counter()
    for message in payload["messages"]:
        if message.get("from_id") != CREATOR_ID:
            continue
        text = flatten_text(message.get("text", ""))
        token_counts.update(re.findall(r"[A-Za-z]+", text.lower()))

    parsed = {}
    for token in token_counts:
        parses = element_parses(token)
        if parses:
            parsed[token] = parses

    def has_sum_span(parses, target_sum):
        for parse in parses:
            numbers = atomic_numbers(parse)
            for start in range(len(parse)):
                running = 0
                for end in range(start, len(parse)):
                    running += numbers[end]
                    if running == target_sum:
                        return True
                    if running > target_sum:
                        break
        return False

    def has_exact_span(parses, target):
        return any(
            tuple(parse[start:start + len(target)]) == target
            for parse in parses
            for start in range(len(parse) - len(target) + 1)
        )

    def replace_ph_with_v(token):
        return {
            token[:offset] + "v" + token[offset + 2:]
            for offset in range(len(token) - 1)
            if token[offset:offset + 2] == "ph"
        }

    profiles = {}
    for label, predicate in (
        ("all_lengths", lambda token: True),
        ("length_10", lambda token: len(token) == len(SPOKEN_PHASE_WORD)),
        ("length_8_to_12", lambda token: 8 <= len(token) <= 12),
    ):
        words = {
            token: parses
            for token, parses in parsed.items()
            if predicate(token)
        }
        sum16_words = {
            token
            for token, parses in words.items()
            if has_sum_span(parses, 16)
        }
        ph_words = {
            token
            for token, parses in words.items()
            if has_exact_span(parses, ("P", "H"))
        }
        target_words = {
            token
            for token in ph_words
            if TARGET_WORD.lower() in replace_ph_with_v(token)
        }
        profiles[label] = {
            "creator_word_types": sum(
                1 for token in token_counts if predicate(token)
            ),
            "element_parsable_word_types": len(words),
            "sum16_span_word_types": len(sum16_words),
            "ph_span_word_types": len(ph_words),
            "ph_span_words": tuple(sorted(ph_words)),
            "ph_to_salvation_word_types": len(target_words),
            "ph_to_salvation_words": tuple(sorted(target_words)),
            "element_parsable_token_occurrences": sum(
                token_counts[token] for token in words
            ),
            "sum16_span_token_occurrences": sum(
                token_counts[token] for token in sum16_words
            ),
            "ph_span_token_occurrences": sum(
                token_counts[token] for token in ph_words
            ),
        }
    return {
        "creator_message_count": sum(
            message.get("from_id") == CREATOR_ID
            for message in payload["messages"]
        ),
        "creator_word_types": len(token_counts),
        "profiles": profiles,
    }


def scheme_sensitivity_audit():
    schemes = {
        "atomic_number": lambda letter: ATOMIC_NUMBER[letter.lower()],
        "a1z26": lambda letter: ord(letter) - ord("A") + 1,
        "ascii_upper": ord,
        "scrabble_en": SCRABBLE_VALUES.__getitem__,
        "phone_keypad": PHONE_VALUES.__getitem__,
    }
    results = {}
    for label, value_of in schemes.items():
        old_sum = value_of("P") + value_of("H")
        new_value = value_of("V")
        results[label] = {
            "old_sum": old_sum,
            "new_value": new_value,
            "delta": new_value - old_sum,
            "matches_23_16_7": (
                (new_value, old_sum, new_value - old_sum)
                == EXPECTED_SUM_LIST
            ),
        }
    return results


def atomic_numbers(symbols):
    return tuple(ATOMIC_NUMBER[symbol.lower()] for symbol in symbols)


def checkerboard_code_count(value, escapes=("b", "e")):
    count = 0
    offset = 0
    while offset < len(value):
        width = 2 if value[offset] in escapes else 1
        if offset + width > len(value):
            raise ValueError("dangling checkerboard escape")
        count += 1
        offset += width
    return count


def elemental_topology():
    title_parses = element_parses(EXPECTED_TITLE)
    source_parses = element_parses(SPOKEN_PHASE_WORD)
    target_parses = element_parses(TARGET_WORD)
    transition = split_replacement(SPOKEN_PHASE_WORD, TARGET_WORD)
    old_middle_parses = element_parses(transition["source_middle"])
    new_middle_parses = element_parses(transition["target_middle"])
    if title_parses:
        raise AssertionError(
            "SalPhaseIon unexpectedly has a complete elemental parse; "
            "the historical community parse inserted an extra S"
        )
    if not all(
        len(parses) == 1
        for parses in (
            source_parses,
            target_parses,
            old_middle_parses,
            new_middle_parses,
        )
    ):
        raise AssertionError(
            "spoken-phase/target elemental tokenizations are not unique: "
            f"{source_parses}, {target_parses}, "
            f"{old_middle_parses}, {new_middle_parses}"
        )

    source_symbols = source_parses[0]
    target_symbols = target_parses[0]
    old_middle_symbols = old_middle_parses[0]
    new_middle_symbols = new_middle_parses[0]
    source_numbers = atomic_numbers(source_symbols)
    target_numbers = atomic_numbers(target_symbols)
    old_middle_numbers = atomic_numbers(old_middle_symbols)
    new_middle_numbers = atomic_numbers(new_middle_symbols)
    return {
        "title_has_element_parse": bool(title_parses),
        "source_symbols": source_symbols,
        "source_numbers": source_numbers,
        "source_sum": sum(source_numbers),
        "target_symbols": target_symbols,
        "target_numbers": target_numbers,
        "target_sum": sum(target_numbers),
        "old_middle_symbols": old_middle_symbols,
        "old_middle_numbers": old_middle_numbers,
        "new_middle_symbols": new_middle_symbols,
        "new_middle_numbers": new_middle_numbers,
        "transition": transition,
        "old_middle_sum": sum(old_middle_numbers),
        "new_middle_sum": sum(new_middle_numbers),
        "middle_sum_delta": sum(new_middle_numbers) - sum(old_middle_numbers),
        "element_count_delta": len(source_symbols) - len(target_symbols),
        "atomic_sum_delta": sum(target_numbers) - sum(source_numbers),
        "dbbi_raw_length": len(DBBI),
        "dbbi_be_code_count": checkerboard_code_count(DBBI),
        "target_count_times_al": len(target_symbols) * ATOMIC_NUMBER["al"],
        "source_count_times_al": len(source_symbols) * ATOMIC_NUMBER["al"],
        "matrix_instruction_bits": len("matrixsumlist") * 8,
        "atomic_transition_list": (
            sum(new_middle_numbers),
            sum(old_middle_numbers),
            sum(new_middle_numbers) - sum(old_middle_numbers),
        ),
    }


def screenplay_evidence(pdf_path):
    completed = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    normalized = re.sub(r"[^a-z]+", " ", completed.stdout.lower())
    normalized = re.sub(r"\s+", " ", normalized)
    phrases = (
        "anomaly revealed as both beginning and end",
        "salvation of zion",
        "the problem is choice",
        "but we already know",
        "blinding you from the simple and obvious truth",
    )
    return {phrase: phrase in normalized for phrase in phrases}


def fixed_candidates():
    return (
        EXPECTED_NEW_MIDDLE,
        "SalVATIon",
        TARGET_WORD,
        "SALVATION OF ZION",
        "THE SALVATION OF ZION",
    )


def audit(html_path, export_path, pdf_path):
    title = load_title(html_path)
    macro = load_macro(export_path)
    recognition_message = load_creator_message(
        export_path,
        RECOGNITION_MESSAGE_ID,
    )
    replacement = split_replacement(title, TARGET_WORD)
    readings = clue_readings()
    topology = elemental_topology()
    base_rate = creator_element_base_rate(export_path)
    scheme_sensitivity = scheme_sensitivity_audit()
    screenplay = screenplay_evidence(pdf_path)

    if title != EXPECTED_TITLE:
        raise AssertionError(f"unexpected archived title: {title!r}")
    if macro != EXPECTED_MACRO:
        raise AssertionError("creator macro clue does not match expected bytes")
    if not macro.endswith("verylaststepisatruegiveawaypromised"):
        raise AssertionError("macro clue lacks the expected final clause")
    if "salphation" not in recognition_message.lower():
        raise AssertionError("creator recognition message lacks salphation")
    if replacement != {
        "prefix": "SAL",
        "source_middle": EXPECTED_OLD_MIDDLE,
        "target_middle": EXPECTED_NEW_MIDDLE,
        "suffix": "ION",
    }:
        raise AssertionError(f"unexpected title replacement: {replacement}")
    if readings["give_away_g"] != EXPECTED_NEW_MIDDLE:
        raise AssertionError("bounded final-clause rebus does not produce VAT")
    if sum(value == EXPECTED_NEW_MIDDLE for value in readings.values()) != 1:
        raise AssertionError("VAT is not unique inside the declared reading family")
    if not all(screenplay.values()):
        raise AssertionError(f"missing screenplay evidence: {screenplay}")
    if topology["atomic_transition_list"] != EXPECTED_SUM_LIST:
        raise AssertionError(
            "PH -> V atomic-number transition does not reproduce [23,16,7]"
        )
    if not (
        topology["target_count_times_al"]
        == topology["dbbi_raw_length"]
        == 91
    ):
        raise AssertionError("7 x Al(13) does not reproduce DBBI raw length")
    if not (
        topology["source_count_times_al"]
        == topology["matrix_instruction_bits"]
        == 104
    ):
        raise AssertionError(
            "8 x Al(13) does not reproduce binary matrixsumlist length"
        )
    for profile in base_rate["profiles"].values():
        if profile["ph_to_salvation_words"] != ("salphation",):
            raise AssertionError(
                "creator-corpus lexical convergence is not uniquely salphation"
            )
    if tuple(
        label
        for label, result in scheme_sensitivity.items()
        if result["matches_23_16_7"]
    ) != ("atomic_number",):
        raise AssertionError("scheme-sensitivity family does not isolate atomic numbers")

    return {
        "title": title,
        "macro": macro,
        "recognition_message": recognition_message,
        "replacement": replacement,
        "readings": readings,
        "elemental_topology": topology,
        "elemental_base_rate": base_rate,
        "scheme_sensitivity": scheme_sensitivity,
        "screenplay": screenplay,
        "candidates": fixed_candidates(),
    }


def oracle_check(candidates, blobs):
    tested_keystrings = set()
    hits = {
        "cbc": [],
        "ecb": [],
        "stream": [],
        "keywrap": [],
    }
    for candidate in candidates:
        for form in sorted(answer_forms(candidate)):
            for keystring in keystr_forms(form, newline_variants=True):
                if keystring in tested_keystrings:
                    continue
                tested_keystrings.add(keystring)

                for variants in (None, EXTENDED_CIPHER_VARIANTS):
                    result = aes_try_open(
                        keystring,
                        kdf_variants=variants,
                        blobs=blobs,
                    )
                    if result:
                        hits["cbc"].append((candidate, keystring, result))

                result = aes_try_open_ecb(keystring, blobs=blobs)
                if result:
                    hits["ecb"].append((candidate, keystring, result))

                result = aes_try_open_stream(keystring, blobs=blobs)
                if result:
                    hits["stream"].append((candidate, keystring, result))

                for result in aes_keywrap_try_open_bytes(
                    keystring.encode(),
                    blobs=blobs,
                ):
                    hits["keywrap"].append((candidate, keystring, result))

    return {
        "candidate_count": len(candidates),
        "unique_keystrings": len(tested_keystrings),
        "blob_count": len(blobs),
        "hits": hits,
    }


def print_report(report):
    replacement = report["replacement"]
    print(f"[*] archived title: {report['title']}")
    print(
        "[*] fixed title mutation: "
        f"{replacement['prefix']}[{replacement['source_middle']}]"
        f"{replacement['suffix']} -> "
        f"{replacement['prefix']}[{replacement['target_middle']}]"
        f"{replacement['suffix']}"
    )
    print("[*] declared final-clause readings:")
    for label, value in report["readings"].items():
        marker = "  <-- fixed VAT target" if value == EXPECTED_NEW_MIDDLE else ""
        print(f"    {label}: {value}{marker}")
    topology = report["elemental_topology"]
    print("[*] unique elemental tokenizations:")
    print(
        "    archived title SalPhaseIon: no complete elemental parse "
        "(the old community parse inserted an extra S)"
    )
    print(
        "    creator word SALPHATION: "
        f"{' '.join(topology['source_symbols'])} -> "
        f"{list(topology['source_numbers'])}, sum={topology['source_sum']}"
    )
    print(
        "    target: "
        f"{' '.join(topology['target_symbols'])} -> "
        f"{list(topology['target_numbers'])}, sum={topology['target_sum']}"
    )
    print(
        "    atomic transition: "
        f"{' + '.join(topology['old_middle_symbols'])}="
        f"{topology['old_middle_sum']} -> "
        f"{' + '.join(topology['new_middle_symbols'])}="
        f"{topology['new_middle_sum']}; delta="
        f"{topology['middle_sum_delta']}; list="
        f"{list(topology['atomic_transition_list'])}"
    )
    print(
        "    matrix lengths: "
        f"{len(topology['target_symbols'])} x Al(13)="
        f"{topology['target_count_times_al']} raw DBBI; "
        f"{len(topology['source_symbols'])} x Al(13)="
        f"{topology['source_count_times_al']} binary matrixsumlist bits"
    )
    print("[*] creator-corpus elemental base rates:")
    for label, profile in report["elemental_base_rate"]["profiles"].items():
        parsable = profile["element_parsable_word_types"]
        sum16 = profile["sum16_span_word_types"]
        ph = profile["ph_span_word_types"]
        exact = profile["ph_to_salvation_word_types"]
        sum16_rate = sum16 / parsable if parsable else 0.0
        ph_rate = ph / parsable if parsable else 0.0
        print(
            f"    {label}: parsable={parsable}/"
            f"{profile['creator_word_types']} word types; "
            f"sum16={sum16} ({sum16_rate:.3%}); "
            f"exact P,H={ph} ({ph_rate:.3%}); "
            f"P,H -> fixed SALVATION={exact} "
            f"{list(profile['ph_to_salvation_words'])}"
        )
    print(
        "    exact P,H creator words: "
        f"{list(report['elemental_base_rate']['profiles']['all_lengths']['ph_span_words'])}"
    )
    print("[*] fixed PH-versus-V scheme sensitivity:")
    for label, result in report["scheme_sensitivity"].items():
        marker = "  <-- exact [23,16,7]" if result["matches_23_16_7"] else ""
        print(
            f"    {label}: P+H={result['old_sum']}; "
            f"V={result['new_value']}; delta={result['delta']}{marker}"
        )
    print("[*] screenplay evidence:")
    for phrase, present in report["screenplay"].items():
        print(f"    {present!s:<5} {phrase}")
    print(
        "[*] status: exact lexical convergence, but generic atomic sum-16 "
        "matches have a high creator-corpus base rate; operand role remains "
        "unproven"
    )


def self_test():
    assert decode_reversed_bitstream("01000110 10000110") == "ab"
    assert split_replacement("SalPhaseIon", "salvation") == {
        "prefix": "SAL",
        "source_middle": "PHASE",
        "target_middle": "VAT",
        "suffix": "ION",
    }
    assert clue_readings() == {
        "full_clause_initials": "VLSIATG",
        "full_clause_finals": "YTPSAEY",
        "very_plus_a_true_giveaway_initials": "VATG",
        "give_away_g": "VAT",
    }
    assert fixed_candidates() == (
        "VAT",
        "SalVATIon",
        "SALVATION",
        "SALVATION OF ZION",
        "THE SALVATION OF ZION",
    )
    topology = elemental_topology()
    assert not topology["title_has_element_parse"]
    assert topology["source_symbols"] == (
        "S", "Al", "P", "H", "At", "I", "O", "N",
    )
    assert topology["target_symbols"] == (
        "S", "Al", "V", "At", "I", "O", "N",
    )
    assert topology["source_sum"] == 198
    assert topology["target_sum"] == 205
    assert topology["atomic_sum_delta"] == 7
    assert topology["element_count_delta"] == 1
    assert topology["old_middle_symbols"] == ("P", "H")
    assert topology["new_middle_symbols"] == ("V",)
    assert topology["atomic_transition_list"] == EXPECTED_SUM_LIST
    assert topology["dbbi_raw_length"] == 91
    assert topology["dbbi_be_code_count"] == 63
    assert topology["matrix_instruction_bits"] == 104
    sensitivity = scheme_sensitivity_audit()
    assert sensitivity["atomic_number"]["matches_23_16_7"]
    assert not any(
        result["matches_23_16_7"]
        for label, result in sensitivity.items()
        if label != "atomic_number"
    )
    print(
        "[*] self-test OK: title diff, bounded clue readings, unique elemental "
        "topology, fixed candidates"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument(
        "--export",
        type=Path,
        default=DEFAULT_EXPORT_DIR / "result.json",
    )
    parser.add_argument("--screenplay", type=Path, default=PDF_PATH)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--include-quarantined", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    report = audit(args.html, args.export, args.screenplay)
    print_report(report)

    if args.oracle:
        blobs = dict(BLOBS)
        if args.include_quarantined:
            blobs.update(QUARANTINED_BLOBS)
        result = oracle_check(report["candidates"], blobs)
        total_hits = sum(len(values) for values in result["hits"].values())
        print(
            f"[*] oracle: candidates={result['candidate_count']} "
            f"unique_keystrings={result['unique_keystrings']} "
            f"blobs={result['blob_count']} hits={total_hits}"
        )
        for family, family_hits in result["hits"].items():
            print(f"    {family}: {len(family_hits)}")
            for hit in family_hits:
                print(f"      {hit!r}")


if __name__ == "__main__":
    main()
