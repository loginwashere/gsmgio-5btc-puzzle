#!/usr/bin/env python3
"""Bounded audit of the ``SalPhaseIon + T -> SaltPhaseIon`` hypothesis.

This is a clue-driven construction audit, not a dictionary search.  It keeps
six exact observations together:

* ``SalPhaseIon`` becomes ``SaltPhaseIon`` by receiving the ``T`` from the
  creator's "a True giveaway" wording;
* every authenticated encrypted target visibly starts with OpenSSL's
  ``Salted__`` envelope;
* the first-piece color values are exact complementary 24-bit masks;
* SALPH/P32 have 80-byte ciphertext bodies with natural matrix layouts;
* the prime-walk output is 31 bytes, one byte short of a Bitcoin scalar; and
* the unresolved DBBI/FAED lengths have prime sum and difference.

The generated family is intentionally finite.  The solved Phase 3.2 blob is a
positive control for salt/XOR claims, and the community's literal
SALT/PHRASE/ION XOR reading is run over DBBI, FAED, and the open blob bodies.
Every resulting 32-byte material is tested
as a secp256k1 private scalar against the genuine GSMG addresses and as a
literal raw AES/3DES key against the authenticated blobs.  No candidate words,
permutations, arbitrary offsets, or variable iteration counts are introduced.

Usage:
    python3 tools/gsmg/salt_phase_ion_audit.py
    python3 tools/gsmg/salt_phase_ion_audit.py --self-test
"""

import argparse
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from binary_key_material_backfill import private_key_details  # noqa: E402
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
    evp_bytes_to_key,
    _load_blob,
    raw_key_try_open,
)
from data import (  # noqa: E402
    DBBI,
    FAED,
    PHASE32_BLOB_B64,
    PHASE32_PASSWORD,
    PHASE32_PLAINTEXT_PREFIX,
)
from first_hint_hash_audit import HALVING_ADDRESS, PRIZE_ADDRESS  # noqa: E402


TITLE = "SalPhaseIon"
SALT_TITLE = "SaltPhaseIon"
SELECTED = b"ncsyangcahiriasogaleafayanestve"
BLUE_MASK = bytes.fromhex("f73d92")
YELLOW_MASK = bytes.fromhex("08c26d")
KNOWN_ADDRESSES = {PRIZE_ADDRESS, HALVING_ADDRESS}
MATRIX_LAYOUTS = ((5, 16), (8, 10), (10, 8), (16, 5))
ONE_BYTE_COMPLETIONS = {
    "true_T": b"T",
    "true_t": b"t",
    "rebus_H": b"H",
    "rebus_h": b"h",
    "fefe_n": b"n",
    "zero": b"\x00",
    "enter_lf": b"\n",
    "enter_cr": b"\r",
    "space": b" ",
}
LITERAL_XOR_KEYS = {
    "tri_initials_lower": b"spi",
    "tri_initials_upper": b"SPI",
    "salt": b"salt",
    "phrase": b"phrase",
    "ion": b"ion",
    "three_words": b"saltphraseion",
    "expanded_words": b"saltpassphraseiteration",
}


def is_prime(value):
    if value < 2:
        return False
    if value % 2 == 0:
        return value == 2
    divisor = 3
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 2
    return True


def prime_rank(value):
    if not is_prime(value):
        return None
    return sum(is_prime(candidate) for candidate in range(2, value + 1))


def xor_bytes(left, right):
    if len(left) != len(right):
        raise ValueError("xor operands must have equal lengths")
    return bytes(a ^ b for a, b in zip(left, right))


def bytewise(left, right, operation):
    if len(left) != len(right):
        raise ValueError("bytewise operands must have equal lengths")
    if operation == "xor":
        return xor_bytes(left, right)
    if operation == "add":
        return bytes((a + b) & 0xFF for a, b in zip(left, right))
    if operation == "sub_ab":
        return bytes((a - b) & 0xFF for a, b in zip(left, right))
    if operation == "sub_ba":
        return bytes((b - a) & 0xFF for a, b in zip(left, right))
    raise ValueError(f"unknown operation: {operation}")


