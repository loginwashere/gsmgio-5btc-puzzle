#!/usr/bin/env python3
"""Fast structural tests for Phase 516. The module's own `self_test()`
function is the real correctness check (order recovery on synthetic
plants) but costs ~19 minutes per trial due to the two-stage anneal search,
so it is run manually and reported in the phase writeup rather than wired
into this fast suite -- see doc/GSMG_PHASE516_DBBI_WIDTH7_UNRESTRICTED_AUDIT.md.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase516_dbbi_width7_exhaustive as p516


class Phase516StructuralTests(unittest.TestCase):
    def test_dbbi_length_and_width_divisor(self):
        self.assertEqual(p516.LENGTH, 91)
        self.assertEqual(p516.LENGTH % p516.WIDTH, 0)
        self.assertEqual(p516.LENGTH // p516.WIDTH, 13)

    def test_all_36_pairs_enumerated(self):
        self.assertEqual(len(p516.ALL_PAIRS), 36)
        self.assertEqual(len(set(p516.ALL_PAIRS)), 36)

    def test_geometry_roundtrip(self):
        from phase484a_raw_symbol_vic_solver import Geometry

        geometry = p516.Geometry(p516.LENGTH, p516.WIDTH)
        order = list(range(p516.WIDTH))[::-1]
        encrypted = geometry.encrypt(p516.DBBI, order)
        restored = geometry.decrypt(encrypted, order)
        self.assertEqual(restored, p516.DBBI)
        self.assertIsInstance(geometry, Geometry)

    def test_lock_payload_deterministic_and_matches_dbbi(self):
        payload_a = p516.lock_payload()
        payload_b = p516.lock_payload()
        self.assertEqual(payload_a, payload_b)
        self.assertEqual(payload_a["dbbi_sha256"], p516.DBBI_SHA256)
        self.assertEqual(payload_a["width"], 7)
        self.assertEqual(len(payload_a["pairs"]), 36)

    def test_all_orders_count(self):
        self.assertEqual(len(p516.all_orders(7)), 5040)

    def test_checkpoint_round_trip(self, tmp_path=None):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            payload = {"observed_sha256": "deadbeef", "per_pair": {"ab": {"normalized_score": -1.0}}}
            p516._write_checkpoint(path, payload)
            loaded = p516._load_checkpoint(path)
            self.assertEqual(loaded, payload)


if __name__ == "__main__":
    unittest.main()
