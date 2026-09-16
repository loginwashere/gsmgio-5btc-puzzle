import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

import phase490_width19_checkpointed_dual_lane as solver


class CheckpointedWidth19Tests(unittest.TestCase):
    def test_self_test(self):
        result = solver.self_test()
        self.assertTrue(result["checkpointed_per_depth"])
        self.assertFalse(result["faed_imported"])

    def test_atomic_population_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "population.npz"
            paths = np.asarray([[0, 1, 2], [2, 1, 0]], dtype=np.uint8)
            scores = np.asarray([-4.5, -4.25])
            solver.atomic_population(path, paths, scores)
            loaded = solver.load_population(path, min_depth=3, max_depth=3)
            np.testing.assert_array_equal(loaded[0], paths)
            np.testing.assert_array_equal(loaded[1], scores)
            self.assertFalse(path.with_suffix(".npz.tmp.npz").exists())

    def test_stage_commit_and_resume_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            source = work / "source.npz"
            solver.atomic_population(
                source, np.asarray([[0, 1, 2, 3]], dtype=np.uint8),
                np.asarray([-4.0]))
            output = solver.commit_stage(
                work, "sample", 14, "dev",
                np.asarray([[0, 1, 2, 3, 4]], dtype=np.uint8),
                np.asarray([-3.9]), {"depth": 5}, source)
            self.assertEqual(
                solver.completed_stage(work, "sample", 14, "dev", source),
                output)
            record_path = solver.stage_paths(work, "sample")[1]
            record = json.loads(record_path.read_text())
            record["schedule_sha256"] = "0" * 64
            solver.atomic_json(record_path, record)
            with self.assertRaisesRegex(RuntimeError, "wrong schedule_sha256"):
                solver.completed_stage(work, "sample", 14, "dev", source)

    def test_orphan_population_is_recomputed_not_resumed(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            output, _ = solver.stage_paths(work, "orphan")
            solver.atomic_population(
                output, np.asarray([[0, 1, 2, 3]], dtype=np.uint8),
                np.asarray([-4.0]))
            self.assertIsNone(
                solver.completed_stage(work, "orphan", 14, "dev"))

    def test_invalid_repeated_column_checkpoint_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.npz"
            np.savez(path, paths=np.asarray([[0, 1, 1, 2]], dtype=np.uint8),
                     scores=np.asarray([-4.0]))
            with self.assertRaisesRegex(ValueError, "repeated"):
                solver.load_population(path)


if __name__ == "__main__":
    unittest.main()
