#!/usr/bin/env python3
"""Phase 540 pilot: build the history-free dossiers and the frozen prompts.

Only the puzzle's own artifacts are used: page mirrors under doc/html, the
decrypted texts quoted in README.md, and constants in data.py. No project
phases, negative results, chat, or creator statements outside the pages.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from data import DBBI, FAED  # noqa: E402

ROOT = SCRIPT_DIR.parents[1]
OUT = ROOT / "_work" / "phase540_pilot"
PROMPTS = SCRIPT_DIR / "phase540_pilot_prompts.json"
PAGE_P2 = ROOT / "doc/html/choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecialdessertiwroteitmyself.html"
PAGE_FINAL = ROOT / "doc/html/89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32.html"
PAGE_SEED = ROOT / "doc/html/theseedisplanted.html"


def visible(path):
    s = path.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.S)
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', t)
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(re.sub(r"\s+", " ", t)).strip(), imgs


def readme_block(after, count):
    lines = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith(after))
    return "\n".join(lines[i:i + count])


def _architect_text():
    lines = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()
    start = next(k for k, l in enumerate(lines) if l.startswith("YOUR LIFE IS THE SUM"))
    end = next(k for k in range(start, len(lines)) if lines[k].startswith("```"))
    return "\n".join(lines[start:end])


ARCHITECT_3_2_1 = _architect_text()

MAIN = f"""# GSMG.IO 5 BTC puzzle: artifact dossier

This dossier holds the puzzle's own artifacts and nothing else. There is a 5 BTC
prize at address 1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe. The last stage is described
in the puzzle's own text as a regular Bitcoin private key ("half and better half").

## Stage 0: the first image
A 14x14 pixel-art grid (a white rabbit). Reading it from the top-left counter-clockwise
in a spiral, classifying black/blue as 1 and white/yellow as 0, gives the URL
`gsmg.io/theseedisplanted`. The grid has 24 coloured cells (15 blue, 9 yellow), which
fall on the byte boundaries of that URL, and exactly one off-white pixel (254,254,254).

## Stage 1: gsmg.io/theseedisplanted
Eight coloured icon fragments: war+ning, ca, dig i, lo (in a lock), crypto/gic, n you, t.
They resolve to "WARNING", "CAN YOU DIG IT" and the song "The Warning" by Logic. The
lyric line used as the passphrase was
`theflowerblossomsthroughwhatseemstobeaconcretesurface`. It unlocks the next page.

## Stage 2: the Phase 2/3 page
The page URL is `gsmg.io/choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecialdessertiwroteitmyself`.
The riddle is the sentence in the URL. Its answer, `causality`, is hashed with SHA-256; the
hex digest is the AES-256-CBC passphrase (OpenSSL, base64) for the next material.

## Stage 3: seven-part password
Seven answers concatenated with preserved case and no spaces, then SHA-256:
`causality`, `Safenet`, `Luna`, `HSM`, `11110`, a hex string decoding to text, and the
post-move chess FEN `B5KR/1r5B/2R5/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 b - - 0 1`.

