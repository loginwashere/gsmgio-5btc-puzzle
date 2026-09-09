#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

import phase479_p32_alignment_audit as audit


class Phase479Tests(unittest.TestCase):
    def test_self_test(self):
        self.assertTrue(audit.self_test())

    def test_alignment_domain_is_complete(self):
        self.assertEqual(audit.ALIGNMENTS, tuple(range(17)))

    def test_target_tiers_are_disjoint(self):
        self.assertTrue(set(audit.AUTHENTICATED_TARGETS).isdisjoint(audit.DERIVED_TARGETS))
        self.assertEqual(len(audit.AUTHENTICATED_TARGETS), 2)
        self.assertEqual(len(audit.DERIVED_TARGETS), 8)

    def test_body_length_is_fail_closed(self):
        with self.assertRaises(ValueError):
            audit.evaluate_body(b"x" * 79)

    def test_lock_round_trip_and_code_tamper_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "lock.json"
            audit.issue_lock(lock)
            self.assertEqual(audit.verify_lock(lock)["phase"], 479)
            original = lock.read_text(encoding="utf-8")
            lock.write_text(original.replace('"phase": 479', '"phase": 480'), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                audit.verify_lock(lock)


if __name__ == "__main__":
    unittest.main()

