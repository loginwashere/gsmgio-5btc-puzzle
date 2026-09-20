import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase529_dbbi_payload_material_overlap as phase529


def test_frozen_base_family_is_exactly_five():
    bases = phase529.frozen_bases()
    assert tuple(bases) == phase529.BASE_LABELS
    assert len(set(bases.values())) == 5


def test_standard_expansion_is_18_per_base_and_90_unique():
    by_base, materials = phase529.candidate_materials()
    assert all(len(forms) == 18 for forms in by_base.values())
    assert sum(len(forms) for forms in by_base.values()) == 90
    assert len(materials) == 90


def test_no_unlicensed_historical_residue_base():
    bases = phase529.frozen_bases()
    result = json_load(phase529.P528_RESULT)
    assert result["exact_objects"]["historical_hosted_residue_60"] not in bases.values()


def json_load(path):
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def test_base_file_scanner_finds_exact_material(tmp_path):
    path = tmp_path / "bases.txt"
    path.write_text("abc\n", encoding="utf-8")
    target = next(iter(phase529.p523.expand_std("abc", True)))
    result = phase529.scan_base_file(path, {target, "not-present"})
    assert result["bases"] == 1
    assert result["exact_hits"] == [target]


def test_scope_has_no_oracle_imports():
    assert not any(
        name in phase529.__dict__
        for name in ("aes_try_open_bytes", "aes_try_open_stream_bytes", "raw_key_try_open")
    )

