#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase485_ring_endpoint_747474_audit as audit


class Phase485RingEndpointTests(unittest.TestCase):
    def test_ring_partition_is_exact(self):
        rows = audit.ring_rows()
        self.assertEqual(sum(row["length"] for row in rows), 196)
        self.assertEqual([row["start_spiral_0"] for row in rows], [0, 52, 96, 132, 160, 180, 192])
        self.assertEqual([row["end_spiral_0"] for row in rows], [51, 95, 131, 159, 179, 191, 195])

    def test_six_text_rings_land_on_ossaed(self):
        rows = [row for row in audit.ring_rows() if row["text_bearing"]]
        self.assertEqual("".join(row["landing_character"] for row in rows), "ossaed")
        self.assertEqual([row["end_bit_offset_0"] for row in rows], [3, 7, 3, 7, 3, 7])

    def test_center_ring_is_four_zero_tail_bits(self):
        report = audit.audit()
        self.assertEqual(report["center_tail_bits"], "0000")
        self.assertIsNone(report["rings"][-1]["landing_character"])

    def test_exact_selector_yields_ascii_multiplication(self):
        result = audit.extract_selector_bits("ossaed", "747474", index_base=0)
        self.assertEqual(result["selected_bits"], "101010")
        self.assertEqual(result["value"], 42)
        self.assertEqual(result["ascii_if_printable"], "*")

    def test_opposite_phase_is_ascii_four(self):
        result = audit.extract_selector_bits("ossaed", "474747", index_base=0)
        self.assertEqual(result["selected_bits"], "110100")
        self.assertEqual(result["ascii_if_printable"], "4")

    def test_index_base_and_length_fail_closed(self):
        self.assertEqual(
            audit.extract_selector_bits("ossaed", "747474", index_base=1)["ascii_if_printable"],
            "8",
        )
        with self.assertRaises(ValueError):
            audit.extract_selector_bits("ossaed", "74747", index_base=0)
        with self.assertRaises(ValueError):
            audit.extract_selector_bits("ossaed", "848484", index_base=0)

    def test_product_bridge_does_not_invent_consumer(self):
        report = audit.audit()
        bridge = report["operation_bridge"]
        self.assertEqual(bridge["canonical_product"], (255, 103))
        self.assertEqual(bridge["canonical_serialized_hex_if_bytes"], "FF67")
        self.assertTrue(bridge["multiplication_selected_if_selector_authenticated"])
        self.assertFalse(bridge["byte_consumer_selected"])
        self.assertFalse(report["ring_endpoint_rule"]["authenticated"])
        self.assertFalse(report["disposition"]["matrix_product_gap_closed"])
        self.assertFalse(report["oracle_run"])


if __name__ == "__main__":
    unittest.main()

