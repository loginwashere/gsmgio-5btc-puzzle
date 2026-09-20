#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase538_faed_lane_extraction as p538
from data import FAED


class Phase538Tests(unittest.TestCase):
    def test_masks_match_phase48_and_selection_a(self):
        masks = p538.build_masks()
        self.assertEqual(masks["M31"]["H"], p538.PHASE48_MASK)
        self.assertEqual(masks["M30"]["H"], p538.PHASE48_MASK[:-1])
        self.assertEqual(len(masks["M31"]["C"]), 60)
        self.assertEqual(len(masks["M30"]["C"]), 61)
        for m in masks.values():
            self.assertEqual(sorted(m["Hb"] + m["Hy"]), m["H"])

    def test_precedent_reproduction(self):
        self.assertTrue(all(p538.control_precedent().values()), p538.control_precedent())

    def test_extraction_exactness_on_distinct_values(self):
        self.assertTrue(p538.control_extraction())

    def test_candidate_family_is_closed_and_symbolic(self):
        cands = p538.candidate_strings(FAED)
        self.assertLessEqual(len(cands), 64)
        self.assertGreater(len(cands), 32)
        self.assertEqual(len(cands), len(set(cands)))
        self.assertTrue(all(set(c) <= set(p538.SYMS) for c in cands))

    def test_no_oracle_in_namespace(self):
        for name in ("aes_try_open", "aes_try_open_bytes", "passphrase_hits", "BLOBS"):
            self.assertNotIn(name, dir(p538))

    def test_gate_is_reproducible(self):
        arr = p538.plant("pair", 0.5, np.random.default_rng(7))
        a = p538.gate_scores(arr, 300, 11)
        b = p538.gate_scores(arr, 300, 11)
        self.assertEqual(a["S1"]["tail"], b["S1"]["tail"])
        self.assertEqual(a["S2"]["z"], b["S2"]["z"])

    def test_zero_noise_plants_are_leads_for_their_statistic(self):
        rng = np.random.default_rng(3)
        res = p538.gate_scores(p538.plant("pair", 0.0, rng), p538.CONTROL_REPLICATES, 5)
        self.assertTrue(res["S1"]["lead"])
        res = p538.gate_scores(p538.plant("column", 0.0, rng), p538.CONTROL_REPLICATES, 6)
        self.assertTrue(res["S2"]["lead"])

    def test_lead_threshold_is_attainable_at_control_replicates(self):
        self.assertLessEqual(1 / (p538.CONTROL_REPLICATES + 1), p538.LEAD_TAIL)

    def test_lock_fields_detect_mutation(self):
        want = p538.expected_lock_fields()
        mutated = dict(want)
        mutated["faed_sha256"] = "0" * 64
        self.assertNotEqual(mutated, want)
        self.assertEqual(want["candidate_count"], len(p538.candidate_strings(FAED)))


if __name__ == "__main__":
    unittest.main()
