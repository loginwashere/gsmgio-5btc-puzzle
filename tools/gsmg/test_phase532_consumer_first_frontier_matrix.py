import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase532_consumer_first_frontier_matrix as phase532


class Phase532Tests(unittest.TestCase):
    def test_all_rows_have_frozen_fields(self):
        for row in phase532.frontier_rows():
            self.assertTrue(all(field in row for field in phase532.FIELDS))
            self.assertEqual(
                row["gates_passed"], sum(row[field] for field in phase532.FIELDS)
            )

    def test_no_evidence_complete_row_exists(self):
        self.assertFalse([row for row in phase532.frontier_rows() if row["eligible"]])

    def test_p32_has_strong_terminal_oracle_but_no_input_selector(self):
        row = next(
            row
            for row in phase532.frontier_rows()
            if row["id"] == "p32_two_private_key_role"
        )
        self.assertTrue(row["expected_output_schema_fixed"])
        self.assertTrue(row["exact_terminal_validator"])
        self.assertFalse(row["independent_input_selector"])
        self.assertEqual(row["first_missing_field"], "independent_input_selector")

    def test_f09_is_only_operational_coverage_debt(self):
        debts = [
            row for row in phase532.frontier_rows() if row["operationally_runnable"]
        ]
        self.assertEqual(
            [row["id"] for row in debts], ["p32_tier1_nopad_whitespace"]
        )
        self.assertTrue(debts[0]["finite_uncovered_scope"])
        self.assertFalse(debts[0]["independent_input_selector"])

    def test_dbbi84_is_complete_but_covered(self):
        row = next(
            row
            for row in phase532.frontier_rows()
            if row["id"] == "dbbi84_direct_terminal_consumers"
        )
        self.assertEqual(row["gates_passed"], 5)
        self.assertFalse(row["finite_uncovered_scope"])
        self.assertFalse(row["eligible"])

    def test_soft_blob_validators_do_not_promote(self):
        for identifier in (
            "salph_local_password",
            "cosmic_local_container",
            "urlblob_orphan",
        ):
            row = next(row for row in phase532.frontier_rows() if row["id"] == identifier)
            self.assertFalse(row["exact_terminal_validator"])


if __name__ == "__main__":
    unittest.main()
