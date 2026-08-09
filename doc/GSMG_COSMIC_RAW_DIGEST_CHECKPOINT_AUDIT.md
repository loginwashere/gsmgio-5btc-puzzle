# COSMIC Raw-Digest/MD5 Checkpoint Audit

**Date:** 2026-08-09  
**Status:** The `4f7a1e4e...c081` checkpoint and the complete published
103x103/base-38/two-address pipeline reproduce exactly. This corrects the
project's 2026-07-12 representation error. It does not weaken the separate
fabrication evidence; the output and addresses instead tie the reproducible
construction directly to the known GitHub/on-chain spam campaign.

## Why this was reopened

Telegram export messages `68249` and `68259` preserve a same-day falsification
and correction by MrNobody. Message `68249` tested the XOR result as its
64-character hexadecimal rendering. Message `68259` reports that Rick
Luminari's construction instead supplies the 32 raw digest bytes directly to
the legacy MD5 KDF and reproduces the published checkpoint.

The distinction is load-bearing:

```text
hex text:  b"a795de11...e50735"     64 password bytes
raw data:  bytes.fromhex("a795...") 32 password bytes
```

They are different password inputs. This project's 2026-07-12 audit tested the
first and incorrectly generalized its negative result to the second.

The original public implementation was also fetched and inspected directly:

```text
repository  jackdevs66/GSMG5_CDuality
commit      8f47839251a8b49e67a41ecb8d964fddd5e9270c
date        2025-09-15
file        solver_salphasion_cosmic.py
```

Its code calls `binascii.unhexlify(hex_key)` before MD5 EVP_BytesToKey. The
README's phrase “use that hex as the OpenSSL password” is therefore imprecise,
but the implementation itself unambiguously uses the decoded 32 bytes rather
than 64 ASCII hex characters.

## Frozen construction

The seven published tokens, including the repeated first/fifth token, are:

```text
matrixsumlist
enter
lastwordsbeforearchichoice
thispassword
matrixsumlist
yourlastcommand
secondanswer
```

XORing their SHA-256 digests gives:

```text
a795de117e472590e572dc193130c763e3fb555ee5db9d34494e156152e50735
```

The authenticated COSMIC OpenSSL envelope is 1,344 bytes:

```text
header       Salted__
salt         2d3f6fe06dc950e6
ciphertext   1,328 bytes / 83 AES blocks
```

Passing the 32 raw XOR bytes through legacy `EVP_BytesToKey` with MD5 and then
AES-256-CBC produces valid one-byte PKCS#7 padding. Removing that `01` byte
leaves 1,327 bytes whose SHA-256 is:

```text
4f7a1e4efe4bf6c5581e32505c019657cb7b030e90232d33f011aca6a5e9c081
```

## Representation/KDF controls

All four immediate interpretations were frozen before inspecting anything
downstream:

| Password material | KDF digest | Padding | Payload length | Payload SHA-256 |
|---|---:|---:|---:|---|
| 32 raw XOR bytes | MD5 | valid, `01` | 1,327 | `4f7a1e4e...c081` |
| 32 raw XOR bytes | SHA-256 | invalid, terminal `66` | 1,328 | `8d3ef569...b927e` |
| 64 ASCII hex bytes | MD5 | invalid, terminal `d9` | 1,328 | `5654a394...a1c2` |
| 64 ASCII hex bytes | SHA-256 | invalid, terminal `f8` | 1,328 | `4edce289...1b7` |

Only raw32+MD5 reproduces the checkpoint. The two ASCII-hex rows also reproduce
the hashes reported in Telegram message `68249`, directly diagnosing the prior
mistake rather than merely finding another working command.

## Complete published downstream reconstruction

The unpadded payload contains 10,616 bits. Reading bytes MSB-first and filling
the first 10,609 bits row-major gives a 103x103 binary matrix, leaving seven
terminal bits:

```text
unused bits = 0111010
S           = 5193
Wr          = 268603   (one-based weighted row sum)
Wc          = 268828   (one-based weighted column sum)
```

These reproduce three invariants quoted in the later discussion. Zero-based
weighting gives `Wr=263410` and `Wc=263635`, so the published values also fix
the indexing convention. Interpreting the seven unused bits in the two bit
orders gives the other two published invariants:

```text
p_big       int("0111010", 2)          = 58
p_little    int("0111010" reversed, 2) = 46
```

GitHub issue `puzzlehunt/gsmgio-5btc-puzzle#81` supplies the next explicit
formula:

```text
s[i]   = row_sum[i] + column_sum[(i + 7) mod 103]
digit  = s[i] - 80
number = the 103 digits interpreted in base 38
output = number serialized as exactly 68 big-endian bytes
```

It reproduces every advertised property:

