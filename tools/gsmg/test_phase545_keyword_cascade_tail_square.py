import phase545_keyword_cascade_tail_square as p545


def test_construction_reproduces_prior_phases():
    checks = p545.control_construction()
    assert all(checks.values()), checks


def test_roundtrip_and_generalised_model():
    checks = p545.control_roundtrip_and_model()
    assert all(checks.values()), checks


def test_cascade_logic():
    checks = p545.control_cascade_logic()
    assert all(checks.values()), checks


def test_layout_shape():
    cells, chains, squares = p545.real_layout()
    assert len(cells) == 9 + 2 * len(squares)
    assert [c[0] for c in cells[:9]] == ["faed"] * 9
    assert squares == sorted(squares) and all(len(set(s)) == 25 for s in squares)
    assert set(chains) == {"7", "13", "full"}


def test_family_p_toy_pool():
    pool = [[float(i % 10), float((i * 7) % 10)] for i in range(1000)]
    _, fam, corr = p545.family_p([9.0, 9.0], pool)
    assert 0 < fam <= 0.2 and 0 < corr <= 1
    _, fam_low, corr_low = p545.family_p([0.0, 0.0], pool)
    assert fam_low > 0.9 and corr_low > 0.9
