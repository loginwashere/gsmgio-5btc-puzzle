# Phase 527 - Selection-A coordinate slot-extension oracle audit

Date: 2026-09-19  
Disposition: **bounded negative**

## Question

Does any of the 16 Selection-A coordinate representations, used alone or in
Phase 523's frozen macro-slot grammar as a `matrixsumlist` value, open SALPH or
produce an exact structural/key result on a tracked encrypted container?

## Lock and execution

The execution lock SHA-256 was
`179022a1e9c7319bdd2bbbc4435ba48bbbd29fc50fcb9fda6c56c20a5cb14864`.
It pinned:

- the 112,624-base Phase-526A input list (SHA-256 `800e7a18...7ea36`);
- 5,137,056 expected newline-expanded forms;
- current-source CUDA container image
  `sha256:cf2432d...ab60a`;
- the RTX 5070 UUID;
- Bloom-cache SHA-256 `376375ce...82250`; and
- the protocol, preparation code, Phase-525 result, and Phase-526 report.

The mandatory CUDA self-test passed. Startup reported exactly 112,624 bases,
5,137,056 forms, the Bloom cache loaded, and eight Phase-331 EC-derived known
targets folded in. The fixed oracle processed all four tracked blobs because
its variant table is a four-blob superset; SALPH remained the primary consumer.

The run completed with container exit code 0 in 8,734 seconds at approximately
588 forms/second.

## Result

| Quantity | Result |
|---|---:|
| Forms completed | 5,137,056 / 5,137,056 |
| Strong hits | **0** |
| Structural hits | **0** |
| Phase-331 known-target matches | **0** |
| Confirmed funded addresses | **0** |
| Weak rows | 159 |
| Unique weak candidate/KDF/blob triples | 145 |
| Bloom/key-shape rows | 17 |
| Unique Bloom addresses | 16 |

Weak rows by blob were SALPH 39, COSMIC 47, P32TRAILING 31, and URLBLOB 42.
Their z-scores ranged from 5.003 to 6.076, below the strong threshold. All 159
were re-derived with the CPU implementation: zero padding-reconstruction
failures, zero z-score mismatches, and zero hex64/WIF/BIP39 key-shape matches.

All 17 Bloom rows were checked by the run's live API path and recorded
`confirmed_funded: false`; one address appeared twice, leaving 16 unique false
positives. The log contains no strong, structural, known-target, or confirmed-
funded marker.

## Fail-closed verification

`phase527_verify_run.py` independently verifies:

- lock integrity;
- checkpoint header and the contiguous sequence `0..5,137,055`;
- required self-test/cache/known-target/completion log markers;
- absence of every positive log marker;
- weak-row CPU re-derivation and key-shape classification; and
- false status on every key-shape row.

Three verifier tests pass. The saved verification record SHA-256 is
`c45a0d29a6cc2ac7a289a8ea125dc1ef1bdcd4ffbeb4202aba90945eac3fbf03`.

Runtime artifact hashes:

- checkpoint: `31980ced...7a7f0`;
- weak hits: `54a261e3...afff`;
- key-shape rows: `2c955421...570`;
- container log: `9aa2ab8f...d5ba`.

## Disposition

Closed negative for the 16 frozen Selection-A coordinate values under Phase
523's exact slot order, subset grammar, connected/single-space joins, standard
newline-enabled passphrase expansion, and the Phase-524 60-variant four-blob
oracle with Bloom and known-target checks active.

Do not add coordinate reversals, permutations, bases, separators, or encodings
on this negative. Reopening requires a new authenticated representation rule or
consumer, not another formatting hedge.

## Interpretation and limits

The result rejects the most direct password use of Selection A. It does not
disprove Selection A as a structural observation, authenticate its one-byte-
representative criterion, explain the 61 non-prime DBBI symbols, or rule out a
non-password operation consuming its coordinates.

## Artifacts

- `tools/gsmg/phase527_execution_lock.json`
- `tools/gsmg/phase527_selection_a_oracle_lock.py`
- `tools/gsmg/phase527_verify_run.py`
- `tools/gsmg/phase527_verification.json`
- corresponding focused tests
- runtime files under `tools/gpu_oracle/output_local/phase527.*`