```text
len(s)             = 103
min(s), max(s)     = 80, 117
digit range        = 0..37 exactly
base-38 output     = 68 bytes / 539 significant bits

half:
0423d9115a1dc756d5d08d2de880ab508bd4745fc97709f4fcb513f2cb8fcc35

better_half:
48cc46e66bdd36b09ae344552f606a761f9d90681f20dfefe2b43db18b623971

trailing four bytes:
fc0c1b02
```

Treating the first two 32-byte fields as secp256k1 private scalars and deriving
compressed-mainnet P2PKH addresses reproduces the public claims:

```text
1JG648yaB7Wp2dpUfcZoRSD4q35oq47vCu
145ZQ9siLrsXBKf465wjdyQYAP5dRwhRhQ
```

These are not the GSMG prize address. Reproducing them proves that the public
algorithm has now been captured accurately; it does not prove the fields were
intended as private keys.

## Fabrication and on-chain provenance

Reproducibility and authenticity are different questions. The corrected
decrypt shows that the construction is deterministic, but a deliberately or
post-hoc selected garbage decrypt is expected to remain deterministic.

The pre-existing project record supplies evidence independent of the
raw-versus-hex mistake:

- the same checkpoint, XOR result, and two addresses recur through at least
  nine GitHub issues plus bitcointalk, generally by mutually citing accounts
  rather than independent derivations;
- issue #88's six-account thread supplied expanding terminology but no
  derivation code in the thread itself;
- issue #17's `pawel-mar` warned that much of the shared code was LLM-produced
  and that the AES stage had not actually been solved;
- Phase 156 independently traced 105 human-readable OP_RETURN messages sent to
  the two genuine GSMG addresses. Zero was signed by a creator-controlled
  input. The exact two addresses produced by this base-38 construction signed
  88 of those 105 transactions;
- the on-chain graffiti includes
  `matrixsumlistenterlastwordsbeforearchichoicethispassword`, directly reusing
  this checkpoint construction's token sequence.

This is a mechanical campaign link, not merely two “unrelated” addresses. The
reproducible branch and the on-chain bait share both derived keys/addresses and
password vocabulary.

## Calibration and limits

The 1,327-byte output is high entropy:

```text
Shannon entropy       7.870209989 bits/byte
strict ASCII ratio    0.388847
```

Valid PKCS#7 padding for a random final AES block occurs with probability

```text
sum(256^-k, k=1..16) ~= 0.003921569 ~= 1/255
```

Therefore valid one-byte padding is not an independent authentication oracle.
The source repository's bounded `p5 x p6 x p7` family has 210 combinations and
exactly one padding-valid member, the published tuple. A random family of that
size expects roughly `210/255 = 0.824` padding-valid members, so this uniqueness
is not independently striking and the candidate lists were not preregistered.

For the row-plus-shifted-column formula, 15 of the 103 cyclic offsets keep all
values in the fixed ASCII/base-38 interval `80..117`; shift 7 is uniquely the
one that spans both endpoints and therefore uses all digits `0..37`. This is a
real internal property. Its evidentiary weight is limited because the number
seven is also mechanically the count of leftover bits, while offset 80 and
base 38 may have been recognized from the resulting minimum and range.

The published payload hash, matrix invariants, base-38 fields, and addresses
all descend from the same branch. Together they establish deterministic
reproducibility, but not independent authentication of its token set,
raw-byte representation, MD5 KDF, or matrix consumer. Combined with the
high-entropy payload and the independently verified address/vocabulary link to
the spam campaign, the evidence continues to favor fabrication.

## Corrected verdict

Promote as facts:

- the exact seven-token XOR;
- the distinction between raw 32-byte and hexadecimal 64-byte passwords;
- raw32 + MD5 + AES-256-CBC reproduces the 1,327-byte checkpoint;
- the MSB-first 103x103 construction reproduces `S`, `Wr`, `Wc`, `p_big`, and
  `p_little`;
- the published shift-7/base-38 construction reproduces the complete 68-byte
  output, split, and two claimed addresses.

Do not promote yet:

- interpreting the two 32-byte fields as intended private keys rather than
  arbitrary same-branch output;
- treating their reproducible but unrelated addresses as puzzle checkpoints;
- any claim that the branch reaches the actual GSMG prize address;
- the checkpoint as a creator-authenticated solve rather than a reproducible
  community construction.

**Overall verdict:** retain the complete pipeline as a reproducible negative
control and correct test vector. Do not reopen it as a puzzle-solution lead
without creator provenance or an independent validation target. Repetition of
values computed from the same 1,327 bytes is consistency, not independent
evidence, while the address and token reuse positively links the branch to the
known spam campaign.

## Reproduction

```bash
python3 tools/gsmg/cosmic_raw_digest_checkpoint_audit.py --self-test
```
