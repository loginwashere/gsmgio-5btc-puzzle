import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase531_faed_closed_system_operator_eligibility as phase531


def test_every_row_has_all_frozen_fields():
    for row in phase531.operator_rows():
        assert all(field in row for field in phase531.FIELDS)
        assert "covered" in row and "eligible" in row


def test_no_row_is_currently_executable():
    rows = phase531.operator_rows()
    assert not [row for row in rows if row["eligible"]]
    assert all(row["first_missing_field"] for row in rows)


def test_checkerboard_transposition_lacks_selection_not_source():
    row = next(row for row in phase531.operator_rows() if row["id"] == "checkerboard_columnar_transposition")
    assert row["authenticated_source"]
    assert row["faed_operand_binding"]
    assert not row["operation_selected"]
    assert not row["parameters_fixed"]


def test_crib_rejected_for_missing_faed_binding():
    row = next(row for row in phase531.operator_rows() if row["id"] == "known_text_crib")
    assert row["authenticated_source"]
    assert not row["faed_operand_binding"]
    assert row["first_missing_field"] == "faed_operand_binding"


def test_phase530_delta_does_not_create_faed_edge():
    row = next(row for row in phase531.operator_rows() if row["id"] == "dbbi_84_host_rails")
    assert row["covered"]
    assert not row["faed_operand_binding"]

