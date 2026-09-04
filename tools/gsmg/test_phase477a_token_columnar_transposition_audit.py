#!/usr/bin/env python3
"""Unit tests for the Phase 477A reference implementation."""

import itertools
import sys
import unittest
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase477a_token_columnar_transposition_audit as p477  # noqa: E402


class PCG32Tests(unittest.TestCase):
    def test_reference_stream(self):
        # PCG32 XSH-RR with the reference seeding sequence (state 42, seq 54).
        rng = p477.PCG32(42, 54)
        first = [rng.next_u32() for _ in range(3)]
        self.assertEqual(first, [0xa15c02b7, 0x7b47f409, 0xba1d3330])

    def test_determinism_and_shuffle(self):
        a, b = p477.PCG32(7), p477.PCG32(7)
        self.assertEqual(a.permutation(12), b.permutation(12))
        self.assertEqual(sorted(a.permutation(9)), list(range(9)))


class GeometryTests(unittest.TestCase):
    def test_ragged_lengths(self):
        geo = p477.Geometry(436, 7)
        self.assertEqual(geo.rows, 63)
        self.assertEqual(geo.short, 5)
        self.assertEqual(geo.lengths.tolist(), [63, 63, 62, 62, 62, 62, 62])
        self.assertTrue(p477.Geometry(436, 4).is_exact)

    def test_sigma_is_permutation_both_directions(self):
        for w in (2, 4, 9, 23, 40):
            geo = p477.Geometry(436, w)
            perm = p477.PCG32(w).permutation(w)
            for d in p477.DIRECTIONS:
                sig = geo.sigma(perm, d)
                self.assertEqual(sorted(sig.tolist()), list(range(436)), (w, d))
            inv = np.empty(436, dtype=np.int64)
            inv[geo.sigma(perm, "untranspose")] = np.arange(436)
            self.assertTrue(np.array_equal(inv, geo.sigma(perm, "transpose")))

    def test_sigma_batch_matches_scalar(self):
        geo = p477.Geometry(436, 9)
        perms = np.array([p477.PCG32(k).permutation(9) for k in range(6)])
        batch = geo.sigma_batch(perms)
        for k in range(6):
            self.assertTrue(np.array_equal(batch[k], geo.sigma(perms[k], "untranspose")))

    def test_direction_equivalence_retains_two(self):
        for w in (3, 7, 13):
            self.assertEqual(p477.direction_equivalence(w)["retained_directions"], 2)


class RoundTripTests(unittest.TestCase):
    def test_fixture_round_trip(self):
        for w in (2, 5, 12, 31):
            for d in p477.DIRECTIONS:
                fx = p477.make_fixture(w, d, "broad", p477.derive_seed(1, w))
                obs = p477.stream_to_slots(fx["stream"])
                key = np.array(fx["key"])
                plain = p477.text_of(key[obs[p477.Geometry(436, w).sigma(fx["perm"], d)]])
                self.assertEqual(plain, fx["passage"])
                self.assertEqual(len(obs), 436)

    def test_hard_fixture_singles_are_top7(self):
        fx = p477.make_fixture(6, "untranspose", "hard", 5)
        passage = fx["passage"]
        counts = sorted(range(26), key=lambda i: -passage.count(p477.ALPHABET[i]))[:7]
        self.assertEqual(sorted(fx["key"][:7]), sorted(counts))
        self.assertGreaterEqual(fx["top7_share"], p477.HARD_TOP7_SHARE)

    def test_corpus_is_prose_only(self):
        letters = p477.corpus_letters()
        self.assertNotIn("J", letters)
        self.assertGreater(len(letters), 50000)
        self.assertLess(len(letters), 60000)  # index and back matter removed


