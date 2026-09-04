import tempfile
import unittest
from pathlib import Path

import phase467_closed_system_constraint_closure as phase467


class Phase467Tests(unittest.TestCase):
    def test_frozen_closure(self):
        report = phase467.build_report(phase467.load_manifest())
        phase467.self_test(report)
        self.assertEqual(report["verdict"], "no_executable_assignment_constraint_tie")
        self.assertFalse(report["transform_licensed"])

    def test_output_round_trip(self):
        report = phase467.build_report(phase467.load_manifest())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.json"
            path.write_text(__import__("json").dumps(report), encoding="utf-8")
            self.assertEqual(__import__("json").loads(path.read_text())["phase"], 467)


if __name__ == "__main__":
    unittest.main()
