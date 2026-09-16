import collections
import unittest

import phase493_partial_unrestricted_board_diagnostic as phase493
import phase491_raw_histogram_fixture as rawonly


class Phase493Tests(unittest.TestCase):
    def test_canonical_codes_are_complete(self):
        codes = phase493.canonical_codes()
        self.assertEqual(len(codes), 25)
        self.assertEqual(set(codes), set(phase493.base.slot_codes(rawonly.PAIR)))

    def test_partition_swap_distance(self):
        fixture = phase493.make_variant(0, 2)
        common, _ = rawonly.training_groups()
        singles = {letter for letter, code in fixture["letter_to_code"].items()
                   if len(code) == 1}
        self.assertEqual(len(set(common) - singles), 2)
        self.assertEqual(collections.Counter(fixture["raw"]),
                         collections.Counter(rawonly.RAW_COUNTS))

    def test_control_paths_exclude_truth(self):
        truth = {(0, 1, 2, 3, 4, 5)}
        controls = phase493.control_paths(19, 6, 0, 1, truth)
        self.assertEqual(len(controls), phase493.CONTROLS)
        self.assertNotIn((0, 1, 2, 3, 4, 5), {tuple(x) for x in controls})

    def test_self_test(self):
        self.assertFalse(phase493.self_test()["faed_scored"])


if __name__ == "__main__":
    unittest.main()