def repeat_to(data, length=32):
    if not data:
        raise ValueError("cannot repeat an empty value")
    return (data * ((length + len(data) - 1) // len(data)))[:length]


def repeating_xor(data, key):
    return xor_bytes(data, repeat_to(key, len(data)))


def printable_ratio(data):
    if not data:
        return 0.0
    return sum(byte in (9, 10, 13) or 32 <= byte <= 126 for byte in data) / len(data)


def longest_printable_run(data):
    longest = current = 0
    for byte in data:
        if byte in (9, 10, 13) or 32 <= byte <= 126:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def bit_matrix_sums(data):
    """Treat eight bytes as an 8x8 MSB-first bit matrix."""
    if len(data) != 8:
        raise ValueError("bit_matrix_sums requires exactly eight bytes")
    rows = tuple(byte.bit_count() for byte in data)
    cols = tuple(
        sum((data[row] >> (7 - column)) & 1 for row in range(8))
        for column in range(8)
    )
    return rows, cols


def checker_halves(body, rows, columns):
    if rows * columns != len(body):
        raise ValueError("layout does not fit body")
    first = bytearray()
    second = bytearray()
    for row in range(rows):
        for column in range(columns):
            target = first if (row + column) % 2 == 0 else second
            target.append(body[row * columns + column])
    if len(first) != len(second):
        raise AssertionError("declared even matrix did not split evenly")
    return bytes(first), bytes(second)


class CandidateRegistry:
    def __init__(self):
        self.sources = defaultdict(list)

    def add(self, source, material):
        if len(material) != 32:
            raise ValueError(f"{source}: candidate is {len(material)} bytes, not 32")
        if source not in self.sources[material]:
            self.sources[material].append(source)

    def add_hash(self, source, material):
        self.add(f"sha256:{source}", hashlib.sha256(material).digest())


def add_title_candidates(registry):
    for title in (SALT_TITLE, SALT_TITLE.lower(), SALT_TITLE.upper(), "salt phase ion"):
        registry.add_hash(f"title:{title}", title.encode())


def add_selected_completions(registry):
    bases = {
        "selected_lower": SELECTED,
        "selected_upper": SELECTED.upper(),
        "selected_reverse": SELECTED[::-1],
        "selected_upper_reverse": SELECTED.upper()[::-1],
    }
    for base_label, base in bases.items():
        registry.add_hash(base_label, base)
        digest = hashlib.sha256(base).digest()
        registry.add(f"{base_label}+sha_first", base + digest[:1])
        registry.add(f"sha_first+{base_label}", digest[:1] + base)
        for suffix_label, suffix in ONE_BYTE_COMPLETIONS.items():
            completed = base + suffix
            registry.add(f"{base_label}+{suffix_label}", completed)
            registry.add(f"{suffix_label}+{base_label}", suffix + base)


def add_color_mask_candidates(registry):
    masks = {
        "blue": repeat_to(BLUE_MASK),
        "yellow": repeat_to(YELLOW_MASK),
    }
    completed = {
        label: SELECTED + suffix
        for label, suffix in ONE_BYTE_COMPLETIONS.items()
    }
    for base_label, base in completed.items():
        for mask_label, mask in masks.items():
            registry.add(f"selected+{base_label}:xor:{mask_label}", xor_bytes(base, mask))
            registry.add(
                f"selected+{base_label}:and:{mask_label}",
                bytes(a & b for a, b in zip(base, mask)),
            )
    registry.add("color_masks:xor", xor_bytes(masks["blue"], masks["yellow"]))
    registry.add(
        "color_masks:add",
        bytes((a + b) & 0xFF for a, b in zip(masks["blue"], masks["yellow"])),
    )


def add_salt_candidates(registry, salt_reports):
    for tag, (salt, _body) in BLOBS.items():
        rows, cols = bit_matrix_sums(salt)
        salt_reports[tag] = {
            "salt": salt.hex(),
            "row_sums": rows,
            "column_sums": cols,
        }
        expanded = repeat_to(salt)
        registry.add(f"{tag}:salt_repeated", expanded)
        registry.add_hash(f"{tag}:salt", salt)
        registry.add_hash(f"{tag}:salt_row_sums", bytes(rows))
        registry.add_hash(f"{tag}:salt_column_sums", bytes(cols))
        registry.add_hash(f"{tag}:selected+salt", SELECTED + salt)
        registry.add_hash(f"{tag}:salt+selected", salt + SELECTED)
        for suffix_label, suffix in ONE_BYTE_COMPLETIONS.items():
            registry.add(
                f"{tag}:selected+{suffix_label}:xor_salt",
                xor_bytes(SELECTED + suffix, expanded),
            )

    # The solved Phase 3.2 artifact is a calibration control, not another
    # unsolved-target candidate generator.  Still report its fourth known salt
    # beside the four open/default blobs so cross-salt structure claims cannot
    # omit the solved control.
    phase32_salt, _phase32_body = _load_blob(PHASE32_BLOB_B64)
    rows, cols = bit_matrix_sums(phase32_salt)
    salt_reports["PHASE32_SOLVED"] = {
        "salt": phase32_salt.hex(),
        "row_sums": rows,
        "column_sums": cols,
    }


def add_literal_xor_candidates(registry, xor_reports):
    """Run WILL's literal SALT/PHRASE/ION reading as a small XOR oracle."""
    sources = {
        "DBBI": DBBI.encode(),
        "FAED": FAED.encode(),
    }
    sources.update({tag: body for tag, (_salt, body) in BLOBS.items()})
    markers = (b"Salted__", PHASE32_PLAINTEXT_PREFIX.encode(), b"bitcoin", b"private key")
    for source_name, source in sources.items():
        xor_reports[source_name] = []
        for key_name, key in LITERAL_XOR_KEYS.items():
            transformed = repeating_xor(source, key)
            marker_hits = tuple(
                marker.decode(errors="replace")
                for marker in markers
                if marker.lower() in transformed.lower()
            )
            xor_reports[source_name].append({
                "key": key_name,
                "printable_ratio": printable_ratio(transformed),
                "longest_printable_run": longest_printable_run(transformed),
                "marker_hits": marker_hits,
            })
            registry.add_hash(f"literal_xor:{source_name}:{key_name}:whole", transformed)
            if len(transformed) >= 32:
                registry.add(f"literal_xor:{source_name}:{key_name}:first32", transformed[:32])
                registry.add(f"literal_xor:{source_name}:{key_name}:last32", transformed[-32:])


def add_length_candidates(registry):
    total = len(DBBI) + len(FAED)
    difference = abs(len(FAED) - len(DBBI))
    for label, value in (("length_sum", total), ("length_difference", difference)):
        registry.add(label, value.to_bytes(32, "big"))
        registry.add_hash(f"{label}:decimal", str(value).encode())
    registry.add_hash("lengths:sum_then_difference", f"{total}{difference}".encode())
    registry.add_hash("lengths:difference_then_sum", f"{difference}{total}".encode())


def add_blob_matrix_candidates(registry, matrix_reports):
    operations = ("xor", "add", "sub_ab", "sub_ba")
    for tag, (_salt, body) in BLOBS.items():
        if len(body) != 80:
            continue
        matrix_reports[tag] = []
        for rows, columns in MATRIX_LAYOUTS:
            left, right = checker_halves(body, rows, columns)
            entry = {
                "layout": f"{rows}x{columns}",
                "half_length": len(left),
                "left_sha256": hashlib.sha256(left).hexdigest(),
                "right_sha256": hashlib.sha256(right).hexdigest(),
            }
            matrix_reports[tag].append(entry)
            left_hash = hashlib.sha256(left).digest()
            right_hash = hashlib.sha256(right).digest()
            for operation in operations:
                combined = bytewise(left, right, operation)
                registry.add_hash(
                    f"{tag}:{rows}x{columns}:checker:{operation}", combined
                )
                registry.add(
                    f"{tag}:{rows}x{columns}:checker_hashes:{operation}",
                    bytewise(left_hash, right_hash, operation),
                )

        # A second exact duality: face the first half toward a 180-degree
        # rotation of the second half.  Both operands are 40 bytes.
        left = body[:40]
        right = body[40:][::-1]
        for operation in operations:
            registry.add_hash(f"{tag}:facing_halves:{operation}", bytewise(left, right, operation))


def build_candidates():
    registry = CandidateRegistry()
    salt_reports = {}
    matrix_reports = {}
    xor_reports = {}
    add_title_candidates(registry)
    add_selected_completions(registry)
    add_color_mask_candidates(registry)
    add_salt_candidates(registry, salt_reports)
    add_literal_xor_candidates(registry, xor_reports)
    add_length_candidates(registry)
    add_blob_matrix_candidates(registry, matrix_reports)
    return registry, salt_reports, matrix_reports, xor_reports


def evaluate(registry):
    address_hits = []
    decrypt_hits = []
    invalid_scalars = 0
    for material, sources in registry.sources.items():
        details = private_key_details(material)
        if details is None:
            invalid_scalars += 1
        else:
            for address_type, address_data in details.items():
                if address_data["address"] in KNOWN_ADDRESSES:
                    address_hits.append({
                        "sources": tuple(sources),
                        "address_type": address_type,
                        "address": address_data["address"],
                        "private_key_hex": material.hex(),
                    })
        for tag, cipher, plaintext, z_score in raw_key_try_open(material):
            decrypt_hits.append({
                "sources": tuple(sources),
                "blob": tag,
                "cipher": cipher,
                "z_score": z_score,
                "private_key_hex": material.hex(),
                "plaintext": plaintext,
            })
    return {
        "candidate_count": len(registry.sources),
        "invalid_scalar_count": invalid_scalars,
        "address_hits": address_hits,
        "decrypt_hits": decrypt_hits,
    }


def evaluate_title_passphrases():
    """Try only the exact new title reading through every established oracle.

    This is deliberately separate from the 32-byte construction registry:
    here the title is a passphrase and the blob's own salt participates in the
    established EVP_BytesToKey/PBKDF2 derivations.
    """
    forms = tuple(sorted({
        SALT_TITLE,
        SALT_TITLE.lower(),
        SALT_TITLE.upper(),
        "salt phase ion",
        "SALT PHASE ION",
    }))
    hits = []
    for form in forms:
        encoded = form.encode()
        families = (
            ("cbc", aes_try_open_bytes, KDF_VARIANTS + EXTENDED_CIPHER_VARIANTS),
            ("stream", aes_try_open_stream_bytes, STREAM_CIPHER_VARIANTS),
            ("ecb", aes_try_open_ecb_bytes, ECB_CIPHER_VARIANTS),
            ("keywrap", aes_keywrap_try_open_bytes, KEY_WRAP_KDF_VARIANTS),
        )
        for family, oracle, variants in families:
            for result in oracle(encoded, kdf_variants=variants) or ():
                hits.append({"form": form, "family": family, "result": repr(result)})
    return {
        "forms": forms,
        "family_count": 4,
        "hits": hits,
    }


def decrypt_phase32_ground_truth():
    salt, ciphertext = _load_blob(PHASE32_BLOB_B64)
    key, iv = evp_bytes_to_key(PHASE32_PASSWORD.encode(), salt, "sha256", 32)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    pad = padded[-1]
    if not (1 <= pad <= 16 and padded[-pad:] == bytes([pad]) * pad):
        raise AssertionError("Phase 3.2 ground truth no longer has valid PKCS7 padding")
    plaintext = padded[:-pad]
    if not plaintext.startswith(PHASE32_PLAINTEXT_PREFIX.encode()):
        raise AssertionError("Phase 3.2 ground truth prefix mismatch")
    return salt, ciphertext, plaintext, key


def phase32_calibration():
    """Gate speculative salt/XOR mechanisms against the solved blob first.

    A mechanism passes only if it recovers the known Phase 3.2 plaintext using
    its proposed material.  The ordinary OpenSSL path is retained as the
    positive control, so a zero result cannot be blamed on the AES oracle.
    """
    salt, ciphertext, plaintext, correct_key = decrypt_phase32_ground_truth()
    rows, columns = bit_matrix_sums(salt)
    phase_blobs = {"PHASE32": (salt, ciphertext)}
    salt_candidates = {
        "salt_bytes_as_password": salt,
        "salt_hex_as_password": salt.hex().encode(),
        "salt_repeated_raw_key": repeat_to(salt),
        "sha256_salt_raw_key": hashlib.sha256(salt).digest(),
        "sha256_row_sums_raw_key": hashlib.sha256(bytes(rows)).digest(),
        "sha256_column_sums_raw_key": hashlib.sha256(bytes(columns)).digest(),
    }
    decrypt_hits = []
    for name, material in salt_candidates.items():
        if aes_try_open_bytes(material, blobs=phase_blobs):
            decrypt_hits.append(f"{name}:passphrase_kdf")
        if len(material) in (16, 24, 32) and raw_key_try_open(material, blobs=phase_blobs):
            decrypt_hits.append(f"{name}:raw_zero_iv")

    xor_reports = []
    overlap = min(len(ciphertext), len(plaintext))
    observed_stream = xor_bytes(ciphertext[:overlap], plaintext[:overlap])
    for key_name, operand in {
        "salt": salt,
        "blue_mask": BLUE_MASK,
        "yellow_mask": YELLOW_MASK,
        **LITERAL_XOR_KEYS,
    }.items():
        transformed_ciphertext = repeating_xor(ciphertext, operand)
        transformed_plaintext = repeating_xor(plaintext, operand)
        prefix_match = transformed_ciphertext.startswith(PHASE32_PLAINTEXT_PREFIX.encode())
        periodic_stream_match = observed_stream == repeat_to(operand, overlap)
        xor_reports.append({
            "operand": key_name,
            "ciphertext_to_known_prefix": prefix_match,
            "known_xor_stream_is_periodic_operand": periodic_stream_match,
            "plaintext_printable_before": printable_ratio(plaintext),
            "plaintext_printable_after": printable_ratio(transformed_plaintext),
        })

    return {
        "salt": salt.hex(),
        "ciphertext_length": len(ciphertext),
        "plaintext_length": len(plaintext),
        "known_prefix": PHASE32_PLAINTEXT_PREFIX,
        "positive_control": bool(
            aes_try_open_bytes(PHASE32_PASSWORD.encode(), blobs=phase_blobs)
        ) and correct_key == evp_bytes_to_key(
            PHASE32_PASSWORD.encode(), salt, "sha256", 32
        )[0],
        "salt_row_sums": rows,
        "salt_column_sums": columns,
        "speculative_decrypt_hits": decrypt_hits,
        "xor_reports": xor_reports,
    }


def arithmetic_spine_report():
    triple = (23, 16, 7)
    total, difference = len(DBBI) + len(FAED), len(FAED) - len(DBBI)
    blob_blocks = {
        tag: len(body) // 16
        for tag, (_salt, body) in BLOBS.items()
    }
    return {
        "triple": triple,
        "triple_sum": sum(triple),
        "sum_minus_triple_sum": total - sum(triple),
        "difference_minus_triple_sum": difference - sum(triple),
        "91_factors": (7, 13),
        "570_factors": (2, 3, 5, 19),
        "570_remainders_by_triple": tuple(570 % value for value in triple),
        "open_blob_aes_blocks": blob_blocks,
        "open_blob_block_prime_ranks": {
            tag: prime_rank(count) for tag, count in blob_blocks.items()
        },
    }


def title_eye_report():
    headings = (TITLE, "Cosmic Duality")
    report = {}
    for heading in headings:
        positions = tuple(index for index, char in enumerate(heading) if char.lower() == "i")
        flanks = tuple(
            heading[index - 1] + heading[index + 1]
            for index in positions
            if 0 < index < len(heading) - 1
        )
        report[heading] = {"positions_zero_based": positions, "flanks": flanks}
    return report


def audit():
    registry, salt_reports, matrix_reports, xor_reports = build_candidates()
    return {
        "title_mutation": TITLE[:3] + "t" + TITLE[3:],
        "color_xor": xor_bytes(BLUE_MASK, YELLOW_MASK).hex(),
        "color_sum": (int.from_bytes(BLUE_MASK, "big") + int.from_bytes(YELLOW_MASK, "big")),
        "dbbi_length": len(DBBI),
        "faed_length": len(FAED),
        "length_sum": len(DBBI) + len(FAED),
        "length_sum_is_prime": is_prime(len(DBBI) + len(FAED)),
        "length_difference": abs(len(FAED) - len(DBBI)),
        "length_difference_is_prime": is_prime(abs(len(FAED) - len(DBBI))),
        "selected_length": len(SELECTED),
        "salt_reports": salt_reports,
        "matrix_reports": matrix_reports,
        "literal_xor_reports": xor_reports,
        "phase32_calibration": phase32_calibration(),
        "arithmetic_spine": arithmetic_spine_report(),
        "title_eyes": title_eye_report(),
        "evaluation": evaluate(registry),
        "title_passphrases": evaluate_title_passphrases(),
    }


def self_test():
    assert TITLE[:3] + "t" + TITLE[3:] == SALT_TITLE
    assert xor_bytes(BLUE_MASK, YELLOW_MASK) == b"\xff\xff\xff"
    assert int.from_bytes(BLUE_MASK, "big") + int.from_bytes(YELLOW_MASK, "big") == 0xFFFFFF
    assert len(SELECTED) == 31
    assert (len(DBBI), len(FAED)) == (91, 570)
    assert is_prime(661) and is_prime(479)
    assert not is_prime(1) and not is_prime(91) and not is_prime(570)
    assert bit_matrix_sums(bytes.fromhex("ff00000000000000")) == (
        (8, 0, 0, 0, 0, 0, 0, 0),
        (1, 1, 1, 1, 1, 1, 1, 1),
    )
    test_body = bytes(range(80))
    for rows, columns in MATRIX_LAYOUTS:
        left, right = checker_halves(test_body, rows, columns)
        assert len(left) == len(right) == 40
        assert sorted(left + right) == list(range(80))
    one_details = private_key_details((1).to_bytes(32, "big"))
    assert one_details["compressed"]["address"] == "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"
    report = audit()
    assert report["title_mutation"] == SALT_TITLE
    assert report["evaluation"]["candidate_count"] > 100
    assert set(report["salt_reports"]) == {
        "SALPH", "COSMIC", "P32TRAILING", "URLBLOB", "PHASE32_SOLVED"
    }
    assert set(report["matrix_reports"]) == {"SALPH", "P32TRAILING"}
    assert len(report["title_passphrases"]["forms"]) == 5
    assert report["phase32_calibration"]["salt"] == "eefc4c5befc1656a"
    assert report["phase32_calibration"]["positive_control"]
    assert not report["phase32_calibration"]["speculative_decrypt_hits"]
    assert not any(
        item["ciphertext_to_known_prefix"]
        or item["known_xor_stream_is_periodic_operand"]
        for item in report["phase32_calibration"]["xor_reports"]
    )
    assert report["arithmetic_spine"]["570_remainders_by_triple"] == (18, 10, 3)
    assert tuple(report["arithmetic_spine"]["open_blob_aes_blocks"].values()) == (
        5, 83, 5, 6
    )
    assert tuple(
        report["arithmetic_spine"]["open_blob_block_prime_ranks"].values()
    ) == (3, 23, 3, None)
    assert report["title_eyes"][TITLE]["flanks"] == ("eo",)
    print(
        "[*] self-test OK: exact title/color/length identities, salt matrices, "
        f"matrix splits, scalar oracle, and {report['evaluation']['candidate_count']} "
        "deduplicated candidates verified"
    )


def print_report(report):
    print(f"[*] title mutation: {TITLE} + T -> {report['title_mutation']}")
    print(
        "[*] complementary colors: "
        f"{BLUE_MASK.hex().upper()} XOR {YELLOW_MASK.hex().upper()} = "
        f"{report['color_xor'].upper()}; sum = {report['color_sum']:06X}"
    )
    print(
        f"[*] lengths: DBBI={report['dbbi_length']}, FAED={report['faed_length']}, "
        f"sum={report['length_sum']} (prime={report['length_sum_is_prime']}), "
        f"difference={report['length_difference']} "
        f"(prime={report['length_difference_is_prime']})"
    )
    print(f"[*] selected prime-walk text length: {report['selected_length']} bytes")
    for tag, salt in report["salt_reports"].items():
        print(
            f"[*] {tag} salt={salt['salt']} row_sums={salt['row_sums']} "
            f"column_sums={salt['column_sums']}"
        )
    for tag, layouts in report["matrix_reports"].items():
        print(
            f"[*] {tag}: {len(layouts)} exact 80-byte matrix layouts, "
            "each split into 40/40 checkerboard channels"
        )
    calibration = report["phase32_calibration"]
    print(
        "[*] Phase 3.2 calibration: "
        f"salt={calibration['salt']}, ciphertext={calibration['ciphertext_length']} bytes, "
        f"plaintext={calibration['plaintext_length']} bytes, "
        f"positive_control={calibration['positive_control']}, "
        f"speculative_salt_decrypt_hits={len(calibration['speculative_decrypt_hits'])}, "
        "literal/salt/mask XOR matches="
        f"{sum(item['ciphertext_to_known_prefix'] or item['known_xor_stream_is_periodic_operand'] for item in calibration['xor_reports'])}"
    )
    literal_reports = report["literal_xor_reports"]
    literal_marker_hits = sum(
        len(item["marker_hits"])
        for source_reports in literal_reports.values()
        for item in source_reports
    )
    print(
        f"[*] literal SALT/PHRASE/ION XOR: {len(LITERAL_XOR_KEYS)} keys over "
        f"{len(literal_reports)} sources; recognizable marker hits={literal_marker_hits}"
    )
    spine = report["arithmetic_spine"]
    print(
        f"[*] 661/479 on [23,16,7] spine: triple sum={spine['triple_sum']}; "
        f"661-46={spine['sum_minus_triple_sum']}, "
        f"479-46={spine['difference_minus_triple_sum']}; "
        f"570 remainders={spine['570_remainders_by_triple']}"
    )
    print(
        f"[*] open-blob AES blocks: {spine['open_blob_aes_blocks']}; "
        f"prime ranks={spine['open_blob_block_prime_ranks']}"
    )
    print(f"[*] title-I audit: {report['title_eyes']}")
    result = report["evaluation"]
    print(
        f"[*] evaluated {result['candidate_count']} unique 32-byte constructions "
        f"({result['invalid_scalar_count']} outside the secp256k1 scalar range)"
    )
    print(f"[*] exact known-address hits: {len(result['address_hits'])}")
    print(f"[*] literal raw-key blob openings: {len(result['decrypt_hits'])}")
    title_result = report["title_passphrases"]
    print(
        f"[*] exact SaltPhaseIon passphrase forms: {len(title_result['forms'])} "
        f"across {title_result['family_count']} oracle families; "
        f"hits={len(title_result['hits'])}"
    )
    for hit in result["address_hits"]:
        print(f"[+++ ADDRESS HIT] {hit}")
    for hit in result["decrypt_hits"]:
        printable = dict(hit)
        printable["plaintext"] = printable["plaintext"][:160]
        print(f"[+++ RAW-KEY HIT] {printable}")
    for hit in title_result["hits"]:
        print(f"[+++ TITLE-PASSPHRASE HIT] {hit}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    print_report(audit())


if __name__ == "__main__":
    main()
