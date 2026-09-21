import numpy as np

import phase546_prefix_selectivity_curve as p546


def test_fast_prefix_matches_full_decode():
    checks = p546.control_fast_vs_slow()
    assert all(checks.values()), checks


def test_real_square_reproduces_btcseed():
    checks = p546.control_real_square()
    assert all(checks.values()), checks


def test_class_machinery():
    checks = p546.control_class_machinery(p546.load_words())
    assert checks["btcseed_in_E1_E3_not_E2"], checks


def test_counting_controls():
    checks = p546.control_counting()
    assert all(v for k, v in checks.items() if k != "arm_a_size"), checks


def test_wilson_interval_brackets_rate():
    lo, hi = p546.wilson(5, 1000)
    assert lo < 0.005 < hi and 0 <= lo and hi <= 1


def test_encode_decode_roundtrip():
    for w in ("BTCSEED", "AAAAAAA", "ZZZZZZZ"):
        assert p546.decode_code(p546.encode(w)) == w
