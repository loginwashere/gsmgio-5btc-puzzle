#!/usr/bin/env python3

import unittest

import denis_full_corpus_audit as audit


class DenisFullCorpusAuditTest(unittest.TestCase):
    def test_synthetic_self_test(self):
        audit.self_test()


if __name__ == "__main__":
    unittest.main()
