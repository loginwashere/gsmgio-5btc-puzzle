import phase544_rail_feasible_lexicon_scan as p544


def test_decode_reproduces_phase425_output_and_rails():
    checks = p544.control_decode()
    assert all(checks.values()), checks


def test_probability_model_is_consistent():
    checks = p544.control_model()
    assert all(checks.values()), checks


def test_scan_and_interval_cover_on_toy_tail():
    checks = p544.control_scan_and_cover()
    assert all(checks.values()), checks


def test_plant_roundtrip_both_alignments():
    words = ["BADGERED", "DEADHEAD"]
    for off, w in ((200, "BADGERED"), (301, "DEADHEAD")):
        s = p544.plant(p544.FAED_U, off, w)
        assert s is not None
        assert p544.decode(s)[off:off + len(w)] == w
        assert len(s) == 570 and set(s) <= set(p544.FAED_U)


def test_plant_rejects_infeasible_cell():
    # K would need cell (1, 4), which no FAED symbol occupies
    assert p544.plant(p544.FAED_U, 200, "KKKKKKKK") is None


def test_lexicon_is_ascii_without_j():
    words = p544.load_words()
    assert all(w.isascii() and "J" not in w and p544.MIN_WORD <= len(w) <= p544.MAX_WORD
               for w in words)


def test_null_trial_is_deterministic():
    words = p544.load_words()
    p544._init_worker(words)
    assert p544._trial(7) == p544._trial(7)