## Stage 3.2: three clues
`jacquefresco`, `giveitjustonesecond` (Alice: "How long is forever? White Rabbit:
Sometimes, just one second."), `heisenbergsuncertaintyprinciple`. Concatenated, then
SHA-256, then used as the AES passphrase. Decrypted text, verbatim:

I've been waiting for you. You have many questions, and although the process has altered your consciousness, you remain irrevocably human. Ergo, some of my answers you will understand, and some of them you will not. Concordantly, while your first question may be the most pertinent, you may or may not realize it is also irrelevant.

... am I here? Wake up, you... I've designed you a beautiful strategic position. One for one, four for one.

[a block of box-drawing characters, an EBCDIC 1141 ciphertext]

[a 149-digit decimal string]

Raising the stakes without extra chances of winning. A fubcd-king & oracle-queen, thingky mvps, on a sad board but as wide as the first one seen.

[a base64 OpenSSL blob, "Salted__", unresolved]

### Stage 3.2.1 output (EBCDIC 1141 then Beaufort with key THEMATRIXHASYOU)
```
{ARCHITECT_3_2_1}
```

### Stage 3.2.2 output (keyed straddling checkerboard, alphabet FUBCDORA.LETHINGKYMVPS.JQZXW, escape digits 1 and 4)
IN CASE YOU MANAGE TO CRACK THIS THE PRIVATE KEYS BELONG TO HALF AND BETTER HALF AND THEY ALSO NEED FUNDS TO LIVE

## Route to the final page
`SHA-256("GSMGIO5BTCPUZZLECHALLENGE" + "1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe")` =
`89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32`, which is the URL path
of the final page (title "SalPhaseIon"; a second page, "Cosmic Duality", exists).

## The final page (SalPhaseIon): stream layout, in order
1. `DBBI`, 91 letters over a-i: `{DBBI}`
2. a binary block that decodes to the text `matrixsumlist`
3. `FAED`, 570 letters over a-i: `{FAED}`
4. a decimal block that decodes to `lastwordsbeforearchichoice`
5. a decimal block that decodes to `thispassword`
6. the literal text `sha256 our first hint is your last command`
7. the first half of a base64 OpenSSL "Salted__" AES blob (called SALPH), a binary block
   that decodes to `enter`, then the second half of the blob
8. the raw text `shabefanstoo`

A reversed binary message on the page decodes to the ordered phrase:
`yellowblueprimes matrixsumlist lastwordsbeforearchichoice yinyang wewontgiveawaythepassword itsinfrontofyoureyesbutyourenotseeingit verylaststepisatruegiveaway promised`

## The unsolved problem and how answers are checked
A passphrase for the SALPH blob (and the other encrypted blobs on the final pages) is
unknown. An automatic checker will try each candidate you give as a base phrase, in
several forms: the raw text, lowercase, spaces removed, the SHA-256 hex digest of these,
with and without a trailing newline. So give the phrase itself, not a hash. Earlier
passphrases were: a lyric line (Stage 1); the SHA-256 of a one-word riddle answer
(Stage 2); the SHA-256 of concatenated clue answers (Stages 3, 3.2). Every earlier
answer was a word or phrase recognizable from the clue text and general culture.
"""

R1 = """# Stage: the Phase 2 page

The page is served at
`gsmg.io/choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecialdessertiwroteitmyself`
and shows the following text (a base64 OpenSSL blob follows, omitted here):

{p2}

The blob is "Salted__" AES-256-CBC with a passphrase that is the SHA-256 hex digest of a
single base phrase. A checker tries your base phrase in several forms. Give the base phrase.
"""

R2 = """# Stage: gsmg.io/theseedisplanted

The page shows only eight coloured icon images and no text. Their filenames are:

{imgs}

The page is a gate: entering the right passphrase in a form opens the next page. The
passphrase is a single text string, tried in several case and spacing forms. Give the
base string exactly as it would be typed.
"""

TEMPLATE = """You are a fresh solver of the GSMG.IO 5 BTC puzzle. Your job is to generate candidate passphrases.

Rules:
- Read ONLY this file: {dossier}
- Do NOT read any other file on the filesystem, do NOT use web search or any network access, do NOT run code that reads other files. Use only the dossier and your own knowledge.
- Task: {task}
- Lens for this run: {lens}
- Produce at most {n} candidates. Each must have a distinct reason. Do not output trivial case, spacing or punctuation variants of the same phrase. Multi-word or concatenated answers are fine when motivated. Prefer specific, checkable strings over vague ones.
- Write the result with the Write tool to {out}. One JSON object per line: {{"candidate": "<base phrase as it would be typed>", "clue": "<which clue or artifact>", "reading": "<one sentence: why this is the answer>"}}
- An automatic checker tries every candidate against the real encrypted blobs. Agreement with other readers and cleverness count for nothing; only the check does.
- When done, reply with one line: the number of lines you wrote.
"""

AGENTS = {
    "A1": ("sonnet", "literal reader. Use only what is visible on the pages and decrypted texts, plus simple recombination (concatenation, order, case). Take the phrase 'it's in front of your eyes' literally."),
    "A2": ("opus", "Matrix trilogy scholar. Use scenes, characters, quotes, props, names and lore from the Matrix films (the Architect, the Oracle, the Keymaker, Neo's passport, Trinity, Morpheus, the Merovingian) to read the unresolved clue words."),
    "A3": ("fable", "creator-style modeler. From the solved chain, infer how this creator turns a clue into a passphrase (what kind of clue, what kind of answer, how answers are combined), then predict what the creator intends for the final page."),
    "A4": ("opus", "wordplay and riddle specialist. Consider acronyms, initials, anagrams, homophones, hidden words, literal extraction of the phrases the pages name (for example the actual last words before the word 'choice' in the Architect text), and name expansions."),
    "A5": ("sonnet", "semantic reader of the on-page macro message and of 'half and better half'. Ask what the ordered phrase yellowblueprimes ... promised, and the words yinyang and thispassword, mean as English and as concepts, and what a solver would type."),
    "A6": ("haiku", "minimalist. Give the shortest plausible answers: single words or two to three word phrases that a solver would recognize from the clues and general culture."),
}
MAIN_TASK = "propose passphrases for the unsolved final-page blob(s) described at the end of the dossier."
RETRO = {
    "R1": ("sonnet", "dossier_r1.md", "propose the base phrase that is the passphrase for the blob on this page.", "a general solver with no special lens", 150),
    "R2": ("opus", "dossier_r2.md", "propose the string that opens the next page from this gate.", "a general solver with no special lens", 150),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "out").mkdir(exist_ok=True)
    p2, _ = visible(PAGE_P2)
    p2 = p2[: p2.index("There's a guy who")].strip()
    p2 = p2[: p2.rfind(" ")] if len(p2) > 3000 else p2
    _, imgs = visible(PAGE_SEED)
    (OUT / "dossier_main.md").write_text(MAIN, encoding="utf-8")
    # drop the long base64 blob from the Phase 2 page text: keep the prose before the blob
    prose = p2.split("U2FsdGVkX1")[0].strip()
    (OUT / "dossier_r1.md").write_text(R1.format(p2=prose), encoding="utf-8")
    (OUT / "dossier_r2.md").write_text(R2.format(imgs="\n".join(Path(i).name for i in imgs)), encoding="utf-8")
    prompts = {}
    for name, (model, lens) in AGENTS.items():
        prompts[name] = {
            "model": model,
            "prompt": TEMPLATE.format(dossier=OUT / "dossier_main.md", task=MAIN_TASK, lens=lens, n=250, out=OUT / "out" / f"{name}.jsonl"),
        }
    for name, (model, dossier, task, lens, n) in RETRO.items():
        prompts[name] = {
            "model": model,
            "prompt": TEMPLATE.format(dossier=OUT / dossier, task=task, lens=lens, n=n, out=OUT / "out" / f"{name}.jsonl"),
        }
    PROMPTS.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {k: len((OUT / k).read_text()) for k in ("dossier_main.md", "dossier_r1.md", "dossier_r2.md")}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
