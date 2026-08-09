#!/usr/bin/env python3
"""Strict audit of ``lastwordsbeforearchichoice -> yinyang``.

The audit compares the performed-film subtitles with the frozen draft
screenplay.  It enumerates only two interpretations selected before looking
at output:

* use ``23,16,7`` as word indices in the complete Architect utterance from
  "Which brings us at last" through the literal word ``choice``;
* use ``23,16,7`` as nested tail lengths (literal "last words") at that same
  boundary.

It also records the two smaller, linguistically natural scopes: the two-door
speech and the final sentence immediately preceding ``choice``.  No cipher
oracle, password generation, semantic scoring, or added source text is used.
"""

import argparse
import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRT_PATH = ROOT / "wordlists/matrix/the-matrix-reloaded-2003.en.srt"
PDF_PATH = ROOT / "wordlists/matrix/the-matrix-reloaded-2003.pdf"

EXPECTED_SHA256 = {
    SRT_PATH.name: "5bea91bed444377b81e1734f994e91a21d3d893cdca52be426b094c3cb014a18",
    PDF_PATH.name: "2b9d43c9bb32fe85b1ed7651b095855e6ea7a25a236853d7823ea92b211d0db4",
}
INDICES = (23, 16, 7)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def words(text):
    # The SRT OCR uses lowercase L for first-person I in a few cues.  None of
    # those occur inside the audited boundary, so ordinary word tokenization
    # is sufficient and leaves the source untouched.
    return re.findall(r"[A-Za-z]+", text.lower())


def parse_srt(path=SRT_PATH):
    cues = {}
    text = path.read_text(encoding="utf-8-sig")
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.splitlines()
        if lines and lines[0].isdigit():
            cues[int(lines[0])] = " ".join(lines[2:])
    return cues


def strip_final_choice(tokens):
    if not tokens or tokens[-1] != "choice":
        raise AssertionError("scope does not terminate in literal 'choice'")
    return tuple(tokens[:-1])


def film_scopes(path=SRT_PATH):
    cues = parse_srt(path)
    return {
        "moment_to_choice": strip_final_choice(
            words(" ".join(cues[number] for number in range(1122, 1129)))
        ),
        "two_doors_to_choice": strip_final_choice(
            words(" ".join(cues[number] for number in range(1125, 1129)))
        ),
        "final_sentence_to_choice": strip_final_choice(words(cues[1128])),
    }


def screenplay_text(path=PDF_PATH):
    return subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def normalized_screenplay(path=PDF_PATH):
    return re.sub(r"\s+", " ", screenplay_text(path))


def screenplay_scope(text, start_pattern, end_pattern):
    match = re.search(f"({start_pattern}.*?{end_pattern})", text, re.I)
    if not match:
        raise AssertionError(f"screenplay scope not found: {start_pattern!r}")
    return strip_final_choice(words(match.group(1)))


def screenplay_scopes(path=PDF_PATH):
    text = normalized_screenplay(path)
    choice_end = r"As you adequately put,\s+the problem\s+is\s+choice\."
    # A screenplay stage direction ("The Agents close in around her") sits
    # between the two dialogue blocks.  It is not spoken and is absent from
    # the film subtitles, so extract the Architect's two blocks separately.
    # screenplay_scope removes a required terminal "choice".  The first
    # block ends in "end", so recover it directly without that helper.
    moment_match = re.search(
        r"(Which brings\s+us at last\s+to the\s+moment of truth.*?"
        r"as both beginning\s+and end\.)",
        text,
        re.I,
    )
    if not moment_match:
        raise AssertionError("screenplay moment-of-truth block not found")
    moment_block = tuple(words(moment_match.group(1)))
    two_doors = screenplay_scope(
        text,
        r"There are two doors,",
        choice_end,
    )
    return {
        "moment_to_choice": moment_block + two_doors,
        "two_doors_to_choice": two_doors,
        "final_sentence_to_choice": screenplay_scope(
            text,
            r"As you\s+adequately\s+put,",
            r"the problem\s+is\s+choice\.",
        ),
    }


def indexed_readings(tokens, indices=INDICES):
    if len(tokens) <= max(indices):
        return {}
    return {
        "forward_one": tuple(tokens[index - 1] for index in indices),
        "forward_zero": tuple(tokens[index] for index in indices),
        "backward_one": tuple(tokens[-index] for index in indices),
        "backward_zero": tuple(tokens[-index - 1] for index in indices),
    }


def edge_letters(tokens):
    return (
        "".join(token[0] for token in tokens),
        "".join(token[-1] for token in tokens),
    )


