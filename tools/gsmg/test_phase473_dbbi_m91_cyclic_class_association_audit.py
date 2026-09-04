#!/usr/bin/env python3

import unittest

import numpy as np

import phase473_dbbi_m91_cyclic_class_association_audit as audit


class Phase473StructuralTest(unittest.TestCase):
    def test_structural_self_test(self):
        audit.structural_self_test()

    def test_family_is_exact_and_unique(self):
        labels = audit.cell_labels()
        self.assertEqual(len(labels), 1092)
        self.assertEqual(len({
            (x["representation"], x["plaintext_feature"], x["offset"])
            for x in labels
        }), 1092)

    def test_fft_matches_direct_at_two_offsets(self):
        base = np.fromiter((ord(c) - ord("a") for c in audit.DBBI), dtype=np.uint8, count=91)
        _, feature, ky = audit.plaintext_features(audit.VALIDATION_ANSWER)[3]
        values = audit.fft_mi_offsets(base[None, :], feature, 9, ky)[0]
        self.assertAlmostEqual(values[0], audit.direct_mutual_information(base, feature, 9, ky), places=12)
        shifted = np.roll(base, -23)
        self.assertAlmostEqual(values[23], audit.direct_mutual_information(shifted, feature, 9, ky), places=12)

    def test_perfect_synthetic_dependency(self):
        feature = np.tile(np.arange(3, dtype=np.uint8), 31)[:91]
        values = audit.fft_mi_offsets(feature[None, :], feature, 3, 3)[0]
        self.assertAlmostEqual(
            values[0], audit.direct_mutual_information(feature, feature, 3, 3), places=12
        )
        self.assertGreater(values[0], values[1])


if __name__ == "__main__":
    unittest.main()
