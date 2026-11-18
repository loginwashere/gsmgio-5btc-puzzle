import numpy as np

import phase548_generator_fingerprint as p548


def test_generators_emit_exact_length_and_alphabet():
    rng = np.random.default_rng(1)
    for name in p548.GENERATORS:
        gen = p548.generator(name, p548.FAED_COUNTS)
        for n in (91, 570):
            s = gen(rng, n)
            assert len(s) == n and s.min() >= 0 and s.max() <= 8, name


def test_board_has_25_distinct_cells():
    assert len(set(p548.CELLS)) == 25
    board = p548.vic_board(np.random.default_rng(2))
    assert set(board) == set(p548.LETTERS25) and len(set(board.values())) == 25
    assert all(len(board[c]) == 1 for c in p548.TOP7)


def test_label_invariance():
    assert p548.control_label_invariance()["label_invariant"]


def test_stats_known_values():
    s = np.array([0, 0, 1, 1] * 10)
    x = p548.stats(s)
    assert np.isclose(x[0], 0.5) and np.isclose(x[1], 0.5) and np.isclose(x[8], 20 / 39)
    assert len(x) == len(p548.STAT_NAMES) == 14


def test_base9_bytes():
    assert p548.bytes_base9([65, 255], 6).tolist() == [0, 7, 2, 3, 1, 3]


def test_holm():
    adj = p548.holm([0.001, 0.02, 0.5])
    assert np.isclose(adj[0], 0.003) and np.isclose(adj[1], 0.04) and adj[2] == 0.5
