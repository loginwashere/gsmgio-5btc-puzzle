#!/usr/bin/env python3
"""Bounded consumer for the Stage-0 annotator's "G in the shadows" rule.

Within each of the two marked text rows, every uppercase G has the same
#383838 pixel count (4 in the large banner font, 2 in the small address
font).  Use that row-local G count as the selector and retain non-G glyphs
with the same count.  This is narrower than inventing a cipher for all 17
non-G glyphs and preserves the image's two different font scales.
"""

import argparse

from PIL import Image

from cb_common import BLOBS
from remaining_structural_avenues_audit import material_family
from stage0_footer_palette_layer_audit import (
    ADDRESS,
    ADDRESS_X,
    ADDRESS_Y,
    BANNER,
    BANNER_X,
    BANNER_Y,
    IMAGE_PATH,
    TARGET,
    glyph_histograms,
)

ELEMENTS = {"O": 8, "C": 6, "Be": 4}
ORACLE_CANDIDATES = ("OCBe", "864")
PERIODIC_SYMBOLS = frozenset(
    "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe "
    "Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In "
    "Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf "
    "Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm "
    "Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split()
)


def consume_row(image, label, text, x_boxes, y_box):
    histograms = glyph_histograms(image, text, x_boxes, y_box)
    counts = tuple(histogram[TARGET] for histogram in histograms)
    g_counts = tuple(count for character, count in zip(text, counts) if character == "G")
    if not g_counts or len(set(g_counts)) != 1:
        raise AssertionError(f"{label}: uppercase G counts are not a single reference: {g_counts}")
    reference = g_counts[0]
    matching = "".join(
        character for character, count in zip(text, counts) if count == reference
    )
    payload = "".join(
        character
        for character, count in zip(text, counts)
        if character != "G" and count == reference
    )
    residue = "".join(
        character
        for character, count in zip(text, counts)
        if character != "G" and count != 0 and count != reference
    )
    lowercase_g_counts = tuple(
        count for character, count in zip(text, counts) if character == "g"
    )
    return {
        "label": label,
        "reference_count": reference,
        "g_counts": g_counts,
        "lowercase_g_counts": lowercase_g_counts,
        "matching_with_g": matching,
        "payload": payload,
        "residue": residue,
        "residue_count": len(residue),
        "selected_text": "".join(
            character for character, count in zip(text, counts) if count
        ),
        "selected_counts": tuple(count for count in counts if count),
    }


def element_parses(text):
    """All exact-case periodic-symbol segmentations of a short string."""
    memo = {}

    def walk(offset):
        if offset == len(text):
            return ((),)
        if offset in memo:
            return memo[offset]
        parses = []
        for width in (1, 2):
            symbol = text[offset : offset + width]
            if symbol not in PERIODIC_SYMBOLS:
                continue
            parses.extend((symbol,) + tail for tail in walk(offset + width))
        memo[offset] = tuple(parses)
        return memo[offset]

    return walk(0)


def marker_null(rows, casefold=False):
    def key(character):
        return character.lower() if casefold else character

    shared = set(key(character) for character in rows[0]["selected_text"])
    for row in rows[1:]:
        shared &= set(key(character) for character in row["selected_text"])

    reports = []
    for marker in sorted(shared):
        references = []
        payload_parts = []
        valid = True
        marker_counts_by_row = []
        for row in rows:
            pairs = tuple(zip(row["selected_text"], row["selected_counts"]))
            marker_counts = tuple(
                count for character, count in pairs if key(character) == marker
            )
            marker_counts_by_row.append(marker_counts)
            if not marker_counts or len(set(marker_counts)) != 1:
                valid = False
                break
            reference = marker_counts[0]
            references.append(reference)
            payload_parts.append(
                "".join(
                    character
                    for character, count in pairs
                    if key(character) != marker and count == reference
                )
            )
        payload = "".join(payload_parts) if valid else None
        reports.append(
            {
                "marker": marker,
                "valid": valid,
                "marker_counts_by_row": tuple(marker_counts_by_row),
                "references": tuple(references),
                "payload": payload,
                "element_parses": element_parses(payload) if payload is not None else (),
            }
        )
    return tuple(reports)


