import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import phase507_faed_terminal_aes_oracle as phase507


class Phase507Tests(unittest.TestCase):
    def test_source_universe_is_exact_and_unique(self):
        rows, hashes = phase507.source_candidates()
        self.assertEqual(len(rows), 43)
        self.assertEqual(len(hashes), 7)
        self.assertEqual(sum(len(row["provenance"]) for row in rows), 43)
        self.assertEqual(len({row["preimage_b64"] for row in rows}), 43)

    def test_targets_exclude_quarantined_urlblob(self):
        self.assertEqual(phase507.TARGETS,
                         ("SALPH", "COSMIC", "P32TRAILING"))
        self.assertNotIn("URLBLOB", phase507.TARGETS)

    def test_run_refuses_before_oracle_without_lock(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(phase507, "LOCK", Path(directory) / "none"), \
                mock.patch.object(phase507.oracle, "decrypt_padded",
                                  side_effect=AssertionError("oracle called")):
            with self.assertRaisesRegex(RuntimeError, "lock is absent"):
                phase507.run()

    def test_manifest_detects_source_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps({"wrong": True}) + "\n")
            with mock.patch.object(phase507, "MANIFEST", path):
                with self.assertRaisesRegex(RuntimeError, "manifest mismatch"):
                    phase507.validate_manifest()


if __name__ == "__main__":
    unittest.main()
