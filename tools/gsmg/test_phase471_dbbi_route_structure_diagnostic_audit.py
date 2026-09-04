#!/usr/bin/env python3

import unittest

import phase471_dbbi_route_structure_diagnostic_audit as audit


class Phase471StructuralTest(unittest.TestCase):
    def test_helpers(self):
        audit.structural_self_test()

    def test_route_census_invariants(self):
        census = audit.route_census()
        self.assertEqual(census["total_routes_enumerated"], 19690)
        self.assertEqual(census["unique_permutations"], 19686)
        self.assertEqual(census["unique_output_strings"], 19686)
        self.assertTrue(census["identity_string_present"])
        self.assertFalse(census["crt_claim_linear_equals_toroidal_7x13_strings"])
        self.assertEqual(census["linear_toroidal_string_overlap"], 0)

    def test_rank_full_and_masks(self):
        ranks = audit.rank_vector(audit.DBBI)
        self.assertEqual(set(ranks.values()), {7})
        for name in audit.MASK_NAMES:
            bits = audit.mask_bits(name)
            self.assertEqual(len(bits), 91)
            self.assertEqual(set(bits) - {0, 1}, set())

    def test_exact_bar_records_are_degenerate_families_only(self):
        seven = [x for x in audit.seven_segment_readings() if x["exact_bar_met"]]
        self.assertEqual(len(seven), 3)
        for record in seven:
            self.assertEqual(record["on_polarity"], 0)
            self.assertIn(record["mask"], {"a", "d", "i"})
            self.assertGreaterEqual(record["decoded"].count("8"), 8)
        packed = [x for x in audit.base9_readings() if x["exact_bar_met"]]
        self.assertEqual(packed, [])
        bitmask = [x for x in audit.bitmask_readings() if x["exact_bar_met"]]
        self.assertEqual(len(bitmask), 2)
        for record in bitmask:
            self.assertEqual(record["mask"], "b")
            self.assertEqual(record["on_polarity"], 0)


if __name__ == "__main__":
    unittest.main()
