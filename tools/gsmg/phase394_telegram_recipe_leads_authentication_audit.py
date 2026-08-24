#!/usr/bin/env python3
"""Phase 394: authenticate the two reproducible leads from Phase 393.

The frozen 142-message executable-recipe lane produced two constructions
that were complete enough to reproduce rather than classify from prose:

1. Telegram 65082 flips the unique FEFE cell in the authenticated 14x14
   Stage-0 matrix, then observes a two-dimensional GF(2) row/column kernel.
2. Telegram 66244/66245 takes the four-symbol alternating rail from the
   Phase-386 Bifid output and obtains a checksum-valid 24-word BIP39 mnemonic.

This audit reproduces both claims and applies their natural closed controls.
It also runs every exact, previously unauthenticated passphrase material in
the Phase-393 lane through the current four-blob oracle.  No wordlist or
generated concatenation is admitted.
"""

import argparse
import hashlib
import hmac
import itertools
import json
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import (  # noqa: E402
    BLOBS,
    ECB_CIPHER_VARIANTS,
    EXTENDED_CIPHER_VARIANTS,
    KDF_VARIANTS,
    KEY_WRAP_KDF_VARIANTS,
    STREAM_CIPHER_VARIANTS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    aes_try_open_ecb_bytes,
    aes_try_open_stream_bytes,
    keystr_forms,
)
from phase386_btcseed_bifid_faed_decode_audit import audit as btcseed_audit  # noqa: E402


TARGET_ADDRESS = "1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe"
BIP39_WORDLIST = ROOT / "wordlists" / "bip39" / "english.txt"
BIP39_WORDLIST_SHA256 = "2f5eed53a4727b4bf8880d8f3f199efc90e58503646d9ff8eff3a2ed3b24dbda"
TARGET_MNEMONIC = (
    "dust trophy mule tragic corn cupboard sand crunch salt like inspire radar "
    "hunt twice wolf empower sweet glimpse update turtle copy satoshi fee allow"
)
TARGET_ENTROPY_HEX = "445d1e457373066bafc9a7beb035d55856f7d6bf3248dbac67ba7573017ed520"
TARGET_MAPPING = (2, 1, 0, 3)  # b,c,d,e -> 2,1,0,3 (equiv. d,c,b,e -> 0,1,2,3)
TARGET_FULL_RAIL_OFFSET = 30

SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
HARDENED = 1 << 31
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

# README's authenticated matrix.  Telegram 65082 changes only row 8, column 5
# (one-based), the unique FEFE cell, from its source value 0 to 1.
STAGE0_MATRIX = tuple(
    tuple(int(ch) for ch in row)
    for row in (
        "00110100101100",
        "11110011101011",
        "11011101001001",
        "01101000011101",
        "01100011000110",
        "10011000100011",
        "10011100010000",
        "11100000001000",
        "00011101111101",
        "11111100110001",
        "11010000011011",
        "11110010101100",
        "01011101000110",
        "01101101101011",
    )
)
FEFE_COORD_0 = (7, 4)


# Exact roots in the Phase-393 lane that were asserted as a password/key for
# an open artifact and were not already an authenticated solved password.
# Each receives only the established literal/single-SHA/double-SHA forms.
CLAIM_ROOTS = (
    "_GدA+/05҃-{J @qZOb`ŏdiX)YpVl}PbD",
    "icantbreathe",
    "1334001941",
    "u+2e2e",
    "shabefanstoo",
    "ourfirsthintisyourlastcommand",
    "backtothebasics",
    "93de0175aa3d0a6a2768ba650009a35a36530fa31898da6f3c46757a693f108f",
    "wewontmeetagain",
    "e24bd2c0fd454632f9fdd26cbdc210597f79e9fca9719c126a6d30cb41ef0238",
    "baff7ec4a1686de56f065d9c72a557eec5977a94c155a18dd78ee833e0ab6f9b",
    "ZION",
    "Temple Mount",
    "rEdEmPtIoN",
    "AWAKENZION",
    "hopeitisthequintessential",
    "uncertainty",
    "8f8a1cdb2e58828c61a7c76c437a1b365db5ee5e733ee87645ae576178d7b276",
    "25615225",
    "lastwordsbeforearchichoice",
    "theseedisplanted",
    "20c53e334ca2e74815e5b93536db1849c8ac36929eea409bb02f9f52b177824d",
)


def gf2_rank(matrix):
    work = [list(row) for row in matrix]
    rank = 0
    for column in range(len(work[0])):
        pivot = next(
            (row for row in range(rank, len(work)) if work[row][column]), None
        )
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        for row in range(len(work)):
            if row != rank and work[row][column]:
                work[row] = [a ^ b for a, b in zip(work[row], work[rank])]
        rank += 1
    return rank


