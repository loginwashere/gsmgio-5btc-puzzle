#!/usr/bin/env python3
"""Audit local operand binding in the authenticated SalPhaseIon stream.

This is a structural grammar audit, not a transform or password sweep. It
imports the byte-exact page segmentation and enumerates a closed family over
four genuine syntax ambiguities: matrix-instruction fixity, the role of
``thispassword``, the SHA operand, and the unresolved trailing ``anstoo``.

A reading is strictly supported only if no literal remains unresolved and no
community expansion or operand override is introduced.
"""

import argparse
from dataclasses import dataclass
from itertools import product
from pathlib import Path

from page_structure_audit import (
    DEFAULT_HTML,
    HASH_SUFFIX,
    audit as audit_page,
)

EXPECTED_SEGMENTS = (
    "dbbi",
    "abba_matrix_instruction",
    "faed",
    "z_separator_1",
    "decimal_instruction_1",
    "z_separator_2",
    "decimal_instruction_2",
    "z_separator_3",
    "hash_prefix",
    "salphaseion_aes_prefix",
    "abba_enter_instruction",
    "salphaseion_aes_suffix",
    "hash_suffix",
)


@dataclass(frozen=True)
class BindingModel:
    name: str
    matrix_role: str
    password_role: str
    sha_operand: str
    tail_role: str
    unsupported_assumptions: tuple[str, ...]
    ambiguous_fragments: tuple[str, ...]

    @property
    def structurally_total(self):
        return not self.ambiguous_fragments

    @property
    def strictly_supported(self):
        return self.structurally_total and not self.unsupported_assumptions


def segment_names(page_report):
    return tuple(
        segment["name"]
        for segment in page_report["salphaseion"]["segments"]
    )


def fixed_local_bindings(page_report):
    segments = page_report["salphaseion"]["segments"]
    by_name = {segment["name"]: segment for segment in segments}
    if segment_names(page_report) != EXPECTED_SEGMENTS:
        raise AssertionError("authenticated SalPhaseIon segment order changed")
    if by_name["abba_matrix_instruction"]["decoded"] != "matrixsumlist":
        raise AssertionError("matrix instruction changed")
    if (
        by_name["decimal_instruction_1"]["decoded"]
        != "lastwordsbeforearchichoice"
    ):
        raise AssertionError("last-words instruction changed")
    if by_name["decimal_instruction_2"]["decoded"] != "thispassword":
        raise AssertionError("password label changed")
    if by_name["abba_enter_instruction"]["decoded"] != "enter":
        raise AssertionError("enter instruction changed")
    if (
        by_name["hash_prefix"]["decoded"]
        != "sha256 our first hint is your last command"
    ):
        raise AssertionError("prefix hash instruction changed")
    if HASH_SUFFIX != "shabefanstoo":
        raise AssertionError("raw suffix fragment changed")

    if (
        by_name["abba_matrix_instruction"]["start"] != by_name["dbbi"]["end"]
        or by_name["faed"]["start"] != by_name["abba_matrix_instruction"]["end"]
    ):
        raise AssertionError("matrixsumlist is no longer exactly between dbbi/faed")
    if (
        by_name["abba_enter_instruction"]["start"]
        != by_name["salphaseion_aes_prefix"]["end"]
        or by_name["salphaseion_aes_suffix"]["start"]
        != by_name["abba_enter_instruction"]["end"]
    ):
        raise AssertionError("enter no longer lies exactly between AES halves")
    if by_name["hash_prefix"]["end"] != by_name["salphaseion_aes_prefix"]["start"]:
        raise AssertionError("prefix hash command is no longer AES-adjacent")
    if by_name["hash_suffix"]["start"] != by_name["salphaseion_aes_suffix"]["end"]:
        raise AssertionError("suffix hash command is no longer AES-adjacent")

    return (
        "dbbi [matrixsumlist] faed (fixity unresolved)",
        "faed [lastwordsbeforearchichoice] [thispassword] "
        "(target/result role unresolved)",
        "enter(aes_prefix,aes_suffix) -> salphaseion_blob",
        "sha256 our first hint is your last command before salphaseion_blob",
        "trailing raw shabefanstoo after salphaseion_blob "
        "(shabef -> sha256; anstoo unresolved)",
    )


