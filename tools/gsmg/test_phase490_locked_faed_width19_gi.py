import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

import phase490_locked_faed_width19_gi as real
import phase490_width19_checkpointed_dual_lane as continuation


class Phase490LockedRealTests(unittest.TestCase):
    def test_self_test(self):
        result = real.self_test()
        self.assertEqual(result["width"], 19)
        self.assertEqual(result["token_length_in_observed_order"], 436)
        self.assertTrue(result["checkpointed"])

    def test_lock_payload_is_one_run_and_nonclosing(self):
        payload = real.lock_payload()
        self.assertEqual(payload["run_count"], 1)
        self.assertEqual(payload["input"]["pair"], ["g", "i"])
        self.assertEqual(payload["negative_scope"], "one_seed_exploratory_miss_only")
        self.assertEqual(len(payload["binaries_sha256"]), 3)

    def test_real_fixture_is_exact_width19_grid(self):
        fixture = real.real_fixture()
        self.assertEqual(len(fixture["observed"]), 19 * 30)
        self.assertEqual(fixture["order"], list(range(19)))
        self.assertEqual(fixture["plaintext"], "?" * 436)

    def test_sanitize_removes_false_truth_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "continuation" / "final_resolve.json"
            stage.parent.mkdir()
            stage.write_text(json.dumps({
                "status": "development_final_resolve_complete",
                "faed_scored": False,
                "exact_order_final_rank": 1,
                "top1_exact_order": True,
                "top1_plaintext_accuracy": 0.0,
                "final_candidates": [{
                    "plaintext": "ABC", "is_exact_order": True,
                    "plaintext_accuracy": 0.0,
                }],
            }))
            real.sanitize_stage_records(root)
            cleaned = json.loads(stage.read_text())
            self.assertTrue(cleaned["faed_scored"])
            self.assertNotIn("exact_order_final_rank", cleaned)
            self.assertNotIn("is_exact_order", cleaned["final_candidates"][0])

    def test_all_terminal_records_are_exposed_by_source(self):
        source = Path(continuation.__file__).read_text()
        self.assertIn('"terminal_candidates": terminals', source)
        self.assertIn('"skipped_terminals": skipped', source)

    def test_front_checkpoint_fails_closed_on_hash_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            population = root / "depth7_refined.npz"
            continuation.atomic_population(
                population, np.asarray([[0, 1, 2, 3, 4, 5, 6]], dtype=np.uint8),
                np.asarray([-1.0]))
            front_record = root / "result.json"
            front_record.write_text("{}\n")
            checkpoint = {
                "phase": "490R", "stage": "front_depth7_refined",
                "faed_scored": True,
                "sentinel_diagnostics_are_evidential": False,
                "execution_lock_sha256": "not-the-real-lock",
                "population_sha256": real.sha256_file(population),
                "front_record_sha256": real.sha256_file(front_record),
                "front_schedule_sha256": real.front.schedule_sha256(),
            }
            (root / "real_front_checkpoint.json").write_text(json.dumps(checkpoint))
            temporary_lock = root / "lock.json"
            temporary_lock.write_text("{}\n")
            with mock.patch.object(real, "LOCK", temporary_lock):
                with self.assertRaises(RuntimeError):
                    real.validate_front_checkpoint(root)


if __name__ == "__main__":
    unittest.main()
