#!/usr/bin/env python3
"""Phase 440: bounded prime/complement readings of prior-page comments."""

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import phase439_historical_web_source_referent_audit as phase439


VOCABULARY = (
    "SOURCE", "CODE", "PRIME", "KEY", "PASSWORD", "BLUE", "YELLOW",
    "RABBIT", "HUNTER", "NEXT", "STEP", "GOOD", "LUCK",
)
NEW_INSTRUCTION_VOCABULARY = (
    "SOURCE", "CODE", "PRIME", "KEY", "PASSWORD", "BLUE", "YELLOW",
)
UNITS = ("letters", "words")
BOUNDARIES = ("global", "reset_each_comment")
BASES = (0, 1)
DIRECTIONS = ("forward", "reverse")
RAILS = ("prime", "nonprime")


def is_prime(value):
    if value < 2:
        return False
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 1
    return True


def extract_comments():
    comments = []
    for name in ("seed", "choice"):
        parsed = phase439.parse_source(phase439.RAW_PATHS[name])
        expected = phase439.EXPECTED_COMMENTS[name]
        if parsed["comments"] != [expected]:
            raise AssertionError(f"Phase 439 source comment drifted: {name}")
        comments.append(parsed["comments"][0])
    return tuple(comments)


def normalize(comment, unit):
    if unit == "letters":
        return tuple(re.findall(r"[A-Z]", comment.upper()))
    if unit == "words":
        return tuple(re.findall(r"[A-Z]+", comment.upper()))
    raise ValueError(unit)


def retain(sequence, base, direction, rail):
    sequence = tuple(sequence if direction == "forward" else reversed(sequence))
    keep_prime = rail == "prime"
    return tuple(
        item for index, item in enumerate(sequence)
        if is_prime(index + base) == keep_prime
    )


def index_of_coincidence(text):
    if len(text) < 2:
        return 0.0
    counts = {character: text.count(character) for character in set(text)}
    return sum(count * (count - 1) for count in counts.values()) / (len(text) * (len(text) - 1))


def make_row(comments, unit, boundary, base, direction, rail):
    normalized = tuple(normalize(comment, unit) for comment in comments)
    if boundary == "global":
        source_parts = (tuple(item for part in normalized for item in part),)
    else:
        source_parts = normalized
    selected_parts = tuple(retain(part, base, direction, rail) for part in source_parts)
    selected = tuple(item for part in selected_parts for item in part)
    machine = "".join(selected)
    displayed = machine if unit == "letters" else " ".join(selected)
    source_machine = "".join(item for part in source_parts for item in part)
    vocabulary = {token: machine.count(token) for token in VOCABULARY if token in machine}
    variant_id = f"{unit}:{boundary}:base{base}:{direction}:{rail}"
    return {
        "id": variant_id,
        "unit": unit,
        "boundary": boundary,
        "index_base": base,
        "direction": direction,
        "rail": rail,
        "source_unit_count": sum(len(part) for part in source_parts),
        "selected_unit_count": len(selected),
        "selected_words": selected if unit == "words" else (),
        "display": displayed,
        "machine": machine,
        "machine_length": len(machine),
        "sha256": hashlib.sha256(machine.encode("ascii")).hexdigest(),
        "vowel_fraction": (
            sum(character in "AEIOU" for character in machine) / len(machine)
            if machine else 0.0
        ),
        "index_of_coincidence": index_of_coincidence(machine),
        "vocabulary_occurrences": vocabulary,
        "new_instruction_tokens": tuple(
            token for token in NEW_INSTRUCTION_VOCABULARY
            if token in machine and token not in source_machine
        ),
    }


def collision_report(rows):
    exact = defaultdict(list)
    for row in rows:
        exact[row["machine"]].append(row["id"])
    exact_classes = tuple(
        tuple(ids) for ids in exact.values() if len(ids) > 1
    )
    reverse_pairs = []
    for left_index, left in enumerate(rows):
        for right in rows[left_index + 1:]:
            if left["machine"] and left["machine"] == right["machine"][::-1]:
                reverse_pairs.append((left["id"], right["id"]))
    return {"exact_equality_classes": exact_classes, "reverse_equality_pairs": tuple(reverse_pairs)}


def audit():
    comments = extract_comments()
    rows = tuple(
        make_row(comments, unit, boundary, base, direction, rail)
        for unit in UNITS
        for boundary in BOUNDARIES
        for base in BASES
        for direction in DIRECTIONS
        for rail in RAILS
    )
    collisions = collision_report(rows)
    new_hits = tuple(
        {"id": row["id"], "tokens": row["new_instruction_tokens"]}
        for row in rows if row["new_instruction_tokens"]
    )
    inherited_hits = tuple(
        {"id": row["id"], "tokens": tuple(row["vocabulary_occurrences"])}
        for row in rows if row["vocabulary_occurrences"]
    )
    if new_hits:
        decision = "exact_new_instruction_token_present"
    elif collisions["exact_equality_classes"] or collisions["reverse_equality_pairs"]:
        decision = "structural_collision_requires_review"
    else:
        decision = "only_inherited_or_flavor_tokens"
    return {
        "phase": 440,
        "classification": "exploratory_not_instruction_licensed",
        "source_comments": comments,
        "variant_count": len(rows),
        "rows": rows,
        "new_instruction_token_hits": new_hits,
        "inherited_or_flavor_token_hits": inherited_hits,
        "collisions": collisions,
        "decision": decision,
        "password_materials_generated": 0,
        "oracle_calls": 0,
        "docker_touched": False,
        "gpu_touched": False,
    }


def self_test():
    report = audit()
    assert report["source_comments"] == (
        phase439.EXPECTED_COMMENTS["seed"], phase439.EXPECTED_COMMENTS["choice"]
    )
    assert report["variant_count"] == 32
    assert len({row["id"] for row in report["rows"]}) == 32
    for unit in UNITS:
        assert sum(row["unit"] == unit for row in report["rows"]) == 16
    paired = defaultdict(dict)
    for row in report["rows"]:
        key = (row["unit"], row["boundary"], row["index_base"], row["direction"])
        paired[key][row["rail"]] = row["selected_unit_count"]
    for key, rails in paired.items():
        source_count = next(
            row["source_unit_count"] for row in report["rows"]
            if (row["unit"], row["boundary"], row["index_base"], row["direction"]) == key
        )
        assert rails["prime"] + rails["nonprime"] == source_count
    assert report["password_materials_generated"] == report["oracle_calls"] == 0
    assert report["docker_touched"] is report["gpu_touched"] is False
    print(f"[*] Phase 440 self-test OK: 32 frozen prime readings; decision={report['decision']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    if args.self_test:
        self_test()
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    elif not args.self_test:
        print(payload, end="")


if __name__ == "__main__":
    main()
