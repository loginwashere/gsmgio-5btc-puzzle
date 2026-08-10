#!/usr/bin/env python3
"""Permanent regressions for corrected late-stage GSMG audit claims."""

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import architect_choice_boundary_audit
import architect_choice_literal_password_audit
import architect_hye_bye_audit
import architect_yinyang_distinctiveness_audit
import binary_message_export_audit
import checkerboard_code_ic_oracle
import cosmic_raw_digest_checkpoint_audit
import creator_feasibility_envelope_audit
import creator_yingyang_faed_pair_audit
import creator_operator_vocabulary_audit
import dual_channel_consistency_audit
import first_piece_hamming_control_audit
import first_piece_bitplane_audit
import first_piece_ggn_distinctiveness_audit
import first_piece_prime_sum_reconstruction
import first_piece_matrix_product_audit
import first_piece_second_matrixsumlist_audit
import first_piece_event_rail_preservation_audit
import first_piece_png_palette_provenance_audit
import first_piece_shadow_column_rail_audit
import faed_decoder_coverage_audit
import first_piece_even_odd_alphabet_gate_audit
import first_piece_batch_rebus_gate_audit
import first_piece_cefe_checkerboard_gate_audit
import first_piece_overlay_dna_rgb_gate_audit
import first_piece_border_raster_scan_audit
import matrixsum_cumulative_stride_audit
import matrixsum_dbbi_faed_position_audit
import matrixsumlist_provenance_refresh_audit
import matrixsumlist_page_scope_audit
import matrixsumlist_historical_code_audit
import macro_tail_title_insertion_audit
import macro_literal_adjacency_audit
import minimal_macro_chain_audit
import neo_choice_last_words_audit
import neo_smith_equation_audit
import onchain_op_return_provenance_audit
import phase32_column_calibration_audit
import post_yinyang_dataflow_audit
import post_phase217_consistency_audit
import promised_standalone_audit
import prime_sum_fefe_mask_composition_audit
import remaining_structural_avenues_audit
import safenet_luna_hsm_audit
import salphaseion_salvation_role_audit
import salphaseion_presentation_binding_audit
import salphaseion_responsive_wrap_audit
import salphaseion_wayback_history_audit
import spi_cd_initials_audit
import stage0_footer_palette_layer_audit
import stage0_even_sequence_convergence_audit
import stage0_g_shadow_consumer_audit
import stage0_repeated_grayscale_audit
import synthesis_action_paths_audit
import telegram_yellow_blue_matrix_direction_audit
import triangular_matrixsumlist_audit
import urlblob_keywrap_backfill
import visible_referent_delta_audit
import yinyang_cosmic_phase_label_audit
from page_structure_audit import DEFAULT_HTML
from telegram_export_manifest import DEFAULT_EXPORT_DIR
from cb_common import BLOBS, QUARANTINED_BLOBS


