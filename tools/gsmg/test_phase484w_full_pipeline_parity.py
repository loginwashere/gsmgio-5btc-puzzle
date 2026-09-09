import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484w_full_pipeline_parity as subject


class Phase484WFullPipelineParityTests(unittest.TestCase):
    def test_self_test(self):
        result = subject.self_test()
        self.assertTrue(result["comparison_self_test"])

    def test_compare_detects_scalar_change(self):
        sample = {field: 1 for field in subject.SCALAR_FIELDS}
        sample.update({field: [] for field in subject.LARGE_FIELDS})
        changed = dict(sample)
        changed[subject.SCALAR_FIELDS[0]] = 2
        self.assertFalse(subject.compare(sample, changed)["exact_parity"])


if __name__ == "__main__":
    unittest.main()
