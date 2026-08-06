"""Shared straddling-checkerboard decode + AES-oracle verification, ported from the
community fork's `cb2.py` (decoder) and `joint_attack.py` (AES oracle).

Uses the `cryptography` package (already present via apt's python3-cryptography) for
AES-CBC instead of pycryptodome (not installed, and this environment has no `pip`).

Runs a self-test against the known-good Phase 3.2.2 vector at import time so a
porting bug can't silently produce false negatives in every script that imports
this module.
"""
import base64
import hmac
import hashlib
import itertools
import json
import math
import re
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.keywrap import (
    InvalidUnwrap,
    aes_key_unwrap,
    aes_key_unwrap_with_padding,
    aes_key_wrap,
    aes_key_wrap_with_padding,
)

from data import (
    ALPHA_322,
    COSMIC_BLOB_B64,
    P32_TRAILING_BLOB_B64,
    PHASE32_BLOB_B64,
    PHASE32_PASSWORD,
    PHASE32_PLAINTEXT_PREFIX,
    SALPHASEION_BLOB_B64,
    URLBLOB_B64,
    VALIDATION_ANSWER_PREFIX,
    VALIDATION_ESCAPES,
    VALIDATION_NUM,
)

ALL_ESCAPE_PAIRS = list(itertools.combinations(range(10), 2))  # 45 pairs


def build_board(alphabet28, e1, e2):
    e1, e2 = sorted((e1, e2))
    top_cols = [c for c in range(10) if c not in (e1, e2)]
    bd = {}
    for k, c in enumerate(top_cols):
        bd[str(c)] = alphabet28[k]
    for c in range(10):
        bd[f"{e1}{c}"] = alphabet28[8 + c]
    for c in range(10):
        bd[f"{e2}{c}"] = alphabet28[18 + c]
    return bd


def decode(digits, alphabet28, e1, e2):
    bd = build_board(alphabet28, e1, e2)
    out = []
    i = 0
    while i < len(digits):
        d = int(digits[i])
        if d in (e1, e2):
            if i + 1 >= len(digits):
                out.append("?")
                break
            out.append(bd.get(digits[i:i + 2], "?"))
            i += 2
        else:
            out.append(bd.get(digits[i], "?"))
            i += 1
    return "".join(out)


def pad28(seed):
    """keyword -> keyed 28-symbol alphabet (26 letters, deduped+keyword-first, plus
    '.' inserted twice as the straddling-checkerboard row/col separators)."""
    s = "".join(dict.fromkeys(re.sub(r"[^A-Za-z]", "", seed).upper()))
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if ch not in s:
            s += ch
    s = s[:26]
    return s[:8] + "." + s[8:17] + "." + s[17:26]


MAPS = {
    "a0i8": {c: str(i) for i, c in enumerate("abcdefghi")},
    "a1i9": {c: str(i + 1) for i, c in enumerate("abcdefghi")},
}

# ── Native base-9 checkerboard model (hypothesis: dbbi/faed's a-i alphabet IS the
# digit system, not a lossy stand-in for decimal 0-9). Escape-share analysis (see
# doc/GSMG_PUZZLE.md) found {b,e} matches the known-good 3.2.2 escape-digit character
# share (47.25% vs 46.98%) far better than any other pair among all 36 candidates,
# and segments dbbi cleanly (no dangling escape). That forces a 7-top + 9 + 9 = 25
# symbol code table, not 8+10+10=28 -- consistent with a classic 25-letter
# Polybius-style alphabet (I/J merged) rather than 26-letters-plus-2-dots.
NINE_SYMS = "abcdefghi"


TAIL_FILL_ORDERS = {
    "forward": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "reverse": "ZYXWVUTSRQPONMLKJIHGFEDCBA",
    "keyboard": "QWERTYUIOPASDFGHJKLZXCVBNM",
}


def pad25(seed, drop="J", tail_fill="forward", merge_direction="backward"):
    """keyword -> keyed 25-symbol alphabet (26 letters minus `drop`, merged into a
    neighboring letter, deduped+keyword-first) -- the natural analogue of pad28() for
    a 7+9+9 board. `drop` defaults to J (classic Polybius practice, merged into I) but
    is a parameter since that specific choice is itself a guess -- 3.2.2's one
    validated example used a 26-letter/28-symbol board, so there is no ground truth
    for what a 25-letter board would drop. `tail_fill` governs what order the
    *leftover* (non-keyword) letters are appended in -- confirmed UNCONSTRAINED, not
    just approximated, for messages like 3.2.2's: its real tail order (JQZXW) matches
    none of pad28()'s formula-generated JQWXZ nor pad25()'s reverse/keyboard presets,
    and checking the validated 91-char answer directly shows why -- it never uses any
    of J/Q/X/Z/W, so every one of the 120 possible orderings of that tail would have
    decoded identically. The parameter still matters whenever a candidate's true
    answer *does* need a rare tail letter (which this axis can't predict in advance),
    so it stays swept rather than fixed -- but there is no hidden rule to find for the
    one case that's actually been checked; the letters are simply never read.
    `merge_direction`
    governs whether `drop`'s occurrences fold into the alphabetically-preceding letter
    ("backward", e.g. J->I -- the only direction ever tested before this) or the
    following one ("forward", e.g. J->K) -- never previously exposed as a variable at
    all, and equally unconfirmed."""
    drop = drop.upper()
    if len(drop) != 1 or drop not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        raise ValueError(f"drop must be one A-Z letter, got {drop!r}")
    if tail_fill not in TAIL_FILL_ORDERS:
        raise ValueError(f"unknown tail_fill: {tail_fill!r}")
    if merge_direction not in {"backward", "forward"}:
        raise ValueError(f"unknown merge_direction: {merge_direction!r}")
    if merge_direction == "backward":
        merge_into = chr(ord(drop) - 1) if drop != "A" else "B"
    else:
        merge_into = chr(ord(drop) + 1) if drop != "Z" else "Y"
    s = re.sub(r"[^A-Za-z]", "", seed).upper().replace(drop, merge_into)
    s = "".join(dict.fromkeys(s))
    rest = "".join(ch for ch in TAIL_FILL_ORDERS[tail_fill] if ch != drop)
    for ch in rest:
        if ch not in s:
            s += ch
    return s[:25]


def build_board_9ary(alphabet25, e1, e2, topology="top_first"):
    """`topology` governs where in the 25-symbol alphabet the top-row (7 singles) vs
    the two escape-led rows (9 each) sit. "top_first" mirrors the validated 3.2.2
    layout ([tops][e1-row][e2-row]); "escapes_first" is the untested reversal
    ([e1-row][e2-row][tops])."""
    if len(alphabet25) != 25:
        raise ValueError(f"alphabet25 must contain 25 symbols, got {len(alphabet25)}")
    if e1 == e2 or e1 not in NINE_SYMS or e2 not in NINE_SYMS:
        raise ValueError(f"escapes must be distinct a-i symbols, got {e1!r}, {e2!r}")
    if topology not in {"top_first", "escapes_first"}:
        raise ValueError(f"unknown topology: {topology!r}")
    tops = [c for c in NINE_SYMS if c not in (e1, e2)]
    bd = {}
    if topology == "top_first":
        top_off, e1_off, e2_off = 0, 7, 16
    else:
        e1_off, e2_off, top_off = 0, 9, 18
    for k, c in enumerate(tops):
        bd[c] = alphabet25[top_off + k]
    for k, c2 in enumerate(NINE_SYMS):
        bd[e1 + c2] = alphabet25[e1_off + k]
    for k, c2 in enumerate(NINE_SYMS):
        bd[e2 + c2] = alphabet25[e2_off + k]
    return bd


def _key_order(key):
    return [i for i, _ in sorted(enumerate(key), key=lambda x: (x[1], x[0]))]


