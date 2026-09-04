#!/usr/bin/env python3
"""Phase 468 frozen catalogs: established outputs (List 1) and open-gate
slots (List 2), plus the finalized Lane-B candidate byte records.

Pure data only -- no logic. Evidence-class and slot-kind tags follow the
taxonomy frozen in the Phase 468 preregistration protocol
(doc/Brainstorms/2026-09-01 - Phase 468 Known-Parts Cross-Reference
Protocol.md). Only `authenticated_output` and `authenticated_derived` and
`reproduced_conditional` entries are eligible for Output 3 value matching;
`recognition_only`, `candidate_parameter`, `analyst_generated_metadata`,
and `rule_template` are catalogued but excluded by construction.
"""

# Evidence classes: authenticated_output, authenticated_derived,
# reproduced_conditional, recognition_only, candidate_parameter,
# analyst_generated_metadata, rule_template.
ESTABLISHED_OUTPUTS = (
    {"id": "dbbi_raw", "value": "DBBI (91 symbols)", "type": "text",
     "evidence_class": "authenticated_output", "phase": "pre-100",
     "provenance": "literal page textarea segment"},
    {"id": "faed_raw", "value": "FAED (570 symbols)", "type": "text",
     "evidence_class": "authenticated_output", "phase": "pre-100",
     "provenance": "literal page textarea segment"},
    {"id": "ciao_bella_o", "value": "CIAO BELLA O", "type": "text",
     "evidence_class": "authenticated_output", "phase": 236,
     "provenance": "authenticated page text"},
    {"id": "matrix_23_16_7", "value": "[23,16,7]", "type": "int_list",
     "evidence_class": "authenticated_derived", "phase": "pre-100",
     "provenance": "sourced dialogue scene, decimal matrix sums"},
    {"id": "matrix_574_061", "value": "[[5,7,4],[0,6,1]]", "type": "int_matrix",
     "evidence_class": "authenticated_derived", "phase": 101,
     "provenance": "six distinct decimal digits, G2 PASS"},
    {"id": "matrix_43_25_18", "value": "[43,25,18]", "type": "int_list",
     "evidence_class": "authenticated_derived", "phase": "pre-200",
     "provenance": "second source matrix's row sums"},
    {"id": "prime_574061", "value": 574061, "type": "integer",
     "evidence_class": "reproduced_conditional", "phase": 0,
     "provenance": "first-piece color aperture decode, dark/blue=1, spiral order"},
    {"id": "prime_311027", "value": 311027, "type": "integer",
     "evidence_class": "reproduced_conditional", "phase": 461,
     "provenance": "quarter-turn (90deg CW) rotation, inverse polarity"},
    {"id": "prime_33414671", "value": 33414671, "type": "integer",
     "evidence_class": "reproduced_conditional", "phase": 462,
     "provenance": "49-aperture grille, added-rail inverse reading, 270deg, spiral order"},
    {"id": "theflower", "value": "THEFLOWER", "type": "text",
     "evidence_class": "reproduced_conditional", "phase": 461,
     "provenance": "unique hit inside frozen orientation/composition family, Phase 461"},
    {"id": "sum_401", "value": 401, "type": "integer",
     "evidence_class": "reproduced_conditional", "phase": 263,
     "provenance": "Roman-projection sum (CDI), title-C mechanism unselected"},
    {"id": "sum_400", "value": 400, "type": "integer",
     "evidence_class": "reproduced_conditional", "phase": 263,
     "provenance": "Roman-projection sum (CD), title-C mechanism unselected"},
    {"id": "sum_73_fefe", "value": 73, "type": "integer",
     "evidence_class": "reproduced_conditional", "phase": 263,
     "provenance": "FEFE's fitted sum; winning rule does not reproduce it (gives 100), Phase 450"},
    {"id": "ff67_pair", "value": "(255,103) / FF67", "type": "int_pair",
     "evidence_class": "reproduced_conditional", "phase": "pre-300",
     "provenance": "matrix product, unselected multiplication op + byte consumer; unusual_but_unselected, Phase 453"},
    {"id": "kit_reversed", "value": "KIT", "type": "text",
     "evidence_class": "reproduced_conditional", "phase": "pre-300",
     "provenance": "second matrix list difference, A1Z26 + reversal; null-sensitive, Phase 453"},
    {"id": "ggn_tuple", "value": "ggn", "type": "text",
     "evidence_class": "reproduced_conditional", "phase": "pre-300",
     "provenance": "flattened FEFE tuple {1,4,21}; common under matched null, Phase 453"},
    {"id": "batch", "value": "BATCH", "type": "text",
     "evidence_class": "recognition_only", "phase": "pre-300",
     "provenance": "community G-shadow/element-rebus extraction"},
    {"id": "youwon", "value": "YOUWON", "type": "text",
     "evidence_class": "recognition_only", "phase": 460,
     "provenance": "community-derived lexical delimiter, no creator authentication"},
    {"id": "salph_103_digit_stream", "value": "<103 digits>", "type": "text",
     "evidence_class": "reproduced_conditional", "phase": 460,
     "provenance": "conditional on non-grid-native YOUWON|X boundary; grid-native cut gives 101"},
    {"id": "exec_order_13224", "value": "13224", "type": "text",
     "evidence_class": "recognition_only", "phase": 460,
     "provenance": "explicit semantic recognition, not an instruction, per GSMG_YOUWON_SALPH_103_ALIGNMENT_AUDIT.md"},
    {"id": "faed_escape_gi", "value": "{g,i}", "type": "pair",
     "evidence_class": "candidate_parameter", "phase": 449,
     "provenance": "independently-best working prior, code-IC rank 1/29, not authenticated-selected"},
    {"id": "faed_escape_he", "value": "{h,e}", "type": "pair",
     "evidence_class": "candidate_parameter", "phase": 449,
     "provenance": "exactly mirror9({b,e}) under the Architect-mirror route, disfavored, unselected"},
    {"id": "dbbi_escape_be", "value": "{b,e}", "type": "pair",
     "evidence_class": "candidate_parameter", "phase": "pre-200",
     "provenance": "DBBI's own independently-best, directly legible escape pair"},
    {"id": "btcseed_p90_p91_q472", "value": "P90/P91/Q472/CONTROL285", "type": "text",
     "evidence_class": "reproduced_conditional", "phase": 386,
     "provenance": "Bifid-decrypt fields; period-non-robust per Phase 408"},
    {"id": "dbbi_faed_sha256", "value": "SHA-256(DBBI)/SHA-256(FAED)", "type": "hex",
     "evidence_class": "analyst_generated_metadata", "phase": "n/a",
     "provenance": "produced by this project's own tooling, not the puzzle"},
    {"id": "phase410_kdf_template", "value": "SHA256->EVP_BytesToKey->AES-256-CBC->PKCS7", "type": "template",
     "evidence_class": "rule_template", "phase": 410,
     "provenance": "cryptographic profile of the three solved boundaries (Phase 2, 3, 3.2)"},
)

