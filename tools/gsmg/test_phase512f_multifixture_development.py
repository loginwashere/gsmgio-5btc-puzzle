#!/usr/bin/env python3
from __future__ import annotations

import unittest

import phase512f_multifixture_development as phase512f


class Phase512FMultiFixtureDevelopmentTests(unittest.TestCase):
    def test_manifest_is_closed_and_balanced_across_widths(self):
        manifest = phase512f.default_manifest()
        positives = [row for row in manifest if row["kind"] == "present"]
        negatives = [row for row in manifest if row["kind"] == "absent"]
        self.assertEqual([row["width"] for row in positives], [15, 19, 30, 38])
        self.assertEqual(len(negatives), 1)
        self.assertEqual({row["crib_id"] for row in manifest},
                         {"phase1_credential"})

    def test_fixture_construction_is_deterministic(self):
        row = phase512f.default_manifest()[0]
        first = phase512f.fixture_for(row)
        second = phase512f.fixture_for(row)
        self.assertEqual(first["observed"], second["observed"])
        self.assertEqual(first["order"], second["order"])

    def test_self_test(self):
        self.assertEqual(phase512f.self_test()["self_test"], "pass")


if __name__ == "__main__":
    unittest.main()
