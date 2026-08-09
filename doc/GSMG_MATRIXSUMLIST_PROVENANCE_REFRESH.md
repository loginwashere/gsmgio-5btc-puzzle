# GSMG `matrixsumlist` Provenance Refresh

**Date:** 2026-08-09  
**Question:** does any recovered primary source uniquely specify what
`matrixsumlist` does to `ncsyangcahiriasogaleafayanestve`?

## Result

No. The source and input gates remain strong, but the operation gate still
fails. No transform or AES trial is authorized by the strict transition
worksheet.

```text
yellowblueprimes
-> exact 31-position DBBI selection
-> ncsyangcahiriasogaleafayanestve
-> matrixsumlist
-> UNKNOWN OPERATION
```

## Evidence recovered

### 1. Creator-authored material

Telegram message `8446` was posted by `Jrk Bgrt` (`user9815232`) on
2023-02-24. Reversing its complete 1,288-bit stream and then decoding bytes
reproduces the continuous macro clue beginning:

```text
yellowblueprimesmatrixsumlistlastwordsbeforearchichoiceyinyang...
```

This authenticates the word and its order in the macro clue. Across all 294
ordinary-text `matrixsumlist` hits in the 57,729-message full export, however,
there are zero creator-authored hits. The creator also never posts Denis's
exact 31-character selection. The binary clue therefore supplies no visible
spaces, dimensions, traversal, indexing convention, or definition of “sum
list.”

The SalPhaseIon page itself is stronger evidence for locality: binary ASCII
`matrixsumlist` lies exactly between DBBI and FAED. It still permits at least
three grammatical roles already catalogued in Phase 101: postfix to DBBI,
prefix to FAED, or an infix relationship between both.

### 2. The recovered yellow/blue guide

The recovered guide is a real community artifact, not creator confirmation.
Its direct reply neighborhood records three important limitations:

- the author answers that the segmentation was made **“To match all prime
  positions”** after being challenged that a character was included “just to
  match the pattern”;
- for FAED, the author says he **“don't have such pattern”**;
- the author later reports **“nothing more”** had been found.

The guide's actual matrix mechanic is fixed for its own DBBI construction: a
14×14 placement followed by row sums, producing `IZLKESEEDQPPEN`. It does not
consume the later 31-character selection, and it does not open an authenticated
next stage.

### 3. Historical community code

Telegram message `33950`, posted by `𝔻𝕖𝕦𝕤 ℕ𝕒𝕞𝕖`
(`user1571850682`) on 2024-12-10, attaches
`files/696783482-puzzle-1.txt`:

```text
sha256=b6cbab2b55a83e1bbd993c33596b4d732155a8fe9e26c1a922cb8db3de63f0c5
```

It gives one explicit programming definition:

```python
row_sums = [sum(row) for row in matrix]
col_sums = [sum(col) for col in zip(*matrix)]
matrix_sum_list = row_sums + col_sums
```

This is useful provenance for a community interpretation, but it cannot fill
G3. It uses a different, much larger input; it does not contain the selected
31 characters; and its row-plus-column rule differs from the later guide's
row-only consumption. No creator reply selects it.

The public walkthrough history is similarly limited. The 2021 README already
decoded the standalone binary ASCII word `matrixsumlist`, but documented no
consumer operation for it.

### 4. Matrix passage and *Cosmic Duality*

The exact “YOUR LIFE IS THE SUM...” language comes from the already-solved
Phase 3.2.1 plaintext. That plaintext contains one `SUM`, zero `MATRIX`, and
zero `CHOICE`. Denis's later bridge to the Architect scene is coherent
community interpretation, not a typed instruction.

The current full-book transcription contains no `matrixsumlist` phrase and no
“your life is the sum” phrase. It still has a physical gap between the p.56
and p.59 transcriptions. The source photograph was re-opened directly:

```text
/home/loginwashere/Pictures/Screenshots/Screenshot from 2026-07-12 14-44-39.png
sha256=19c3ccfd31257d9832884d1d7a1011cf44423e2903c6c51bb5f831a761cbeaa8
```

It visibly places printed p.56 directly beside printed p.59; pages 57–58 are
the unphotographed inner faces of the closed gatefold, not merely an OCR
omission. That is a genuine uninspected primary artifact, but absence of those
pages does not license guessing their contents.

### 5. Incremental export through 2026-08-09

The latest valid GSMG export contains 1,026 messages from 2026-07-25 through
2026-08-09 12:35:14. The relevant new discussion is entirely community
authored:

| Message | Proposal | Evidence status |
|---|---|---|
| `67787` | Four-component SalPhaseIon password assembly | Author reports about 240,000 negative combinations; no canonical sub-answer set |
| `67789` | `we won't -> we will -> rockyou.txt` | Reply theory with several semantic substitutions; no fixed relation to the 31 characters |
| `68021` | Pair `matrixsumlist` with `enter` as a repeated method | Names a pairing but never specifies the method or operand |
| `68057` | “you have cracked the matrix sum list” joke | No derivation or output |
| `68249` | Uses `matrixsumlist` inside the disputed COSMIC checkpoint pipeline | Community/spam-linked construction; not independent puzzle evidence |

There are zero creator-authored relevant messages in this export window.

## Strict worksheet decision

| Gate | Status | Reason |
|---|---|---|
| G1 — source | **PASS / PARTIAL** | Creator authenticates the literal word and ordering; proposed mechanics are community-only |
| G2 — input | **PASS** | Exact 31-character selection is reproducible |
| G3 — operation | **FAIL** | No source fixes dimensions, traversal, character values, sum type, indexing, or DBBI/FAED scope |
| G4 — output | **FAIL** | No independently authenticated next-stage object |
| G5 — controls | **PARTIAL** | Multiple bounded consumers are negative, but there is no selected candidate to calibrate |

## Next evidence actions

1. Photograph pages 57–58 of the physical *Cosmic Duality* book with the
   gatefold fully open; preserve image hashes and transcribe them separately.
2. Ask one targeted community question requesting a pre-output source—not a
   proposed solve—that fixes all of: input, matrix dimensions, traversal,
   character values, and whether the result is row sums, column sums, both, or
   indices.
3. Reopen computation only if one of those sources reduces the surviving G3
   alternatives to exactly one.

## Reproduction

```bash
python3 tools/gsmg/matrixsumlist_provenance_refresh_audit.py --self-test
```
