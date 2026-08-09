#!/usr/bin/env python3
"""Reproduce and calibrate the disputed COSMIC ``4f7a1e4e...`` checkpoint.

The published construction XORs seven SHA-256 digests.  The critical detail is
that the resulting 32 bytes are passed to OpenSSL's legacy EVP_BytesToKey KDF as
binary password material.  Treating their 64-character hexadecimal rendering as
password text is a different input and was the source of this project's earlier
false negative.

This audit freezes all four raw/hex x MD5/SHA-256 interpretations, verifies the
one reproducible checkpoint, and reconstructs the three documented 103x103
matrix invariants.  It does not treat valid padding, a published result hash, or
invariants derived from the same plaintext as independent proof that the branch
is creator-intended.
"""

import argparse
import base64
from collections import Counter
from fractions import Fraction
import hashlib
import math

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import ec

from cb_common import evp_bytes_to_key
from data import COSMIC_BLOB_B64
from onchain_op_return_provenance_audit import KNOWN_SCAM_ADDRESSES


TOKENS = (
    "matrixsumlist",
    "enter",
    "lastwordsbeforearchichoice",
    "thispassword",
    "matrixsumlist",
    "yourlastcommand",
    "secondanswer",
)

EXPECTED_XOR_HEX = (
    "a795de117e472590e572dc193130c763"
    "e3fb555ee5db9d34494e156152e50735"
)
EXPECTED_PAYLOAD_SHA256 = (
    "4f7a1e4efe4bf6c5581e32505c019657"
    "cb7b030e90232d33f011aca6a5e9c081"
)
MATRIX_SIDE = 103
BASE38_ASCII_OFFSET = 80
P5_CANDIDATES = (
    "6108766549978798108108736759668",
    "matrixsumlist",
    "sumlist",
    "matrixsums",
    "sumsofmatrix",
    "rowcolsum",
    "rowcolsumlist",
)
P6_CANDIDATES = (
    "ourfirsthintisyourlastcommand",
    "firsthintisyourlastcommand",
    "firsthintlastcommand",
    "yourlastcommand",
    "lastcommand",
)
P7_CANDIDATES = (
    "answertoo",
    "answertwo",
    "answer2",
    "shabefanstoo",
    "secondanswer",
    "answeralso",
)
EXPECTED_HALF_HEX = "0423d9115a1dc756d5d08d2de880ab508bd4745fc97709f4fcb513f2cb8fcc35"
EXPECTED_BETTER_HALF_HEX = "48cc46e66bdd36b09ae344552f606a761f9d90681f20dfefe2b43db18b623971"
EXPECTED_TAIL_HEX = "fc0c1b02"
EXPECTED_ADDRESSES = (
    "1JG648yaB7Wp2dpUfcZoRSD4q35oq47vCu",
    "145ZQ9siLrsXBKf465wjdyQYAP5dRwhRhQ",
)


def xor_sha256_digests(tokens=TOKENS):
    result = bytes(hashlib.sha256(tokens[0].encode()).digest_size)
    for token in tokens:
        digest = hashlib.sha256(token.encode()).digest()
        result = bytes(left ^ right for left, right in zip(result, digest))
    return result


def decrypt(password, digest_name):
    envelope = base64.b64decode(COSMIC_BLOB_B64, validate=True)
    assert envelope.startswith(b"Salted__")
    salt = envelope[8:16]
    ciphertext = envelope[16:]
    key, iv = evp_bytes_to_key(password, salt, digest_name, 32, 16)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    raw_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    padding_length = raw_plaintext[-1]
    valid_padding = (
        1 <= padding_length <= 16
        and raw_plaintext[-padding_length:] == bytes((padding_length,)) * padding_length
    )
    payload = raw_plaintext[:-padding_length] if valid_padding else raw_plaintext
    return {
        "digest": digest_name,
        "padding_length": padding_length,
        "valid_padding": valid_padding,
        "raw_length": len(raw_plaintext),
        "raw_sha256": hashlib.sha256(raw_plaintext).hexdigest(),
        "payload": payload,
        "payload_length": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
    }


def shannon_entropy(data):
    counts = Counter(data)
    return -sum(
        (count / len(data)) * math.log2(count / len(data))
        for count in counts.values()
    )


