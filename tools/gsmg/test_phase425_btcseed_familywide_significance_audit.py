#!/usr/bin/env python3

import unittest
import json
from pathlib import Path

import numpy as np

import phase425_btcseed_familywide_significance_audit as phase425


class Phase425AuditTests(unittest.TestCase):
    def test_frozen_result_artifact(self):
        result_path = Path(__file__).with_name("phase425_result.json")
        report = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertEqual(report["outcome"], "family_corrected_positive_checkpoint_only")
        self.assertEqual(report["distinct_square_count"], 12)
        self.assertEqual(report["observed"]["configuration_count"], 1536)
        self.assertEqual(report["observed"]["distinct_output_count"], 1248)
        self.assertEqual(report["observed"]["maximum_lcp"], 7)
        self.assertEqual(report["observed"]["exact_prefix_output_count"], 1)
        self.assertEqual(report["null"]["null_maximum_lcp"], 6)
        self.assertEqual(report["null"]["null_trials_reaching_exact_target"], 0)
        self.assertEqual(report["tail_count"], 0)
        self.assertAlmostEqual(report["empirical_familywise_p"], 1 / 10001)

    def test_full_family_regression_and_planted_positive(self):
        report = phase425.audit(trials=32, seed=phase425.DEFAULT_SEED, include_candidates=False)
        self.assertTrue(report["observed"]["original_matches_phase386"])
        self.assertEqual(report["observed"]["maximum_lcp"], 7)
        self.assertGreaterEqual(report["observed"]["exact_prefix_output_count"], 1)
        self.assertEqual(report["planted_positive"]["recovered_prefix"], phase425.TARGET)
        self.assertEqual(report["planted_positive"]["detector_lcp"], 7)
        self.assertEqual(report["oracle_calls"], 0)

    def test_batch_edge_matches_full_transform(self):
        square = phase425.keyword_square_manifest()[0]
        lookup, positions, mapping = phase425.square_arrays(square["grid_keyword"])
        source = np.array(
            [mapping[ch] for ch in phase425.normalize_letters(phase425.FAED)], dtype=np.int16
        )
        batch = np.stack((source, source[::-1]))
        for operation in ("decrypt", "encrypt"):
            for order in ("rc", "cr"):
                for sizes in phase425.schedules().values():
                    first_size = sizes[0]
                    first = phase425.transform_edge_batch(
                        batch[:, :first_size], lookup, positions, operation, order, "first"
                    )
                    last = phase425.transformed_last_batch(
                        batch, sizes, lookup, positions, operation, order
                    )
                    for row, text in enumerate(batch):
                        full = phase425.transform_full(
                            text, lookup, positions, sizes, operation, order
                        )
                        self.assertTrue(np.array_equal(first[row], full[:7]))
                        self.assertTrue(np.array_equal(last[row], full[-7:]))


if __name__ == "__main__":
    unittest.main()

