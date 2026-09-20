#!/usr/bin/env python3
"""Phase 541 (pilot round 2): build the changed dossier, the data file and the prompts.

The dossier is the round-1 dossier plus closed-system derived facts (reconstructions
computed from the puzzle's own artifacts), a short list of already-tested operation
families, and the operation-proposal interface. Everything derived is recomputed here
from repository code and result files, not typed by hand.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from data import DBBI, FAED, VALIDATION_ANSWER  # noqa: E402
import phase540_pilot_build as r1  # noqa: E402
from phase386_btcseed_bifid_faed_decode_audit import bifid_decrypt, build_grid  # noqa: E402
from phase539_base9_scalar_all_bijections import target_strings  # noqa: E402
from phase538_faed_lane_extraction import build_masks  # noqa: E402

ROOT = SCRIPT_DIR.parents[1]
OUT = ROOT / "_work" / "phase541_round2"
PROMPTS = SCRIPT_DIR / "phase541_round2_prompts.json"
P525 = SCRIPT_DIR / "phase525_selection_a_result.json"
P535 = SCRIPT_DIR / "phase535_selection_a_matrix_result.json"
SYMS = "abcdefghi"


def facts():
    masks = build_masks()
    strings = target_strings()
    ans = VALIDATION_ANSWER
    m31 = masks["M31"]
    sel = "".join(ans[p - 1] for p in m31["H"]).lower()
    comp = "".join(ans[p - 1] for p in m31["C"]).lower()
    blue = "".join(ans[p - 1] for p in m31["Hb"]).lower()
    yellow = "".join(ans[p - 1] for p in m31["Hy"]).lower()
    square, grid, pos = build_grid("".join(dict.fromkeys(DBBI.upper())))
    btcseed = bifid_decrypt(FAED, pos, grid)
    p525 = json.loads(P525.read_text(encoding="utf-8"))
    p535 = json.loads(P535.read_text(encoding="utf-8"))
    events = [
        [e["event_rank"], e["kind"], e["source_byte"], e["character"], e["color"], e["spiral_0"], e["row_1"], e["column_1"]]
        for e in p525["picture_events"]
    ]
    sel_a = next(r for r in p535["rows"] if r["logical_length"] == 84 and r["omitted_event_ranks"] == [22, 25])
    variant = sel_a["variants"][0]
    zero = {c["name"]: {"row_sums": c["row_sums"], "output": c["output"]} for c in p535["selection_a_zeroing_comparison"]}
    counts = {c: FAED.count(c) for c in SYMS}
    return {
        "masks": masks, "P83": strings["P83"], "P84": strings["P84"], "answer": ans,
        "selected31": sel, "complement60": comp, "single_rail": blue, "pair_rail": yellow,
        "square": square, "btcseed": btcseed, "events": events,
        "matrix": {"row_sums": variant["row_sums"], "output": variant["output"], "unplaced_tail": sel_a["unplaced_tail"],
                   "endpoints_zero_based": sel_a["endpoints_zero_based"], "zeroing": zero},
        "faed_counts": counts,
    }


def data_json(f):
    r = {
        "DBBI": DBBI,
        "FAED": FAED,
        "ANSWER_322": f["answer"],
        "ARCH_321": r1.ARCHITECT_3_2_1,
        "PAGE_STRINGS": {
            "matrixsumlist": "matrixsumlist",
            "lastwordsbeforearchichoice": "lastwordsbeforearchichoice",
            "thispassword": "thispassword",
            "lastcommand": "sha256 our first hint is your last command",
            "enter": "enter",
            "tail": "shabefanstoo",
            "macro": ["yellowblueprimes", "matrixsumlist", "lastwordsbeforearchichoice", "yinyang",
                      "wewontgiveawaythepassword", "itsinfrontofyoureyesbutyourenotseeingit",
                      "verylaststepisatruegiveaway", "promised"],
            "url_seed": "gsmg.io/theseedisplanted",
        },
        "P83": f["P83"], "P84": f["P84"],
        "MASK31": f["masks"]["M31"]["H"], "MASK30": f["masks"]["M30"]["H"],
        "EVENTS": f["events"],
        "MATRIX_SELECTION_A": {"row_sums": f["matrix"]["row_sums"], "output": f["matrix"]["output"]},
        "BTCSEED_DECODE": f["btcseed"],
    }
    return r


def facts_md(f):
    m31, m30 = f["masks"]["M31"], f["masks"]["M30"]
    return f"""
## Derived facts (reconstructions from the artifacts above; use them, verify if you like)

