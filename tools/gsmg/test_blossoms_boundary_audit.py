#!/usr/bin/env python3

import unittest

import blossoms_boundary_audit as audit


class BlossomsBoundaryAuditTest(unittest.TestCase):
    def test_bounded_column_extension(self):
        audit.self_test()


if __name__ == "__main__":
    unittest.main()
