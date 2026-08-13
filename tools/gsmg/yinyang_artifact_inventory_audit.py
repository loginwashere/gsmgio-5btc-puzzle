#!/usr/bin/env python3
"""Build the bounded, assertion-backed GSMG yin-yang artifact inventory.

This implements Phases 1-2 of doc/GSMG_YINYANG_ARTIFACT_IDENTIFICATION_PLAN.md.
It inventories exactly seven pre-registered artifact families, evaluates the
pre-registered qualification table, and runs no cipher or password oracle.
"""

import argparse
import hashlib
import json
from pathlib import Path

from data import DBBI, SALPHASEION_BLOB_B64
from denis_prime_extraction_audit import SOURCE, TARGET, recover_position_masks
from first_piece_color_reconstruction import DEFAULT_IMAGE, reconstruct
from flo_prime_walk_provenance_audit import (
    EXPECTED_FLO_POSITIONS_1_INDEXED,
    audit as audit_prime_walk,
)
from page_structure_audit import DEFAULT_HTML, audit as audit_page
from prime_matrixsum_reconstruction import (
    PDF_PATH,
    bounded_indexings,
    edge_letters,
    load_architect_words,
    matrixsumlist,
    mirror9,
)
from telegram_export_manifest import DEFAULT_EXPORT_DIR, load_export, plain_text

ROOT = Path(__file__).resolve().parents[2]
BOOK_OCR = ROOT / "wordlists" / "gsmg" / "cosmic_duality_book_full_text.txt"
CREATOR_ID = "user9815232"
PRIVATE_KEY_PHRASE = "THE PRIVATE KEYS BELONG TO HALF AND BETTER HALF"

EXPECTED_FILE_HASHES = {
    "rabbit_image": "5e8d84b88f8f829428df5d2a8bf36c7268346f169b799ac7570b6223990d204f",
    "architect_pdf": "2b9d43c9bb32fe85b1ed7651b095855e6ea7a25a236853d7823ea92b211d0db4",
    "salphaseion_page": "b13cbc5c2935dc3e9ff8bf71681f2ef61317fefdce04159129877244a92a3947",
    "book_ocr": "69e8021309957a204628c3c0045108b8f69f50b0a1da7a76abfe6783b36d4c3d",
    "book_cover": "3a9b0a6ecacef83e1ef9f688303105570b3dcae95fd82be75f1fcbd2f5fddd04",
    "guide_one": "475456f9ecf8fd56ef6247f081ba8ee0796eef3f6ed3be0ca01c4a5ee0bfb85a",
    "guide_two": "efdf08b8268f883eafb136a5a37a9e04d236374ebcf95900f71b99d0c1172671",
}

MESSAGE_REQUIREMENTS = {
    1710: ("user9815232", "Yellow has a number and so does Blue"),
    6884: ("user9815232", 'another door might be found on {1 },{4} ,{21}'),
    8310: ("user925838121", ""),
    8311: ("user9815232", "That is very specific"),
    8315: ("user9815232", "scary specific"),
    8328: ("user9815232", "provided a very specific hint already"),
    8446: ("user9815232", "00100110 10100110"),
    8483: ("user9815232", "👆"),
    9599: ("user9815232", 'hit a "ying yang"'),
    9603: ("user9815232", "Both?"),
    9607: ("user9815232", "You have all the info"),
    20223: ("user9815232", "Regular Bitcoin Private key"),
    39224: ("user9815232", "when yingyang is reached, 2 hours max"),
    39237: ("user9815232", "It’s the next phase"),
    39937: ("user6985476275", "What are your thoughts on this approach?"),
    54430: ("user398109413", ""),
    60325: ("user398109413", "guide to yellow-blue-primes"),
    60333: ("user398109413", "ncsyangcahiriasogaleafayanestve"),
    60886: ("user398109413", "One"),
    60887: ("user398109413", "Two"),
}

