# Phase 527 - Selection-A coordinate slot-extension oracle protocol

Status: prepared, **not execution-locked and not run**.

## Objective

Test the complete Phase-526A base universe against SALPH under the project's
fixed passphrase oracle. Determine whether any Selection-A coordinate value,
alone or in the already-frozen macro-slot grammar, opens a tracked encrypted
container or yields an exact key/address structure.

## Frozen candidate universe

- `_work/phase526/bases.txt`: 112,624 plain bases, SHA-256
  `800e7a181a015416725d399059e8369c556a4f9e4e2fffe9e71f18f9fcd7ea36`.
- Standard `answer_forms() x keystr_forms(newline_variants=True)` expansion.
- Expected GPU form count: 5,137,056, including the GPU tool's 368 empty-alpha
  emissions from digit-only bases.
- No value, join, order, encoding, reversal, or separator may be added.

## Consumers and validators

SALPH is primary because the new values occupy the `matrixsumlist` macro slot
on that transition. If the fixed GPU binary necessarily processes all four
tracked blobs, COSMIC, P32TRAILING, and URLBLOB are a declared secondary
superset, not post-hoc escalation.

Use the same current-source CUDA oracle and validator suite as Phase 524's
final run:

- standard strong and structural plaintext detectors;
- exact 64-byte/full-padding shape;
- raw-key Bloom cache, followed by live funded-address confirmation for any
  Bloom hit;
- Phase-331 eight-address known-target detector.

Weak printable-score rows are descriptive only and cannot promote without an
independent exact structural validator.

## Preconditions for the execution lock

Before issuing the lock:

1. NVIDIA must be visible through `nvidia-smi`.
2. The current-source CUDA image/binary must pass its self-test.
3. The locked container identity must be the same current-source image whose
   Phase-524 run logged both the Bloom cache and eight known targets. On the
   Phase-527 launch, startup must confirm both again before the run is accepted;
   absence of either makes the execution invalid and it must be stopped.
4. Pin the protocol, preparation script, base list, overlap report, executable
   or container image identity, blob inputs, and detector configuration.
5. Verify the expected 112,624 input lines and 5,137,056 emitted forms.

## Run and stop rule

Run once, resumably. Zero strong, structural, funded, and known-target hits
closes this exact universe. Do not add seeds, values, encodings, or separators
after a miss. Any apparent hit must be independently re-derived on CPU from the
recorded base, KDF, cipher, and blob before interpretation.

## Estimated cost

At Phase 524's final measured throughput, approximately 1 hour 55 minutes on
the NVIDIA GPU. No CPU fallback is authorized merely because the GPU is
temporarily unavailable.
