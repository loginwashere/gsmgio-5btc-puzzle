import tempfile
import unittest
from pathlib import Path
from unittest import mock

import phase506b_top5_faed_width19 as phase506b


class Phase506BTests(unittest.TestCase):
    def test_run_refuses_without_lock_before_training(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(phase506b, "LOCK", Path(directory) / "none"), \
                mock.patch.object(phase506b.exact, "train_profile_models",
                                  side_effect=AssertionError("trained")):
            with self.assertRaisesRegex(RuntimeError, "lock is absent"):
                phase506b.run_pair(0)

    def test_real_fixture_uses_requested_pair(self):
        fixture = phase506b.real_fixture(17)
        self.assertEqual(tuple(fixture["pair"]),
                         phase506b.ranker.ceiling.ALL_PAIRS[17])
        self.assertEqual(fixture["observed"], phase506b.FAED)
        self.assertEqual(len(fixture["plaintext"]), len(phase506b.FAED))

    def test_pair_outside_lock_refused(self):
        with mock.patch.object(phase506b, "verify_lock", return_value={}), \
                mock.patch.object(phase506b, "allowed_pair_indices",
                                  return_value=[1, 2, 3, 4, 5]), \
                mock.patch.object(phase506b.exact, "train_profile_models",
                                  side_effect=AssertionError("trained")):
            with self.assertRaisesRegex(RuntimeError, "outside"):
                phase506b.run_pair(0)


if __name__ == "__main__":
    unittest.main()
