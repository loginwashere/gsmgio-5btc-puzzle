import tempfile
import unittest
from pathlib import Path
from unittest import mock

import phase510a_closed_vocabulary_manifest as phase510a


class Phase510ATests(unittest.TestCase):
    def test_exact_source_and_term_counts(self):
        value = phase510a.build_manifest()
        self.assertEqual(value["source_count"], 4)
        self.assertEqual(value["term_count"], 108)
        self.assertFalse(value["faed_imported_or_scored"])

    def test_low_leave_one_out_coverage_is_visible(self):
        rows = phase510a.build_manifest()["source_diagnostics"]
        self.assertAlmostEqual(
            rows["phase2_solved_plaintext"]["leave_one_document_out_coverage"],
            3 / 39)
        self.assertAlmostEqual(
            rows["phase3_literal_plaintext"]["leave_one_document_out_coverage"],
            3 / 41)
        self.assertEqual(
            rows["phase32_literal_plaintext"]["leave_one_document_out_coverage"], 0)

    def test_unspaced_sequences_are_not_split_into_terms(self):
        value = phase510a.build_manifest()
        terms = {row["term"] for row in value["terms"]}
        self.assertNotIn("privatekeys", terms)
        self.assertEqual(len(value["exact_sequences"]), 4)
        self.assertTrue(all(row["role"] == "exact_sequence_control_not_word_segmented"
                            for row in value["exact_sequences"]))

    def test_write_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(phase510a, "MANIFEST", Path(directory) / "manifest.json"):
            phase510a.atomic_json(phase510a.MANIFEST, {"x": 1})
            with self.assertRaises(FileExistsError):
                phase510a.atomic_json(phase510a.MANIFEST, {"x": 2})


if __name__ == "__main__":
    unittest.main()

