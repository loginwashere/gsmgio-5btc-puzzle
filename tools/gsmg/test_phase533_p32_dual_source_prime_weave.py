import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase533_p32_dual_source_prime_weave as phase533


class Phase533Tests(unittest.TestCase):
    def test_frozen_manifest(self):
        phase533.self_test()

    def test_eight_unique_bases(self):
        bases = phase533.build_bases()
        self.assertEqual(len(bases), 8)
        self.assertEqual(len({base["value"] for base in bases}), 8)

    def test_material_treatments_are_exactly_raw_and_sha256_hex(self):
        records = phase533.build_material_records()
        self.assertEqual(len(records), 16)
        by_source = {}
        for record in records:
            by_source.setdefault(record["sources"][0], set()).update(record["treatments"])
        self.assertEqual(set(by_source), {base["label"] for base in phase533.build_bases()})
        self.assertTrue(all(treatments == {"raw", "sha256-hex"} for treatments in by_source.values()))

    def test_lock_payload_pins_trial_count(self):
        payload = phase533.lock_payload()
        self.assertEqual(payload["base_count"], 8)
        self.assertEqual(payload["fresh_material_count"], 16)
        self.assertEqual(payload["expected_trial_count"], 96)

    def test_lock_tamper_fails_closed(self):
        if phase533.LOCK_PATH.exists():
            self.skipTest("real execution lock exists; do not mutate it")
        payload = phase533.lock_payload()
        payload["base_count"] = 9
        phase533.LOCK_PATH.write_text(json.dumps(payload))
        try:
            with self.assertRaises(RuntimeError):
                phase533.verify_lock()
        finally:
            phase533.LOCK_PATH.unlink()


if __name__ == "__main__":
    unittest.main()
