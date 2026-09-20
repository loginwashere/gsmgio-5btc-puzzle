# Phase 541 — fresh-context agents, round 2: derived facts and operation proposals

Status at creation: protocol, written before any round-2 agent was started and before
any round-2 output exists. Dossier, data file, prompts, harness and this protocol are
hashed into `tools/gsmg/phase541_round2_lock.json` before the first agent runs.

## Why a second round is licensed

Phase 540 closed round 1 for its dossier: 848 interpretation-type candidates from six
lenses, zero oracle hits. Its reopen condition was a changed dossier or a new
constraint on which readings to generate. This round supplies both: the agents see, for
the first time, the closed-system objects this project reconstructed from the artifacts
(prime-host parse and payload strings, the image's 25-event sequence, the 31-letter
selection, the Selection A matrix, the Bifid reading of FAED, size coincidences), and
they must produce operation proposals as executable code with a named check, alongside
passphrase candidates. It is still a method pilot. No candidate is promoted by agreement.

## Design (frozen)

**Dossier v2** = the round-1 dossier, plus six derived facts recomputed from repository
code and result files (`phase541_round2_build.py`), a short list of already-tested
families ("propose something outside these"), and the operation interface. No other
project results, no chat, no creator statements outside the pages.

**Six agents, one prompt each, one round:**

| Agent | Lens | Model |
|---|---|---|
| B1 | classical cryptographer: DBBI-derived keys and selectors for classical ciphers on other artifacts | opus |
| B2 | grid and addressing: the 14x14 spiral, events, masks and 7x13 / 6x91+24 layouts as addressing | sonnet |
| B3 | numbers and bases: counts, primes, 574061, row sums, rendered as text | sonnet |
| B4 | text extraction: structures as indices or masks over the Architect texts and the answer | opus |
| B5 | consumer-first: work backwards from the page's own instructions to the string hashed or typed | opus |
| B6 | interpretive reader of the derived facts (yang, salvation, BTCSEED, the 31 letters, the payload) | sonnet |

The Fable model is not used (spend limit). Each agent writes at most 10 operation
proposals (JSON lines with name, idea, inputs, named check, earlier solved stage that
used a similar operation, and Python `run(data)` code) and at most 150 passphrase
candidates.

## Execution and exact bar

1. **Static check** every proposal: only whitelisted imports (math, itertools, string, re,
   collections, hashlib, base64, binascii, functools, struct, operator, textwrap), no
   file, network, `eval`, `exec`, `open`, `getattr`, `type`, or dunder names or strings.
2. **Run** every accepted proposal exactly as written in a separate isolated Python
   process (empty environment, CPU and memory limits, no file writes, 30 s wall clock,
   at most 3,000 returned strings). Failures are recorded and never repaired.
3. **Key-shape scan** every returned string and every candidate (64-hex, WIF, BIP39
   mnemonic, 64 raw bytes via the project's `classify_body`), derive both address
   encodings, and compare with the eleven target hash160s of Phase 539 (prize in two
   encodings, halving address, eight EC neighbors). Bloom hits are counted as context only.
4. **Oracle:** the union of candidates and the first 1,000 returned strings per proposal
   (at most 6,000 per agent, 200 characters or fewer, deduplicated) is run through the GPU
   oracle exactly as in Phase 540 (60-variant table, all four tracked blobs,
   `--newline-variants`, Bloom raw-key arm, known-target detector).
5. **Exact hit:** any strong or structural oracle record, any known-target match, or any
   key-shape hit against the eleven targets. Weak rows are reported and classified with the
   Phase 524 method and do not count. A hit is a candidate password or key for separate
   validation and is never printed or committed.

**Reported, not gated:** per agent, proposals written, statically rejected, run failures,
outputs returned, bases tried, novelty against round 1, key-shaped string counts.

## Controls (before the lock)

Static check accepts a clean function and rejects imports, `open`, `eval`, dunder access,
`getattr` and a missing `run`; the sandbox returns normal output, times out an infinite
loop, records exceptions and non-list returns, caps output, and blocks a runtime import;
a planted key (as hex64 and as WIF) is flagged against a synthetic target and not against
the real targets, and an unrelated hex64 is not flagged; the data file reproduces the
Phase 539 payload strings, the Phase 48 mask, the 31-letter selection, the 570-letter Bifid
reading beginning `BTCSEED`, 25 events and the Selection A output; an end-to-end run with
one good, one rejected and one non-terminating proposal produces the expected counts and
one exact key-shape hit.

## Stop rule

One round, one prompt per agent. No repair of agent code, no second prompt from any
result, no cherry-picking before the oracle. If a model call fails before writing, it may
be rerun once with the identical prompt and disclosed. Zero exact hits closes only round
2 for this dossier. A round 3 needs a changed dossier or a new constraint, not more
agents or wider lenses.

## Non-claims

Agents know public write-ups of this puzzle from training. A result they produce is not
evidence of independent insight until an exact bar confirms it. The sandbox (import
whitelist, static checks, resource limits, empty environment, no file writes) is a
guard against accidents, not a security boundary against deliberately adversarial code;
an unprivileged network namespace was not available. Agent code runs only on the
dossier's own data.

## Reproduction

```bash
python3 tools/gsmg/phase541_round2_build.py
python3 tools/gsmg/phase541_round2_exec.py --self-test
python3 tools/gsmg/phase541_round2_exec.py --lock
# after the agents run:
python3 tools/gsmg/phase541_round2_exec.py --collect
python3 tools/gsmg/phase541_round2_exec.py --verify-oracle
```
