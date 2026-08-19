#!/usr/bin/env python3
"""Detect private-key-shaped substrings in already-decrypted oracle output.

Every existing sweep script (`cb_common.aes_try_open`/`aes_try_open_ecb`, the
`weak_candidates_log.txt` printable-ratio gate, `binary_key_material_backfill.py`'s
raw `32|32`-byte binary check) already decides whether a decrypt's *body*
looks like plausible output. None of them ask a narrower, more specific
question once a body clears that bar: does this text/byte-string, read as key
material, actually decode to a valid secp256k1 private key?

This module answers that question for four disjoint encodings, all of which
the puzzle's own address format (both `PRIZE_ADDRESS` and `HALVING_ADDRESS`
in `first_hint_hash_audit.py` are legacy P2PKH `1...`) motivates checking:

* raw 32-byte binary (re-exposed here; `binary_key_material_backfill.py`
  already handles this case directly for SALPH/P32TRAILING's padded-64-byte
  shape -- `raw_binary_halves` just gives other callers the same split);
* a 64-hex-character string;
* a base58check WIF (mainnet, compressed or uncompressed; testnet excluded --
  not relevant to this puzzle);
* a checksum-valid BIP39 English mnemonic (12/15/18/21/24 words), derived via
  standard BIP32 to the master key (`m`) and the first legacy receiving
  address (`m/44'/0'/0'/0/0`), empty passphrase only -- there is no known
  puzzle passphrase to try, and testing arbitrary passphrases here would be
  exactly the open-ended search this project's brainstorm discipline avoids.
  Segwit paths (BIP49 `m/49'`, BIP84 `m/84'`) are deliberately NOT derived:
  they need bech32/P2SH address encoding this module doesn't implement, and
  neither known GSMG address is segwit, so there is no clue-based reason to
  add that surface.

Every finder is exact/checksum-gated, not approximate: a hex string must be
exactly 64 hex characters at a token boundary; a WIF must pass its base58
checksum; a mnemonic must pass its BIP39 checksum. `classify_body()` returns
every match (there can be more than one, e.g. multiple hex-looking runs); it
never itself decides a match is "the" answer. Address derivation, Bloom
lookups, and API verification are the caller's job (see `key_shape_sweep.py`),
reusing `binary_key_material_backfill.private_key_details`/`hash160` so this
project has exactly one implementation of "scalar -> address".
"""

import hashlib
import hmac
import re
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from binary_key_material_backfill import hash160, private_key_details  # noqa: E402
from first_hint_hash_audit import BASE58_ALPHABET, SECP256K1_ORDER, base58check  # noqa: E402

BIP39_WORDLIST_PATH = SCRIPT_DIR.parents[1] / "wordlists" / "bip39" / "english.txt"
BIP39_WORDS = BIP39_WORDLIST_PATH.read_text().split()
BIP39_WORD_INDEX = {word: index for index, word in enumerate(BIP39_WORDS)}
BIP39_LENGTHS = (12, 15, 18, 21, 24)  # ENT = 128/160/192/224/256 bits