def candidate_models(page_report):
    fixed_local_bindings(page_report)
    matrix_roles = (
        "postfix_to_dbbi",
        "prefix_to_faed",
        "infix_dbbi_faed",
    )
    password_roles = (
        "password_for_faed",
        "faed_answer_is_password",
        "password_for_salph_blob",
    )
    sha_operands = (
        "explicit_first_hint_equals_last_command",
        "preceding_thispassword_result",
        "preceding_phase_answer",
    )
    tail_roles = (
        "literal_anstoo_unresolved",
        "community_expansion_answer_too",
    )
    models = []
    for matrix_role, password_role, sha_operand, tail_role in product(
        matrix_roles,
        password_roles,
        sha_operands,
        tail_roles,
    ):
        unsupported = []
        ambiguous = []
        if sha_operand != "explicit_first_hint_equals_last_command":
            unsupported.append("override explicit SHA operand words")
        if tail_role == "literal_anstoo_unresolved":
            ambiguous.append("anstoo")
        else:
            unsupported.append("expand anstoo to answer too")
        models.append(
            BindingModel(
                name="/".join(
                    (matrix_role, password_role, sha_operand, tail_role)
                ),
                matrix_role=matrix_role,
                password_role=password_role,
                sha_operand=sha_operand,
                tail_role=tail_role,
                unsupported_assumptions=tuple(unsupported),
                ambiguous_fragments=tuple(ambiguous),
            )
        )
    return tuple(models)


def audit(html_path=DEFAULT_HTML):
    page_report = audit_page(html_path)
    models = candidate_models(page_report)
    normalized_stream = "".join(
        HASH_SUFFIX
        if segment["name"] == "hash_suffix"
        else segment["decoded"] or ""
        for segment in page_report["salphaseion"]["segments"]
    ).lower()
    salvation_terms = {
        term: term in normalized_stream
        for term in ("salvation", "vat", "salphaseion")
    }
    structurally_total_models = tuple(
        model.name for model in models if model.structurally_total
    )
    strictly_supported_models = tuple(
        model.name for model in models if model.strictly_supported
    )
    return {
        "source": page_report["source"],
        "segment_names": segment_names(page_report),
        "fixed_local_bindings": fixed_local_bindings(page_report),
        "models": models,
        "structurally_total_models": structurally_total_models,
        "strictly_supported_models": strictly_supported_models,
        "salvation_terms_in_decoded_stream": salvation_terms,
        "verdict": (
            "The exact stream does not select a unique grammar. The closed "
            "3 x 3 x 3 x 2 family contains 54 models; 27 become structurally "
            "total only by expanding 'anstoo' to 'answer too', and none is "
            "strictly supported without an unresolved or extra assumption. "
            "The unresolved edge is not another cipher: it is instruction "
            "fixity/operand scope and the literal meaning of 'anstoo'. "
            "SALVATION is absent from the decoded textarea instructions, so "
            "inserting it as an operand requires external evidence."
        ),
    }


def self_test():
    report = audit()
    assert report["segment_names"] == EXPECTED_SEGMENTS
    assert len(report["models"]) == 54
    assert len(report["structurally_total_models"]) == 27
    assert report["strictly_supported_models"] == ()
    assert report["salvation_terms_in_decoded_stream"] == {
        "salvation": False,
        "vat": False,
        "salphaseion": False,
    }
    assert {
        model.matrix_role for model in report["models"]
    } == {"postfix_to_dbbi", "prefix_to_faed", "infix_dbbi_faed"}
    assert sum(
        model.tail_role == "literal_anstoo_unresolved"
        for model in report["models"]
    ) == 27
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    report = audit(args.html)
    print("[*] fixed local bindings:")
    for binding in report["fixed_local_bindings"]:
        print(f"    {binding}")
    print("[*] bounded grammar family:")
    print(
        f"    models={len(report['models'])}; "
        f"structurally_total={len(report['structurally_total_models'])}; "
        f"strictly_supported={len(report['strictly_supported_models'])}"
    )
    print("    axes: matrix fixity=3; password role=3; SHA operand=3; tail=2")
    print(
        "[*] salvation terms in decoded textarea instructions: "
        f"{report['salvation_terms_in_decoded_stream']}"
    )
    print(
        "[*] structurally total models require community expansion "
        f"'anstoo' -> 'answer too': {len(report['structurally_total_models'])}"
    )
    print(f"[*] verdict: {report['verdict']}")
    if args.self_test:
        print("[*] self-test OK")


if __name__ == "__main__":
    main()
