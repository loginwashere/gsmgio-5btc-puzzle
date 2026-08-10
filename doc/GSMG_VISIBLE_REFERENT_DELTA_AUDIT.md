# GSMG visible-referent delta audit

> **Phase-228 matched-control correction:** P32TRAILING's equal 64+64
> mechanical split and COSMIC's authored 28x64 layout are now explicit delta
> controls. They confirm that SALPH's locally authored `enter`, rather than
> the common width 64 by itself, is the load-bearing structural fact.

## Scope

Phase 227 updates the original seven-family yin-yang artifact inventory with
only later discoveries or page-local structures that were not separately
gated there. It does not run a password, cipher, address, or blob oracle.

A candidate must pass all five gates:

1. authenticated and visible/already present;
2. deterministically recovered without selecting a rule from its result;
3. genuinely dual rather than merely adjacent or repeated;
4. produced at the immediate `lastwordsbeforearchichoice -> yinyang` boundary;
5. connected to a fixed consumer or an independent structural discriminator.

The original inventory's frozen qualification table still has seven artifact
families and zero qualifiers after the Phase-223/224 corrections.

## Delta results

| Candidate | Visible | Deterministic | Dual | Correct boundary | Consumer/discriminator | Result |
|---|---:|---:|---:|---:|---:|---|
| OpenSSL `Salted__` fronts | yes | yes | no | no | no | Container marker only |
| `Salt | Phase | Ion` insertion | no | no | no | no | no | Result is neither authored nor uniquely selected |
| creator `YING/YANG -> IG/AG` | yes | no | yes | yes | yes | FAED-specific, but typo-derived operator is not authenticated |
| `thispassword -> sha256 -> SALPH` sequence | yes | no | no | no | no | Page order does not fix operand scope |
| SALPH `64 chars -> enter -> 64 chars` | yes | yes | yes | no | yes | Genuine positive control at the wrong boundary |
| P32TRAILING mechanical `64+64` | yes | no | no | no | no | Same length as SALPH, but no authored separator |
| COSMIC authored `28x64` layout | yes | yes | no | no | no | Width control, not a two-half structure |

### OpenSSL front marker

The visible authenticated SALPH, COSMIC, and P32TRAILING Base64 strings begin
with encodings of the same OpenSSL header. Demonstrated Base64 decoding
recovers literal `Salted__` as the first eight bytes of all three. This is exact and does
fit the idea of something encoded at the front, but it identifies an OpenSSL
container—not a dual state, password, KDF, mode, or operand binding.

### `Salt | Phase | Ion`

Phase 222 already established the complete source-neutral family: inserting
each distinct letter of lowercase `true` at every title position gives 48
candidates and six dictionary-valid three-word readings. Both
`salt|phase|ion` and `sale|phase|ion` survive at the original CamelCase
boundary. The `Salted__` resonance is real recognition after enumeration,
but the edited title itself is not an authenticated visible object and its
`t`/position are not source-selected.

### `YING/YANG -> IG/AG`

This is the strongest delta candidate. Native `a-i` filtering is exact,
`I <-> A` are mirror endpoints, and shared `G` uniquely wins the paired FAED
rank control (`{g,i}` rank 1, `{a,g}` rank 5). It therefore passes the dual,
boundary, and independent-discriminator gates.

It still fails deterministic recovery as an authored puzzle operation. The
creator's authenticated binary macro uses standard `yinyang`, while the two
plain-language messages use the typo-like `ying` form, and the creator's
earlier direct caveat says not to mine typos for clues. The alignment cannot
authorize an `{a,g}` decoder or an IG/AG combination rule.

### Local password/SHA/SALPH sequence

The page genuinely orders `thispassword`,
`sha256 our first hint is your last command`, and the SALPH envelope. Phase
220's raw-markup audit remains decisive: all SalPhaseIon segments occupy one
uniformly spaced textarea text node with no authored boundary markup or line
breaks. The presentation supplies no exact SHA preimage or operand-to-blob
edge.

### SALPH `enter` halves

The page contains a real positive control for the gate. Literal decoded
`enter` separates two visible 64-character parts and deterministically
reconstructs the authenticated SALPH Base64 envelope. This proves the audit
can recognize an intentional dual page structure. It does not identify
yin-yang because it occurs after the unresolved password/SHA region rather
than immediately after `lastwordsbeforearchichoice`.

### P32TRAILING and COSMIC width controls

P32TRAILING is exactly 128 Base64 characters, decoding to the same 96-byte
full-envelope / 80-byte ciphertext-body shape as SALPH. It therefore admits a
mechanical midpoint split of 64+64. Unlike SALPH, however, no local instruction
or authenticated separator selects that midpoint. Importing SALPH's split
would be the rule choice the audit is designed to reject, and equal length
alone does not make the resulting pieces opposed or independently meaningful.

COSMIC supplies the complementary presentation control: its authenticated
textarea contains 28 authored lines, all exactly 64 characters. It proves that
64 is the page's general Base64 display width, not sufficient evidence for a
two-half yin-yang object. COSMIC has no midpoint `enter` and is a 28-row
rectangle rather than two selected components.

## Verdict

No delta candidate passes all five gates. The two strongest failures are
complementary:

- IG/AG is at the correct semantic boundary and independently FAED-specific,
  but is not a deterministic authored operator.
- the SALPH halves are deterministic, visible, dual, and consumed, but occur
  at the wrong transition boundary.

P32TRAILING and COSMIC sharpen the latter finding: SALPH's authored `enter` is
unique among the controls, while the number 64 is ordinary shared layout.

No password, decoder, or oracle expansion follows from Phase 227. A candidate
can reopen only if new primary evidence fixes the missing spelling/operator
for IG/AG or relocates/binds a deterministic visible dual object to the
Architect boundary.

## Reproduction

```bash
python3 tools/gsmg/visible_referent_delta_audit.py --self-test
python3 -m unittest tools/gsmg/test_recent_audits.py
```