def xor_zero_subsets(vectors):
    """Return all non-empty one-based subsets whose vector XOR is zero."""
    width = len(vectors[0])
    out = []
    for mask in range(1, 1 << len(vectors)):
        acc = [0] * width
        for index, vector in enumerate(vectors):
            if mask & (1 << index):
                acc = [a ^ b for a, b in zip(acc, vector)]
        if not any(acc):
            out.append(tuple(i + 1 for i in range(len(vectors)) if mask & (1 << i)))
    return tuple(out)


def uniform_square_rank_probability(size, rank):
    numerator = 1
    denominator = 1
    for i in range(rank):
        numerator *= (2**size - 2**i) ** 2
        denominator *= 2**rank - 2**i
    count = numerator // denominator
    return Fraction(count, 2 ** (size * size))


def spiral_decode(matrix):
    size = len(matrix)
    seen = [[False] * size for _ in range(size)]
    row, column, dr, dc = 0, 0, 0, -1
    bits = []
    for _ in range(size * size):
        bits.append(str(matrix[row][column]))
        seen[row][column] = True
        next_row, next_column = row + dr, column + dc
        if (
            not (0 <= next_row < size and 0 <= next_column < size)
            or seen[next_row][next_column]
        ):
            dr, dc = -dc, dr
            next_row, next_column = row + dr, column + dc
        row, column = next_row, next_column
    bitstream = "".join(bits)
    return "".join(
        chr(int(bitstream[offset:offset + 8], 2))
        for offset in range(0, 192, 8)
    )


def matrix_report():
    source = [list(row) for row in STAGE0_MATRIX]
    flipped = [row[:] for row in source]
    flipped[FEFE_COORD_0[0]][FEFE_COORD_0[1]] ^= 1
    columns = tuple(tuple(row[c] for row in flipped) for c in range(14))

    flip_ranks = Counter()
    rank12_cells = []
    for row in range(14):
        for column in range(14):
            trial = [r[:] for r in source]
            trial[row][column] ^= 1
            trial_rank = gf2_rank(trial)
            flip_ranks[trial_rank] += 1
            if trial_rank == 12:
                rank12_cells.append((row + 1, column + 1))

    rank_probabilities = {
        rank: uniform_square_rank_probability(14, rank) for rank in range(15)
    }
    probability_rank_le_12 = sum(rank_probabilities[rank] for rank in range(13))

    # The authenticated spiral places FEFE at zero-based position 163: byte
    # 20, bit 3.  Decode both matrices directly rather than assuming which
    # output byte changes.
    source_url = spiral_decode(source)
    changed_url = spiral_decode(flipped)
    assert source_url == "gsmg.io/theseedisplanted"

    return {
        "source_rank": gf2_rank(source),
        "fefe_flipped_rank": gf2_rank(flipped),
        "fefe_coord_1": (8, 5),
        "row_zero_subsets": xor_zero_subsets(tuple(tuple(r) for r in flipped)),
        "column_zero_subsets": xor_zero_subsets(columns),
        "single_cell_flip_rank_counts": dict(sorted(flip_ranks.items())),
        "rank12_flip_count": len(rank12_cells),
        "rank12_flip_fraction": len(rank12_cells) / 196,
        "fefe_is_one_of_rank12_flips": (8, 5) in rank12_cells,
        "uniform_rank12_probability": float(rank_probabilities[12]),
        "uniform_rank_le_12_probability": float(probability_rank_le_12),
        "source_url": source_url,
        "flipped_url": changed_url,
        "authenticated_url_survives_flip": changed_url == source_url,
    }


def load_bip39_words():
    raw = BIP39_WORDLIST.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == BIP39_WORDLIST_SHA256
    words = raw.decode("utf-8").splitlines()
    assert len(words) == 2048 and len(set(words)) == 2048
    return words


def bits_to_mnemonic(bits, words):
    return tuple(words[int(bits[i:i + 11], 2)] for i in range(0, 264, 11))


def bip39_checksum_valid(bits):
    entropy = int(bits[:256], 2).to_bytes(32, "big")
    expected = f"{hashlib.sha256(entropy).digest()[0]:08b}"
    return bits[256:] == expected


