#!/usr/bin/env python3
"""Permanent regressions for corrected late-stage GSMG audit claims."""

import hashlib
import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from data import FAED

import aes_key_wrap_sweep
import anstoo_provenance_audit
import architect_choice_boundary_audit
import bip32_authenticated_number_paths_audit
import command_provenance_recheck
import embedded_key_format_scanner_audit
import external_archive_lead_audit
import fefe_zero_operation_audit
import genesis_adjacent_fields_audit
import image_stego_metadata_audit
import lastcommand_probe
import salph_cosmic_phase341_eligibility_audit
import legacy_cbc_backfill
import stream_mode_cipher_sweep
import salphaseion_operand_binding_audit
import small_number_coincidence_calibration
import telegram_export_keyword_sweep
import youwon_full_oracle_backfill
import youwon_partition_audit
import typed_decode_parse_ladder_audit
import architect_choice_literal_password_audit
import architect_hye_bye_audit
import architect_mirror_selector_audit
import architect_passage_residual_audit
import architect_yinyang_distinctiveness_audit
import binary_key_material_backfill
import binary_message_export_audit
import bye_ciao_provenance_audit
import checkerboard_keyword_blob_gap_audit
import checkerboard_code_ic_oracle
import curated_candidate_corpus_audit
import curated_candidate_registry
import curated_v2_bounded_promotion_backfill
import curated_v2_residual_oracle_backfill
import cosmic_duality_title_initials_yinyang_audit
import cosmic_duality_chapter2_yin_lead_audit
import cosmic_duality_dropcap_inventory
import ciao_selection_coverage_audit
import cosmic_raw_digest_checkpoint_audit
import cosmic_sweep
import cosmic_duality_book_second_riddle_audit
import prefix_boundary_sweep
import creator_feasibility_envelope_audit
import creator_yingyang_faed_pair_audit
import creator_operator_vocabulary_audit
import creator_personal_disclosures_audit
import dbbi_faed_independent_consumer_audit
import dbbi_faed_boundary_selector_audit
import dbbi_faed_six_lane_audit
import dbbi_faed_transition_matrix_audit
import dbbi_faed_gf9_audit
import dbbi_faed_base27_audit
import dbbi_faed_mtf_gate_audit
import dbbi_faed_base81_token_audit
import dbbi_faed_factoradic_gate_audit
import dbbi_faed_crib_recurrence_audit
import dbbi_faed_arithmetic_model_audit
import dbbi_faed_rans_feasibility_audit
import dbbi_faed_fsm_audit
import dbbi_faed_sequence_alignment_audit
import dbbi_faed_audio_spectrogram_audit
import dbbi_faed_matrix_barcode_audit
import dbbi_faed_continued_fraction_audit
import dbbi_faed_authenticated_selector_audit
import dbbi_faed_cosmic_duality_running_key_audit
import decimal_transport_inverse_audit
import denis_prime_extraction_audit
import door_prime_passport_probe
import dual_channel_consistency_audit
import eyes_transition_chronology_audit
import excluded_wordlist_coverage_audit
import extended_cipher_recheck
import first_piece_hamming_control_audit
import first_piece_bitplane_audit
import first_piece_ggn_distinctiveness_audit
import first_piece_prime_sum_reconstruction
import first_piece_matrix_product_audit
import first_piece_second_matrixsumlist_audit
import first_piece_event_rail_preservation_audit
import first_piece_png_palette_provenance_audit
import first_piece_shadow_column_rail_audit
import first_piece_full_mask_audit
import first_hint_hash_audit
import faed_decoder_coverage_audit
import faed_monoalphabetic_sweep
import faed_token_null_check
import favicon_wayback_chronology_audit
import flo_prime_walk_provenance_audit
import first_piece_color_reconstruction
import grid_spiral
import half_better_half_algebra_audit
import hash_duality_corrected_oracle_backfill
import generate_phase_index
import gameoflogic_source_audit
import validate_vault_metadata
import first_piece_even_odd_alphabet_gate_audit
import first_piece_batch_rebus_gate_audit
import first_piece_cefe_checkerboard_gate_audit
import first_piece_overlay_dna_rgb_gate_audit
import first_piece_border_raster_scan_audit
import first_piece_marker_numeric_control_audit
import first_piece_native_matrixsumlist_audit
import first_piece_g_operator_gate_audit
import first_puzzle_announcement_audit
import jacque_fresco_wordlist_audit
import key_shape_classifier
import key_shape_sweep
import literal_raw_key_material_audit
import matrixsum_cumulative_stride_audit
import matrixsum_dbbi_faed_position_audit
import matrixsumlist_31_feasibility_audit
import matrixsumlist_provenance_refresh_audit
import matrixsumlist_page_scope_audit
import matrixsumlist_historical_code_audit
import matrixsumlist_color_prime_audit
import matrixsumlist_self_fold_consumer_audit
import macro_tail_title_insertion_audit
import macro_literal_adjacency_audit
import macro_model_disposition_audit
import minimal_macro_chain_audit
import multi_blob_structural_concordance_audit
import neo_choice_last_words_audit
import neo_smith_equation_audit
import native_favicon_shadow_audit
import nibble_packing_audit
import nopad_window_sweep
import onchain_op_return_provenance_audit
import p32_transaction_graph_audit
import p32_sibling_password_audit
import p32_solved_boundary_grammar_transfer_audit
import page_syntax_house_style_audit
import phase1_icon_symbol_layer_audit
import phase1_icon_rebus_audit
import qr_fafafa_final_structural_closure_audit
import qr_fafafa_braille_audit
import qr_fafafa_six_variant_atlas_audit
import qr_finder_ring_texture_reindex_dither_audit
import qr_finder_ring_texture_generator_comparison_audit
import qr_finder_ring_texture_irregular_rows_only_audit
import phase32_column_calibration_audit
import post_yinyang_dataflow_audit
import post_phase217_consistency_audit
import prime_matrixsum_reconstruction
import promised_standalone_audit
import provenance_monitor
import black_rabbit_negative_space_audit
import black_rabbit_drawn_overlay_audit
import rabbit_hole_nest_audit
import rabbit_nest_nibble_audit
import remaining_secret_container_delta_audit
import salphaseion_aphelion_anagram_audit
import salphaseion_urlscan_history_audit
import prime_sum_fefe_mask_composition_audit
import phase32_monologue_residual_audit
import phase3_chain_full_text_p32_sweep_audit
import phase3_sevenpart_p32_reuse_audit
import remaining_structural_avenues_audit
import roman_rail_prime_sum_audit
import safenet_luna_hsm_audit
import salphaseion_salvation_role_audit
import salphaseion_presentation_binding_audit
import salphaseion_responsive_wrap_audit
import salphaseion_wayback_history_audit
import salphaseion_heading_metadata_audit
import salphaseion_title_rebus_audit
import snapshot_dependency_closure_audit
import shadow_macro_faed_geometry_audit
import spi_cd_initials_audit
import stage0_footer_palette_layer_audit
import stage0_even_sequence_convergence_audit
import stage0_g_shadow_consumer_audit
import stage0_repeated_grayscale_audit
import stage0_png_filter_anomaly_audit
import staged_pipeline
import salt_phase_ion_audit
import cosmic_83_guide_alignment_audit
import salt_selector_permutation_audit
import qr_finder_ring_texture_center_square_continuation_render
import qr_finder_ring_texture_line_type_alphabet_audit
import synthesis_action_paths_audit
import svg_png_edge_geometry_audit
import telegram_backend_comparison_audit
import telegram_creator_media_completeness_audit
import telegram_yellow_blue_fefe_sweep
import telegram_yellow_blue_guide_audit
import telegram_yellow_blue_matrix_direction_audit
import telegram_matrix_sum_passage_audit
import thispassword_role_identifiability_audit
import thispassword_role_topology_discrimination_audit
import topology_identifiability_evidence_freeze
import thread_convergence_audit
import transition_evidence_recovery_audit
import triangular_matrixsumlist_audit
import urlblob_keywrap_backfill
import visible_referent_delta_audit
import x2sh4y0qb15_p32_candidate_audit
import x2sh4y0qb15_fork_resolution_delta_audit
import yinyang_cosmic_phase_label_audit
import yin_yang_transition_audit
import yin_yang_next_edge_audit
import looking_forward_source_audit
import input_byte_pathway_reconstruction_audit
import raw_key_chunk_audit
import raw_asset_byte_password_audit
import phase382_1141_offset_audit
import phase385_stream_compression_length_envelope_audit
import phase386_btcseed_bifid_faed_decode_audit
import phase387_btcseed_kmodest_checkpoint_audit
import phase389_btcseed_kmodest_authentication_selection_bias_audit
import phase390_p32_transaction_fingerprint_audit
import phase391_bounded_numeric_temporal_p32trailing_audit
import phase392_seed7_representation_residue_evidence_gate
import phase394_telegram_recipe_leads_authentication_audit
import phase395_youwon_vic_dual_rail_convergence_audit
import phase396_p91_header_aware_block_audit
import phase397_p91z_priority1_control_channel_audit
import phase398_p91z_priority2_bip39_recalibration_audit
import phase399_p91z_priority3_coordinate_matrix_audit
import phase400_p91z_priority4_direct_bitcoin_consumer_audit
import phase401_p91z_priority5_youwon_difference_algebra_audit
import phase402_p91z_priority6_control_data_digraph_machine_audit
import phase403_raw_control_channel_bip32_seed_audit
import phase404_q472_native_data_rail_identity_audit
import phase405_bcde_base64_sextet_channel_audit
import phase406_control285_natural_boundary_256bit_windows_audit
import phase407_p91_repeated_vigenere_key_over_q472_audit
import phase408_bifid_period_robustness_audit
import phase410_solved_vector_toolchain_provenance_audit
import telegram_export_all_hit_context_clusters
import telegram_executable_recipe_residual_audit
import telegram_export_technique_surprise_sweep
import telegram_stage1_residual_classification_audit
from page_structure_audit import DEFAULT_HTML
from telegram_export_manifest import DEFAULT_EXPORT_DIR
from cb_common import BLOBS, QUARANTINED_BLOBS


