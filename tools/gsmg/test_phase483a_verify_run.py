#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
import phase483a_invariant_order_statistic_probe as probe
import phase483a_verify_run as verifier

class Phase483AVerifierTests(unittest.TestCase):
    def test_reduced_result_fails_closed(self):
        lock = probe.lock_payload()
        result = probe.run_probe("holdout", fixtures=1, random_orders=1, corruptions=1)
        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / "lock.json"
            result_path = Path(directory) / "result.json"
            lock_path.write_text(json.dumps(lock), encoding="utf-8")
            result_path.write_text(json.dumps(result), encoding="utf-8")
            report = verifier.verify(lock_path, result_path)
        self.assertFalse(report["consistent"])
        self.assertFalse(report["checks"]["holdout_identity"])

if __name__ == "__main__":
    unittest.main()