def bip39_candidate_report():
    decoded = btcseed_audit()["decoded"].lower()
    rails = (decoded[0::2], decoded[1::2])
    four_symbol = tuple(rail for rail in rails if set(rail) == set("bcde"))
    assert len(four_symbol) == 1
    rail = four_symbol[0]
    assert len(rail) == 285

    words = load_bip39_words()
    valid = []
    for permutation in itertools.permutations(range(4)):
        mapping = {symbol: f"{value:02b}" for symbol, value in zip("bcde", permutation)}
        bitstream = "".join(mapping[symbol] for symbol in rail)
        for offset in range(len(rail) - 132 + 1):
            bits = bitstream[2 * offset:2 * (offset + 132)]
            if not bip39_checksum_valid(bits):
                continue
            mnemonic = bits_to_mnemonic(bits, words)
            valid.append({
                "mapping_bcde": permutation,
                "offset": offset,
                "mnemonic": " ".join(mnemonic),
                "entropy_hex": int(bits[:256], 2).to_bytes(32, "big").hex(),
            })

    target_rows = [
        row for row in valid
        if row["mapping_bcde"] == TARGET_MAPPING
        and row["offset"] == TARGET_FULL_RAIL_OFFSET
    ]
    assert len(target_rows) == 1

    return {
        "decoded_length": len(decoded),
        "four_symbol_rail_length": len(rail),
        "four_symbol_alphabet": "".join(sorted(set(rail))),
        "mapping_count": 24,
        "window_count_per_mapping": len(rail) - 132 + 1,
        "mapping_window_trials": 24 * (len(rail) - 132 + 1),
        "checksum_valid_count": len(valid),
        "expected_checksum_valid_under_uniform": 24 * (len(rail) - 132 + 1) / 256,
        "target": target_rows[0],
        "target_contains_satoshi_fee": "satoshi fee" in target_rows[0]["mnemonic"],
        "valid_candidates": tuple(valid),
    }


def base58_decode(text):
    value = 0
    for char in text:
        value = value * 58 + BASE58_ALPHABET.index(char)
    body = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return b"\0" * (len(text) - len(text.lstrip("1"))) + body


def hash160(data):
    return hashlib.new("ripemd160", hashlib.sha256(data).digest()).digest()


def public_key(private_key, compressed=True):
    key = ec.derive_private_key(private_key, ec.SECP256K1()).public_key()
    form = (
        serialization.PublicFormat.CompressedPoint
        if compressed else serialization.PublicFormat.UncompressedPoint
    )
    return key.public_bytes(serialization.Encoding.X962, form)


def child_private_key(private_key, chain_code, index):
    if index >= HARDENED:
        data = b"\0" + private_key.to_bytes(32, "big")
    else:
        data = public_key(private_key, compressed=True)
    digest = hmac.new(chain_code, data + index.to_bytes(4, "big"), hashlib.sha512).digest()
    child = (int.from_bytes(digest[:32], "big") + private_key) % SECP256K1_ORDER
    assert child != 0
    return child, digest[32:]


def derive_path(master, path):
    private_key, chain_code = master
    for index in path:
        private_key, chain_code = child_private_key(private_key, chain_code, index)
    return private_key, chain_code


def wallet_authentication_report(mnemonic):
    entropy = bytes.fromhex(TARGET_ENTROPY_HEX)
    seed = hashlib.pbkdf2_hmac(
        "sha512", mnemonic.encode("utf-8"), b"mnemonic", 2048
    )
    master_digest = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    master = (int.from_bytes(master_digest[:32], "big"), master_digest[32:])

    decoded_target = base58_decode(TARGET_ADDRESS)
    assert len(decoded_target) == 25 and decoded_target[0] == 0
    checksum = hashlib.sha256(hashlib.sha256(decoded_target[:-4]).digest()).digest()[:4]
    assert checksum == decoded_target[-4:]
    target_hash160 = decoded_target[1:-4]

    direct_materials = {
        "entropy": int.from_bytes(entropy, "big"),
        "seed_first32": int.from_bytes(seed[:32], "big"),
        "bip32_master": master[0],
    }
    direct_hits = []
    for label, private_key in direct_materials.items():
        for compressed in (True, False):
            if hash160(public_key(private_key, compressed)) == target_hash160:
                direct_hits.append((label, compressed))

    # Closed standard/conservative family.  BIP32 itself specifies compressed
    # public keys; testing both forms is an extra allowance for the prize
    # address's known uncompressed public key.  Index 0..999 exceeds the usual
    # wallet gap limit while remaining finite.
    path_templates = (
        ("m/44'/0'/0'/0/i", (44 + HARDENED, HARDENED, HARDENED, 0)),
        ("m/44'/0'/0'/1/i", (44 + HARDENED, HARDENED, HARDENED, 1)),
        ("m/0'/0/i", (HARDENED, 0)),
        ("m/0'/1/i", (HARDENED, 1)),
        ("m/0/i", (0,)),
        ("m/1/i", (1,)),
    )
    hits = []
    checked_keys = 0
    for label, prefix in path_templates:
        parent_key, parent_chain = derive_path(master, prefix)
        for index in range(1000):
            private_key, _ = child_private_key(parent_key, parent_chain, index)
            checked_keys += 1
            for compressed in (True, False):
                if hash160(public_key(private_key, compressed)) == target_hash160:
                    hits.append((label, index, compressed, f"{private_key:064x}"))

    return {
        "bip39_seed_hex": seed.hex(),
        "bip32_master_private_hex": f"{master[0]:064x}",
        "bip32_master_chain_code_hex": master[1].hex(),
        "target_hash160": target_hash160.hex(),
        "direct_material_count": len(direct_materials),
        "direct_address_checks": len(direct_materials) * 2,
        "direct_hits": direct_hits,
        "path_templates": tuple(label for label, _ in path_templates),
        "indices_per_path": 1000,
        "derived_private_key_count": checked_keys,
        "derived_address_checks": checked_keys * 2,
        "derived_hits": hits,
        "standard_bip32_uses_compressed_pubkeys": True,
        "prize_address_pubkey_known_uncompressed": True,
    }


