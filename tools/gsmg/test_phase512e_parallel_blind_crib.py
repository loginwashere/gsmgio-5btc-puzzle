#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import phase512a_transposition_crib_feasibility as phase512a
import phase512d_length_pattern_csp as phase512d
import phase512e_parallel_blind_crib as phase512e


class Phase512EParallelBlindCribTests(unittest.TestCase):
    def test_fixture_zero_is_backward_compatible_and_extensions_differ(self):
        old = phase512a.make_fixture("phase1_credential", 15)
        explicit = phase512a.make_fixture("phase1_credential", 15, 0)
        later = phase512a.make_fixture("phase1_credential", 15, 1)
        self.assertEqual(old["observed"], explicit["observed"])
        self.assertEqual(old["order"], explicit["order"])
        self.assertNotEqual(old["observed"], later["observed"])

    def test_absent_fixture_has_no_true_order_pattern_match(self):
        fixture = phase512e.make_absent_fixture("phase1_credential", 15, 0)
        matches = phase512a.crib_matches_for_order(
            fixture["observed"], fixture["width"], fixture["order"],
            phase512a.PAIR, fixture["crib"])
        self.assertEqual(matches, ())
        self.assertEqual(fixture["fixture_kind"], "crib_absent")

    def test_parallel_worker_matches_serial(self):
        result = phase512e.parity_probe(2)
        self.assertEqual(result["parity"], "pass")
        self.assertTrue(result["true_pair_hit"])

    def test_checkpoint_is_fail_closed_and_resumable(self):
        fixture = phase512a.make_fixture("phase1_credential", 15)
        true_pair_index = phase512a.base.ESCAPE_PAIRS.index(phase512a.PAIR)
        # At the planted start, the true pair produces an immediate exact hit.
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            value = phase512e.scan_fixture(
                fixture, workers=1, pair_indices=(true_pair_index,),
                start_begin=fixture["planted_raw_offset"], start_count=1,
                checkpoint_path=checkpoint)
            self.assertEqual(value["status"], "hit_at_earliest_completed_start")
            resumed = phase512e.scan_fixture(
                fixture, workers=1, pair_indices=(true_pair_index,),
                start_begin=fixture["planted_raw_offset"], start_count=1,
                checkpoint_path=checkpoint)
            self.assertEqual(value["completed_starts"], resumed["completed_starts"])
            tampered = json.loads(checkpoint.read_text())
            tampered["identity"]["observed_sha256"] = "0" * 64
            checkpoint.write_text(json.dumps(tampered))
            with self.assertRaises(RuntimeError):
                phase512e.scan_fixture(
                    fixture, workers=1, pair_indices=(true_pair_index,),
                    start_begin=fixture["planted_raw_offset"], start_count=1,
                    checkpoint_path=checkpoint)

    def test_search_result_exposes_node_limit_status(self):
        fixture = phase512a.make_fixture("phase1_credential", 15)
        patterns = tuple(phase512d.length_patterns(fixture["crib"]))
        result = phase512d.search_lengths_at_start(
            fixture, 0, 1, patterns=patterns, pair=phase512a.PAIR)
        self.assertTrue(result["node_limit_reached"])
        self.assertFalse(result["search_complete"])

    def test_pattern_shards_merge_to_serial_cell(self):
        fixture = phase512a.make_fixture("phase1_credential", 15)
        true_pair_index = phase512a.base.ESCAPE_PAIRS.index(phase512a.PAIR)
        start = fixture["planted_raw_offset"]
        serial = phase512e.scan_fixture(
            fixture, workers=1, pair_indices=(true_pair_index,),
            start_begin=start, start_count=1)
        sharded = phase512e.scan_fixture(
            fixture, workers=2, pair_indices=(true_pair_index,),
            start_begin=start, start_count=1, pattern_shards=4)
        serial_cell = serial["completed_starts"][0]["cells"][0]
        sharded_cell = sharded["completed_starts"][0]["cells"][0]
        self.assertEqual(serial_cell["hits"], sharded_cell["hits"])
        self.assertEqual(serial_cell["pair"], sharded_cell["pair"])
        self.assertTrue(sharded_cell["search_complete"])


if __name__ == "__main__":
    unittest.main()
