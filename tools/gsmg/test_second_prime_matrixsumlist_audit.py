#!/usr/bin/env python3

import unittest

import second_prime_matrixsumlist_audit as audit


class SecondPrimeMatrixsumlistAuditTest(unittest.TestCase):
    def test_structural_chain_and_null(self):
        audit.self_test(run_oracle=False)


if __name__ == "__main__":
    unittest.main()
