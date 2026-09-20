#!/usr/bin/env python3
import random
import sys
import unittest
from pathlib import Path

import coincurve

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase539_base9_scalar_all_bijections as p539


class Phase539Tests(unittest.TestCase):
    def test_validator_control(self):
        self.assertTrue(all(p539.control_validator().values()), p539.control_validator())

    def test_phase318_digit_arithmetic(self):
        self.assertTrue(p539.control_digit_arithmetic())

    def test_target_strings(self):
        s = p539.target_strings()
        self.assertEqual([len(s[k]) for k in ("P83", "P84", "DBBI")], [60, 61, 91])
        self.assertTrue(all(set(v) == set(p539.SYMS) for v in s.values()))
        self.assertTrue(s["P84"].endswith("e"))

    def test_no_oracle_in_namespace(self):
        for name in ("aes_try_open", "aes_try_open_bytes", "passphrase_hits", "BLOBS"):
            self.assertNotIn(name, dir(p539))

    def test_candidate_count(self):
        want = p539.expected_lock_fields()
        self.assertEqual(want["candidate_scalars"], 3 * 2 * 2 * 362_880)
        self.assertEqual(len(want["target_hash160"]), 11)

    def test_planted_recovery_on_a_pair_subset(self):
        s = p539.target_strings()["P83"]
        for direction in p539.DIRECTIONS:
            for conv in p539.CONVENTIONS:
                rng = random.Random(1)
                sigma = tuple(rng.sample(range(9), 9))
                w, r = p539.weights(s, direction)
                k = p539.scalar(w, r, conv, sigma)
                pk = coincurve.PublicKey.from_secret(k.to_bytes(32, "big"))
                synthetic = {p539.hash160(pk.format(compressed=False)): "planted"}
                pair = [(sigma[0], sigma[1]), (sigma[1], sigma[0])]
                checked, matches = p539.scan(s, direction, conv, synthetic, pairs=pair)
                self.assertEqual(checked, 2 * 5040)
                self.assertEqual({m[1] for m in matches}, {sigma})
                self.assertEqual({m[2] for m in matches}, {"uncompressed"})

    def test_no_planted_target_gives_no_match(self):
        s = p539.target_strings()["P84"]
        checked, matches = p539.scan(s, "forward", "D0", {b"\x00" * 20: "none"}, pairs=[(0, 1)])
        self.assertEqual((checked, matches), (5040, []))

    def test_lock_fields_are_deterministic(self):
        self.assertEqual(p539.expected_lock_fields(), p539.expected_lock_fields())


if __name__ == "__main__":
    unittest.main()
