#!/usr/bin/env python3

import unittest

import periodic_grille_fefe_audit as audit


class PeriodicGrilleFefeAuditTest(unittest.TestCase):
    def test_complete_bounded_family(self):
        audit.self_test()


if __name__ == "__main__":
    unittest.main()
