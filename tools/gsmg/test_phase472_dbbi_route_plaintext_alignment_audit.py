#!/usr/bin/env python3

import unittest

import numpy as np

import phase472_dbbi_route_plaintext_alignment_audit as audit


class Phase472StructuralTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.perms, cls.labels = audit.canonical_route_registry()

    def test_structural_self_test(self):
        audit.structural_self_test()

    def test_registry_exact_and_unique(self):
        self.assertEqual(self.perms.shape, (19686, 91))
        self.assertEqual(len(set(map(tuple, self.perms.tolist()))), 19686)
        self.assertEqual(len(set(self.labels)), 19686)

    def test_fixed_targets(self):
        self.assertEqual(len(audit.VALIDATION_ANSWER), 91)
        controls = audit.normalized_control_windows()
        self.assertEqual([name for name, _ in controls], [
            "control_offset_0", "control_offset_273",
            "control_offset_546", "control_offset_819",
        ])
        self.assertTrue(all(len(text) == 91 and text.isupper() for _, text in controls))

    def test_score_recovers_synthetic_perfect_route(self):
        routed = np.zeros((2, 91), dtype=np.uint8)
        routed[1] = np.arange(91, dtype=np.uint8) % 9
        scores, mappings = audit.score_vector(
            routed, 8 - routed, np.arange(91, dtype=np.uint8) % 9
        )
        self.assertEqual(int(scores[1]), 91)
        self.assertEqual(int(mappings[1]), 0)


if __name__ == "__main__":
    unittest.main()
