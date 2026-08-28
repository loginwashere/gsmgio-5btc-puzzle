import phase437_source_codes_referent_eligibility_corrected_audit as phase437


def test_documentary_correction_changes_no_eligibility_rule():
    correction = phase437.audit()["correction"]
    assert correction["phase418_protocol_exists"] is True
    assert correction["phase418_completed_finding_exists"] is False
    assert correction["eligibility_rules_changed"] is False


def test_no_source_referent_is_eligible():
    report = phase437.audit()
    assert report["referent_count"] == 11
    assert report["eligible_referents"] == ()
    assert all(not row["eligible"] for row in report["referents"])


def test_only_two_authenticated_uncovered_source_families_remain_gated():
    report = phase437.audit()
    assert report["authenticated_uncovered_but_ineligible"] == (
        "raw_encoded_321", "cp1141_beaufort_ciphertext"
    )
    rows = {row["id"]: row for row in report["referents"]}
    for identifier in report["authenticated_uncovered_but_ineligible"]:
        assert "unique_representation" in rows[identifier]["failed_gates"]
        assert "operator_fixed" in rows[identifier]["failed_gates"]


def test_and_or_oracle_and_gpu_remain_gated():
    report = phase437.audit()
    assert report["and_or_authorized"] is False
    assert report["password_materials_generated"] == 0
    assert report["oracle_calls"] == 0
    assert report["gpu_touched"] is False