HEX64_RE = re.compile(rb"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
WIF_RE = re.compile(
    rb"(?<![1-9A-HJ-NP-Za-km-z])(?:5[1-9A-HJ-NP-Za-km-z]{50}"
    rb"|[KL][1-9A-HJ-NP-Za-km-z]{51})(?![1-9A-HJ-NP-Za-km-z])"
)
WORD_RE = re.compile(rb"[a-zA-Z]+")

BIP44_LEGACY_PATH = (0x80000000 + 44, 0x80000000, 0x80000000, 0, 0)


def raw_binary_halves(body):
    """Split a 64-byte body into (half, better_half); `None` if not 64 bytes."""
    if len(body) != 64:
        return None
    return body[:32], body[32:]


def base58check_decode(token):
    """Inverse of `first_hint_hash_audit.base58check`; `None` on any failure."""
    if not token or any(c not in BASE58_ALPHABET for c in token):
        return None
    value = 0
    for char in token:
        value = value * 58 + BASE58_ALPHABET.index(char)
    body = value.to_bytes((value.bit_length() + 7) // 8, "big") if value else b""
    leading_ones = len(token) - len(token.lstrip("1"))
    full = b"\x00" * leading_ones + body
    if len(full) < 5:
        return None
    payload, checksum = full[:-4], full[-4:]
    if hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4] != checksum:
        return None
    return payload


def find_hex64(body):
    """Every checksum-free but scalar-valid 64-hex-char run in `body`."""
    found = []
    for match in HEX64_RE.finditer(body):
        key = bytes.fromhex(match.group().decode("ascii"))
        if 1 <= int.from_bytes(key, "big") < SECP256K1_ORDER:
            found.append(("hex64", key))
    return found


def wif_to_private_key(token):
    """Decode one WIF token; `None` unless it is a valid mainnet WIF."""
    payload = base58check_decode(token)
    if payload is None or payload[0] != 0x80:
        return None
    if len(payload) == 34 and payload[-1] == 0x01:
        key = payload[1:33]
    elif len(payload) == 33:
        key = payload[1:33]
    else:
        return None
    if not 1 <= int.from_bytes(key, "big") < SECP256K1_ORDER:
        return None
    return key


def find_wif(body):
    found = []
    for match in WIF_RE.finditer(body):
        key = wif_to_private_key(match.group().decode("ascii"))
        if key is not None:
            found.append(("wif", key))
    return found


def compressed_pubkey(private_key):
    value = int.from_bytes(private_key, "big")
    public = ec.derive_private_key(value, ec.SECP256K1()).public_key().public_numbers()
    return bytes([2 + (public.y & 1)]) + public.x.to_bytes(32, "big")


def bip39_checksum_valid(words):
    """`words`: exactly one of BIP39_LENGTHS entries, all in BIP39_WORD_INDEX."""
    bits = "".join(f"{BIP39_WORD_INDEX[w]:011b}" for w in words)
    checksum_bits = len(words) * 11 // 33
    entropy_bits, checksum = bits[:-checksum_bits], bits[-checksum_bits:]
    entropy = int(entropy_bits, 2).to_bytes(len(entropy_bits) // 8, "big")
    expected = bin(int.from_bytes(hashlib.sha256(entropy).digest(), "big"))[2:].zfill(256)
    return expected[:checksum_bits] == checksum


def mnemonic_seed(words):
    """BIP39 seed, empty passphrase (see module docstring for why)."""
    mnemonic = " ".join(words)
    return hashlib.pbkdf2_hmac("sha512", mnemonic.encode(), b"mnemonic", 2048)


def bip32_master(seed):
    digest = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    return digest[:32], digest[32:]


def bip32_ckd_priv(parent_key, parent_chaincode, index):
    """One BIP32 private-parent-key-to-private-child-key step; `None` in the
    astronomically unlikely case the derived scalar is invalid (spec-mandated
    skip, never expected to trigger)."""
    if index >= 0x80000000:
        data = b"\x00" + parent_key + index.to_bytes(4, "big")
    else:
        data = compressed_pubkey(parent_key) + index.to_bytes(4, "big")
    digest = hmac.new(parent_chaincode, data, hashlib.sha512).digest()
    left, right = digest[:32], digest[32:]
    left_int = int.from_bytes(left, "big")
    child_int = (left_int + int.from_bytes(parent_key, "big")) % SECP256K1_ORDER
    if left_int >= SECP256K1_ORDER or child_int == 0:
        return None
    return child_int.to_bytes(32, "big"), right


def bip32_derive_path(master_key, master_chaincode, path):
    key, chaincode = master_key, master_chaincode
    for index in path:
        step = bip32_ckd_priv(key, chaincode, index)
        if step is None:
            return None
        key, chaincode = step
    return key


def find_bip39(body):
    """Every checksum-valid BIP39 mnemonic window in `body`, each yielding the
    BIP32 master key (`m`) and the first legacy receiving key
    (`m/44'/0'/0'/0/0`)."""
    words = [w.decode("ascii").lower() for w in WORD_RE.findall(body)]
    found = []
    for length in BIP39_LENGTHS:
        for start in range(0, len(words) - length + 1):
            window = words[start:start + length]
            if any(w not in BIP39_WORD_INDEX for w in window):
                continue
            if not bip39_checksum_valid(window):
                continue
            seed = mnemonic_seed(window)
            master_key, master_chaincode = bip32_master(seed)
            if 1 <= int.from_bytes(master_key, "big") < SECP256K1_ORDER:
                found.append(("bip39_master", master_key))
            child_key = bip32_derive_path(master_key, master_chaincode, BIP44_LEGACY_PATH)
            if child_key is not None:
                found.append(("bip39_bip44_0", child_key))
    return found


def classify_body(body):
    """Every private-key-shaped candidate found in `body`, as
    `(source_label, 32_byte_key)` pairs. Does not dedupe across encodings
    (callers already dedupe by derived address before queuing)."""
    found = []
    halves = raw_binary_halves(body)
    if halves is not None:
        for label, key in (("raw_half", halves[0]), ("raw_better_half", halves[1])):
            if 1 <= int.from_bytes(key, "big") < SECP256K1_ORDER:
                found.append((label, key))
    found.extend(find_hex64(body))
    found.extend(find_wif(body))
    found.extend(find_bip39(body))
    return found


def self_test():
    assert len(BIP39_WORDS) == 2048, f"expected 2048 BIP39 words, got {len(BIP39_WORDS)}"
    assert BIP39_WORDS == sorted(BIP39_WORDS), "BIP39 wordlist must be sorted (spec requirement)"
    assert BIP39_WORDS[0] == "abandon" and BIP39_WORDS[-1] == "zoo"

    # base58check round trip, including the leading-zero-byte edge case.
    for payload in (b"\x00" + b"\x01" * 20, b"\x80" + b"\x00" * 32, b"\x80" + b"\xff" * 32 + b"\x01"):
        assert base58check_decode(base58check(payload)) == payload
    assert base58check_decode("not valid base58check!!") is None
    assert base58check_decode("1" + "1" * 33) is None  # valid alphabet, bad checksum

    # hex64: exact scalar range, word-boundary anchored (embedded in a longer
    # hex run must NOT match).
    key_hex = (5).to_bytes(32, "big").hex()
    assert find_hex64(f"prefix {key_hex} suffix".encode()) == [("hex64", (5).to_bytes(32, "big"))]
    assert find_hex64(("a" + key_hex).encode()) == []  # not anchored -> no match
    zero_hex = (0).to_bytes(32, "big").hex()
    assert find_hex64(zero_hex.encode()) == []  # scalar 0 is invalid

    # WIF: known-good mainnet compressed/uncompressed vectors for private key
    # value 1, cross-checked against `private_key_details`'s own WIF encoding
    # (both paths share nothing but the base58check primitive, so this also
    # catches a divergence between encode and decode).
    details = private_key_details((1).to_bytes(32, "big"))
    for label in ("compressed", "uncompressed"):
        wif = details[label]["wif"]
        assert wif_to_private_key(wif) == (1).to_bytes(32, "big"), (label, wif)
        assert find_wif(f"key: {wif} end".encode()) == [("wif", (1).to_bytes(32, "big"))]
    assert wif_to_private_key("L" + "1" * 51) is None  # bad checksum

    # BIP39: round-trip a synthetic 12-word mnemonic through our own
    # encoder/checksum so this doesn't depend on memorized external test
    # vectors -- entropy -> words -> checksum-valid -> recovered by
    # find_bip39, and a single flipped word breaks the checksum.
    entropy = bytes(range(16))  # 128 bits -> 12 words
    checksum_byte = hashlib.sha256(entropy).digest()[0]
    bits = "".join(f"{b:08b}" for b in entropy) + f"{checksum_byte:08b}"[:4]
    indices = [int(bits[i:i + 11], 2) for i in range(0, len(bits), 11)]
    words = [BIP39_WORDS[i] for i in indices]
    assert len(words) == 12
    assert bip39_checksum_valid(words)
    mutated = list(words)
    mutated[-1] = "zoo" if mutated[-1] != "zoo" else "abandon"
    assert not bip39_checksum_valid(mutated), "mutation must break the checksum for this test to mean anything"
    body = f"start {' '.join(words)} end".encode()
    hits = find_bip39(body)
    labels = {label for label, _ in hits}
    assert labels == {"bip39_master", "bip39_bip44_0"}, labels
    for _, key in hits:
        assert 1 <= int.from_bytes(key, "big") < SECP256K1_ORDER

    # BIP32 CKD: deterministic, hardened != normal, child is always a
    # different valid scalar from the parent for a real (non-astronomically-
    # unlucky) parent/chaincode pair.
    seed = mnemonic_seed(words)
    master_key, master_chaincode = bip32_master(seed)
    hardened = bip32_ckd_priv(master_key, master_chaincode, 0x80000000)
    normal = bip32_ckd_priv(master_key, master_chaincode, 0)
    again = bip32_ckd_priv(master_key, master_chaincode, 0x80000000)
    assert hardened is not None and normal is not None
    assert hardened[0] == again[0] and hardened[1] == again[1]  # deterministic
    assert hardened[0] != normal[0]  # hardened and normal diverge
    assert hardened[0] != master_key
    path_key = bip32_derive_path(master_key, master_chaincode, BIP44_LEGACY_PATH)
    assert path_key is not None and 1 <= int.from_bytes(path_key, "big") < SECP256K1_ORDER

    # compressed_pubkey matches the independently self-tested P2PKH address
    # path (first_hint_hash_audit / binary_key_material_backfill both assert
    # scalar 1 -> "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH").
    pub = compressed_pubkey((1).to_bytes(32, "big"))
    addr = base58check(b"\x00" + hash160(pub))
    assert addr == "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", addr

    # classify_body: raw binary64 shape still recognized alongside the new
    # encodings, and unrelated printable noise yields nothing.
    raw_body = (1).to_bytes(32, "big") + (2).to_bytes(32, "big")
    raw_hits = {label for label, _ in classify_body(raw_body)}
    assert raw_hits == {"raw_half", "raw_better_half"}, raw_hits
    assert classify_body(b"just some ordinary English sentence, nothing special here.") == []

    print("[*] self-test OK: base58check round trip, hex64/WIF anchoring, "
          "BIP39 checksum + BIP32 derivation, compressed_pubkey cross-check, "
          "classify_body coverage")


if __name__ == "__main__":
    self_test()