def audit():
    image = Image.open(IMAGE_PATH).convert("RGB")
    rows = (
        consume_row(image, "banner", BANNER, BANNER_X, BANNER_Y),
        consume_row(image, "address", ADDRESS, ADDRESS_X, ADDRESS_Y),
    )
    payload = "".join(row["payload"] for row in rows)
    residue = "".join(row["residue"] for row in rows)
    symbols = (payload[0], payload[1], payload[2:])
    atomic_numbers = tuple(ELEMENTS[symbol] for symbol in symbols)
    case_sensitive_null = marker_null(rows, casefold=False)
    casefold_null = marker_null(rows, casefold=True)
    return {
        "rows": rows,
        "payload": payload,
        "residue": residue,
        "residue_count": len(residue),
        "element_symbols": symbols,
        "atomic_numbers": atomic_numbers,
        "atomic_string": "".join(str(number) for number in atomic_numbers),
        "constant_step": tuple(
            right - left for left, right in zip(atomic_numbers, atomic_numbers[1:])
        ),
        "case_sensitive_marker_null": case_sensitive_null,
        "casefold_marker_null": casefold_null,
        "oracle": material_family(ORACLE_CANDIDATES, BLOBS),
    }


def self_test():
    report = audit()
    banner, address = report["rows"]
    assert banner["reference_count"] == 4
    assert banner["g_counts"] == (4, 4, 4)
    assert banner["matching_with_g"] == "GGOG"
    assert banner["payload"] == "O"
    assert banner["residue"] == "S5BCPUC"
    assert address["reference_count"] == 2
    assert address["g_counts"] == (2, 2)
    assert address["lowercase_g_counts"] == (3,)
    assert address["matching_with_g"] == "GGCBe"
    assert address["payload"] == "CBe"
    assert address["residue"] == "M9g2cP"
    assert report["payload"] == "OCBe"
    assert report["residue_count"] == 13
    assert report["element_symbols"] == ("O", "C", "Be")
    assert report["atomic_numbers"] == (8, 6, 4)
    assert report["constant_step"] == (-2, -2)
    sensitive = {row["marker"]: row for row in report["case_sensitive_marker_null"]}
    assert tuple(sensitive) == ("B", "C", "G", "P")
    assert {marker: row["payload"] for marker, row in sensitive.items()} == {
        "B": "SCPCGGCe",
        "C": "SBPGGBe",
        "G": "OCBe",
        "P": "SBCCM92c",
    }
    assert sensitive["G"]["element_parses"] == (("O", "C", "Be"),)
    assert all(
        not row["element_parses"] for marker, row in sensitive.items() if marker != "G"
    )
    folded = {row["marker"]: row for row in report["casefold_marker_null"]}
    assert tuple(folded) == ("b", "c", "g", "p")
    assert folded["g"]["valid"] is False
    assert folded["g"]["marker_counts_by_row"] == ((4, 4, 4), (2, 2, 3))
    assert report["oracle"]["candidate_count"] == 2
    assert report["oracle"]["unique_material_count"] == 15
    assert report["oracle"]["hits"] == []
    print("[*] self-test OK: G-count consumer yields OCBe -> O/C/Be -> 8/6/4")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return
    report = audit()
    for row in report["rows"]:
        print(
            f"[*] {row['label']}: G count={row['reference_count']}; "
            f"matching={row['matching_with_g']}; payload={row['payload']}; "
            f"residue={row['residue']}"
        )
    print(
        f"[*] combined: {report['payload']} -> {report['element_symbols']} -> "
        f"{report['atomic_numbers']} -> {report['atomic_string']}"
    )
    print(f"[*] case-sensitive marker null: {report['case_sensitive_marker_null']}")
    print(f"[*] casefold marker null: {report['casefold_marker_null']}")
    oracle = report["oracle"]
    print(
        f"[*] oracle: {oracle['candidate_count']} candidates / "
        f"{oracle['unique_material_count']} materials / {len(oracle['hits'])} hits"
    )


if __name__ == "__main__":
    main()
