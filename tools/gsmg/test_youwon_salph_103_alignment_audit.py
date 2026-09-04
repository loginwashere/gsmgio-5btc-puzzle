#!/usr/bin/env python3

import unittest

import youwon_salph_103_alignment_audit as audit


class YouwonSalph103AlignmentAuditTest(unittest.TestCase):
    def test_alignment_and_controls(self):
        audit.self_test()


if __name__ == "__main__":
    unittest.main()