def matrix_components(payload):
    bitstream = "".join(f"{value:08b}" for value in payload)
    used_bit_count = MATRIX_SIDE * MATRIX_SIDE
    matrix_bits = bitstream[:used_bit_count]
    unused_bits = bitstream[used_bit_count:]
    rows = tuple(
        sum(int(bit) for bit in matrix_bits[offset : offset + MATRIX_SIDE])
        for offset in range(0, used_bit_count, MATRIX_SIDE)
    )
    columns = tuple(
        sum(int(matrix_bits[row * MATRIX_SIDE + column]) for row in range(MATRIX_SIDE))
        for column in range(MATRIX_SIDE)
    )
    return bitstream, unused_bits, rows, columns


def matrix_report(payload):
    bitstream, unused_bits, rows, columns = matrix_components(payload)
    used_bit_count = MATRIX_SIDE * MATRIX_SIDE
    return {
        "side": MATRIX_SIDE,
        "available_bits": len(bitstream),
        "used_bits": used_bit_count,
        "unused_bits": unused_bits,
        "S": sum(rows),
        "Wr_zero_based": sum(index * value for index, value in enumerate(rows)),
        "Wr_one_based": sum(index * value for index, value in enumerate(rows, 1)),
        "Wc_zero_based": sum(index * value for index, value in enumerate(columns)),
        "Wc_one_based": sum(index * value for index, value in enumerate(columns, 1)),
        "row_min": min(rows),
        "row_max": max(rows),
        "column_min": min(columns),
        "column_max": max(columns),
        "row_sums_sha256": hashlib.sha256(bytes(rows)).hexdigest(),
        "column_sums_sha256": hashlib.sha256(bytes(columns)).hexdigest(),
        "padding_big_endian": int(unused_bits, 2),
        "padding_little_endian": int(unused_bits[::-1], 2),
    }


def base58check(payload):
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    encoded_value = int.from_bytes(payload + checksum, "big")
    encoded = ""
    while encoded_value:
        encoded_value, remainder = divmod(encoded_value, 58)
        encoded = alphabet[remainder] + encoded
    leading_zeroes = len(payload + checksum) - len((payload + checksum).lstrip(b"\x00"))
    return alphabet[0] * leading_zeroes + encoded


def compressed_p2pkh(private_key):
    public = ec.derive_private_key(
        int.from_bytes(private_key, "big"), ec.SECP256K1()
    ).public_key().public_numbers()
    compressed = bytes((2 + (public.y & 1),)) + public.x.to_bytes(32, "big")
    public_hash = hashlib.new("ripemd160", hashlib.sha256(compressed).digest()).digest()
    return base58check(b"\x00" + public_hash)


def downstream_report(payload):
    _, unused_bits, rows, columns = matrix_components(payload)
    shift = len(unused_bits)
    combined = bytes(
        (rows[index] + columns[(index + shift) % MATRIX_SIDE]) & 0xFF
        for index in range(MATRIX_SIDE)
    )
    digits = tuple(value - BASE38_ASCII_OFFSET for value in combined)
    valid_digits = all(0 <= digit < 38 for digit in digits)
    integer = 0
    for digit in digits:
        integer = integer * 38 + digit
    decoded = integer.to_bytes(68, "big") if valid_digits else b""
    half = decoded[:32]
    better_half = decoded[32:64]
    tail = decoded[64:]

    offset_ranges = []
    for candidate_shift in range(MATRIX_SIDE):
        values = tuple(
            rows[index] + columns[(index + candidate_shift) % MATRIX_SIDE]
            for index in range(MATRIX_SIDE)
        )
        low, high = min(values), max(values)
        if BASE38_ASCII_OFFSET <= low and high < BASE38_ASCII_OFFSET + 38:
            offset_ranges.append((candidate_shift, low, high))

    return {
        "shift_from_unused_bit_count": shift,
        "combined_length": len(combined),
        "combined_hex": combined.hex(),
        "combined_min": min(combined),
        "combined_max": max(combined),
        "base38_ascii_offset": BASE38_ASCII_OFFSET,
        "digit_min": min(digits),
        "digit_max": max(digits),
        "all_digits_valid": valid_digits,
        "decoded_integer_bits": integer.bit_length(),
        "decoded_length": len(decoded),
        "decoded_hex": decoded.hex(),
        "half_hex": half.hex(),
        "better_half_hex": better_half.hex(),
        "tail_hex": tail.hex(),
        "tail_integer": int.from_bytes(tail, "big"),
        "compressed_p2pkh": (
            compressed_p2pkh(half),
            compressed_p2pkh(better_half),
        ),
        "fixed_base38_valid_offsets": tuple(offset_ranges),
        "fixed_base38_full_span_offsets": tuple(
            candidate_shift
            for candidate_shift, low, high in offset_ranges
            if (low, high) == (BASE38_ASCII_OFFSET, BASE38_ASCII_OFFSET + 37)
        ),
    }


