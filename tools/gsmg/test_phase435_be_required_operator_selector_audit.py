import phase435_be_required_operator_selector_audit as phase435


def test_authenticated_letters_and_readme_boundaries_agree():
    report = phase435.audit()
    assert report["word_count"] == 336
    assert report["connected_letter_count"] == 1539
    assert report["be_required"]["connected_positions_0"] == (1131, 1277)
    assert report["be_required"]["word_positions_0"] == (256, 283)


def test_repetition_is_real_but_not_unique_under_frozen_comparator():
    report = phase435.audit()
    repeated = {tuple(row["words"]): row["count"] for row in report["repeated_bigrams"]}
    assert repeated[("BE", "REQUIRED")] == 2
    assert repeated[("RESULT", "IN")] == 2
    assert report["repeated_trigrams"] == ()
    assert report["be_required_unique_under_mixed_provenance_test"] is False


def test_be_count_depends_on_unit():
    counts = phase435.audit()["be_counts"]
    assert counts["whole_word_be"] == 3
    assert counts["raw_connected_be"] == 7
    assert counts["whole_word_be_required"] == 2


def test_no_registered_consumer_and_no_oracle_activity():
    report = phase435.audit()
    assert all(not row["supplies_matching_consumer"] for row in report["registered_mechanisms"])
    assert report["promoted"] is False
    assert report["password_materials_generated"] == 0
    assert report["oracle_calls"] == 0
    assert report["gpu_touched"] is False
