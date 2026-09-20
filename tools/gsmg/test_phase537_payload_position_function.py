#!/usr/bin/env python3
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase537_payload_position_function as p537


class Phase537Tests(unittest.TestCase):
    def test_self_test_passes(self):
        result = p537.self_test()
        self.assertTrue(result["ok"], result["checks"])

    def test_no_oracle_in_namespace(self):
        for name in ("aes_try_open", "aes_try_open_bytes", "passphrase_hits", "BLOBS"):
            self.assertNotIn(name, dir(p537))

    def test_targets_and_cells(self):
        targets = p537.payload_targets()
        self.assertEqual([len(t["symbols"]) for t in targets], [60, 61])
        cells, dup = p537.build_cells(targets[0]["coords"])
        self.assertGreaterEqual(dup, 0)
        self.assertTrue(all(c["n_classes"] <= 9 for c in cells))
        self.assertEqual(len(p537.pick_planting_cells(cells)), 8)

    def test_planted_payload_is_exact_and_scored_as_lead(self):
        target = p537.payload_targets()[0]
        cells, _ = p537.build_cells(target["coords"])
        mats = p537.class_matrix(cells, len(target["symbols"]))
        cell = p537.pick_planting_cells(cells)[0]
        planted = p537.planted_payload(cell, random.Random(3), 0.0)
        result = p537.score_target(planted, cells, mats, 300, 7)
        self.assertIn(cell["label"], result["exact_cells"])
        noisy = p537.planted_payload(cell, random.Random(4), 0.10)
        self.assertLessEqual(p537.score_target(noisy, cells, mats, 1000, 8)["family_tail_add_one"], 0.001)

    def test_shuffled_real_payload_is_not_a_lead(self):
        target = p537.payload_targets()[0]
        cells, _ = p537.build_cells(target["coords"])
        mats = p537.class_matrix(cells, len(target["symbols"]))
        rng = random.Random(11)
        symbols = list(target["symbols"])
        rng.shuffle(symbols)
        result = p537.score_target("".join(symbols), cells, mats, 500, 9)
        self.assertEqual(result["exact_cells"], [])
        self.assertGreater(result["family_tail_add_one"], 0.001)


if __name__ == "__main__":
    unittest.main()
