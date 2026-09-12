import itertools, sys, unittest
import json, tempfile
from pathlib import Path
import numpy as np
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import phase484y_width30_blind_joint_solver as subject


class Phase484YBlindJointTests(unittest.TestCase):
    def test_initial_board_is_permutation(self):
        self.assertEqual(sorted(subject.initial_board(subject.SEED, (7, 3, 11, 2)).tolist()), list(range(25)))

    def test_fragment_seed_depends_on_path_not_shortlist_position(self):
        path = (7, 3, 11, 2)
        self.assertEqual(subject.fragment_seed(subject.SEED, path), subject.fragment_seed(subject.SEED, tuple(path)))
        self.assertNotEqual(subject.fragment_seed(subject.SEED, path), subject.fragment_seed(subject.SEED, (3, 7, 11, 2)))

    def test_cpu_recompute_uses_the_coarse_kernels_own_canonical_convention(self):
        fixture = subject.width30.width30_fixture(13)
        blocks = subject.prefix.blocks_from_observed(fixture)
        pair = tuple(fixture["pair"])
        quad, _ = subject.base.load_language_model()
        path = next(itertools.permutations(range(subject.WIDTH), subject.DEPTH))
        board = np.arange(25)
        score, windows = subject.cpu_recompute(blocks, pair, quad, path, board)
        rows = subject.canonical_token_rows(blocks, pair, path)
        self.assertEqual(windows, sum(max(0, len(row) - 3) for row in rows))
        self.assertTrue(np.isfinite(score))

    def test_canonical_token_rows_differs_from_absolute_alphabet_convention_for_gi(self):
        # Regression guard for the convention mismatch the self-test caught:
        # canonical_token_rows (matches the coarse/extend kernels) must NOT
        # coincide with partial.token_rows (true absolute-alphabet slots)
        # for a non-{a,b} pair, or cpu_recompute would silently verify the
        # wrong thing again.
        fixture = subject.width30.width30_fixture(13)
        blocks = subject.prefix.blocks_from_observed(fixture)
        pair = tuple(fixture["pair"])
        self.assertNotEqual(pair, ("a", "b"))
        path = next(itertools.permutations(range(subject.WIDTH), subject.DEPTH))
        canonical = subject.canonical_token_rows(blocks, pair, path)
        absolute = subject.partial.token_rows(blocks, pair, path)
        self.assertFalse(all(np.array_equal(c, a) for c, a in zip(canonical, absolute)))

    def test_multistart_keeps_each_paths_best_score(self):
        old = subject.gpu_coarse_screen
        try:
            calls = []

            def fake(*args, **kwargs):
                restart = len(calls)
                calls.append(restart)
                scores = np.array([restart, 2 - restart], dtype=float)
                return scores, np.array([3, 4]), np.tile(np.arange(25, dtype=np.uint8), (2, 1))

            subject.gpu_coarse_screen = fake
            scores, windows, boards, restarts = subject.gpu_multistart_screen(None, None, None, None, [(), ()], restarts=3)
            np.testing.assert_array_equal(scores, [2, 2])
            np.testing.assert_array_equal(windows, [3, 4])
            np.testing.assert_array_equal(restarts, [2, 0])
        finally:
            subject.gpu_coarse_screen = old

    def test_extend_population_deduplicates_terminal_orders(self):
        fake_extend = lambda blocks, pair, quad, record, binary, beam_width: ([(2.0, (0, 1)), (1.0, (1, 0))], [])
        records = [{"rank": 1, "shortlist_index": 3}, {"rank": 2, "shortlist_index": 4}]
        terminal, diagnostics = subject.extend_population(
            fake_extend, None, None, None, records, None, seed_count=2, terminals_per_seed=2)
        self.assertEqual(len(terminal), 2)
        self.assertEqual(terminal[0]["extension_rank"], 1)
        self.assertEqual(len(diagnostics), 2)

    def test_extension_backend_rejects_unknown_name(self):
        with self.assertRaisesRegex(ValueError, "unknown extension backend"):
            subject.run_extension_backend(None, None, None, [], backend="bogus")

    def test_extension_backend_defaults_to_reanneal(self):
        old = subject.extend_population
        captured = {}
        try:
            def fake(extend_fn, blocks, pair, quad, refined, binary, **kwargs):
                captured["extend_fn"] = extend_fn
                captured["binary"] = binary
                return [], []

            subject.extend_population = fake
            subject.run_extension_backend(None, None, None, [], coarse_binary="COARSE", board_binary="FROZEN")
            self.assertEqual(captured["binary"], "COARSE")
            self.assertIs(captured["extend_fn"].func, subject.extend_seed_reanneal)
        finally:
            subject.extend_population = old

    def test_pooled_backend_records_reanneal_budget(self):
        self.assertTrue(subject.records_reanneal_budget("reanneal"))
        self.assertTrue(subject.records_reanneal_budget("pooled_reanneal"))
        self.assertFalse(subject.records_reanneal_budget("frozen"))

    def test_extension_backend_frozen_uses_extend_seed_and_board_binary(self):
        old = subject.extend_population
        captured = {}
        try:
            def fake(extend_fn, blocks, pair, quad, refined, binary, **kwargs):
                captured["extend_fn"] = extend_fn
                captured["binary"] = binary
                return [], []

            subject.extend_population = fake
            subject.run_extension_backend(
                None, None, None, [], backend="frozen", coarse_binary="COARSE", board_binary="FROZEN")
            self.assertEqual(captured["binary"], "FROZEN")
            self.assertIs(captured["extend_fn"], subject.extend_seed)
        finally:
            subject.extend_population = old

    def test_extend_seed_reanneal_calls_gpu_multistart_screen_at_every_depth(self):
        old = subject.gpu_multistart_screen
        calls = []
        try:
            def fake(binary, blocks, pair, quad, paths, restarts, iterations):
                calls.append(len(paths))
                n = len(paths)
                return (np.arange(n, dtype=float), np.full(n, 4), np.tile(np.arange(25, dtype=np.uint8), (n, 1)), np.zeros(n, dtype=np.int64))

            subject.gpu_multistart_screen = fake
            record = {"path": tuple(range(subject.DEPTH)), "normalized_score": 0.0}
            beam, diagnostics = subject.extend_seed_reanneal(None, ("g", "i"), None, record, beam_width=4)
            self.assertEqual(len(diagnostics), subject.WIDTH - subject.DEPTH)
            self.assertEqual(len(calls), subject.WIDTH - subject.DEPTH)
            self.assertTrue(len(beam) <= 4)
        finally:
            subject.gpu_multistart_screen = old

    def test_pooled_reanneal_uses_one_shared_bounded_population(self):
        old = subject.gpu_multistart_screen
        calls = []
        try:
            def fake(binary, blocks, pair, quad, paths, restarts, iterations):
                calls.append(len(paths))
                n = len(paths)
                return (np.arange(n, dtype=float), np.full(n, 4),
                        np.tile(np.arange(25, dtype=np.uint8), (n, 1)),
                        np.zeros(n, dtype=np.int64))
            subject.gpu_multistart_screen = fake
            refined = [
                {"rank": rank + 1, "path": list(range(rank, rank + 8)),
                 "normalized_score": float(rank), "shortlist_index": rank}
                for rank in range(3)
            ]
            terminals, diagnostics = subject.extend_pooled_reanneal(
                None, ("g", "i"), None, refined, seed_count=3,
                beam_width=4, terminals_per_seed=2)
            self.assertEqual(len(calls), subject.WIDTH - subject.DEPTH)
            self.assertEqual(diagnostics[0]["pooled_seed_count"], 3)
            self.assertLessEqual(len(terminals), 2)
        finally:
            subject.gpu_multistart_screen = old

    def test_shortlist_capacity_only_expands_final_depth(self):
        self.assertEqual(subject.shortlist_capacity(subject.DEPTH - 1, 262144, 1048576), 262144)
        self.assertEqual(subject.shortlist_capacity(subject.DEPTH, 262144, 1048576), 1048576)

    def test_proven_final_shortlist_is_the_default(self):
        self.assertEqual(subject.build_depth8_shortlist.__defaults__[1],
                         subject.FINAL_SHORTLIST_KEEP)
        self.assertEqual(subject.screen_fixture.__defaults__[-1],
                         subject.FINAL_SHORTLIST_KEEP)

    def test_load_true_refined_seed_chooses_best_true_rank(self):
        payload = {"fixture_index": 16, "refined_population": [
            {"rank": 7, "is_true_segment": True, "path": list(range(8))},
            {"rank": 1, "is_true_segment": True, "path": list(range(1, 9))},
            {"rank": 2, "is_true_segment": False, "path": list(range(2, 10))},
        ]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.json"
            path.write_text(json.dumps(payload))
            source, record = subject.load_true_refined_seed(path)
        self.assertEqual(source["fixture_index"], 16)
        self.assertEqual(record["rank"], 1)

    def test_screen_observed_rejects_wrong_length(self):
        with self.assertRaisesRegex(ValueError, "570 symbols"):
            subject.screen_observed("abc")

    def test_screen_observed_rejects_symbols_outside_nine_letter_alphabet(self):
        with self.assertRaisesRegex(ValueError, "outside a-i"):
            subject.screen_observed("z" * subject.base.RAW_LENGTH)

    def test_complete_token_slots_uses_width30_row_count(self):
        fixture = subject.width30.width30_fixture(13)
        blocks = subject.prefix.blocks_from_observed(fixture)
        pair = tuple(fixture["pair"])
        truth = subject.prefix.order_to_sequence(fixture["order"])
        self.assertEqual(len(blocks[0]), subject.ROWS)
        good = subject.complete_token_slots(blocks, pair, truth, strict=False)
        self.assertIsNotNone(good)

    def test_complete_token_slots_nonstrict_returns_none_on_failed_segmentation(self):
        fixture = subject.width30.width30_fixture(13)
        blocks = subject.prefix.blocks_from_observed(fixture)
        pair = tuple(fixture["pair"])
        truth = subject.prefix.order_to_sequence(fixture["order"])
        old = subject.base.segment_raw
        try:
            subject.base.segment_raw = lambda raw, pair: None
            self.assertIsNone(subject.complete_token_slots(blocks, pair, truth, strict=False))
            with self.assertRaises(ValueError):
                subject.complete_token_slots(blocks, pair, truth, strict=True)
        finally:
            subject.base.segment_raw = old

    def test_resolve_terminals_skips_invalid_segmentations_instead_of_crashing(self):
        old_complete, old_multistart = subject.complete_token_slots, subject.gpu_full_multistart
        try:
            def fake_complete(blocks, pair, order, strict=True):
                return None if order == (0,) else np.array([1, 2, 3, 4], dtype=np.int64)

            subject.complete_token_slots = fake_complete

            def fake_multistart(binary, token_rows, quad, restarts, iterations, seed=None):
                n = len(token_rows)
                return np.arange(n, dtype=float), np.tile(np.arange(25, dtype=np.uint8), (n, 1)), np.zeros(n, dtype=np.int64)

            subject.gpu_full_multistart = fake_multistart
            terminals = [{"order": (0,), "extension_rank": 1}, {"order": (1,), "extension_rank": 2}, {"order": (2,), "extension_rank": 3}]
            ranked, skipped = subject.resolve_terminals(None, None, None, terminals)
            self.assertEqual([r["order"] for r in skipped], [(0,)])
            self.assertEqual(len(ranked), 2)
            self.assertEqual(ranked[0]["order"], (2,))
            self.assertEqual(ranked[1]["order"], (1,))
        finally:
            subject.complete_token_slots, subject.gpu_full_multistart = old_complete, old_multistart

    def test_resolve_terminals_skips_all_returns_empty_ranked(self):
        old_complete = subject.complete_token_slots
        try:
            subject.complete_token_slots = lambda blocks, pair, order, strict=True: None
            ranked, skipped = subject.resolve_terminals(None, None, None, [{"order": (0,), "extension_rank": 1}])
            self.assertEqual(ranked, [])
            self.assertEqual(len(skipped), 1)
        finally:
            subject.complete_token_slots = old_complete


if __name__ == "__main__":
    unittest.main()
