#!/usr/bin/env python3
"""Regression tests for the Phase 480 no-oracle novelty comparator."""

import hashlib
import unittest

import phase480_address_novelty_comparator as audit


class Phase480AddressNoveltyComparatorTests(unittest.TestCase):
    def test_frozen_address_constructions(self):
        preimages = audit.proposed_preimages()
        self.assertEqual(
            tuple(preimages),
            (
                "prize_then_halving",
                "halving_then_prize",
                "banner_prize_halving",
                "banner_halving_prize",
            ),
        )
        self.assertEqual({len(value) for value in preimages.values()}, {68, 93})
        self.assertEqual(len(set(preimages.values())), 4)

    def test_material_levels_are_exactly_preimage_and_sha256_hex(self):
        materials = audit.proposed_materials()
        self.assertEqual(len(materials), 8)
        for label, preimage in audit.proposed_preimages().items():
            password = hashlib.sha256(preimage).hexdigest().encode("ascii")
            self.assertEqual(
                materials[preimage],
                [{"construction": label, "level": "preimage"}],
            )
            self.assertEqual(
                materials[password],
                [{"construction": label, "level": "sha256_hex_password"}],
            )

    def test_phase416_frozen_reconstruction_count(self):
        self.assertEqual(len(set(audit._phase416_tested_materials())), 8)

    def test_phase421_evaluated_reconstruction_count(self):
        self.assertEqual(len(set(audit._phase421_evaluated_materials())), 16)


if __name__ == "__main__":
    unittest.main()
