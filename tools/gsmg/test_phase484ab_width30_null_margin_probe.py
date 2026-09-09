import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484ab_width30_null_margin_probe as subject


class Phase484ABNullMarginTests(unittest.TestCase):
    def test_shuffle_is_deterministic_and_preserves_each_row_multiset(self):
        rows = [np.asarray([1, 2, 2, 3]), np.asarray([9, 8, 7]),
                np.asarray([], dtype=np.int64)]
        first = subject.shuffle_rows(rows, 123)
        second = subject.shuffle_rows(rows, 123)
        for original, left, right in zip(rows, first, second):
            np.testing.assert_array_equal(left, right)
            np.testing.assert_array_equal(np.sort(left), np.sort(original))

    def test_load_pool_rejects_hash_mismatch(self):
        payload = {
            "fixture_index": 16, "faed_scored": False,
            "holdout_consumed": False, "pool_sha256": "wrong",
            "per_candidate": [{"path": list(range(8)), "is_true": False}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.json"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                subject.load_pool(path, 16)

    def test_null_control_count_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            subject.run(null_controls=0)


if __name__ == "__main__":
    unittest.main()