def published_uniqueness_family_report():
    fixed = TOKENS[:4]
    hits = []
    attempts = 0
    for p5 in P5_CANDIDATES:
        for p6 in P6_CANDIDATES:
            for p7 in P7_CANDIDATES:
                attempts += 1
                tokens = fixed + (p5, p6, p7)
                result = decrypt(xor_sha256_digests(tokens), "md5")
                if result["valid_padding"]:
                    hits.append(
                        {
                            "tokens_5_7": (p5, p6, p7),
                            "padding_length": result["padding_length"],
                            "payload_sha256": result["payload_sha256"],
                        }
                    )
    return {"attempts": attempts, "padding_valid_hits": tuple(hits)}


def audit():
    raw_password = xor_sha256_digests()
    password_forms = {
        "raw32": raw_password,
        "hex64": raw_password.hex().encode(),
    }
    decryptions = {
        f"{form}_{digest}": decrypt(password, digest)
        for form, password in password_forms.items()
        for digest in ("md5", "sha256")
    }
    checkpoint = decryptions["raw32_md5"]
    payload = checkpoint["payload"]
    downstream = downstream_report(payload)
    return {
        "tokens": TOKENS,
        "xor_digest_hex": raw_password.hex(),
        "password_lengths": {
            form: len(password) for form, password in password_forms.items()
        },
        "decryptions": {
            name: {key: value for key, value in result.items() if key != "payload"}
            for name, result in decryptions.items()
        },
        "checkpoint": {
            "payload_length": len(payload),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "entropy_bits_per_byte": shannon_entropy(payload),
            "strict_ascii_ratio": sum(32 <= value < 127 for value in payload) / len(payload),
        },
        "matrix": matrix_report(payload),
        "downstream": downstream,
        "published_uniqueness_family": published_uniqueness_family_report(),
        "spam_provenance": {
            "known_spam_payer_addresses": KNOWN_SCAM_ADDRESSES,
            "derived_addresses_match_known_spam_payers": (
                downstream["compressed_p2pkh"] == KNOWN_SCAM_ADDRESSES
            ),
            "phase156_op_return_messages": 105,
            "phase156_messages_from_these_payers": 88,
            "phase156_messages_from_creator_keys": 0,
        },
        "calibration": {
            "random_pkcs7_valid_probability": sum(
                (Fraction(1, 256) ** length) for length in range(1, 17)
            ),
            "tested_password_kdf_forms": len(decryptions),
            "valid_padding_forms": sum(
                result["valid_padding"] for result in decryptions.values()
            ),
        },
    }


