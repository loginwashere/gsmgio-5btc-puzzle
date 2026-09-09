#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484k_bidirectional_segment_assembly_probe as probe


class Phase484KTests(unittest.TestCase):
    def test_self_test(self):
        probe.self_test()

    def test_both_extension_directions_exist(self):
        path = (1, 2, 3)
        block = 0
        self.assertEqual((block,) + path, (0, 1, 2, 3))
        self.assertEqual(path + (block,), (1, 2, 3, 0))

    def test_endpoint_diversity(self):
        candidates = {
            (a, b, c): float(100 - a * 10 - b)
            for a in range(5) for b in range(5) for c in range(5)
            if len({a, b, c}) == 3
        }
        selected = probe.select_diverse(candidates, width=5, beam_width=20)
        self.assertEqual(len(selected), 20)
        self.assertGreater(len({(p[0], p[-1]) for _, p in selected}), 5)

    def test_faed_is_prohibited(self):
        source = Path(probe.__file__).read_text()
        self.assertNotIn("from data import FAED", source)
        self.assertNotIn("data.FAED", source)

    def test_fresh_replication_uses_new_fixture(self):
        self.assertNotEqual(probe.FRESH_EVAL_INDEX, probe.EVAL_INDEX)
        self.assertEqual(probe.WORKERS, 6)

    def test_dev_batch_scope_and_gate(self):
        self.assertEqual(probe.DEV_BATCH_WIDTHS, (10, 15))
        self.assertEqual(probe.DEV_BATCH_INDICES, (23, 24, 25, 26, 27))
        self.assertEqual(probe.DEV_GATE_PER_CELL, 4)

    def test_dev_batch_uses_aggregate_schema(self):
        example = {
            "all_cells_pass": True,
            "cells": [{"records": [], "exact_recovery_count": 5}],
        }
        self.assertNotIn("exact_recovery_count", example)
        self.assertIn("exact_recovery_count", example["cells"][0])


if __name__ == "__main__":
    unittest.main()
