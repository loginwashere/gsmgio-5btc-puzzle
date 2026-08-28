import phase436_source_codes_referent_eligibility_audit as phase436


def test_authenticated_source_commitments_and_phase270_inventory():
    report = phase436.audit()
    assert report["authenticated_sources"]["encoded_321"]["length"] == 1539
    assert report["authenticated_sources"]["cipher_321"]["length"] == 1539
    assert report["phase270_inventory"] == {"base_count": 25, "material_count": 50}


def test_frozen_protocol_fails_closed_on_missing_phase418_finding():
    report = phase436.audit()
    assert report["decision"] == "protocol_invalid"
    assert report["missing_phase_findings"] == (418,)


def test_phase436_is_oracle_and_gpu_free():
    report = phase436.audit()
    assert report["password_materials_generated"] == 0
    assert report["oracle_calls"] == 0
    assert report["gpu_touched"] is False
