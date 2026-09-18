#!/usr/bin/env python3
"""Phase 523 -- house-style slot-grammar password product for SALPH: overlap
audit only (zero oracle calls).

Pre-registration for the "brute-force the password grammar, not the cipher"
lane (session 2026-09-18). The lane's premise: every solved AES stage used
`SHA-256(concatenated riddle answers)` as its passphrase, the SalPhaseIon page
repeats that instruction twice (`sha256 ...`, `shabefanstoo`), and the
creator's macro fixes the riddle order
`yellowblueprimes -> matrixsumlist -> lastwordsbeforearchichoice -> yinyang`.
So the closed-system candidate universe is: one already-authenticated
checkpoint value per macro slot (or the slot omitted), joined in macro order
under the solved-stage assembly conventions, then expanded through the
project's standard `answer_forms() x keystr_forms(newline_variants=True)`
passphrase forms.

This script does NOT query any blob. It answers one question: which of those
passphrase materials have already been tried against SALPH by a prior sweep
(exact material-string membership against each prior corpus, expanded the way
that sweep's own record says it expanded), and which are genuinely new. The
later, separate execution phase consumes the manifest this script writes.

Why an exact oracle changes the discipline: the SALPH detector is PKCS#7 +
printable-z / exact 64-byte full-pad shape, with a per-attempt false-accept
rate far below 1e-9 (cb_common docstrings, Phase 270). For a detector like
that, exhausting a bounded, pre-declared product is not multiple-testing
creep -- that objection applies to statistical scores, not to exact-match
locks. What the pre-registration still has to guarantee is that the value
sets are closed BEFORE anything runs and are drawn only from authenticated
checkpoint outputs -- hence the source tag on every value below.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
WORK_DIR = REPO_ROOT / "_work" / "phase523"
SRT_PATH = REPO_ROOT / "wordlists" / "matrix" / "the-matrix-reloaded-2003.en.srt"
sys.path.insert(0, str(SCRIPT_DIR))

# Only the two pure form-expansion helpers are imported from cb_common. No
# decrypt/oracle function is imported anywhere in this module, by design.
from cb_common import answer_forms, keystr_forms  # noqa: E402
from extended_cipher_recheck import WORDLIST_DIR, load_curated_candidates  # noqa: E402
from first_piece_prime_sum_reconstruction import (  # noqa: E402
    EXPECTED_EVENT_TYPES,
    EXPECTED_FITTED_SUMS,
    first_primes,
    is_prime,
)
from denis_prime_extraction_audit import TARGET as SELECTED_31  # noqa: E402
from prime_matrixsum_reconstruction import EXPECTED_PRIME, EXPECTED_SUM_LIST  # noqa: E402
from promised_standalone_audit import MACRO_CLUE  # noqa: E402
from lastcommand_probe import CANDIDATES as LASTCOMMAND_CANDIDATES  # noqa: E402
from phase32_monologue_residual_audit import RESIDUAL_CANDIDATES  # noqa: E402
from architect_hye_bye_audit import candidate_keystrings as hye_bye_keystrings  # noqa: E402
from phase3_chain_full_text_p32_sweep_audit import candidate_sentences  # noqa: E402
from salph_cosmic_phase341_eligibility_audit import frozen_manifest as p372_manifest  # noqa: E402
from binary_hint_operand_audit import operand_materials, EXPECTED_FIRST_HINT_PRIME  # noqa: E402
from ciao_selection_coverage_audit import CANDIDATES as CIAO_CANDIDATES  # noqa: E402
from salphaseion_title_rebus_audit import fixed_candidates as title_rebus_candidates  # noqa: E402
from architect_choice_literal_password_audit import candidates as architect_literal_candidates  # noqa: E402
from remaining_structural_avenues_audit import ATOMIC_CANDIDATES, BOOK_CANDIDATES  # noqa: E402
from door_prime_passport_probe import CANDIDATES as DOOR_PROBE_CANDIDATES  # noqa: E402
from second_prime_matrixsumlist_audit import derived_candidates as second_prime_derived  # noqa: E402
from flower_prefix_checkpoint_audit import derived_candidates as flower_prefix_derived  # noqa: E402

# ---------------------------------------------------------------------------
# 1. Closed slot value sets. Every value carries the ledger/phase that
#    authenticates it as a checkpoint output. Nothing here is invented for
#    this phase; the only construction is "serialize an established list".
# ---------------------------------------------------------------------------

SLOT_ORDER = ("yellowblueprimes", "matrixsumlist", "lastwordsbeforearchichoice", "yinyang")
SLOT_SHORT = {"yellowblueprimes": "YBP", "matrixsumlist": "MSL",
              "lastwordsbeforearchichoice": "LWB", "yinyang": "YY"}

# Assembly conventions taken from the three solved AES boundaries (Phase 341,
# solved_boundary_rule_audit.py): riddle-order concatenation, no separator
# (primary). The page renders every token space-separated, so a single space
# join is the one hedge axis. Casing/alpha-only/SHA/newline are not axes here
# because the standard answer_forms x keystr_forms expansion already covers
# them exactly as every prior sweep did.
SEPARATORS = (("connected", ""), ("spaced", " "))

ARCHITECT_FINAL_SENTENCE = "as you adequately put the problem is"  # film + screenplay stable, Phase 216


def prime_lists():
    """Blue / yellow / FEFE prime lists of the fitted 23-event prime walk
    (first_piece_prime_sum_reconstruction, sums 401/400/73)."""
    primes = first_primes(len(EXPECTED_EVENT_TYPES))
    fitted = EXPECTED_EVENT_TYPES[:23]
    groups = {"B": [], "Y": [], "F": []}
    for prime, event in zip(primes, fitted):
        groups[event].append(prime)
    sums = {k: sum(v) for k, v in groups.items()}
    if sums != EXPECTED_FITTED_SUMS:
        raise AssertionError(f"prime-walk sums drifted: {sums} != {EXPECTED_FITTED_SUMS}")
    return groups


def architect_last_words():
    """Last N words (N=1..7) before the Architect's own `choice`, from the
    seven-word final sentence both frozen sources agree on (Phase 216)."""
    words = ARCHITECT_FINAL_SENTENCE.split()
    return [" ".join(words[-n:]) for n in range(1, len(words) + 1)]


def slot_values():
    groups = prime_lists()
    blue, yellow = groups["B"], groups["Y"]
    ybp = [
        ("574061", "F-CHAIN-001 first-piece prime (yellow=1)"),
        ("08C26D", "clue ledger 2020-01-14: hex of the yellow=1 reading"),
        ("F73D92", "clue ledger 2020-01-14: rose RGB (blue=1)"),
        ("311027", "F-CHAIN-019 quarter-turn prime"),
        ("04BEF3", "G-FLOWER-001 hex of 311027"),
        ("000010001100001001101101", "first_piece_color_candidates.txt 24-bit yellow=1 string"),
        ("111101110011110110010010", "first_piece_color_candidates.txt 24-bit blue=1 string"),
        ("163", "clue ledger 2021-04-01: FEFE zero-based spiral index (prime)"),
        ("1421", "creator hint {1},{4},{21} digits"),
        ("1,4,21", "creator hint {1},{4},{21} literal"),
        (",".join(map(str, blue)), "fitted prime walk: blue primes, comma list (sum 401)"),
        ("".join(map(str, blue)), "fitted prime walk: blue primes, concatenated"),
        (",".join(map(str, yellow)), "fitted prime walk: yellow primes, comma list (sum 400)"),
        ("".join(map(str, yellow)), "fitted prime walk: yellow primes, concatenated"),
        ("yellowblueprimes", "macro label (message 8446)"),
    ]
    a, b, c = EXPECTED_SUM_LIST
    msl = [
        (f"{a}{b}{c}", "F-CHAIN-002 [23,16,7] concatenated"),
        (f"{a},{b},{c}", "F-CHAIN-002 [23,16,7] comma list"),
        (f"{a} {b} {c}", "F-CHAIN-002 [23,16,7] space list"),
        (str(a + b + c), "F-CHAIN-002 total 46"),
        ("IZLKESEEDQPPEN", "recovered Telegram guide 14x14 row sums (stage summary)"),
        (SELECTED_31, "F-CHAIN-011 exact 31-character selection"),
        (SELECTED_31[:-1].upper(), "Phase 270 30-character split-final-be selection"),
        ("401", "stage summary blue prime sum"),
        ("400", "stage summary yellow prime sum"),
        ("73", "stage summary FEFE prime"),
        ("401400", "stage summary blue+yellow sums concatenated"),
        ("40140073", "stage summary all three sums concatenated"),
        ("401,400,73", "stage summary all three sums, comma list"),
        ("FF67", "G-MATPROD-001 matrix product hex"),
        ("255103", "G-MATPROD-001 matrix product decimal concatenated"),
        ("255,103", "G-MATPROD-001 matrix product decimal list"),
        ("kit", "G-KIT-001 reversed KIT"),
        ("matrixsumlist", "macro label (message 8446)"),
    ]
    lwb = [
        ("BOTH ULTIMATELY THE", "F-CHAIN-003 selected Architect words"),
        ("bothultimatelythe", "F-CHAIN-003 selected Architect words, connected"),
        ("BUT", "F-CHAIN-004 beginnings rail"),
        ("HYE", "F-CHAIN-004 endings rail"),
        ("BUTHYE", "F-CHAIN-004 both rails"),
        ("BYE", "F-CHAIN-006 partial-mirror9 endings rail"),
    ]
    lwb += [(phrase, f"Phase 216 film/screenplay last {len(phrase.split())} word(s) before `choice`")
            for phrase in architect_last_words()]
    lwb += [
        ("CIAO BELLA O", "F-CHAIN-008 authenticated Phase 3.2.1 tail"),
        ("ciaobellao", "F-CHAIN-008 authenticated Phase 3.2.1 tail, connected"),
        ("theflowerblossomsthroughwhatseemstobeaconcretesurface",
         "Stage-1 password: the last words typed before the `choice...` page"),
        ("THEFLOWER", "F-CHAIN-019 authenticated old-password prefix"),
        ("causality", "Phase 2 answer on the `choice...` page"),
        ("lastwordsbeforearchichoice", "macro/page label"),
    ]
    yy = [
        ("yinyang", "macro label (message 8446)"),
        ("yin yang", "macro label, spaced"),
        ("yingyang", "creator spelling (messages 9599/39237)"),
        ("ying yang", "creator spelling, spaced"),
        ("salvation", "SalPhaseIon -> SALVATION rebus (stage summary)"),
        ("salphaseion", "authenticated page title"),
        ("SalPhaseIon", "authenticated page title, page casing"),
        ("cosmicduality", "authenticated page title"),
        ("Cosmic Duality", "authenticated page title, page casing"),
        ("thispassword", "page label after lastwordsbeforearchichoice"),
    ]
    values = {"yellowblueprimes": ybp, "matrixsumlist": msl,
              "lastwordsbeforearchichoice": lwb, "yinyang": yy}
    for slot, items in values.items():
        strings = [v for v, _ in items]
        if len(set(strings)) != len(strings):
            raise AssertionError(f"duplicate value inside slot {slot}")
        if any(not v for v in strings):
            raise AssertionError(f"empty value inside slot {slot}")
    return values


# ---------------------------------------------------------------------------
# 2. Expansion helpers -- each reproduces one prior sweep's recorded form
#    space. Materials are passphrase strings (pre-KDF). Raw 32-byte digest
#    materials (Phase 121/266) are outside this string form space and are
#    dropped on load; empty-string materials are dropped on both sides.
# ---------------------------------------------------------------------------

def expand_std(base, newline_variants):
    out = set()
    for form in answer_forms(base):
        out.update(keystr_forms(form, newline_variants=newline_variants))
    out.discard("")
    return out


def expand_lastcommand(base):
    """lastcommand_probe.probe(): base x {'', LF, CRLF} x {raw, sha256-hex}."""
    out = set()
    for suffix in ("", "\n", "\r\n"):
        source = base + suffix
        out.add(source)
        out.add(hashlib.sha256(source.encode()).hexdigest())
    return out


def expand_p121(operand):
    """binary_hint_operand_audit.operand_materials(): literal / sha-hex lower /
    sha-hex upper / double-sha hex, each over none/LF/CRLF. Raw digests dropped."""
    out = set()
    for material in operand_materials({"x": operand.encode()}):
        try:
            out.add(material.decode("utf-8"))
        except UnicodeDecodeError:
            continue
    return out


def expand_raw_sha(base):
    """door_prime_passport_probe.probe_direct_passphrases(): base and its
    SHA-256 hex only -- no case forms, no newline forms."""
    return {base, hashlib.sha256(base.encode()).hexdigest()}


def _phase461_forms(generator):
    """Phase 461's two oracle checks ran answer_forms() case variants of each
    derived candidate as raw materials only (no SHA, no newline)."""
    _candidates, forms = generator()
    return sorted({form for _label, form, _material in forms})


def _read_wordlist(name):
    path = WORDLIST_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    lines = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\n").rstrip("\r")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            lines.append(line.strip())
    return lines


def _macro_k8():
    """Phase 334's k=8 corpus is a gitignored generated file; regenerate the
    exact same 8! direct concatenations if it is absent."""
    name = "macro_clue_permutation_combinations_k8.txt"
    if (WORDLIST_DIR / name).exists():
        return _read_wordlist(name)
    return ["".join(p) for p in itertools.permutations(MACRO_CLUE, 8)]


def _p372_materials():
    out = set()
    for material in p372_manifest().values():
        out.add(material.decode("utf-8"))
    return out


# Each source: name, loader -> list of base strings (or, for kind="materials",
# final materials), expansion kind, blobs the recorded run covered, oracle
# families, phase references. `salph` must be True for a source to count.
COVERAGE_SOURCES = [
    dict(name="curated_648", kind="bases", expansion="std_newline",
         loader=load_curated_candidates,
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="CBC legacy+extended, ECB, CFB/OFB/CTR, Key Wrap, OpenSSL menu gaps",
         phases="79, 253, 522 (and every extended_cipher_recheck run)"),
    dict(name="medium_curated_all", kind="bases", expansion="std",
         loader=lambda: _read_wordlist("medium_curated_all.txt"),
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="AES-CBC 12 KDF/key-size variants (P323); 60-variant AES table (P328)",
         phases="83/90 (Tier 1+2, SALPH/P32), 323, 328"),
    dict(name="macro_perm_k1_7", kind="bases", expansion="std_newline",
         loader=lambda: _read_wordlist("macro_clue_permutation_combinations.txt"),
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="AES-CBC 12 KDF/key-size variants (GPU oracle)",
         phases="322"),
    dict(name="macro_perm_k8", kind="bases", expansion="std_newline",
         loader=_macro_k8,
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="60-variant AES table (GPU oracle)",
         phases="334"),
    dict(name="curated_v2_full", kind="bases", expansion="std_newline",
         loader=lambda: _read_wordlist("curated_v2_full.txt"),
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="CBC legacy+extended, ECB, stream, Key Wrap (dedicated audits + residual backfill)",
         phases="44, 88, 90, 116, 253, 255, 256"),
    dict(name="lastcommand_probe", kind="bases", expansion="lastcommand",
         loader=lambda: list(LASTCOMMAND_CANDIDATES),
         blobs="SALPH",
         families="AES-CBC (KDF_VARIANTS); 18-material grammar subset widened by P372",
         phases="0.1, 372"),
    dict(name="phase32_monologue_residual", kind="bases", expansion="std",
         loader=lambda: list(RESIDUAL_CANDIDATES),
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="full standard passphrase oracle",
         phases="265"),
    dict(name="phase3_chain_sentences", kind="bases", expansion="std_newline",
         loader=candidate_sentences,
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="full standard passphrase oracle",
         phases="267"),
    dict(name="architect_hye_bye_BYE", kind="materials", expansion="direct",
         loader=lambda: list(hye_bye_keystrings()),
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="CBC, ECB, stream, Key Wrap",
         phases="232"),
    dict(name="phase372_grammar_manifest", kind="materials", expansion="direct",
         loader=lambda: sorted(_p372_materials()),
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="CBC, ECB, stream, Key Wrap",
         phases="372"),
    dict(name="phase121_closed_operands", kind="bases", expansion="p121",
         loader=lambda: [EXPECTED_FIRST_HINT_PRIME, SELECTED_31],
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="legacy+extended CBC, ECB, CFB/OFB/CTR, Key Wrap",
         phases="121"),
    dict(name="ciao_bella_family", kind="bases", expansion="std_newline",
         loader=lambda: list(CIAO_CANDIDATES),
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="CBC, ECB, stream, Key Wrap",
         phases="234"),
    dict(name="title_rebus_fixed", kind="bases", expansion="std_newline",
         loader=lambda: list(title_rebus_candidates()),
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="CBC (legacy+extended) at the time; salvation family",
         phases="96, 97, 98"),
    dict(name="architect_literal_seven_words", kind="bases", expansion="std_newline",
         loader=lambda: list(architect_literal_candidates()),
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="CBC extended, ECB, stream, Key Wrap",
         phases="216"),
    dict(name="atomic_and_book_vocab", kind="bases", expansion="std_newline",
         loader=lambda: list(ATOMIC_CANDIDATES) + list(BOOK_CANDIDATES),
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="full standard passphrase oracle",
         phases="179"),
    dict(name="door_prime_passport_probe", kind="bases", expansion="raw_sha",
         loader=lambda: list(DOOR_PROBE_CANDIDATES),
         blobs="SALPH/COSMIC",
         families="AES-CBC (KDF_VARIANTS at the time)",
         phases="4"),
    dict(name="phase461_second_prime_forms", kind="materials", expansion="direct",
         loader=lambda: _phase461_forms(second_prime_derived),
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="CBC, ECB, stream, Key Wrap (raw case forms only)",
         phases="461"),
    dict(name="phase461_theflower_forms", kind="materials", expansion="direct",
         loader=lambda: _phase461_forms(flower_prefix_derived),
         blobs="SALPH/COSMIC/P32TRAILING/URLBLOB",
         families="CBC, ECB, stream, Key Wrap (raw case forms only)",
         phases="461"),
]

# Recorded sweeps deliberately NOT counted as SALPH coverage, with the reason.
EXCLUDED_SWEEPS = {
    "Phase 270 sibling-composition (25 candidates)": "P32TRAILING only",
    "Phase 480 two-address constructions": "P32TRAILING only",
    "Phase 481 Pwdb 10M wordlist": "P32TRAILING only; literal bytes only",
    "Phase 317 seven-part permutations": "no shared vocabulary with any slot value",
    "Phases 268/269 X2SH4Y0QB15 family": "no shared vocabulary with any slot value",
    "Phases 336-342 / 346 raw-key-material tiers": "raw key bytes, not passphrases",
    "Phase 164 literal raw-key oracle": "raw key bytes, not passphrases",
}

_SLOW_SOURCES = {"medium_curated_all", "macro_perm_k1_7", "macro_perm_k8"}


def _mkey(material):
    return int.from_bytes(hashlib.blake2b(material.encode("utf-8"), digest_size=8).digest(), "big")


def _expand_source(source, base):
    kind = source["expansion"]
    if kind == "std_newline":
        return expand_std(base, True)
    if kind == "std":
        return expand_std(base, False)
    if kind == "lastcommand":
        return expand_lastcommand(base)
    if kind == "p121":
        return expand_p121(base)
    if kind == "raw_sha":
        return expand_raw_sha(base)
    if kind == "direct":
        return {base} if base else set()
    raise ValueError(kind)


def build_tested(sources):
    """material-key -> bitmask of covering source indices."""
    tested = {}
    summary = []
    for index, source in enumerate(sources):
        started = time.time()
        items = source["loader"]()
        bit = 1 << index
        base_digest = hashlib.sha256("\n".join(items).encode("utf-8")).hexdigest()
        materials = 0
        for item in items:
            for material in _expand_source(source, item):
                key = _mkey(material)
                tested[key] = tested.get(key, 0) | bit
                materials += 1
        summary.append({
            "name": source["name"],
            "bases": len(items),
            "materials_expanded": materials,
            "base_list_sha256": base_digest,
            "expansion": source["expansion"],
            "blobs": source["blobs"],
            "families": source["families"],
            "phases": source["phases"],
            "seconds": round(time.time() - started, 2),
        })
    return tested, summary


# ---------------------------------------------------------------------------
# 3. Candidate enumeration and classification.
# ---------------------------------------------------------------------------

def cells():
    """Every non-empty ordered slot subset in macro order x separator."""
    out = []
    for size in range(1, len(SLOT_ORDER) + 1):
        for subset in itertools.combinations(SLOT_ORDER, size):
            for sep_name, sep in SEPARATORS:
                if size == 1 and sep_name != "connected":
                    continue  # a single slot has nothing to join
                cell_id = "+".join(SLOT_SHORT[s] for s in subset) + "|" + sep_name
                out.append((cell_id, subset, sep))
    return out


def enumerate_bases(values=None):
    """Yield (cell_id, base, provenance) with exact-string dedupe across cells."""
    values = values or slot_values()
    seen = set()
    duplicates = 0
    for cell_id, subset, sep in cells():
        for combo in itertools.product(*[values[s] for s in subset]):
            base = sep.join(v for v, _ in combo)
            if base in seen:
                duplicates += 1
                continue
            seen.add(base)
            yield cell_id, base, [src for _, src in combo]
    enumerate_bases.duplicates = duplicates


def tagged_materials(base):
    """The standard expansion, with each material tagged by how it was
    derived from the base. `literal` family = the base and its plain
    upper/lower casings; `alpha` family = answer_forms()' letters-only
    stripping (which collapses a digit-bearing base into a much shorter
    string). Coverage of an alpha-family material says nothing about
    whether the base itself was ever tried, so the two are reported apart."""
    alpha = re.sub(r"[^A-Za-z]", "", base)
    literal_family = {base, base.upper(), base.lower()}
    tags = {}
    for form in answer_forms(base):
        family = "literal" if form in literal_family else "alpha"
        if form == "":
            continue
        for index, material in enumerate(keystr_forms(form, newline_variants=True)):
            newline = ("none", "lf", "crlf")[index // 3]
            hashing = ("raw", "sha", "dsha")[index % 3]
            tag = f"{family}/{hashing}/{newline}"
            # A literal-family derivation wins if the same string arises both ways.
            if material not in tags or (family == "literal" and tags[material].startswith("alpha")):
                tags[material] = tag
    if alpha == base:
        # pure-letter base: alpha forms coincide with literal forms by construction
        tags = {m: t.replace("alpha/", "literal/") for m, t in tags.items()}
    return tags


def classify(base, tested):
    tags = tagged_materials(base)
    covered = 0
    literal_total = literal_covered = 0
    mask = 0
    covered_tags = {}
    for material, tag in tags.items():
        is_literal = tag.startswith("literal/")
        literal_total += is_literal
        hit = tested.get(_mkey(material), 0)
        if hit:
            covered += 1
            literal_covered += is_literal
            mask |= hit
            covered_tags[tag] = covered_tags.get(tag, 0) + 1
    if covered == 0:
        klass = "new"
    elif covered == len(tags):
        klass = "all_covered"
    elif literal_covered == 0:
        klass = "alpha_only_covered"
    else:
        klass = "literal_partially_covered"
    return klass, len(tags), covered, mask, literal_total, literal_covered, covered_tags


def audit(sources=None, write=True, values=None):
    sources = COVERAGE_SOURCES if sources is None else sources
    started = time.time()
    tested, source_summary = build_tested(sources)
    values = values or slot_values()
    per_cell = {}

    def bucket():
        return {"bases": 0, "materials": 0, "materials_covered": 0,
                "literal_materials": 0, "literal_materials_covered": 0,
                "new": 0, "alpha_only_covered": 0, "literal_partially_covered": 0, "all_covered": 0}

    totals = bucket()
    covered_by_tag = {}
    source_hits = [0] * len(sources)
    rows = []
    single_slot_detail = []
    for cell_id, base, provenance in enumerate_bases(values):
        klass, n_mat, n_cov, mask, lit_total, lit_cov, tags = classify(base, tested)
        cell = per_cell.setdefault(cell_id, bucket())
        for target in (cell, totals):
            target["bases"] += 1
            target["materials"] += n_mat
            target["materials_covered"] += n_cov
            target["literal_materials"] += lit_total
            target["literal_materials_covered"] += lit_cov
            target[klass] += 1
        for tag, count in tags.items():
            covered_by_tag[tag] = covered_by_tag.get(tag, 0) + count
        for index in range(len(sources)):
            if mask & (1 << index):
                source_hits[index] += 1
        rows.append((cell_id, base, klass, n_mat, n_cov, lit_total, lit_cov, provenance))
        if "+" not in cell_id:
            single_slot_detail.append({
                "slot": cell_id.split("|")[0], "value": base, "class": klass,
                "literal_covered": f"{lit_cov}/{lit_total}", "covered_tags": dict(sorted(tags.items())),
                "sources": [sources[i]["name"] for i in range(len(sources)) if mask & (1 << i)],
            })
    for index, count in enumerate(source_hits):
        source_summary[index]["candidate_bases_touched"] = count

    manifest_lines = ["cell\tclass\tmaterials\tcovered\tliteral_materials\tliteral_covered\tbase\tprovenance"]
    for cell_id, base, klass, n_mat, n_cov, lit_total, lit_cov, provenance in rows:
        manifest_lines.append("\t".join([
            cell_id, klass, str(n_mat), str(n_cov), str(lit_total), str(lit_cov),
            json.dumps(base, ensure_ascii=False), " | ".join(provenance),
        ]))
    manifest_text = "\n".join(manifest_lines) + "\n"
    manifest_digest = hashlib.sha256(manifest_text.encode("utf-8")).hexdigest()
    new_bases_text = "\n".join(json.dumps(r[1], ensure_ascii=False) for r in rows if r[2] != "all_covered") + "\n"
    new_bases_digest = hashlib.sha256(new_bases_text.encode("utf-8")).hexdigest()

    report = {
        "phase": 523,
        "oracle_calls": 0,
        "slot_order": SLOT_ORDER,
        "separators": [name for name, _ in SEPARATORS],
        "slot_value_counts": {s: len(values[s]) for s in SLOT_ORDER},
        "slot_values": {s: [{"value": v, "source": src} for v, src in values[s]] for s in SLOT_ORDER},
        "cells": per_cell,
        "totals": totals,
        "covered_materials_by_tag": dict(sorted(covered_by_tag.items())),
        "single_slot_values": single_slot_detail,
        "cross_cell_duplicate_bases": enumerate_bases.duplicates,
        "tested_material_keys": len(tested),
        "sources": source_summary,
        "excluded_sweeps": EXCLUDED_SWEEPS,
        "manifest_sha256": manifest_digest,
        "not_all_covered_bases_sha256": new_bases_digest,
        "not_all_covered_bases": totals["bases"] - totals["all_covered"],
        "seconds": round(time.time() - started, 2),
    }
    if write:
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        (WORK_DIR / "manifest.tsv").write_text(manifest_text, encoding="utf-8")
        (WORK_DIR / "not_all_covered_bases.txt").write_text(new_bases_text, encoding="utf-8")
        (WORK_DIR / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report["written"] = str(WORK_DIR)
    return report


# ---------------------------------------------------------------------------
# 4. Self-test: input-integrity checks plus a fast classification check on the
#    non-slow sources (the full build is exercised by --run).
# ---------------------------------------------------------------------------

def self_test():
    checks = {}
    groups = prime_lists()
    checks["prime_walk_sums"] = {k: sum(v) for k, v in groups.items()} == EXPECTED_FITTED_SUMS
    checks["574061_prime_and_expected"] = is_prime(574061) and EXPECTED_PRIME == 574061 and EXPECTED_FIRST_HINT_PRIME == "574061"
    checks["311027_prime_hex"] = is_prime(311027) and f"{311027:06X}" == "04BEF3" and f"{574061:06X}" == "08C26D"
    checks["sum_list"] = tuple(EXPECTED_SUM_LIST) == (23, 16, 7)
    checks["selected_31"] = len(SELECTED_31) == 31 and SELECTED_31.islower()
    srt = re.sub(r"[^a-z ]", " ", SRT_PATH.read_text(encoding="utf-8", errors="replace").lower())
    srt = " ".join(srt.split())
    checks["srt_has_final_sentence"] = (ARCHITECT_FINAL_SENTENCE + " choice") in srt
    checks["architect_literal_matches_ours"] = ARCHITECT_FINAL_SENTENCE in architect_literal_candidates()
    checks["macro_clue_order"] = MACRO_CLUE[:4] == SLOT_ORDER
    values = slot_values()
    checks["slot_counts"] = {s: len(values[s]) for s in SLOT_ORDER} == {
        "yellowblueprimes": 15, "matrixsumlist": 18, "lastwordsbeforearchichoice": 19, "yinyang": 10}
    checks["cell_count"] = len(cells()) == 15 + 11  # 15 subsets connected + 11 multi-slot spaced
    checks["expansion_matches_cb_common"] = expand_std("Ab c", True) == {
        k for f in answer_forms("Ab c") for k in keystr_forms(f, newline_variants=True)} - {""}

    fast_sources = [s for s in COVERAGE_SOURCES if s["name"] not in _SLOW_SOURCES]
    tested, _ = build_tested(fast_sources)
    checks["known_single_covered"] = all(classify(v, tested)[0] == "all_covered"
                                         for v in ("574061", "yinyang", "matrixsumlist", "BYE", "IZLKESEEDQPPEN"))
    synthetic = "574061" + "23167" + "bothultimatelythe" + "yinyang"
    checks["synthetic_product_new"] = classify(synthetic, tested)[0] == "new"
    # A digit-bearing base whose alpha-only collapse is an already-tested word
    # must be reported as alpha_only_covered, never as literal coverage.
    checks["alpha_collapse_is_separated"] = classify("574061" + "kit", tested)[0] in ("alpha_only_covered", "new")
    tags = tagged_materials("574061kit")
    checks["tag_families"] = {t.split("/")[0] for t in tags.values()} == {"literal", "alpha"} and len(tags) == 36
    checks["pure_letter_base_all_literal"] = all(t.startswith("literal/") for t in tagged_materials("yinyang").values())
    checks["lastcommand_expansion_pinned"] = len(expand_lastcommand("x")) == 6
    checks["phase4_and_461_values_seen"] = (
        classify("1,4,21", tested)[0] != "new"
        and classify("311027", tested)[0] != "new"
        and classify("THEFLOWER", tested)[0] != "new")
    checks["p121_expansion_pinned"] = len(expand_p121("574061")) == 12  # 3 newline x (literal, hex lower, hex upper, double hex)
    return {"ok": all(checks.values()), "checks": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true", help="full overlap audit over all coverage sources; writes _work/phase523/")
    parser.add_argument("--fast", action="store_true", help="skip the three large corpora (development only; not the recorded result)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        result = self_test()
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1
    if args.run:
        sources = [s for s in COVERAGE_SOURCES if not (args.fast and s["name"] in _SLOW_SOURCES)]
        report = audit(sources=sources, write=not args.fast)
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            t = report["totals"]
            print(f"[*] bases={t['bases']} materials={t['materials']} covered_materials={t['materials_covered']} "
                  f"literal_materials={t['literal_materials']} literal_covered={t['literal_materials_covered']}")
            print(f"[*] bases: new={t['new']} alpha_only_covered={t['alpha_only_covered']} "
                  f"literal_partially_covered={t['literal_partially_covered']} all_covered={t['all_covered']}")
            print(f"[*] tested material keys={report['tested_material_keys']} sources={len(report['sources'])}")
            for cell_id, c in report["cells"].items():
                print(f"    {cell_id:<26} bases={c['bases']:>6} new={c['new']:>6} alpha_only={c['alpha_only_covered']:>5} "
                      f"lit_partial={c['literal_partially_covered']:>4} all={c['all_covered']:>3} "
                      f"lit_cov={c['literal_materials_covered']}/{c['literal_materials']}")
            print("[*] covered materials by derivation tag:")
            for tag, count in report["covered_materials_by_tag"].items():
                print(f"    {tag:<24} {count}")
            print("[*] single-slot values:")
            for d in report["single_slot_values"]:
                print(f"    {d['slot']:<4} {d['class']:<26} lit={d['literal_covered']:<6} {json.dumps(d['value'])[:60]:<62} {','.join(d['sources'])}")
            for s in report["sources"]:
                print(f"    src {s['name']:<32} bases={s['bases']:>7} materials={s['materials_expanded']:>9} touched={s['candidate_bases_touched']:>6}")
            print(f"[*] manifest sha256={report['manifest_sha256']}")
            print(f"[*] not-all-covered bases={report['not_all_covered_bases']} sha256={report['not_all_covered_bases_sha256']}")
            if report.get("written"):
                print(f"[*] written to {report['written']}")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
