---
type: audit
phase: 445
date: 2026-08-29
status: complete
result: two-native-carriers-no-established-consumer-binding
disposition: gated
script: tools/gsmg/phase445_code_you_carry_transport_audit.py
---

# Phase 445 — `CODE YOU ... CARRY` Transport-Role Audit

## Question

Does `ALLOWING A TEMPORARY DISSEMINATION OF THE CODE YOU HOPEFULLY
CARRY` identify a unique object carried out of Phase 3.2.1 or 3.2.2 and a
unique established consumer for it?

The protocol was frozen before the graph was evaluated. This is an
architecture audit, not a password experiment: it generates no candidate
material and makes no oracle call.

## Native graph

The audit pins 13 exact Phase-3.2 objects by length and SHA-256 and records
their native transformations. Six edges are established transforms and four
are authenticated container extractions:

| Path | Established role |
|---|---|
| password + encrypted Phase-3.2 blob → plaintext | AES container decryption |
| plaintext → 3.2.1 raw block / validation digits / 3.2.2 clue / P32 text | authenticated delimiter extraction |
| raw 3.2.1 block → CP1141 letters | clue-selected transcode |
| CP1141 letters + Beaufort key → `answer_321` | Architect decode |
| 3.2.2 clue → keyed alphabet | clue solution |
| validation digits + keyed alphabet → `answer_322` | checkerboard decode |
| P32 text → P32 envelope | Base64 decode |

The graph also registers three already-tested negative edges from
`answer_321`, `answer_322`, and their ordered composition to the P32 envelope.
Those negative edges are coverage records, not established transport rules.

## Carrier gates

An eligible carried object had to be exact and reproducible, be the output of
an established transform, exist before P32, remain unconsumed by its native
mini-solve, serialize without a new normalization choice, and not itself be
the unresolved target.

Exactly two objects pass all six gates:

| Object | Length | SHA-256 | Native role |
|---|---:|---|---|
| `answer_321` | 1,539 | `56c43a300e28b86bb43b8dcbae74c43c76bde90b3e1190620fb656f2c94b2241` | decoded Architect instruction output |
| `answer_322` | 91 | `878b7afacc9e35412e76b8506cc8297fa5aeba5381e108dc421b71a0ab8993d8` | decoded two-private-key semantic output |

Every other object is consumed inside the established solve, is delivered
input rather than a transformed output, is downstream of the instruction, or
is the target itself. The phrase therefore does not select one carrier: both
decoded sibling outputs fit the same literal transport role.

## Missing edge

No established edge binds either eligible output to the P32 envelope, and no
established transform maps either output to it. Promoting one would still
require choosing at least:

- which of the two decoded outputs is carried;
- whether they are combined and in which order;
- what operation converts the selected object into key material; and
- whether P32 is even the intended consumer.

Those are precisely the choices the transport wording does not settle.
Phase 270 already recorded 300 negative structural trials over direct sibling
readings. Phases 442, 443, and 444 add 36, 36, and 216 machine-verified
negative trials for the precedent-bound prime and AND/OR derivatives. These
closures do not prove that no transport exists, but they prevent the known
negative constructions from being presented as an untested edge.

## Provenance control

The connected wording `temporary dissemination ... code you ... carry` is
inherited from the Architect screenplay material; only `hopefully` is a
creator addition. Consequently, the apparent transport vocabulary is not an
independent puzzle-native selector for an object or consumer. It can describe
the narrative role of a carried code, but cannot break the two-carrier tie.

## Verdict

Disposition: `two_native_carriers_no_established_consumer_binding`.

The transport model is structurally plausible but non-executable. It leaves
two equally eligible native carried outputs, zero established target
bindings, and zero established transforms to P32. Promotion requires new
primary evidence that uniquely fixes an object, consumer, and transform.
Zero password materials were generated, zero oracle calls occurred, and
Docker and the GPU were untouched.

Reproduce:

```bash
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase445_code_you_carry_transport_audit.py --self-test
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase445_code_you_carry_transport_audit.py \
  --output tools/gsmg/phase445_result.json
```
