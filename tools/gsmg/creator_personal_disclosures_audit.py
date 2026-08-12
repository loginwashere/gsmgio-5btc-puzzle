#!/usr/bin/env python3
"""Validate creator-authored off-puzzle personal disclosures: Netherlands
residency/nationality and casual references to recreational/psychedelic
substance use.

Both are ordinary chat content, not puzzle mechanics -- they carry
`disposition: provenance-only` in the Fact Ledger. Inclusion is bounded to
messages authored by the stable creator ID, present verbatim in the raw
export, and not already explained by an unrelated topic (e.g. a search-engine
result mentioning a country is not a self-disclosure).

Every indexed record is tied to Telegram's stable creator user ID; each
entry's required text fragment is checked against the raw message text at
run time, so a summary can never silently drift from the source.
"""

import argparse
import json
from pathlib import Path

CREATOR_ID = "user9815232"
SOLVER_EXPORT_DIR = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-26"
)
SUPPORT_EXPORT_DIR = Path(
    "/home/loginwashere/Downloads/Telegram Desktop/ChatExport_2026-07-29 (2)"
)

# id: (export, required text fragment)
SUBSTANCE_INDEX = {
    6846: ("solver", "psilocybe azurescens and mao inhibitors"),
    23152: ("solver", "you're hallucinating. Is it the mescaline?"),
    66606: ("solver", "not lsd or ayahuasca with mao-inhibitors"),
    66940: ("solver", "ketamine is immune to me by now"),
    66944: ("solver", "nearly optimal drug setup"),
    66969: ("solver", "70mq lsd, 100 mg mdma and bit of ket"),
    66976: ("solver", 'in Dutch its called "geestveruimend"'),
}

# id: (export, required text fragment) -- curated to first-person/explicit
# statements only; the frequent "ofcourse" Dutch-English spelling tell is
# reported as a separate aggregate count, not indexed message-by-message.
DUTCH_LOCATION_INDEX = {
    1076: ("support", "Sorry for dutch"),
    1708: ("support", "Ah dutch, sorry"),
    5515: ("support", "You can pm us in dutch"),
    11423: ("support", "Enough Dutch for now"),
    13937: ("support", "real dutch blood"),
    13942: ("support", "the dutch are basterds"),
    16082: ("support", "abnamro.nl"),
    22482: ("support", "utc not cet"),
    25644: ("support", "The dutch law doesn't even a legal framework"),
    29295: ("support", "daytrading in the netherlands"),
    41268: ("support", "'iets' in Dutch"),
    41557: ("support", "I'm in the Netherlands even"),
    41572: ("support", "dutch island without Corona"),
    42511: ("support", "Albert Heijn and a Jumbo"),
    42934: ("support", "PM us, then we can assist in Dutch"),
    44210: ("support", "You can PM for Dutch"),
    45523: ("support", '"proefkonijn" in dutch'),
    52684: ("support", "most of us are indeed"),
    59061: ("support", "back in the NL"),
    66976: ("solver", 'in Dutch its called "geestveruimend"'),
}

# Weaker/ambiguous hits deliberately excluded from the frozen index above,
# recorded here so a future pass does not silently re-discover and
# overweight them: msg 32695 (solver, "festival thingy in the Netherlands")
# is commentary on a PimEyes search result, not self-disclosure; msg 49176
# (solver, Dutch carrot trivia) is a historical fact shared, not a personal
# claim. Neither is required by any self-test assertion below.

OFCOURSE_KEYWORD = "ofcourse"


def plain_text(message):
    entities = message.get("text_entities") or []
    return "".join(entity.get("text", "") for entity in entities)


def load_export(export_dir):
    with open(Path(export_dir) / "result.json", encoding="utf-8") as handle:
        return json.load(handle)


def _messages_by_id(data):
    return {message["id"]: message for message in data["messages"]}


def check_index(index, exports):
    results = {}
    for message_id, (export_label, fragment) in index.items():
        data = exports[export_label]
        message = _messages_by_id(data).get(message_id)
        if message is None:
            results[message_id] = {"found": False, "reason": "message id not in export"}
            continue
        if message.get("from_id") != CREATOR_ID:
            results[message_id] = {
                "found": False,
                "reason": f"from_id={message.get('from_id')!r}, not creator",
            }
            continue
        text = plain_text(message)
        results[message_id] = {
            "found": fragment in text,
            "export": export_label,
            "date": message.get("date"),
            "text": text,
        }
    return results


def count_ofcourse(data):
    count = 0
    for message in data["messages"]:
        if message.get("from_id") != CREATOR_ID:
            continue
        if OFCOURSE_KEYWORD in plain_text(message).lower():
            count += 1
    return count


def audit(solver_export_dir=SOLVER_EXPORT_DIR, support_export_dir=SUPPORT_EXPORT_DIR):
    exports = {
        "solver": load_export(solver_export_dir),
        "support": load_export(support_export_dir),
    }
    substance_results = check_index(SUBSTANCE_INDEX, exports)
    dutch_results = check_index(DUTCH_LOCATION_INDEX, exports)
    return {
        "substance": substance_results,
        "dutch_location": dutch_results,
        "ofcourse_count": {
            "solver": count_ofcourse(exports["solver"]),
            "support": count_ofcourse(exports["support"]),
        },
    }


def print_report(report):
    print("Creator personal-disclosures audit")
    print()
    print(f"Substance references ({len(report['substance'])} indexed):")
    for message_id, result in sorted(report["substance"].items()):
        status = "OK" if result.get("found") else "FAIL"
        print(f"  [{status}] {message_id} {result.get('date', '')}: "
              f"{result.get('text', result.get('reason'))!r:.120}")
    print()
    print(f"Netherlands/Dutch self-disclosures ({len(report['dutch_location'])} indexed):")
    for message_id, result in sorted(report["dutch_location"].items()):
        status = "OK" if result.get("found") else "FAIL"
        print(f"  [{status}] {message_id} {result.get('date', '')}: "
              f"{result.get('text', result.get('reason'))!r:.120}")
    print()
    print(f"'ofcourse' spelling tell (creator messages, aggregate): "
          f"solver={report['ofcourse_count']['solver']}, "
          f"support={report['ofcourse_count']['support']}")


def self_test():
    report = audit()
    for message_id, result in report["substance"].items():
        assert result["found"], (message_id, result)
    for message_id, result in report["dutch_location"].items():
        assert result["found"], (message_id, result)
    assert len(report["substance"]) == 7
    assert len(report["dutch_location"]) == 20
    assert report["ofcourse_count"]["support"] >= 20, report["ofcourse_count"]
    print(
        f"[*] self-test OK: {len(report['substance'])} substance references and "
        f"{len(report['dutch_location'])} Netherlands/Dutch disclosures verified "
        f"verbatim against the raw export, all creator-authored "
        f"({CREATOR_ID}); 'ofcourse' tell count "
        f"solver={report['ofcourse_count']['solver']} "
        f"support={report['ofcourse_count']['support']}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    print_report(audit())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
