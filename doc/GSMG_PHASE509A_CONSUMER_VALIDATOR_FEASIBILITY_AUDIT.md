# Phase 509A consumer/validator feasibility audit

Date: 2026-09-15

## Outcome

Consumer-first validation is useful only at the terminal boundary. None of
the strong closed-system validators supplies a meaningful gradient for
assembling a transposition order or checkerboard. AES, address derivation,
Base58Check, BIP39 checksums, and key-wrap integrity are effectively yes/no
tests after a complete candidate exists.

Accordingly, Phase 509 must not replace the quadgram score with an "AES score"
or "address score": wrong partial candidates receive no useful information.
Soft properties such as printability, permitted characters, or language score
can guide a search, but Phase 508 shows that such a proxy must beat a
same-budget real-versus-null calibration before it is allowed to prioritize
expensive real runs.

## Validator classes

| Validator | Independent strength | Search gradient | Standalone promotion? |
|---|---|---|---|
| Exact derived P2PKH match to either known address | approximately `2/2^160` per derived address | none | yes |
| Phase-410 AES-CBC | padding alone is only about `1/255`; needs independently strong plaintext classification | none | no, not on padding alone |
| AES Key Wrap | built-in integrity value, conservatively at least about 32 bits in the weakest padded case | none | yes, subject to exact mode provenance |
| WIF/Base58Check | 32-bit checksum plus prefix/length | none | no; derive and match address |
| BIP39 | only 4--8 checksum bits after word membership | none | no; derive and match address |
| Other Base58Check containers | 32-bit checksum plus type structure | none | no unless independently expected |
| Raw/hex secp256k1 scalar shape | almost every random 32-byte value is valid | none | no |
| Printability/language | family-dependent heuristic | yes, soft | no without calibration |

The existing ten-entry exact hash160 registry includes the two known puzzle
addresses plus eight EC-derived neighbors. The neighbors are useful bounded
derived hypotheses, but the first Phase-509 terminal test should use only the
two directly known addresses; this avoids silently enlarging the target after
candidate observation.

## Exact Phase-507 coverage

Phase 507 consumed 43 exact uppercase terminal byte strings, 437--491 bytes
long. It tested only:

```
SHA256(terminal).hexdigest().encode("ascii")
    -> legacy EVP_BytesToKey/SHA-256
    -> AES-256-CBC/PKCS7
    -> SALPH, COSMIC, P32TRAILING
```

That was 129 decryptions, with zero valid padding and zero promotions. It did
not test those 43 raw SHA-256 digests as Bitcoin private scalars. It also did
not test raw terminal passphrases, alternate KDF/cipher modes, Key Wrap,
URLBLOB, substrings, or mutations. These omissions are recorded as scope, not
an invitation to sweep them all.

## Recommended Phase 509B

The strongest cheap residual is one exact, closed family:

1. Reuse the unchanged 43 Phase-507 terminal byte strings.
2. Compute exactly `SHA256(terminal).digest()` once per candidate.
3. Treat the 32 bytes as a secp256k1 scalar.
4. Derive compressed and uncompressed legacy P2PKH addresses.
5. Compare exactly with `1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe` and
   `17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa`.
6. No mutation, alternate hash, substring, scalar algebra, neighboring target,
   or AES query.

This yields 86 derived addresses and 172 exact address comparisons. The simple
union bound for an accidental target match is `172/2^160`, approximately
`1.18e-46`. A null simulation would add no practical calibration information;
the important controls are a known private-key positive fixture, exact target
pinning, and a lock issued before checking the 43 digests.

This remains a terminal check. A negative result would close only this
digest-to-private-key interpretation of the already-produced 43 candidates;
it would not validate their generating solver or rank new widths and pairs.

## Reproduction

```bash
PYTHONPATH=tools/gsmg python3 tools/gsmg/phase509a_consumer_validator_feasibility.py --self-test
PYTHONPATH=tools/gsmg python3 tools/gsmg/phase509a_consumer_validator_feasibility.py --report
```

## Phase 509B execution outcome

The recommended exact family was subsequently locked and executed once. All
43 raw SHA-256 digests were valid secp256k1 scalars. Their 86 compressed and
uncompressed P2PKH addresses produced zero matches against the two frozen
targets across 172 exact comparisons. No sensitive hit artifact was created.

Disposition: bounded negative for exactly
`SHA256(terminal).digest() -> secp256k1 -> {compressed,uncompressed} P2PKH`
over the 43 Phase-507 terminals and the two directly known addresses. No
mutation or neighboring target is licensed by this result.

- Execution-lock SHA-256:
  `8c4f8a98641a49cdbe23fe957b37cc2729c7fec8e484fa01dd8ad4412e5e6285`
- Result SHA-256:
  `3c2874d9022afc3e3c1f93eb9502a272adf94ffbb860c67e8e9a252e67aed32c`
- Focused tests: 8/8 pass across Phase 509A and 509B.
