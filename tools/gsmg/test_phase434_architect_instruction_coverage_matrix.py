import phase434_architect_instruction_coverage_matrix as phase434


def test_every_clause_is_found_in_freshly_derived_plaintext_in_order():
    report = phase434.audit()
    assert report["clause_count"] == 8
    offsets = report["derived_offsets"]
    assert all(left["end_exclusive_0"] <= right["start_0"] for left, right in zip(offsets, offsets[1:]))


def test_models_and_and_or_gate_are_bounded():
    report = phase434.audit()
    assert len(report["model_comparison"]) == 4
    assert report["and_or_gate"]["authorized_now"] is False
    assert "source" in report["and_or_gate"]["decoded_strings"]


def test_phase434_is_oracle_free():
    report = phase434.audit()
    assert report["oracle_calls"] == 0
    assert report["password_materials_generated"] == 0