# Slot kinds: operator, parameter_value, representation_or_serialization,
# consumer_interface, selector. Only parameter_value slots are eligible for
# Output 3 value matching. G-X2SH-001 is excluded outright (closed
# secondary reading of an already-solved phase, not live frontier).
OPEN_GATE_SLOTS = (
    {"gate": "G-MSL-001", "slots": (
        {"name": "matrix_dimensions", "kind": "parameter_value"},
        {"name": "traversal_order", "kind": "selector"},
        {"name": "value_mapping_alphabet", "kind": "representation_or_serialization"},
        {"name": "aggregation_op", "kind": "operator"},
        {"name": "serialization", "kind": "representation_or_serialization"},
        {"name": "consumer", "kind": "consumer_interface"},
    )},
    {"gate": "G-FLOWER-001", "slots": (
        {"name": "quarter_turn_selection", "kind": "selector"},
        {"name": "frame_parity_affix_composition", "kind": "selector"},
        {"name": "consumer", "kind": "consumer_interface"},
    )},
    {"gate": "G-ARCH-001", "slots": (
        {"name": "mirror_operation", "kind": "operator"},
        {"name": "thispassword_role", "kind": "selector"},
    )},
    {"gate": "G-ESC-001", "slots": (
        {"name": "escape_pair_selection", "kind": "selector"},
    )},
    {"gate": "G-YIN-001", "slots": (
        {"name": "cross_stream_operator", "kind": "operator"},
    )},
    {"gate": "G-PRIME-001", "slots": (
        {"name": "consumer", "kind": "consumer_interface"},
        {"name": "roman_title_c_selector", "kind": "selector"},
    )},
    {"gate": "G-MATPROD-001", "slots": (
        {"name": "multiplication_vs_other", "kind": "operator"},
        {"name": "byte_consumer", "kind": "consumer_interface"},
    )},
    {"gate": "G-KIT-001", "slots": (
        {"name": "subtraction_reversal_operator", "kind": "operator"},
        {"name": "a1z26_mapping", "kind": "representation_or_serialization"},
    )},
    {"gate": "G-GGN-001", "slots": (
        {"name": "indexing_convention", "kind": "selector"},
        {"name": "g_to_group_generator_mapping", "kind": "operator"},
        {"name": "scalar_k", "kind": "parameter_value"},
        {"name": "negation", "kind": "operator"},
        {"name": "curve_selection", "kind": "selector"},
    )},
    {"gate": "G-X2SH-001", "slots": (),
     "excluded": "closed_secondary_reading_not_live_frontier"},
)