EXPECTED_REPLY_TO = {
    8311: 8310,
    9607: 9605,
    39237: 39233,
    60325: 39937,
    60333: 60325,
    60886: 39937,
    60887: 54430,
}

QUALIFICATION = {
    "but_hye_rails": {
        "primary": True,
        "visible": True,
        "dual": True,
        "correct_boundary": True,
        "independent_discriminator": False,
        "reason": (
            "Mechanically derived at the Architect choice boundary and BUT matches "
            "the next screenplay word, but Phase 223 found the partial B/H+fixed-E "
            "mirror non-distinctive and the set closure permutation-invariant."
        ),
    },
    "selected_complement": {
        "primary": True,
        "visible": True,
        "dual": True,
        "correct_boundary": False,
        "independent_discriminator": True,
        "reason": (
            "Exact complementary 31/60 mask with strong convergence, but it is "
            "the yellowblueprimes output and therefore precedes matrixsumlist."
        ),
    },
    "paired_page_objects": {
        "primary": True,
        "visible": True,
        "dual": False,
        "correct_boundary": False,
        "independent_discriminator": False,
        "reason": (
            "The two authenticated textareas are visible together, but DOM "
            "adjacency alone supplies neither complementarity nor a consumer edge."
        ),
    },
    "first_piece_polarity": {
        "primary": True,
        "visible": True,
        "dual": True,
        "correct_boundary": False,
        "independent_discriminator": True,
        "reason": (
            "Positive control: exact complementary color-bit readings with FEFE, "
            "but it is the chain input two stages before lastwords."
        ),
    },
    "cosmic_duality_book": {
        "primary": True,
        "visible": True,
        "dual": True,
        "correct_boundary": False,
        "independent_discriminator": True,
        "reason": (
            "Creator-confirmed physical clue with explicit yin/yang content, but "
            "no established operation connects it to the Architect boundary. "
            "Phase 260/261: the book's gold/black yin-yang drop-cap design "
            "(pixel-confirmed) decorates the title's C/D initials AND ordinary "
            "body paragraphs book-wide -- a house style, not title-unique. Roman "
            "CD=400 matches the yellow prime sum, but as corroboration/possible "
            "coincidence rather than an independent echo. Phase 262: "
            "(page-A1Z26(letter)) mod 26 over Chapter 2's first three drop caps "
            "spells YIN exactly (pixel-confirmed); no YANG counterpart found, "
            "bounded lead only. Still no operation."
        ),
    },
    "one_two_guides": {
        "primary": False,
        "visible": True,
        "dual": True,
        "correct_boundary": False,
        "independent_discriminator": False,
        "reason": (
            "The pair is retained media and converges on one mask, but both the "
            "construction and One/Two labels are community-authored."
        ),
    },
    "salph_key_halves": {
        "primary": True,
        "visible": False,
        "dual": True,
        "correct_boundary": False,
        "independent_discriminator": True,
        "reason": (
            "The ciphertext split and half/better-half phrase are real, but two "
            "private keys remain a hypothetical future plaintext shape."
        ),
    },
}

EXPECTED_ARTIFACT_ORDER = tuple(QUALIFICATION)


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256_text(value):
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def source_path(path):
    path = Path(path).resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def media_path(export_dir, message):
    relative = message.get("photo") or message.get("file")
    if not relative:
        raise AssertionError(f"message {message['id']} has no retained media")
    path = Path(export_dir) / relative
    if not path.is_file():
        raise AssertionError(f"message {message['id']} media is missing: {path}")
    return path


