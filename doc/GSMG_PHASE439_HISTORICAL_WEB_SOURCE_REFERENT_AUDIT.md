---
type: audit
phase: 439
date: 2026-08-28
status: complete
result: new-source-referent-registered-but-ineligible
disposition: gated
script: tools/gsmg/phase439_historical_web_source_referent_audit.py
---

# Phase 439 — Historical Web-Source Referent Audit

Creator-served historical page source is a distinct referent that Phase 437's
“repository source files” row did not cover. Four exact historical web-source
families are now registered, but none is executable from the instruction as written.

## Chronology

| Object | Relation to Architect instruction | Disposition |
|---|---|---|
| Original lowercase `/puzzle` | Earlier, but served a PNG directly | Not HTML/source code; grounded image paths already covered |
| `theseedisplanted` HTML | Earlier | Eligible for referent review |
| `choice...iwroteitmyself` HTML | Earlier; carried the Phase 2/3 ciphertexts | Eligible for referent review |
| SalPhaseIon/Cosmic HTML | Downstream | Fails literal `RETURN` chronology |
| Restored `Puzzle.html` | Created in 2026 after restoration | Postdates instruction; authorship unresolved |
| General GSMG site JavaScript | Broad site surface | No selected, authenticated puzzle operand |

The two earlier raw captures are pinned as:

| Page | Bytes | SHA-256 |
|---|---:|---|
| `theseedisplanted` | 1,585 | `5356c88769137ec82953888d7c5b9f18b0fa00019fad7591cc6aaaaf91463136` |
| `choice...iwroteitmyself` | 9,902 | `7237ce18a62f16dc55d94a2594da4256543b7dc7b34e4e59783473c34c7fbf9b` |

Their committed readable copies are normalized reconstructions, not identical
raw responses. Raw bytes include changing/request/deployment material such as
CSRF values and an external Cloudflare beacon. Therefore full-response bytes do
not have a puzzle-fixed normalization.

## Source-only comment pair

The two chronologically prior HTML sources each contain exactly one hidden comment:

1. `Nice to see you around! Good luck little bunny hunter ;)`
2. `You made it to the next step! Good luck little bunny hunter ;)`

They share the exact suffix `Good luck little bunny hunter ;)`; their distinct
prefixes are `Nice to see you around!` and `You made it to the next step!`.

This ordered pair is the strongest literal web-source referent because it is:

- present only in source, not rendered page text;
- attached to the only two real prior HTML stages;
- stable as an exact pair after excluding request/deployment fields;
- absent from registered prime/password families.

It is still not selected uniquely. `SOURCE CODES` could mean full HTML,
ciphertext textareas, comments, earlier puzzle artifacts, or something outside
the pages. Nothing says to retain the common suffix, take the differing prefixes,
index words versus letters, or concatenate in a particular representation.

## Excluded source material

- The historical CSRF value is deployment/session state. Creator message 28703
  explicitly describes the changing mechanism as protection against brute force
  and says to find the right next hint.
- Both archived pages contain one external Cloudflare analytics script and zero
  inline or puzzle-authored JavaScript.
- The Phase 2 and Phase 3 textarea ciphertexts are exact creator puzzle objects,
  but their solved containers/toolchain are already covered by Phase 410.
- Creator message 28794 directly replies `Won't work` to someone who said they
  scanned GSMG entirely. Message 28812 points instead to `/puzzle` and says all
  needed information is there. These constrain broad site archaeology; they do
  not identify the two comments as an endgame operand.

The solver-export fixed-term check found no creator-authored hits and no direct
creator reply for any of: `nice to see you around`, `you made it to the next
step`, `good luck little bunny hunter`, `html source`, or `source code`.

## Eligibility result

Four newly registered historical source families are genuinely uncovered:

- raw `theseedisplanted` HTML;
- raw `choice...iwroteitmyself` HTML;
- their ordered full-response pair;
- their ordered source-only comment pair.

Zero of eleven audited objects passes all eight gates. The comment pair comes
closest: it passes creator-puzzle-artifact, chronology, stable representation,
and novelty, but fails local selection, fixed operator, fixed unit/boundary, and
fixed consumer. The full HTML objects additionally fail stable representation.

## Verdict

Disposition: `new_source_referent_registered_but_ineligible`.

This is a real new coverage entry, not a new decoding result. It should reopen
only if primary evidence selects source comments or a canonical normalized HTML
core and fixes prime unit/base/direction/rail/boundary plus consumer.

No prime extraction or password material was generated. No oracle, network,
Docker, or GPU action occurred.

Reproduce:

```bash
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase439_historical_web_source_referent_audit.py --self-test
PYTHONPATH=tools/gsmg python3 \
  tools/gsmg/phase439_historical_web_source_referent_audit.py \
  --output tools/gsmg/phase439_result.json
```
