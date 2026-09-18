---
type: audit
phase: 522
date: 2026-09-18
status: complete
result: closed-negative
disposition: closed-negative
script: tools/gsmg/cb_common.py, tools/gsmg/extended_cipher_recheck.py
---

# GSMG Phase 522 — OpenSSL Menu-Gap Round 2 (CAST5, RC4; IDEA/RC2 excluded)

## Question

Round 1 (2026-07-26, `OPENSSL_MENU_GAP_CIPHER_VARIANTS`) rechecked this
project's curated candidate corpus against Blowfish/Camellia/SEED-CBC —
historically plausible `openssl enc` menu items no prior sweep had ever
tried, since `Salted__` identifies the OpenSSL container, not which
cipher/KDF produced it. That round stopped there. CAST5, IDEA, and RC4 were
also ordinary named `openssl enc` menu items from the same era. Does the
same curated corpus, against these three, open any tracked blob?

## Method

**`cb_common.py`**: registered `cast5` in `CIPHER_CLASSES`/`CIPHER_BLOCK_SIZES`
(8-byte block) — since `aes_try_open_bytes`/`aes_try_open_ecb_bytes` already
generalize over `cipher`, this needed no other code change for CAST5. Added
`OPENSSL_MENU_GAP_ROUND2_CBC_CIPHER_VARIANTS` (CAST5-CBC only, fixed at
OpenSSL's single named 128-bit key size, legacy MD5/SHA1/SHA256 +
PBKDF2-HMAC-SHA256@10000 — 4 variants). RC4 is a stream cipher with no
block/IV concept (`openssl enc -rc4` derives only a key via the same
Salted__/EVP_BytesToKey machinery), so it needed a new dedicated oracle
function, `aes_try_open_rc4_bytes`, mirroring `aes_try_open_stream_bytes`'s
printable-z-score-only plausibility gate (no PKCS7 pad to check). Added
`OPENSSL_MENU_GAP_ROUND2_RC4_VARIANTS` at OpenSSL's three actually-named RC4
key sizes (`-rc4-40`/`-rc4-64`/`-rc4`(-128), 12 variants). Wired a new
`--openssl-menu-gaps-round2` flag into `extended_cipher_recheck.py`
(generalizing `sweep()` with an `oracle_fn` parameter, default `aes_try_open`,
unchanged for every existing caller), sweeping the same 648-candidate
curated corpus × `answer_forms()` × `keystr_forms()` used by round 1.

**IDEA and RC2 correction, made before any real sweep ran:** the original
scoping claimed IDEA needed no new dependency because `cryptography` exposes
an `algorithms.IDEA` Python class. Verified directly that this is wrong for
*this* environment: `Cipher(algorithms.IDEA(key), modes.CBC(iv))` raises
`UnsupportedAlgorithm` against the installed OpenSSL 3.0.13 backend (IDEA is
compiled out of this build entirely, unlike Blowfish/CAST5/SEED, which
remain reachable through the legacy provider). Exposing a class in the
Python API is not the same as the underlying operation working — a
distinction the original round-2 scoping note missed. IDEA is therefore
excluded from the runnable variant set (would crash mid-sweep otherwise),
alongside RC2 (never implemented by `cryptography` at all). Both would need
a different backend (pycryptodome implements both) — deferred as an
explicitly-scoped follow-up, not silently dropped.

**Controls**: new module-level self-test (`_self_test_menu_gap_round2`,
runs automatically on every `cb_common` import) round-trips a known-positive
synthetic vector for every CAST5-CBC and RC4 variant, plus a wrong-password
negative control for RC4 (no padding check would otherwise catch a false
accept). Three new `unittest` cases in `test_cb_common.py` cover the same
ground directly. Confirmed no regression: full `test_cb_common.py` suite
(13 tests) and `test_recent_audits.py` (a broad recent-phase regression
suite) both pass unchanged after the `cb_common.py` edit.

## Result

```
[*] loaded 648 curated candidates from 23 files + seed lists
[*] candidate-list digest: 2d233645ef49a141
[*] cast5-cbc: 17,037 attempts across 4 variants x 4 blobs (SALPH, COSMIC, P32TRAILING, URLBLOB)
[*] rc4: 17,037 attempts across 12 variants x 4 blobs (SALPH, COSMIC, P32TRAILING, URLBLOB)
[*] no candidate opened any blob under any tested cipher/KDF variant
```

34,074 total decrypt attempts, **0 hits**.

## Disposition

Closed negative. None of this project's curated candidate corpus opens
`SALPH`/`COSMIC`/`P32TRAILING`/`URLBLOB` under CAST5-CBC or RC4 at any
OpenSSL-named key size, across the standard legacy-KDF and PBKDF2 digest
set. No registered gap closes. The `OPENSSL_MENU_GAP_ROUND2_CBC_CIPHER_VARIANTS`
and `OPENSSL_MENU_GAP_ROUND2_RC4_VARIANTS` lists are now standing,
reusable infrastructure (same status as round 1's variant lists) for any
future candidate corpus, not single-use to this sweep.

## Facts affected

None.

## Supersedes/corrects

None against prior phases. Corrects this same investigation's own initial
scoping claim about IDEA's dependency-free availability, caught before any
real sweep was run against it.

## Artifacts

- `tools/gsmg/cb_common.py` — `cast5` registered in `CIPHER_CLASSES`/
  `CIPHER_BLOCK_SIZES`; `OPENSSL_MENU_GAP_ROUND2_CBC_CIPHER_VARIANTS`,
  `RC4_KEY_LENS`, `OPENSSL_MENU_GAP_ROUND2_RC4_VARIANTS`,
  `aes_try_open_rc4_bytes`, `_self_test_menu_gap_round2`.
- `tools/gsmg/extended_cipher_recheck.py` — `oracle_fn` parameter on
  `sweep()`, `aes_try_open_rc4` wrapper, `--openssl-menu-gaps-round2` flag.
- `tools/gsmg/test_cb_common.py` — `OpensslMenuGapRound2Tests` (3 cases).

## Reopen condition

Only on a new curated candidate source, or a pycryptodome-backed follow-up
specifically scoped to IDEA/RC2 — not on re-running this exact variant set
against the same corpus again.