def keyed_columnar(s, key, direction):
    """Classic keyed columnar transposition, ported from the community fork's
    columnar.py -- a real lead from chat line 31761: 'matrixsumlist' (13 letters)
    keys dbbi (91 = 7x13 exactly) and 'lastwordsbeforearchichoicethispassword'
    (38 letters) keys faed (570 = 15x38 exactly). The fork only tested this under
    a direct digit->ASCII interpretation, never combined with the validated
    {b,e}/pad25 checkerboard model -- that combination is what's new here."""
    if not key:
        raise ValueError("key must not be empty")
    if direction not in {"encrypt", "decrypt"}:
        raise ValueError(f"unknown keyed-columnar direction: {direction!r}")
    w = len(key)
    order = _key_order(key)
    if direction == "encrypt":
        rows = [s[i:i + w] for i in range(0, len(s), w)]
        out = []
        for col in order:
            for r in rows:
                if col < len(r):
                    out.append(r[col])
        return "".join(out)
    n = len(s)
    nrows = -(-n // w)
    rem = n % w
    col_len = {c: (nrows if (c < (rem if rem else w)) else nrows - 1) for c in range(w)} if rem else {c: nrows for c in range(w)}
    cols = {}
    pos = 0
    for c in order:
        length = col_len[c]
        cols[c] = s[pos:pos + length]
        pos += length
    out = []
    for r in range(nrows):
        for c in range(w):
            if r < len(cols[c]):
                out.append(cols[c][r])
    return "".join(out)


KEYCOL_DBBI = "matrixsumlist"
KEYCOL_FAED = "lastwordsbeforearchichoicethispassword"


_MIRROR9 = str.maketrans("abcdefghi", "ihgfedcba")


def transpose(s, kind):
    """Simple transposition/keystream candidates -- unknown #4 from the original
    4-unknowns analysis ("a transposition/over-encryption keystream layered on
    top"), never actually tested under the corrected {b,e}/pad25 model. `kind`:
    identity, reverse, 'colN' (deinterleave into N columns) for N in 2..6,
    'keycol:<key>:<encrypt|decrypt>' for the keyed columnar transposition,
    'halfswap' (swap the first/second halves -- the two "eyes" of a yin-yang
    trading places), or 'mirror9' (complement each a-i symbol around e: a<->i,
    b<->h, c<->g, d<->f, e fixed -- the "dot of the other color inside each
    half" idea, applied to the symbol alphabet itself rather than position)."""
    if kind == "identity":
        return s
    if kind == "reverse":
        return s[::-1]
    if kind == "halfswap":
        mid = len(s) // 2
        return s[mid:] + s[:mid]
    if kind == "mirror9":
        return s.translate(_MIRROR9)
    if kind.startswith("keycol:"):
        try:
            _, key, direction = kind.split(":")
        except ValueError as exc:
            raise ValueError(f"invalid keyed-columnar transform: {kind!r}") from exc
        return keyed_columnar(s, key, direction)
    if kind.startswith("col"):
        try:
            period = int(kind[3:])
        except ValueError as exc:
            raise ValueError(f"invalid column transform: {kind!r}") from exc
        if period < 1:
            raise ValueError(f"column period must be positive, got {period}")
        return "".join(s[i::period] for i in range(period))
    raise ValueError(f"unknown transform: {kind!r}")


TRANSFORM_KINDS = ["identity", "reverse", "col2", "col3", "col4", "col5", "col6",
                   "halfswap", "mirror9"]
KEYCOL_TRANSFORM_KINDS = [
    f"keycol:{KEYCOL_DBBI}:encrypt", f"keycol:{KEYCOL_DBBI}:decrypt",
    f"keycol:{KEYCOL_DBBI[::-1]}:encrypt", f"keycol:{KEYCOL_DBBI[::-1]}:decrypt",
    f"keycol:{KEYCOL_FAED}:encrypt", f"keycol:{KEYCOL_FAED}:decrypt",
    f"keycol:{KEYCOL_FAED[::-1]}:encrypt", f"keycol:{KEYCOL_FAED[::-1]}:decrypt",
]


def keyword_to_seed(keyword, base):
    """keyword -> list of digits mod `base` (A=1..Z=26, wrapped) -- the short numeric
    seed a VIC-style chain-addition keystream is grown from."""
    letters = re.sub(r"[^A-Za-z]", "", keyword).upper()
    return [(ord(c) - 64) % base for c in letters]


def chain_add(seed, length, base):
    """VIC-cipher-style lagged digit addition: extends a short seed via
    d[i] = (d[i-1]+d[i-2]) % base. This is the real VIC cipher's mechanism for
    turning a short keyword-derived seed into an arbitrarily long masking
    keystream (a deterministic, non-carrying analogue of a one-time pad) --
    see doc/GSMG_PUZZLE.md's "Plan A" section. Returns None if the seed is too
    short to bootstrap the recurrence."""
    if len(seed) < 2:
        return None
    d = list(seed)
    while len(d) < length:
        d.append((d[-1] + d[-2]) % base)
    return d[:length]


_NINE_IDX = {c: i for i, c in enumerate(NINE_SYMS)}


def dechain_9ary(s, seed, sign=-1):
    """Add/subtract (per `sign`) a mod-9 chain-addition keystream from a 9-symbol
    ciphertext string, symbol-wise -- tests whether dbbi/faed carry a VIC-style
    additive keystream *underneath* the checkerboard (applied to the raw a-i
    stream before board decode), independent of guessing the board's own
    alphabet keyword."""
    ks = chain_add(seed, len(s), 9)
    if ks is None:
        return None
    return "".join(NINE_SYMS[(_NINE_IDX[ch] + sign * k) % 9] for ch, k in zip(s, ks))


def dechain_letters(s, seed, sign=-1):
    """Same idea applied to already-decoded letters (mod 26) instead of the raw
    9-symbol ciphertext -- tests the keystream as a layer *on top of* the
    checkerboard decode rather than underneath it."""
    ks = chain_add(seed, len(s), 26)
    if ks is None:
        return None
    out = []
    for ch, k in zip(s, ks):
        if ch.isalpha():
            out.append(chr(65 + (ord(ch.upper()) - 65 + sign * k) % 26))
        else:
            out.append(ch)
    return "".join(out)


def _autokey_digits(cipher_digits, seed, base, mode, sign):
    """Autokey keystream: a short priming `seed` extended by feeding the stream's
    own past values back in as the key (self-referential), unlike chain_add's
    fixed Fibonacci-style recursion from a static seed. `mode="ciphertext"` extends
    the key using past *ciphertext* digits (computable upfront, order-independent);
    `mode="plaintext"` extends using past *recovered* digits (must be computed
    sequentially, since each step's key depends on the previous step's output)."""
    if mode not in {"ciphertext", "plaintext"}:
        raise ValueError(f"unknown autokey mode: {mode!r}")
    n = len(cipher_digits)
    if mode == "ciphertext":
        k_stream = list(seed) + list(cipher_digits[:max(0, n - len(seed))])
        return [(cipher_digits[i] + sign * k_stream[i]) % base for i in range(n)]
    out, k_stream = [], list(seed)
    for i in range(n):
        v = (cipher_digits[i] + sign * k_stream[i]) % base
        out.append(v)
        k_stream.append(v)
    return out


def autokey_dechain_9ary(s, seed, mode="ciphertext", sign=-1):
    """Autokey applied to the raw 9-symbol ciphertext (mod 9), before checkerboard
    decode -- the pre-decode analogue of dechain_9ary()."""
    if len(seed) < 1:
        return None
    digits = [_NINE_IDX[ch] for ch in s]
    out = _autokey_digits(digits, seed, 9, mode, sign)
    return "".join(NINE_SYMS[d] for d in out)


def autokey_dechain_letters(s, seed, mode="ciphertext", sign=-1):
    """Autokey applied to already-decoded letters (mod 26), after checkerboard
    decode -- the post-decode analogue of dechain_letters(). Assumes `s` is pure
    A-Z (true for decode_9ary output once the "?" check has already passed)."""
    if len(seed) < 1:
        return None
    digits = [ord(ch) - 65 for ch in s]
    out = _autokey_digits(digits, seed, 26, mode, sign)
    return "".join(chr(65 + d) for d in out)


def decode_9ary(s, alphabet25, e1, e2, topology="top_first"):
    bd = build_board_9ary(alphabet25, e1, e2, topology)
    out = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in (e1, e2):
            if i + 1 >= len(s):
                out.append("?")
                break
            out.append(bd.get(s[i:i + 2], "?"))
            i += 2
        else:
            out.append(bd.get(ch, "?"))
            i += 1
    return "".join(out)


def answer_forms(s):
    """Normalization forms tried against the AES oracle, matching joint_attack.py."""
    a = re.sub(r"[^A-Za-z]", "", s)
    return {s, s.upper(), s.lower(), a, a.upper(), a.lower()}


def _load_blob(b64_str):
    raw = base64.b64decode("".join(b64_str.split()))
    assert raw[:8] == b"Salted__", "blob missing OpenSSL Salted__ header"
    return raw[8:16], raw[16:]


BLOBS = {
    "SALPH": _load_blob(SALPHASEION_BLOB_B64),
    "COSMIC": _load_blob(COSMIC_BLOB_B64),
    # Third target, added 2026-07-24 -- see data.P32_TRAILING_BLOB_B64 for full
    # provenance (confirmed real via the official community repo README + an
    # actively-maintained fork's detailed documentation, not previously
    # tracked in this project). Small cost to add as a peer default (one more
    # 80-byte blob in the same fast inner loop every sweep already runs) --
    # unlike the cipher/KDF variant expansion, this isn't the expensive axis.
    "P32TRAILING": _load_blob(P32_TRAILING_BLOB_B64),
}

# "urlblob", added 2026-07-24 -- see data.URLBLOB_B64 for full provenance,
# including this project's own independent re-verification directly against
# the live Wayback CDX API (not just the HosterjackAGV fork's docs), which
# also caught and corrected a truncated-capture/timestamp error in that
# fork's own citation. Deliberately kept OUT of the default BLOBS: unlike
# SALPH/COSMIC/P32TRAILING, no official-README or solved-plaintext source
# corroborates this blob as a genuine puzzle artifact -- the fork that
# surfaced it calls it "orphaned" and reports no tested key decrypts it.
# Sweep scripts that want to include it pass
# `blobs={**BLOBS, **QUARANTINED_BLOBS}` (or an equivalent opt-in flag)
# explicitly, rather than it silently joining every default run.
QUARANTINED_BLOBS = {
    "URLBLOB": _load_blob(URLBLOB_B64),
}


def evp_bytes_to_key(passwd: bytes, salt: bytes, digest_name="sha256", key_len=32, iv_len=16):
    """OpenSSL legacy EVP_BytesToKey. `digest_name` and `key_len` (AES-256 vs AES-128)
    were never independently confirmed for these specific blobs -- there's no known
    passphrase for either one to validate against (unlike the checkerboard cipher's
    VALIDATION_NUM crib). OpenSSL `enc` changed its default digest from MD5 to SHA-256
    in OpenSSL 1.1.0, before this puzzle's 2019 launch. See doc/GSMG_PUZZLE.md."""
    digest = {"md5": hashlib.md5, "sha1": hashlib.sha1, "sha256": hashlib.sha256}[digest_name]
    d = b""
    prev = b""
    while len(d) < key_len + iv_len:
        prev = digest(prev + passwd + salt).digest()
        d += prev
    return d[:key_len], d[key_len:key_len + iv_len]


def pbkdf2_bytes_to_key(passwd: bytes, salt: bytes, iterations: int, digest_name: str,
                         key_len: int, iv_len: int):
    """OpenSSL's `-pbkdf2` KDF (added 1.1.0, mandatory without `-iter` in 3.0+): a
    single PBKDF2-HMAC-<digest> call producing key_len+iv_len bytes, split the same
    way the legacy digest-chain derivation splits its output. Never previously
    implemented in this oracle -- `Salted__` identifies the OpenSSL container, not
    which KDF/cipher produced it, so a correct passphrase against the wrong KDF
    would silently fail every prior sweep (see path 1, doc/GSMG_PUZZLE.md 2026-07-24
    review)."""
    d = hashlib.pbkdf2_hmac(digest_name, passwd, salt, iterations, dklen=key_len + iv_len)
    return d[:key_len], d[key_len:key_len + iv_len]


# (digest, key_len) combos to try -- key_len=32/16 is AES-256/AES-128-CBC (iv_len always
# 16). Ordered by prior likelihood: sha256+256 was this project's original assumption
# and the OpenSSL `enc` default from 1.1.0 onward; md5+256 covers older OpenSSL.
#
# Deliberately AES-CBC-only, matching the original joint_attack.py assumption --
# kept as the unchanged default so every existing sweep script's cost/behavior is
# unaffected. See EXTENDED_CIPHER_VARIANTS below for the broadened, opt-in set.
KDF_VARIANTS = [
    ("sha256", 32), ("md5", 32), ("sha1", 32),
    ("sha256", 16), ("md5", 16), ("sha1", 16),
]

# cipher name -> (cryptography class, block/IV size in bytes). CBC mode's IV size
# always equals the cipher's block size, so one table covers both.
CIPHER_CLASSES = {"aes": algorithms.AES, "3des": algorithms.TripleDES}
CIPHER_BLOCK_SIZES = {"aes": 16, "3des": 8}

# Broadened cipher/KDF coverage beyond this project's original AES+legacy-KDF-only
# assumption -- found 2026-07-24 to be the strongest genuinely untested premise
# underlying every prior sweep's "0 hits" result (a correct passphrase against the
# wrong cipher/KDF looks identical to a wrong passphrase). Opt-in only: NOT merged
# into KDF_VARIANTS, so this doesn't silently multiply the cost of every existing
# sweep script that still imports the plain default.
#
#   - AES-192-CBC: the one AES key size KDF_VARIANTS omits.
#   - 3DES-CBC at all three `cryptography`-supported key sizes (24/16/8 bytes ==
#     3-key / 2-key / single-key-EDE "3DES") -- OpenSSL's `enc` supports
#     des-ede3-cbc/des-ede-cbc/des-cbc under the same Salted__ container.
#   - PBKDF2-HMAC-SHA256, bounded to OpenSSL's own fixed default of 10000
#     iterations (unchanged since `-pbkdf2` was introduced) rather than an
#     open-ended iteration-count sweep -- if a non-default `-iter` was used there
#     is no principled way to bound that search, so it stays out of scope here.
EXTENDED_CIPHER_VARIANTS = [
    ("legacy", digest, cipher, key_len)
    for digest in ("sha256", "md5", "sha1")
    for cipher, key_len in (
        ("aes", 24),
        ("3des", 24), ("3des", 16), ("3des", 8),
    )
] + [
    ("pbkdf2", ("sha256", 10000), cipher, key_len)
    for cipher, key_len in (
        ("aes", 32), ("aes", 16), ("aes", 24),
        ("3des", 24), ("3des", 16), ("3des", 8),
    )
]

# Cipher *mode* coverage, added 2026-07-26 -- every sweep to this point
# (KDF_VARIANTS, EXTENDED_CIPHER_VARIANTS, and the AES Key Wrap oracle) only
# ever tries AES-CBC. `Salted__` identifies the OpenSSL legacy container, not
# the mode: `openssl enc -aes-256-cfb`/`-ofb`/`-ctr` produce the exact same
# header, salt, and EVP_BytesToKey/PBKDF2 derivation, differing only in how
# the keystream is generated -- a correct passphrase under one of these modes
# would look identical to a wrong passphrase under every prior sweep, the
# same blind spot that motivated the Key Wrap addition (Phase 26). Scoped to
# AES only (matching KDF_VARIANTS' original scope, not EXTENDED_CIPHER_
# VARIANTS' 3DES/AES-192 breadth) x legacy sha256/md5/sha1 x {128,192,256}-bit
# keys, plus PBKDF2-HMAC-SHA256 at OpenSSL's fixed default of 10000
# iterations -- the same principled bound EXTENDED_CIPHER_VARIANTS already
# uses for PBKDF2, for the same reason (an open-ended -iter search has no
# natural stopping point).
STREAM_CIPHER_VARIANTS = [
    ("legacy", digest, key_len, stream_mode)
    for digest in ("sha256", "md5", "sha1")
    for key_len in (32, 24, 16)
    for stream_mode in ("cfb", "ofb", "ctr")
] + [
    ("pbkdf2", ("sha256", 10000), key_len, stream_mode)
    for key_len in (32, 24, 16)
    for stream_mode in ("cfb", "ofb", "ctr")
]

STREAM_MODE_CLASSES = {"cfb": modes.CFB, "ofb": modes.OFB, "ctr": modes.CTR}

# AES-ECB is kept separate from both CBC and the stream-like modes. OpenSSL
# `enc` still emits the same Salted__ envelope and derives only the key
# (there is no IV). It is most relevant to the 80-byte SALPH/P32TRAILING
# targets because a 64-byte plaintext receives one complete 16-byte PKCS7
# padding block, giving a strong structural oracle even when the plaintext is
# binary key material rather than readable text.
ECB_CIPHER_VARIANTS = [
    ("legacy", digest, key_len)
    for digest in ("sha256", "md5", "sha1")
    for key_len in (32, 24, 16)
] + [
    ("pbkdf2", ("sha256", 10000), key_len)
    for key_len in (32, 24, 16)
]


def _normalize_variant(v):
    """Accept both the original (digest_name, key_len) AES/legacy-KDF shorthand
    every existing sweep script's KDF_VARIANTS-shaped argument still uses, and the
    richer (kdf_kind, kdf_param, cipher, key_len) form EXTENDED_CIPHER_VARIANTS
    uses -- so broadening the oracle can't silently change old call sites'
    behavior."""
    if len(v) == 2:
        digest_name, key_len = v
        return "legacy", digest_name, "aes", key_len
    return v


def _kdf_label(kdf_kind, kdf_param, cipher):
    if kdf_kind == "legacy":
        label = kdf_param
    else:
        digest_name, iterations = kdf_param
        label = f"pbkdf2-{digest_name}-i{iterations}"
    return label if cipher == "aes" else f"{label}+{cipher}"


# ── AES Key Wrap (RFC 3394 / RFC 5649), added 2026-07-24 -- a genuinely
# different cipher *mode* hypothesis, distinct from the CBC-only assumption
# every prior sweep (including EXTENDED_CIPHER_VARIANTS) still makes. Surfaced
# independently by an external fork's own attempt catalog (see FINDINGS.md
# Phase 25) flagging "-id-aes256-wrap-pad" as untested for the same blob this
# project calls P32TRAILING. Reuses the *same* Salted__/salt/body parsing
# already established for BLOBS -- only the transform applied to the body
# changes (unwrap instead of CBC-decrypt), and the KEK is derived from a
# candidate passphrase through the exact same EVP_BytesToKey/PBKDF2 machinery.
# Strict RFC mode uses the standard AIV and derives only the KEK; OpenSSL
# `enc` instead derives a custom 8-byte/4-byte wrap IV after the KEK.
#
# RFC 3394 (aes_key_unwrap) requires ciphertext length a multiple of 8 bytes,
# >=24 (>=2 wrapped 64-bit semiblocks plus the 64-bit integrity block). RFC
# 5649 (aes_key_unwrap_with_padding, the "-wrap-pad" variant) relaxes the
# unwrapped-length-must-be-a-multiple-of-8 requirement but keeps the same
# wrapped-ciphertext alignment/minimum. Both use a fixed integrity-check
# constant (not a guessable value) baked into the algorithm itself, so unlike
# the CBC PKCS7-padding heuristic (~1/255 false-accept prior), a successful
# unwrap here is a near-zero-false-accept signal on its own -- `cryptography`
# raises InvalidUnwrap on any integrity-check mismatch.
KEY_WRAP_KEY_LENS = (16, 24, 32)  # AES-128/192/256 wrapping-key sizes.

KEY_WRAP_KDF_VARIANTS = [
    ("legacy", digest, key_len)
    for digest in ("sha256", "md5", "sha1")
    for key_len in KEY_WRAP_KEY_LENS
] + [
    ("pbkdf2", ("sha256", 10000), key_len)
    for key_len in KEY_WRAP_KEY_LENS
]


def derive_kek(kdf_kind, kdf_param, salt: bytes, passwd: bytes, key_len: int) -> bytes:
    """Derive only the KEK, for strict RFC default-AIV key wrap."""
    if kdf_kind == "legacy":
        key, _ = evp_bytes_to_key(passwd, salt, kdf_param, key_len, 0)
    else:
        digest_name, iterations = kdf_param
        key, _ = pbkdf2_bytes_to_key(passwd, salt, iterations, digest_name, key_len, 0)
    return key


def derive_wrap_material(kdf_kind, kdf_param, salt: bytes, passwd: bytes,
                         key_len: int, iv_len: int):
    """Derive the KEK plus OpenSSL `enc`'s custom wrap IV.

    Although RFC 3394/5649 define default integrity values, OpenSSL's
    `enc -id-aes*-wrap[-pad]` treats them as cipher IVs. Its password KDF
    therefore derives 8 extra bytes for RFC 3394 or 4 for RFC 5649 and uses
    those bytes instead of the RFC defaults. Testing only `iv_len=0` does not
    reproduce the command-line mode that motivated this hypothesis.
    """
    if kdf_kind == "legacy":
        return evp_bytes_to_key(passwd, salt, kdf_param, key_len, iv_len)
    digest_name, iterations = kdf_param
    return pbkdf2_bytes_to_key(
        passwd, salt, iterations, digest_name, key_len, iv_len,
    )


def _aes_key_unwrap_core(kek: bytes, wrapped: bytes):
    chunks = [wrapped[i:i + 8] for i in range(0, len(wrapped), 8)]
    a = chunks.pop(0)
    count = len(chunks)
    decryptor = Cipher(algorithms.AES(kek), modes.ECB()).decryptor()
    for round_index in reversed(range(6)):
        for chunk_index in reversed(range(count)):
            counter = count * round_index + chunk_index + 1
            block = (
                (int.from_bytes(a, "big") ^ counter).to_bytes(8, "big")
                + chunks[chunk_index]
            )
            decrypted = decryptor.update(block)
            a = decrypted[:8]
            chunks[chunk_index] = decrypted[8:]
    decryptor.finalize()
    return a, b"".join(chunks)


def _aes_key_unwrap_custom(kek: bytes, wrapped: bytes, expected_iv: bytes):
    if len(wrapped) < 24 or len(wrapped) % 8:
        raise InvalidUnwrap
    a, plaintext = _aes_key_unwrap_core(kek, wrapped)
    if not hmac.compare_digest(a, expected_iv):
        raise InvalidUnwrap
    return plaintext


def _aes_key_unwrap_with_padding_custom(kek: bytes, wrapped: bytes,
                                        expected_iv_prefix: bytes):
    if len(wrapped) < 16 or len(wrapped) % 8:
        raise InvalidUnwrap
    if len(wrapped) == 16:
        decryptor = Cipher(algorithms.AES(kek), modes.ECB()).decryptor()
        decrypted = decryptor.update(wrapped) + decryptor.finalize()
        a, plaintext = decrypted[:8], decrypted[8:]
        semiblocks = 1
    else:
        a, plaintext = _aes_key_unwrap_core(kek, wrapped)
        semiblocks = len(plaintext) // 8
    message_len = int.from_bytes(a[4:], "big")
    padding_len = 8 * semiblocks - message_len
    if (
        not hmac.compare_digest(a[:4], expected_iv_prefix)
        or not 8 * (semiblocks - 1) < message_len <= 8 * semiblocks
        or (
            padding_len
            and not hmac.compare_digest(
                plaintext[-padding_len:], bytes(padding_len),
            )
        )
    ):
        raise InvalidUnwrap
    return plaintext if padding_len == 0 else plaintext[:-padding_len]


def aes_keywrap_try_open_bytes(passwd: bytes, kdf_variants=None, blobs=None):
    """Try `passwd` as a KEK-deriving passphrase against known blobs' bodies,
    treated as AES-Key-Wrapped (RFC 3394) or AES-Key-Wrapped-with-Padding
    (RFC 5649) ciphertext rather than AES-CBC ciphertext. For each algorithm,
    test both the RFC default integrity value and OpenSSL `enc`'s password-
    derived custom IV behavior.

    Returns a list of (tag, wrap_kind, kdf_label, key_len, unwrapped_bytes)
    tuples -- every successful unwrap, since (unlike the printable-ratio
    gate) a clean unwrap is already a strong signal and there's no plaintext
    to rank by printability yet (see `raw_key_try_open` for what happens
    next: the unwrapped bytes are key material, not necessarily plaintext)."""
    selected_kdfs = KEY_WRAP_KDF_VARIANTS if kdf_variants is None else kdf_variants
    selected_blobs = BLOBS if blobs is None else blobs
    hits = []
    for kdf_kind, kdf_param, key_len in selected_kdfs:
        kdf_label = _kdf_label(kdf_kind, kdf_param, "aes")
        for tag, (salt, ct) in selected_blobs.items():
            if len(ct) % 8 != 0 or len(ct) < 16:
                continue
            kek, wrap_iv = derive_wrap_material(
                kdf_kind, kdf_param, salt, passwd, key_len, 8,
            )
            if len(ct) >= 24:
                try:
                    unwrapped = aes_key_unwrap(kek, ct)
                except InvalidUnwrap:
                    unwrapped = None
                if unwrapped is not None:
                    hits.append((
                        tag, "rfc3394-default", kdf_label, key_len, unwrapped,
                    ))
                try:
                    unwrapped = _aes_key_unwrap_custom(kek, ct, wrap_iv)
                except InvalidUnwrap:
                    unwrapped = None
                if unwrapped is not None:
                    hits.append((
                        tag, "rfc3394-openssl", kdf_label, key_len, unwrapped,
                    ))
            try:
                unwrapped_p = aes_key_unwrap_with_padding(kek, ct)
            except InvalidUnwrap:
                unwrapped_p = None
            if unwrapped_p is not None:
                hits.append((
                    tag, "rfc5649-default", kdf_label, key_len, unwrapped_p,
                ))
            try:
                unwrapped_p = _aes_key_unwrap_with_padding_custom(
                    kek, ct, wrap_iv[:4],
                )
            except InvalidUnwrap:
                unwrapped_p = None
            if unwrapped_p is not None:
                hits.append((
                    tag, "rfc5649-openssl", kdf_label, key_len, unwrapped_p,
                ))
    return hits


def aes_keywrap_try_open(keystr: str, kdf_variants=None, blobs=None):
    """Text wrapper around aes_keywrap_try_open_bytes, matching aes_try_open's API."""
    return aes_keywrap_try_open_bytes(keystr.encode(), kdf_variants, blobs)


# Key lengths a raw byte-string is valid as a *direct* cipher key for (as
# opposed to a passphrase run through EVP_BytesToKey/PBKDF2) -- the natural
# next step once AES Key Wrap unwrap succeeds: the task instructions are
# explicit that the unwrapped output should be "treated as key material
# first, not necessarily plaintext."
RAW_KEY_LENS = {"aes": (16, 24, 32), "3des": (8, 16, 24)}


def raw_key_try_open(key: bytes, blobs=None):
    """Try `key` directly as a cipher key (zero IV, no password-based
    derivation) against blob bodies -- the natural interpretation of AES-Key-
    Wrap-unwrapped output, which is raw key bytes rather than passphrase
    text. Tries AES if len(key) in RAW_KEY_LENS['aes'], 3DES if len(key) in
    RAW_KEY_LENS['3des'] (both apply for the 16/24-byte overlap). Same
    two-tier printable-ratio gate as aes_try_open_bytes."""
    selected_blobs = BLOBS if blobs is None else blobs
    hits = []
    for cipher, valid_lens in RAW_KEY_LENS.items():
        if len(key) not in valid_lens:
            continue
        block = CIPHER_BLOCK_SIZES[cipher]
        iv = bytes(block)
        for tag, (salt, ct) in selected_blobs.items():
            if len(ct) % block != 0 or not ct:
                continue
            decryptor = Cipher(CIPHER_CLASSES[cipher](key), modes.CBC(iv)).decryptor()
            try:
                pt = decryptor.update(ct) + decryptor.finalize()
            except Exception:
                continue
            pad = pt[-1]
            if 1 <= pad <= block and pt[-pad:] == bytes([pad]) * pad:
                body = pt[:-pad]
                if not body:
                    continue
                z = printable_z_score(body)
                if z >= PRINTABLE_Z_STRONG_THRESHOLD:
                    hits.append((tag, cipher, body, z))
                elif z >= PRINTABLE_Z_WEAK_THRESHOLD:
                    _log_candidate("weak", tag, key, body, z, "raw-key-zero-iv", cipher, len(key))
    return hits


def keystr_forms(form: str, newline_variants: bool = False):
    """Passphrase forms to try for a decoded/candidate answer: raw, single SHA-256
    hex digest, and double SHA-256 hex (hash of the hex digest) -- the last one
    added per the "sha256 ans too" reading of the trailing shabefanstoo fragment
    (ans = the calculator/REPL convention for "last computed result"; "too" =
    hash it again on top of whatever hashing already happened).

    `newline_variants`: also try each form with a trailing "\\n"/"\\r\\n" appended
    before use -- the "enter" reading of the abba-encoded word buried in the AES
    blob (an `echo "password" | sha256sum`-style terminal session includes the
    newline from pressing Enter; `echo -n` does not). Off by default since it
    triples the passphrase-form count for every candidate in every sweep."""
    bases = (form, form + "\n", form + "\r\n") if newline_variants else (form,)
    out = []
    for b in bases:
        h1 = hashlib.sha256(b.encode()).hexdigest()
        h2 = hashlib.sha256(h1.encode()).hexdigest()
        out.extend((b, h1, h2))
    return tuple(out)


# Bytes counted as "printable" for the oracle's plausibility gate: ASCII
# 32-126 plus tab/LF/CR. Under a wrong password the decrypted body is
# effectively uniform random bytes, so this set's own size sets the null-model
# baseline the gate is measured against, rather than an arbitrary fixed ratio.
PRINTABLE_BYTE_COUNT = 95 + 3  # 32-126 inclusive, plus {9, 10, 13}
PRINTABLE_P0 = PRINTABLE_BYTE_COUNT / 256

# Found 2026-07-23: the real, byte-for-byte-verified Phase 3.2 plaintext (see
# data.PHASE32_BLOB_B64) has a printable ratio of only ~0.598 -- it legitimately
# embeds a CP437/high-bit-set garbled sub-block as part of the puzzle's own
# multi-stage design. A flat ">0.85 printable" gate (this project's rule until
# this fix) would have silently rejected that exact correct decryption. Replaced
# with a null-model z-score: how many standard deviations the observed
# printable-byte count sits above the random-byte baseline (PRINTABLE_P0). This
# scales correctly with body length (a short body needs a much higher ratio
# than a long one to be equally surprising) instead of penalizing all lengths
# by the same fixed number.
PRINTABLE_Z_WEAK_THRESHOLD = 5.0  # logged as a weak candidate, NOT returned as
# a hit. ~2.9e-7 false-accept rate alone; combined with the ~1/255 valid-PKCS7-
# pad prior, compound false-accept is ~1e-9/attempt -- but at the true attempt
# volume of a large sweep (hundreds of millions once KDF variants/escape
# orders/keystring forms all multiply out), that rate alone still produces an
# occasional false positive at this exact boundary (confirmed 2026-07-24: the
# autokey faed backfill produced two, both z~5.03, both incoherent noise).
PRINTABLE_Z_STRONG_THRESHOLD = 8.0  # returned as a hit requiring inspection.
# Leaves the real Phase 3.2 vector (z~22) enormous margin while cutting the
# false-accept rate by ~9 orders of magnitude versus the weak threshold.

WEAK_CANDIDATE_LOG = Path(__file__).parent / "weak_candidates_log.txt"  # .txt
# so it's covered by the existing *.txt gitignore rule like other run output;
# content is JSON-per-line (jsonl). Append-only like other hit files in this
# project -- see FINDINGS.md's "append-only hit files" note before assuming a
# fresh run's absence of new lines means a fresh run found nothing.


def printable_z_score(body: bytes) -> float:
    n = len(body)
    if n == 0:
        return 0.0
    count = sum(1 for c in body if 32 <= c < 127 or c in (9, 10, 13))
    mean = n * PRINTABLE_P0
    std = math.sqrt(n * PRINTABLE_P0 * (1 - PRINTABLE_P0))
    return (count - mean) / std if std else 0.0


def longest_printable_run(body: bytes) -> int:
    return max((len(run) for run in re.findall(rb"[ -~]{2,}", body)), default=0)


def is_structural_binary_plaintext(cipher, block, pad, body):
    """Return whether a padded decrypt has the exact two-key binary shape.

    SALPH and P32TRAILING each contain 80 ciphertext bytes. Under AES, a
    64-byte plaintext is followed by a complete PKCS7 block consisting of
    sixteen 0x10 bytes. A wrong decrypt reproduces that exact final block with
    probability 256^-16 = 2^-128, so this is independently strong enough to
    retain even a completely non-printable body. The helper is intentionally
    narrow: it does not promote arbitrary valid padding or 3DES output.
    """
    return cipher == "aes" and block == 16 and pad == 16 and len(body) == 64


def _log_candidate(tier, tag, passwd, body, z, kdf_label, cipher, key_len):
    count = sum(1 for c in body if 32 <= c < 127 or c in (9, 10, 13))
    try:
        body.decode("utf-8")
        utf8_valid = True
    except UnicodeDecodeError:
        utf8_valid = False
    record = {
        "tier": tier,
        "blob": tag,
        "kdf": f"{kdf_label}/{cipher}{key_len * 8}",
        "passphrase_hex": passwd.hex(),
        "z_score": round(z, 4),
        "printable_ratio": round(count / len(body), 4) if body else 0.0,
        "printable_count": count,
        "plaintext_length": len(body),
        "longest_printable_run": longest_printable_run(body),
        "utf8_valid": utf8_valid,
        "plaintext_hex_preview": body[:200].hex(),
    }
    with open(WEAK_CANDIDATE_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


def aes_try_open_bytes(passwd: bytes, kdf_variants=None, blobs=None):
    """Try raw `passwd` bytes against known blobs (default: the two real
    unsolved targets, `BLOBS`), across all KDF-variant hypotheses. Two-tier
    plausibility gate on top of a valid PKCS7 pad:

      - z >= PRINTABLE_Z_STRONG_THRESHOLD (8): returned as a hit, same as
        before -- (tag, plaintext, kdf_label, key_len). For the default
        (legacy-KDF, AES-only) variants, kdf_label is still a bare digest name
        like "sha256", exactly as before. For EXTENDED_CIPHER_VARIANTS, it's a
        self-describing string (e.g. "pbkdf2-sha256-i10000+3des") so callers
        that already do `f"{kdf_label}/aes{key_len*8}"`-style formatting for
        the default variants are unaffected.
      - PRINTABLE_Z_WEAK_THRESHOLD (5) <= z < 8: logged to
        WEAK_CANDIDATE_LOG (z-score, printable ratio/count, plaintext length,
        longest printable run, UTF-8 validity) but NOT returned as a hit --
        this suppresses noisy alerts at the scale a large sweep produces
        without silently discarding borderline decryptions the way a single
        pass/fail threshold would.
      - z < 5: neither logged nor returned.

    Hits still require human inspection regardless of tier; padding and
    printability are strong filters, not cryptographic authentication.

    The byte-oriented entry point matters for hash-duality experiments: XOR/HMAC
    material may contain NUL or non-UTF-8 bytes and must reach EVP_BytesToKey
    unchanged.

    `blobs` lets the self-test check the known-positive Phase 3.2 vector
    end-to-end without adding an already-solved blob to every real sweep's
    per-candidate work (the default `BLOBS` stays just the two open targets).

    `kdf_variants` entries may be either the original (digest_name, key_len)
    AES/legacy-KDF shorthand or the richer (kdf_kind, kdf_param, cipher,
    key_len) form used by EXTENDED_CIPHER_VARIANTS -- see _normalize_variant()."""
    selected_kdfs = KDF_VARIANTS if kdf_variants is None else kdf_variants
    selected_blobs = BLOBS if blobs is None else blobs
    for variant in selected_kdfs:
        kdf_kind, kdf_param, cipher, key_len = _normalize_variant(variant)
        block = CIPHER_BLOCK_SIZES[cipher]
        for tag, (salt, ct) in selected_blobs.items():
            if len(ct) % block != 0 or not ct:
                continue
            if kdf_kind == "legacy":
                key, iv = evp_bytes_to_key(passwd, salt, kdf_param, key_len, block)
            else:
                digest_name, iterations = kdf_param
                key, iv = pbkdf2_bytes_to_key(passwd, salt, iterations, digest_name, key_len, block)
            decryptor = Cipher(CIPHER_CLASSES[cipher](key), modes.CBC(iv)).decryptor()
            try:
                pt = decryptor.update(ct) + decryptor.finalize()
            except Exception:
                continue
            pad = pt[-1]
            if 1 <= pad <= block and pt[-pad:] == bytes([pad]) * pad:
                body = pt[:-pad]
                if not body:
                    continue
                if is_structural_binary_plaintext(cipher, block, pad, body):
                    return tag, body, _kdf_label(kdf_kind, kdf_param, cipher), key_len
                z = printable_z_score(body)
                kdf_label = _kdf_label(kdf_kind, kdf_param, cipher)
                if z >= PRINTABLE_Z_STRONG_THRESHOLD:
                    return tag, body, kdf_label, key_len
                if z >= PRINTABLE_Z_WEAK_THRESHOLD:
                    _log_candidate("weak", tag, passwd, body, z, kdf_label, cipher, key_len)
    return None


def aes_try_open_stream_bytes(passwd: bytes, kdf_variants=None, blobs=None):
    """Like `aes_try_open_bytes`, but for CFB/OFB/CTR -- stream-like modes
    with no PKCS7 padding to validate first. Ciphertext and plaintext are the
    same length, so every candidate goes straight to `printable_z_score` on
    the full decrypted body.

    Losing the ~1/255 valid-pad pre-filter does not weaken the STRONG-tier
    gate: PRINTABLE_Z_STRONG_THRESHOLD (8) is already derived purely from
    printable-byte-count statistics, independent of padding (see its comment
    above) -- padding was always a cheap additional multiplier, not part of
    the statistical argument for that threshold. Reuses the same thresholds
    and weak-candidate logging as `aes_try_open_bytes` for consistency.

    `kdf_variants` entries are `STREAM_CIPHER_VARIANTS`-shaped 4-tuples:
    (kdf_kind, kdf_param, key_len, stream_mode)."""
    selected_kdfs = STREAM_CIPHER_VARIANTS if kdf_variants is None else kdf_variants
    selected_blobs = BLOBS if blobs is None else blobs
    for kdf_kind, kdf_param, key_len, stream_mode in selected_kdfs:
        block = 16  # AES only.
        mode_class = STREAM_MODE_CLASSES[stream_mode]
        for tag, (salt, ct) in selected_blobs.items():
            if not ct:
                continue
            if kdf_kind == "legacy":
                key, iv = evp_bytes_to_key(passwd, salt, kdf_param, key_len, block)
            else:
                digest_name, iterations = kdf_param
                key, iv = pbkdf2_bytes_to_key(passwd, salt, iterations, digest_name, key_len, block)
            decryptor = Cipher(algorithms.AES(key), mode_class(iv)).decryptor()
            try:
                body = decryptor.update(ct) + decryptor.finalize()
            except Exception:
                continue
            if not body:
                continue
            z = printable_z_score(body)
            kdf_label = f"{_kdf_label(kdf_kind, kdf_param, 'aes')}+{stream_mode}"
            if z >= PRINTABLE_Z_STRONG_THRESHOLD:
                return tag, body, kdf_label, key_len
            if z >= PRINTABLE_Z_WEAK_THRESHOLD:
                _log_candidate("weak", tag, passwd, body, z, kdf_label, "aes", key_len)
    return None


def aes_try_open_stream(keystr: str, kdf_variants=None, blobs=None):
    """Text wrapper around `aes_try_open_stream_bytes`."""
    return aes_try_open_stream_bytes(keystr.encode(), kdf_variants, blobs)


def aes_try_open_ecb_bytes(passwd: bytes, kdf_variants=None, blobs=None):
    """Try AES-ECB OpenSSL-container hypotheses.

    ECB has no IV, so its KDF derives only the AES key. Like the CBC oracle,
    readable plaintext passes the two-tier printable gate, while an exact
    64-byte body plus a complete 16-byte PKCS7 block is retained as structural
    binary key material.
    """
    selected_kdfs = ECB_CIPHER_VARIANTS if kdf_variants is None else kdf_variants
    selected_blobs = BLOBS if blobs is None else blobs
    for kdf_kind, kdf_param, key_len in selected_kdfs:
        for tag, (salt, ct) in selected_blobs.items():
            if not ct or len(ct) % 16:
                continue
            if kdf_kind == "legacy":
                key, _ = evp_bytes_to_key(passwd, salt, kdf_param, key_len, 0)
            else:
                digest_name, iterations = kdf_param
                key, _ = pbkdf2_bytes_to_key(
                    passwd, salt, iterations, digest_name, key_len, 0,
                )
            decryptor = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
            try:
                pt = decryptor.update(ct) + decryptor.finalize()
            except Exception:
                continue
            pad = pt[-1]
            if not 1 <= pad <= 16 or pt[-pad:] != bytes([pad]) * pad:
                continue
            body = pt[:-pad]
            if not body:
                continue
            kdf_label = f"{_kdf_label(kdf_kind, kdf_param, 'aes')}+ecb"
            if is_structural_binary_plaintext("aes", 16, pad, body):
                return tag, body, kdf_label, key_len
            z = printable_z_score(body)
            if z >= PRINTABLE_Z_STRONG_THRESHOLD:
                return tag, body, kdf_label, key_len
            if z >= PRINTABLE_Z_WEAK_THRESHOLD:
                _log_candidate(
                    "weak", tag, passwd, body, z, kdf_label, "aes", key_len,
                )
    return None


def aes_try_open_ecb(keystr: str, kdf_variants=None, blobs=None):
    """Text wrapper around `aes_try_open_ecb_bytes`."""
    return aes_try_open_ecb_bytes(keystr.encode(), kdf_variants, blobs)


def aes_try_open(keystr: str, kdf_variants=None, blobs=None):
    """Text wrapper around `aes_try_open_bytes`, preserving the original API."""
    return aes_try_open_bytes(keystr.encode(), kdf_variants, blobs)


def _self_test():
    val = decode(VALIDATION_NUM, ALPHA_322, *VALIDATION_ESCAPES)
    cleaned = val.replace(".", "")
    assert cleaned.startswith(VALIDATION_ANSWER_PREFIX), (
        f"cb_common self-test FAILED: decoder does not reproduce known 3.2.2 answer "
        f"(got {cleaned[:40]!r})"
    )

    # Known-positive AES/KDF ground truth (2026-07-23) -- the only real
    # plaintext available for this project's actual decrypt code path,
    # independent of the still-unsolved SALPH/COSMIC targets. Guards against
    # silently regressing the base64/Salted__/EVP_BytesToKey/AES-CBC/unpad
    # chain, and against the printable-ratio gate becoming too strict again
    # (this exact plaintext is the reason it isn't a flat 0.85 anymore).
    salt, ct = _load_blob(PHASE32_BLOB_B64)
    key, iv = evp_bytes_to_key(PHASE32_PASSWORD.encode(), salt, "sha256", 32)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    pt = decryptor.update(ct) + decryptor.finalize()
    pad = pt[-1]
    assert 1 <= pad <= 16 and pt[-pad:] == bytes([pad]) * pad, (
        "cb_common self-test FAILED: known-positive Phase 3.2 blob did not "
        "produce valid PKCS7 padding -- AES/KDF pipeline is broken"
    )
    body = pt[:-pad]
    assert body.startswith(PHASE32_PLAINTEXT_PREFIX.encode()), (
        f"cb_common self-test FAILED: known-positive Phase 3.2 blob decrypted "
        f"to unexpected content (got {body[:60]!r})"
    )
    z = printable_z_score(body)
    assert z > PRINTABLE_Z_STRONG_THRESHOLD, (
        f"cb_common self-test FAILED: known-positive Phase 3.2 plaintext "
        f"(z={z:.1f}) no longer clears PRINTABLE_Z_STRONG_THRESHOLD="
        f"{PRINTABLE_Z_STRONG_THRESHOLD} -- the oracle would reject a real hit"
    )
    phase32_blobs = {"PHASE32": (salt, ct)}
    assert aes_try_open_bytes(PHASE32_PASSWORD.encode(), blobs=phase32_blobs) is not None, (
        "cb_common self-test FAILED: aes_try_open_bytes() does not recognize "
        "the known-positive Phase 3.2 password as a hit end-to-end"
    )


def _self_test_extended_ciphers():
    """Known-positive synthetic vectors for every cipher/KDF combo added in
    EXTENDED_CIPHER_VARIANTS (path 1, 2026-07-24) -- there is no real puzzle blob
    to validate these against (unlike the Phase 3.2 AES-256 vector above), so this
    builds one directly for each combo and round-trips it end to end through the
    real aes_try_open_bytes() code path, guarding against the exact bug class a
    generalization like this invites: a block-size or IV-size mismatch (3DES is
    8 bytes, not AES's 16) silently producing garbage instead of an error."""
    passwd = b"correct horse battery staple"
    plaintext = b"the quick brown fox jumps over the lazy dog several times today"
    salt = b"01234567"
    checks = [
        ("legacy", "sha256", "aes", 24),
        ("legacy", "md5", "3des", 24),
        ("legacy", "sha1", "3des", 16),
        ("legacy", "sha256", "3des", 8),
        ("pbkdf2", ("sha256", 10000), "aes", 32),
        ("pbkdf2", ("sha256", 10000), "3des", 24),
    ]
    for kdf_kind, kdf_param, cipher, key_len in checks:
        variant = (kdf_kind, kdf_param, cipher, key_len)
        block = CIPHER_BLOCK_SIZES[cipher]
        if kdf_kind == "legacy":
            key, iv = evp_bytes_to_key(passwd, salt, kdf_param, key_len, block)
        else:
            digest_name, iterations = kdf_param
            key, iv = pbkdf2_bytes_to_key(passwd, salt, iterations, digest_name, key_len, block)
        pad_len = block - (len(plaintext) % block)
        padded = plaintext + bytes([pad_len]) * pad_len
        encryptor = Cipher(CIPHER_CLASSES[cipher](key), modes.CBC(iv)).encryptor()
        ct = encryptor.update(padded) + encryptor.finalize()
        result = aes_try_open_bytes(passwd, kdf_variants=[variant], blobs={"SYNTH": (salt, ct)})
        assert result is not None, (
            f"cb_common self-test FAILED: extended cipher variant {variant} did "
            f"not round-trip its own known-positive synthetic vector"
        )
        tag, body, kdf_label, returned_key_len = result
        assert body == plaintext, (
            f"cb_common self-test FAILED: extended cipher variant {variant} "
            f"decrypted to wrong content (got {body!r}, want {plaintext!r})"
        )
        assert returned_key_len == key_len, (
            f"cb_common self-test FAILED: extended cipher variant {variant} "
            f"returned key_len={returned_key_len}, expected {key_len}"
        )


def _self_test_stream_ciphers():
    """Known-positive synthetic vectors for every STREAM_CIPHER_VARIANTS
    combo (CFB/OFB/CTR, added 2026-07-26), plus a negative control -- since
    these modes have no padding to validate, a wrong passphrase producing a
    false STRONG-tier hit would be a much more serious silent bug here than
    for the padded CBC path."""
    passwd = b"correct horse battery staple"
    wrong_passwd = b"definitely the wrong passphrase"
    plaintext = b"the quick brown fox jumps over the lazy dog several times today"
    salt = b"01234567"
    for kdf_kind, kdf_param, key_len, stream_mode in STREAM_CIPHER_VARIANTS:
        variant = (kdf_kind, kdf_param, key_len, stream_mode)
        block = 16
        if kdf_kind == "legacy":
            key, iv = evp_bytes_to_key(passwd, salt, kdf_param, key_len, block)
        else:
            digest_name, iterations = kdf_param
            key, iv = pbkdf2_bytes_to_key(passwd, salt, iterations, digest_name, key_len, block)
        encryptor = Cipher(algorithms.AES(key), STREAM_MODE_CLASSES[stream_mode](iv)).encryptor()
        ct = encryptor.update(plaintext) + encryptor.finalize()

        result = aes_try_open_stream_bytes(
            passwd, kdf_variants=[variant], blobs={"SYNTH": (salt, ct)}
        )
        assert result is not None, (
            f"cb_common self-test FAILED: stream cipher variant {variant} did "
            f"not round-trip its own known-positive synthetic vector"
        )
        tag, body, kdf_label, returned_key_len = result
        assert body == plaintext, (
            f"cb_common self-test FAILED: stream cipher variant {variant} "
            f"decrypted to wrong content (got {body!r}, want {plaintext!r})"
        )
        assert returned_key_len == key_len, (
            f"cb_common self-test FAILED: stream cipher variant {variant} "
            f"returned key_len={returned_key_len}, expected {key_len}"
        )

        wrong_result = aes_try_open_stream_bytes(
            wrong_passwd, kdf_variants=[variant], blobs={"SYNTH": (salt, ct)}
        )
        assert wrong_result is None, (
            f"cb_common self-test FAILED: stream cipher variant {variant} "
            f"accepted a WRONG passphrase as a STRONG-tier hit"
        )


def _self_test_binary_plaintext_oracles():
    """Protect the non-printable 64-byte structural-hit path for CBC and ECB."""
    passwd = b"binary material passphrase"
    wrong_passwd = b"wrong binary material passphrase"
    salt = b"bin64key"
    body = bytes(range(64))
    assert printable_z_score(body) < PRINTABLE_Z_WEAK_THRESHOLD
    padded = body + bytes([16]) * 16

    key, iv = evp_bytes_to_key(passwd, salt, "sha256", 32, 16)
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    cbc_ct = encryptor.update(padded) + encryptor.finalize()
    cbc_result = aes_try_open_bytes(
        passwd,
        kdf_variants=[("sha256", 32)],
        blobs={"SYNTH_BINARY_CBC": (salt, cbc_ct)},
    )
    assert cbc_result is not None and cbc_result[1] == body, (
        "cb_common self-test FAILED: CBC oracle discarded exact non-printable "
        "64-byte plaintext with full-block PKCS7 padding"
    )
    assert aes_try_open_bytes(
        wrong_passwd,
        kdf_variants=[("sha256", 32)],
        blobs={"SYNTH_BINARY_CBC": (salt, cbc_ct)},
    ) is None

    key, _ = evp_bytes_to_key(passwd, salt, "sha256", 32, 0)
    encryptor = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    ecb_ct = encryptor.update(padded) + encryptor.finalize()
    ecb_variant = ("legacy", "sha256", 32)
    ecb_result = aes_try_open_ecb_bytes(
        passwd,
        kdf_variants=[ecb_variant],
        blobs={"SYNTH_BINARY_ECB": (salt, ecb_ct)},
    )
    assert ecb_result is not None and ecb_result[1] == body, (
        "cb_common self-test FAILED: ECB oracle discarded exact non-printable "
        "64-byte plaintext with full-block PKCS7 padding"
    )
    assert aes_try_open_ecb_bytes(
        wrong_passwd,
        kdf_variants=[ecb_variant],
        blobs={"SYNTH_BINARY_ECB": (salt, ecb_ct)},
    ) is None


def _self_test_keywrap():
    """Known-positive synthetic vectors for AES Key Wrap (RFC 3394) and AES Key
    Wrap with Padding (RFC 5649), one per KEY_WRAP_KDF_VARIANTS combo, plus a
    negative control confirming a wrong KEK is actually rejected (not just
    that the happy path works) -- the whole point of this cipher mode as an
    oracle is that its integrity check is much stronger than CBC's PKCS7-pad
    heuristic, so a false accept here would be a serious silent bug."""
    passwd = b"correct horse battery staple"
    wrong_passwd = b"definitely the wrong passphrase"
    salt = b"01234567"
    # Exactly 16 bytes (2 semiblocks) -- the minimum RFC 3394 accepts.
    key_material_3394 = b"0123456789ABCDEF"
    # Deliberately NOT a multiple of 8 -- only RFC 5649 (padded) can wrap this.
    key_material_5649 = b"unwrapped output is key material, not plaintext"

    for kdf_kind, kdf_param, key_len in KEY_WRAP_KDF_VARIANTS:
        variant = (kdf_kind, kdf_param, key_len)
        kek = derive_kek(kdf_kind, kdf_param, salt, passwd, key_len)
        wrong_kek = derive_kek(kdf_kind, kdf_param, salt, wrong_passwd, key_len)
        assert kek != wrong_kek, (
            f"cb_common self-test FAILED: key-wrap variant {variant} derived "
            f"identical KEKs for two different passphrases"
        )

        wrapped_3394 = aes_key_wrap(kek, key_material_3394)
        hits = aes_keywrap_try_open_bytes(
            passwd, kdf_variants=[variant], blobs={"SYNTH3394": (salt, wrapped_3394)},
        )
        assert any(
            h[1] == "rfc3394-default" and h[4] == key_material_3394
            for h in hits
        ), (
            f"cb_common self-test FAILED: key-wrap variant {variant} did not "
            f"round-trip its own RFC 3394 known-positive synthetic vector"
        )
        # Negative control: the wrong KEK must NOT unwrap this ciphertext.
        wrong_hits = aes_keywrap_try_open_bytes(
            wrong_passwd, kdf_variants=[variant], blobs={"SYNTH3394": (salt, wrapped_3394)},
        )
        assert not any(h[1].startswith("rfc3394") for h in wrong_hits), (
            f"cb_common self-test FAILED: key-wrap variant {variant} accepted "
            f"a WRONG passphrase's KEK for RFC 3394 unwrap -- integrity check "
            f"is not actually discriminating"
        )

        wrapped_5649 = aes_key_wrap_with_padding(kek, key_material_5649)
        hits = aes_keywrap_try_open_bytes(
            passwd, kdf_variants=[variant], blobs={"SYNTH5649": (salt, wrapped_5649)},
        )
        assert any(
            h[1] == "rfc5649-default" and h[4] == key_material_5649
            for h in hits
        ), (
            f"cb_common self-test FAILED: key-wrap variant {variant} did not "
            f"round-trip its own RFC 5649 known-positive synthetic vector"
        )
        wrong_hits = aes_keywrap_try_open_bytes(
            wrong_passwd, kdf_variants=[variant], blobs={"SYNTH5649": (salt, wrapped_5649)},
        )
        assert not any(h[1].startswith("rfc5649") for h in wrong_hits), (
            f"cb_common self-test FAILED: key-wrap variant {variant} accepted "
            f"a WRONG passphrase's KEK for RFC 5649 unwrap -- integrity check "
            f"is not actually discriminating"
        )

    # Independent OpenSSL 3.0.13 CLI vectors. These fixed ciphertexts were
    # generated with:
    #   openssl enc -id-aes256-wrap[-pad] -e -S 0123456789abcdef
    #       {-md sha256|-pbkdf2} -pass pass:keywrap-openssl-vector
    # They validate the password-derived custom-IV semantics that the strict
    # RFC helpers above do not exercise.
    openssl_passwd = b"keywrap-openssl-vector"
    openssl_salt = bytes.fromhex("0123456789abcdef")
    openssl_plaintext = b"0123456789ABCDEF"
    openssl_vectors = [
        (
            ("legacy", "sha256", 32),
            "rfc3394-openssl",
            "52ec3d0416d3e6f37e8bc022ec9a459c048212337217b848",
        ),
        (
            ("legacy", "sha256", 32),
            "rfc5649-openssl",
            "ab05a99b40dd75c228448a73128da43cc7c640e2a0271be7",
        ),
        (
            ("pbkdf2", ("sha256", 10000), 32),
            "rfc3394-openssl",
            "e4302b5fb2a34d8d58c6e715f0d74f44ce0592fc4df25473",
        ),
        (
            ("pbkdf2", ("sha256", 10000), 32),
            "rfc5649-openssl",
            "94d8d611604e2f9c2c397edd3630572d2f5f565dc37949d1",
        ),
    ]
    for variant, wrap_kind, ciphertext_hex in openssl_vectors:
        hits = aes_keywrap_try_open_bytes(
            openssl_passwd,
            kdf_variants=[variant],
            blobs={"OPENSSL": (openssl_salt, bytes.fromhex(ciphertext_hex))},
        )
        assert any(
            h[1] == wrap_kind and h[4] == openssl_plaintext for h in hits
        ), (
            "cb_common self-test FAILED: independent OpenSSL CLI vector "
            f"{wrap_kind}/{variant} was not recovered"
        )

    # raw_key_try_open(): confirm unwrapped output is correctly usable as a
    # direct cipher key (zero IV) against a synthetic AES-CBC blob, distinct
    # from the password-based EVP_BytesToKey path raw_key_try_open bypasses.
    raw_key = b"0123456789ABCDEF"  # 16 bytes -- valid as a direct AES-128 key.
    plaintext = b"treat unwrapped output as key material first, not plaintext"
    block = 16
    pad_len = block - (len(plaintext) % block)
    padded = plaintext + bytes([pad_len]) * pad_len
    encryptor = Cipher(algorithms.AES(raw_key), modes.CBC(bytes(block))).encryptor()
    ct = encryptor.update(padded) + encryptor.finalize()
    hits = raw_key_try_open(raw_key, blobs={"SYNTHRAW": (b"01234567", ct)})
    assert any(h[0] == "SYNTHRAW" and h[2] == plaintext for h in hits), (
        "cb_common self-test FAILED: raw_key_try_open() did not recover a "
        "known-positive plaintext from its own synthetic zero-IV AES vector"
    )
    wrong_raw_key = b"FEDCBA9876543210"
    wrong_hits = raw_key_try_open(wrong_raw_key, blobs={"SYNTHRAW": (b"01234567", ct)})
    assert not any(h[0] == "SYNTHRAW" for h in wrong_hits), (
        "cb_common self-test FAILED: raw_key_try_open() accepted a WRONG raw "
        "key for a synthetic AES-CBC vector"
    )


_self_test()
_self_test_extended_ciphers()
_self_test_stream_ciphers()
_self_test_binary_plaintext_oracles()
_self_test_keywrap()
