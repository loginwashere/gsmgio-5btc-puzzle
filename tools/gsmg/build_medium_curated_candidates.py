#!/usr/bin/env python3
"""Build staged, provenance-tracked GSMG candidate lists.

This deliberately does not add the result to extended_cipher_recheck.CURATED_FILES.
The existing 648-candidate set remains the small default. The generated tiers are
explicit inputs for progressively larger follow-up sweeps:

Tier 1 -- primary/high-confidence material:
  * the existing curated set;
  * complete Cosmic Duality OCR lines and content-word reductions;
  * the 80 indexed creator clue/confirmation messages and the community messages
    they directly confirm, including bounded one-to-six-content-word n-grams.

Tier 2 -- puzzle-derived combinations:
  * previously generated anchor combinations, book candidate sets, thematic chat
    reductions, and the session's bounded chain-combination corpus.

Tier 3 -- filtered broad vocabulary:
  * clean standalone words mined from chat and the Matrix scripts;
  * community chat lines selected by puzzle-specific anchors or at least two
    independent generic clue anchors;
  * one non-overlapping 15-word Matrix screenplay partition, restricted to the
    Architect/Oracle/choice scene vocabulary.

Every candidate has a JSONL provenance record. Candidates are promoted to the
earliest tier that contains them; later source matches are retained as additional
provenance rather than duplicated.
"""

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from extended_cipher_recheck import load_curated_candidates
from riddle_content_words import content_words, filtered_candidate
from telegram_creator_clue_index_audit import (
    DEFAULT_EXPORT_DIR,
    INDEX,
    flatten_text,
    load_messages,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
WORDLIST_DIR = REPO_ROOT / "wordlists" / "gsmg"
DEFAULT_OUTPUT_DIR = WORDLIST_DIR

TIER_FILES = {
    1: "medium_curated_tier1_primary.txt",
    2: "medium_curated_tier2_derived.txt",
    3: "medium_curated_tier3_broad.txt",
}
COMBINED_FILE = "medium_curated_all.txt"
PROVENANCE_FILE = "medium_curated_provenance.txt"

TIER2_FILES = (
    "anchor_x_vocab_combos.txt",
    "session_combined_for_chain.txt",
    "chat_theme_content_words.txt",
    "cosmic_duality_book_candidates.txt",
    "content_word_filtered.txt",
    "cosmic_duality_book_p6_11_candidates.txt",
    "cosmic_duality_book_p8_9.txt",
    "looking_forward_candidates.txt",
)

LEXICAL_FILES = (
    "chat_mined_words.txt",
    "matrix_scripts_words.txt",
)

HIGH_SPECIFICITY_CHAT_ANCHORS = (
    "matrixsumlist",
    "lastwordsbeforearchichoice",
    "yellowblueprime",
    "salphaseion",
    "dbbi",
    "faed",
    "zeroed",
    "causality",
    "better half",
    "in front of your eyes",
    "looking forward",
    "you won",
    "last command",
)

GENERIC_CHAT_ANCHORS = (
    "yellow",
    "blue",
    "prime",
    "primes",
    "architect",
    "yin",
    "yang",
    "rabbit",
    "seed",
    "planted",
    "password",
    "passphrase",
    "private key",
    "half",
    "cosmic",
    "duality",
    "choice",
    "oracle",
    "enter",
)

MATRIX_SCENE_ANCHORS = (
    "architect",
    "oracle",
    "choice",
    "causality",
    "anomaly",
    "equation",
    "balance",
    "unbalance",
    "purpose",
    "love",
    "hope",
    "faith",
)

KNOWN_PROJECT_VOCABULARY = {
    "architect",
    "causality",
    "cosmicduality",
    "dbbi",
    "faed",
    "followthewhiterabbit",
    "gsmg",
    "matrixsumlist",
    "morpheus",
    "neo",
    "oracle",
    "p32trailing",
    "salphaseion",
    "smith",
    "theseedisplanted",
    "yinyang",
    "yellowblueprime",
    "zion",
}


def clean_letters(value):
    return re.sub(r"[^A-Za-z]", "", value)


def eligible(value, minimum=4):
    value = re.sub(r"\s+", " ", value.strip())
    return value if minimum <= len(value) <= 256 and "\0" not in value else None


def line_variants(line, include_raw=True):
    variants = []
    raw = eligible(line)
    letters = eligible(clean_letters(line))
    filtered = eligible(filtered_candidate(line))
    if include_raw and raw:
        variants.append(raw)
    if letters:
        variants.append(letters)
    if filtered:
        variants.append(filtered)
    return tuple(dict.fromkeys(variants))


def content_ngrams(line, max_words=6):
    words = content_words(line)
    for width in range(1, min(max_words, len(words)) + 1):
        for start in range(len(words) - width + 1):
            candidate = eligible("".join(words[start:start + width]))
            if candidate:
                yield candidate


def dictionary_words():
    paths = (
        Path("/usr/share/dict/american-english"),
        Path("/usr/share/dict/british-english"),
    )
    words = set()
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(errors="ignore").splitlines():
            word = clean_letters(line).lower()
            if 3 <= len(word) <= 32:
                words.add(word)
    if not words:
        raise FileNotFoundError("system English dictionaries are required")
    return words


def segmentable_compound(candidate, words):
    reachable = {0: 0}
    for start in range(len(candidate)):
        if start not in reachable or reachable[start] >= 3:
            continue
        for end in range(start + 3, len(candidate) + 1):
            if candidate[start:end] in words:
                reachable[end] = min(reachable.get(end, 99), reachable[start] + 1)
    return 2 <= reachable.get(len(candidate), 0) <= 3


def clean_lexical_candidate(line, words, cross_source_words):
    stripped = line.strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z'-]*", stripped):
        return None
    candidate = clean_letters(stripped).lower()
    if not 4 <= len(candidate) <= 32:
        return None
    if not any(character in "aeiouy" for character in candidate):
        return None
    if max(Counter(candidate).values()) > max(3, len(candidate) // 2):
        return None
    if (
        candidate in words
        or candidate in KNOWN_PROJECT_VOCABULARY
        or candidate in cross_source_words
        or segmentable_compound(candidate, words)
    ):
        return candidate
    return None


def boundary_contains(text, phrase):
    return re.search(rf"(?<![A-Za-z]){re.escape(phrase)}(?![A-Za-z])", text) is not None


def chat_line_selected(line):
    lowered = line.lower()
    if any(anchor in lowered for anchor in HIGH_SPECIFICITY_CHAT_ANCHORS):
        return True
    matched = {
        anchor
        for anchor in GENERIC_CHAT_ANCHORS
        if boundary_contains(lowered, anchor)
    }
    return len(matched) >= 2


def matrix_line_selected(line):
    lowered = line.lower()
    return any(boundary_contains(lowered, anchor) for anchor in MATRIX_SCENE_ANCHORS)


class Collector:
    def __init__(self):
        self.tier = {}
        self.sources = defaultdict(set)
        self.order = {1: [], 2: [], 3: []}

    def add(self, candidate, tier, source, minimum=4):
        candidate = eligible(candidate, minimum=minimum)
        if not candidate:
            return
        self.sources[candidate].add(source)
        previous = self.tier.get(candidate)
        if previous is None:
            self.tier[candidate] = tier
            self.order[tier].append(candidate)
        elif tier < previous:
            self.order[previous].remove(candidate)
            self.tier[candidate] = tier
            self.order[tier].append(candidate)

    def add_line(self, line, tier, source, include_raw=True):
        for candidate in line_variants(line, include_raw=include_raw):
            self.add(candidate, tier, source)

    def tier_candidates(self, tier):
        return self.order[tier]

    def all_candidates(self):
        return [
            candidate
            for tier in (1, 2, 3)
            for candidate in self.order[tier]
        ]


def add_existing_curated(collector):
    for candidate in load_curated_candidates():
        collector.add(candidate, 1, "existing_curated", minimum=1)


def add_complete_book(collector):
    path = WORDLIST_DIR / "cosmic_duality_book_screenshot_ocr.txt"
    for line_number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        collector.add_line(
            line,
            1,
            f"book_ocr:{line_number}",
            include_raw=True,
        )


def add_creator_evidence(collector, export_dir):
    _, messages = load_messages(export_dir)
    message_ids = []
    for creator_id in INDEX:
        message_ids.append(("creator", creator_id))
        reply_id = messages[creator_id].get("reply_to_message_id")
        if reply_id in messages:
            message_ids.append(("confirmed_reply", reply_id))
    seen_ids = set()
    for role, message_id in message_ids:
        if message_id in seen_ids:
            continue
        seen_ids.add(message_id)
        text = flatten_text(messages[message_id].get("text", ""))
        source = f"telegram_{role}:{message_id}"
        collector.add_line(text, 1, source, include_raw=True)
        for candidate in content_ngrams(text):
            collector.add(candidate, 1, source + ":ngram1-6")


def add_tier2_files(collector):
    for name in TIER2_FILES:
        path = WORDLIST_DIR / name
        for line_number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if line.strip() and not line.lstrip().startswith("#"):
                collector.add(line.strip(), 2, f"{name}:{line_number}")


def add_lexical_files(collector):
    words = dictionary_words()
    source_sets = []
    for name in LEXICAL_FILES:
        values = {
            clean_letters(line).lower()
            for line in (WORDLIST_DIR / name).read_text(errors="replace").splitlines()
            if clean_letters(line)
        }
        source_sets.append(values)
    cross_source_words = set.intersection(*source_sets)
    for name in LEXICAL_FILES:
        path = WORDLIST_DIR / name
        for line_number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            candidate = clean_lexical_candidate(line, words, cross_source_words)
            if candidate:
                collector.add(candidate, 3, f"{name}:{line_number}")


def add_selected_chat_lines(collector):
    path = WORDLIST_DIR / "chat_mined_lines.txt"
    for line_number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if chat_line_selected(line):
            collector.add_line(
                line,
                3,
                f"chat_anchor_line:{line_number}",
                include_raw=True,
            )


def add_selected_matrix_windows(collector):
    path = WORDLIST_DIR / "matrix_script_windows.txt"
    for zero_index, line in enumerate(path.read_text(errors="replace").splitlines()):
        # The source is a one-word-sliding 15-word window corpus. Offset-zero
        # stride-15 gives a deterministic non-overlapping partition instead of
        # retaining fifteen near-duplicates around every matching phrase.
        if zero_index % 15 == 0 and matrix_line_selected(line):
            collector.add_line(
                line,
                3,
                f"matrix_partition_window:{zero_index + 1}",
                include_raw=True,
            )


def write_outputs(collector, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    for tier, filename in TIER_FILES.items():
        candidates = collector.tier_candidates(tier)
        (output_dir / filename).write_text("\n".join(candidates) + "\n")
    combined = collector.all_candidates()
    (output_dir / COMBINED_FILE).write_text("\n".join(combined) + "\n")
    with (output_dir / PROVENANCE_FILE).open("w") as output:
        for candidate in combined:
            output.write(json.dumps({
                "candidate": candidate,
                "tier": collector.tier[candidate],
                "sources": sorted(collector.sources[candidate]),
            }, sort_keys=True) + "\n")
    return combined


def build(export_dir=DEFAULT_EXPORT_DIR, output_dir=DEFAULT_OUTPUT_DIR):
    collector = Collector()
    add_existing_curated(collector)
    add_complete_book(collector)
    add_creator_evidence(collector, export_dir)
    add_tier2_files(collector)
    add_lexical_files(collector)
    add_selected_chat_lines(collector)
    add_selected_matrix_windows(collector)
    combined = write_outputs(collector, output_dir)
    return collector, combined


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    collector, combined = build(args.export_dir, args.output_dir)
    digest = hashlib.sha256("\n".join(combined).encode()).hexdigest()[:16]
    counts = {tier: len(collector.tier_candidates(tier)) for tier in (1, 2, 3)}
    source_kinds = Counter(
        source.split(":", 1)[0]
        for sources in collector.sources.values()
        for source in sources
    )
    print(
        f"[*] tier1={counts[1]:,} tier2={counts[2]:,} tier3={counts[3]:,} "
        f"combined={len(combined):,} digest={digest}"
    )
    print("[*] top provenance kinds:")
    for source, count in source_kinds.most_common(12):
        print(f"    {source}: {count:,}")
    if args.self_test:
        assert len(load_curated_candidates()) == 648
        assert all(candidate in combined for candidate in load_curated_candidates())
        assert counts[1] > 10_000
        assert counts[2] > 5_000
        assert counts[3] > 20_000
        assert len(combined) == len(set(combined))
        print("[*] self-test OK")


if __name__ == "__main__":
    main()
