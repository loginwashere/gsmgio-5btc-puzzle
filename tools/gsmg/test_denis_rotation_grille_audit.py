#!/usr/bin/env python3

import unittest

import denis_rotation_grille_audit as audit


class DenisRotationGrilleAuditTest(unittest.TestCase):
    def test_rotation_grille(self):
        audit.self_test()


if __name__ == "__main__":
    unittest.main()