class CorrectedClaimTests(unittest.TestCase):
    def test_architect_hye_partial_mirror_gives_bye_but_no_blob_hit(self):
        report = architect_hye_bye_audit.audit()
        controls = report["structural"]["controls"]
        self.assertEqual(
            report["structural"]["fixed"]["partial_mirror_finals"],
            "bye",
        )
        self.assertEqual(controls["but_rows"], 48)
        self.assertEqual(controls["distinct_partial_mirror_outputs_given_but"], 18)
        self.assertEqual(controls["dictionary_outputs_given_but"], ("bye",))
        self.assertFalse(report["structural"]["operation_authored"])
        self.assertEqual(report["oracle"]["keystring_count"], 18)
        self.assertEqual(report["oracle"]["total_hits"], 0)

    @unittest.skipUnless(
        Path(DEFAULT_EXPORT_DIR, "result.json").exists(),
        "complete puzzle-solvers export is unavailable",
    )
    def test_macro_literal_adjacency_does_not_supply_password(self):
        report = macro_literal_adjacency_audit.audit()
        self.assertEqual(
            report["raw"]["after_password_before_youreyes"],
            "itsinfrontof",
        )
        self.assertEqual(report["raw"]["immediately_after_youreyes"], "but")
        self.assertEqual(report["raw"]["hye_count"], 0)
        self.assertEqual(
            report["stable_local_syntax"]["literal_your_eyes_but"],
            ("your", "eyes", "but"),
        )
        self.assertEqual(
            report["stable_local_syntax"]["initials_your_eyes_but"],
            "yeb",
        )
        self.assertFalse(report["gates"]["non_placeholder_password_value"])
        self.assertFalse(report["oracle_authorized"])

    @unittest.skipUnless(
        Path(DEFAULT_EXPORT_DIR, "result.json").exists()
        and creator_feasibility_envelope_audit.SUPPORT_RESULT.exists(),
        "one or both pinned Telegram exports are unavailable",
    )
    def test_creator_feasibility_envelope_separates_exact_claims(self):
        report = creator_feasibility_envelope_audit.audit()
        self.assertEqual(report["offline_solvability"]["status"], "verified")
        self.assertTrue(report["no_new_url"]["reply_edge"])
        self.assertEqual(
            report["visible_referent"]["status"],
            "phrase_verified_referent_unknown",
        )
        self.assertEqual(
            report["moderate_bruteforce"]["status"],
            "not_endgame_endorsed",
        )
        self.assertEqual(
            tuple(
                row["message_id"]
                for row in report["moderate_bruteforce"]["support_group_mentions"]
            ),
            (12697, 28703, 54419),
        )
        self.assertEqual(
            report["moderate_bruteforce"]["stage_count_reply_edge"],
            (28704, 28702),
        )
        self.assertEqual(
            report["rapid_construction"]["status"],
            "two_sloppy_days_verified_retrospectively",
        )
        self.assertFalse(
            report["rapid_construction"]["support_group_retrospective"][
                "contemporaneous"
            ]
        )
        self.assertEqual(
            report["corpus_scope"]["support"]["sha256"],
            creator_feasibility_envelope_audit.EXPECTED_SUPPORT_SHA256,
        )
        self.assertEqual(
            report["corpus_scope"]["support"]["message_count"],
            52851,
        )
        self.assertEqual(
            report["presentation_vocabulary"]["puzzle_geometry_instruction_count"],
            0,
        )
        self.assertEqual(
            report["near_completion"]["status"],
            "verified_conditionally",
        )

    @unittest.skipUnless(
        Path(DEFAULT_EXPORT_DIR, "result.json").exists(),
        "complete Telegram export is unavailable",
    )
    def test_creator_yingyang_faed_pair_is_not_promoted(self):
        report = creator_yingyang_faed_pair_audit.audit()
        self.assertEqual(
            report["lexical_mechanics"]["native_filtered"],
            ("ig", "ag"),
        )
        self.assertEqual(
            report["observed_pair_ranks"]["faed_ranks"]["gi"]["rank"],
            1,
        )
        self.assertEqual(
            report["observed_pair_ranks"]["faed_ranks"]["ag"]["rank"],
            5,
        )
        self.assertEqual(
            report["shared_suffix_controls"]["faed"]["best_joint_suffix"]["shared_symbol"],
            "g",
        )
        self.assertEqual(
            report["shared_suffix_controls"]["dbbi"]["best_joint_suffix"]["shared_symbol"],
            "b",
        )
        self.assertFalse(report["gates"]["authored_spelling_operator"])
        self.assertFalse(report["promotion"]["new_compute_authorized"])

    def test_cosmic_raw_digest_checkpoint_correction(self):
        report = cosmic_raw_digest_checkpoint_audit.audit()
        self.assertEqual(
            report["xor_digest_hex"],
            cosmic_raw_digest_checkpoint_audit.EXPECTED_XOR_HEX,
        )
        self.assertEqual(report["password_lengths"], {"raw32": 32, "hex64": 64})
        decryptions = report["decryptions"]
        self.assertTrue(decryptions["raw32_md5"]["valid_padding"])
        self.assertEqual(decryptions["raw32_md5"]["padding_length"], 1)
        self.assertEqual(
            decryptions["raw32_md5"]["payload_sha256"],
            cosmic_raw_digest_checkpoint_audit.EXPECTED_PAYLOAD_SHA256,
        )
        self.assertFalse(decryptions["raw32_sha256"]["valid_padding"])
        self.assertFalse(decryptions["hex64_md5"]["valid_padding"])
        self.assertFalse(decryptions["hex64_sha256"]["valid_padding"])
        matrix = report["matrix"]
        self.assertEqual(matrix["unused_bits"], "0111010")
        self.assertEqual(
            (matrix["S"], matrix["Wr_one_based"], matrix["Wc_one_based"]),
            (5193, 268603, 268828),
        )
        self.assertEqual(
            (matrix["padding_big_endian"], matrix["padding_little_endian"]),
            (58, 46),
        )
        downstream = report["downstream"]
        self.assertEqual(downstream["shift_from_unused_bit_count"], 7)
        self.assertTrue(downstream["all_digits_valid"])
        self.assertEqual(downstream["decoded_length"], 68)
        self.assertEqual(
            downstream["compressed_p2pkh"],
            cosmic_raw_digest_checkpoint_audit.EXPECTED_ADDRESSES,
        )
        self.assertEqual(
            downstream["compressed_p2pkh"],
            onchain_op_return_provenance_audit.KNOWN_SCAM_ADDRESSES,
        )
        self.assertEqual(downstream["fixed_base38_full_span_offsets"], (7,))
        uniqueness = report["published_uniqueness_family"]
        self.assertEqual(uniqueness["attempts"], 210)
        self.assertEqual(len(uniqueness["padding_valid_hits"]), 1)
        self.assertEqual(report["calibration"]["valid_padding_forms"], 1)

    def test_first_piece_overlay_dna_rgb_gates(self):
        report = first_piece_overlay_dna_rgb_gate_audit.audit()
        self.assertEqual(report["overlay"]["minimum_target_aperture_orientation_family"], 72)
        self.assertFalse(report["overlay"]["pass"])
        self.assertEqual(report["dna"]["endpoint_packed_bytes"], 3)
        self.assertEqual(report["dna"]["family_size"], 72)
        self.assertEqual(report["dna"]["unique_amino_sequences"], 72)
        self.assertEqual(report["dna"]["proposed_mapping"]["amino"], "GVGWGGCC")
        self.assertFalse(report["dna"]["pass"])
        self.assertEqual(report["rgb"]["difference"], (7, 193, 108))
        self.assertEqual(report["rgb"]["rose_mod26_a0"], "NJQ")
        self.assertEqual(report["rgb"]["rose_mod26_a1"], "MIP")
        self.assertFalse(report["rgb"]["claimed_niq_consistent"])
        self.assertFalse(report["rgb"]["pass"])
        self.assertFalse(report["oracle_run"])

    def test_first_piece_cefe_checkerboard_gate(self):
        report = first_piece_cefe_checkerboard_gate_audit.audit()
        self.assertEqual(report["atomic_arithmetic"]["atomic_numbers"], (58, 26))
        self.assertEqual(report["atomic_arithmetic"]["half_sum_list"], (42, 29, 13))
        self.assertEqual(report["role_matches"]["zero_pad_bytes_to_scalar"], 29)
        self.assertTrue(report["role_matches"]["fe_half_matches_instruction_length"])
        self.assertEqual(report["byte_identity"]["subtraction"], 0x30)
        self.assertEqual(report["byte_identity"]["independent_confirmations"], 1)
        self.assertEqual(report["checkerboard_seed"]["native_deduped_seed"], "BATCHOEFPV")
        self.assertEqual(report["checkerboard_seed"]["unique_boards"], 2430)
        self.assertFalse(report["point16_gate"]["pass"])
        self.assertFalse(report["point18_gate"]["pass"])
        self.assertFalse(report["oracle_run"])

    def test_first_piece_batch_rebus_gate(self):
        report = first_piece_batch_rebus_gate_audit.audit()
        self.assertEqual(report["source"]["shadow_rgb"], (56, 56, 56))
        self.assertEqual(report["source"]["shadow_pixel_count"], 43)
        self.assertEqual(report["source"]["pixel_atomic_symbols"], ("Ba", "Tc"))
        self.assertEqual(report["candidate"]["exact_case"], "BaTcH")
        self.assertEqual(report["candidate"]["casefolded"], "batch")
        self.assertEqual(report["ordering_calibration"]["family_size"], 6)
        self.assertEqual(report["ordering_calibration"]["batch_count"], 1)
        self.assertTrue(report["chemical_context"]["element_vocabulary_established"])
        self.assertFalse(report["strict_gate"]["pass"])
        self.assertFalse(report["oracle_run"])

    def test_first_piece_border_raster_scan(self):
        report = first_piece_border_raster_scan_audit.audit()
        self.assertEqual(report["border"]["top"]["cells"], "WWKKWBWWKWKKWY")
        self.assertEqual(
            report["nearest_inward"]["from_left"],
            {"blue": 12, "yellow": 2, "fefe": 0},
        )
        self.assertEqual((report["fefe"]["row0"], report["fefe"]["col0"]), (7, 4))
        self.assertTrue(report["fefe"]["nearest_from_bottom_in_its_column"])
        self.assertEqual(report["raster"]["left_to_right"]["value"], 16763473)
        self.assertTrue(report["raster"]["left_to_right"]["is_prime"])
        self.assertFalse(report["raster"]["top_to_bottom"]["is_prime"])
        self.assertFalse(any(report["matches_spiral"].values()))
        self.assertEqual(report["prime_directions"], ["left_to_right"])
        self.assertFalse(report["posthoc_valid_p_value"])

    def test_urlblob_is_a_default_provenance_labeled_target(self):
        self.assertEqual(
            tuple(BLOBS), ("SALPH", "COSMIC", "P32TRAILING", "URLBLOB")
        )
        self.assertEqual(QUARANTINED_BLOBS["URLBLOB"], BLOBS["URLBLOB"])

    def test_urlblob_keywrap_backfill_scope(self):
        # The full sweep (~17k KEK-deriving attempts) is too slow for this
        # regression suite; this checks the module's scope/plumbing instead
        # of re-running Phase 193's already-recorded negative result.
        module = urlblob_keywrap_backfill
        self.assertEqual(tuple(module.TARGET_BLOBS), ("URLBLOB",))
        candidates = module.load_curated_candidates()
        self.assertGreaterEqual(len(candidates), 568)
        self.assertEqual(
            module.candidate_list_digest(candidates), "2d233645ef49a141"
        )

    def test_phase32_column_calibration(self):
        report = phase32_column_calibration_audit.audit()
        cosmic, phase32 = report["cosmic"], report["phase32"]
        self.assertEqual(phase32["row_count"], 51)
        self.assertEqual(phase32["bytes_per_column"], 38)
        self.assertEqual(phase32["md5_columns"], ())
        self.assertEqual(len(phase32["fe_columns"]), 8)
        self.assertFalse(phase32["last_column_has_fe"])
        self.assertEqual(cosmic["row_count"], 28)
        self.assertTrue(cosmic["last_column_hex"].startswith("7a20fe"))
        self.assertTrue(cosmic["last_column_has_fe"])
        # Both blobs' observed FE-column counts are within one column of
        # their uniform-random-byte expectation -- neither is anomalous.
        for entry in (cosmic, phase32):
            self.assertLess(
                abs(len(entry["fe_columns"]) - entry["expected_fe_columns"]), 1.0
            )

    def test_stage0_even_sequence_convergence(self):
        report = stage0_even_sequence_convergence_audit.audit()
        self.assertTrue(report["overlap"])
        self.assertEqual(report["joined"], (8, 6, 4, 2, 0))
        self.assertEqual(report["steps"], (-2, -2, -2, -2))
        self.assertEqual(report["candidate"], "86420")
        self.assertEqual(report["oracle"]["hits"], [])
        self.assertEqual(report["quarantined_oracle"]["hits"], [])
        self.assertEqual(
            report["fefe_value_shared_with"], ("fefefe", "white", "yellow")
        )
        self.assertEqual(report["quarantined_oracle"]["hits"], [])

    def test_stage0_g_shadow_consumer(self):
        report = stage0_g_shadow_consumer_audit.audit()
        self.assertEqual(report["payload"], "OCBe")
        self.assertEqual(report["residue_count"], 13)
        self.assertEqual(report["atomic_numbers"], (8, 6, 4))
        self.assertEqual(report["constant_step"], (-2, -2))
        sensitive = {
            row["marker"]: row for row in report["case_sensitive_marker_null"]
        }
        self.assertEqual(sensitive["G"]["element_parses"], (("O", "C", "Be"),))
        self.assertFalse(
            next(row for row in report["casefold_marker_null"] if row["marker"] == "g")[
                "valid"
            ]
        )
        self.assertEqual(report["oracle"]["hits"], [])

    def test_stage0_repeated_grayscale(self):
        report = stage0_repeated_grayscale_audit.audit()
        self.assertEqual(report["collapsed_claim"], ("CE", "FE"))
        self.assertEqual(report["ce"]["pixel_count"], 9)
        self.assertEqual(report["fe"]["pixel_count"], 5625)
        self.assertEqual(len(report["logo_bytes"]), 34)
        self.assertEqual(len(report["logo_single_3x3_bytes"]), 10)

    def test_stage0_footer_palette_layer(self):
        report = stage0_footer_palette_layer_audit.audit()
        self.assertEqual(report["target"]["selected_counts"], (11, 11))
        self.assertEqual(report["target"]["pixel_count"], 43)
        self.assertEqual(report["balanced_11_colors"], ((56, 56, 56),))
        self.assertEqual(report["sparse_count"], 41)
        self.assertEqual(report["oracle"]["candidate_count"], 8)
        self.assertEqual(report["oracle"]["hits"], [])
        self.assertEqual(
            report["intermediate_grayscale_all_g"],
            (((56, 56, 56), (4, 4, 4, 2, 2)),),
        )
        self.assertEqual(report["target_non_g_selected_count"], 17)

    def test_first_piece_hamming_control_language(self):
        report = first_piece_hamming_control_audit.audit()
        masks = report["color_masks"]
        gray = report["gray_controls"]
        self.assertEqual(masks["prime_matrix"], ((0, 1, 2), (1, 2, 3)))
        self.assertEqual(masks["rose_matrix"], ((4, 3, 2), (3, 2, 1)))
        self.assertEqual(masks["prime_matrix_sums"]["columns"], (1, 3, 5))
        self.assertEqual(masks["rose_matrix_sums"]["columns"], (7, 5, 3))
        self.assertEqual(gray["shadow_popcount"], 9)
        self.assertEqual(gray["shadow_complement_popcount"], 15)
        self.assertEqual(gray["fefe_popcount"], 21)
        self.assertEqual(gray["fefe_zero_count"], 3)
        self.assertEqual(gray["fefe_and_prime_value"], 574060)
        self.assertEqual(report["structural_21"]["flat_1_4_21"], "ggn")
        self.assertEqual(report["structural_21"]["residual_byte_count"], 21)

    def test_first_piece_complete_bitplanes(self):
        report = first_piece_bitplane_audit.audit()
        self.assertTrue(report["lsb_matches_image_blue_one"])
        self.assertEqual(report["source_bit_count"], 192)
        self.assertEqual(report["residual_dimensions"], (7, 24))
        self.assertEqual(report["residual_byte_count"], 21)
        self.assertEqual(report["plane_reconstruction"], report["source"])
        self.assertEqual(report["character_major_reconstruction"], report["source"])
        self.assertEqual(report["prime_members"], ((0, "complement", 574061),))
        self.assertEqual(
            tuple((bit, polarity) for bit, polarity, _ in report["staircase_members"]),
            ((0, "direct"), (0, "complement")),
        )

    def test_first_piece_ggn_distinctiveness(self):
        report = first_piece_ggn_distinctiveness_audit.audit()
        flat = report["flat_extractions"]
        family = report["text_triple_family"]
        self.assertTrue(report["tuple_provenance"]["hierarchical_match"])
        self.assertEqual(flat["one_based_text"], "ggn")
        self.assertEqual(flat["zero_based_text"], "s.t")
        self.assertEqual(flat["one_based_colors"], "BBY")
        self.assertEqual(family["family_size"], 2024)
        self.assertEqual(family["uniquely_emitted_rows"], 519)
        self.assertEqual(family["first_pair_equal_then_distinct"], 85)
        self.assertEqual(family["first_pair_equal_unique_third"], 36)
        self.assertEqual(report["exact_ggn"]["indices_1"], ((1, 4, 21),))
        self.assertFalse(report["exact_ggn"]["posthoc_valid_p_value"])
        self.assertFalse(report["curve_identity_scope"]["secp256k1_specific"])

    def test_first_piece_matrix_product(self):
        report = first_piece_matrix_product_audit.audit()
        fixed = report["fixed_operation"]
        permutations_report = report["fixed_matrix_vector_permutations"]
        geometry = report["geometric_family"]
        expanded = report["expanded_digit_assignment_control"]
        self.assertEqual(report["source"]["matrix"], ((5, 7, 4), (0, 6, 1)))
        self.assertEqual(report["source"]["sum_list"], (23, 16, 7))
        self.assertEqual(fixed["output"], (255, 103))
        self.assertEqual(fixed["serialized_hex_if_bytes"], "FF67")
        self.assertEqual(permutations_report["property_counts"]["exact_255_103"], 1)
        self.assertEqual(geometry["distinct_unordered_output_count"], 6)
        self.assertEqual(expanded["operation_class_count"], 720)
        self.assertEqual(expanded["exact_ordered_rate"].numerator, 1)
        self.assertEqual(expanded["exact_ordered_rate"].denominator, 720)
        self.assertFalse(expanded["primary_null"])
        self.assertFalse(report["oracle_run"])

    def test_first_piece_second_matrixsumlist(self):
        report = first_piece_second_matrixsumlist_audit.audit()
        source = report["source"]
        delta = report["difference"]
        family = report["row_alignment_traversal_family"]
        self.assertEqual(source["shadow_matrixsumlist"], (43, 25, 18))
        self.assertEqual(source["prime_matrixsumlist"], (23, 16, 7))
        self.assertEqual(delta["direct"], (20, 9, 11))
        self.assertEqual(delta["direct_a1z26"], "TIK")
        self.assertEqual(delta["reverse_a1z26"], "KIT")
        self.assertTrue(delta["additive_checksum_forced"])
        self.assertEqual(
            report["event_cross_checks"],
            {
                "events_before_fefe": 20,
                "yellow_endpoint_count": 9,
                "shadow_row_widths": (11, 11),
            },
        )
        self.assertTrue(report["cross_check_match"])
        self.assertEqual(family["kit_count"], 1)
        self.assertEqual(family["family_size"], 8)
        self.assertFalse(family["posthoc_valid_p_value"])
        self.assertFalse(report["oracle_run"])

    def test_first_piece_event_rail_preservation(self):
        report = first_piece_event_rail_preservation_audit.audit()
        endpoint = report["endpoint_mask"]
        fitted = report["fitted_event_inventory"]
        blue = report["blue_to_grid_rows"]
        buckets = report["all_event_row_buckets"]
        mux = report["literal_24_endpoint_mux"]
        self.assertEqual((endpoint["blue_count"], endpoint["yellow_count"]), (15, 9))
        self.assertEqual(fitted["profile_BYF"], (14, 8, 1))
        self.assertEqual(fitted["flattened_symbol_length"], 31)
        self.assertEqual(fitted["distinct_url_objects"], 22)
        self.assertFalse(blue["one_per_row"])
        self.assertEqual(blue["actual_distinct_rows"], 12)
        self.assertEqual(blue["missing_rows"], (6, 11))
        self.assertEqual(blue["duplicated_rows"], (2, 14))
        self.assertTrue(buckets["all_rows_nonempty"])
        self.assertEqual(buckets["first_full_coverage_event"], 20)
        self.assertEqual(
            mux["blue_to_dbbi_yellow_to_faed"]["output"],
            "dbbifbfbaehccbdegggbeeid",
        )
        self.assertEqual(
            mux["blue_to_faed_yellow_to_dbbi"]["output"],
            "faeddggebbedfcibdbfabhbc",
        )
        self.assertFalse(
            report["architecture_constraints"][
                "dual_stream_mux_preserves_distinct_fefe_class"
            ]
        )
        self.assertFalse(report["oracle_run"])

    def test_first_piece_png_palette_provenance(self):
        report = first_piece_png_palette_provenance_audit.audit()
        full, rabbit = report["full"], report["rabbit"]
        verdict = report["format_verdict"]
        self.assertTrue(report["root_copy_byte_identical"])
        self.assertEqual(full["ihdr"]["color_type"], 6)
        self.assertEqual(rabbit["ihdr"]["color_type"], 6)
        self.assertFalse(full["plte_present"])
        self.assertFalse(rabbit["plte_present"])
        self.assertFalse(full["trns_present"])
        self.assertFalse(rabbit["trns_present"])
        self.assertEqual(full["pixels"]["fe_bbox_inclusive"], (300, 525, 374, 599))
        self.assertEqual(rabbit["pixels"]["fe_bbox_inclusive"], (100, 175, 124, 199))
        self.assertTrue(full["pixels"]["all_pixels_opaque"])
        self.assertTrue(rabbit["pixels"]["all_pixels_opaque"])
        self.assertFalse(verdict["palette_index_exists"])
        self.assertFalse(verdict["fe_has_distinct_alpha"])
        self.assertEqual(verdict["decoded_fe_sample_hex"], "FEFEFEFF")
        self.assertTrue(report["marker_scaling"]["full_bbox_equals_scaled_rabbit_bbox"])

    def test_first_piece_shadow_column_rails(self):
        report = first_piece_shadow_column_rail_audit.audit()
        larger = report["larger_count_selection"]
        smaller = report["smaller_count_selection"]
        numeric = report["numeric_operations"]
        calibration = report["alignment_calibration"]
        geometry = report["spatial_alignment"]
        self.assertEqual(larger["strict_unequal_text"], "GGO5gUBG")
        self.assertEqual(larger["tie_template"], "G=GO5g==UBG")
        self.assertEqual(smaller["strict_unequal_text"], "GGC9BPCe")
        self.assertEqual(numeric["column_sum_digits"], "62663422336")
        self.assertEqual(numeric["absolute_difference_digits"], "20221200112")
        self.assertEqual(numeric["equality_mask_bits"], "01000011000")
        self.assertEqual(
            (numeric["upper_win_count"], numeric["lower_win_count"], numeric["tie_count"]),
            (6, 2, 3),
        )
        self.assertEqual(calibration["family_size"], 2772)
        self.assertEqual(calibration["absolute_total_rate"].numerator, 25)
        self.assertEqual(calibration["absolute_total_rate"].denominator, 77)
        self.assertFalse(calibration["posthoc_valid_p_value"])
        self.assertEqual(geometry["ordinal_pair_x_overlap_count"], 0)
        self.assertFalse(geometry["constant_x_offset"])
        self.assertFalse(geometry["physical_vertical_columns"])
        self.assertFalse(report["verdict"]["column_alignment_yields_selected_consumer"])
        self.assertFalse(report["oracle_run"])

    def test_first_piece_even_odd_alphabet_gate(self):
        report = first_piece_even_odd_alphabet_gate_audit.audit()
        provenance = report["provenance"]
        gate = report["strict_gate"]
        complement = report["conditional_nines_complement"]
        mapping = report["conditional_a_i_mapping"]
        self.assertEqual(report["even_sequence"]["digits"], (8, 6, 4, 2, 0))
        self.assertEqual(report["even_sequence"]["steps"], (-2, -2, -2, -2))
        self.assertEqual(provenance["fefe_value_shared_with"], ("fefefe", "white", "yellow"))
        self.assertEqual(provenance["architect_he_route"]["a_i_filtered_end_rail"], "he")
        self.assertEqual(provenance["architect_he_route"]["atomic_number"], 2)
        self.assertFalse(gate["same_operation_or_value_type"])
        self.assertFalse(gate["terminal_zero_unique_to_fefe"])
        self.assertFalse(gate["independent_five_digit_recovery"])
        self.assertFalse(gate["pass"])
        self.assertEqual(complement["string"], "13579")
        self.assertEqual(mapping["zero_based_join_after_dropping_invalid"], "igecabdfh")
        self.assertEqual(mapping["one_based_join_after_dropping_invalid"], "hfdbacegi")
        self.assertEqual(mapping["orientation_family_size"], 8)
        self.assertFalse(mapping["invalid_terminal_as_delimiter_selected"])
        self.assertFalse(report["prior_direct_86420_oracle"]["rerun"])
        self.assertFalse(report["oracle_run"])

    def test_first_piece_prime_sum_reconstruction(self):
        report = first_piece_prime_sum_reconstruction.audit()
        self.assertEqual(report["fitted_event_count"], 23)
        self.assertTrue(report["all_fitted_match"])
        self.assertEqual(report["fitted_sums"], {"B": 401, "Y": 400, "F": 73})
        self.assertEqual(report["all_sums"], {"B": 490, "Y": 497, "F": 73})
        self.assertEqual(report["near_balance_prefixes"], (23,))
        self.assertEqual(report["fefe_record"]["ordinal"], 21)
        self.assertEqual(report["fefe_record"]["prime"], 73)
        self.assertEqual(report["first_outside"]["position_1"], 97)
        self.assertEqual(report["same_prefix_consumer_lengths"], tuple(range(91, 97)))

    def test_prime_sum_fefe_mask_composition(self):
        report = prime_sum_fefe_mask_composition_audit.audit()
        self.assertEqual(report["input_values_BYF"], (401, 400, 73))
        self.assertEqual(report["repeated_fe_outputs_BYF"], (144, 144, 72))
        self.assertTrue(report["equal_halves"])
        self.assertTrue(report["fefe_is_half"])
        self.assertEqual(report["scalar_lsb_only_control_BYF"], (400, 400, 72))
        fixed = report["fixed_fefe_calibration"]
        self.assertEqual(fixed["successes"], fixed["near_balances"])
        self.assertEqual(fixed["rate"].numerator, 271)
        self.assertEqual(fixed["rate"].denominator, 106_590)
        floating = report["floating_fefe_calibration"]
        self.assertEqual(floating["successes"], 813)
        self.assertEqual(
            tuple(row["fefe_prime"] for row in floating["successful_fefe_rows"]),
            (73,),
        )

    def test_neo_choice_last_words(self):
        module = neo_choice_last_words_audit
        self.assertEqual(len(module.CANDIDATES), 7)
        self.assertEqual(
            module.letters_only("Run, Neo. Run."),
            "runneorun",
        )
        self.assertEqual(set(module.SCENE_ANCHORS), set(module.PDFS))
        self.assertEqual(
            module.EXPECTED_CHOICE_LEXEMES,
            {"MATRIX_1999": 13, "RELOADED_2003": 19, "REVOLUTIONS_2003": 19},
        )
        self.assertEqual(sum(module.EXPECTED_CHOICE_LEXEMES.values()), 51)

    def test_neo_smith_equation_scene(self):
        module = neo_smith_equation_audit
        self.assertEqual(len(module.CANDIDATES), 4)
        self.assertEqual(
            module.letters_only("Nothing this weak is meant to survive."),
            "nothingthisweakismeanttosurvive",
        )
        report = module.audit()
        self.assertEqual(report["source"]["what_do_you_want_occurrences"], 3)
        self.assertEqual(report["oracle"]["candidate_count"], 4)
        self.assertEqual(report["oracle"]["hits"], [])

    def test_matrixsum_dbbi_faed_position_selector(self):
        module = matrixsum_dbbi_faed_position_audit
        self.assertEqual(module.INDICES, (23, 16, 7))
        report = module.audit()
        self.assertEqual(report["oracle"]["candidate_count"], 8)
        self.assertEqual(report["oracle"]["hits"], [])

    def test_matrixsum_cumulative_stride(self):
        module = matrixsum_cumulative_stride_audit
        self.assertEqual(module.CYCLE, (23, 16, 7))
        report = module.audit()
        self.assertEqual(report["results"]["DBBI"]["string"], "hebgb")
        self.assertEqual(len(report["results"]["FAED"]["positions"]), 36)
        self.assertEqual(report["oracle"]["hits"], [])

    def test_remaining_structural_avenues(self):
        module = remaining_structural_avenues_audit
        self.assertEqual(module.keyword_to_seed("AI", 9), [1, 0])
        self.assertEqual(
            module.rotation_scope()["distinct_mod9_rotations"],
            (5, 7),
        )
        self.assertEqual(
            module.repeat_transform("abc", (1,), "cipher_minus_key"),
            "iab",
        )

    def test_synthesis_action_paths(self):
        module = synthesis_action_paths_audit
        self.assertEqual(module.base9_integer("bi"), 17)
        self.assertEqual(module.pad25(module.TARGET), "NCSYAGHIROLEFTVBDKMPQUWXZ")
        provenance = module.source_provenance()
        self.assertTrue(provenance["architect_final_present"])
        self.assertFalse(provenance["proposed_neo_reply_present"])
        scalar_sum = module.path_d()["reports"][2]
        self.assertTrue(scalar_sum["valid"])
        self.assertEqual(scalar_sum["known_address_hits"], ())

    def test_triangular_matrixsumlist_geometry(self):
        module = triangular_matrixsumlist_audit
        self.assertEqual(len(module.DBBI), module.triangular(13))
        self.assertEqual(len(module.BITS) + 1, module.triangular(14))
        self.assertEqual(len(module.DBBI) + len(module.BITS) + 1, 14 ** 2)
        self.assertEqual(len(module.MERGE_STARTS), 8)
        rows = module.candidate_rows(module.BITS, module.load_quadgrams())
        self.assertEqual(len(rows), 210)
        self.assertTrue(all(len(row["diagonal_bits"]) == 14 for row in rows))

    def test_ic_ranking_uses_distance_from_english(self):
        reference = checkerboard_code_ic_oracle.ENGLISH_PROSE_IC
        ic_map = {
            ("a", "b"): reference + 0.020,
            ("a", "c"): reference + 0.004,
            ("a", "d"): reference - 0.006,
        }
        rank, value, ranked, tied = checkerboard_code_ic_oracle.rank_of_pair(
            ic_map,
            ("a", "c"),
        )
        self.assertEqual(rank, 1)
        self.assertEqual(tied, 1)
        self.assertEqual(value, reference + 0.004)
        self.assertNotEqual(ranked[0][0], ("a", "b"))

    def test_real_ic_top_pairs(self):
        dbbi = checkerboard_code_ic_oracle.apply_to_real_data("dbbi")
        faed = checkerboard_code_ic_oracle.apply_to_real_data("faed")
        self.assertEqual(frozenset(dbbi["ranked"][0][0]), frozenset("be"))
        self.assertEqual(frozenset(faed["ranked"][0][0]), frozenset("gi"))

    def test_promised_candidate_family_is_deduplicated(self):
        report = promised_standalone_audit.audit()
        self.assertEqual(
            report["candidates"],
            ("promised", "PROMISED", "Promised"),
        )

    def test_yellow_blue_guide_matrix_directions(self):
        report = telegram_yellow_blue_matrix_direction_audit.historical_family()
        self.assertEqual(
            report["outputs"],
            telegram_yellow_blue_matrix_direction_audit.EXPECTED_OUTPUTS,
        )
        self.assertEqual(
            report["diagonals"],
            telegram_yellow_blue_matrix_direction_audit.EXPECTED_DIAGONALS,
        )
        self.assertEqual(report["best_label"], "rows_forward")
        self.assertEqual(
            telegram_yellow_blue_matrix_direction_audit.caesar_shift(
                "IZLKESEEDQPPEN",
                4,
            ),
            "MDPOIWIIHUTTIR",
        )

    def test_safenet_luna_scope_and_boundaries(self):
        candidates = safenet_luna_hsm_audit.load_candidates()
        report = safenet_luna_hsm_audit.structural_audit()
        self.assertEqual(len(candidates), 62)
        self.assertEqual(candidates[:3], ("SafeNet", "Luna", "HSM"))
        self.assertEqual(
            report["historical_context"]["days_before_launch"],
            18,
        )
        self.assertEqual(report["first_piece"]["puzzle_only"], ("yellow",))
        self.assertEqual(report["stage1_icons"]["puzzle_only"], ())
        if report["creator_mentions"] is not None:
            self.assertEqual(report["creator_mentions"], ())

    def test_spi_cd_missing_e_relation_is_exact(self):
        report = spi_cd_initials_audit.audit()
        joined = report["spi"] + report["cd"]
        self.assertEqual(joined, "SPICD")
        self.assertEqual(
            spi_cd_initials_audit.PHONETIC_READING.replace("E", "", 1),
            joined,
        )

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists(),
        "sibling GSMG page mirror is unavailable",
    )
    def test_salvation_role_statuses(self):
        report = salphaseion_salvation_role_audit.audit()
        self.assertEqual(
            sorted(report["closed_negative_roles"]),
            ["replacement_state", "sha_operand"],
        )
        self.assertEqual(report["bounded_negative_roles"], ["rail_selector"])
        self.assertEqual(report["open_untestable_roles"], ["checksum"])

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists()
        and Path(dual_channel_consistency_audit.DEFAULT_IMAGE).exists(),
        "page mirror or first-piece image is unavailable",
    )
    def test_dual_channel_scope(self):
        report = dual_channel_consistency_audit.audit()
        self.assertEqual(len(report["pairs"]), 7)
        self.assertEqual(len(report["established_edges"]), 4)
        self.assertEqual(
            set(report["pairs"]),
            {
                "yellow_blue",
                "matrix_rows",
                "total_split",
                "but_hye_rail",
                "salph_halves",
                "half_better_half",
                "textareas",
            },
        )

    @unittest.skipUnless(
        (Path(DEFAULT_EXPORT_DIR) / "result.json").exists(),
        "Telegram export is unavailable",
    )
    def test_full_binary_export_inventory(self):
        report = binary_message_export_audit.audit()
        self.assertEqual(report["hit_count"], 25)
        self.assertEqual(report["unique_payload_count"], 16)
        self.assertEqual(report["creator_ids"], (8446, 53342))
        self.assertEqual(
            tuple(row["id"] for row in report["inventory"]),
            binary_message_export_audit.EXPECTED_MESSAGE_IDS,
        )

    @unittest.skipUnless(
        (Path(DEFAULT_EXPORT_DIR) / "result.json").exists()
        and (
            matrixsumlist_provenance_refresh_audit.LATEST_EXPORT_DIR
            / "result.json"
        ).exists(),
        "full or incremental Telegram export is unavailable",
    )
    def test_matrixsumlist_provenance_refresh(self):
        report = matrixsumlist_provenance_refresh_audit.self_test()
        self.assertEqual(
            report["latest_export"]["relevant_ids"],
            matrixsumlist_provenance_refresh_audit.EXPECTED_LATEST_RELEVANT_IDS,
        )
        self.assertEqual(report["creator"]["literal_matrixsumlist_message_ids"], ())
        self.assertEqual(report["gates"]["G3_operation"][:4], "FAIL")

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists()
        and (Path(DEFAULT_EXPORT_DIR) / "result.json").exists(),
        "page mirror or Telegram export is unavailable",
    )
    def test_matrixsumlist_page_scope(self):
        report = matrixsumlist_page_scope_audit.self_test()
        self.assertEqual(
            tuple(report["surviving_roles"]),
            ("postfix_to_dbbi", "prefix_to_faed", "infix_dbbi_faed"),
        )
        self.assertFalse(report["matrix_neighbors"]["validated_join"])
        self.assertEqual(report["strictly_supported_binding_models"], ())

    @unittest.skipUnless(
        (Path(DEFAULT_EXPORT_DIR) / "result.json").exists(),
        "Telegram export is unavailable",
    )
    def test_matrixsumlist_historical_code(self):
        report = matrixsumlist_historical_code_audit.self_test()
        self.assertEqual(report["cutoff"]["message_id"], 60333)
        self.assertEqual(
            report["prime_sum_tool"]["row_letters"], "ANTLGHQESHKTPG"
        )
        self.assertFalse(report["prime_sum_tool"]["sum_depends_on_grid_bits"])
        self.assertEqual(report["attachment_scan"]["selected31_hits"], ())
        self.assertFalse(report["gate_result"]["historical_code_fixes_transition"])

    @unittest.skipUnless(
        (Path(DEFAULT_EXPORT_DIR) / "result.json").exists()
        and (
            creator_operator_vocabulary_audit.SUPPORT_EXPORT_DIR / "result.json"
        ).exists()
        and Path(DEFAULT_HTML).exists(),
        "solver/support exports or page mirror are unavailable",
    )
    def test_creator_operator_vocabulary(self):
        report = creator_operator_vocabulary_audit.self_test()
        self.assertEqual(report["solved_operator_count"], 16)
        self.assertEqual(report["g3_fixed_field_count"], 0)
        self.assertEqual(report["g3_total_field_count"], 7)
        excluded = {item["term"] for item in report["excluded_terms"]}
        self.assertIn("XOR", excluded)
        self.assertIn("beginnings/endings", excluded)
        self.assertFalse(report["g3_pass"])

    def test_architect_choice_boundary(self):
        report = architect_choice_boundary_audit.audit()
        film = report["sources"]["film"]["moment_to_choice"]
        screenplay = report["sources"]["screenplay"]["moment_to_choice"]
        self.assertEqual(film["word_count"], 69)
        self.assertEqual(screenplay["word_count"], 72)
        self.assertEqual(
            report["boundary_checks"]["forward_one_tokens"],
            ("both", "ultimately", "the"),
        )
        self.assertEqual(report["boundary_checks"]["forward_one_edges"], ("but", "hye"))
        self.assertTrue(report["boundary_checks"]["initials_equal_next_word"])
        self.assertTrue(
            report["cross_source"]["moment_to_choice"]["shared_indexed_outputs"][
                "forward_one"
            ]
        )
        self.assertFalse(report["cross_source"]["moment_to_choice"]["identical_full_scope"])

    def test_architect_choice_literal_password_negative(self):
        candidates = architect_choice_literal_password_audit.candidates()
        self.assertEqual(
            candidates,
            (
                "as you adequately put the problem is",
                "asyouadequatelyputtheproblemis",
            ),
        )
        result = architect_choice_literal_password_audit.oracle_check(
            candidates, dict(BLOBS, **QUARANTINED_BLOBS)
        )
        self.assertEqual(result["tested_keystrings"], 36)
        self.assertEqual(sum(len(v) for v in result["hits"].values()), 0)

    @unittest.skipUnless(
        (Path(DEFAULT_EXPORT_DIR) / "result.json").exists(),
        "Telegram export is unavailable",
    )
    def test_minimal_macro_chain_excludes_circular_and_posthoc_steps(self):
        report = minimal_macro_chain_audit.audit(Path(DEFAULT_EXPORT_DIR) / "result.json")
        self.assertEqual(report["prime"], 574061)
        self.assertEqual(report["sum_list"], (23, 16, 7))
        self.assertEqual(report["edge_rails"], ("but", "hye"))
        self.assertEqual(
            report["mirror_state"],
            {
                "beginning_a_i": "b",
                "ending_a_i": "he",
                "b_mirrors_h": True,
                "e_is_fixed": True,
            },
        )
        self.assertTrue(report["scope_comparison"]["minimal_prime_operand"]["reaches_but_hye_checkpoint"])
        self.assertFalse(report["scope_comparison"]["minimal_prime_operand"]["reaches_macro_yinyang"])
        self.assertFalse(report["scope_comparison"]["selected_31_operand"]["reaches_macro_yinyang"])
        # The circular H|YE|BUT construction and the post-hoc VAT/SALVATION
        # rebus were removed after review -- assert they stay out rather than
        # silently reappearing in a future edit.
        self.assertNotIn("post_yinyang_checks", report)
        self.assertIn("deliberately excluded", report["verdict"])
        self.assertIn("post-hoc", report["verdict"])

    @unittest.skipUnless(
        (Path(DEFAULT_EXPORT_DIR) / "result.json").exists()
        and Path(DEFAULT_HTML).exists(),
        "Telegram export or page mirror is unavailable",
    )
    def test_post_yinyang_dataflow_keeps_only_live_roles(self):
        report = post_yinyang_dataflow_audit.audit(
            Path(DEFAULT_EXPORT_DIR) / "result.json"
        )
        self.assertEqual(
            report["premise_status"],
            "conditional_unverified_after_phase223",
        )
        self.assertEqual(
            report["most_local_live_role"],
            "faed_plaintext_is_password",
        )
        self.assertEqual(
            report["routes"]["first_hint_or_last_command_is_password"][
                "unique_material_count"
            ],
            162,
        )
        self.assertEqual(
            report["routes"]["dbbi_faed_joint_result_is_password"]["status"],
            "live_but_operator_unknown",
        )
        self.assertEqual(
            set(report["excluded_anchors"]),
            {"h_ye_but", "vat_salvation"},
        )

    def test_faed_coverage_requires_a_binding_not_more_bruteforce(self):
        report = faed_decoder_coverage_audit.audit()
        checkpoint = report["faed_checkpoint"]
        self.assertEqual(checkpoint["raw_length"], 570)
        self.assertEqual(checkpoint["best_escape_pair"], ("g", "i"))
        self.assertEqual(checkpoint["segmented_code_count"], 436)
        self.assertEqual(checkpoint["distinct_code_count"], 25)
        self.assertEqual(len(report["known_incomplete_compute"]), 1)
        self.assertEqual(report["admitted_clue_supported_open_models"], ())
        self.assertIn("binding/provenance", report["verdict"])

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists(),
        "sibling GSMG page mirror is unavailable",
    )
    def test_salphaseion_presentation_has_no_segment_binding(self):
        report = salphaseion_presentation_binding_audit.audit()
        self.assertEqual(report["headings"], ("SalPhaseIon", "Cosmic Duality"))
        self.assertEqual(report["salphaseion"]["authored_line_breaks"], 0)
        self.assertEqual(
            len(report["salphaseion"]["segment_boundaries"]),
            12,
        )
        self.assertEqual(
            report["cosmic_duality_control"]["line_lengths"],
            (64,) * 28,
        )
        self.assertEqual(report["binding_candidates_found"], ())

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists()
        and salphaseion_responsive_wrap_audit.DEFAULT_SCREENSHOT.exists(),
        "page mirror or historical SalPhaseIon screenshot is unavailable",
    )
    def test_responsive_wrap_has_no_deterministic_second_layer(self):
        report = salphaseion_responsive_wrap_audit.audit()
        self.assertEqual(
            report["historical_screenshot"]["recovered_logical_symbols_per_row"],
            45,
        )
        self.assertEqual(report["screenshot_grid"]["row_count"], 24)
        self.assertEqual(report["screenshot_grid"]["last_row_length"], 40)
        self.assertEqual(report["screenshot_grid"]["aligned_segment_ends"], ("faed",))
        self.assertEqual(
            report["boundary_controls"]["faed_end_aligned_widths"],
            (45, 51, 85),
        )
        self.assertEqual(report["responsive_vocabulary"]["real_score"], (0, 0, 0))
        self.assertEqual(report["responsive_vocabulary"]["screenshot_width_hits"], ())
        self.assertEqual(
            report["responsive_vocabulary"]["calibration"]["empirical_p"],
            1.0,
        )
        self.assertFalse(report["promotion"]["promoted"])

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists()
        and Path(DEFAULT_EXPORT_DIR, "result.json").exists()
        and yinyang_cosmic_phase_label_audit.BOOK_PATH.exists(),
        "page mirror, complete export, or book transcript is unavailable",
    )
    def test_yinyang_does_not_redirect_salphaseion_to_cosmic(self):
        report = yinyang_cosmic_phase_label_audit.audit()
        gates = report["gates"]
        self.assertFalse(gates["1_structural_binding"]["pass"])
        self.assertTrue(gates["2_book_semantics"]["pass"])
        self.assertFalse(gates["3_creator_usage_precedent"]["pass"])
        self.assertEqual(
            gates["4_dom_adjacency"]["weight"],
            "necessary_but_trivial",
        )
        self.assertTrue(gates["5_contamination_guard"]["pass"])
        self.assertEqual(
            report["creator_usage"]["next_page_or_section_rows"],
            (),
        )
        self.assertFalse(report["promotion"]["promoted"])

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists()
        and Path(DEFAULT_EXPORT_DIR, "result.json").exists()
        and macro_tail_title_insertion_audit.DEFAULT_DICTIONARY.exists(),
        "page mirror, complete export, or frozen dictionary is unavailable",
    )
    def test_visible_referent_delta_has_no_qualifier(self):
        report = visible_referent_delta_audit.audit()
        self.assertEqual(report["baseline"]["artifact_count"], 7)
        self.assertEqual(report["baseline"]["qualifying_artifacts"], ())
        self.assertEqual(len(report["candidates"]), 7)
        self.assertEqual(report["qualifying_candidates"], ())
        self.assertFalse(report["new_compute_authorized"])
        by_id = {
            row["candidate_id"]: row
            for row in report["candidates"]
        }
        self.assertTrue(by_id["salph_enter_halves"]["gates"]["genuine_dual"])
        self.assertFalse(
            by_id["salph_enter_halves"]["gates"]["correct_transition_position"]
        )
        self.assertTrue(
            by_id["creator_ying_ig_ag"]["gates"][
                "fixed_consumer_or_independent_discriminator"
            ]
        )
        self.assertFalse(
            by_id["creator_ying_ig_ag"]["gates"]["deterministic_recovery"]
        )
        self.assertEqual(
            by_id["p32_equal_length_halves"]["evidence"]["mechanical_half_lengths"],
            (64, 64),
        )
        self.assertFalse(
            by_id["p32_equal_length_halves"]["evidence"][
                "authored_midpoint_separator"
            ]
        )
        self.assertEqual(
            by_id["cosmic_64_column_layout"]["evidence"]["line_lengths"],
            (64,) * 28,
        )

    def test_phase217_circular_rebus_correction_is_propagated(self):
        report = post_phase217_consistency_audit.audit()
        self.assertEqual(report["forbidden_rebus_forms_present"], ())
        self.assertEqual(len(report["corrected_legacy_documents"]), 6)
        self.assertIn("no post-yinyang operator", report["verdict"])

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists()
        and macro_tail_title_insertion_audit.DEFAULT_DICTIONARY.exists(),
        "page mirror or frozen system dictionary is unavailable",
    )
    def test_macro_tail_does_not_uniquely_give_t_to_title(self):
        report = macro_tail_title_insertion_audit.audit()
        self.assertEqual(report["macro_authored_case"], "lowercase")
        self.assertEqual(report["family_size"], 48)
        self.assertEqual(report["valid_reading_count"], 6)
        self.assertEqual(len(report["original_camel_boundary_readings"]), 2)
        self.assertEqual(len(report["salt_readings"]), 1)
        self.assertEqual(len(report["authenticated_envelope_tags"]), 3)
        self.assertEqual(report["quarantined_envelope_tags"], ("URLBLOB",))
        self.assertEqual(
            report["selection_status"],
            "recognizable_after_enumeration_but_not_source_unique",
        )

    def test_architect_mirror_does_not_independently_reach_yinyang(self):
        report = architect_yinyang_distinctiveness_audit.audit()
        self.assertFalse(report["fixed_selection"]["strict_positional_mirror"])
        self.assertEqual(report["control_counts"]["but_initial_rows"], 48)
        self.assertEqual(report["control_counts"]["but_and_partial_rule_rows"], 10)
        self.assertEqual(report["permutation_invariance"]["mirror_closed_passes"], 6)
        self.assertIn("not yet mechanically reached", report["verdict"])

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists(),
        "sibling GSMG page mirror is unavailable",
    )
    def test_wayback_latest_matches_local_mirror(self):
        report = salphaseion_wayback_history_audit.audit_local_mirror()
        self.assertEqual(
            report["sha256"],
            salphaseion_wayback_history_audit.CAPTURES[-1]["sha256"],
        )


if __name__ == "__main__":
    unittest.main()
