import unittest

import phase466_phase1_credential_crib_audit as audit


class Phase466Test(unittest.TestCase):
    def test_self_test(self):
        audit.self_test()

    def test_family_and_oracle_invariants(self):
        result = audit.audit()
        self.assertEqual(len(result["families"]), 6)
        self.assertEqual(result["oracle_calls"], 0)
        self.assertEqual(result["password_candidates"], 0)
        for family in result["families"]:
            self.assertEqual(len(family["offsets"]), family["crib_length"])


if __name__ == "__main__":
    unittest.main()