class SolverComponentTests(unittest.TestCase):
    def test_held_karp_matches_brute_force(self):
        for n in (3, 5, 7):
            rng = p477.PCG32(n)
            gain = np.array([[rng.random() for _ in range(n)] for _ in range(n)])
            self.assertEqual(p477.held_karp_path(gain), p477.brute_force_path(gain))

    def test_invariant_batch_matches_scalar(self):
        obs = p477.stream_to_slots(p477.FAED)
        geo = p477.Geometry(436, 8)
        perms = np.array([p477.PCG32(k).permutation(8) for k in range(4)])
        got = p477.invariant_batch(obs, geo, perms)
        for k in range(4):
            seq = obs[geo.sigma(perms[k], "untranspose")]
            c2 = np.bincount(seq[:-1] * 25 + seq[1:])
            c3 = np.bincount((seq[:-2] * 25 + seq[1:-1]) * 25 + seq[2:])
            ref = (c2 * (c2 - 1)).sum() / 2 + p477.TRIGRAM_WEIGHT * (c3 * (c3 - 1)).sum() / 2
            self.assertAlmostEqual(got[k], ref)

    def test_enumeration_ranks_planted_order_first(self):
        fx = p477.make_fixture(6, "untranspose", "hard", p477.derive_seed(2, 6))
        obs = p477.stream_to_slots(fx["stream"])
        top, total = p477.enumerate_top_orders(obs, 6, 3)
        self.assertEqual(total, 720)
        self.assertEqual(list(top[0][1]), fx["perm"])

    def test_kendall_tau(self):
        self.assertEqual(p477.kendall_tau([0, 1, 2, 3], [0, 1, 2, 3]), 1.0)
        self.assertEqual(p477.kendall_tau([0, 1, 2, 3], [3, 2, 1, 0]), -1.0)

    def test_planted_positive_untranspose(self):
        budget = dict(p477.BUDGET, top_orders=4, enum_board_restarts=1, enum_board_iters=20000)
        fx = p477.make_fixture(5, "untranspose", "hard", p477.derive_seed(3, 5))
        result = p477._solve_task((fx["stream"], 5, "untranspose", 11, budget))
        metrics = p477.evaluate_fixture(fx, result)
        self.assertTrue(metrics["reach"])
        self.assertEqual(result["perm"], fx["perm"])

    def test_planted_positive_transpose(self):
        budget = dict(p477.BUDGET, restarts=3, top_k=1, rounds=1)
        fx = p477.make_fixture(9, "transpose", "hard", p477.derive_seed(3, 9))
        result = p477._solve_task((fx["stream"], 9, "transpose", 11, budget))
        self.assertTrue(p477.evaluate_fixture(fx, result)["reach"])

    def test_not_enumerable_width(self):
        obs = p477.stream_to_slots(p477.FAED)
        result = p477.CellSolver(obs, p477.ENUM_MAX_WIDTH + 1, "untranspose").solve(1)
        self.assertEqual(result["status"], "not_enumerable")
        cells = p477.family_cells(p477.WIDTHS, p477.DIRECTIONS)
        self.assertEqual(len(cells), 39 + p477.ENUM_MAX_WIDTH - 1)


class SecondaryPairTests(unittest.TestCase):
    def test_he_configuration_round_trips_and_restores(self):
        try:
            p477.configure_pair("h", "e")
            self.assertEqual(p477.L, 469)
            self.assertTrue(p477.Geometry(p477.L, 7).is_exact)
            fx = p477.make_fixture(7, "untranspose", "hard", p477.pair_seed(p477.SEED_DEV))
            obs = p477.stream_to_slots(fx["stream"])
            self.assertEqual(len(obs), 469)
            key = np.array(fx["key"])
            plain = p477.text_of(key[obs[p477.Geometry(469, 7).sigma(fx["perm"], "untranspose")]])
            self.assertEqual(plain, fx["passage"])
            self.assertNotEqual(p477.pair_seed(p477.SEED_NULL), p477.SEED_NULL)
        finally:
            p477.configure_pair("g", "i")
        self.assertEqual(p477.L, 436)
        self.assertEqual(p477.pair_seed(p477.SEED_NULL), p477.SEED_NULL)


class NullTests(unittest.TestCase):
    def test_token_shuffle_preserves_histogram(self):
        real = p477.stream_to_slots(p477.FAED)
        rng = p477.PCG32(p477.derive_seed(p477.SEED_NULL, 0))
        shuffled = real.tolist()
        rng.shuffle(shuffled)
        self.assertEqual(np.bincount(shuffled, minlength=25).tolist(), np.bincount(real, minlength=25).tolist())
        self.assertNotEqual(shuffled, real.tolist())
        self.assertEqual(len(p477.stream_to_slots(p477.slots_to_stream(np.array(shuffled)))), 436)


if __name__ == "__main__":
    unittest.main()