**D1. DBBI has a prime-position scaffold.** Read DBBI as tokens at logical positions
1, 2, 3, ...: at a prime logical position the token is `b` (one character) or `be`
(two characters); at every other position it is one character. Exactly two complete
parses of the 91 characters exist: an 83-token parse (23 hosts: 15 `b` and 8 `be`) and
an 84-token parse (23 hosts: 16 `b` and 7 `be`; its last `e` is an unhosted token).
Raw 1-based host positions, 83-token parse (31 positions):
`{" ".join(map(str, m31["H"]))}`
84-token parse (30 positions): the same list without 91. The non-host symbols in stream order:
- 83-token payload (60): `{f["P83"]}`
- 84-token payload (61): `{f["P84"]}`

**D2. The first image supplies the same structure.** Its 24 coloured cells read in spiral
order, plus the off-white cell (`F`, the single FEFE pixel, at 0-based spiral index 163, inserted
before colour object 21), give a 25-event sequence of colours `BBBBYBBBYYBBBBYBBYYBFYYBY`
(B blue, Y yellow). The 84-token parse's host kinds (blue = `b`, yellow = `be`) match events
1 to 23 with events 22 and 25 omitted (the FEFE cell stands for byte 21). Events
`[rank, kind, source byte, character, colour, spiral index (0-based), row, column]`:
`{json.dumps(f["events"])}`
Yellow read as 1 and blue as 0 over the 24 cells gives the binary value 574061, which is prime.

**D3. The same walk, applied to the Stage 3.2.2 answer.** Selecting the 83-token host
positions above from the 91-character answer gives `{f["selected31"]}`; the 60
remaining letters are `{f["complement60"]}`; one-character hosts give `{f["single_rail"]}`,
two-character hosts give `{f["pair_rail"]}` (16 letters; the one-character rail has 15, of which 14 are
blue and one is the FEFE cell, so 7 blue pairs). The numbers 23 (hosts), 16 and 7 also appear in the
Stage 3.2.1 text as 23 ciphers, 16 encryptions and 7 passwords.

**D4. Matrix placement.** Placing the 84-token parse's host chunks backwards from their
image endpoints on the 14x14 spiral, with values a=1..i=9 and `be`=25, and summing rows, gives
row sums `{f["matrix"]["row_sums"]}`. Rendered as letters A0 mod 26 (A=0) this is `{f["matrix"]["output"]}`.
The unhosted final `e` stays unplaced. Hosts only give `{f["matrix"]["zeroing"]["host_only"]["output"]}`
(row sums {f["matrix"]["zeroing"]["host_only"]["row_sums"]}); payload only gives
`{f["matrix"]["zeroing"]["payload_only"]["output"]}` (row sums {f["matrix"]["zeroing"]["payload_only"]["row_sums"]}).

**D5. A Bifid reading of FAED.** Take DBBI's nine symbols in order of first appearance,
then the rest of the alphabet without J, as a 5x5 square: `{f["square"]}`. Bifid-decrypt the whole
570-letter FAED as one block (row-column coordinates): the 570 letters begin `BTCSEED`, then
`{f["btcseed"][7:120]}...`. The only `Z` is at 0-based index 97. The letters `B C D E` make up 57% of the output.

**D6. Sizes and counts.** DBBI = 91 = 7x13 = 1+2+...+13. FAED = 570 = 6x91 + 24 = 2x285.
`matrixsumlist` decodes from a 104-bit block (13x8); DBBI plus that block is 195 = 14x14 - 1.
FAED letter counts: {json.dumps(f["faed_counts"])}. FAED's best-scoring escape pair (for a
straddling checkerboard) is `g,i`; DBBI's is `b,e`.

## Already tested (do not just repeat these)

Password products from the strings above and their recombinations; DBBI-derived coordinates
and positions as passwords; the matrix placement and its row sums as word indices into the
Architect scene; numeric-text generators and arithmetic position functions over the payload; the
payload and whole DBBI as base-9 private-key scalars under every digit bijection; FAED's six
91-symbol lanes read through the host masks; joint DBBI plus FAED splice and shared-board
decodes; straddling-checkerboard, Bifid and VIC decodes of FAED across escape pairs, boards and
widths; the Bifid tail as key or seed material. Propose something outside these.

## Interface for operation proposals

