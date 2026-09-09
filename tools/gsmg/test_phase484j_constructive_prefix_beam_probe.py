#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484j_constructive_prefix_beam_probe as probe


class Phase484JTests(unittest.TestCase):
    def test_self_test(self):
        probe.self_test()

    def test_order_sequence_round_trip(self):
        for order in ([0, 1, 2], [2, 0, 1], [1, 2, 0]):
            self.assertEqual(
                probe.sequence_to_order(probe.order_to_sequence(order)), list(order)
            )

    def test_true_sequence_reconstructs_raw_rows(self):
        fixture = probe.base.make_fixture(
            15, 0, 779, seed=probe.learned.SEED,
            board_mode="vic_profile", split="dev",
        )
        blocks = probe.blocks_from_observed(fixture)
        sequence = probe.order_to_sequence(fixture["order"])
        restored = "".join(
            "".join(blocks[index][row] for index in sequence)
            for row in range(len(blocks[0]))
        )
        self.assertEqual(restored, fixture["raw"])

    def test_prefix_feature_is_invariant_to_call_order(self):
        fixture = probe.base.make_fixture(
            10, 0, 778, seed=probe.learned.SEED,
            board_mode="broad_random", split="dev",
        )
        blocks = probe.blocks_from_observed(fixture)
        path = probe.order_to_sequence(fixture["order"])[:5]
        left = probe.prefix_features(blocks, path, tuple(fixture["pair"]))
        right = probe.prefix_features(blocks, path, tuple(fixture["pair"]))
        np.testing.assert_array_equal(left, right)

    def test_invalid_full_order_objective_is_explicit(self):
        fixture = probe.base.make_fixture(
            10, 0, 780, seed=probe.learned.SEED,
            board_mode="vic_profile", split="dev",
        )
        classifier = probe.full_model.load_model()
        spectral = probe.base.SpectralModel.from_training_corpus()
        values = [
            probe.full_model.objective(
                classifier, spectral, fixture, probe.sequence_to_order(path)
            )
            for path in (
                tuple(range(10)),
                tuple(reversed(range(10))),
            )
        ]
        self.assertTrue(all(value is None or np.isfinite(value) for value in values))

    def test_faed_is_prohibited(self):
        source = Path(probe.__file__).read_text()
        self.assertNotIn("from data import FAED", source)
        self.assertNotIn("data.FAED", source)

    def test_training_accepts_one_board_pool(self):
        models = probe.train_models(10, board_modes=("vic_profile",))
        self.assertEqual(set(models), set(range(probe.START_DEPTH, 10)))

    def test_adaptive_beam_is_bounded_to_early_depths(self):
        self.assertGreater(probe.EARLY_BEAM_WIDTH, probe.BEAM_WIDTH)
        self.assertEqual(probe.EARLY_THROUGH_DEPTH, 6)


if __name__ == "__main__":
    unittest.main()
