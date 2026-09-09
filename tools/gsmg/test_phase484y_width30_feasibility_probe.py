import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484y_width30_feasibility_probe as subject


class Phase484YTests(unittest.TestCase):
    def test_width30_fixture_roundtrip_and_profile(self):
        fixture = subject.width30_fixture(13)
        self.assertEqual(fixture["width"], 30)
        self.assertEqual(len(fixture["observed"]), 570)
        subject.exact.verify_exact_profile(fixture)

    def test_packed_keys_are_distinct_for_distinct_paths(self):
        paths = np.asarray([[0, 1, 2, 3], [0, 1, 3, 2], [29, 28, 27, 26]],
                           dtype=np.uint8)
        self.assertEqual(len(set(subject.packed_keys(paths).tolist())), 3)

    def test_depth13_paths_do_not_collide_during_deduplication(self):
        # The old uint64 key silently discarded the first five bits here.
        paths = np.asarray([
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            [29, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        ], dtype=np.uint8)
        with self.assertRaisesRegex(ValueError, "depth 12"):
            subject.packed_keys(paths)
        selected, _, unique = subject.select_diverse(
            paths, np.asarray([1.0, 2.0]), keep=2)
        self.assertEqual(unique, 2)
        self.assertEqual(len(selected), 2)

    def test_initial_path_counts(self):
        self.assertEqual(subject.initial_paths(4).shape, (657720, 4))

    def test_chunked_scoring_preserves_order(self):
        class Fake:
            def score(self, paths):
                return paths[:, 0].astype(float)
        paths = np.arange(30, dtype=np.uint8).reshape(10, 3)
        np.testing.assert_array_equal(
            subject.score_chunked(Fake(), paths, chunk_size=4),
            paths[:, 0].astype(float))

    def test_bidirectional_expansion_count_and_uniqueness(self):
        parents = np.asarray([[0, 1, 2, 3], [1, 2, 3, 4]], dtype=np.uint8)
        expanded = subject.expand_bidirectional(parents)
        self.assertEqual(len(expanded), 2 * 2 * (30 - 4))
        self.assertEqual(len(np.unique(subject.packed_keys(expanded))),
                         2 * 2 * (30 - 4) - 1)

    def test_selector_deduplicates_and_respects_capacity(self):
        paths = np.asarray([[0, 1, 2, 3], [0, 1, 2, 3],
                            [1, 2, 3, 4], [2, 3, 4, 5]], dtype=np.uint8)
        scores = np.asarray([1.0, 1.0, 3.0, 2.0])
        selected, selected_scores, unique = subject.select_diverse(paths, scores, 2)
        self.assertEqual(unique, 3)
        self.assertEqual(len(selected), 2)
        self.assertEqual(len(np.unique(subject.packed_keys(selected))), 2)
        self.assertEqual(selected_scores.tolist(), [3.0, 2.0])

    def test_selector_matches_established_reference(self):
        rng = np.random.default_rng(48430)
        paths = np.asarray([rng.choice(30, 4, replace=False)
                            for _ in range(300)], dtype=np.uint8)
        paths = np.vstack([paths, paths[:20]])
        scores = rng.normal(size=len(paths))
        scores[-20:] = scores[:20]
        selected, selected_scores, _ = subject.select_diverse(paths, scores, 80)
        candidates = {}
        for path, score in zip(paths, scores):
            candidates[tuple(int(value) for value in path)] = float(score)
        expected = subject.bidi.select_diverse(candidates, 30, beam_width=80)
        self.assertEqual([tuple(row) for row in selected.tolist()],
                         [path for _, path in expected])
        np.testing.assert_allclose(selected_scores,
                                   [score for score, _ in expected])

    def test_generated_true_metrics_rank(self):
        truth = [0, 1, 2, 3, 4]
        paths = np.asarray([[0, 1, 2, 3], [1, 2, 3, 4],
                            [5, 6, 7, 8]], dtype=np.uint8)
        count, rank = subject.generated_true_metrics(
            paths, np.asarray([1.0, 3.0, 2.0]), truth, 4)
        self.assertEqual(count, 2)
        self.assertEqual(rank, 1)


if __name__ == "__main__":
    unittest.main()
