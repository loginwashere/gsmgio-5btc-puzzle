import unittest

import phase500_holdout0_depth11_bridge_postmortem as phase500


class Phase500Tests(unittest.TestCase):
    def test_self_test(self):
        result = phase500.self_test()
        self.assertFalse(result["faed_scored"])
        self.assertFalse(result["phase499_gate_can_be_rescued"])

    def test_inputs_identify_one_true_parent(self):
        paths, _ = phase500.verify_inputs()
        fixture = phase500.phase499.make_holdout_variant(0)
        truth = phase500.prefix.order_to_sequence(fixture["order"])
        self.assertEqual(int(phase500.true_mask(paths, truth, 10).sum()), 1)


if __name__ == "__main__":
    unittest.main()
