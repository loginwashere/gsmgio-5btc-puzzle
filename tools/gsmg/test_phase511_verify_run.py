#!/usr/bin/env python3
from __future__ import annotations

import unittest

import phase511_verify_run as verifier


class Phase511VerifierTests(unittest.TestCase):
    def test_completed_result_reproduces(self):
        record = verifier.verify()
        self.assertTrue(record["consistent"])
        self.assertEqual(record["transfer_pass_count"], 3)
        self.assertEqual(record["incremental_value_pass_count"], 0)
        self.assertFalse(record["faed_scored"])

    def test_hashes_are_sha256(self):
        record = verifier.verify()
        self.assertEqual(len(record["execution_lock_sha256"]), 64)
        self.assertEqual(len(record["result_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
