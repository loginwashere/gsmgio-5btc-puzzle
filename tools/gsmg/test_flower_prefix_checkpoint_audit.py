#!/usr/bin/env python3

import unittest

import flower_prefix_checkpoint_audit as audit


class FlowerPrefixCheckpointAuditTest(unittest.TestCase):
    def test_authenticated_prefix_family(self):
        audit.self_test(run_oracle=False)


if __name__ == "__main__":
    unittest.main()
