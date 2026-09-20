# Phase 528 — DBBI 84-token consequence audit

Date: 2026-09-19  
Disposition: **one historical cell corrected negative; new payload objects isolated**

## Question

What actually changes when DBBI's newly justified 84-token prime-host parse is
used instead of the historical 83-token guide, and which earlier conclusions
need to be rerun?

This is an oracle-free dependency audit. It does not test passwords, AES, or
FAED.

## Exact parse delta

Both parses contain the same 23 group payloads in the same order:

```text
d, "", i, f, hcc, g, iha, e, eih, ggege, b, gehhe, hhf, a,
fdh, ffcdb, fcccg, f, eggec, dci, f, ffgig, eea
```

Their only grammatical difference is at the raw terminal `be`:

| Property | 83-token parse | 84-token parse |
|---|---:|---:|
| Host 23 | `be` (yellow) | `b` (blue) |
| Unhosted tail | empty | `e` |
| Host profile | 15 `b` / 8 `be` | 16 `b` / 7 `be` |
| Hosted payload symbols | 60 | 60 |
| Full non-host residue | 60 | 61 |

Thus the 84-symbol logical sequence does **not** discover a different internal
grouping. It reclassifies group 23 from the yellow rail to the blue rail and
leaves one terminal `e` outside all 23 prime hosts.

The common 60-symbol hosted residue is:

```text
difhccgihaeeihggegebgehhehhfafdhffcdbfcccgfeggecdcifffgigeea
```

The 84-parse full residue is exactly that string plus `e`:

```text
difhccgihaeeihggegebgehhehhfafdhffcdbfcccgfeggecdcifffgigeeae
```

## Direct 16/7 payload partition

Earlier 16/7 work used the endpoint colors as an operator projected onto other
source strings. It did not concatenate the DBBI group payloads classified by
those hosts. The directly implied rails are:

| Rail | Groups | Symbols | A1I9 sum | Concatenated payload |
|---|---:|---:|---:|---|
| `b` host / blue | 16 | 35 | 183 | `difgihaebgehhehhfaffcdbfcccgdcifeea` |
| `be` host / yellow | 7 | 25 | 153 | `hcceihggegefdhfeggecffgig` |

Together the hosted payload has 60 symbols and A1I9 sum 336. The unhosted tail
is `e` (value 5), so the complete 61-symbol residue sums to 341. These are
measurements, not decoded messages or password claims.

All six bounded text objects—the historical residue, new residue, both rails,
and both rail orders—are absent as exact bytes from:

- Phase 478's 1,749,878 actually submitted oracle materials; and
- Phase 523's 133,657 base strings.

This establishes exact-object novelty only. It does not establish that any is
creator-intended or that an encrypted consumer uses one.

## Historical dependency result

The change is narrower than it initially appeared:

- Phases 61, 270, and 442–444 already used the identical 16/7 endpoint-color
  profile produced by splitting final `be`. Their negative endpoint
  projections remain valid; Phase 525 strengthens the source status of their
  operator but does not change its bytes.
- Phases 171/172 already tested both the 83-block and split-84-block COSMIC
  mappings. Those bounded negatives remain valid.
- Phase 53's statement that the recovered guide has 83 tokens remains a valid
  parse, but no longer a unique parse.
- Phase 177's `be` class labels genuinely change. The historical comparison
  used eight merged versus two split literal `be` pairs. Under the 84-token
  parse the terminal raw `be` is split into host `b` plus tail `e`, producing
  seven merged versus three split pairs.

No other prior cell identified in the inventory changes its tested bytes.

## Corrected Phase-177 result

Only the invalidated `merge_gap` cell was rerun. The 105 zero-insertion
positions, two orientations, original binary profile, seed 177, and 2,000
shuffle trials were preserved exactly.

```text
real family maximum:        0.7142857143
best insertion/orientation: 52 / dbbi_lower
nulls at or above:          1050 / 2000
familywise p:               1051/2001 = 0.525237
promotion bar:              0.005
```

This is a clean negative. Correcting the final merge label does not make the
`matrixsumlist` triangular bits explain DBBI's merge/split choices.

## Verification

- Seven focused tests pass, plus the module self-test.
- Result SHA-256:
  `ac30ee6810e85a62ac29028c18321f1dde2a5919cbc01bfdc6d49d8e84f4a86b`.
- The run records `aes_called=false`, `faed_accessed=false`,
  `password_expansion_performed=false`, and `language_score_used=false`.

## Disposition and next gate

The 84-token result does not reopen the already-negative endpoint-color
projection family and does not rescue Phase 177. It does isolate a small,
previously unsubmitted source family: the 61-symbol full residue and the exact
35/25 payload rails.

A follow-up may expand only these three primary bases (full residue, blue rail,
yellow rail), with the two rail concatenation orders as deterministic compound
forms, through the project's already-established solved-boundary password
grammar. It must first diff every expanded material against all executed
candidate corpora. No reversal, arbitrary separator, XOR, base conversion, or
new consumer follows from this audit.

## Limits

The Atlas and Selection-A reasoning remain unauthenticated community analysis.
This phase does not prove the 84-token parse is uniquely intended, that the
tail `e` is data rather than a grammatical remainder, that the rails are
password material, or that any known encrypted blob consumes them.

