#!/usr/bin/env python3
"""Verify the November Telegram review from its actual inputs; never run attachments.

The supplemental candidate set is frozen in the companion verification scope.
All outputs are separate from the previous agent's checker/result.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

import cb_common
import endgame_map_u1_u5_check as consumer
import telegram_2026_11_04_claims_check as previous
from data import COSMIC_BLOB_B64, DBBI, FAED, PHASE32_BLOB_B64, SALPHASEION_BLOB_B64
from key_shape_classifier import bip39_checksum_valid, wif_to_private_key
from naddiseo_update_review_2026_11_04 import decrypt, inspect
from phase386_btcseed_bifid_faed_decode_audit import build_grid
from phase525_dbbi_selection_a_reconstruction import enumerate_complete_parses, is_prime
from phase550_board_profiled_frequency import answer_321, phase32_plaintext
from qr_fafafa_tile_predictability_audit import load_finders
from rabbit_cryptojs import evp_key_iv, keystream

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "_work/telegram_2026_11_04_verification"
RESULT = Path(__file__).with_name("telegram_2026_11_04_independent_result.json")
EXPORT_ROOT = Path("/home/loginwashere/Downloads/Telegram Desktop")
PROTOCOL = ROOT / "doc/Brainstorms/2026-11-04 - Telegram Independent Verification Scope.md"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text(message):
    value = message.get("text", "")
    return value if isinstance(value, str) else "".join(x if isinstance(x, str) else x.get("text", "") for x in value)


def normalized(value):
    return "".join(c.lower() for c in value if c.isascii() and c.isalpha())


def inventory(export, old):
    rows, before = export["messages"], {m["id"]: m for m in old["messages"]}
    delta = [m for m in rows if m["id"] > max(before)]
    overlap = [m for m in rows if m["id"] in before]
    changes = [{"id": m["id"], "fields": sorted(k for k in m.keys() | before[m["id"]].keys()
                                               if m.get(k) != before[m["id"]].get(k))}
               for m in overlap if m != before[m["id"]]]
    result = {"total_rows": len(rows), "new_rows": len(delta),
              "new_types": dict(Counter(m["type"] for m in delta)),
              "new_photos": sum(bool(m.get("photo")) for m in delta),
              "new_file_types": dict(Counter(m.get("media_type", "document") for m in delta if m.get("file"))),
              "overlap_rows": len(overlap), "overlap_object_changes": changes,
              "overlap_text_changes": [m["id"] for m in overlap if text(m) != text(before[m["id"]])],
              "creator_messages": [m["id"] for m in rows if m.get("from_id") == "user9815232"],
              "first_new": {k: delta[0][k] for k in ["id", "date", "date_unixtime"]},
              "last_new": {k: delta[-1][k] for k in ["id", "date", "date_unixtime"]}}
    assert result["total_rows"] == 2828 and result["new_rows"] == 2777
    assert result["new_types"] == {"message": 2641, "service": 136}
    assert result["new_photos"] == 112 and result["overlap_rows"] == 51
    assert not result["overlap_text_changes"] and not result["creator_messages"]
    return result


def supplemental_registry(messages):
    def quoted(mid, value):
        assert value in text(messages[mid]), (mid, value)
        return value
    registry = {
        "76367_quoted_ascii": [quoted(76367, "2iyGJ!4@?uebzY")],
        "77024_complete_post": [text(messages[77024]).strip()],
        "77045_complete_post": [text(messages[77045]).strip()],
        "77049_literal": [quoted(77049, "Wh 173 R4b B17"), "Wh173R4bB17"],
        "76333_mnemonic_literal": [quoted(76333, "zoo zoo zoo zoo zoo zoo zoo zoo zoo winner zoo zoo")],
    }
    for label, wif in previous.WIFS.items():
        mid = int(label.rsplit("_", 1)[1])
        registry[label + "_as_password"] = [quoted(mid, wif)]
    assert sum(len(v) for v in registry.values()) == 11
    return registry


def rabbit_screen(registry):
    materials = list(dict.fromkeys(m for forms in registry.values() for s in forms for m in consumer.materials(s).values()))
    hits, weak, trials = [], [], 0
    for name, (salt, ciphertext) in consumer.BLOBS.items():
        for digest in ["md5", "sha256"]:
            pairs = [evp_key_iv(m, salt, digest) for m in materials]
            keys = np.array([list(k) for k, _ in pairs], dtype=np.uint8)
            ivs = np.array([list(iv) for _, iv in pairs], dtype=np.uint8)
            for legacy in [False, True]:
                plain = keystream(keys, ivs, 80, legacy) ^ np.frombuffer(ciphertext[:80], dtype=np.uint8)
                scores = (((plain >= 32) & (plain < 127)) | np.isin(plain, [9, 10, 13])).sum(axis=1)
                for i in np.nonzero(scores >= 56)[0]:
                    row = {"target": name, "digest": digest, "legacy": legacy,
                           "material_sha256": sha(materials[int(i)]), "printable_of_80": int(scores[i])}
                    (hits if scores[i] >= 64 else weak).append(row)
                trials += len(materials)
    return {"unique_materials": len(materials), "trials": trials, "hits": hits, "weak": weak,
            "screen": "same finite set; at least 64/80 printable for a hit, 56/80 for weak; binary formats not excluded"}


def docx_text(path):
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    return "\n".join("".join(t.text or "" for t in p.findall(".//w:t", ns)) for p in root.findall(".//w:p", ns))


def attachments(directory, messages):
    rows = []
    for m in messages:
        if m["id"] <= 75648:
            continue
        for kind in ["file", "photo"]:
            if m.get(kind):
                path = directory / m[kind]
                rows.append({"id": m["id"], "kind": kind, "path": m[kind],
                             "exists": path.is_file(), "bytes": path.stat().st_size if path.is_file() else None,
                             "sha256": sha(path.read_bytes()) if path.is_file() else None})
    assert all(r["exists"] for r in rows)
    files = directory / "files"
    cosmic = base64.b64decode("".join((files / "CosmicDuality.txt").read_text().split()), validate=True)
    assert cosmic == base64.b64decode(COSMIC_BLOB_B64)
    alleged = (files / "cosmic_decrypted_verified.bin").read_bytes()
    assert sha(alleged) == "4f7a1e4efe4bf6c5581e32505c019657cb7b030e90232d33f011aca6a5e9c081"
    speech = normalized((files / "phase3.2-monologue-corrected.txt").read_text())
    native_speech = answer_321(phase32_plaintext()).lower()
    assert speech == native_speech
    soup = "".join((files / "live_salphaseion.txt").read_text().split())
    assert soup[:91] == DBBI and soup[195:765] == FAED and len(soup) == 1075
    assert base64.b64decode(soup[895:959] + soup[999:1063]) == base64.b64decode(SALPHASEION_BLOB_B64)
    audio_equal = (files / "puzzlepiece.mp3").read_bytes() == (ROOT / "decentraland-assets/puzzlepiece.mp3").read_bytes()
    old_book = EXPORT_ROOT / "ChatExport_2026-10-07/files/vdoc.pub_cosmic-duality.pdf"
    book_equal = (files / "cosmic-duality_compress.pdf").read_bytes() == old_book.read_bytes()
    # Reconstruct the attachment's address recipe independently, without importing it.
    def address(payload):
        from naddiseo_update_review_2026_11_04 import check_encode
        return check_encode(b"\x00" + payload)
    addresses = [address(alleged[i*32+16:i*32+32] + i.to_bytes(4, "big")) for i in range(39)]
    concatenated = "".join(addresses)
    posted_concat = (files / "cosmic_correct_12addrs.txt").read_text().strip()
    # The file name says 12; the content contains all 39 generated addresses.
    assert concatenated == posted_concat
    utxo = docx_text(files / "UTXO.docx")
    assert "mockElectrumSignedHex" in utxo and "avgUtxoVal = 450000" in utxo
    # This is code in a Word container, not a decryption report or real signed transaction.
    return {"manifest": rows, "checks": {
        "cosmic_envelope_identical": True, "cosmic_claimed_plaintext_sha256": sha(alleged),
        "cosmic_claimed_plaintext_stats": inspect(alleged + b"\x01"),
        "corrected_monologue_normalized_length": len(speech), "corrected_monologue_matches_native": True,
        "corrected_monologue_normalized_sha256": sha(speech.encode()), "salphaseion_soup_matches": True,
        "decentraland_mp3_byte_identical": audio_equal, "book_identical_to_october7_pdf": book_equal,
        "address_list_name_says_12_but_content_count": 39, "address_list_exactly_rebuilt": True,
        "address_list_contains_tracked_target": bool(set(addresses) & {previous.PRIZE_ADDRESS, previous.HALVING_ADDRESS}),
        "utxo_docx_contains_html_mock_transaction": True}}


def structural(messages):
    parses = enumerate_complete_parses(DBBI)
    summaries = []
    for tokens in parses:
        host_bits = "".join("1" if t == "b" else "0" for i, t in enumerate(tokens, 1) if is_prime(i))
        payload = "".join(t for i, t in enumerate(tokens, 1) if not is_prime(i))
        summaries.append({"tokens": len(tokens), "prime_bits": host_bits, "payload": payload,
                          "b_positions": [i for i, c in enumerate(payload) if c == "b"],
                          "b_split_lengths": [len(s) for s in payload.split("b")]})
    assert [r["tokens"] for r in summaries] == [83, 84]
    assert summaries[0]["b_positions"] == [19, 36] and summaries[0]["b_split_lengths"] == [19, 16, 23]
    assert summaries[0]["prime_bits"] == "11110111001111011001100"
    assert summaries[1]["prime_bits"] == "11110111001111011001101"
    _, _, positions = build_grid("THEMATRIXHASYOU")
    rows = {s: positions[s][0] for s in "ABCDEFGHI"}
    assert max(rows.values()) > 1  # Explicit counterexample to ANY keyworded square.
    slices = []
    for name, stream, cells, skips in [("dbbi7x13", DBBI, 91, [0, 1, 5]),
                                      ("dbbi14x14", DBBI, 196, [0, 1, 5]),
                                      ("faed15x38", FAED, 570, [0, 4])]:
        for skip in skips:
            moves = stream[skip:][:cells-1]
            assert len(set(moves)) == 9
            slices.append({"board": name, "skip": skip, "move_symbols": len(set(moves)),
                           "eight_move_injection_possible": False})
    finders = load_finders()
    assert all(np.array_equal(finders[0], f) for f in finders[1:])
    j_text = text(messages[78605])
    assert "prime number of bytes" in j_text and "79" not in j_text
    mnemonic = "zoo zoo zoo zoo zoo zoo zoo zoo zoo winner zoo zoo".split()
    return {"dbbi_parses": summaries, "keyword_counterexample": {"keyword": "THEMATRIXHASYOU", "zero_based_rows": rows},
            "knight_injection_impossibility": slices,
            "qr_finders_identical": True, "finder_crop_shape": list(finders[0].shape),
            "j_78605_discloses_79_bytes": False,
            "possible_prime_plaintext_lengths_if_80_byte_aes_cbc": {
                str(n): {"padding_bytes": 80-n} for n in range(64, 80) if is_prime(n)},
            "mnemonic_bip39_checksum_valid": bip39_checksum_valid(mnemonic)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", type=Path, default=EXPORT_ROOT / "ChatExport_2026-11-04/result.json")
    parser.add_argument("--reuse-completed-oracles", action="store_true",
                        help="Reuse the already completed original and supplemental replay JSON after checking their registries; rerun remaining checks.")
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    raw = args.export.read_bytes()
    assert sha(raw) == "eaf63cfe31a48bb243b2f85683408b84686a91c56f8f6de952215b1a0bb6a0b3"
    export = json.loads(raw)
    old_path = EXPORT_ROOT / "ChatExport_2026-10-07/result.json"
    old = json.loads(old_path.read_text())
    messages = {m["id"]: m for m in export["messages"]}
    report = {"export": str(args.export), "source_sha256": sha(raw), "previous_export_sha256": sha(old_path.read_bytes()),
              "protocol_sha256": sha(PROTOCOL.read_bytes()), "coverage": inventory(export, old),
              "structural": structural(messages), "attachments": attachments(args.export.parent, export["messages"])}
    # Redirect both runners; the prior checker and its saved result stay unchanged.
    saved = json.loads(previous.RESULT.read_text())
    previous.RESULT = WORK / "original_checker_replay.json"
    if not args.reuse_completed_oracles:
        previous.main()
    replay = json.loads(previous.RESULT.read_text())
    assert replay == saved
    report["previous_result_reproduced_exactly"] = True
    registry = supplemental_registry(messages)
    consumer.REGISTRY = registry
    consumer.RESULT = WORK / "supplemental_oracles.json"
    if not args.reuse_completed_oracles:
        consumer.main()
    report["supplemental"] = json.loads(consumer.RESULT.read_text())
    assert {k: [r["base"] for r in v] for k, v in report["supplemental"]["items"].items()} == registry
    assert report["supplemental"]["totals"]["materials"] == 165
    assert report["supplemental"]["map_sha256"] == sha(consumer.MAP.read_bytes())
    report["supplemental"]["scope_note"] = "315 old materials reproduced; this is a separate 11-string/165-form fixed set. Counts are registered forms, not deduplicated passwords."
    report["rabbit_supplemental"] = rabbit_screen(registry)
    scalar_checks = {}
    for name, value in previous.WIFS.items():
        key = wif_to_private_key(value)
        if key is not None:
            scalar_checks[name] = {"raw_key_hits": len(cb_common.raw_key_try_open(key)),
                                   "addresses": previous.p2pkh_addresses(key)}
    report["decoded_wif_raw_key_checks"] = scalar_checks
    solved_html = ROOT / "doc/html/choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecialdessertiwroteitmyself.html"
    fields = re.findall(r"<textarea[^>]*>(.*?)</textarea>", solved_html.read_text(), flags=re.DOTALL)
    assert len(fields) == 2
    solved = {"phase2": cb_common._load_blob("".join(fields[0].split())),
              "phase3": cb_common._load_blob("".join(fields[1].split())),
              "phase32": cb_common._load_blob(PHASE32_BLOB_B64)}
    report["solved_stage_html_sha256"] = sha(solved_html.read_bytes())
    # Each solved stage must accept its actual passphrase before these negatives count.
    from data import VERIFIED_PRIOR_COMMAND_HASHES
    positives = {}
    for label, hash_label in [("phase2", "phase2_causality"), ("phase3", "phase3_parts"), ("phase32", "phase32_clues")]:
        hit = cb_common.aes_try_open_bytes(VERIFIED_PRIOR_COMMAND_HASHES[hash_label].encode(), blobs={label: solved[label]})
        assert hit is not None
        positives[label] = True
    level3 = {}
    for name in ["tommy_77069", "tommy_77071", "tommy_77253", "tommy_77646"]:
        hits = []
        for form, material in consumer.materials(previous.WIFS[name]).items():
            hit = cb_common.aes_try_open_bytes(material, kdf_variants=consumer.ALL_CBC_VARIANTS, blobs=solved)
            if hit:
                hits.append({"form": form, "hit": repr(hit)})
        level3[name] = hits
    report["solved_stage_positive_controls"] = positives
    report["claimed_level3_passwords_on_solved_stages"] = level3
    pdf_index = WORK / "pdf_file_index.json"
    if pdf_index.exists():
        entries = json.loads(pdf_index.read_text())
        assert len(entries) == 238 and [e["index"] for e in entries] == list(range(1, 239))
        report["pdf_index"] = {"named_entries": 238, "pages": 25442,
                               "index_sha256": sha(pdf_index.read_bytes()),
                               "entries": entries,
                               "scope": "All entries indexed; selected summaries inspected. Computations not independently rerun. JSON line wraps not silently repaired."}
    live_home, archived_home = WORK / "live_home.html", WORK / "home_august19_from_pr15.html"
    if live_home.exists() and archived_home.exists():
        assert live_home.read_bytes() == archived_home.read_bytes()
        report["homepage_comparison"] = {"bytes": live_home.stat().st_size,
                                          "sha256": sha(live_home.read_bytes()),
                                          "identical_to_pr15_august19_capture_copy": True,
                                          "markers": ["finalGrid", "carrier anomaly", "burst-flash", "#fefefe"],
                                          "historical_copy_source": "https://raw.githubusercontent.com/Naddiseo/gsmgio-5btc-puzzle/1e913fdbd42b8d5bd7d0a0cf3406d6abdd33142a/neo/materials/wayback/pages/root_2026-08-19_finale.html"}
    chain_status = WORK / "chain_status.json"
    if chain_status.exists():
        report["chain_status"] = json.loads(chain_status.read_text())
    report["execution"] = {"reused_completed_oracles": args.reuse_completed_oracles,
                           "runner_sha256": sha(Path(__file__).read_bytes()),
                           "downloaded_code_executed": False}
    RESULT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"result": str(RESULT), "original_reproduced": True,
                      "new_totals": report["supplemental"]["totals"],
                      "rabbit": report["rabbit_supplemental"], "level3": level3}))


if __name__ == "__main__":
    main()