def self_test():
    report = audit()
    assert report["tokens"] == TOKENS
    assert report["xor_digest_hex"] == EXPECTED_XOR_HEX
    assert report["password_lengths"] == {"raw32": 32, "hex64": 64}

    decryptions = report["decryptions"]
    assert tuple(decryptions) == (
        "raw32_md5",
        "raw32_sha256",
        "hex64_md5",
        "hex64_sha256",
    )
    assert decryptions["raw32_md5"]["valid_padding"] is True
    assert decryptions["raw32_md5"]["padding_length"] == 1
    assert decryptions["raw32_md5"]["raw_length"] == 1328
    assert decryptions["raw32_md5"]["payload_length"] == 1327
    assert decryptions["raw32_md5"]["payload_sha256"] == EXPECTED_PAYLOAD_SHA256
    assert all(
        not decryptions[name]["valid_padding"]
        for name in ("raw32_sha256", "hex64_md5", "hex64_sha256")
    )

    matrix = report["matrix"]
    assert matrix["side"] == 103
    assert matrix["available_bits"] == 10616
    assert matrix["used_bits"] == 10609
    assert matrix["unused_bits"] == "0111010"
    assert matrix["S"] == 5193
    assert matrix["Wr_zero_based"] == 263410
    assert matrix["Wr_one_based"] == 268603
    assert matrix["Wc_zero_based"] == 263635
    assert matrix["Wc_one_based"] == 268828
    assert matrix["row_sums_sha256"] == (
        "24c2fc3c3fea5b0433daee60946e7422b4b7be01844e88580a9b1c9fa2f2d787"
    )
    assert matrix["column_sums_sha256"] == (
        "672905e92f6984741afb3275a6177892229e9508f0dde569b763ab2e7bd56449"
    )
    assert matrix["padding_big_endian"] == 58
    assert matrix["padding_little_endian"] == 46

    downstream = report["downstream"]
    assert downstream["shift_from_unused_bit_count"] == 7
    assert downstream["combined_length"] == 103
    assert downstream["combined_min"] == 80
    assert downstream["combined_max"] == 117
    assert downstream["digit_min"] == 0
    assert downstream["digit_max"] == 37
    assert downstream["all_digits_valid"] is True
    assert downstream["decoded_integer_bits"] == 539
    assert downstream["decoded_length"] == 68
    assert downstream["half_hex"] == EXPECTED_HALF_HEX
    assert downstream["better_half_hex"] == EXPECTED_BETTER_HALF_HEX
    assert downstream["tail_hex"] == EXPECTED_TAIL_HEX
    assert downstream["compressed_p2pkh"] == EXPECTED_ADDRESSES
    assert len(downstream["fixed_base38_valid_offsets"]) == 15
    assert downstream["fixed_base38_full_span_offsets"] == (7,)

    uniqueness = report["published_uniqueness_family"]
    assert uniqueness["attempts"] == 210
    assert uniqueness["padding_valid_hits"] == (
        {
            "tokens_5_7": ("matrixsumlist", "yourlastcommand", "secondanswer"),
            "padding_length": 1,
            "payload_sha256": EXPECTED_PAYLOAD_SHA256,
        },
    )
    assert report["spam_provenance"] == {
        "known_spam_payer_addresses": EXPECTED_ADDRESSES,
        "derived_addresses_match_known_spam_payers": True,
        "phase156_op_return_messages": 105,
        "phase156_messages_from_these_payers": 88,
        "phase156_messages_from_creator_keys": 0,
    }

    calibration = report["calibration"]
    assert calibration["tested_password_kdf_forms"] == 4
    assert calibration["valid_padding_forms"] == 1
    assert calibration["random_pkcs7_valid_probability"] == Fraction(
        1334440654591915542993625911497130241,
        340282366920938463463374607431768211456,
    )
    print("[*] self-test OK: raw-digest/MD5 checkpoint and 103x103 invariants reproduce")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = audit()
    print("tokens:", " | ".join(report["tokens"]))
    print("xor digest:", report["xor_digest_hex"])
    for name, result in report["decryptions"].items():
        print(
            f"{name:12s} padding={result['valid_padding']}:{result['padding_length']} "
            f"payload={result['payload_length']} sha256={result['payload_sha256']}"
        )
    checkpoint = report["checkpoint"]
    matrix = report["matrix"]
    downstream = report["downstream"]
    probability = report["calibration"]["random_pkcs7_valid_probability"]
    uniqueness = report["published_uniqueness_family"]
    spam = report["spam_provenance"]
    print(
        "checkpoint:",
        f"entropy={checkpoint['entropy_bits_per_byte']:.9f}",
        f"strict_ascii={checkpoint['strict_ascii_ratio']:.6f}",
    )
    print(
        "matrix:",
        f"{matrix['side']}x{matrix['side']}",
        f"unused={matrix['unused_bits']}",
        f"S={matrix['S']}",
        f"Wr={matrix['Wr_one_based']}",
        f"Wc={matrix['Wc_one_based']}",
        f"p_big={matrix['padding_big_endian']}",
        f"p_little={matrix['padding_little_endian']}",
    )
    print(
        "downstream:",
        f"shift={downstream['shift_from_unused_bit_count']}",
        f"range={downstream['combined_min']}..{downstream['combined_max']}",
        f"base38={downstream['decoded_length']} bytes",
    )
    print(
        "split:",
        downstream["half_hex"],
        downstream["better_half_hex"],
        downstream["tail_hex"],
    )
    print(
        "addresses:",
        " | ".join(downstream["compressed_p2pkh"]),
    )
    print(
        "published uniqueness family:",
        f"{len(uniqueness['padding_valid_hits'])}/{uniqueness['attempts']} padding-valid",
    )
    print(
        "spam provenance:",
        f"derived-address match={spam['derived_addresses_match_known_spam_payers']}",
        f"messages={spam['phase156_messages_from_these_payers']}/"
        f"{spam['phase156_op_return_messages']}",
        f"creator-signed={spam['phase156_messages_from_creator_keys']}",
    )
    print(
        "random PKCS7-valid probability:",
        f"{float(probability):.9f} (~1 in {1 / float(probability):.3f})",
    )
    if args.self_test:
        self_test()


if __name__ == "__main__":
    main()