# Lane B: finalized candidate byte records (Fix 4, one type per candidate).
# YOUWON and 13224 are excluded (recognition_only). P90/P91/Q472/full
# BTCSEED decode are excluded (N/A too long for direct-scalar; closed
# negative for sha256-scalar/bip32-seed per Phase 400, P00400.md -- cited,
# not re-run). salph_103_digit_stream is text-only, N/A too long for
# direct-scalar (its sha256-scalar/bip32-seed interpretations still run).
LANE_B_CANDIDATES = (
    {"id": "prime_574061", "type": "integer", "canonical_text": "574061",
     "value": 574061, "direct_bytes_before_padding_hex": "08c26d"},
    {"id": "prime_311027", "type": "integer", "canonical_text": "311027",
     "value": 311027, "direct_bytes_before_padding_hex": "04bef3"},
    {"id": "prime_33414671", "type": "integer", "canonical_text": "33414671",
     "value": 33414671, "direct_bytes_before_padding_hex": "01fdde0f"},
    {"id": "theflower", "type": "text", "canonical_text": "THEFLOWER",
     "direct_bytes_before_padding_hex": "544845464c4f574552"},
    {"id": "salph_103_digit_stream", "type": "text",
     "canonical_text": (
         "2431611237214124471074211414221316122016161124131025122622123518"
         "414242545191121152243113224101217201971"
     ),
     "direct_scalar_status": "not_applicable_too_long"},
)

EXCLUDED_LANE_B_CANDIDATES = (
    {"id": "youwon", "reason": "recognition_only, ineligible for Output-3 value matching"},
    {"id": "exec_order_13224", "reason": "recognition_only, ineligible for Output-3 value matching"},
    {"id": "btcseed_p90_p91_q472", "reason": (
        "direct-scalar: N/A, exceeds 32 bytes for all four fields; "
        "sha256-scalar and bip32-seed: closed negative, Phase 400 "
        "(tools/gsmg/findings/P00400.md), 96032 checks, 0 hits -- cited, not re-run"
    )},
)
