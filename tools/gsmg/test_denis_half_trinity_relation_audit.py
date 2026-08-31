#!/usr/bin/env python3

import unittest

import denis_half_trinity_relation_audit as audit


class DenisHalfTrinityRelationAuditTest(unittest.TestCase):
    def test_relation(self):
        audit.self_test()


if __name__ == "__main__":
    unittest.main()
