#!/usr/bin/env python3
import sys
import unittest
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import cb_common
import cosmic_sweep_9ary
from data import (
    ALPHA_322,
    PHASE32_BLOB_B64,
    PHASE32_PASSWORD,
    VALIDATION_ANSWER_PREFIX,
    VALIDATION_ESCAPES,
    VALIDATION_NUM,
)


class CheckerboardTests(unittest.TestCase):
    def test_validation_vector_still_decodes(self):
        answer = cb_common.decode(
            VALIDATION_NUM,
            ALPHA_322,
            *VALIDATION_ESCAPES,
        )
        self.assertTrue(
            answer.replace(".", "").startswith(VALIDATION_ANSWER_PREFIX)
        )

    def test_decimal_dangling_escape_is_invalid(self):
        self.assertEqual(cb_common.decode("1", cb_common.pad28("seed"), 1, 2), "?")

    def test_9ary_dangling_escape_is_invalid(self):
        alphabet = cb_common.pad25("seed")
        self.assertEqual(
            cb_common.decode_9ary("b", alphabet, "b", "e"),
            "?",
        )

    def test_keyed_columnar_round_trip(self):
        for text in ("", "A", "ABCDEFGHIJKLMN", "uneven-column-length"):
            encrypted = cb_common.keyed_columnar(text, "matrixsumlist", "encrypt")
            self.assertEqual(
                cb_common.keyed_columnar(
                    encrypted,
                    "matrixsumlist",
                    "decrypt",
                ),
                text,
            )

    def test_invalid_algorithm_options_raise(self):
        alphabet = cb_common.pad25("seed")
        with self.assertRaises(ValueError):
            cb_common.pad25("seed", merge_direction="typo")
        with self.assertRaises(ValueError):
            cb_common.build_board_9ary(alphabet, "b", "e", "typo")
        with self.assertRaises(ValueError):
            cb_common.autokey_dechain_9ary("abc", [1], mode="typo")
        with self.assertRaises(ValueError):
            cb_common.keyed_columnar("abc", "key", "typo")
        with self.assertRaises(ValueError):
            cb_common.transpose("abc", "col0")


class AesOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        salt, ciphertext = cb_common._load_blob(PHASE32_BLOB_B64)
        cls.phase32_blobs = {"PHASE32": (salt, ciphertext)}

    def test_known_positive_vector(self):
        result = cb_common.aes_try_open(
            PHASE32_PASSWORD,
            [("sha256", 32)],
            self.phase32_blobs,
        )
        self.assertIsNotNone(result)

    def test_explicit_empty_kdf_scope_stays_empty(self):
        result = cb_common.aes_try_open(
            PHASE32_PASSWORD,
            [],
            self.phase32_blobs,
        )
        self.assertIsNone(result)

    def test_explicit_empty_blob_scope_stays_empty(self):
        result = cb_common.aes_try_open(
            PHASE32_PASSWORD,
            [("sha256", 32)],
            {},
        )
        self.assertIsNone(result)

    def test_binary_structural_gate_is_exact(self):
        body = bytes(range(64))
        self.assertTrue(
            cb_common.is_structural_binary_plaintext("aes", 16, 16, body)
        )
        self.assertFalse(
            cb_common.is_structural_binary_plaintext("aes", 16, 15, body)
        )
        self.assertFalse(
            cb_common.is_structural_binary_plaintext("3des", 8, 8, body)
        )
        self.assertFalse(
            cb_common.is_structural_binary_plaintext("aes", 16, 16, body[:-1])
        )


class MultiprocessingTests(unittest.TestCase):
    def test_9ary_config_survives_spawn(self):
        config = cosmic_sweep_9ary.DEFAULT_CONFIG._replace(
            input_transforms=("mirror9",),
        )
        with ProcessPoolExecutor(
            max_workers=1,
            mp_context=get_context("spawn"),
        ) as executor:
            result = executor.submit(
                cosmic_sweep_9ary.test_batch,
                ["duality"],
                ["dbbi"],
                config,
            ).result(timeout=30)
        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()
