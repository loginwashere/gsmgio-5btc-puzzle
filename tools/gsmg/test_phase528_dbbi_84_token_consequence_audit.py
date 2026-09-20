import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase528_dbbi_84_token_consequence_audit as phase528


def test_parse_family_and_tail_delta():
    family = phase528.parse_family()
    assert sorted(family) == [83, 84]
    assert family[83]["hosted_residue"] == family[84]["hosted_residue"]
    assert family[84]["full_residue"] == family[83]["full_residue"] + "e"
    assert family[84]["tail"] == "e"


def test_group_payloads_are_identical_but_final_host_changes():
    family = phase528.parse_family()
    assert [g["payload"] for g in family[83]["groups"]] == [
        g["payload"] for g in family[84]["groups"]
    ]
    assert family[83]["groups"][-1]["host"] == "be"
    assert family[84]["groups"][-1]["host"] == "b"


def test_84_rails_have_exact_16_7_partition():
    parse84 = phase528.parse_family()[84]
    assert parse84["rails"]["b"]["group_count"] == 16
    assert parse84["rails"]["be"]["group_count"] == 7
    assert parse84["rails"]["b"]["total_payload_length"] == 35
    assert parse84["rails"]["be"]["total_payload_length"] == 25
    assert parse84["rails"]["b"]["total_a1i9_sum"] == 183
    assert parse84["rails"]["be"]["total_a1i9_sum"] == 153


def test_corrected_merge_labels_are_seven_three():
    parse84 = phase528.parse_family()[84]
    merged = phase528.corrected_merge_starts(parse84)
    split = tuple(i for i in phase528.LITERAL_BE_STARTS if i not in set(merged))
    assert merged == (10, 23, 30, 49, 64, 71, 84)
    assert split == (17, 19, 89)


def test_exact_objects_are_bounded_and_distinct():
    family = phase528.parse_family()
    objects = phase528.exact_objects(family[83], family[84])
    assert len(objects) == 6
    assert len(set(objects.values())) == 6
    assert len(objects["parse84_full_residue_61"]) == 61
    assert len(objects["parse84_b_host_payload_rail"]) == 35
    assert len(objects["parse84_be_host_payload_rail"]) == 25


def test_small_null_is_deterministic_and_oracle_free():
    parse84 = phase528.parse_family()[84]
    left = phase528.corrected_phase177(parse84, trials=7, seed=177)
    right = phase528.corrected_phase177(parse84, trials=7, seed=177)
    assert left == right
    assert left["merged_count"] == 7
    assert left["split_count"] == 3


def test_dependency_inventory_has_one_invalidated_cell():
    rows = phase528.dependency_inventory()
    invalidated = [row for row in rows if row["effect"] == "invalidated_and_rerun"]
    assert len(invalidated) == 1
    assert invalidated[0]["phases"] == "177"

