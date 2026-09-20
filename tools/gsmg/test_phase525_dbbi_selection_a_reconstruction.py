import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase525_dbbi_selection_a_reconstruction as p525


def test_complete_parse_family_is_exactly_83_and_84():
    parses = p525.enumerate_complete_parses(p525.DBBI)
    assert [len(tokens) for tokens in parses] == [83, 84]
    records = {record["logical_length"]: record for record in map(p525.parse_record, parses)}
    assert (records[83]["b_hosts"], records[83]["be_hosts"]) == (15, 8)
    assert (records[84]["b_hosts"], records[84]["be_hosts"]) == (16, 7)


def test_picture_event_sequence_and_fefe_rank():
    events = p525.picture_events()
    assert "".join(event["color"] for event in events) == p525.EXPECTED_EVENT_COLORS
    assert events[20]["event_rank"] == 21
    assert events[20]["kind"] == "fefe"
    assert events[20]["spiral_1"] == 164


def test_84_parse_has_exactly_two_picture_matches():
    tokens = next(tokens for tokens in p525.enumerate_complete_parses(p525.DBBI) if len(tokens) == 84)
    matches = p525.compatible_selections(p525.picture_events(), p525.parse_record(tokens)["host_colors"])
    assert [tuple(match["omitted_event_ranks"]) for match in matches] == [(22, 25), (23, 25)]


def test_selection_a_is_unique_byte_representative_match():
    events = p525.picture_events()
    tokens = next(tokens for tokens in p525.enumerate_complete_parses(p525.DBBI) if len(tokens) == 84)
    matches = p525.compatible_selections(events, p525.parse_record(tokens)["host_colors"])
    good = [match for match in matches if match["represents_source_bytes_1_through_23_once"]]
    assert len(good) == 1
    assert good[0]["omitted_event_ranks"] == [22, 25]


def test_selection_a_exact_core_representations():
    events = p525.picture_events()
    selected = [e for e in events if e["event_rank"] not in p525.SELECTION_A_OMITTED]
    records = {record["label"]: record["value"] for record in p525.representations(selected)}
    assert records["selected_url_bytes"] == "gsmg.io/theseedisplante"
    assert records["selected_colors_by"] == "BBBBYBBBYYBBBBYBBYYBBYB"
    assert records["spiral_0_sum"] == "2181"
    assert records["spiral_1_sum"] == "2204"
    assert records["row_1_sum"] == "172"
    assert records["column_1_sum"] == "171"


def test_full_audit_without_comparators_is_oracle_free_and_consistent():
    result = p525.audit(run_comparators=False)
    assert result["complete_parse_count"] == 2
    assert result["selection_a"]["represents_source_bytes_1_through_23_once"]
    assert not result["selection_b_control"]["represents_source_bytes_1_through_23_once"]
    assert result["comparators"]["executed"] is False


def test_self_test():
    assert p525.self_test() == {"ok": True, "checks": 4}
