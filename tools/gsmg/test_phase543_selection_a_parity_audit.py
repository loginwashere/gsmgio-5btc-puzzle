import phase543_selection_a_parity_audit as p543


def test_phase543_scope_and_matrix_reconstruction():
    report = p543.self_test()
    assert report == {
        "structural": "ok",
        "passphrase_materials": 36,
        "slot_bases": 14078,
    }
