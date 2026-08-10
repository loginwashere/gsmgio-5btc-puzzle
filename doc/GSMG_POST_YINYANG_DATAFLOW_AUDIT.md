# GSMG Post-Yin-Yang Dataflow Audit

> **Phase-223 condition:** BUT/HYE remains exact, but its partial mirror9
> reading does not independently establish that `yinyang` has been reached.
> The FAED role ranking below is therefore conditional on a transition still
> lacking mechanical validation.

## Question

Given the corrected working checkpoint

```text
574061 -> [23,16,7] -> BOTH/ULTIMATELY/THE -> BUT/HYE -> yinyang
```

what authenticated object can supply the page's decoded `thispassword`
instruction?

## Exact local order

The archived textarea remains:

```text
DBBI
[binary matrixsumlist]
FAED
[decimal lastwordsbeforearchichoice]
[decimal thispassword]
[sha256 our first hint is your last command]
SALPH-prefix
[binary enter]
SALPH-suffix
[sha256 + unresolved anstoo]
```

Under the Phase-217 default, `matrixsumlist` and
`lastwordsbeforearchichoice` are consumed by the prime-to-BUT/HYE recognition
route. That changes their preferred role from local operators on adjacent
ciphertext to decoded clue steps, but it does not erase DBBI or FAED.

## Surviving password roles

| Proposed source | Current status | Reason |
|---|---|---|
| Literal BUT/HYE recognition output | Closed for direct literal forms only | Phase 33 tested the selected words/rails/EOL family: 216 CBC keystrings and 306 Key-Wrap attempts across four blobs, zero hits. No different operation is selected. |
| Literal seven words before `choice` | Closed direct negative | Phase 216 and a fresh rerun: 36 keystrings, four blobs, zero hits. |
| Exact first-hint/last-command materials | Closed bounded direct negative | Fresh rerun of nine source-grounded operands and 162 literal/SHA/double-SHA/newline materials: four blobs, zero hits. The referents of “our” and “last command” remain linguistically ambiguous beyond that bounded set. |
| Decoded FAED result | **Live, decoder unknown** | Once the two clue instructions are consumed externally, FAED is the nearest preceding undecoded payload to `thispassword`. |
| Joint DBBI/FAED result | **Live, operator unknown** | Both a-i streams occur before `thispassword`; yin-yang could name their relationship, but no alignment or combining operation is authenticated. |

The circular `H | YE | BUT` construction and post-hoc VAT/SALVATION rebus are
excluded and contribute nothing to this ranking.

## Result

The strongest local dataflow is now:

```text
FAED -> unknown decode -> thispassword -> adjacent SHA/SALPH region
```

with a joint DBBI/FAED result as the surviving alternative. This is not a
solution or a recovered decoder. Four dependencies remain open:

1. how BUT/HYE or yin-yang selects a FAED decoder;
2. whether DBBI participates in that decoder;
3. whether the explicit SHA command consumes the decoded password or its own
   literal “first hint / last command” operand;
4. what raw `anstoo` means.

The audit therefore rejects another password-format sweep. The next useful
investigation must constrain the FAED or DBBI/FAED relationship itself. Any
candidate should first explain the page order and yield a recognizable
plaintext; AES success must remain a confirmation rather than the selector.

## Reproduction

```bash
python3 tools/gsmg/post_yinyang_dataflow_audit.py --self-test
python3 tools/gsmg/post_yinyang_dataflow_audit.py --oracle
```

The second command reruns only the two bounded direct families described
above. It does not rerun the historical Phase-33 rail family or generate new
password variants.
