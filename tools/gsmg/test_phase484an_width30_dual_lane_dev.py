import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import phase484ai_width30_early_switch_full_solve as full
import phase484an_width30_dual_lane_dev as subject


class DualLaneHelpersTest(unittest.TestCase):
    def test_schedule_freezes_both_independent_rescue_lanes(self):
        self.assertEqual(subject.SCHEDULE["keep_board"], 524288)
        self.assertEqual(subject.SCHEDULE["depth7_refine_keep"], 655360)
        self.assertEqual(subject.SCHEDULE["lane_a_depth8_children_per_parent"], 40)
        self.assertEqual(subject.SCHEDULE["lane_b_descendants_per_root"], 4)
        self.assertEqual(subject.SCHEDULE["lane_b_depth9_root_keep"], 262144)
        self.assertEqual(subject.SCHEDULE["lane_b_depth10_root_keep"], 65536)

    def test_prune_root_population_uses_best_descendant_and_remaps(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.npz"
            destination = root / "pruned.npz"
            paths = np.array([[0, 1], [0, 2], [1, 2], [1, 3], [2, 3]], dtype=np.uint8)
            scores = np.array([4.0, 1.0, 3.0, 2.0, 5.0])
            roots = np.array([0, 0, 1, 1, 2], dtype=np.int64)
            np.savez(source, paths=paths, scores=scores, root_ids=roots,
                     original_root_ids=np.array([10, 11, 12]))
            record = subject.prune_root_population(source, destination, 2)
            self.assertEqual(record["root_count_after"], 2)
            with np.load(destination) as payload:
                self.assertEqual(payload["root_ids"].tolist(), [0, 0, 1])
                self.assertEqual(payload["original_root_ids"].tolist(), [10, 12])
                self.assertEqual(payload["scores"].tolist(), [4.0, 1.0, 5.0])

    def test_merge_exact_deduplicates_and_keeps_best_score(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            a, b, output = root / "a.npz", root / "b.npz", root / "out.npz"
            np.savez(a, paths=np.array([[0, 1, 2, 3], [1, 2, 3, 4]], dtype=np.uint8),
                     scores=np.array([1.0, 3.0]))
            np.savez(b, paths=np.array([[0, 1, 2, 3], [2, 3, 4, 5]], dtype=np.uint8),
                     scores=np.array([5.0, 2.0]))
            record = subject.merge_populations([a, b], output, 2)
            self.assertEqual(record["unique_before_cut"], 3)
            with np.load(output) as payload:
                got = {tuple(path): score for path, score in
                       zip(payload["paths"], payload["scores"])}
            self.assertEqual(got, {(0, 1, 2, 3): 5.0, (1, 2, 3, 4): 3.0})

    def test_initial_schedule_rejects_missing_keys_before_fixture_work(self):
        with self.assertRaisesRegex(ValueError, "missing keys"):
            full.initial_to_depth7(0, Path("unused"), schedule={})


if __name__ == "__main__":
    unittest.main()
