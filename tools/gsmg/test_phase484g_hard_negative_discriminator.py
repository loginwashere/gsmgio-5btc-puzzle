#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484g_hard_negative_discriminator as probe


class Phase484GTests(unittest.TestCase):
    def test_self_test(self):
        probe.self_test()

    def test_split_is_disjoint_and_faed_is_not_imported(self):
        self.assertTrue(set(probe.TRAIN_INDICES).isdisjoint(probe.EVAL_INDICES))
        source = Path(probe.__file__).read_text()
        self.assertNotIn("from data import FAED", source)
        self.assertNotIn("data.FAED", source)

    def test_feature_is_deterministic(self):
        model = probe.base.SpectralModel.from_training_corpus()
        fixture = probe.base.make_fixture(
            10, 0, 998, seed=probe.SEED,
            board_mode="broad_random", split="dev",
        )
        left = probe.candidate_features(model, fixture, fixture["order"])
        right = probe.candidate_features(model, fixture, fixture["order"])
        np.testing.assert_array_equal(left, right)
        cheap = probe.candidate_features(
            model, fixture, fixture["order"], include_neighborhood=False
        )
        np.testing.assert_array_equal(cheap, left[:40])

    def test_overlapping_split_fails_closed(self):
        with self.assertRaises(ValueError):
            probe.run_probe(
                train_indices=(1,), eval_indices=(1,),
                train_random=1, train_hard=1,
                eval_random=1, eval_hard=1,
            )

    def test_feature_selection_does_not_mutate_input(self):
        records = [{"examples": [
            {"kind": "planted", "feature": [1.0, 2.0, 3.0]},
            {"kind": "hard", "feature": [4.0, 5.0, 6.0]},
        ]}]
        selected = probe.select_features(records, (0, 2))
        self.assertEqual(selected[0]["examples"][0]["feature"], [1.0, 3.0])
        self.assertEqual(records[0]["examples"][0]["feature"], [1.0, 2.0, 3.0])


if __name__ == "__main__":
    unittest.main()