def canonical_message_hash(message):
    payload = {
        "id": message["id"],
        "date": message.get("date"),
        "from_id": message.get("from_id"),
        "reply_to_message_id": message.get("reply_to_message_id"),
        "text": plain_text(message),
        "media": message.get("photo") or message.get("file"),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(encoded)


def load_evidence(export_dir):
    data = load_export(export_dir)
    messages = {message["id"]: message for message in data["messages"]}
    for message_id, (from_id, fragment) in MESSAGE_REQUIREMENTS.items():
        message = messages.get(message_id)
        if message is None:
            raise AssertionError(f"missing required Telegram message {message_id}")
        if message.get("from_id") != from_id:
            raise AssertionError(
                f"message {message_id} sender drift: {message.get('from_id')!r}"
            )
        if fragment not in plain_text(message):
            raise AssertionError(
                f"message {message_id} text drift: missing {fragment!r}"
            )
    for message_id, reply_to in EXPECTED_REPLY_TO.items():
        if messages[message_id].get("reply_to_message_id") != reply_to:
            raise AssertionError(f"message {message_id} reply target drift")
    for message_id in (1710, 6884, 8311, 8315, 8328, 8446, 8483, 9599, 9603, 9607,
                       20223, 39224, 39237):
        if messages[message_id].get("from_id") != CREATOR_ID:
            raise AssertionError(f"message {message_id} is no longer creator-authored")
    return messages


def file_evidence(label, path):
    digest = sha256_file(path)
    if digest != EXPECTED_FILE_HASHES[label]:
        raise AssertionError(f"{label} hash drift: {digest}")
    return {
        "path": source_path(path),
        "sha256": digest,
        "size": Path(path).stat().st_size,
    }


def message_evidence(messages, *message_ids):
    return [
        {
            "message_id": message_id,
            "date": messages[message_id].get("date"),
            "from": messages[message_id].get("from"),
            "from_id": messages[message_id].get("from_id"),
            "reply_to_message_id": messages[message_id].get("reply_to_message_id"),
            "sha256": canonical_message_hash(messages[message_id]),
        }
        for message_id in message_ids
    ]


def artifact_record(
    artifact_id,
    sources,
    content_hashes,
    left_component,
    right_component,
    invariant,
    transition_distance,
    transition_relation,
    visible,
    provenance_status,
    tested_operations,
):
    qualification = dict(QUALIFICATION[artifact_id])
    qualification["all_core"] = all(
        qualification[field]
        for field in ("primary", "visible", "dual", "correct_boundary")
    )
    qualification["qualifies_for_local_mechanics"] = (
        qualification["all_core"]
        and qualification["independent_discriminator"]
    )
    if visible != qualification["visible"]:
        raise AssertionError(f"{artifact_id} visibility disagrees with frozen table")
    return {
        "artifact_id": artifact_id,
        "sources": sources,
        "content_hashes": content_hashes,
        "left_component": left_component,
        "right_component": right_component,
        "fixed_center_or_invariant": invariant,
        "transition_distance_from_lastwords": transition_distance,
        "transition_relation": transition_relation,
        "visible_before_decryption": visible,
        "provenance_status": provenance_status,
        "already_tested_operations": tested_operations,
        "qualification": qualification,
    }


def build_inventory(export_dir=DEFAULT_EXPORT_DIR):
    messages = load_evidence(export_dir)
    rabbit = reconstruct(DEFAULT_IMAGE)
    if rabbit["prime_value"] != 574061 or rabbit["rose_hex"] != "F73D92":
        raise AssertionError("first-piece complementary values drifted")
    if rabbit["fefe"]["value"] != 0 or rabbit["fefe"]["spiral_0"] != 163:
        raise AssertionError("first-piece FEFE invariant drifted")

    matrix, sum_list = matrixsumlist(rabbit["prime_value"])
    architect_words, first_after_choice = load_architect_words()
    selected_words = bounded_indexings(architect_words, sum_list)["forward_one"]
    first_edges, last_edges = edge_letters(selected_words)
    if matrix != [[5, 7, 4], [0, 6, 1]] or sum_list != (23, 16, 7):
        raise AssertionError("matrixsumlist reconstruction drifted")
    if selected_words != ("both", "ultimately", "the"):
        raise AssertionError("Architect selected words drifted")
    if first_edges != "but" or last_edges != "hye" or first_after_choice != "but":
        raise AssertionError("BUT/HYE boundary rails drifted")
    if mirror9("b") != "h" or mirror9("e") != "e":
        raise AssertionError("native a-i mirror invariant drifted")

    prime_walk = audit_prime_walk()
    mask = recover_position_masks(SOURCE, TARGET)[2]
    mask_positions = tuple(position + 1 for position in mask)
    if mask_positions != EXPECTED_FLO_POSITIONS_1_INDEXED:
        raise AssertionError("selected/complement mask drifted")
    selected_text = "".join(SOURCE[position] for position in mask)
    mask_set = set(mask)
    complement_text = "".join(
        character for position, character in enumerate(SOURCE)
        if position not in mask_set
    )
    if selected_text != TARGET or prime_walk["flo_selected_plaintext"] != TARGET:
        raise AssertionError("selected text no longer matches Denis/Flo convergence")
    if len(complement_text) != 60:
        raise AssertionError("selected/complement profile drifted")

    page = audit_page(DEFAULT_HTML)
    if page["dom_order"] != ["SalPhaseIon", "Cosmic Duality"]:
        raise AssertionError("page DOM order drifted")
    salph_segments = {
        segment["name"]: segment
        for segment in page["salphaseion"]["segments"]
    }
    if (
        salph_segments["salphaseion_aes_prefix"]["length"] != 64
        or salph_segments["salphaseion_aes_suffix"]["length"] != 64
    ):
        raise AssertionError("SALPH visible 64/64 split drifted")

    book_text = BOOK_OCR.read_text(encoding="utf-8")
    book_fragments = (
        "Harmony from a Divided Universe",
        "holds the seed of its opposite",
        "both the yin and yang are present to the same degree",
    )
    if any(fragment not in book_text for fragment in book_fragments):
        raise AssertionError("Cosmic Duality yin-yang text drifted")

    book_cover_path = media_path(export_dir, messages[8310])
    guide_one_path = media_path(export_dir, messages[39937])
    guide_two_path = media_path(export_dir, messages[54430])

    common_creator_sources = message_evidence(
        messages, 8446, 8483, 9599, 9603, 9607, 39224, 39237
    )
    rabbit_file = file_evidence("rabbit_image", DEFAULT_IMAGE)
    architect_file = file_evidence("architect_pdf", PDF_PATH)
    page_file = file_evidence("salphaseion_page", DEFAULT_HTML)
    book_file = file_evidence("book_ocr", BOOK_OCR)
    cover_file = file_evidence("book_cover", book_cover_path)
    guide_one_file = file_evidence("guide_one", guide_one_path)
    guide_two_file = file_evidence("guide_two", guide_two_path)

    artifacts = [
        artifact_record(
            "but_hye_rails",
            {
                "files": [rabbit_file, architect_file],
                "messages": common_creator_sources,
            },
            {
                "selected_words": sha256_text("both|ultimately|the"),
                "left": sha256_text(first_edges),
                "right": sha256_text(last_edges),
            },
            "BUT (beginnings)",
            "HYE (endings)",
            "B mirrors H in a-i while E is fixed; BUT is the first word after choice",
            0,
            "Immediate mechanical output of lastwordsbeforearchichoice",
            True,
            "puzzle-derived; creator chain authenticated; yin-yang identification unconfirmed",
            [
                "two-row alignment and column pairs",
                "native a-i filtering and B/H mirror",
                "H|YE|BUT rebus",
                "direct password/route/hash forms",
                "{h,e} monoalphabetic, autokey, and chain-addition models",
            ],
        ),
        artifact_record(
            "selected_complement",
            {
                "files": [rabbit_file, guide_one_file, guide_two_file],
                "messages": message_evidence(
                    messages, 39937, 54430, 60325, 60333, 60886, 60887
                ),
            },
            {
                "selected": sha256_text(selected_text),
                "complement": sha256_text(complement_text),
                "mask_positions": sha256_text(",".join(map(str, mask_positions))),
            },
            selected_text,
            complement_text,
            "Exact disjoint 31/60 partition of the fixed 91-character source",
            -2,
            "Output of yellowblueprimes, before matrixsumlist and lastwords",
            True,
            "mechanically puzzle-derived; concrete mask and labels are community-authored",
            [
                "literal substring search",
                "zeroing and complement reads",
                "7x13/13x7 reads and sums",
                "selected/complement rails",
                "raw/SHA oracle forms",
            ],
        ),
        artifact_record(
            "paired_page_objects",
            {
                "files": [page_file],
                "messages": common_creator_sources,
            },
            {
                "dom_order": sha256_text("|".join(page["dom_order"])),
                "salph_blob": sha256_text(SALPHASEION_BLOB_B64),
            },
            "SalPhaseIon textarea",
            "Cosmic Duality textarea",
            "Fixed DOM order and two static textarea objects; no demonstrated complement",
            None,
            "Visible container of the chain, not an output produced at its boundary",
            True,
            "authenticated archived page; no artifact-specific creator confirmation",
            [
                "DOM order and textarea geometry",
                "exact segment and split-point audit",
                "cross-blob pooled oracle coverage",
                "staged SALPH-to-COSMIC pipeline",
            ],
        ),
        artifact_record(
            "first_piece_polarity",
            {
                "files": [rabbit_file],
                "messages": message_evidence(messages, 1710, 6884),
            },
            {
                "blue_one_bits": sha256_text(rabbit["blue_one_bits"]),
                "yellow_one_bits": sha256_text(rabbit["yellow_one_bits"]),
                "fefe": sha256_text(json.dumps(rabbit["fefe"], sort_keys=True)),
            },
            "blue=1/yellow=0 -> F73D92",
            "yellow=1/blue=0 -> 574061",
            "Bitwise complementary readings plus one separately inserted FEFE zero event",
            -2,
            "Supplies yellowblueprimes and therefore precedes matrixsumlist",
            True,
            "authenticated puzzle image and creator-directed reconstruction",
            [
                "spiral color-bit reconstruction",
                "FEFE insertion and prime walk",
                "zeroing/deletion/nibble families",
                "route/hash forms",
            ],
        ),
        artifact_record(
            "cosmic_duality_book",
            {
                "files": [cover_file, book_file],
                "messages": message_evidence(messages, 8310, 8311, 8315, 8328),
            },
            {
                "yin": sha256_text("yin"),
                "yang": sha256_text("yang"),
                "seed_invariant": sha256_text("each force holds the seed of its opposite"),
            },
            "yin: dark force containing a speck of yang",
            "yang: pale force containing a germ of yin",
            "Opposed halves in balance, each visibly containing the seed of the other",
            None,
            "Creator-confirmed clue artifact, but no operation reaches it from lastwords",
            True,
            "creator-confirmed book-cover lead; retained OCR complete, including previously-missing physical pages 57-58 (recovered 2026-08-13)",
            [
                "complete retained-page OCR keyword sweep",
                "book-motivated transforms",
                "Looking Forward candidate audit",
                "Jacque Fresco candidate audit",
            ],
        ),
        artifact_record(
            "one_two_guides",
            {
                "files": [guide_one_file, guide_two_file],
                "messages": message_evidence(
                    messages, 39937, 54430, 60325, 60333, 60886, 60887
                ),
            },
            {
                "one_media": guide_one_file["sha256"],
                "two_media": guide_two_file["sha256"],
                "shared_mask": sha256_text(",".join(map(str, mask_positions))),
            },
            "One: Nik's yellow-blue-primes guide",
            "Two: Denis's 31-position mask image",
            "Both community constructions converge on the same 31-position mask",
            -2,
            "Community reconstruction of yellowblueprimes, before the boundary",
            True,
            "community-only; no creator confirmation tied to the concrete pair",
            [
                "guide row-sum audit",
                "corrected FEFE policy family and null",
                "Flo/Denis exact-mask convergence",
                "prime-walk output consumption",
            ],
        ),
        artifact_record(
            "salph_key_halves",
            {
                "files": [page_file],
                "messages": message_evidence(messages, 20223),
            },
            {
                "salph_blob": sha256_text(SALPHASEION_BLOB_B64),
                "first_base64_half": sha256_text(SALPHASEION_BLOB_B64[:64]),
                "second_base64_half": sha256_text(SALPHASEION_BLOB_B64[64:]),
                "private_key_phrase": sha256_text(PRIVATE_KEY_PHRASE),
            },
            "hypothetical first 32-byte private key",
            "hypothetical second 32-byte private key",
            "80-byte ciphertext permits 64 data bytes plus a full 16-byte pad block",
            None,
            "Expected future plaintext shape, not an artifact visible at lastwords",
            False,
            "authenticated ciphertext and creator-confirmed output type; plaintext halves hypothetical",
            [
                "padded 64-byte binary-material Tier 1 and Tier 2",
                "nopad fixed-window Tier 1",
                "CBC/ECB/stream/Key-Wrap cipher families",
                "raw key, WIF, hex, sum, concat-hash, and XOR candidates",
            ],
        ),
    ]

    if tuple(item["artifact_id"] for item in artifacts) != EXPECTED_ARTIFACT_ORDER:
        raise AssertionError("artifact universe or order drifted")
    qualifying = [
        item["artifact_id"]
        for item in artifacts
        if item["qualification"]["qualifies_for_local_mechanics"]
    ]
    if qualifying:
        raise AssertionError(f"pre-registered qualification result drifted: {qualifying}")

    return {
        "objective": "Identify a visible, transition-adjacent yin-yang artifact without an oracle",
        "frozen_artifact_count": len(artifacts),
        "creator_recognition_messages": common_creator_sources,
        "artifacts": artifacts,
        "qualifying_artifacts": qualifying,
        "promotion_result": {
            "promoted": [],
            "reason": (
                "Phase 223 retains BUT/HYE as a robust boundary reconstruction but "
                "removes its independent yin-yang discriminator. No artifact clears "
                "all gates, and no artifact is promoted."
            ),
        },
        "stop_rule": (
            "Stop: no retained artifact currently supplies both the full evidence "
            "qualification and one surviving deterministic downstream operation."
        ),
    }


def print_report(report):
    print(
        f"[*] frozen artifact inventory: {report['frozen_artifact_count']} families "
        "(no cipher oracle)"
    )
    print(
        "artifact                         P V D B I  core  local  transition"
    )
    for artifact in report["artifacts"]:
        q = artifact["qualification"]
        flags = " ".join(
            "Y" if q[field] else "N"
            for field in (
                "primary",
                "visible",
                "dual",
                "correct_boundary",
                "independent_discriminator",
            )
        )
        print(
            f"{artifact['artifact_id']:<32} {flags}  "
            f"{'Y' if q['all_core'] else 'N':>4}  "
            f"{'Y' if q['qualifies_for_local_mechanics'] else 'N':>5}  "
            f"{artifact['transition_relation']}"
        )
    print(f"[*] qualifying artifacts: {report['qualifying_artifacts']}")
    print(f"[*] promotion: {report['promotion_result']['reason']}")
    print(f"[*] {report['stop_rule']}")


def self_test(export_dir=DEFAULT_EXPORT_DIR):
    report = build_inventory(export_dir)
    assert report["frozen_artifact_count"] == 7
    assert report["qualifying_artifacts"] == []
    assert report["promotion_result"]["promoted"] == []
    assert all(
        len(artifact["content_hashes"]) >= 2
        for artifact in report["artifacts"]
    )
    assert all(
        artifact["sources"]["files"]
        for artifact in report["artifacts"]
    )
    print(
        "[*] self-test OK: seven frozen artifacts, source hashes, message "
        "relationships, qualification table, and stop rule verified"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = build_inventory(args.export_dir)
    self_test(args.export_dir)
    if args.self_test:
        return
    print_report(report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[*] wrote {args.json_out}")


if __name__ == "__main__":
    main()
