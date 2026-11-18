import numpy as np

import phase550_board_profiled_frequency as p550


def test_incidence_matrix():
    assert p550.A.shape == (9, 25)
    assert p550.A[:, :7].sum() == 7 and p550.A[:, 7:].sum() == 36
    assert p550.A[7, 7:16].sum() == 10 and p550.A[8, 16:].sum() == 10  # cell 77 / 88 emits its escape twice


def test_puzzle_corpus_reproduces_solved_text():
    text = p550.corpus_puzzle()
    assert "YOURLIFEISTHESUMOFAREMAINDER" in text
    assert text.endswith(p550.VALIDATION_ANSWER.replace("J", "I"))


def test_screenplay_dedup_and_letters_only():
    idx, q = p550.corpus("K2_screenplay")
    assert len(idx) > 100000 and np.isclose(q.sum(), 1.0)


def test_encode_counts_matches_expectation_direction():
    q = p550.corpus("K1_book")[1]
    board = p550.vic_board(q)
    obs = p550.encode_counts(p550.corpus("K1_book")[0][:20000], board, 20000)
    exp = p550.A @ q[board]
    assert np.corrcoef(obs, exp)[0, 1] > 0.99


def test_search_not_worse_than_known_board():
    rng = np.random.default_rng(3)
    q = p550.corpus("K1_book")[1]
    board = p550.random_board(rng)
    obs = p550.sample_counts("K1_book", board, 570, rng)
    t, b = p550.search(obs, q, rng, restarts=2, steps=1500)
    assert t <= p550.objective(board, q, np.sort(obs)[::-1]) + 1e-9
    assert sorted(b.tolist()) == list(range(25))


def test_holm():
    adj = p550.holm([0.001, 0.02, 0.5])
    assert np.isclose(adj[0], 0.003) and np.isclose(adj[1], 0.04) and adj[2] == 0.5