ORACLE_FAMILIES = (
    ("cbc", aes_try_open_bytes, KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS, 1),
    ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS, 1),
    ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS, 1),
    ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS, 4),
)


def exact_claim_oracle_report():
    materials = []
    for root in CLAIM_ROOTS:
        for form, material in zip(("literal", "sha256_hex", "sha256_hex_hex"), keystr_forms(root)):
            materials.append((root, form, material.encode("utf-8")))

    hits = []
    attempts = 0
    for root, form, material in materials:
        for family_name, oracle, variants, forms_per_config in ORACLE_FAMILIES:
            attempts += len(variants) * len(BLOBS) * forms_per_config
            if family_name == "keywrap":
                for tag, wrap_kind, kdf_label, key_len, plaintext in oracle(
                    material, kdf_variants=variants, blobs=BLOBS
                ):
                    hits.append((root, form, family_name, tag, wrap_kind, kdf_label, key_len, plaintext.hex()))
            else:
                result = oracle(material, kdf_variants=variants, blobs=BLOBS)
                if result:
                    tag, plaintext, kdf_label, key_len = result
                    hits.append((root, form, family_name, tag, "", kdf_label, key_len, plaintext.hex()))

    return {
        "claim_root_count": len(CLAIM_ROOTS),
        "material_count": len(materials),
        "blob_count": len(BLOBS),
        "effective_decrypt_attempts": attempts,
        "hits": hits,
        "total_hits": len(hits),
    }


def audit(run_oracle=True):
    matrix = matrix_report()
    bip39 = bip39_candidate_report()
    wallet = wallet_authentication_report(bip39["target"]["mnemonic"])
    report = {"matrix": matrix, "bip39": bip39, "wallet": wallet}
    if run_oracle:
        report["exact_claim_oracle"] = exact_claim_oracle_report()
    return report


def self_test(run_oracle=False):
    report = audit(run_oracle=run_oracle)
    matrix = report["matrix"]
    assert matrix["source_rank"] == 13
    assert matrix["fefe_flipped_rank"] == 12
    assert matrix["row_zero_subsets"] == (
        (2, 6, 8, 10, 11, 12, 13),
        (1, 4, 5, 6, 8, 11, 12, 14),
        (1, 2, 4, 5, 10, 13, 14),
    )
    assert matrix["column_zero_subsets"] == (
        (2, 4, 7, 8, 9, 10, 11, 12),
        (4, 5, 6, 7, 8, 9, 10, 11, 14),
        (2, 5, 6, 12, 14),
    )
    assert matrix["rank12_flip_count"] == 27
    assert matrix["authenticated_url_survives_flip"] is False

    bip39 = report["bip39"]
    assert bip39["mapping_window_trials"] == 3696
    assert bip39["checksum_valid_count"] == 13
    assert bip39["target"]["mnemonic"] == TARGET_MNEMONIC
    assert bip39["target"]["entropy_hex"] == TARGET_ENTROPY_HEX

    wallet = report["wallet"]
    assert wallet["bip39_seed_hex"] == (
        "c66ee7a3f16dcf10d6b0975662c21c792024ed2bd466f741a0841530568412e1"
        "72a4a981bb4aae5d2e5c931868e19a312c8a0e0ca29d3e57da127edb6906e54d"
    )
    assert wallet["bip32_master_private_hex"] == (
        "44bb7490a2d44bef9512b30533a39d10c2730a14d564b23d18c6dfebd0db05fb"
    )
    assert wallet["direct_hits"] == []
    assert wallet["derived_private_key_count"] == 6000
    assert wallet["derived_hits"] == []
    if run_oracle:
        assert report["exact_claim_oracle"]["total_hits"] == 0
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--skip-oracle", action="store_true")
    args = parser.parse_args()
    report = self_test(run_oracle=not args.skip_oracle) if args.self_test else audit(run_oracle=not args.skip_oracle)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
