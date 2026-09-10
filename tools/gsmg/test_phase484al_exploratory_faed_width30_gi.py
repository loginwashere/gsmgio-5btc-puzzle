import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484al_exploratory_faed_width30_gi as subject


class Phase484ALTests(unittest.TestCase):
    def test_input_and_schedule_are_pinned(self):
        result = subject.self_test()
        self.assertEqual(result["raw_length"], 570)
        self.assertEqual(result["token_length"], 436)
        self.assertEqual(result["single_slots"], 302)
        self.assertEqual(result["pair"], ["g", "i"])

    def test_fixture_adapter_contains_real_observed_without_claimed_truth(self):
        fixture = subject.real_fixture()
        self.assertEqual(fixture["observed"], subject.FAED)
        self.assertEqual(fixture["plaintext"], "?" * 436)
        self.assertEqual(fixture["order"], list(range(30)))

    def test_adapter_policy_is_exercised_by_run(self):
        original = subject.width30.width30_fixture
        seen = {}

        def fake_pipeline(index, directory):
            provider = subject.width30.width30_fixture
            seen["real"] = provider(index, "dev")
            seen["training"] = provider(subject.width30.TRAIN_INDICES[0], "dev")
            with self.assertRaises(RuntimeError):
                provider(22, "dev")
            raise RuntimeError("canary")

        with tempfile.TemporaryDirectory() as directory, \
             mock.patch.object(subject, "verify_lock", return_value={}), \
             mock.patch.object(subject.full, "run_fixture", side_effect=fake_pipeline):
            with self.assertRaisesRegex(RuntimeError, "canary"):
                subject.run(Path(directory))
        self.assertEqual(seen["real"]["observed"], subject.FAED)
        self.assertNotEqual(seen["training"]["fixture_index"],
                            subject.SENTINEL_FIXTURE_INDEX)
        self.assertIs(subject.width30.width30_fixture, original)

    def test_run_restores_fixture_provider_on_pipeline_error(self):
        original = subject.width30.width30_fixture
        with tempfile.TemporaryDirectory() as directory, \
             mock.patch.object(subject, "verify_lock", return_value={}), \
             mock.patch.object(subject.full, "run_fixture",
                               side_effect=RuntimeError("canary")):
            with self.assertRaisesRegex(RuntimeError, "canary"):
                subject.run(Path(directory))
        self.assertIs(subject.width30.width30_fixture, original)

    def test_lock_payload_pins_one_run_and_nonclosing_miss(self):
        payload = subject.lock_payload()
        self.assertEqual(payload["run_count"], 1)
        self.assertEqual(payload["negative_scope"],
                         "nonclosing_without_holdout_power")
        self.assertEqual(payload["schedule_sha256"], subject.full.schedule_sha256())


if __name__ == "__main__":
    unittest.main()
