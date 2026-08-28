#!/usr/bin/env python3

import math
import unittest

import phase431_bifid16_equivalence_class_audit as audit


class Phase431EquivalenceTests(unittest.TestCase):
    def test_exact_census(self):
        result = audit.audit()
        results = result["results"]
        self.assertEqual(results["canonical_template_count"], 240)
        self.assertEqual(results["cross_placement_template_collisions"], 0)
        self.assertEqual(
            results["placement_count_by_visible_other_free_cells"],
            {"5": 42, "10": 6, "11": 12, "12": 38, "13": 12, "14": 130},
        )
        self.assertEqual(results["unique_decoded_outputs"], 14_231_866_128_480)
        self.assertEqual(results["rank_count_reconstructed_from_classes"], math.factorial(16))

    def test_invisible_cell_swap_is_exact_output_equivalence(self):
        g_position, h_position = 7, 10
        visible = audit.visible_free_cells(g_position, h_position)
        remaining = [
            cell
            for cell in audit.FREE_POSITIONS
            if cell not in {g_position, h_position}
        ]
        invisible = [cell for cell in remaining if cell not in visible]
        self.assertEqual(len(visible), 5)
        self.assertEqual(len(invisible), 9)

        assignments = dict(zip(remaining, audit.OTHER_FREE_SYMBOLS))
        first = audit.decode_square(
            audit.square_for_placement(g_position, h_position, assignments)
        )
        assignments[invisible[0]], assignments[invisible[1]] = (
            assignments[invisible[1]],
            assignments[invisible[0]],
        )
        second = audit.decode_square(
            audit.square_for_placement(g_position, h_position, assignments)
        )
        self.assertEqual(first, second)

    def test_visible_cell_swap_changes_output(self):
        g_position, h_position = 7, 10
        visible = sorted(audit.visible_free_cells(g_position, h_position))
        remaining = [
            cell
            for cell in audit.FREE_POSITIONS
            if cell not in {g_position, h_position}
        ]
        assignments = dict(zip(remaining, audit.OTHER_FREE_SYMBOLS))
        first = audit.decode_square(
            audit.square_for_placement(g_position, h_position, assignments)
        )
        assignments[visible[0]], assignments[visible[1]] = (
            assignments[visible[1]],
            assignments[visible[0]],
        )
        second = audit.decode_square(
            audit.square_for_placement(g_position, h_position, assignments)
        )
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
