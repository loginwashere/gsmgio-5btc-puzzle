import tempfile
import unittest
from pathlib import Path
from unittest import mock

import phase510b_heldout_vocabulary_signal as phase510b


class Phase510BTests(unittest.TestCase):
    def test_weighted_nonoverlap(self):
        value = phase510b.score("abcdef", [("abcde", 1), ("bcdef", 5)])
        self.assertEqual([row["term"] for row in value["matches"]], ["bcdef"])

    def test_heldout_vocabulary_excludes_unique_self_terms(self):
        manifest = phase510b.phase510a.validate_manifest()
        terms = dict(phase510b.heldout_terms(manifest, "phase32_literal_plaintext"))
        self.assertNotIn("concordantly", terms)
        self.assertIn("puzzle", terms)

    def test_run_refuses_without_lock_before_scoring(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(phase510b, "LOCK", Path(directory) / "none"), \
                mock.patch.object(phase510b, "score",
                                  side_effect=AssertionError("scored")):
            with self.assertRaisesRegex(RuntimeError, "lock is absent"):
                phase510b.run()

    def test_pcg_preserves_multiset(self):
        first = list("aaaabbbbcccc")
        second = list(first)
        phase510b.PCG32(123).shuffle(first)
        phase510b.PCG32(123).shuffle(second)
        self.assertEqual(first, second)
        self.assertEqual(sorted(first), sorted("aaaabbbbcccc"))


if __name__ == "__main__":
    unittest.main()

