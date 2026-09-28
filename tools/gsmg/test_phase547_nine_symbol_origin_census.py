import numpy as np

import phase547_nine_symbol_origin_census as p547


def test_machinery_vectorized_equals_direct():
    checks = p547.control_machinery()
    assert checks["m1_vectorized_equals_direct"] and checks["m2_vectorized_equals_direct"], checks


def test_morse_planted_recovered():
    checks = p547.control_morse_planted()
    assert checks["morbit_true_key_found"] and checks["pollux_valid"] >= 1, checks


def test_m1_trit_grouping_lengths():
    s = p547.to_idx(p547.FAED)
    assert [p547.m1_terms(s, off)[1] for off in range(3)] == [380, 379, 379]
    assert p547.m1_terms(p547.to_idx(p547.DBBI), 0)[1] == 60


def test_m2_lut_and_caps():
    assert p547.LUT[5, 4] == ord("S") - 65 and p547.LUT[0, 4] == -1
    assert list(p547.CAPS) == [3, 3, 3, 3, 3, 4, 3, 4]


def test_holm_monotone():
    adj = p547.holm([0.001, 0.02, 0.5])
    assert np.isclose(adj[0], 0.003) and np.isclose(adj[1], 0.04) and adj[2] == 0.5
