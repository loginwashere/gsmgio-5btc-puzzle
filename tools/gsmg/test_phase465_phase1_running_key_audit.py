import unittest

import phase465_phase1_running_key_audit as audit


class Phase465Test(unittest.TestCase):
    def test_self_test(self):
        audit.self_test()

    def test_structural_family_is_frozen_and_oracle_free(self):
        result = audit.audit(run_tier2=False)
        self.assertEqual(len(result["structural_configs"]), 16)
        self.assertEqual(result["key_lengths"], {
            "full_credential": 53,
            "continuation_after_theflower": 44,
        })
        self.assertEqual(result["oracle_calls"], 0)
        self.assertEqual(result["password_candidates"], 0)
        for config in result["structural_configs"]:
            self.assertEqual(
                len(config["ranked_offsets"]), config["valid_offset_count"]
            )
            ranks = [row["structural_rank"] for row in config["ranked_offsets"]]
            self.assertEqual(ranks, list(range(1, len(ranks) + 1)))


if __name__ == "__main__":
    unittest.main()
