#!/usr/bin/env python3
"""Permanent regressions for corrected late-stage GSMG audit claims."""

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import binary_message_export_audit
import checkerboard_code_ic_oracle
import dual_channel_consistency_audit
import promised_standalone_audit
import remaining_structural_avenues_audit
import safenet_luna_hsm_audit
import salphaseion_salvation_role_audit
import salphaseion_wayback_history_audit
import spi_cd_initials_audit
import synthesis_action_paths_audit
import telegram_yellow_blue_matrix_direction_audit
import triangular_matrixsumlist_audit
from page_structure_audit import DEFAULT_HTML
from telegram_export_manifest import DEFAULT_EXPORT_DIR


class CorrectedClaimTests(unittest.TestCase):
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
