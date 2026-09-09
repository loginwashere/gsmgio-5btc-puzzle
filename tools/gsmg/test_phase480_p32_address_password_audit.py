#!/usr/bin/env python3

import hashlib
import unittest

import phase480_p32_address_password_audit as audit


class Phase480AuditTests(unittest.TestCase):
    def test_self_test(self):
        self.assertTrue(audit.self_test())

    def test_material_manifest_is_exactly_four_by_two(self):
        rows = audit.material_rows()
        self.assertEqual(len(rows), 8)
        self.assertEqual({row["construction"] for row in rows}, set(audit.EXPECTED_CONSTRUCTIONS))
        self.assertEqual({row["level"] for row in rows}, set(audit.EXPECTED_LEVELS))
        self.assertEqual(len({row["material_b64"] for row in rows}), 8)

    def test_padding_alone_does_not_promote(self):
        weak = bytes(range(63)) + b"\x01"
        result = audit.classify_padded(weak)
        self.assertTrue(result["padding_valid"])
        self.assertFalse(result["promoted"])

    def test_binary_shape_promotes(self):
        body = hashlib.shake_256(b"phase480-test").digest(64)
        result = audit.classify_padded(body + b"\x10" * 16)
        self.assertTrue(result["structural_binary_64"])
        self.assertTrue(result["promoted"])


if __name__ == "__main__":
    unittest.main()
