import collections
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

import phase484a_raw_symbol_vic_solver as base
import phase491_raw_histogram_fixture as rawonly
import phase505_escape_pair_identifiability as phase505


class Phase505Tests(unittest.TestCase):
    def test_pair_universe(self):
        self.assertEqual(len(phase505.ALL_PAIRS), 36)
        self.assertEqual(phase505.ALL_PAIRS[0], ("a", "b"))
        self.assertEqual(phase505.ALL_PAIRS[-1], ("h", "i"))

    def test_profile_reconstructs_frozen_raw_counts(self):
        for pair_index in (0, 17, 35):
            profile = phase505.sampled_token_profile(pair_index, 0)
            reconstructed = collections.Counter()
            for token, count in profile["token_counts"].items():
                for symbol in token:
                    reconstructed[symbol] += count
            self.assertEqual(reconstructed, collections.Counter(
                rawonly.RAW_COUNTS))

    def test_fixture_selection_is_deterministic_and_distinct(self):
        fixtures, rejected = phase505.eligible_candidates(0)
        self.assertEqual([item["fixture_index"] for item in fixtures], [0, 1])
        self.assertNotEqual(fixtures[0]["source_region"],
                            fixtures[1]["source_region"])
        self.assertEqual(fixtures, phase505.eligible_candidates(0)[0])
        self.assertTrue(rejected)
        for fixture in fixtures:
            phase505.verify_fixture(fixture)

    def test_token_slots_rejects_dangling_escape(self):
        self.assertIsNone(phase505.token_slots("abcda", ("a", "b")))

    def test_token_slots_cover_all_codes(self):
        pair = ("a", "b")
        raw = "".join(base.slot_codes(pair))
        slots = phase505.token_slots(raw, pair)
        self.assertTrue(np.array_equal(slots, np.arange(25)))

    def test_rank_true_pair_uses_canonical_tie_break(self):
        records = [
            {"hypothesis_pair_index": 0, "valid": True,
             "normalized_score": -5.0},
            {"hypothesis_pair_index": 1, "valid": True,
             "normalized_score": -4.0},
            {"hypothesis_pair_index": 2, "valid": True,
             "normalized_score": -4.0},
        ]
        result = phase505.rank_true_pair(records, 2)
        self.assertEqual(result["true_pair_rank"], 2)
        self.assertEqual(result["ranked_pair_indices"], [1, 2, 0])
        self.assertEqual(result["true_minus_best_wrong"], 0.0)

    def test_score_fixture_batches_valid_pairs_without_faed(self):
        pair = phase505.ALL_PAIRS[0]
        board = dict(zip(base.LETTER_ALPHABET, base.slot_codes(pair)))
        fixture = {
            "true_pair_index": 0, "pair": list(pair), "fixture_index": 0,
            "raw": "c" * 570, "raw_sha256": "synthetic",
            "plaintext_length": 570, "edit_fraction": 0.0,
            "normalized_quadgram": -4.0, "letter_to_code": board,
        }
        def fake(_binary, rows, _quad, restarts, iterations, seed):
            self.assertEqual((restarts, iterations, seed),
                             (phase505.RESTARTS, phase505.ITERATIONS,
                              phase505.ANNEAL_SEED))
            scores = np.linspace(-4.0, -5.0, len(rows))
            boards = np.tile(np.arange(25, dtype=np.uint8), (len(rows), 1))
            return scores, boards, np.zeros(len(rows), dtype=np.int64)
        with mock.patch.object(phase505.joint, "gpu_full_multistart", fake):
            record = phase505.score_fixture(fixture)
        self.assertEqual(record["true_pair_rank"], 1)
        self.assertEqual(len(record["pairs"]), 36)
        self.assertGreaterEqual(record["wall_seconds"], 0.0)

    def test_self_test_is_cpu_only(self):
        with mock.patch.object(
                phase505.joint, "gpu_full_multistart",
                side_effect=AssertionError("GPU called")):
            result = phase505.self_test()
        self.assertEqual(result["pair_count"], 36)
        self.assertFalse(result["faed_scored"])
        self.assertFalse(result["execution_lock_issued"])

    def test_ceiling_refuses_without_execution_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "absent-lock.json"
            with mock.patch.object(phase505, "LOCK_PATH", missing):
                with self.assertRaisesRegex(RuntimeError, "lock is absent"):
                    phase505.run_ceiling(Path(directory) / "result.json")

    def test_progress_validation_fails_closed(self):
        fixtures = [{"true_pair_index": 0, "pair": ["a", "b"],
                     "fixture_index": 0, "raw_sha256": "raw0"}]
        record = {"true_pair_index": 0, "true_pair": ["a", "b"],
                  "fixture_index": 0, "fixture_raw_sha256": "raw0",
                  "wall_seconds": 2.0}
        progress = phase505.progress_payload([record], 1, "lock", "manifest")
        self.assertEqual(phase505.validate_progress(
            progress, fixtures, "lock", "manifest"), [record])
        progress["records"][0]["fixture_raw_sha256"] = "tampered"
        with self.assertRaisesRegex(RuntimeError, "sequence mismatch"):
            phase505.validate_progress(
                progress, fixtures, "lock", "manifest")


if __name__ == "__main__":
    unittest.main()