A proposal is a Python function that receives a dict `data` and returns a list of strings.
`data` keys: `DBBI`, `FAED`, `ANSWER_322` (the 91-letter answer), `ARCH_321` (the Stage 3.2.1
text), `PAGE_STRINGS` (dict of the page's decoded strings and the macro phrase list), `P83`, `P84`,
`MASK31`, `MASK30`, `EVENTS`, `MATRIX_SELECTION_A` (dict `row_sums`, `output`), `BTCSEED_DECODE`.
Rules: standard library only, and only these imports: math, itertools, string, re, collections,
hashlib, base64, binascii, functools, struct, operator, textwrap. No files, network, `eval`, `exec`,
`open`, `getattr`, `type`, or names or strings containing two underscores. It must finish in 20
seconds and return at most 3,000 strings. The first 1,000 returned strings (200 characters or fewer)
are tried as passphrases; all returned strings are scanned for private-key shapes (64-hex, WIF, BIP39
mnemonic, 64 raw bytes) and checked against the prize address, the halving address and their EC neighbors. Each proposal must say which check would confirm
it and which earlier solved stage used a similar operation.
"""


def dossier_v2(f):
    return r1.MAIN + facts_md(f)


TEMPLATE = """You are a fresh solver of the GSMG.IO 5 BTC puzzle. You generate two kinds of output for an automatic checker.

Rules:
- Read ONLY this file: {dossier}
- Do NOT read any other file on the filesystem, do NOT use web search or any network access, do NOT run code that reads other files. You may run Python to test your own function, but only on values you copy from the dossier.
- Lens for this run: {lens}
- Output 1 (operations): at most 10 proposals, written with the Write tool to {ops}. One JSON object per line: {{"name": "...", "idea": "<2-3 sentences: what is done and why the puzzle text licenses it>", "inputs": ["<data keys used>"], "check": "<which automatic check would confirm it>", "retro": "<earlier solved stage that used a similar operation, or none>", "code": "def run(data):\\n    ...\\n    return [<strings>]"}}. Each proposal must be a genuinely different operation, not a variant of another. The dossier lists what is already tested and the exact interface.
- Output 2 (passphrases): at most 150 candidates, written to {cands}, one JSON object per line: {{"candidate": "<base phrase as typed>", "clue": "<clue or fact>", "reading": "<one sentence>"}}. No trivial case or spacing variants.
- The checker runs your code exactly as written and tries every returned string against the real encrypted blobs and address targets. It never repairs code. Agreement with other readers and cleverness count for nothing; only the check does.
- When done, reply with one line: the number of operation lines and candidate lines you wrote.
"""

AGENTS = {
    "B1": ("opus", "classical cryptographer. Propose operations that use DBBI-derived material (parse, masks, payload, square) as keys, keywords, keystreams or selectors for classical ciphers applied to other artifacts in the dossier, in ways the creator has already used (Beaufort, VIC/checkerboard, Bifid, Caesar/Vigenere-style, columnar)."),
    "B2": ("sonnet", "grid and addressing reader. Use the 14x14 spiral, the 25 events, the masks, and the 7x13 and 6x91+24 layouts to address, fold or overlay other artifacts (the answer, the Architect text, FAED lanes, the matrix). Prefer operations where the structure itself picks the positions."),
    "B3": ("sonnet", "numbers and bases. Use the counts 23/16/7, the primes, 574061, the row sums, sizes and arithmetic on the strings to produce numbers, then render them as text (A1Z26, ASCII, base conversions, mod 26) in creator-plausible ways."),
    "B4": ("opus", "text-extraction reader. Use the derived structures as indices or masks over the Architect texts, the Stage 3.2 texts and the answer to extract words or letters (first, last, nth, before or after the word 'choice'), then assemble passphrases."),
    "B5": ("opus", "consumer-first thinker. Start from the final page's own instructions (thispassword, sha256 our first hint is your last command, enter, shabefanstoo) and work backwards: what exact string is hashed or typed, and which of the derived facts could supply it."),
    "B6": ("sonnet", "interpretive reader of the derived facts. Ask what the creator intends by the literal words that emerge (yang, salvation, the BTCSEED prefix, the 31 letters, the payload) and what a solver would type; propose operations only where an interpretation implies one."),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "out").mkdir(exist_ok=True)
    f = facts()
    (OUT / "dossier_v2.md").write_text(dossier_v2(f), encoding="utf-8")
    (OUT / "data.json").write_text(json.dumps(data_json(f), sort_keys=True), encoding="utf-8")
    prompts = {}
    for name, (model, lens) in AGENTS.items():
        prompts[name] = {
            "model": model,
            "prompt": TEMPLATE.format(dossier=OUT / "dossier_v2.md", lens=lens,
                                      ops=OUT / "out" / f"{name}.ops.jsonl", cands=OUT / "out" / f"{name}.cands.jsonl"),
        }
    PROMPTS.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"dossier_chars": len((OUT / "dossier_v2.md").read_text()), "data_keys": sorted(json.loads((OUT / "data.json").read_text()))}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