class CorrectedClaimTests(unittest.TestCase):
    def test_praised_snapshot_dependency_closure_stop_rule(self):
        report = snapshot_dependency_closure_audit.self_test()
        self.assertEqual(report["everything_occurrences_in_readme"], 1)
        self.assertEqual(
            report["everything_anchor"],
            "> Morpheus: Everything begins with choice.",
        )
        self.assertEqual(
            report["everything_anchor_context"],
            "already-solved Phase 2 explanation",
        )
        self.assertFalse(report["everything_lead_promoted"])
        self.assertEqual(
            report["tiny_hint_directional_reading"],
            "plausible but non-operational",
        )
        self.assertEqual(report["open_payload_count"], 5)
        self.assertEqual(report["frontier_cluster_count"], 3)
        self.assertFalse(report["unique_gap_gate"])
        self.assertFalse(report["oracle_authorized"])

    def test_eyes_transition_chronology_does_not_confirm_selected_31(self):
        report = eyes_transition_chronology_audit.audit()
        self.assertEqual(
            report["timing"],
            {
                "bingo_to_abstract_claim_seconds": 13,
                "bingo_to_exact_text_seconds": 601,
                "bingo_to_chain_narration_seconds": 1705,
            },
        )
        self.assertTrue(report["macro"]["eyes_clause_is_after_yinyang"])
        self.assertEqual(report["qualifier_count"], 0)
        self.assertFalse(report["oracle_authorized"])

    def test_qr_fafafa_final_structural_closure_contract(self):
        qr_fafafa_final_structural_closure_audit.self_test()

    def test_remaining_secret_container_delta_contract_and_result(self):
        module = remaining_secret_container_delta_audit
        self.assertEqual(module.descriptor_checksum("raw(deadbeef)"), "89f8spxm")
        self.assertIsNotNone(module.parse_bip38(
            b"6PRVWUbkzzsbcVac2qwfssoUJAN1Xhrg6bNk8J7Nzm5H7kxEbn2Nh2ZoGg"
        ))
        self.assertIsNotNone(module.parse_minikey(
            b"S6c56bnXQiBjk9mqSYE7ykVQ7NzrRy"
        ))
        self.assertEqual(
            module.parse_bitcoin_core_record(module._core_key_fixture())["record_type"],
            "key",
        )
        report_path = SCRIPT_DIR / "remaining_secret_container_delta_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["candidate_digest"], module.EXPECTED_CANDIDATE_DIGEST)
        self.assertEqual(report["counters"]["bodies_checked"], module.EXPECTED_BODY_COUNT)
        self.assertEqual(report["counters"]["segments_checked"], module.EXPECTED_SEGMENT_COUNT)
        self.assertEqual(report["format_registry"], list(module.FORMAT_NAMES))
        self.assertEqual(report["structural_findings_count"], 0)
        self.assertEqual(report["exact_target_hits_count"], 0)

    def test_provenance_monitor_reads_nested_state_and_preserves_last_good(self):
        module = provenance_monitor

        def live(name, digest):
            return {
                "requested_url": module.FROZEN_URLS[name],
                "final_url": module.FROZEN_URLS[name],
                "status": 200,
                "redirect_chain": [],
                "raw_sha256": digest,
                "normalized_sha256": digest,
                "content_length": 1,
                "observed_at": "2026-08-20T00:00:00Z",
                "source_class": "live_fetch",
            }

        prior_live = {name: live(name, character * 64)
                      for name, character in zip(module.FROZEN_URLS, "abc")}
        capture = {"timestamp": "20200101000000", "digest": "A",
                   "statuscode": "200", "mimetype": "text/html"}
        previous = {
            "baseline": {name: {"live": result} for name, result in prior_live.items()},
            "archive_baseline": {
                "gsmg_io_root": {"ok": True, "captures": [capture]},
                "hosterjack_repo": {"ok": True, "current_head": "28d33ccba517"},
                "naddiseo_repo": {"ok": True, "current_head": "15b43fc859c3"},
            },
        }
        current = dict(prior_live)
        current["gsmg_io_root"] = live("gsmg_io_root", "d" * 64)
        archives = {
            "salphaseion_route": {
                "wayback": {"ok": True, "alert": False},
                "urlscan": {"ok": True, "alert": False},
            },
            "gsmg_io_root": {"ok": False, "detail": "planted 503", "captures": []},
            "hosterjack_repo": {"ok": True, "current_head": "28d33ccba517",
                                "current_head_date": "2026-08-01"},
            "naddiseo_repo": {"ok": True, "current_head": "15b43fc859c3",
                              "current_head_date": "2026-08-20"},
            "live_errors": {},
        }
        report = module.assemble_report(current, archives, previous=previous)
        self.assertEqual([row["target"] for row in report["alerts"]["changed_bytes"]],
                         ["gsmg_io_root"])
        self.assertEqual(report["archive_baseline"]["gsmg_io_root"],
                         previous["archive_baseline"]["gsmg_io_root"])
        self.assertTrue(any(row["source"] == "wayback"
                            for row in report["alerts"]["operational_errors"]))

    def test_multi_blob_concordance_feature_registry_and_null_gate(self):
        module = multi_blob_structural_concordance_audit
        scalar = (1234567).to_bytes(32, "big")
        target = bytes.fromhex(
            module.private_key_details(scalar)["compressed"]["hash160"]
        )
        left = module.extract_features(scalar + b"L" * 48)
        right = module.extract_features(target + b"R" * 60)
        self.assertIn(
            "scalar_hash160:left_to_right:scalar@0:compressed->hash160@0",
            module.concordance_events(left, right),
        )
        null_records = [
            module.Record(
                index,
                "synthetic",
                f"label_{index}",
                hashlib.sha256(f"candidate-{index}".encode()).hexdigest(),
                "literal",
                "synthetic/cfb",
                blob,
                80,
                hashlib.sha256(f"body-{index}-{blob}".encode()).hexdigest(),
                module.extract_features(b"Z" * 80),
            )
            for index in range(4)
            for blob in ("A", "B")
        ]
        report = module.analyze_records(null_records, null_trials=10, null_seed=1)
        self.assertEqual(report["real_maximum_event_count"], 0)
        self.assertFalse(report["candidate_specific_results_disclosed"])
        self.assertEqual(report["promoted_rows"], [])

    def test_dbbi_faed_exact_six_lane_geometry_and_tail_are_bounded(self):
        report = dbbi_faed_six_lane_audit.audit(trials=100)
        self.assertEqual(report["geometry"]["dbbi_length"], 91)
        self.assertEqual(report["geometry"]["faed_length"], 570)
        self.assertEqual(report["geometry"]["lane_count"], 6)
        self.assertEqual(report["geometry"]["tail_length"], 24)
        self.assertEqual(len(report["body"]["lane_match_counts"]), 6)
        self.assertEqual(
            tuple(report["body_calibration"]["rows"]),
            dbbi_faed_six_lane_audit.BODY_METRIC_NAMES,
        )
        self.assertEqual(report["tail"]["endpoint_mask"].count("B"), 15)
        self.assertEqual(report["tail"]["endpoint_mask"].count("Y"), 9)
        self.assertFalse(report["plaintext_or_password_oracle_run"])
        self.assertFalse(report["promotion"]["any"])

    def test_dbbi_faed_transition_matrix_family_is_canonical_and_bounded(self):
        report = dbbi_faed_transition_matrix_audit.audit(trials=25)
        self.assertEqual(report["matrix_shape"], (9, 9))
        self.assertEqual(report["transition_totals"], {"DBBI": 90, "FAED": 569})
        self.assertEqual(sum(report["DBBI"]["row_sums"]), 90)
        self.assertEqual(sum(report["FAED"]["column_sums"]), 569)
        self.assertEqual(
            tuple(report["sequence_calibration"]["rows"]),
            tuple(dbbi_faed_transition_matrix_audit.SEQUENCE_METRIC_ALTERNATIVES),
        )
        self.assertEqual(
            report["degree_profile_test"]["permutation_count"], 362_880
        )
        self.assertFalse(report["candidate_text_generated"])
        self.assertFalse(report["password_oracle_run"])

    def test_dbbi_faed_gf9_family_has_six_presentations_and_no_text_oracle(self):
        report = dbbi_faed_gf9_audit.audit(trials=3)
        self.assertEqual(report["presentation_count"], 6)
        self.assertEqual(
            report["irreducible_quadratics"], ((0, 1), (1, 2), (2, 2))
        )
        self.assertEqual(
            report["lane_geometry"], {"count": 6, "width": 91, "unused_tail": 24}
        )
        self.assertEqual(
            tuple(report["calibration"]["rows"]),
            tuple(dbbi_faed_gf9_audit.METRIC_ALTERNATIVES),
        )
        self.assertFalse(report["candidate_text_generated"])
        self.assertFalse(report["password_oracle_run"])

    def test_dbbi_faed_base27_is_exact_gap_and_preserves_leftover_trits(self):
        report = dbbi_faed_base27_audit.audit(trials=5)
        self.assertFalse(report["prior_coverage"]["base27_present"])
        self.assertEqual(report["family"]["declarations_per_source"], 32)
        self.assertEqual(report["source_geometry"]["DBBI"]["output_characters"], 60)
        self.assertEqual(report["source_geometry"]["DBBI"]["leftover_trits"], 2)
        self.assertEqual(report["source_geometry"]["FAED"]["output_characters"], 380)
        self.assertEqual(report["source_geometry"]["FAED"]["leftover_trits"], 0)
        self.assertFalse(report["password_oracle_run"])

    def test_dbbi_faed_mtf_gate_keeps_bwt_conditional(self):
        report = dbbi_faed_mtf_gate_audit.audit(trials=10)
        self.assertEqual(report["rank_mapping"], "a=0 through i=8")
        self.assertTrue(report["initial_alphabet_structural_relabel_invariant"])
        self.assertEqual(report["calibration"]["metric_count"], 10)
        self.assertEqual(report["bwt"]["primary_indices_scanned"], 0)
        self.assertFalse(report["candidate_text_generated"])
        self.assertFalse(report["password_oracle_run"])

    def test_dbbi_faed_base81_keeps_odd_symbol_and_consumer_conditional(self):
        report = dbbi_faed_base81_token_audit.audit(trials=10)
        self.assertEqual(report["sources"]["DBBI"]["token_count"], 45)
        self.assertEqual(report["sources"]["DBBI"]["leftover_symbol"], "e")
        self.assertEqual(report["sources"]["FAED"]["token_count"], 285)
        self.assertEqual(report["sources"]["FAED"]["leftover_symbol"], "")
        self.assertEqual(report["calibration"]["metric_count"], 12)
        self.assertEqual(report["homophonic_or_lookup_stage"]["operations_run"], 0)
        self.assertFalse(report["candidate_text_generated"])
        self.assertFalse(report["password_oracle_run"])

    def test_dbbi_faed_factoradic_gate_uses_only_fixed_sizes_and_no_consumer(self):
        report = dbbi_faed_factoradic_gate_audit.audit(trials=10)
        self.assertFalse(
            report["specification_correction"]["standard_lehmer_is_self_delimiting"]
        )
        self.assertEqual(report["specification_correction"]["externally_fixed_sizes"], (6, 9))
        self.assertEqual(report["calibration"]["metric_count"], 16)
        self.assertEqual(report["permutation_consumer"]["operations_run"], 0)
        self.assertFalse(report["candidate_text_generated"])
        self.assertFalse(report["password_oracle_run"])

    def test_dbbi_faed_crib_recurrence_fits_two_and_scores_only_holdout(self):
        report = dbbi_faed_crib_recurrence_audit.audit(trials=3)
        self.assertEqual(report["fit_digits"], 2)
        self.assertEqual(report["specification_count"], 4)
        self.assertEqual(report["calibration"]["metric_count"], 4)
        self.assertEqual(
            tuple(report["cribs"]), ("yinyang", "thispassword", "seed")
        )
        self.assertFalse(report["candidate_text_generated"])
        self.assertFalse(report["password_oracle_run"])

    def test_dbbi_faed_arithmetic_model_requires_termination_and_exact_roundtrip(self):
        report = dbbi_faed_arithmetic_model_audit.audit()
        self.assertEqual(report["declaration_count"], 4)
        self.assertTrue(report["missing_required_source_fields"]["termination_or_eos"])
        self.assertEqual(report["exact_canonical_hits"], ())
        self.assertEqual(report["source_plaintext_hits"], ())
        self.assertTrue(all(
            row["input_codepoint_inside_final_interval"] for row in report["rows"]
        ))
        self.assertFalse(report["promotion"]["promoted"])
        self.assertFalse(report["candidate_text_generated"])
        self.assertFalse(report["password_oracle_run"])

    def test_dbbi_faed_rans_requires_terminal_state_and_marks_residual_roundtrip_tautology(self):
        report = dbbi_faed_rans_feasibility_audit.audit()
        self.assertEqual(report["model"]["total"], 91)
        self.assertEqual(len(report["terminal_rows"]), 3)
        self.assertEqual(len(report["fixed_length_rows"]), 2)
        self.assertTrue(all(
            row["reencode_with_residual_is_tautological"]
            for row in report["fixed_length_rows"]
        ))
        self.assertEqual(report["provenance"]["literal_anstoo_creator_explanations"], 0)
        self.assertEqual(report["exact_terminal_roundtrip_hits"], ("zero",))
        self.assertEqual(report["nondegenerate_terminal_roundtrip_hits"], ())
        self.assertFalse(report["candidate_text_generated"])
        self.assertFalse(report["password_oracle_run"])

    def test_dbbi_faed_fsm_uses_one_canonical_81_plus_10_serialization(self):
        report = dbbi_faed_fsm_audit.audit()
        self.assertEqual(report["serialization"]["alternate_conventions_tested"], 0)
        self.assertEqual(report["trailer_text"], "gigbeeeabe")
        self.assertEqual(len(report["statistic_rows"]), 9)
        self.assertEqual(report["corrected_minimum"], 1.0)
        self.assertFalse(report["gate_passed"])
        self.assertFalse(report["output_equals_faed"])
        self.assertFalse(report["output_prefix_equals_dbbi"])
        self.assertFalse(report["output_contains_dbbi"])
        self.assertFalse(report["candidate_text_generated"])
        self.assertFalse(report["password_oracle_run"])

    def test_dbbi_faed_fsm_report_exposes_full_output_text(self):
        """Phase 335: `output_prefix` used to be the only serialized form of
        the machine's full output (truncated to 160 chars), which is why P0A
        scored this model "conditionally eligible" instead of eligible --
        the candidate text existed but wasn't retained in the report. This
        pins the fix: `output_text` is the untruncated string, matches FAED's
        own length (the input tape drives one output symbol per step), and
        `output_prefix` is still exactly its first 160 characters."""
        report = dbbi_faed_fsm_audit.audit()
        self.assertIn("output_text", report)
        self.assertEqual(len(report["output_text"]), len(FAED))
        self.assertEqual(report["output_prefix"], report["output_text"][:160])
        self.assertTrue(all(c in "abcdefghi" for c in report["output_text"]))

    def test_dbbi_faed_sequence_alignment_is_selection_calibrated(self):
        report = dbbi_faed_sequence_alignment_audit.audit()
        self.assertEqual(report["model"]["sliding_window_count"], 480)
        self.assertEqual(report["model"]["alternate_cost_models_tested"], 0)
        self.assertEqual(len(report["fixed_distances"]), 6)
        self.assertEqual(len(report["statistic_rows"]), 3)
        self.assertEqual(report["fixed_distances"], (71, 73, 64, 70, 68, 69))
        self.assertEqual(report["best_start"], 112)
        self.assertEqual(report["best_alignment"]["distance"], 62)
        self.assertFalse(report["gate_passed"])
        self.assertFalse(report["gap_positions_interpreted"])
        self.assertFalse(report["candidate_text_generated"])
        self.assertFalse(report["password_oracle_run"])

    def test_dbbi_faed_audio_family_is_exactly_three_mappings(self):
        with self.subTest("deterministic renderer"):
            dbbi_faed_audio_spectrogram_audit.self_test()

    def test_dbbi_faed_matrix_barcode_family_requires_real_finders(self):
        dbbi_faed_matrix_barcode_audit.self_test()

    def test_dbbi_faed_continued_fractions_use_closed_constant_registry(self):
        report = dbbi_faed_continued_fraction_audit.audit()
        self.assertEqual(len(report["maps"]), 3)
        self.assertEqual(report["target_registry"]["count"], 17)
        self.assertEqual(len(report["rows"]), 6)
        self.assertEqual(report["exact_value_hits"], ())
        self.assertEqual(report["near_value_hits"], ())
        self.assertEqual(report["numerator_or_denominator_hits"], ())
        self.assertFalse(report["promotion"])
        self.assertFalse(report["decimal_substring_search_run"])
        self.assertFalse(report["candidate_text_generated"])
        self.assertFalse(report["password_oracle_run"])

    def test_dbbi_faed_authenticated_selector_family_is_closed(self):
        report = dbbi_faed_authenticated_selector_audit.audit()
        self.assertEqual(report["target_category_count"], 4)
        self.assertEqual(report["target_string_count"], 5)
        self.assertEqual(report["candidate_count"], 20)
        self.assertTrue(report["single_modulo_is_vacuous_for_all_targets"])
        self.assertEqual(len(report["statistic_rows"]), 4)
        self.assertEqual(report["exact_target_hits"], ())
        self.assertFalse(report["gate_passed"])
        self.assertTrue(report["diagnostic_outputs_generated"])
        self.assertFalse(report["candidate_text_promoted"])
        self.assertFalse(report["candidate_text_generated"])
        self.assertFalse(report["password_oracle_run"])

    def test_phase32_monologue_residual_zero_hits(self):
        phase32_monologue_residual_audit.self_test()
        report = phase32_monologue_residual_audit.audit()
        self.assertEqual(report["candidate_count"], 19)
        self.assertEqual(report["validation_num_length"], 149)
        self.assertEqual(
            report["blob_names"], ("COSMIC", "P32TRAILING", "SALPH", "URLBLOB")
        )
        self.assertEqual(report["hits"], [])
        # Independent check that the "two 32-byte keys" reading is only one
        # of 16 padding-consistent plaintext lengths, not byte-count-forced.
        import base64

        from data import P32_TRAILING_BLOB_B64

        raw = base64.b64decode(P32_TRAILING_BLOB_B64)
        self.assertEqual(len(raw), 96)
        ciphertext_len = len(raw) - 16
        self.assertEqual(ciphertext_len, 80)
        consistent_lengths = {ciphertext_len - pad for pad in range(1, 17)}
        self.assertEqual(consistent_lengths, set(range(64, 80)))
        self.assertIn(64, consistent_lengths)

    def test_phase3_sevenpart_p32_reuse_negative(self):
        phase3_sevenpart_p32_reuse_audit.self_test()
        report = phase3_sevenpart_p32_reuse_audit.audit()
        self.assertEqual(report["concat_length"], 227)
        self.assertEqual(
            report["concat_sha256"],
            "1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5",
        )
        self.assertEqual(report["hits"], [])
        # Independent re-derivation, not a re-check of the module's own math.
        import hashlib

        parts = (
            "causality", "Safenet", "Luna", "HSM", "11110",
            "0x736B6E616220726F662074756F6C69616220646E6F63657320666F206B6E69"
            "7262206E6F20726F6C6C65636E61684320393030322F6E614A2F3330207365"
            "6D695420656854",
            "B5KR/1r5B/2R5/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 b - - 0 1",
        )
        concat = "".join(parts)
        self.assertEqual(len(concat), 227)
        self.assertEqual(
            hashlib.sha256(concat.encode()).hexdigest(),
            "1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5",
        )

    def test_phase3_chain_full_text_p32_sweep_negative(self):
        phase3_chain_full_text_p32_sweep_audit.self_test()
        report = phase3_chain_full_text_p32_sweep_audit.audit()
        self.assertEqual(report["candidate_count"], 48)
        self.assertEqual(report["hits"], [])
        candidates = report["candidates"]
        self.assertTrue(any("keymakers" in c for c in candidates))
        self.assertTrue(any("merovingian" in c.lower() for c in candidates))
        self.assertTrue(any("SIXTEEN ENCRYPTIONS" in c for c in candidates))
        self.assertTrue(any("CIAO BELLA O" in c for c in candidates))

    def test_x2sh4y0qb15_p32_candidate_negative(self):
        report = x2sh4y0qb15_p32_candidate_audit.self_test()
        self.assertEqual(report["candidate_count"], 42)
        self.assertEqual(report["unique_material_count"], 1362)
        self.assertEqual(
            report["candidate_digest"],
            "509bfbf096af656567d1bfc6a58824a9ca41c2ea7c4876d1bbd74ce1504954f7",
        )
        self.assertEqual(report["cbc_menu_gap_variant_count"], 20)
        self.assertFalse(report["empty_material_present"])
        self.assertIn(
            "(4,15)(-42,-16)(32,82)(2,0)", report["candidates"]
        )
        self.assertIn(
            x2sh4y0qb15_p32_candidate_audit.SOURCE_BLOCK,
            report["candidates"],
        )
        self.assertEqual(report["hits"], [])
        # Independent check of the backspace-provenance claim: the earliest
        # 2020 repost lacks the trailing \b's a 2025 repost has.
        import json
        from pathlib import Path

        def flatten(value):
            if isinstance(value, str):
                return value
            return "".join(
                item if isinstance(item, str) else item.get("text", "")
                for item in value
            )

        export_path = Path(
            "/home/loginwashere/Downloads/Telegram Desktop/"
            "ChatExport_2026-07-26/result.json"
        )
        if export_path.exists():
            payload = json.loads(export_path.read_text(encoding="utf-8"))
            messages = {m["id"]: m for m in payload["messages"]}
            earliest_text = flatten(messages[2834]["text"])
            self.assertTrue(earliest_text.endswith("worst gear."))
            self.assertNotIn("\\b", earliest_text)
            later_text = flatten(messages[38301]["text"])
            self.assertEqual(later_text.count("\\b"), 8)

    def test_x2sh4y0qb15_fork_resolution_delta_negative(self):
        report = x2sh4y0qb15_fork_resolution_delta_audit.self_test()
        self.assertEqual(report["resolved_values"], {"S": 32, "H": 42, "B": 25, "Q": 82})
        self.assertEqual(report["candidate_count"], 26)
        self.assertIn("5152280Y424232X", report["candidates"])
        self.assertEqual(report["hits"], [])

    def test_phase385_stream_compression_length_envelope(self):
        report = phase385_stream_compression_length_envelope_audit.self_test()
        self.assertEqual(report["lengths"]["bip38"]["raw"], 58)
        self.assertEqual(report["lengths"]["xprv_xpub"]["raw"], 111)
        self.assertIn(
            ("bip38", "zlib", "SALPH", "cbc"), report["newly_admitted"]
        )
        self.assertIn(
            ("hex64_text", "zlib", "SALPH", "cbc"), report["newly_excluded"]
        )
        self.assertFalse(
            any(row[0] == "xprv_xpub" for row in report["newly_admitted"])
        )

    def test_phase386_btcseed_bifid_faed_decode(self):
        report = phase386_btcseed_bifid_faed_decode_audit.self_test()
        self.assertEqual(report["grid_keyword"], "DBIFHCEGAKLMNOPQRSTUVWXYZ")
        self.assertTrue(report["starts_with_btcseed"])
        self.assertEqual(report["pre_z_length"], 97)
        self.assertFalse(report["pre_z_matches_dbbi_length"])
        self.assertEqual(report["embedded_word_count"], 13)
        self.assertLess(
            report["embedded_word_count"],
            report["baseline_mean"] + report["baseline_stdev"],
        )

    def test_phase387_btcseed_kmodest_checkpoint(self):
        phase387_btcseed_kmodest_checkpoint_audit.self_test()
        observed = phase387_btcseed_kmodest_checkpoint_audit.observed_report()
        self.assertEqual(observed["first_z_index"], 97)
        self.assertEqual(observed["prefix_length_through_z"], 98)
        self.assertEqual(observed["candidate"], "KMODEST")

    def test_phase389_btcseed_kmodest_authentication_selection_bias(self):
        phase389_btcseed_kmodest_authentication_selection_bias_audit.self_test()
        observed = phase389_btcseed_kmodest_authentication_selection_bias_audit.observed_family_report()
        self.assertEqual(observed["family_size"], 224)
        self.assertNotEqual(observed["family_max_text"], "KMODEST")
        self.assertGreater(observed["family_max_score"], observed["target_score"])

    def test_phase390_p32_transaction_fingerprint(self):
        phase390_p32_transaction_fingerprint_audit.self_test()
        result = phase390_p32_transaction_fingerprint_audit.audit()
        self.assertEqual(result["total_signing_inputs"], 6)
        self.assertFalse(result["repeated_r"])
        self.assertTrue(result["all_strict_der"])
        self.assertTrue(result["all_low_s"])
        self.assertEqual(result["pubkey_encodings"], ["uncompressed"])

    def test_phase391_bounded_numeric_temporal_p32trailing(self):
        phase391_bounded_numeric_temporal_p32trailing_audit.self_test()
        result = phase391_bounded_numeric_temporal_p32trailing_audit.run_oracle()
        self.assertEqual(result["material_count"], 69)
        self.assertEqual(result["blobs"], ("P32TRAILING",))
        self.assertEqual(result["total_hits"], 0)

    def test_phase392_seed7_representation_residue_evidence_gate(self):
        phase392_seed7_representation_residue_evidence_gate.self_test()
        report = phase392_seed7_representation_residue_evidence_gate.evidence_gate_report()
        v = report["verdict"]
        self.assertFalse(v["html_entity_pathway_applicable"])
        self.assertFalse(v["utf16_low_byte_pathway_applicable"])
        self.assertFalse(v["textcontent_vs_copy_pathway_applicable"])

    @unittest.skipUnless(
        (Path(DEFAULT_EXPORT_DIR) / "result.json").exists(),
        "Telegram export is unavailable",
    )
    def test_phase393_telegram_executable_recipe_residual(self):
        report = telegram_executable_recipe_residual_audit.audit()
        telegram_executable_recipe_residual_audit.corpus_self_test(report)
        self.assertEqual(
            report["classification_counts"],
            {"covered": 88, "noise_or_incomplete": 51, "new_lead": 3},
        )

    def test_phase394_telegram_recipe_leads_authentication(self):
        report = phase394_telegram_recipe_leads_authentication_audit.self_test(
            run_oracle=False
        )
        self.assertEqual(report["matrix"]["rank12_flip_count"], 27)
        self.assertEqual(report["bip39"]["mapping_window_trials"], 3696)
        self.assertEqual(report["bip39"]["checksum_valid_count"], 13)
        self.assertEqual(report["wallet"]["derived_private_key_count"], 6000)
        self.assertEqual(report["wallet"]["derived_hits"], [])

    def test_phase395_youwon_vic_dual_rail_convergence(self):
        report = phase395_youwon_vic_dual_rail_convergence_audit.self_test(
            run_oracle=True
        )
        self.assertEqual(report["borrow_rail"]["runs_len_ge7"], [(21, 7)])
        self.assertTrue(report["borrow_rail"]["forced_matches_actual"])
        self.assertEqual(report["vic_rail"]["max_run_start"], 21)
        self.assertEqual(report["vic_rail"]["second_longest"], 6)
        self.assertEqual(report["final_candidate_oracle"]["total_hits"], 0)

    def test_phase396_p91_header_aware_block(self):
        report = phase396_p91_header_aware_block_audit.self_test(run_oracle=True)
        self.assertEqual(report["structure"]["z_count"], 1)
        self.assertTrue(report["structure"]["p91_matches_dbbi_m91_length"])
        for entry in report["combinators"].values():
            self.assertEqual(entry["keyword_hits"], [])
            self.assertGreater(entry["baseline_tail_rate"], 0.05)
        self.assertEqual(report["oracle"]["materials_tried"], 30)
        self.assertEqual(report["oracle"]["total_hits"], 0)

    def test_phase397_p91z_priority1_control_channel(self):
        report = phase397_p91z_priority1_control_channel_audit.self_test()
        self.assertEqual(report["candidate_count"], 8)
        self.assertFalse(report["any_parser_valid"])
        self.assertFalse(report["any_exact_target_hit"])

    def test_phase398_p91z_priority2_bip39_recalibration(self):
        report = phase398_p91z_priority2_bip39_recalibration_audit.self_test()
        self.assertEqual(report["total_trials"], 308)
        self.assertEqual(report["column_major_bcde"], (2, 1, 0, 3))
        self.assertEqual(report["row_major_bcde"], (1, 2, 0, 3))
        self.assertIsNone(report["natural_offset_selects_30"])

    def test_phase399_p91z_priority3_coordinate_matrix(self):
        report = phase399_p91z_priority3_coordinate_matrix_audit.self_test()
        self.assertTrue(report["planted_parity_a_exact"])
        self.assertFalse(report["real_any_exact"])
        self.assertGreater(report["family_wise_rate"], 0.005)

    def test_phase400_p91z_priority4_direct_bitcoin_consumer(self):
        report = phase400_p91z_priority4_direct_bitcoin_consumer_audit.self_test()
        self.assertEqual(report["root_count"], 8)
        self.assertEqual(report["total_address_checks"], 96032)
        self.assertFalse(report["any_hit"])
        self.assertEqual(len(report["planted_direct_key_positive"]["hits"]), 1)
        self.assertEqual(len(report["planted_bip32_path_positive"]["hits"]), 1)

    def test_phase401_p91z_priority5_youwon_difference_algebra(self):
        report = phase401_p91z_priority5_youwon_difference_algebra_audit.self_test()
        self.assertTrue(report["as1_roundtrip_matches_p91"])
        self.assertTrue(report["cs1_roundtrip_matches_p91"])
        self.assertEqual(report["real_keyword_hits"], {})
        self.assertEqual(report["oracle"]["hits"], [])
        self.assertEqual(report["direct_key"]["hits"], [])
        self.assertGreater(report["family_wise_rate"], 0.005)
        self.assertIn("SATOSHI", report["planted_synthetic_english_positive"]["keyword_hits"])

    def test_phase402_p91z_priority6_control_data_digraph_machine(self):
        report = phase402_p91z_priority6_control_data_digraph_machine_audit.self_test()
        self.assertEqual(report["control_rail_length"], 236)
        self.assertEqual(report["control_rail_alphabet"], "BCDE")
        self.assertEqual(report["real_keyword_hits"], {})
        self.assertEqual(report["oracle"]["hits"], [])
        self.assertEqual(report["letter_direct_key"]["hits"], [])
        self.assertEqual(report["byte_direct_key"]["hits"], [])
        self.assertGreater(report["family_wise_rate"], 0.005)
        self.assertTrue(report["planted_selector_phrase_positive"]["matches"])
        self.assertTrue(report["planted_rotation_phrase_positive"]["matches"])
        self.assertTrue(report["planted_salted_header_byte_positive"]["result"]["parser_valid"])
        self.assertFalse(any(r["parser_valid"] for r in report["byte_results"].values()))

    def test_phase403_raw_control_channel_bip32_seed(self):
        report = phase403_raw_control_channel_bip32_seed_audit.self_test()
        self.assertEqual(report["candidate_count"], 8)
        self.assertEqual(report["total_address_checks"], 96016)
        self.assertFalse(report["any_hit"])
        self.assertEqual(len(report["planted_bip32_path_positive"]["hits"]), 1)

    def test_phase404_q472_native_data_rail_identity(self):
        report = phase404_q472_native_data_rail_identity_audit.self_test()
        self.assertEqual(report["control_length"], 236)
        self.assertEqual(report["data_length"], 236)
        self.assertEqual(report["control_alphabet"], "BCDE")
        self.assertEqual(report["oracle"]["hits"], [])
        self.assertEqual(report["direct_key"]["hits"], [])
        self.assertGreater(report["p_value"], 0.005)
        self.assertFalse(report["promoted"])
        self.assertLessEqual(report["planted_language_positive"]["p_value"], 0.005)
        self.assertTrue(report["planted_blob_positive"]["hit_found"])
        self.assertFalse(report["planted_blob_positive"]["wrong_material_hit"])

    def test_phase405_bcde_base64_sextet_channel(self):
        report = phase405_bcde_base64_sextet_channel_audit.self_test()
        self.assertEqual(report["candidate_count"], 4)
        self.assertEqual(report["full_control_length"], 285)
        self.assertEqual(report["p91_control_length"], 45)
        self.assertFalse(report["any_parser_valid"])
        self.assertFalse(report["any_exact_target_hit"])
        self.assertTrue(report["planted_roundtrip_positive"]["matches"])
        self.assertTrue(report["planted_typed_parser_positive"]["result"]["parser_valid"])
        for entry in report["candidates"].values():
            self.assertEqual(entry["discarded_terminal_bits"], 2)

    def test_phase406_control285_natural_boundary_256bit_windows(self):
        report = phase406_control285_natural_boundary_256bit_windows_audit.self_test()
        self.assertEqual(report["control285_length"], 285)
        self.assertEqual(report["window_offsets"], [0, 4, 49, 157])
        self.assertEqual(report["candidate_count"], 16)
        self.assertEqual(report["total_address_checks"], 192064)
        self.assertFalse(report["any_hit"])
        self.assertTrue(report["planted_roundtrip_positive"]["matches"])
        self.assertEqual(len(report["planted_direct_key_positive"]["hits"]), 1)
        self.assertEqual(len(report["planted_bip32_path_positive"]["hits"]), 1)

    def test_phase407_p91_repeated_vigenere_key_over_q472(self):
        report = phase407_p91_repeated_vigenere_key_over_q472_audit.self_test()
        self.assertEqual(report["p91_length"], 91)
        self.assertEqual(report["q472_length"], 472)
        self.assertTrue(report["as1_roundtrip_matches_q472"])
        self.assertTrue(report["cs1_roundtrip_matches_q472"])
        self.assertEqual(report["real_keyword_hits"], {})
        self.assertEqual(report["oracle"]["hits"], [])
        self.assertEqual(report["direct_key"]["hits"], [])
        self.assertGreater(report["family_wise_rate"], 0.005)
        self.assertIn("SATOSHI", report["planted_synthetic_english_positive"]["keyword_hits"])
        self.assertEqual(len(report["planted_direct_key_positive"]["hits"]), 1)

    def test_phase408_bifid_period_robustness(self):
        report = phase408_bifid_period_robustness_audit.self_test()
        self.assertEqual(report["schedule_count"], 8)
        self.assertTrue(report["period_570_matches_baseline"])
        self.assertEqual(report["schedules_starting_with_btcseed"], ["period_570"])
        self.assertFalse(report["period_robust"])
        for label, entry in report["candidates"].items():
            self.assertTrue(entry["roundtrip_matches_real_ciphertext"], label)
        for label, result in report["planted_btcseed_roundtrip_positives"].items():
            self.assertTrue(result["recovered_matches_plaintext"], label)
            self.assertTrue(result["recovered_starts_with_btcseed"], label)

    def test_phase410_solved_vector_toolchain_provenance(self):
        report = phase410_solved_vector_toolchain_provenance_audit.self_test()
        self.assertEqual(report["vector_count"], 3)
        for key, entry in report["manifest"].items():
            self.assertTrue(entry["roundtrip_matches_original_container"], key)
            self.assertTrue(entry["plaintext_prefix_matches"], key)
            successes = [
                label for label, r in entry["controls"].items() if r["padding_valid"]
            ]
            self.assertEqual(successes, ["representation_lowercase_hex"], key)

    def test_telegram_technique_surprise_sweep_token_boundaries(self):
        telegram_export_technique_surprise_sweep.self_test()

    @unittest.skipUnless(
        (Path(DEFAULT_EXPORT_DIR) / "result.json").exists(),
        "Telegram export is unavailable",
    )
    def test_telegram_all_hit_context_clusters(self):
        telegram_export_all_hit_context_clusters.self_test()

    @unittest.skipUnless(
        (Path(DEFAULT_EXPORT_DIR) / "result.json").exists(),
        "Telegram export is unavailable",
    )
    def test_telegram_stage1_residual_classification(self):
        telegram_stage1_residual_classification_audit.self_test()

    def test_p32_transaction_graph_snapshot(self):
        p32_transaction_graph_audit.self_test()
        report = json.loads(p32_transaction_graph_audit.DEFAULT_REPORT.read_text())
        cache = json.loads(p32_transaction_graph_audit.DEFAULT_CACHE.read_text())
        self.assertTrue(p32_transaction_graph_audit.validate_artifacts(report, cache))

    def test_p32_sibling_password_negative(self):
        p32_sibling_password_audit.self_test()
        report = p32_sibling_password_audit.audit()
        self.assertEqual(report["phase32_plaintext_bytes"], 2422)
        self.assertEqual(
            report["phase32_plaintext_sha256"],
            "b82afeb86f9e50848220f9b64b744b821400308aea273a1c949b9d2d0e408a34",
        )
        self.assertEqual(report["answer_321_length"], 1539)
        self.assertEqual(report["answer_322_length"], 91)
        self.assertEqual(
            report["construction"]["established_selection"],
            "NCSYANGCAHIRIASOGALEAFAYANESTVE",
        )
        split_guide = report["construction"]["split_final_be_guide"]
        self.assertEqual(
            split_guide["prime_rule_selection"],
            "NCSYANGCAHIRIASOGALEAFAYANESTV",
        )
        self.assertEqual(
            split_guide["token_endpoint_projection"],
            "NCSYAAORTERKBLTATRNEAED",
        )
        self.assertEqual(
            split_guide["raw_endpoint_projection"],
            "NCSYNGCAIIASOGLEAAANETE",
        )
        self.assertEqual(report["candidate_count"], 25)
        self.assertEqual(report["password_material_count"], 50)
        structural = report["structural_oracle"]
        self.assertEqual(structural["ciphertext_bytes"], 80)
        self.assertEqual(structural["ciphertext_blocks"], 5)
        self.assertEqual(
            structural["trial_count"],
            report["password_material_count"] * len(
                p32_sibling_password_audit.KDF_SPECS
            ),
        )
        self.assertEqual(structural["hits"], [])
        # The 23/16/7 triple belongs to the split-final-BE guide's endpoint
        # profile, not the established prime walk (23/15/8) -- independent
        # re-check of the module's own falsification claim.
        self.assertFalse(report["interpretation"]["prime_walk_matches_23_16_7"])
        self.assertTrue(
            report["interpretation"]["split_final_be_guide_matches_23_16_7"]
        )

    def test_faed_hex_nibble_packing_negative(self):
        nibble_packing_audit.self_test()
        report = nibble_packing_audit.audit()
        self.assertEqual(report["source_lengths"], {"DBBI": 91, "FAED": 570})
        self.assertEqual(report["variant_count"], 8)
        self.assertEqual(report["faed_packed_byte_length"], 285)
        self.assertEqual(report["unique_password_material_count"], 24)
        self.assertTrue(report["phase32_positive_control"])
        self.assertTrue(all(
            row["leftover_nibble"] is not None
            for row in report["dbbi_diagnostic_rows"]
        ))
        self.assertTrue(all(
            not row["prefix_signatures"] and not row["compression_results"]
            for row in report["faed_rows"]
        ))
        by_label = {row["label"]: row for row in report["faed_rows"]}
        self.assertEqual(
            by_label["a0i8/forward/high_low"]["sha256"],
            "c352749704479ef054a6afa1a7a6262c1fea5d646704ffd7db7eb6d7ccc59265",
        )
        self.assertEqual(report["hits"], [])

    def test_dbbi_faed_decimal_transport_inverse_negative(self):
        decimal_transport_inverse_audit.self_test()
        report = decimal_transport_inverse_audit.audit()
        self.assertEqual(report["source_lengths"], {"DBBI": 91, "FAED": 570})
        self.assertEqual(report["source_zero_symbol_counts"], {"DBBI": 0, "FAED": 0})
        self.assertEqual(
            report["known_transport_controls"],
            {
                "lastwordsbeforearchichoice": "lastwordsbeforearchichoice",
                "thispassword": "thispassword",
            },
        )
        self.assertEqual(report["variant_count"], 8)
        self.assertEqual(report["rejected_variants"], ())
        self.assertEqual(report["unique_password_material_count"], 24)
        self.assertTrue(report["phase32_positive_control"])
        self.assertTrue(all(
            not row["prefix_signatures"] and not row["compression_results"]
            for row in report["rows"]
        ))
        by_label = {row["label"]: row for row in report["rows"]}
        self.assertEqual(
            by_label["DBBI/forward/bytes_forward"]["sha256"],
            "7270ed152fa64b85f144f99b49352ecabeb01c0f0b624fb71cb648f91d1d8b80",
        )
        self.assertEqual(
            by_label["FAED/forward/bytes_forward"]["sha256"],
            "7f14db2d90301b8e1d16ff014ad3e84ba75350ef828ad9b8a8a26b1e69302de9",
        )
        self.assertEqual(report["hits"], [])

    def test_roman_rail_prime_sum_bounded_family(self):
        roman_rail_prime_sum_audit.self_test()
        report = roman_rail_prime_sum_audit.audit()
        self.assertEqual(len(report["rail_rows"]), 14)
        self.assertEqual(len(report["rail_match_rows"]), 1)
        match = report["rail_match_rows"][0]
        self.assertEqual(
            (
                match["blue_token"], match["yellow_token"],
                match["blue_numeral"], match["yellow_numeral"],
                match["blue_value"], match["yellow_value"],
            ),
            ("DBBI", "FAED", "CDI", "CD", 401, 400),
        )
        # Independent sensitivity check: the broader disclosed token family
        # has a second construction, so DBBI/FAED is not globally unique.
        self.assertEqual(
            [
                (row["blue_token"], row["yellow_token"], row["title_fragment"])
                for row in report["control_match_rows"]
            ],
            [("DBBI", "FAED", "C"), ("yinyang", "FEFE", "CD")],
        )
        self.assertIsNone(roman_rail_prime_sum_audit.parse_canonical_roman("IC"))
        self.assertEqual(report["fefe_projection"], "")

    def test_phase1_icon_symbol_layer_scope(self):
        phase1_icon_symbol_layer_audit.self_test()
        report = phase1_icon_symbol_layer_audit.scope_report()
        self.assertEqual(
            (report["candidate_count"], report["candidate_digest"]),
            (16, "11a7607d7b59242a"),
        )
        self.assertEqual(report["unique_passphrases"], 504)
        self.assertEqual(report["effective_operations"], 282240)
        self.assertEqual(report["raw_key_attempts"], 220)

    def test_v2_residual_oracle_backfill_scope(self):
        report = curated_v2_residual_oracle_backfill.scope_report()
        self.assertEqual(
            (len(report["seed_candidates"]), report["seed_candidate_digest"]),
            (2, "10da6a91233b3292"),
        )
        self.assertEqual(
            (
                len(report["looking_forward_candidates"]),
                report["looking_forward_candidate_digest"],
            ),
            (19, "bf5116a99829c05f"),
        )
        self.assertEqual(
            (report["all_candidate_count"], report["all_candidate_digest"]),
            (21, "537635ec6fa1ce0f"),
        )
        self.assertEqual(report["seed_unique_passphrases"], 36)
        self.assertEqual(report["looking_forward_unique_passphrases"], 792)
        self.assertEqual(report["all_unique_passphrases"], 828)
        self.assertEqual(report["cbc_decryptions"], 3456)
        self.assertEqual(report["ecb_decryptions"], 39744)
        self.assertEqual(report["stream_decryptions"], 119232)
        self.assertEqual(report["keywrap_effective_unwrap_attempts"], 158976)
        self.assertEqual(report["effective_operations"], 321408)

    def test_excluded_wordlist_coverage_matrix_and_menu_gap_scope(self):
        report = excluded_wordlist_coverage_audit.audit()
        scope = report["menu_gap_scope"]
        # 29, not 26 -- see the matching comment in
        # test_curated_candidate_corpus_identity_and_provenance below.
        self.assertEqual(report["excluded_wordlist_count"], 29)
        self.assertEqual(
            (scope["candidate_count"], scope["candidate_digest"]),
            (625, "854bffab41ecb1ef"),
        )
        self.assertEqual(scope["candidate_form_evaluations"], 17163)
        self.assertEqual(scope["unique_generated_passphrases"], 16101)
        self.assertEqual(scope["prior_exact_candidate_overlap"], 62)
        self.assertEqual(
            (scope["net_new_exact_candidates"], scope["net_new_exact_candidate_digest"]),
            (563, "a5a3c95b8d8bb594"),
        )
        self.assertEqual(scope["prior_unique_passphrase_overlap"], 2358)
        self.assertEqual(scope["net_new_unique_passphrases"], 13743)
        self.assertEqual(scope["prior_scheduled_evaluations"], 2358)
        self.assertEqual(scope["net_new_scheduled_evaluations"], 14805)
        self.assertEqual(scope["cipher_kdf_variants"], 20)
        self.assertEqual(tuple(scope["blobs"]), tuple(BLOBS))
        self.assertEqual(scope["concrete_decryptions"], 1373040)
        self.assertEqual(scope["net_new_scheduled_decryptions"], 1184400)
        self.assertEqual(scope["net_new_unique_passphrase_decryptions"], 1099440)
        selected = {
            row["source"]
            for row in report["coverage_rows"]
            if row["openssl_menu_gap"] == "selected for bounded run"
        }
        self.assertEqual(
            selected,
            set(excluded_wordlist_coverage_audit.MENU_GAP_FILES),
        )

    def test_curated_candidate_corpus_identity_and_provenance(self):
        base = curated_candidate_corpus_audit.build(False)
        seed = curated_candidate_corpus_audit.build(True)
        self.assertEqual(
            (base["candidate_count"], base["digest"]),
            (648, "2d233645ef49a141"),
        )
        self.assertEqual(
            (seed["candidate_count"], seed["digest"]),
            (650, "ab8252005a8388f5"),
        )
        self.assertEqual(base["active_source_lines"], 765)
        self.assertEqual(base["source_count"], 25)
        self.assertEqual(base["multi_source_candidate_count"], 94)
        self.assertEqual(base["cross_source_tier_candidate_count"], 64)
        self.assertEqual(
            base["first_source_tier_counts"],
            {"direct": 98, "bounded": 243, "thematic": 225, "mixed": 82},
        )
        # 29, not 26: macro_clue_permutation_combinations.txt (Phase 322) and
        # macro_clue_permutation_combinations_k8.txt (Phase 334) added
        # 2026-08-20 by a concurrent session, classified "dedicated-audit"
        # (both already swept separately via tools/gpu_oracle, both
        # rejected); phase382_1141_offset_candidates.txt (Phase 382) added
        # 2026-08-24, classified "dedicated-audit" (swept separately by
        # phase382_1141_offset_audit.py, rejected) -- none of these touches
        # the 648-candidate corpus itself.
        self.assertEqual(
            (base["included_wordlist_count"], base["excluded_wordlist_count"]),
            (23, 29),
        )
        self.assertEqual(base["oracle_overlap_groups"], 104)
        self.assertEqual(base["oracle_overlap_candidates"], 245)
        self.assertEqual(base["shared_generated_passphrases"], 1973)
        self.assertEqual(base["candidate_form_evaluations"], 17037)
        self.assertEqual(base["unique_generated_passphrases"], 14551)
        self.assertEqual(base["duplicate_generated_evaluations"], 2486)
        self.assertEqual(seed["candidate_form_evaluations"], 17073)
        self.assertEqual(seed["unique_generated_passphrases"], 14587)
        self.assertEqual(seed["duplicate_generated_evaluations"], 2486)
        oracle = next(
            row for row in base["source_rows"]
            if row["source"] == "oracle_coded.txt"
        )
        self.assertEqual(oracle["new_exact"], 0)
        validation = next(
            row for row in base["candidates"]
            if row["candidate"]
            == "INCASEYOUMANAGETOCRACKTHISTHEPRIVATEKEYSBELONGTOHALFANDBETTERHALFANDTHEYALSONEEDFUNDSTOLIVE"
        )
        self.assertEqual(validation["first_source_tier"], "mixed")
        self.assertEqual(validation["source_tiers"], ("mixed", "control"))
        self.assertEqual(seed["candidates"][-2]["candidate"], "SEED")
        self.assertEqual(seed["candidates"][-1]["candidate"], "IZLKESEEDQPPEN")

    def test_curated_candidate_registry_v2_classification(self):
        rep = curated_candidate_registry.report()
        self.assertEqual(rep["pool_count"], 1213)
        self.assertEqual(
            (rep["core_count"], rep["core_digest"]),
            (70, "5fb87296c1f04c2b"),
        )
        self.assertEqual(
            (rep["bounded_count"], rep["bounded_digest"]),
            (438, "62885ff021a92b07"),
        )
        self.assertEqual(
            (rep["full_count"], rep["full_digest"]),
            (508, "67e389aa7e6a63a9"),
        )
        self.assertEqual(rep["excluded_count"], 705)
        self.assertEqual(rep["full_candidate_form_evaluations"], 16056)
        self.assertEqual(rep["full_unique_generated_passphrases"], 14272)
        promo = rep["promotion_accounting"]
        self.assertEqual(promo["promoted_count"], 167)
        self.assertEqual(promo["demoted_count"], 34)
        self.assertEqual(promo["rejected_count"], 705)
        self.assertEqual(promo["retained_historical_only_count"], 278)
        self.assertEqual(
            promo["transitions"],
            {
                "bounded->bounded": 243,
                "bounded->core": 2,
                "core->bounded": 34,
                "core->core": 64,
                "excluded->bounded": 161,
                "excluded->core": 4,
                "excluded->excluded": 705,
            },
        )
        core_candidates = {e["candidate"] for e in rep["entries"] if e["class"] == "core"}
        self.assertIn("SEED", core_candidates)
        self.assertIn("IZLKESEEDQPPEN", core_candidates)
        # The historical 648/650-candidate corpus is never merged or mutated:
        # the two SEED leads and the 563 Phase-255 net-new candidates were
        # classified, not written into extended_cipher_recheck.CURATED_FILES.
        base = curated_candidate_corpus_audit.build(False)
        self.assertEqual((base["candidate_count"], base["digest"]), (648, "2d233645ef49a141"))

    def test_v2_bounded_promotion_backfill_scope_and_result(self):
        candidates = curated_v2_bounded_promotion_backfill.net_new_bounded_candidates()
        self.assertEqual(len(candidates), 136)
        self.assertEqual(
            curated_v2_bounded_promotion_backfill.candidate_list_digest(candidates),
            "8db6659bc547569a",
        )
        self.assertEqual(len(curated_v2_bounded_promotion_backfill.CBC_FAMILY_VARIANTS), 44)
        # Live sweep result, independently reproducible via --run: 6,327
        # evaluations x 44 CBC-family variants x 4 blobs = 1,113,552
        # decryptions, 0 hits. Not re-executed on every test run (~90s), same
        # convention as excluded_wordlist_coverage_audit's --menu-gap-sweep.

    @unittest.skipUnless(
        cosmic_duality_title_initials_yinyang_audit.DEFAULT_TITLE_PAGE.exists()
        and cosmic_duality_title_initials_yinyang_audit.DEFAULT_COVER.exists()
        and cosmic_duality_title_initials_yinyang_audit.DEFAULT_BODY_SAMPLE.exists(),
        "user's local book title-page/cover screenshots are unavailable",
    )
    def test_cosmic_duality_title_initials_yinyang(self):
        report = cosmic_duality_title_initials_yinyang_audit.analyze()
        self.assertEqual(
            report["title_page_sha256"],
            cosmic_duality_title_initials_yinyang_audit.EXPECTED_TITLE_PAGE_SHA256,
        )
        self.assertEqual(
            report["cover_sha256"],
            cosmic_duality_title_initials_yinyang_audit.EXPECTED_COVER_SHA256,
        )
        self.assertEqual(
            report["body_sample_sha256"],
            cosmic_duality_title_initials_yinyang_audit.EXPECTED_BODY_SAMPLE_SHA256,
        )
        self.assertGreater(report["body_sample_gold_pixel_count"], 0)
        self.assertTrue(report["design_is_book_wide_not_title_unique"])
        self.assertGreater(report["cosmic_word_gold_pixel_count"], 0)
        self.assertGreater(report["duality_word_gold_pixel_count"], 0)
        self.assertEqual(report["gold_outside_either_initial_count"], 0)
        self.assertEqual(report["cover_title_gold_pixel_count"], 0)
        self.assertEqual(report["roman_cd"], 400)
        self.assertEqual(report["roman_dc"], 600)
        self.assertEqual(report["hex_cd"], 205)
        self.assertEqual(report["ascii_sum_cd"], 135)
        self.assertEqual(report["a1z26_sum_cd"], 7)
        self.assertEqual(report["fitted_sums"], {"B": 401, "Y": 400, "F": 73})
        self.assertTrue(report["cd_matches_yellow_sum"])

    @unittest.skipUnless(
        cosmic_duality_chapter2_yin_lead_audit.DEFAULT_P48.exists()
        and cosmic_duality_chapter2_yin_lead_audit.DEFAULT_P50.exists()
        and cosmic_duality_chapter2_yin_lead_audit.DEFAULT_P55.exists(),
        "user's local book Chapter 2 page screenshots are unavailable",
    )
    def test_cosmic_duality_chapter2_yin_lead(self):
        report = cosmic_duality_chapter2_yin_lead_audit.analyze()
        self.assertEqual(report["sequence"], "YIN")
        for row in report["rows"]:
            self.assertGreater(row["gold_pixel_count"], 0)
            self.assertEqual(
                row["gold_pixel_count"],
                cosmic_duality_chapter2_yin_lead_audit.EXPECTED_GOLD_PIXELS[row["label"]],
            )

    def test_cosmic_duality_dropcap_inventory_no_yang_anywhere(self):
        cosmic_duality_dropcap_inventory.self_test()
        # Independent re-derivation (separately written, not calling the
        # module's own chapter_sequence/transform helpers) that the full
        # 39-entry inventory transforms to the reported per-chapter output
        # and that YANG does not appear anywhere in it.
        def a1z26(c):
            return ord(c) - ord("A") + 1

        def transform(page, letter):
            value = (page - a1z26(letter)) % 26
            return chr((value - 1 if value else 25) + ord("A"))

        by_chapter = {}
        for item in cosmic_duality_dropcap_inventory.DROP_CAPS:
            by_chapter.setdefault(item.chapter, []).append((item.page, item.letter))
        transformed = {
            chapter: "".join(transform(p, l) for p, l in rows)
            for chapter, rows in by_chapter.items()
        }
        self.assertEqual(
            transformed,
            {1: "VYVWXKALOH", 2: "YINJMNNJMV", 3: "GHSQYJVPL", 4: "THYRRWWQWV"},
        )
        full = "".join(transformed[c] for c in sorted(transformed))
        self.assertIn("YIN", full)
        self.assertNotIn("YANG", full)
        self.assertNotIn("YANG", full[::-1])
        # The three Chapter-2 entries this session photo-verified must match
        # the shared inventory exactly, or the two modules have drifted apart.
        ch2 = by_chapter[2][:3]
        self.assertEqual(ch2, [(48, "W"), (50, "O"), (55, "O")])

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists(),
        "sibling GSMG page mirror is unavailable",
    )
    def test_salphaseion_headings_and_metadata_have_no_hidden_channel(self):
        report = salphaseion_heading_metadata_audit.audit()
        self.assertEqual(report["title"], "GSMG Puzzle")
        self.assertEqual(report["meta_description"], ["GSMG Puzzle"])
        self.assertEqual(
            [heading["text"] for heading in report["headings"]],
            ["SalPhaseIon", "Cosmic Duality"],
        )
        self.assertTrue(
            all(not heading["attrs"] and not heading["nested_tags"]
                for heading in report["headings"])
        )
        self.assertEqual(
            report["class_attributes"],
            [{"tag": "html", "class": "no-js"}],
        )
        self.assertEqual(report["explicit_favicon_count"], 0)
        self.assertFalse(report["css_mentions_letter_spacing"])
        self.assertFalse(report["css_mentions_color"])

    @unittest.skipUnless(
        gameoflogic_source_audit.DEFAULT_OCR.exists(),
        "commit-pinned Game of Logic OCR is unavailable",
    )
    def test_gameoflogic_is_structural_recognition_not_a_puzzle_binding(self):
        report = gameoflogic_source_audit.audit()
        self.assertEqual(report["bytes"], 90139)
        self.assertFalse(any(report["puzzle_specific_counts"].values()))
        self.assertEqual(report["structural_counts"]["diagram"], 50)
        self.assertEqual(
            report["structural_counts"]["counter"]
            + report["structural_counts"]["counters"],
            37,
        )
        self.assertFalse(report["creator_selected"])
        self.assertTrue(report["recognition_only"])
        self.assertFalse(report["promoted"])

    def test_checkerboard_keyword_new_blob_gap_is_closed_without_promotion(self):
        report = checkerboard_keyword_blob_gap_audit.audit()
        scope = report["scope"]
        counts = report["counts"]
        self.assertEqual(
            tuple(scope["blobs"]),
            ("P32TRAILING", "URLBLOB"),
        )
        self.assertEqual(counts["candidates"], 12)
        self.assertEqual(counts["keyword_stream_tests"], 24)
        self.assertEqual(counts["decoder_configurations"], 2160)
        self.assertEqual(counts["valid_decodes"], 1776)
        self.assertEqual(counts["normalized_keystring_calls"], 14328)
        self.assertEqual(counts["primitive_blob_kdf_decryptions"], 171936)
        self.assertEqual(counts["strong_hits"], 0)
        self.assertEqual(counts["weak_records"], 0)
        self.assertTrue(
            report["gates"]["residual_checkerboard_keyword_gap_closed"]
        )
        self.assertFalse(report["gates"]["consumer_authenticated"])
        self.assertFalse(report["promoted"])

    @unittest.skipUnless(
        Path(DEFAULT_EXPORT_DIR, "result.json").exists(),
        "complete puzzle-solvers export is unavailable",
    )
    def test_bye_ciao_bridge_is_prior_but_not_creator_selected(self):
        report = bye_ciao_provenance_audit.audit()
        self.assertEqual(report["authenticated_tail"]["value"], "CIAO BELLA O")
        self.assertEqual(
            report["independent_prior"]["direct_bye_beauty_o_dbbi_faed_reply"],
            37921,
        )
        self.assertEqual(
            tuple(row["message_id"] for row in report["creator_ciao_inventory"]),
            (9632, 32773, 66609),
        )
        self.assertFalse(report["gates"]["creator_selected_ciao_as_yinyang"])
        self.assertFalse(report["gates"]["deterministic_bye_to_ciao_operation"])
        self.assertFalse(report["oracle_authorized"])

    @unittest.skipUnless(
        Path(DEFAULT_EXPORT_DIR, "result.json").exists()
        and ciao_selection_coverage_audit.SUPPORT_RESULT.exists(),
        "one or both pinned Telegram exports are unavailable",
    )
    def test_ciao_selection_coverage_finds_no_selection_and_closes_direct_password_gap(self):
        report = ciao_selection_coverage_audit.audit()
        self.assertFalse(
            report["two_corpus_creator_search"]["creator_selection_found"]
        )
        self.assertTrue(
            report["two_corpus_creator_search"][
                "support_corpus_adds_no_ciao_or_yinyang_mention"
            ]
        )
        self.assertTrue(report["coverage_census"]["ciaobellao"]["checkerboard_keyword_pad28"])
        self.assertFalse(report["coverage_census"]["ciao"]["checkerboard_keyword_pad28"])
        self.assertFalse(report["coverage_census"]["obellaciao"]["checkerboard_keyword_pad28"])
        self.assertEqual(report["bounded_direct_password_check"]["blob_count"], 4)
        self.assertEqual(report["bounded_direct_password_check"]["grand_total_hits"], 0)
        self.assertFalse(report["promoted"])

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
        Path(DEFAULT_EXPORT_DIR, "result.json").exists()
        and architect_passage_residual_audit.SUPPORT_RESULT.exists(),
        "one or both pinned Telegram exports are unavailable",
    )
    def test_architect_passage_residual_checks_stay_negative(self):
        report = architect_passage_residual_audit.audit()
        provenance = report["screenplay_provenance"]
        self.assertTrue(provenance["temporary"]["in_screenplay"])
        self.assertFalse(provenance["temporary"]["in_film_dialogue"])
        self.assertFalse(provenance["now_to_word_order"]["matches_screenplay"])
        self.assertTrue(provenance["now_to_word_order"]["matches_film"])
        self.assertFalse(
            report["creator_tone_search"]["passage_specific_commentary_found"]
        )
        self.assertTrue(
            report["coverage_census"]["keynote"]["checkerboard_keyword_dictionary_sweep"]
        )
        self.assertFalse(
            report["coverage_census"]["selfself"]["checkerboard_keyword_dictionary_sweep"]
        )
        self.assertEqual(report["bounded_direct_password_check"]["blob_count"], 4)
        self.assertEqual(report["bounded_direct_password_check"]["grand_total_hits"], 0)
        self.assertFalse(report["promoted"])

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

    def test_native_favicon_shadow_has_c9_to_ce_provenance_but_no_consumer(self):
        report = native_favicon_shadow_audit.audit()
        favicon = report["favicon"]
        self.assertEqual(favicon["visible_gray_bytes"], (201,))
        self.assertEqual(favicon["c9_visible_pixels"], 96)
        self.assertEqual(favicon["c9_opaque_pixels"], 0)
        self.assertEqual(
            report["composite"]["ce_source_pixels"],
            ((27, 26, (201, 201, 201, 224)),),
        )
        self.assertEqual(report["composite"]["reconstructed_ce_pixels"], 9)
        self.assertEqual(report["logo_glyph_control"]["g_only_rgba_layers"], 42)
        self.assertFalse(report["gates"]["logo_g_checksum_distinctive"])
        self.assertFalse(report["gates"]["alpha_or_lsb_consumer_selected"])
        self.assertFalse(report["promoted"])

    def test_svg_geometry_accounts_for_all_native_c9_pixels(self):
        report = svg_png_edge_geometry_audit.audit()
        native = report["native_48"]
        self.assertGreater(native["body_registration"]["binary_iou"], 0.971)
        self.assertEqual(native["c9_pixels"], 96)
        self.assertEqual(native["c9_adjacent_non_c9_4_neighbor"], 96)
        self.assertEqual(native["c9_adjacent_opaque_8_neighbor"], 96)
        self.assertLess(
            native["c9_max_svg_segment_distance"],
            native["ordinary_edge_max_svg_segment_distance"],
        )
        self.assertEqual(native["c9_within_ordinary_edge_envelope"], 96)
        self.assertEqual(native["c9_residue"], ())
        self.assertEqual(native["nearest_svg_path_counts"], ((0, 85), (1, 11)))
        self.assertFalse(report["gates"]["off_contour_c9_residue_found"])
        self.assertFalse(report["gates"]["decode_or_oracle_authorized"])
        self.assertFalse(report["promoted"])

    def test_shadow_macro_nesting_does_not_select_faed_width_38(self):
        report = shadow_macro_faed_geometry_audit.audit(trials=200, seed=240)
        numeric = report["numeric"]
        geometry = report["geometry"]
        self.assertEqual(numeric["shadow_measurement_span_hits"], (18, 38, 43, 56))
        self.assertEqual(numeric["permutations_with_at_least_four_hits"], 8)
        self.assertEqual(len(numeric["exact_unlabeled_nested_permutations"]), 2)
        self.assertEqual(numeric["extended_pool"]["hits"], 44)
        self.assertEqual(len(numeric["factor_pairs_570"]), 8)
        self.assertEqual(numeric["faed_token_divisors"], (("enter", 5, 114),))
        self.assertEqual(geometry["family_size_per_null"], 64)
        self.assertFalse(geometry["width_38_exceptional"])
        self.assertFalse(geometry["any_family_corrected_hit"])
        self.assertFalse(report["gates"]["decode_or_oracle_authorized"])
        self.assertFalse(report["promoted"])

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

    def test_first_piece_marker_numeric_control(self):
        report = first_piece_marker_numeric_control_audit.audit()
        fefe = report["markers"]["FEFE_CHANNEL"]
        shadow = report["markers"]["SHADOW_CHANNEL"]
        self.assertEqual(report["legacy_registry_size"], 20)
        self.assertEqual(report["extended_registry_size"], 22)
        self.assertEqual(fefe["deduplicated_relation_count"], 1)
        self.assertEqual(fefe["byte_family_tail_count"], 147)
        self.assertEqual(shadow["deduplicated_relation_count"], 2)
        self.assertEqual(shadow["byte_family_tail_count"], 70)
        self.assertFalse(report["promoted"])
        self.assertFalse(report["oracle_run"])

    def test_first_piece_native_matrixsumlist(self):
        report = first_piece_native_matrixsumlist_audit.audit()
        self.assertEqual(
            report["row_sums"],
            (6, 10, 8, 7, 6, 6, 5, 4, 9, 9, 7, 8, 7, 9),
        )
        self.assertEqual(
            report["column_sums"],
            (8, 10, 8, 10, 8, 7, 3, 6, 7, 5, 9, 6, 6, 8),
        )
        self.assertEqual(report["total"], 101)
        self.assertEqual(report["row_a1z26"], "FJHGFFEDIIGHGI")
        self.assertEqual(report["column_a1z26"], "HJHJHGCFGEIFFH")
        self.assertEqual(report["d4_orientation_count"], 8)
        self.assertEqual(report["d4_unique_list_count"], 4)
        self.assertFalse(report["consumer_selected"])
        self.assertFalse(report["oracle_run"])

    def test_first_piece_g_operator_gate(self):
        report = first_piece_g_operator_gate_audit.audit()
        banner, address = report["rails"]
        self.assertEqual(banner["operand_after_removing_G"], "SO5BCPUC")
        self.assertEqual(address["operand_after_removing_G"], "MC9g2cPBe")
        self.assertFalse(banner["whole_operand_is_decimal"])
        self.assertFalse(address["whole_operand_is_decimal"])
        self.assertEqual(report["combined_stride_output_count"], 64)
        self.assertEqual(report["combined_stride_term_hits"], ())
        self.assertFalse(report["all_G_anchors_have_numeric_neighbor"])
        self.assertEqual(tuple(report["scalar_addresses"]), (2, 4))
        self.assertFalse(report["any_scalar_address_match"])
        self.assertFalse(report["curve_semantics_selected"])
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

    # 2026-08-22 hub-phase code-vs-premise review: Phase 112's own self_test()
    # covers the code_ic()/segment_codes() mechanism directly (not exercised
    # by the two hand-written tests above) but was never wired in.
    def test_checkerboard_code_ic_oracle_mechanism(self):
        checkerboard_code_ic_oracle.self_test()

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
        Path(DEFAULT_HTML).exists()
        and (Path(DEFAULT_EXPORT_DIR) / "result.json").exists(),
        "page mirror or Telegram export is unavailable",
    )
    def test_page_syntax_has_no_uniform_house_style(self):
        report = page_syntax_house_style_audit.audit()
        self.assertEqual(report["rules_tested"], 6)
        self.assertEqual(report["rules_surviving"], ())
        self.assertTrue(report["roles"]["enter"]["local_page_direction_fixed"])
        self.assertFalse(
            report["roles"]["matrixsumlist"]["local_page_direction_fixed"]
        )
        self.assertEqual(
            report["phase101_model_family"]["conditional_model_b_projection"],
            18,
        )
        self.assertEqual(
            report["phase101_model_family"][
                "conditionally_total_only_with_answer_too"
            ],
            9,
        )
        self.assertFalse(
            report["phase101_model_family"]["projection_is_creator_authenticated"]
        )
        self.assertFalse(
            report["gates"]["empirical_uniform_house_style_found"]
        )
        self.assertFalse(report["gates"]["new_transform_or_oracle_authorized"])

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
        (Path(DEFAULT_EXPORT_DIR) / "result.json").exists(),
        "Telegram export is unavailable",
    )
    def test_macro_model_disposition_changes_without_decoder_promotion(self):
        report = macro_model_disposition_audit.audit(
            Path(DEFAULT_EXPORT_DIR) / "result.json"
        )
        comparison = report["model_comparison"]
        self.assertEqual(
            comparison["models"]["A_selected_31_operand"]["completed_macro_edges"],
            1,
        )
        self.assertEqual(
            comparison["models"]["B_six_digit_prime"]["completed_macro_edges"],
            3,
        )
        self.assertEqual(
            comparison["selected_31_disposition"],
            "structural checkpoint; parked",
        )
        self.assertFalse(comparison["selected_31_recognition_promoted"])

        both = report["both_endpoint_control"]
        self.assertEqual(
            both["clause_polarity"],
            "affirmative, not negated or conditional",
        )
        self.assertEqual(
            both["first_word_counts"],
            {"beginning": 16, "both": 16, "brings": 16},
        )
        self.assertEqual(both["first_words_with_mirror9_endpoints"], ("both",))
        self.assertEqual(both["partial_mirror_bye_rows"], 5)
        self.assertEqual(both["mixed_edge_bye_rows"], 15)

        roles = report["output_role_inventory"]
        self.assertEqual(roles["pure_terminal_recognition_word_precedents"], ())
        self.assertFalse(roles["bingo_control"]["comparable_to_bye"])
        self.assertTrue(
            roles["bingo_control"]["present_in_tier1_candidate_corpus"]
        )

        dbbi_case, faed_case = report["mirror_orbit_table"]["cases"]
        self.assertEqual(dbbi_case["mirror_pair_results"]["faed"]["rank"], 16)
        self.assertEqual(faed_case["mirror_pair_results"]["dbbi"]["rank"], 24)
        self.assertIsNone(faed_case["mirror_pair_results"]["faed"])
        self.assertFalse(report["promotion"]["new_decoder_or_oracle_authorized"])

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

    def test_vault_frontmatter_matches_controlled_vocabulary(self):
        report = validate_vault_metadata.run()
        self.assertGreaterEqual(report["checked"], 15)
        self.assertEqual(report["errors"], {})

    def test_duplicate_phase_numbers_have_explicit_stable_ids(self):
        text = generate_phase_index.FINDINGS.read_text(encoding="utf-8")
        rows = generate_phase_index.parse_phases(text)
        rows = generate_phase_index.assign_stable_ids(rows)  # raises if unstable
        stable_ids = [row["stable_id"] for row in rows]
        self.assertEqual(len(stable_ids), len(set(stable_ids)))
        duplicated_numbers = {"8", "19"}
        marked = {
            row["number"] for row in rows
            if row["number"] in duplicated_numbers and row["explicit_id"]
        }
        self.assertEqual(marked, duplicated_numbers)

    def test_phase_index_heading_split_ignores_colon_inside_inline_code(self):
        # Phase 396's real heading contains `decoded[7:98]` -- a colon with
        # no following space, inside inline code, before the real "subject:
        # result" separator. A bare-colon partition() would split there
        # instead, producing a malformed subject/result pair.
        heading = (
            "## Phase 999 -- header-aware `P91 = decoded[7:98]` block: "
            "confirmed real, no signal, closed negative (2026-08-25)"
        )
        rows = generate_phase_index.parse_phases(heading)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["subject"], "header-aware `P91 = decoded[7:98]` block")
        self.assertEqual(row["result"], "confirmed real, no signal, closed negative")
        self.assertNotIn("[7 ", row["subject"])
        self.assertNotIn("| 98", row["subject"] + row["result"])

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

    def test_urlscan_captures_add_no_new_page_variant(self):
        scans = salphaseion_urlscan_history_audit.SCANS
        successful = [scan for scan in scans if scan[2] == 200]
        self.assertEqual(len(scans), 12)
        self.assertEqual(len(successful), 11)
        self.assertEqual(
            {scan[3] for scan in successful},
            {
                salphaseion_wayback_history_audit.CAPTURES[0]["sha256"],
                salphaseion_wayback_history_audit.CAPTURES[1]["sha256"],
                salphaseion_wayback_history_audit.CAPTURES[2]["sha256"],
            },
        )
        self.assertEqual(scans[-1][2:], (503, None))

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists(),
        "sibling GSMG page mirror is unavailable",
    )
    def test_dbbi_faed_boundary_selectors_exhausted(self):
        checks = dbbi_faed_boundary_selector_audit.audit()
        self.assertEqual(checks["css_selector_count"], 1)
        self.assertFalse(checks["css_has_textarea_specific_rule"])
        self.assertTrue(checks["textarea_attrs_identical"])
        self.assertTrue(checks["single_script_tag"])
        self.assertTrue(checks["script_is_external_analytics_beacon"])
        self.assertFalse(checks["script_references_textarea"])
        self.assertEqual(checks["comment_count"], 0)
        self.assertTrue(checks["dbbi_faed_share_one_textarea"])
        self.assertTrue(checks["whitespace_is_single_character_separation"])
        self.assertEqual(checks["known_captures"], 5)
        self.assertFalse(checks["pre_registered_condition_met"])

    @unittest.skipUnless(
        Path(DEFAULT_EXPORT_DIR, "result.json").exists()
        and Path(
            creator_personal_disclosures_audit.SUPPORT_EXPORT_DIR, "result.json"
        ).exists(),
        "both Telegram exports are unavailable",
    )
    def test_creator_personal_disclosures_verified_against_raw_export(self):
        report = creator_personal_disclosures_audit.audit()
        self.assertEqual(len(report["substance"]), 7)
        self.assertEqual(len(report["dutch_location"]), 20)
        for message_id, result in report["substance"].items():
            self.assertTrue(result["found"], (message_id, result))
        for message_id, result in report["dutch_location"].items():
            self.assertTrue(result["found"], (message_id, result))

    @unittest.skipUnless(
        Path(DEFAULT_EXPORT_DIR, "result.json").exists()
        and Path(
            creator_personal_disclosures_audit.SUPPORT_EXPORT_DIR, "result.json"
        ).exists()
        and Path(
            architect_mirror_selector_audit.SOLVER_RECENT_EXPORT_DIR, "result.json"
        ).exists(),
        "not all three Telegram exports are available",
    )
    def test_architect_mirror_selector_lanes_are_negative(self):
        report = architect_mirror_selector_audit.audit()
        coverage = report["newer_export_coverage"]
        self.assertEqual(coverage["new_message_count"], 952)
        self.assertEqual(coverage["creator_new_count"], 0)
        self.assertEqual(
            report["targeted_keyword_sweep"],
            {"solver": 3, "support": 24, "solver_recent": 0},
        )
        self.assertEqual(
            report["hye_word"], {"solver": 0, "support": 1, "solver_recent": 0}
        )
        candidates = report["architect_selector_candidates"]
        self.assertEqual(candidates["solver"]["hit_count"], 13)
        self.assertEqual(candidates["solver"]["creator_authored_count"], 0)
        self.assertEqual(candidates["solver"]["creator_reply_pairs"], [])
        self.assertEqual(candidates["support"]["hit_count"], 0)
        visual = report["visual_media_inventory"]
        self.assertEqual(visual["total_records"], 88)
        self.assertEqual(visual["unique_payloads"], 83)
        self.assertEqual(visual["visual_selector_ids"], ())
        precedent = report["precedent_transfer"]
        self.assertEqual(precedent["solver"]["direct_transfer_ids"], ())
        self.assertEqual(precedent["support"]["direct_transfer_ids"], ())

    @unittest.skipUnless(
        Path(DEFAULT_EXPORT_DIR, "result.json").exists()
        and Path(
            telegram_creator_media_completeness_audit.DEFAULT_SUPPORT, "result.json"
        ).exists(),
        "both Telegram exports are unavailable",
    )
    def test_creator_media_completeness(self):
        telegram_creator_media_completeness_audit.self_test()

    def test_favicon_wayback_authenticates_bytes_but_not_pre_puzzle_origin(self):
        report = favicon_wayback_chronology_audit.audit()
        self.assertEqual(report["archive"]["exact_200_png_capture_count"], 1)
        self.assertEqual(report["archive"]["distinct_cdx_digests"], 1)
        self.assertEqual(report["chronology"]["days_after_launch"], 8)
        self.assertFalse(report["chronology"]["predates_puzzle"])
        self.assertFalse(report["chronology"]["version_comparison_possible"])
        self.assertEqual(report["c9_properties"]["visible_gray_bytes"], (201,))
        self.assertEqual(report["c9_properties"]["c9_visible_pixels"], 96)
        self.assertTrue(
            report["gates"]["repository_copy_authenticated_to_2019_04_28"]
        )
        self.assertFalse(
            report["gates"]["pre_puzzle_branding_provenance_established"]
        )
        self.assertFalse(report["promoted"])

    # 2026-08-22 hub-phase code-vs-premise review: these five scripts (Phases
    # 46, 48, 52, 62, 64) each already had their own internal self_test(),
    # but none was wired into this suite, so none was actually re-verified by
    # routine `python3 test_recent_audits.py` runs. Three of them
    # (flo_prime_walk_provenance_audit, transition_evidence_recovery_audit,
    # telegram_backend_comparison_audit) also require the raw, never-committed
    # `_work/chat_transcript.txt` export (see doc/GSMG_PUZZLE.md), which is
    # not present in every checkout -- skipped, not silently absent, when
    # it's missing, matching this file's existing external-fixture pattern.

    def test_denis_prime_extraction_masks_reproduce(self):
        denis_prime_extraction_audit.self_test()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 46's headline
    # calibration numbers (the four exact uniform-subset base rates) are
    # computed in main() but never asserted anywhere, including self_test().
    def test_denis_prime_extraction_exact_base_rates(self):
        m = denis_prime_extraction_audit
        _, _, yang31 = m.exact_subset_rate(m.SOURCE, 31, "yang")
        _, _, yang30 = m.exact_subset_rate(m.SOURCE, 30, "yang")
        _, _, ying31 = m.exact_subset_rate(m.SOURCE, 31, "ying")
        _, _, ying30 = m.exact_subset_rate(m.SOURCE, 30, "ying")
        self.assertAlmostEqual(yang31, 0.002579127, places=9)
        self.assertAlmostEqual(yang30, 0.002403975, places=9)
        self.assertAlmostEqual(ying31 / 2.323839e-10, 1.0, places=6)
        self.assertAlmostEqual(ying30 / 4.938532e-10, 1.0, places=6)

    @unittest.skipUnless(
        flo_prime_walk_provenance_audit.DEFAULT_CHAT.exists(),
        "raw chat_transcript.txt export is unavailable",
    )
    def test_flo_prime_walk_reproduces_denis_mask_and_fefe_insertion(self):
        flo_prime_walk_provenance_audit.self_test()

    @unittest.skipUnless(
        transition_evidence_recovery_audit.DEFAULT_CHAT.exists()
        and transition_evidence_recovery_audit.DEFAULT_CREATOR.exists()
        and transition_evidence_recovery_audit.DEFAULT_PARSER.exists(),
        "raw chat_transcript.txt/creator_jrk.txt/parse_chat.py archive is unavailable",
    )
    def test_transition_evidence_no_archived_post_selection_operator(self):
        transition_evidence_recovery_audit.self_test()

    @unittest.skipUnless(
        telegram_backend_comparison_audit.DEFAULT_OLD_TRANSCRIPT.exists(),
        "raw chat_transcript.txt export is unavailable",
    )
    def test_telegram_backend_old_transcript_matches_complete_export(self):
        telegram_backend_comparison_audit.self_test()

    def test_rabbit_hole_nest_matches_fefe_and_leftover_spiral_cells(self):
        rabbit_hole_nest_audit.self_test()

    # 2026-08-22 hub-phase code-vs-premise review, continued: these two
    # scripts (Phases 33/36) had real assertion-driven logic but no
    # self_test()/audit() split -- everything lived in an argparse-parsing
    # main(), so it could only ever be checked by remembering to run the
    # script by hand. Refactored to the project's usual audit()/self_test()
    # split (behavior-preserving; `main()`'s printed output is unchanged)
    # and wired in here.

    def test_prime_matrixsum_reconstruction_reproduces_but_hye_eol(self):
        prime_matrixsum_reconstruction.self_test()

    def test_first_piece_full_mask_audit_reproduces_prime_and_pvalue(self):
        first_piece_full_mask_audit.self_test()

    # 2026-08-22: Phase 2 (the project's first dictionary-scale sweep) had no
    # self-test at all, and 3 of its 5 default wordlist sources (cypherpunk/
    # bitcoin-historical/gutenberg) are large external corpora not committed
    # to this repo, so its real 338,905-candidate/677,810-keyword-test sweep
    # cannot be reproduced here. Added a synthetic self-test that verifies
    # the sweep mechanism itself (wordlist dedup, missing-file resilience,
    # and -- the part that actually matters for trusting "0 hits" -- a
    # planted end-to-end hit through the exact same pad28/decode/answer-
    # form/keystring/AES-oracle chain every real candidate goes through).

    def test_cosmic_sweep_mechanism_and_planted_hit(self):
        cosmic_sweep.self_test()

    @unittest.skipUnless(
        flo_prime_walk_provenance_audit.DEFAULT_CHAT.exists(),
        "raw chat_transcript.txt export is unavailable",
    )
    def test_matrixsumlist_31_feasibility_no_unique_operation(self):
        matrixsumlist_31_feasibility_audit.self_test()

    # 2026-08-22 hub-phase review: while checking Phase 64, found that Phase
    # 127's cell-classifier fix corrected Phases 64/65/125/126's numbers but
    # that correction was never propagated back into their own FINDINGS.md
    # text (fixed separately). These three scripts had working self-tests
    # that were simply never wired into this suite.

    def test_black_rabbit_negative_space_corrected_counts(self):
        black_rabbit_negative_space_audit.self_test()

    def test_black_rabbit_drawn_overlay_no_unique_orientation(self):
        black_rabbit_drawn_overlay_audit.self_test()

    @unittest.skipUnless(
        flo_prime_walk_provenance_audit.DEFAULT_CHAT.exists(),
        "raw chat_transcript.txt export is unavailable",
    )
    def test_rabbit_nest_nibble_is_trivial_all_zero(self):
        rabbit_nest_nibble_audit.self_test()

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists()
        and (Path(DEFAULT_EXPORT_DIR) / "result.json").exists(),
        "sibling GSMG page mirror or Telegram export is unavailable",
    )
    def test_salphaseion_aphelion_subanagram_base_rate_downgrade(self):
        salphaseion_aphelion_anagram_audit.self_test()
        report = salphaseion_aphelion_anagram_audit.audit(
            DEFAULT_HTML, Path(DEFAULT_EXPORT_DIR) / "result.json"
        )
        self.assertEqual(len(report["base_rate"]["all_sub_anagrams"]), 457)
        self.assertEqual(
            report["base_rate"]["same_length_as_target"],
            [
                "Alphonse", "aphelion", "epsilons", "holiness", "painless",
                "pinholes", "polishes", "seasonal", "spaniels",
            ],
        )
        self.assertEqual(report["corpus_mentions"], {"APHELION": [], "PERIHELION": []})
        blobs = dict(BLOBS, **QUARANTINED_BLOBS)
        result = salphaseion_aphelion_anagram_audit.oracle_check(
            report["candidates"], blobs
        )
        self.assertEqual(result["unique_keystrings"], 126)
        self.assertEqual(result["blob_count"], 4)
        self.assertEqual(sum(len(v) for v in result["hits"].values()), 0)

    # 2026-08-22 hub-phase code-vs-premise review: Phase 53's two scripts
    # were never wired into the suite despite passing self-tests. The guide
    # audit depends on a real Telegram Desktop JSON export under a fixed
    # absolute path outside the repo (same external-corpus pattern as
    # chat_transcript.txt), so it is skip-guarded; the FEFE sweep only
    # depends on the committed first-piece image plus a constant imported
    # from the guide module, so it runs unconditionally.
    @unittest.skipUnless(
        telegram_yellow_blue_guide_audit.DEFAULT_EXPORT.exists(),
        "raw Telegram Desktop JSON export is unavailable",
    )
    def test_telegram_yellow_blue_guide_reproduces_izlkeseedqppen(self):
        telegram_yellow_blue_guide_audit.self_test()

    def test_telegram_yellow_blue_fefe_sweep_reproduces_three_policy_outputs(self):
        telegram_yellow_blue_fefe_sweep.self_test()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 78's binary-key-
    # material oracle and Phase 84-87's -nopad window sweep both have
    # thorough, fast, all-synthetic self-tests (temp-dir I/O only, mocked
    # network calls) but were never wired into the suite.
    def test_binary_key_material_backfill_synthetic_hit_and_api_mocking(self):
        binary_key_material_backfill.self_test()

    def test_nopad_window_sweep_reproduces_full_self_test_suite(self):
        nopad_window_sweep.self_test()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 88's Fresco
    # wordlist oracle-wiring self-test was never wired into the suite.
    def test_jacque_fresco_wordlist_audit_oracle_family_wiring(self):
        jacque_fresco_wordlist_audit.self_test()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 38's
    # thread_convergence_audit.py has no self_test()/audit() split -- its
    # main() itself hard-asserts every claim (FEFE coordinate/spiral-index
    # convergence, exact 12/9/1-of-172 null counts) and takes no CLI args,
    # so it is safe to call directly as a regression guard.
    def test_thread_convergence_audit_reproduces_fefe_convergence_and_null(self):
        thread_convergence_audit.main()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 4's
    # door_prime_passport_probe.py has no self_test()/audit() split, but its
    # two probe functions take no args, run against the real production AES
    # oracle deterministically, and only print instead of asserting -- so
    # this test asserts the exact reported counts and 0-hit result directly.
    def test_door_prime_passport_probe_reproduces_zero_hits(self):
        direct_hits = door_prime_passport_probe.probe_direct_passphrases()
        self.assertEqual(direct_hits, [])
        self.assertEqual(len(door_prime_passport_probe.CANDIDATES), 31)
        zero_hits = door_prime_passport_probe.probe_prime_zeroing()
        self.assertEqual(zero_hits, [])

    # 2026-08-22 hub-phase code-vs-premise review: Phase 22's two scripts
    # (extended cipher/KDF coverage recheck, staged SALPH->COSMIC pipeline)
    # both have --self-test flags that were never wired into the suite.
    def test_extended_cipher_recheck_curated_corpus_and_sweep_mechanism(self):
        extended_cipher_recheck.self_test()

    def test_staged_pipeline_synthetic_salph_to_cosmic_chain(self):
        staged_pipeline._self_test()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 43's FAED
    # ciphertext-only hill-climb sweep has a fast standalone self_test()
    # (tiny iters/restarts) that was never wired into the suite.
    def test_faed_monoalphabetic_sweep_code_counts_and_variant_coverage(self):
        faed_monoalphabetic_sweep.self_test()

    def test_faed_token_null_check_shuffle_gate_and_checkpoint_guards(self):
        faed_token_null_check.self_test()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 7's read-through
    # cites two decode chains (the macro-clue rebus, the Caesar/base64/
    # Rick-Roll message) as later hard-asserted by these two scripts'
    # self-tests, but neither was ever wired into the suite.
    def test_salphaseion_title_rebus_audit_reproduces_fixed_candidates(self):
        salphaseion_title_rebus_audit.self_test()

    def test_first_puzzle_announcement_audit_caesar_and_base64_chain(self):
        first_puzzle_announcement_audit.self_test()

    @unittest.skipUnless(
        first_puzzle_announcement_audit.DEFAULT_EXPORT.exists(),
        "raw Telegram Desktop JSON export is unavailable",
    )
    def test_first_puzzle_announcement_audit_full_reconstruction_zero_hits(self):
        message, binary_text = first_puzzle_announcement_audit.extract_forwarded_payload(
            first_puzzle_announcement_audit.DEFAULT_EXPORT
        )
        materials = first_puzzle_announcement_audit.reconstruct(binary_text)
        totals = first_puzzle_announcement_audit.audit(materials)
        self.assertEqual(
            totals, {"address": 0, "cbc": 0, "wrap": 0, "raw_key": 0}
        )

    # 2026-08-22 hub-phase code-vs-premise review: Phase 98's creator-corpus
    # base-rate audit (313/1,312 element-parsable word types, 107/313 sum-16
    # spans, 6/313 exact P,H spans, only "salphation" surviving PH->V) lives
    # in creator_element_base_rate(), reachable only through the real audit()
    # call (needs the archived HTML heading, the Telegram export, and the
    # screenplay PDF) -- self_test() alone never exercises it.
    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists()
        and (Path(DEFAULT_EXPORT_DIR) / "result.json").exists()
        and prime_matrixsum_reconstruction.PDF_PATH.exists(),
        "sibling GSMG page mirror, Telegram export, or screenplay PDF is unavailable",
    )
    def test_salphaseion_title_rebus_audit_creator_corpus_base_rate(self):
        report = salphaseion_title_rebus_audit.audit(
            DEFAULT_HTML,
            Path(DEFAULT_EXPORT_DIR) / "result.json",
            prime_matrixsum_reconstruction.PDF_PATH,
        )
        profile = report["elemental_base_rate"]["profiles"]["all_lengths"]
        self.assertEqual(report["elemental_base_rate"]["creator_message_count"], 482)
        self.assertEqual(report["elemental_base_rate"]["creator_word_types"], 1312)
        self.assertEqual(profile["element_parsable_word_types"], 313)
        self.assertEqual(profile["sum16_span_word_types"], 107)
        self.assertEqual(profile["ph_span_word_types"], 6)
        self.assertEqual(profile["ph_to_salvation_words"], ("salphation",))

    # 2026-08-22 hub-phase code-vs-premise review: Phase 127's cell-classifier
    # fix (single center-pixel sample vs. majority-color-across-the-cell) is
    # the root fix that everything downstream (Phases 64/65/125/126/128, and
    # the validated 192-cell gsmg.io/theseedisplanted decode itself) silently
    # depends on, but neither first_piece_color_reconstruction.py nor
    # grid_spiral.py -- the two places load_grid() was fixed -- was ever
    # itself imported or tested by this suite. reconstruct()/decode() both
    # hard-assert every claim internally (color sequence, rose-hex, prime,
    # FEFE 1/4/21 descriptor), so calling them directly is a real regression
    # guard, not just a smoke test. Also directly pins the exact bug: cell
    # (row 8, column 7, 1-indexed) must classify as white, not black.
    def test_first_piece_color_reconstruction_load_grid_majority_fix(self):
        grid = first_piece_color_reconstruction.load_grid(
            first_piece_color_reconstruction.DEFAULT_IMAGE
        )
        self.assertEqual(grid[7][6], first_piece_color_reconstruction.WHITE)
        result = first_piece_color_reconstruction.reconstruct(
            first_piece_color_reconstruction.DEFAULT_IMAGE
        )
        self.assertEqual(
            result["color_sequence"],
            first_piece_color_reconstruction.EXPECTED_COLOR_SEQUENCE,
        )
        self.assertEqual(
            result["rose_hex"], first_piece_color_reconstruction.EXPECTED_ROSE_HEX
        )
        self.assertEqual(
            result["prime_value"], first_piece_color_reconstruction.EXPECTED_PRIME
        )
        self.assertEqual(
            (result["fefe"]["bit_1"], result["fefe"]["character_1"]), (4, 21)
        )

    @unittest.skipUnless(
        grid_spiral.DEFAULT_IMG_PATH.exists(),
        "sibling gsmg-site-mirror checkout is unavailable",
    )
    def test_grid_spiral_load_grid_majority_fix_and_decode(self):
        grid = grid_spiral.load_grid()
        self.assertEqual(grid[7][6], grid_spiral.WHITE)
        _grid, _coords, _bits, chars = grid_spiral.decode()
        self.assertEqual(chars, grid_spiral.TARGET)

    # 2026-08-22 hub-phase code-vs-premise review: Phase 336's two-half
    # combine-algebra detector has a real self-test (15 combine forms, 9
    # independently re-derived EC known-target constants, an end-to-end
    # planted xor-combine hit, wrong-password control) but was never wired
    # into this suite. Slow-ish (~16s, live secp256k1 point arithmetic) but
    # well within this suite's existing budget.
    def test_half_better_half_algebra_audit_combine_forms_and_planted_hit(self):
        half_better_half_algebra_audit.self_test()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 296 (the single
    # highest in-degree phase in the whole citation graph) has a real
    # self-test pinning the finder-square relocation, the 5/7 exact-row
    # match count, the multi-valued-row falsification, and JPEG-origin
    # invariance -- all against the committed doc/img/gsmg_puzzle_stage1.png
    # asset (no external dependency) -- but it was never wired into the suite.
    def test_qr_finder_ring_texture_reindex_dither_audit(self):
        qr_finder_ring_texture_reindex_dither_audit.self_test()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 298's real free-
    # generator comparison has a self-test pinning all three saved images'
    # analysis (qrserver/quickchart pure B/W, qrcode-monkey's 528 eyes-
    # confined gray pixels) but was never wired into the suite.
    def test_qr_finder_ring_texture_generator_comparison_audit(self):
        qr_finder_ring_texture_generator_comparison_audit.self_test()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 305's irregular-
    # rows-in-isolation audit has a self-test pinning the 6-differing-bit
    # premise and the exact 8-candidate/24-attempt count but was never wired
    # into the suite.
    def test_qr_finder_ring_texture_irregular_rows_only_audit(self):
        qr_finder_ring_texture_irregular_rows_only_audit.self_test()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 327's key-shape
    # classifier (hex64/WIF/BIP39) and its sweep driver both have real,
    # fully-synthetic self-tests (no external dependency, no real network
    # calls) but neither was ever wired into the suite.
    def test_key_shape_classifier_hex64_wif_bip39_and_base58check(self):
        key_shape_classifier.self_test()

    def test_key_shape_sweep_synthetic_wif_hit_reaches_bloom_and_queue(self):
        key_shape_sweep.self_test()

    # 2026-08-22 in-degree-2 tier code-vs-premise review: batch of scripts
    # whose audit()/self_test() already hard-asserts every claim in its own
    # FINDINGS phase but was never wired into this suite. Verified each
    # individually before trusting it.
    def test_fefe_zero_operation_audit_reproduces_fe_plated_rebus(self):
        fefe_zero_operation_audit.audit(fefe_zero_operation_audit.DEFAULT_IMAGE)

    def test_telegram_export_keyword_sweep_mechanism(self):
        telegram_export_keyword_sweep.self_test()

    def test_small_number_coincidence_calibration_base_rate(self):
        small_number_coincidence_calibration.self_test()

    def test_phase1_icon_rebus_audit_reproduces_warning_logic(self):
        phase1_icon_rebus_audit.self_test()

    def test_stage0_png_filter_anomaly_audit_reproduces_row_1416(self):
        stage0_png_filter_anomaly_audit.self_test()

    def test_external_archive_lead_audit(self):
        external_archive_lead_audit.audit()

    @unittest.skipUnless(
        Path(DEFAULT_HTML).exists(),
        "sibling GSMG page mirror is unavailable",
    )
    def test_salphaseion_operand_binding_audit(self):
        salphaseion_operand_binding_audit.self_test()

    # matrixsumlist_color_prime_audit.py's audit() calls
    # flo_prime_walk_provenance_audit.audit() with its default chat_path,
    # so it inherits the same raw chat_transcript.txt dependency.
    @unittest.skipUnless(
        flo_prime_walk_provenance_audit.DEFAULT_CHAT.exists(),
        "raw chat_transcript.txt export is unavailable",
    )
    def test_matrixsumlist_color_prime_audit_reproduces_fitted_sums(self):
        matrixsumlist_color_prime_audit.self_test()

    def test_matrixsumlist_self_fold_consumer_audit(self):
        matrixsumlist_self_fold_consumer_audit.self_test()

    def test_image_stego_metadata_audit(self):
        image_stego_metadata_audit.self_test()

    def test_dbbi_faed_cosmic_duality_running_key_audit(self):
        dbbi_faed_cosmic_duality_running_key_audit.self_test()

    def test_genesis_adjacent_fields_audit_reproduces_eight_candidates(self):
        genesis_adjacent_fields_audit.self_test()

    def test_embedded_key_format_scanner_audit(self):
        embedded_key_format_scanner_audit.self_test()

    def test_bip32_authenticated_number_paths_audit(self):
        bip32_authenticated_number_paths_audit.self_test()

    def test_typed_decode_parse_ladder_audit(self):
        typed_decode_parse_ladder_audit.self_test()

    def test_qr_fafafa_braille_audit(self):
        qr_fafafa_braille_audit.self_test()

    def test_qr_fafafa_six_variant_atlas_audit(self):
        qr_fafafa_six_variant_atlas_audit.self_test()

    # 2026-08-22 in-degree-2 tier: Phase 79's two bookkeeping oracles.
    # aes_key_wrap_sweep.py has a real synthetic _self_test() (leading-
    # underscore convention, already safe to call directly). legacy_cbc_
    # backfill.py has no self-test but its real sweep against the full
    # curated corpus is cheap (~2s, only 6 legacy KDF variants, no PBKDF2),
    # so it's called directly and its exact FINDINGS numbers pinned.
    # stream_mode_cipher_sweep.py's real sweep is NOT reproduced here (its
    # 36 variants include 10,000-iteration PBKDF2, making the real
    # 2,095,344-op run too slow for a regression test) -- only its existing
    # checkpoint/fingerprint-mechanism self_test() is wired.
    def test_aes_key_wrap_sweep_synthetic_chained_unwrap(self):
        aes_key_wrap_sweep._self_test()

    def test_legacy_cbc_backfill_reproduces_zero_hits(self):
        candidates = extended_cipher_recheck.load_curated_candidates()
        result = legacy_cbc_backfill.sweep(candidates)
        self.assertEqual(len(candidates), 648)
        self.assertEqual(result["keystrings"], 14551)
        self.assertEqual(result["hits"], [])

    def test_stream_mode_cipher_sweep_checkpoint_mechanism(self):
        stream_mode_cipher_sweep.self_test()

    # 2026-08-22: Phase 23's command-provenance recheck had the same unsafe
    # inline-in-main() self-test pattern fixed earlier this session in
    # extended_cipher_recheck.py and literal_raw_key_material_audit.py.
    # Extracted a standalone self_test() (verified byte-identical CLI vs.
    # direct-call output) and strengthened it to run the real full sweep
    # (cheap, ~0.2s) instead of a single-candidate probe, matching FINDINGS'
    # own "13 candidates, 0 hits" result.
    def test_command_provenance_recheck_reproduces_zero_hits(self):
        command_provenance_recheck.self_test()

    # 2026-08-22: first_hint_hash_audit.py (Phase 35, extended across many
    # later phases -- 137/154/164) has a real self-test (address derivation,
    # known SalPhaseIon route hash, solved Phase-1 password hash, and the
    # original creator JPEG's exact SHA-256, all against committed assets)
    # but was never wired into this suite.
    def test_first_hint_hash_audit_provenance(self):
        first_hint_hash_audit.self_test()

    # 2026-08-22: lastcommand_probe.py (Phase 0.1) had no self_test()/audit()
    # split and no argparse -- its sweep logic lived entirely inline in
    # main(), only reachable by capturing stdout. Extracted a standalone
    # probe() returning (forms, hits) so this can be asserted directly
    # (behavior-preserving; verified byte-identical CLI output before/after).
    def test_lastcommand_probe_reproduces_zero_hits(self):
        forms, hits = lastcommand_probe.probe()
        self.assertEqual(len(lastcommand_probe.CANDIDATES), 28)
        self.assertEqual(len(forms), 168)
        self.assertEqual(hits, [])

    # 2026-08-22: Phase 75's own audit script (youwon_partition_audit.py)
    # was never wired into this suite either.
    @unittest.skipUnless(
        Path(DEFAULT_EXPORT_DIR, "result.json").exists(),
        "raw Telegram Desktop JSON export is unavailable",
    )
    def test_youwon_partition_audit_geometry_and_oracle(self):
        result = youwon_partition_audit.audit()
        self.assertEqual(result["grid"][3], youwon_partition_audit.ROW_TEXT)
        self.assertEqual(result["oracle"]["hits"], [])

    # 2026-08-22: Phase 368 closes GSMG_PHASE_VALIDATION_LOGIC_CONSISTENCY_
    # AUDIT.md Finding 2 -- Phase 75's YOUWON/YOUWONX candidates predate
    # Phase 78's binary-plaintext oracle fix and were never confirmed
    # re-swept. This reruns them under the current oracle across
    # CBC/ECB/stream/Key Wrap.
    def test_youwon_full_oracle_backfill_reproduces_zero_hits(self):
        youwon_full_oracle_backfill.self_test()

    # 2026-08-22: Phase 370 forward-transfers Phase 341's solved-boundary
    # grammar to P32TRAILING per the user's exact sequencing (freeze rules,
    # generate manifest without querying the blob, diff against Phase 270,
    # query only genuinely-new candidates). Confirms 0 genuinely new
    # candidates -- P32TRAILING has no local annotation for the grammar's
    # case/whitespace axes to freeze, so the transfer collapses to exactly
    # Phase 270's own already-tested "whole-text family."
    def test_p32_solved_boundary_grammar_transfer_audit(self):
        p32_solved_boundary_grammar_transfer_audit.self_test()

    # 2026-08-22: Phase 371 tests the null/T6 topology (GSMG_TOPOLOGY_AUDIT.md)
    # directly -- for each of DBBI/FAED separately: what local instruction
    # consumes it, what output type does that predict, what authenticated
    # target accepts that type. Finds an asymmetric result (DBBI has 1
    # adjacent instruction, unexecutable per G-MSL-001; FAED has 2, pointing
    # at the separately-tracked G-ARCH-001 rather than at FAED itself) and no
    # evidence either stream requires the other as input.
    @unittest.skipUnless(
        dbbi_faed_independent_consumer_audit.DEFAULT_HTML.exists(),
        "sibling GSMG page mirror is unavailable",
    )
    def test_dbbi_faed_independent_consumer_audit(self):
        dbbi_faed_independent_consumer_audit.self_test()

    # 2026-08-22: Phase 372 -- SALPH/COSMIC Phase-341 eligibility-and-delta
    # audit. SALPH's hash_prefix branch is grammar-eligible and fully
    # exhausted (0 new candidates, 0 hits widened to ECB/stream/Key Wrap);
    # its thispassword branch is ineligible because Phase 101's three
    # candidate roles (password for FAED, FAED's answer merely labeled
    # "password", or password for SALPH) remain unreconciled -- none
    # selected, so no candidate is generated (corrected same-day: this is
    # NOT "pending G-ARCH-001"; that was a retracted overclaim -- see the
    # Phase 372 correction blockquote in FINDINGS.md). COSMIC fails
    # eligibility entirely (self-contained, no demonstrated connection).
    @unittest.skipUnless(
        salph_cosmic_phase341_eligibility_audit.DEFAULT_HTML.exists(),
        "sibling GSMG page mirror is unavailable",
    )
    def test_salph_cosmic_phase341_eligibility_audit(self):
        salph_cosmic_phase341_eligibility_audit.self_test()

    # 2026-08-22: Phase 373 -- attempts to discriminate Phase 101's three
    # thispassword roles by scoring dataflow topology on seven frozen
    # dimensions, calibrated first against the two known multi-component
    # solved boundaries (Phase 3, Phase 3.2). No password or transform is
    # run. CORRECTED SAME-DAY (user review): the original modeling scored
    # faed_answer_is_password as though it had to skip
    # lastwordsbeforearchichoice to bind on raw FAED (it doesn't -- its
    # natural graph labels that instruction's own output directly), and
    # scored password_for_salph_blob against hash_prefix -- a separate,
    # already-scoped instruction (Phase 121/372) -- rather than the actual
    # SALPH blob segment, plus awarded message-8446 precedent asymmetrically
    # despite that message fixing token ORDER only, never a consumption
    # edge. The file now keeps both the disputed and a corrected modeling
    # and asserts they DISAGREE on the winner (password_for_salph_blob vs.
    # faed_answer_is_password) -- proving the original conclusion was
    # model-dependent. Combined with CALIBRATION_ANALOG_AVAILABLE=False (no
    # solved boundary calibrates thispassword's specific postpositive-
    # attachment ambiguity), the verdict is inconclusive and
    # operand_ranking_licensed=False. Phase 101's three roles remain
    # unresolved; the self-test source-guards against reintroducing Phase
    # 372's retracted G-ARCH-001 overclaim.
    @unittest.skipUnless(
        thispassword_role_topology_discrimination_audit.DEFAULT_HTML.exists(),
        "sibling GSMG page mirror is unavailable",
    )
    def test_thispassword_role_topology_discrimination_audit(self):
        thispassword_role_topology_discrimination_audit.self_test()

    # 2026-08-22: Phase 374 -- corrected-oracle backfill for Phase 11's
    # frozen hash-duality candidate family (11,899 candidates x 4 prior
    # hashes). Wires only self_test(), which regenerates and digests the
    # manifest and confirms the newline-coverage discrepancy as a checked
    # fact (with_newline=4,283,640 vs no_newline=1,427,880) -- fast, no
    # oracle calls. The actual multi-million-attempt Stage 2/3 oracle sweep
    # (1,427,880 + 2,855,760 attempts, 0 hits, ~132s total) was run once and
    # is recorded in FINDINGS.md, not rerun on every test invocation.
    def test_hash_duality_corrected_oracle_backfill(self):
        hash_duality_corrected_oracle_backfill.self_test()

    # 2026-08-22: Phase 376 -- Step 1 of the topology-identifiability audit.
    # Freezes ONLY primary evidence (5 Wayback captures, live DOM
    # segmentation, solved-stage syntax, creator messages with real reply
    # edges), explicitly excluding community interpretation and prior-phase
    # prose. Independently re-verified this session by live fetch (see
    # FINDINGS.md): both textareas are byte-identical across the full
    # 2023-06-01 to 2026-04-05 observation window. Sharp finding: creator
    # message 20223 replies to 20221, not 20222 -- answers a different
    # question than the one immediately before it.
    def test_topology_identifiability_evidence_freeze(self):
        topology_identifiability_evidence_freeze.self_test()

    # 2026-08-22 (corrected same-day): Steps 2-5 of the topology-
    # identifiability audit. For each of Phase 101's three thispassword
    # roles, states the discriminating observable it would need, checks it
    # against Step 1's frozen evidence (literal DOM stream -- both its
    # deictic vocabulary AND, separately, an explicit attachment marker;
    # solved-stage grammar; creator reply record, including a reply-parent
    # check across all 148 rows), and -- finding no witness and no hard
    # contradiction -- reports the bounded verdict: underdetermined, not
    # formally unidentifiable by any possible model. No scoring or
    # password generation is performed.
    def test_thispassword_role_identifiability_audit(self):
        thispassword_role_identifiability_audit.self_test()

    def test_input_byte_pathway_reconstruction_audit(self):
        input_byte_pathway_reconstruction_audit.self_test()

    def test_raw_key_chunk_audit(self):
        raw_key_chunk_audit.self_test()

    @unittest.skipUnless(
        (raw_asset_byte_password_audit.SOLVER_EXPORT_DIR / "result.json").exists()
        and (raw_asset_byte_password_audit.SUPPORT_EXPORT_DIR / "result.json").exists(),
        "one or both Telegram exports are unavailable",
    )
    def test_raw_asset_byte_password_audit(self):
        raw_asset_byte_password_audit.self_test()

    def test_phase382_1141_offset_audit(self):
        phase382_1141_offset_audit.self_test()

    # 2026-08-22: Phase 169/192's SalPhaseIon salt/selector family and
    # Phase 303's QR line-type/center-square-fill scripts all have real
    # self-tests but were never wired into the suite.
    def test_salt_phase_ion_audit(self):
        salt_phase_ion_audit.self_test()

    def test_cosmic_83_guide_alignment_audit(self):
        cosmic_83_guide_alignment_audit.self_test()

    def test_salt_selector_permutation_audit(self):
        salt_selector_permutation_audit.self_test()

    def test_qr_finder_ring_texture_center_square_continuation_render(self):
        qr_finder_ring_texture_center_square_continuation_render.self_test()

    def test_qr_finder_ring_texture_line_type_alphabet_audit(self):
        qr_finder_ring_texture_line_type_alphabet_audit.self_test()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 44's three scripts
    # were never wired into this suite. yin_yang_next_edge_audit.py's audit()
    # hard-asserts all its claims and needs only the committed first-piece
    # image, so it runs unconditionally. yin_yang_transition_audit.py's
    # audit() needs the raw chat_transcript.txt export (skip-guarded, same
    # external-fixture pattern as elsewhere in this file).
    # looking_forward_source_audit.py's audit() needs the frozen source PDF
    # already downloaded to its default /tmp path (skip-guarded rather than
    # auto-downloading during test runs); this session downloaded it once by
    # hand while verifying Phase 44 and confirmed the exact SHA-256/anchors
    # match, but a fresh checkout without that file will correctly skip.
    def test_yin_yang_next_edge_audit_reproduces_bounded_readings(self):
        report = yin_yang_next_edge_audit.audit(
            yin_yang_next_edge_audit.DEFAULT_IMAGE
        )
        self.assertEqual(
            report["true_characters"],
            yin_yang_next_edge_audit.EXPECTED_TRUE_CHARACTERS,
        )
        self.assertEqual(
            report["false_characters"],
            yin_yang_next_edge_audit.EXPECTED_FALSE_CHARACTERS,
        )
        self.assertEqual(
            report["byte_aligned_forward"],
            yin_yang_next_edge_audit.EXPECTED_BYTE_ALIGNED_FORWARD,
        )

    @unittest.skipUnless(
        yin_yang_transition_audit.DEFAULT_CHAT.exists(),
        "raw chat_transcript.txt export is unavailable",
    )
    def test_yin_yang_transition_audit_reproduces_bingo_evidence(self):
        report = yin_yang_transition_audit.audit(
            yin_yang_transition_audit.DEFAULT_CHAT,
            yin_yang_transition_audit.DEFAULT_MIRROR,
            yin_yang_transition_audit.DEFAULT_IMAGE,
        )
        self.assertEqual(
            len(report["page_mechanics"]["seed_page"]["forms"]), 1
        )
        self.assertAlmostEqual(
            report["first_piece"]["minimal_hue_distance"], 180, delta=1
        )

    @unittest.skipUnless(
        looking_forward_source_audit.DEFAULT_PDF.exists(),
        "Looking Forward source PDF has not been downloaded",
    )
    def test_looking_forward_source_audit_sha256_and_page37_anchors(self):
        report = looking_forward_source_audit.audit(
            looking_forward_source_audit.DEFAULT_PDF
        )
        self.assertEqual(
            report["sha256"], looking_forward_source_audit.EXPECTED_SHA256
        )
        self.assertEqual(report["page_count"], 122)

    # 2026-08-22 hub-phase code-vs-premise review: Phase 102's anstoo/SHA-
    # operand provenance re-scan has a real self-test (0 creator mentions,
    # >=90 community mentions, 103-char instruction-concatenation check,
    # 21-row walkback) but was never wired into the suite.
    @unittest.skipUnless(
        (Path(DEFAULT_EXPORT_DIR) / "result.json").exists(),
        "Telegram export is unavailable",
    )
    def test_anstoo_provenance_audit_creator_silence_and_community_survey(self):
        report = anstoo_provenance_audit.self_test()
        self.assertEqual(report["anstoo_mention_count"], 93)

    # 2026-08-22 hub-phase code-vs-premise review: Phase 164's literal-raw-
    # key-material oracle had its self-test unsafely embedded inline inside
    # main()'s argparse flow (same class of bug fixed earlier in
    # extended_cipher_recheck.py). Extracted a standalone self_test(),
    # behavior-preserving (verified byte-identical CLI vs. direct-call
    # output), and wired it in here.
    def test_literal_raw_key_material_audit_synthetic_vector_recovered(self):
        literal_raw_key_material_audit.self_test()

    # 2026-08-22 hub-phase code-vs-premise review: Phase 259 lists three
    # downstream consumer scripts it re-ran after the book-text update
    # (cosmic_duality_book_second_riddle_audit.py, telegram_matrix_sum_
    # passage_audit.py, prefix_boundary_sweep.py) that were never actually
    # wired into this suite -- unlike yinyang_cosmic_phase_label_audit.py and
    # matrixsumlist_provenance_refresh_audit.py, which already were.
    def test_cosmic_duality_book_second_riddle_audit_reproduces_token_counts(self):
        cosmic_duality_book_second_riddle_audit.self_test()

    @unittest.skipUnless(
        (Path(DEFAULT_EXPORT_DIR) / "result.json").exists(),
        "Telegram export is unavailable",
    )
    def test_telegram_matrix_sum_passage_audit_provenance(self):
        telegram_matrix_sum_passage_audit.self_test()

    def test_prefix_boundary_sweep_self_tests(self):
        prefix_boundary_sweep.run_self_tests()


if __name__ == "__main__":
    unittest.main()
