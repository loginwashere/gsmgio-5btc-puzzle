#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase523_slot_grammar_overlap_audit as p523


class Phase523Tests(unittest.TestCase):
    def test_self_test_passes(self):
        result = p523.self_test()
        self.assertTrue(result["ok"], result["checks"])

    def test_slot_values_are_closed_and_sourced(self):
        values = p523.slot_values()
        self.assertEqual([len(values[s]) for s in p523.SLOT_ORDER], [15, 18, 19, 10])
        for slot in p523.SLOT_ORDER:
            for value, source in values[slot]:
                self.assertTrue(value)
                self.assertTrue(source)

    def test_enumeration_is_deterministic_and_deduplicated(self):
        first = list(p523.enumerate_bases())
        second = list(p523.enumerate_bases())
        self.assertEqual(first, second)
        bases = [b for _, b, _ in first]
        self.assertEqual(len(bases), len(set(bases)))
        # (15+1)(18+1)(19+1)(10+1) - 1 connected products, plus the spaced
        # multi-slot products, minus exact-string duplicates.
        connected = 16 * 19 * 20 * 11 - 1
        spaced_multi = connected - (15 + 18 + 19 + 10)
        self.assertEqual(len(bases) + p523.enumerate_bases.duplicates, connected + spaced_multi)

    def test_no_oracle_imported(self):
        names = set(dir(p523))
        for forbidden in ("aes_try_open", "aes_try_open_bytes", "passphrase_hits", "BLOBS"):
            self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
