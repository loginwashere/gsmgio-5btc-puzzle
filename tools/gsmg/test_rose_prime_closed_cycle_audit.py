#!/usr/bin/env python3

import unittest

import rose_prime_closed_cycle_audit as audit


class RosePrimeClosedCycleAuditTest(unittest.TestCase):
    def test_complete_rotation_type_family(self):
        audit.self_test()


if __name__ == "__main__":
    unittest.main()
