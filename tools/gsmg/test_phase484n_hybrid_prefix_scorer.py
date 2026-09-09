import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase484n_hybrid_prefix_scorer as subject


class DummyModel:
    mean = np.arange(20, dtype=np.float64) / 10
    scale = np.arange(1, 21, dtype=np.float64)
    weight = np.linspace(-1, 1, 20)
    intercept = 0.75


class Phase484NAdapterTests(unittest.TestCase):
    def test_linear_coefficients_are_equivalent(self):
        model = DummyModel()
        coefficient, intercept = subject.linear_coefficients(model)
        values = np.arange(20, dtype=np.float64) / 7
        direct = float(np.dot((values - model.mean) / model.scale, model.weight) + model.intercept)
        flattened = float(np.dot(values, coefficient) + intercept)
        self.assertAlmostEqual(direct, flattened, places=13)

    def test_canonical_blocks_put_pair_first(self):
        blocks = ["abcdefghi" * 3 + "abc" for _ in range(19)]
        encoded = subject.canonical_blocks(blocks, ("g", "i"))
        self.assertEqual(encoded[:9], bytes([2, 3, 4, 5, 6, 7, 0, 8, 1]))

    def test_rejects_wrong_geometry(self):
        with self.assertRaises(ValueError):
            subject.canonical_blocks(["abc"], ("a", "b"))


if __name__ == "__main__":
    unittest.main()
