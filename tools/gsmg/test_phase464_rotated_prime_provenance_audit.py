import unittest

import phase464_rotated_prime_provenance_audit as audit


class Phase464Tests(unittest.TestCase):
    def test_synthetic_self_test(self):
        audit.self_test()

    def test_frozen_manifest_and_real_corpus_metadata(self):
        manifest = audit.load_manifest()
        corpora = audit.load_corpora(manifest)
        self.assertEqual(len(corpora["solver"]["messages"]), 60_375)
        self.assertEqual(len(corpora["support"]["messages"]), 52_851)
        self.assertEqual(corpora["solver"]["source_rows"], [57_729, 1_026, 1_722])
        self.assertEqual(corpora["solver"]["overlap_rows"], 102)
