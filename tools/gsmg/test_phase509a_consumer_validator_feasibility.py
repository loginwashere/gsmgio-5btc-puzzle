import unittest

import phase509a_consumer_validator_feasibility as phase509a


class Phase509AConsumerValidatorTests(unittest.TestCase):
    def test_report_is_read_only_and_has_exact_coverage(self):
        result = phase509a.report()
        self.assertFalse(result["faed_scored"])
        self.assertFalse(result["gpu_used"])
        self.assertEqual(result["phase507_coverage"]["candidate_count"], 43)
        self.assertEqual(result["phase507_coverage"]["covered"]["decryptions"], 129)

    def test_terminal_validators_are_not_search_gradients(self):
        for validator in phase509a.validators():
            if validator["role"].startswith("terminal_confirmation"):
                self.assertEqual(validator["search_gradient"], "none")

    def test_shape_checks_do_not_promote(self):
        by_id = {row["id"]: row for row in phase509a.validators()}
        for name in ("raw_or_hex_scalar_shape", "base58check_container",
                     "wif_base58check", "bip39_checksum"):
            self.assertFalse(by_id[name]["eligible_for_promotion_alone"])

    def test_next_family_is_closed_and_exact(self):
        family = phase509a.recommended_next_family()
        self.assertEqual(family["derived_addresses"], 86)
        self.assertEqual(family["exact_address_comparisons"], 172)
        self.assertEqual(family["mutations"], "none")
        self.assertEqual(family["search_gradient"],
                         "none; exact terminal oracle only")


if __name__ == "__main__":
    unittest.main()

