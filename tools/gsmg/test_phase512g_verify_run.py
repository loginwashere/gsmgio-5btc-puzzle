#!/usr/bin/env python3
from __future__ import annotations

import unittest

import phase512g_verify_run as verifier


class Phase512GVerifierTests(unittest.TestCase):
    def test_locked_run_reverifies(self):
        value = verifier.verify()
        self.assertTrue(value["consistent"], value["errors"])
        self.assertEqual(value["starts_revalidated"], 518)
        self.assertEqual(value["cells_revalidated"], 18_648)
        self.assertEqual(value["hits_recomputed"], 0)


if __name__ == "__main__":
    unittest.main()
