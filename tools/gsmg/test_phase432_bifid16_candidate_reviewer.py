#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

import phase432_bifid16_candidate_reviewer as reviewer


class Phase432ReviewerTests(unittest.TestCase):
    def fixture(self, directory: Path) -> tuple[Path, Path]:
        checkpoint = directory / "checkpoint.json"
        checkpoint.write_text(json.dumps({
            "fingerprint": reviewer.EXPECTED_FINGERPRINT,
            "next_rank": 4_200_000_000_000,
            "block_winners": [
                {"rank": 4_113_233_954_640, "score_total": -3519.4343},
                {"rank": 4_113_233_994_960, "score_total": -3519.4343},
                {"rank": 4_113_234_004_320, "score_total": -3521.062},
            ],
        }), encoding="utf-8")
        dictionary = directory / "words"
        dictionary.write_text(
            "elect\nbaled\nuser\nseed\nbitcoin\nprivate\naddress\nblue\nyellow\n",
            encoding="utf-8",
        )
        return checkpoint, dictionary

    def test_snapshot_deduplicates_and_reviews_tail(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            checkpoint, dictionary = self.fixture(Path(raw_directory))
            report = reviewer.review(checkpoint, dictionary, trials=4, review_limit=2)
        self.assertEqual(report["summary"]["distinct_decodes"], 2)
        self.assertEqual(report["summary"]["duplicate_rows_collapsed"], 1)
        leader = report["distinct_candidates"][0]
        self.assertEqual(leader["raw_member_count"], 2)
        self.assertTrue(leader["decoded_prefix_72"].startswith("BTCSEED"))
        self.assertNotIn("BTCSEED", [hit["keyword"] for hit in leader["keyword_hits"]])
        self.assertEqual(leader["dictionary_calibration"]["trials"], 4)

    def test_fingerprint_mismatch_is_fatal(self):
        with tempfile.TemporaryDirectory() as raw_directory:
            checkpoint, dictionary = self.fixture(Path(raw_directory))
            state = json.loads(checkpoint.read_text())
            state["fingerprint"]["kernel_sha256"] = "wrong"
            checkpoint.write_text(json.dumps(state))
            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                reviewer.review(checkpoint, dictionary, trials=1, review_limit=1)

    def test_previous_delta(self):
        current = [
            {"decoded_sha256": "new", "best_score_total": -10.0},
            {"decoded_sha256": "shared", "best_score_total": -11.0},
        ]
        previous = {"distinct_candidates": [
            {"decoded_sha256": "old", "best_score_total": -12.0},
            {"decoded_sha256": "shared", "best_score_total": -13.0},
        ]}
        delta = reviewer.deltas(current, previous)
        self.assertTrue(delta["leader_changed"])
        self.assertEqual(delta["leader_score_delta"], 2.0)
        self.assertEqual(delta["new_decoded_sha256"], ["new"])
        self.assertEqual(delta["departed_decoded_sha256"], ["old"])


if __name__ == "__main__":
    unittest.main()
