#!/usr/bin/env python3
"""Audit SHA-256 readings of the exact first GSMG puzzle artifact."""

import hashlib
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aes_key_wrap_sweep import ALL_CBC_VARIANTS  # noqa: E402
from cb_common import (  # noqa: E402
    BLOBS,
    QUARANTINED_BLOBS,
    aes_keywrap_try_open_bytes,
    aes_try_open_bytes,
    raw_key_try_open,
)

IMAGE_DIR = Path(__file__).resolve().parents[2] / "doc" / "img"
FIRST_PIECE_IMAGE = IMAGE_DIR / "gsmg_puzzle_stage1.png"
ORIGINAL_TELEGRAM_JPEG = IMAGE_DIR / "gsmg_stage0_original_telegram.jpg"
ORIGINAL_TELEGRAM_JPEG_SHA256 = (
    "9e2a1473933636ea041581e4e0d795c75298b3a8fac52a21cc048e40e9d903a3"
)
RABBIT_IMAGE = (
    IMAGE_DIR / "gsmg_rabbit_hint.png"
)
PUZZLE_BANNER = b"GSMGIO5BTCPUZZLECHALLENGE"
PRIZE_ADDRESS = "1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe"
HALVING_ADDRESS = "17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa"
KNOWN_ENTRY_HASH = (
    "89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32"
)
PHASE1_PASSWORD = b"theflowerblossomsthroughwhatseemstobeaconcretesurface"
FIRST_RABBIT_HINT_MESSAGE = "Follow the white rabbit. 😉".encode()
FIRST_RABBIT_HINT_WORDS = b"Follow the white rabbit"
FIRST_RABBIT_HINT_CANONICAL = b"followthewhiterabbit"
PHASE1_PASSWORD_SHA256 = (
    "5ac407837447fba24ba2802e4d1e9aecb4580aa29fef1088cc387c180b746f75"
)
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
SECP256K1_ORDER = (
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
)


def base58check(payload):
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    value = int.from_bytes(payload + checksum, "big")
    encoded = ""
    while value:
        value, remainder = divmod(value, 58)
        encoded = BASE58_ALPHABET[remainder] + encoded
    leading_zeroes = len(payload + checksum) - len((payload + checksum).lstrip(b"\0"))
    return "1" * leading_zeroes + encoded


def p2pkh_addresses(private_key_bytes):
    private_value = int.from_bytes(private_key_bytes, "big")
    if not 1 <= private_value < SECP256K1_ORDER:
        raise ValueError("private key is outside the secp256k1 scalar range")
    public = ec.derive_private_key(
        private_value,
        ec.SECP256K1(),
    ).public_key().public_numbers()
    x_bytes = public.x.to_bytes(32, "big")
    y_bytes = public.y.to_bytes(32, "big")
    public_keys = {
        "compressed": bytes([2 + (public.y & 1)]) + x_bytes,
        "uncompressed": b"\x04" + x_bytes + y_bytes,
    }
    return {
        label: base58check(
            b"\x00" + hashlib.new(
                "ripemd160",
                hashlib.sha256(public_key).digest(),
            ).digest()
        )
        for label, public_key in public_keys.items()
    }


def self_test():
    addresses = p2pkh_addresses((1).to_bytes(32, "big"))
    assert addresses == {
        "compressed": "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH",
        "uncompressed": "1EHNa6Q4Jz2uvNExL497mE43ikXhwF6kZm",
    }
    visible = PUZZLE_BANNER + PRIZE_ADDRESS.encode()
    assert hashlib.sha256(visible).hexdigest() == KNOWN_ENTRY_HASH
    assert hashlib.sha256(PHASE1_PASSWORD).hexdigest() == PHASE1_PASSWORD_SHA256
    assert (
        hashlib.sha256(ORIGINAL_TELEGRAM_JPEG.read_bytes()).hexdigest()
        == ORIGINAL_TELEGRAM_JPEG_SHA256
    )


