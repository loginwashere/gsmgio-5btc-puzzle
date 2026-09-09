#!/usr/bin/env python3

import sys
import unittest

import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase484a_raw_symbol_vic_solver as audit


class Phase484ARawSymbolInfrastructureTests(unittest.TestCase):
    def test_exact_widths(self):
        self.assertEqual(audit.EXACT_WIDTHS, (2, 3, 5, 6, 10, 15, 19, 30, 38))

    def test_geometry_roundtrip_all_widths(self):
        raw = (audit.NINE_SYMBOLS * 64)[:audit.RAW_LENGTH]
        for width in audit.WIDTHS:
            geometry = audit.Geometry(len(raw), width)
            for order in (tuple(range(width)), tuple(reversed(range(width)))):
                observed = geometry.encrypt(raw, order)
                self.assertEqual(geometry.decrypt(observed, order), raw)
                self.assertEqual(sorted(observed), sorted(raw))

    def test_ragged_column_lengths(self):
        geometry = audit.Geometry(570, 7)
        self.assertEqual(geometry.rows, 82)
        self.assertEqual(geometry.column_lengths, (82, 82, 82, 81, 81, 81, 81))
        self.assertEqual(sum(geometry.column_lengths), 570)

    def test_every_escape_pair_has_25_unique_codes(self):
        self.assertEqual(len(audit.ESCAPE_PAIRS), 36)
        for pair in audit.ESCAPE_PAIRS:
            codes = audit.slot_codes(pair)
            self.assertEqual(len(codes), 25)
            self.assertEqual(len(set(codes)), 25)
            self.assertEqual(audit.segment_raw("".join(codes), pair), codes)

    def test_dangling_escape_is_invalid(self):
        self.assertIsNone(audit.segment_raw("abcg", ("g", "i")))

    def test_fixture_is_exact_570_and_roundtrips(self):
        for width, pair_index in ((7, 0), (15, 12), (19, 24), (38, 35)):
            fixture = audit.make_fixture(width, pair_index, fixture_index=3)
            audit.verify_fixture(fixture)
            self.assertEqual(len(fixture["raw"]), 570)
            self.assertNotEqual(fixture["plaintext_length"], 436)

    def test_both_board_modes_roundtrip(self):
        for mode in audit.BOARD_MODES:
            fixture = audit.make_fixture(15, 0, 4, board_mode=mode)
            audit.verify_fixture(fixture)
            self.assertEqual(fixture["board_mode"], mode)

    def test_vic_profile_puts_training_top_seven_in_single_slots(self):
        fixture = audit.make_fixture(15, 0, 5, board_mode="vic_profile")
        singles = set(audit.slot_codes(tuple(fixture["pair"]))[:7])
        assigned = {letter for letter, code in fixture["letter_to_code"].items() if code in singles}
        training = audit.corpus_splits()["train"]
        frequencies = {letter: training.count(letter) for letter in audit.LETTER_ALPHABET}
        expected = set(sorted(audit.LETTER_ALPHABET,
                              key=lambda letter: (-frequencies[letter], letter))[:7])
        self.assertEqual(assigned, expected)

    def test_fixtures_start_at_word_boundaries(self):
        fixture = audit.make_fixture(15, 0, 12)
        self.assertIn(fixture["source_start"], audit.corpus_word_starts("dev"))

    def test_corpus_splits_are_disjoint_by_gap(self):
        splits = audit.corpus_splits()
        self.assertTrue(all(splits.values()))
        self.assertNotEqual(splits["train"][-100:], splits["dev"][:100])
        self.assertNotEqual(splits["dev"][-100:], splits["holdout"][:100])

    def test_spectral_features_are_label_permutation_invariant(self):
        pair = ("a", "b")
        tokens = audit.slot_codes(pair)
        sequence = tuple(tokens[(index * 7 + index // 3) % 25] for index in range(200))
        matrix = audit.transition_matrix(sequence, pair)
        permutation = list(reversed(range(25)))
        renamed = matrix[permutation][:, permutation]
        np.testing.assert_allclose(audit.spectral_features(matrix),
                                   audit.spectral_features(renamed), atol=1e-12)

    def test_random_order_rank_is_deterministic(self):
        fixture = audit.make_fixture(15, 0, 6)
        model = audit.SpectralModel.from_training_corpus()
        first = audit.random_order_rank(fixture, model, 20, 12345)
        second = audit.random_order_rank(fixture, model, 20, 12345)
        self.assertEqual(first, second)

    def test_exact_enumerator_accounts_for_every_order(self):
        fixture = audit.make_fixture(5, 0, 8)
        result = audit.enumerate_orders_by_spectral(
            fixture["observed"], 5, tuple(fixture["pair"]),
            audit.SpectralModel.from_training_corpus(), keep=16,
        )
        self.assertEqual(result["orders_total"], 120)
        self.assertEqual(result["valid_orders"] + result["invalid_segmentations"], 120)
        self.assertEqual(len(result["shortlist"]), 16)

    def test_exact_enumerator_rejects_unbounded_width(self):
        fixture = audit.make_fixture(10, 0, 1)
        with self.assertRaises(ValueError):
            audit.enumerate_orders_by_spectral(
                fixture["observed"], 10, tuple(fixture["pair"]),
                audit.SpectralModel.from_training_corpus(), keep=1,
            )

    def test_joint_enumerator_accounts_for_all_pair_orders(self):
        fixture = audit.make_fixture(2, pair_index=7, fixture_index=1)
        result = audit.enumerate_pair_orders_by_spectral(
            fixture["observed"], 2, audit.SpectralModel.from_training_corpus()
        )
        self.assertEqual(result["hypotheses_total"], 36 * 2)
        self.assertEqual(
            result["valid_hypotheses"] + result["invalid_segmentations"],
            result["hypotheses_total"],
        )

    def test_planted_joint_spectral_rank_finds_fixture(self):
        fixture = audit.make_fixture(2, pair_index=7, fixture_index=1)
        result = audit.planted_joint_spectral_rank(
            fixture, audit.SpectralModel.from_training_corpus()
        )
        self.assertGreaterEqual(result["rank"], 1)
        self.assertLessEqual(result["rank"], result["valid_hypotheses"])

    def test_joint_rank_batch_is_dev_only_and_self_describing(self):
        result = audit.run_joint_rank_batch(
            widths=(2,), fixtures_per_cell=1, fixture_index_start=25,
            board_modes=("broad_random",),
        )
        self.assertFalse(result["faed_scored"])
        self.assertEqual(result["fixture_split"], "dev")
        self.assertEqual(result["cells"][0]["fixture_count"], 1)
        with self.assertRaises(ValueError):
            audit.run_joint_rank_batch(
                widths=(2,), fixtures_per_cell=1, fixture_index_start=0,
                split="holdout",
            )

    def test_fixture_is_deterministic(self):
        first = audit.make_fixture(15, 28, 9)
        second = audit.make_fixture(15, 28, 9)
        self.assertEqual(first, second)

    def test_fixture_split_is_explicit_and_disjoint(self):
        dev = audit.make_fixture(3, 0, 2, split="dev")
        holdout = audit.make_fixture(3, 0, 2, seed=audit.SEED_HOLDOUT,
                                     split="holdout")
        self.assertEqual(dev["split"], "dev")
        self.assertEqual(holdout["split"], "holdout")
        self.assertNotEqual(dev["plaintext"], holdout["plaintext"])
        with self.assertRaises(ValueError):
            audit.make_fixture(3, 0, 2, split="unknown")

    def test_invalid_orders_fail_closed(self):
        geometry = audit.Geometry(570, 10)
        with self.assertRaises(ValueError):
            geometry.encrypt("a" * 570, [0] * 10)
        with self.assertRaises(ValueError):
            geometry.decrypt("a" * 570, range(9))


class Phase484ABoardSolverTests(unittest.TestCase):
    def test_quadgram_table_shape_and_floor(self):
        quad, floor = audit.load_language_model()
        self.assertEqual(quad.shape[0], 25 ** 4)
        self.assertTrue(np.any(quad > floor))
        self.assertAlmostEqual(quad.min(), floor)

    def test_kendall_tau_identity_and_reversal(self):
        identity = list(range(6))
        self.assertAlmostEqual(audit.kendall_tau(identity, identity), 1.0)
        self.assertAlmostEqual(audit.kendall_tau(identity, list(reversed(identity))), -1.0)

    def test_kendall_tau_width_one_is_defined(self):
        self.assertEqual(audit.kendall_tau([0], [0]), 1.0)

    def test_anneal_board_zero_iters_returns_key0_unchanged(self):
        quad, _ = audit.load_language_model()
        rng = audit.PCG32(1)
        key0 = np.array(rng.permutation(25), dtype=np.int64)
        token_slots = np.array([0, 1, 2, 3, 4] * 20, dtype=np.int64)
        key, score = audit.anneal_board(token_slots, quad, rng, iters=0, t0=20.0, t1=1.0, key0=key0)
        np.testing.assert_array_equal(key, key0)
        self.assertAlmostEqual(score, audit.score_indices(key0[token_slots], quad))

    def test_anneal_board_never_returns_worse_than_initial(self):
        quad, _ = audit.load_language_model()
        fixture = audit.make_fixture(width=3, pair_index=0, fixture_index=0)
        pair = tuple(fixture["pair"])
        codes = audit.slot_codes(pair)
        code_to_slot = {code: index for index, code in enumerate(codes)}
        segmented = audit.segment_raw(fixture["raw"], pair)
        token_slots = np.array([code_to_slot[c] for c in segmented], dtype=np.int64)
        rng = audit.PCG32(7)
        key0 = np.array(rng.permutation(25), dtype=np.int64)
        initial_score = audit.score_indices(key0[token_slots], quad)
        _, best_score = audit.anneal_board(token_slots, quad, rng, iters=500,
                                           t0=20.0, t1=1.0, key0=key0.copy())
        self.assertGreaterEqual(best_score, initial_score)

    def test_solve_fixture_returns_consistent_recovery_metrics(self):
        model = audit.SpectralModel.from_training_corpus()
        quad, _ = audit.load_language_model()
        fixture = audit.make_fixture(width=3, pair_index=0, fixture_index=0)
        result = audit.solve_fixture(fixture, model, quad, shortlist_keep=6,
                                     board_restarts=1, board_iters=300, seed=99)
        self.assertTrue(result["solved"])
        self.assertGreaterEqual(result["valid_candidates"], 1)
        self.assertLessEqual(result["valid_candidates"], result["shortlist_size"])
        self.assertIn(result["exact_order_recovery"], (True, False))
        self.assertGreaterEqual(result["kendall_tau"], -1.0)
        self.assertLessEqual(result["kendall_tau"], 1.0)
        self.assertGreaterEqual(result["board_accuracy"], 0.0)
        self.assertLessEqual(result["board_accuracy"], 1.0)
        self.assertGreaterEqual(result["plaintext_char_accuracy"], 0.0)
        self.assertLessEqual(result["plaintext_char_accuracy"], 1.0)
        if result["exact_order_recovery"]:
            self.assertEqual(result["decoded_length_error"], 0)

    def test_solve_fixture_blind_random_restarts_reach_true_board_score(self):
        """solve_fixture has no key0 argument, so this checks the achievable
        case: starting from independent random-restart initial keys (no
        seeding of the true board), annealing still discovers a board that
        scores at least as well as the true board -- i.e. the search is not
        leaving the true answer's own score unreached, for a shortlist that
        is known to contain the planted order."""
        model = audit.SpectralModel.from_training_corpus()
        quad, _ = audit.load_language_model()
        fixture = audit.make_fixture(width=2, pair_index=0, fixture_index=0)
        pair = tuple(fixture["pair"])
        codes = audit.slot_codes(pair)
        code_to_slot = {code: index for index, code in enumerate(codes)}
        segmented = audit.segment_raw(fixture["raw"], pair)
        token_slots = np.array([code_to_slot[c] for c in segmented], dtype=np.int64)
        true_key = np.array([
            audit.LETTER_ALPHABET.index(
                {code: letter for letter, code in fixture["letter_to_code"].items()}[code]
            )
            for code in codes
        ], dtype=np.int64)
        true_score = audit.score_indices(true_key[token_slots], quad)
        result = audit.solve_fixture(fixture, model, quad, shortlist_keep=2,
                                     board_restarts=2, board_iters=4000, seed=3)
        self.assertGreaterEqual(result["winner_quadgram_score"], true_score - 1e-6)

    def test_solve_fixture_rejects_below_minimum_decoded_length(self):
        model = audit.SpectralModel.from_training_corpus()
        quad, _ = audit.load_language_model()
        fixture = audit.make_fixture(width=3, pair_index=0, fixture_index=0)
        original_min = audit.MIN_DECODED_LENGTH
        audit.MIN_DECODED_LENGTH = 10 ** 6
        try:
            result = audit.solve_fixture(fixture, model, quad, shortlist_keep=6,
                                         board_restarts=1, board_iters=200, seed=1)
        finally:
            audit.MIN_DECODED_LENGTH = original_min
        self.assertFalse(result["solved"])
        self.assertEqual(result["rejected_reason"], "no_candidate_met_min_decoded_length")

    def test_normalized_score_does_not_favour_shorter_decoding(self):
        equal_total = -100.0
        shorter = audit.normalized_quadgram_score(equal_total, decoded_length=20)
        longer = audit.normalized_quadgram_score(equal_total, decoded_length=200)
        self.assertLess(shorter, longer)

    def test_exhaustive_flag_rejects_width_above_budget(self):
        model = audit.SpectralModel.from_training_corpus()
        quad, _ = audit.load_language_model()
        fixture = audit.make_fixture(width=10, pair_index=0, fixture_index=0)
        with self.assertRaises(ValueError):
            audit.solve_fixture(fixture, model, quad, exhaustive=True)

    def test_dev_batch_exhaustive_records_shortlist_mode(self):
        result = audit.run_dev_batch(widths=(2,), fixtures_per_width=1, exhaustive=True,
                                     board_iters=200, board_restarts=1)
        self.assertEqual(result["shortlist_mode"], "exhaustive")
        self.assertIsNone(result["budgets"]["shortlist_keep"])
        self.assertEqual(result["fixture_split"], "dev")

    def test_relabeling_equivalence_across_escape_pairs(self):
        pair_from = audit.ESCAPE_PAIRS[0]
        fixture = audit.make_fixture(width=6, pair_index=0, fixture_index=2)
        code_to_letter_from = {code: letter for letter, code in fixture["letter_to_code"].items()}
        for pair_to_index in (5, 17, 35):
            pair_to = audit.ESCAPE_PAIRS[pair_to_index]
            mapping = audit.relabel_symbol_map(pair_from, pair_to)
            self.assertEqual(sorted(mapping), sorted(audit.NINE_SYMBOLS))
            self.assertEqual(len(set(mapping.values())), 9)

            relabeled_raw = audit.relabel_string(fixture["raw"], mapping)
            code_to_letter_to = {
                audit.relabel_string(code, mapping): letter
                for code, letter in code_to_letter_from.items()
            }
            decoded_from = audit.decode_raw(fixture["raw"], pair_from, code_to_letter_from)
            decoded_to = audit.decode_raw(relabeled_raw, pair_to, code_to_letter_to)
            self.assertEqual(decoded_from, decoded_to)

            relabeled_observed = audit.relabel_string(fixture["observed"], mapping)
            geometry = audit.Geometry(audit.RAW_LENGTH, fixture["width"])
            restored_to = geometry.decrypt(relabeled_observed, fixture["order"])
            self.assertEqual(restored_to, relabeled_raw)

    def test_joint_pair_solver_reports_blind_recovery_fields(self):
        model = audit.SpectralModel.from_training_corpus()
        quad, _ = audit.load_language_model()
        fixture = audit.make_fixture(2, pair_index=0, fixture_index=0)
        result = audit.solve_fixture_joint_pairs(
            fixture, model, quad, joint_keep=8,
            board_restarts=1, board_iters=200, seed=7,
        )
        self.assertTrue(result["solved"])
        self.assertIn(result["escape_pair_recovery"], (True, False))
        self.assertIn(result["exact_order_recovery"], (True, False))
        self.assertEqual(
            result["joint_recovery"],
            result["escape_pair_recovery"] and result["exact_order_recovery"],
        )

    def test_joint_tail_batch_is_self_describing(self):
        result = audit.run_joint_tail_batch(
            fixture_specs=(("vic_profile", 2, 25),),
            joint_keep=4, board_restarts=1, board_iters=100,
        )
        self.assertFalse(result["faed_scored"])
        self.assertEqual(result["fixture_split"], "dev")
        self.assertEqual(result["fixture_count"], 1)
        self.assertEqual(result["budgets"]["joint_keep"], 4)


if __name__ == "__main__":
    unittest.main()