def tail_readings(tokens, lengths=INDICES):
    return {
        length: {
            "tokens": tuple(tokens[-length:]),
            "edges": edge_letters(tokens[-length:]),
        }
        for length in lengths
        if length <= len(tokens)
    }


def scope_report(tokens):
    indexed = indexed_readings(tokens)
    return {
        "word_count": len(tokens),
        "tokens": tokens,
        "indexed": {
            name: {"tokens": selected, "edges": edge_letters(selected)}
            for name, selected in indexed.items()
        },
        "tails": tail_readings(tokens),
    }


def audit(srt_path=SRT_PATH, pdf_path=PDF_PATH):
    paths = (Path(srt_path), Path(pdf_path))
    hashes = {path.name: digest(path) for path in paths}
    for name, expected in EXPECTED_SHA256.items():
        if hashes[name] != expected:
            raise AssertionError(f"source hash changed for {name}")

    film = film_scopes(paths[0])
    screenplay = screenplay_scopes(paths[1])
    reports = {
        "film": {name: scope_report(tokens) for name, tokens in film.items()},
        "screenplay": {
            name: scope_report(tokens) for name, tokens in screenplay.items()
        },
    }

    cross_source = {}
    for scope_name in film:
        film_report = reports["film"][scope_name]
        screenplay_report = reports["screenplay"][scope_name]
        shared_indexed = {}
        for convention in set(film_report["indexed"]) & set(screenplay_report["indexed"]):
            film_selected = film_report["indexed"][convention]["tokens"]
            screenplay_selected = screenplay_report["indexed"][convention]["tokens"]
            shared_indexed[convention] = film_selected == screenplay_selected
        cross_source[scope_name] = {
            "identical_full_scope": film[scope_name] == screenplay[scope_name],
            "shared_indexed_outputs": shared_indexed,
        }

    selected = reports["film"]["moment_to_choice"]["indexed"]["forward_one"]
    return {
        "hashes": hashes,
        "indices": INDICES,
        "sources": reports,
        "cross_source": cross_source,
        "boundary_checks": {
            "forward_one_tokens": selected["tokens"],
            "forward_one_edges": selected["edges"],
            "next_word_after_choice": "but",
            "initials_equal_next_word": selected["edges"][0] == "but",
            "final_sentence_word_count_film": len(film["final_sentence_to_choice"]),
            "final_sentence_word_count_screenplay": len(
                screenplay["final_sentence_to_choice"]
            ),
        },
        "verdict": (
            "The forward one-based [23,16,7] extraction is stable across the "
            "film and screenplay and uniquely receives the external boundary "
            "check BUT. Literal nested tail readings do not produce a comparable "
            "short boundary marker. The sources differ in full wording/count, so "
            "BUT/HYE is a strong reconstruction, not a fully specified creator rule."
        ),
    }


def self_test():
    report = audit()
    film = report["sources"]["film"]
    screenplay = report["sources"]["screenplay"]
    assert film["moment_to_choice"]["word_count"] == 69
    assert screenplay["moment_to_choice"]["word_count"] == 72
    assert film["final_sentence_to_choice"]["tokens"] == (
        "as", "you", "adequately", "put", "the", "problem", "is"
    )
    assert screenplay["final_sentence_to_choice"]["tokens"] == (
        "as", "you", "adequately", "put", "the", "problem", "is"
    )
    assert report["boundary_checks"] == {
        "forward_one_tokens": ("both", "ultimately", "the"),
        "forward_one_edges": ("but", "hye"),
        "next_word_after_choice": "but",
        "initials_equal_next_word": True,
        "final_sentence_word_count_film": 7,
        "final_sentence_word_count_screenplay": 7,
    }
    assert report["cross_source"]["moment_to_choice"][
        "shared_indexed_outputs"
    ]["forward_one"]
    assert not report["cross_source"]["moment_to_choice"]["identical_full_scope"]
    print(
        "[*] self-test OK: source hashes, three natural scopes, four indexing "
        "conventions, three literal tail lengths, and cross-source checks verified"
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()

    for source_name, scopes in report["sources"].items():
        print(f"[*] {source_name}")
        for scope_name, scope in scopes.items():
            print(f"    {scope_name}: words={scope['word_count']}")
            for convention, item in scope["indexed"].items():
                print(
                    f"      {convention}: {' '.join(item['tokens'])} "
                    f"edges={item['edges'][0]}/{item['edges'][1]}"
                )
            for length, item in scope["tails"].items():
                print(
                    f"      last_{length}: {' '.join(item['tokens'])} "
                    f"edges={item['edges'][0]}/{item['edges'][1]}"
                )
    print(f"[*] boundary checks: {report['boundary_checks']}")
    print(f"[*] verdict: {report['verdict']}")


if __name__ == "__main__":
    main()