def source_materials():
    return {
        "visible_banner": PUZZLE_BANNER,
        "visible_prize_address": PRIZE_ADDRESS.encode(),
        "visible_banner_plus_address": PUZZLE_BANNER + PRIZE_ADDRESS.encode(),
        "original_creator_telegram_jpeg": ORIGINAL_TELEGRAM_JPEG.read_bytes(),
        "full_stage0_png": FIRST_PIECE_IMAGE.read_bytes(),
        "rabbit_grid_png": RABBIT_IMAGE.read_bytes(),
        # Support-group message 28522 is a direct creator reply to "when
        # hint?". The full Telegram message, its literal words, and the
        # creator's later exact concatenated form (messages 35283/36714)
        # define this closed three-member family.
        "first_rabbit_hint_exact_message": FIRST_RABBIT_HINT_MESSAGE,
        "first_rabbit_hint_words": FIRST_RABBIT_HINT_WORDS,
        "first_rabbit_hint_canonical": FIRST_RABBIT_HINT_CANONICAL,
        # The literal solved answer to the puzzle's first hint. This exact
        # hash was posted as a self-check in 2019, so its byte spelling is
        # independently fixed rather than normalized or guessed here.
        "solved_phase1_password": PHASE1_PASSWORD,
        # Self-referential readings: hash the literal words of the clue
        # phrase itself rather than an external puzzle artifact.
        "literal_our_first_hint": b"our first hint",
        "literal_our_first_hint_newline": b"our first hint\n",
        "literal_Our_first_hint_capitalized": b"Our first hint",
        "literal_our_first_hint_period": b"our first hint.",
        "literal_first_hint": b"first hint",
        "literal_full_phrase": b"our first hint is your last command",
        "literal_full_phrase_with_sha256_prefix": b"sha256 our first hint is your last command",
    }


def main():
    self_test()
    blobs = {**BLOBS, **QUARANTINED_BLOBS}
    targets = {PRIZE_ADDRESS, HALVING_ADDRESS}
    total_cbc_hits = 0
    total_wrap_hits = 0
    total_raw_key_hits = 0
    total_address_hits = 0

    for label, material in source_materials().items():
        digest = hashlib.sha256(material).digest()
        digest_hex = digest.hex()
        addresses = p2pkh_addresses(digest)
        address_hits = targets.intersection(addresses.values())
        total_address_hits += len(address_hits)

        cbc_hits = []
        wrap_hits = []
        for passphrase_kind, passphrase in (
            ("digest_raw", digest),
            ("digest_hex", digest_hex.encode()),
        ):
            cbc_hit = aes_try_open_bytes(
                passphrase,
                kdf_variants=ALL_CBC_VARIANTS,
                blobs=blobs,
            )
            if cbc_hit:
                cbc_hits.append((passphrase_kind, cbc_hit))
            for wrap_hit in aes_keywrap_try_open_bytes(passphrase, blobs=blobs):
                wrap_hits.append((passphrase_kind, wrap_hit))
        raw_key_hits = raw_key_try_open(digest, blobs=blobs)

        total_cbc_hits += len(cbc_hits)
        total_wrap_hits += len(wrap_hits)
        total_raw_key_hits += len(raw_key_hits)

        print(label)
        print("  sha256:", digest_hex)
        print("  p2pkh compressed:", addresses["compressed"])
        print("  p2pkh uncompressed:", addresses["uncompressed"])
        print("  known-address hits:", sorted(address_hits))
        print("  CBC passphrase hits:", len(cbc_hits))
        print("  Key-Wrap hits:", len(wrap_hits))
        print("  raw-key CBC hits:", len(raw_key_hits))

    print(
        "totals:",
        f"address={total_address_hits}",
        f"cbc={total_cbc_hits}",
        f"wrap={total_wrap_hits}",
        f"raw_key={total_raw_key_hits}",
    )


if __name__ == "__main__":
    main()
