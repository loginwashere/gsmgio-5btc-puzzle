import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase526_selection_a_slot_overlap as p526


def test_coordinate_value_scope_is_exact():
    values = p526.coordinate_values()
    assert len(values) == 16
    assert len({value for value, _ in values}) == 16
    assert all(source.startswith("Phase 525 Selection A:") for _, source in values)


def test_extension_base_count_matches_closed_form():
    records, duplicates = p526.enumerate_extension_bases()
    assert len(records) + duplicates == 112_624


def test_every_base_has_one_new_matrixsumlist_value():
    records, _ = p526.enumerate_extension_bases()
    for cell, _base, provenance in records:
        assert "MSL" in cell
        assert sum(item.startswith("Phase 525 Selection A:") for item in provenance) == 1


def test_no_oracle_entrypoint_is_imported():
    for name in ("aes_try_open_bytes", "aes_try_open_stream_bytes", "raw_key_try_open"):
        assert name not in vars(p526)


def test_phase523_material_map_is_explicitly_converted_to_set():
    with tempfile.NamedTemporaryFile() as manifest, patch.object(
        p526.p523, "build_tested", return_value=({11: 1, 22: 2}, [])
    ), patch.object(p526, "P524_BASES", Path("/dev/null")), patch.object(
        p526, "P478_MANIFEST", Path(manifest.name)
    ):
        prior, counts = p526.prior_material_keys()
        assert prior == {11, 22}
        assert counts["coverage_material_keys"] == 2


def test_self_test():
    result = p526.self_test()
    assert result["ok"]
    assert result["checks"] == 5
