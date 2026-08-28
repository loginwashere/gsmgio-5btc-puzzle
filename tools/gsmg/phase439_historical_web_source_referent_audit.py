#!/usr/bin/env python3
"""Phase 439: eligibility of creator-served historical web page source."""

import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

from support_group_export_delta_audit import (
    CREATOR_ID,
    DEFAULT_EXPORT_DIR as DEFAULT_SUPPORT_EXPORT_DIR,
    load_export as load_support_export,
    plain_text as support_plain_text,
)
from telegram_export_manifest import (
    DEFAULT_EXPORT_DIR as DEFAULT_SOLVER_EXPORT_DIR,
    load_export as load_solver_export,
    plain_text as solver_plain_text,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
MIRROR_ROOT = REPO_ROOT.parent / "gsmg-site-mirror"
SEED_NAME = "theseedisplanted.html"
CHOICE_NAME = (
    "choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutavery"
    "specialdessertiwroteitmyself.html"
)
RAW_PATHS = {"seed": MIRROR_ROOT / SEED_NAME, "choice": MIRROR_ROOT / CHOICE_NAME}
NORMALIZED_PATHS = {
    "seed": REPO_ROOT / "doc" / "html" / SEED_NAME,
    "choice": REPO_ROOT / "doc" / "html" / CHOICE_NAME,
}
EXPECTED_FILES = {
    "raw_seed": (1585, "5356c88769137ec82953888d7c5b9f18b0fa00019fad7591cc6aaaaf91463136"),
    "raw_choice": (9902, "7237ce18a62f16dc55d94a2594da4256543b7dc7b34e4e59783473c34c7fbf9b"),
    "normalized_seed": (1153, "c38fa27671a2040120b45bf70c6f7c04749087255ffe86673b28322970ad2bb4"),
    "normalized_choice": (9134, "647744a2957219a4084ede994719124e7445bab1dfdeb68258fbeff2615a8d43"),
}
EXPECTED_COMMENTS = {
    "seed": "Nice to see you around! Good luck little bunny hunter ;)",
    "choice": "You made it to the next step! Good luck little bunny hunter ;)",
}
COMMENT_SUFFIX = "Good luck little bunny hunter ;)"
COMMENT_PREFIXES = {
    "seed": "Nice to see you around!",
    "choice": "You made it to the next step!",
}
SOLVER_TERMS = (
    "nice to see you around",
    "you made it to the next step",
    "good luck little bunny hunter",
    "html source",
    "source code",
)
EXPECTED_SOLVER_COUNTS = {
    "nice to see you around": 10,
    "you made it to the next step": 4,
    "good luck little bunny hunter": 15,
    "html source": 3,
    "source code": 141,
}
GATE_NAMES = (
    "creator_puzzle_artifact",
    "chronologically_returnable",
    "stable_representation",
    "locally_selected",
    "operator_fixed",
    "unit_boundary_fixed",
    "consumer_fixed",
    "genuinely_uncovered",
)


class SourceParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.comments = []
        self.forms = []
        self.inputs = []
        self.metas = []
        self.scripts = []
        self.textareas = []

    def handle_comment(self, data):
        self.comments.append(data.strip())

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        record = dict(attrs)
        if tag == "form":
            self.forms.append(record)
        elif tag == "input":
            self.inputs.append(record)
        elif tag == "meta":
            self.metas.append(record)
        elif tag == "script":
            self.scripts.append(record)
        elif tag == "textarea":
            self.textareas.append(record)


def file_record(path):
    raw = Path(path).read_bytes()
    return {"path": str(path), "length": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def parse_source(path):
    parser = SourceParser()
    parser.feed(Path(path).read_text(encoding="utf-8"))
    csrf_meta = [m.get("content") for m in parser.metas if m.get("name") == "csrf-token"]
    csrf_inputs = [i.get("value") for i in parser.inputs if i.get("name") == "_token"]
    return {
        "comments": parser.comments,
        "forms": parser.forms,
        "inputs": parser.inputs,
        "csrf_meta_values": csrf_meta,
        "csrf_input_values": csrf_inputs,
        "scripts": parser.scripts,
        "textarea_count": len(parser.textareas),
        "external_script_count": sum(bool(s.get("src")) for s in parser.scripts),
        "inline_script_count": sum(not s.get("src") for s in parser.scripts),
        "puzzle_authored_script_count": sum(
            bool(s.get("src")) and "cloudflareinsights.com" not in s.get("src", "")
            for s in parser.scripts
        ),
    }


def support_constraints(export_dir=DEFAULT_SUPPORT_EXPORT_DIR):
    data = load_support_export(export_dir)
    by_id = {message["id"]: message for message in data["messages"]}
    expected = {
        28703: "against bruteforcing",
        28794: "Won't work",
        28812: "All the info you need is there.",
    }
    records = {}
    for message_id, fragment in expected.items():
        message = by_id[message_id]
        text = support_plain_text(message)
        if message.get("from_id") != CREATOR_ID or fragment not in text:
            raise AssertionError(f"support constraint drifted: {message_id}")
        records[str(message_id)] = {
            "date": message["date"],
            "reply_to": message.get("reply_to_message_id"),
            "text": text,
        }
    if by_id[28794].get("reply_to_message_id") != 28791:
        raise AssertionError("general-site-scan reply edge drifted")
    if "scanned gsmg entirely" not in support_plain_text(by_id[28791]):
        raise AssertionError("general-site-scan parent drifted")
    return records


def solver_term_evidence(export_dir=DEFAULT_SOLVER_EXPORT_DIR):
    data = load_solver_export(export_dir)
    messages = data["messages"]
    results = {}
    for term in SOLVER_TERMS:
        hits = [message for message in messages if term in solver_plain_text(message).lower()]
        hit_ids = {message["id"] for message in hits}
        creator_hits = [message["id"] for message in hits if message.get("from_id") == CREATOR_ID]
        creator_replies = [
            message["id"] for message in messages
            if message.get("from_id") == CREATOR_ID
            and message.get("reply_to_message_id") in hit_ids
        ]
        if len(hits) != EXPECTED_SOLVER_COUNTS[term]:
            raise AssertionError(f"solver fixed-term evidence drifted: {term}")
        results[term] = {
            "hit_count": len(hits),
            "creator_authored_hit_ids": creator_hits,
            "creator_direct_reply_ids": creator_replies,
        }
    return results


def gates(**values):
    if set(values) != set(GATE_NAMES):
        raise AssertionError("eligibility gate schema drifted")
    return values


def candidate_rows():
    common_fail = dict(
        locally_selected=False,
        operator_fixed=False,
        unit_boundary_fixed=False,
        consumer_fixed=False,
    )
    return (
        {
            "id": "raw_seed_html",
            "object": "raw historical theseedisplanted HTML response",
            "coverage": "Page mechanics and visible rebus are audited; whole raw source as a prime operand is unregistered.",
            "gates": gates(creator_puzzle_artifact=True, chronologically_returnable=True, stable_representation=False, genuinely_uncovered=True, **common_fail),
        },
        {
            "id": "raw_choice_html",
            "object": "raw historical choice...iwroteitmyself HTML response",
            "coverage": "Textarea payloads are solved/audited; whole raw source as a prime operand is unregistered.",
            "gates": gates(creator_puzzle_artifact=True, chronologically_returnable=True, stable_representation=False, genuinely_uncovered=True, **common_fail),
        },
        {
            "id": "ordered_prior_html_pair",
            "object": "seed HTML followed by choice HTML",
            "coverage": "No registered whole-source pair extraction; deployment/request fields make raw concatenation noncanonical.",
            "gates": gates(creator_puzzle_artifact=True, chronologically_returnable=True, stable_representation=False, genuinely_uncovered=True, **common_fail),
        },
        {
            "id": "ordered_source_comment_pair",
            "object": "the two prior source-only bunny-hunter comments in stage order",
            "coverage": "Exact source-only pair is not in a registered prime or password family.",
            "gates": gates(creator_puzzle_artifact=True, chronologically_returnable=True, stable_representation=True, genuinely_uncovered=True, **common_fail),
        },
        {
            "id": "csrf_values",
            "object": "CSRF metadata/input token values",
            "coverage": "Creator identifies the changing mechanism as anti-bruteforce state, not puzzle material.",
            "gates": gates(creator_puzzle_artifact=False, chronologically_returnable=True, stable_representation=False, genuinely_uncovered=True, **common_fail),
        },
        {
            "id": "markup_and_cloudflare",
            "object": "HTML tags/attributes plus Cloudflare beacon material",
            "coverage": "Page structure is audited; Cloudflare is external deployment analytics and normalization is unfixed.",
            "gates": gates(creator_puzzle_artifact=False, chronologically_returnable=True, stable_representation=False, genuinely_uncovered=True, **common_fail),
        },
        {
            "id": "textarea_ciphertexts",
            "object": "Phase 2 and Phase 3 textarea ciphertexts",
            "coverage": "Authenticated exact containers and their solved toolchain are covered by Phase 410.",
            "gates": gates(creator_puzzle_artifact=True, chronologically_returnable=True, stable_representation=True, locally_selected=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=True, genuinely_uncovered=False),
        },
        {
            "id": "original_lowercase_puzzle",
            "object": "original lowercase /puzzle response",
            "coverage": "It is a bare PNG and its grounded prime/color projections are already audited.",
            "gates": gates(creator_puzzle_artifact=True, chronologically_returnable=True, stable_representation=True, locally_selected=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=True, genuinely_uncovered=False),
        },
        {
            "id": "restored_puzzle_html",
            "object": "post-restoration Puzzle.html",
            "coverage": "Postdates the instruction and operator attribution is unresolved.",
            "gates": gates(creator_puzzle_artifact=False, chronologically_returnable=False, stable_representation=True, genuinely_uncovered=True, **common_fail),
        },
        {
            "id": "salphaseion_html",
            "object": "SalPhaseIon/Cosmic HTML source",
            "coverage": "Extensively audited, but downstream of the Architect instruction under literal RETURN chronology.",
            "gates": gates(creator_puzzle_artifact=True, chronologically_returnable=False, stable_representation=True, locally_selected=False, operator_fixed=False, unit_boundary_fixed=False, consumer_fixed=True, genuinely_uncovered=False),
        },
        {
            "id": "general_site_javascript",
            "object": "general GSMG JavaScript and site assets",
            "coverage": "Broad site scanning is creator-disfavored; no selected historical JS operand is authenticated.",
            "gates": gates(creator_puzzle_artifact=False, chronologically_returnable=True, stable_representation=False, genuinely_uncovered=True, **common_fail),
        },
    )


def audit(support_dir=DEFAULT_SUPPORT_EXPORT_DIR, solver_dir=DEFAULT_SOLVER_EXPORT_DIR):
    files = {
        "raw_seed": file_record(RAW_PATHS["seed"]),
        "raw_choice": file_record(RAW_PATHS["choice"]),
        "normalized_seed": file_record(NORMALIZED_PATHS["seed"]),
        "normalized_choice": file_record(NORMALIZED_PATHS["choice"]),
    }
    for name, (length, digest) in EXPECTED_FILES.items():
        if (files[name]["length"], files[name]["sha256"]) != (length, digest):
            raise AssertionError(f"historical source file drifted: {name}")
    structures = {name: parse_source(path) for name, path in RAW_PATHS.items()}
    for name, expected in EXPECTED_COMMENTS.items():
        if structures[name]["comments"] != [expected]:
            raise AssertionError(f"source-only comment drifted: {name}")
    if structures["seed"]["textarea_count"] != 0 or structures["choice"]["textarea_count"] != 2:
        raise AssertionError("prior-page textarea structure drifted")
    if any(row["inline_script_count"] or row["puzzle_authored_script_count"] for row in structures.values()):
        raise AssertionError("unexpected puzzle-authored or inline JavaScript appeared")

    rows = []
    for row in candidate_rows():
        failed = tuple(name for name in GATE_NAMES if not row["gates"][name])
        rows.append({**row, "failed_gates": failed, "eligible": not failed})
    eligible = tuple(row["id"] for row in rows if row["eligible"])
    newly_registered = tuple(
        row["id"] for row in rows
        if row["gates"]["genuinely_uncovered"]
        and row["gates"]["creator_puzzle_artifact"]
        and row["gates"]["chronologically_returnable"]
    )
    decision = (
        "eligible_source_referent_requires_execution_preregistration"
        if eligible else "new_source_referent_registered_but_ineligible"
    )
    return {
        "phase": 439,
        "files": files,
        "raw_source_structures": structures,
        "comment_pair": {
            "stage_order": (EXPECTED_COMMENTS["seed"], EXPECTED_COMMENTS["choice"]),
            "common_suffix": COMMENT_SUFFIX,
            "page_specific_prefixes": COMMENT_PREFIXES,
            "source_only": True,
        },
        "support_creator_constraints": support_constraints(support_dir),
        "solver_fixed_term_evidence": solver_term_evidence(solver_dir),
        "candidate_count": len(rows),
        "gate_names": GATE_NAMES,
        "candidates": tuple(rows),
        "eligible_referents": eligible,
        "newly_registered_historical_source_referents": newly_registered,
        "decision": decision,
        "next_trigger": "new primary evidence must select comments or normalized prior-page source and fix prime mechanics plus consumer",
        "prime_extractions_generated": 0,
        "password_materials_generated": 0,
        "oracle_calls": 0,
        "docker_touched": False,
        "gpu_touched": False,
    }


def self_test():
    report = audit()
    assert report["candidate_count"] == 11
    assert report["eligible_referents"] == ()
    assert report["newly_registered_historical_source_referents"] == (
        "raw_seed_html", "raw_choice_html", "ordered_prior_html_pair", "ordered_source_comment_pair"
    )
    assert report["raw_source_structures"]["seed"]["textarea_count"] == 0
    assert report["raw_source_structures"]["choice"]["textarea_count"] == 2
    assert report["comment_pair"]["common_suffix"] == COMMENT_SUFFIX
    assert all(
        not row["creator_authored_hit_ids"] and not row["creator_direct_reply_ids"]
        for row in report["solver_fixed_term_evidence"].values()
    )
    assert report["decision"] == "new_source_referent_registered_but_ineligible"
    assert report["prime_extractions_generated"] == report["password_materials_generated"] == report["oracle_calls"] == 0
    assert report["docker_touched"] is report["gpu_touched"] is False
    print("[*] Phase 439 self-test OK: 4 historical web-source gaps registered, 0 eligible; no execution")


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
