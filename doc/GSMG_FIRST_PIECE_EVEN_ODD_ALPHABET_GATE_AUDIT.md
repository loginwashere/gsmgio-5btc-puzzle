# GSMG `86420 / 13579 / igecabdfh` Gate Audit

**Date:** 2026-08-09  
**Status:** Arithmetic verified; independent-recovery gate fails.

## Gate definition

Points 12–13 proposed:

```text
86420 -> nine's complement 13579
86420 under a=0 -> igeca
1357  under a=0 -> bdfh
joined            igecabdfh
```

Before promoting the complement or alphabet permutation, the ranked queue
required all five even digits to be recovered independently rather than
completing a visible `-2` progression.

`tools/gsmg/first_piece_even_odd_alphabet_gate_audit.py` reconstructs every
source value and applies a strict gate. It does not rerun the direct `86420`
blob oracle, which Phase 191 already closed with zero hits.

## Exact provenance

### `8,6,4`

The row-local uppercase-G consumer remains strong:

```text
payload:          O / C / Be
atomic numbers:   8 / 6 / 4
```

The marker-null comparison already established that uppercase `G` is the only
shared exact-case marker producing a fully element-parsable payload.

### `4,2`

The two uppercase-G reference counts are:

```text
banner G count:   4
address G count:  2
```

The first reference overlaps the terminal atomic number:

```text
8,6,4
    4,2
--------
8,6,4,2
```

This is a real measured join, although both streams arise from the same
`#383838` row-local consumer.

The Architect route supplies a secondary `2` echo:

```text
selected end rail: hye
filter to a-i:      he
chemical case:     He
atomic number:      2
```

That route requires filtering and chemical case promotion, but confirms that
`2` is not merely extrapolated from `8,6,4`.

### Terminal `0`

The unique FEFE cell's authenticated binary value is exactly zero. However,
the grid's `base_bit()` rule is only an ink/non-ink classifier:

```text
black   1
blue    1
white   0
yellow  0
FEFEFE  0
```

Thus the FEFE location is independently selected and genuinely contains a
zero bit, but the value `0` is not specific to the anomaly. Any ordinary white
or yellow cell supplies the same digit. Appending this binary class bit after
three atomic numbers and one pixel count is also not selected by a clue.

## Gate result

Every numeric value is measured without extrapolation:

```text
8,6,4,2,0
```

But the strict independent-recovery gate fails:

| Requirement | Result |
|---|---|
| All five values occur in authenticated measurements | Pass |
| Same operation/value type across digits | Fail |
| Terminal zero uniquely identifies FEFE | Fail |
| Concatenation/join selected by a clue | Fail |
| Independent five-digit recovery | **Fail** |

The source types are heterogeneous:

```text
atomic number, atomic number, atomic number, pixel count, binary class bit
```

The exact four `-2` steps are attractive, but after observing `8,6,4` the
continuation `2,0` is already predicted. Finding compatible measured values
afterward is constructor-style coherence, not a preregistered confirmation.

## Conditional decimal complement

If `86420` is nevertheless accepted and decimal nine's complement is chosen:

```text
86420
13579
-----
99999
```

This is exact but forced by the chosen operation. `13579` adds no independent
evidence. Forward interleaving gives the exact digit permutation:

```text
8163452709
```

No clue selects complement or interleaving as a consumer.

## Conditional a–i mappings

### Zero-based alphabet

With `a=0,...,i=8`:

```text
86420 -> igeca
1357  -> bdfh
9     -> out of range
```

Dropping `9` yields:

```text
igecabdfh
```

### One-based alphabet

With `a=1,...,i=9`:

```text
8642  -> hfdb
0     -> out of range
13579 -> acegi
```

Dropping `0` instead yields the symmetric alternative:

```text
hfdbacegi
```

Therefore `igecabdfh` is not convention-free. Zero-based indexing preserves
the full even rail by discarding odd terminal `9`; one-based indexing preserves
the full odd rail by discarding even terminal `0`.

Treating the invalid terminal as Enter, delimiter, escape, or control data
would be another unselected operation.

## Orientation family

After discarding one invalid terminal, the two parity subsets necessarily
partition all nine a–i symbols. Exact permutation status is therefore forced,
not evidentiary. Rail order and independent rail directions give eight natural
permutations:

```text
igecabdfh  igecahfdb  acegibdfh  acegihfdb
bdfhigeca  bdfhacegi  hfdbigeca  hfdbacegi
```

`igecabdfh` is one of eight and has no independent selector over the other
seven.

## Verdict

Promote only the source facts:

1. `OCBe -> 8,6,4`;
2. uppercase-G references `4,2` and their overlapping `4`;
3. the weaker Architect `he -> He -> 2` echo;
4. FEFE's real zero bit and its low palette specificity;
5. the exact conditional complement and alphabet calculations.

Do not promote `86420` as an authenticated instruction, `13579` as a second
rail, or `igecabdfh` as a checkerboard alphabet. The required five-digit gate
fails, and the alphabet result additionally drops an out-of-range terminal and
chooses one of eight orientations.

Reopen only if a new clue explicitly concatenates atomic numbers/counts/bits,
selects decimal nine's complement, or identifies the invalid terminal as a
control symbol.

## Reproduction

```bash
python3 tools/gsmg/first_piece_even_odd_alphabet_gate_audit.py --self-test
```
