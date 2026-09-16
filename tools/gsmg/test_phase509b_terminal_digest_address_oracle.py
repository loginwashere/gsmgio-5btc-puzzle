import tempfile
import unittest
from pathlib import Path
from unittest import mock

import phase509b_terminal_digest_address_oracle as phase509b


class Phase509BTests(unittest.TestCase):
    def test_self_test(self):
        self.assertEqual(phase509b.self_test()["exact_comparisons"], 172)

    def test_zero_and_out_of_range_scalars_rejected(self):
        self.assertIsNone(phase509b.derived_addresses(bytes(32)))
        value = phase509b.SECP256K1_ORDER.to_bytes(32, "big")
        self.assertIsNone(phase509b.derived_addresses(value))

    def test_run_refuses_before_any_derivation_without_lock(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(phase509b, "LOCK", Path(directory) / "none"), \
                mock.patch.object(phase509b, "derived_addresses",
                                  side_effect=AssertionError("consumer ran")):
            with self.assertRaisesRegex(RuntimeError, "lock is absent"):
                phase509b.run()

    def test_lock_budget_and_targets(self):
        payload = phase509b.lock_payload()
        self.assertEqual(payload["candidate_count"], 43)
        self.assertEqual(payload["derived_address_count"], 86)
        self.assertEqual(payload["exact_comparison_count"], 172)
        self.assertEqual(payload["targets"], list(phase509b.TARGETS))


if __name__ == "__main__":
    unittest.main()

