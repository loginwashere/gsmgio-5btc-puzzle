#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase524_slot_grammar_sweep_prep as p524


class Phase524Tests(unittest.TestCase):
    def test_self_test_passes(self):
        self.assertTrue(p524.self_test()["ok"])

    def test_no_decrypt_function_in_namespace(self):
        names = set(dir(p524))
        for forbidden in ("aes_try_open", "aes_try_open_bytes", "passphrase_hits", "BLOBS"):
            self.assertNotIn(forbidden, names)

    def test_summarize_output_counts_kinds_without_plaintext(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "hits.jsonl"
            rows = [
                {"hit_kind": "weak", "blob_tag": "SALPH", "body_preview": "secret"},
                {"hit_kind": "weak", "blob_tag": "COSMIC", "body_preview": "secret"},
                {"hit_kind": "strong", "blob_tag": "SALPH", "kdf": "x", "candidate_source": "c", "z_score": 9.0,
                 "body_preview": "secret"},
            ]
            path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
            counts, notable = p524.summarize_output(path)
            self.assertEqual(counts["weak"], 2)
            self.assertEqual(counts["strong"], 1)
            self.assertEqual(len(notable), 1)
            self.assertNotIn("body_preview", notable[0])

    def test_variant_label_parser(self):
        ok = ["legacy-md5/aes-128-cfb", "legacy-sha256/aes-256-ofb", "pbkdf2-sha256-10000/aes-192-ctr",
              "legacy-sha1/aes-256-cbc", "legacy-md5/aes-128-ecb"]
        for label in ok:
            self.assertIsNotNone(p524._LABEL.match(label), label)
        for label in ("legacy-md5/seed-128-cbc", "legacy-sha512/aes-256-cbc", "pbkdf2-sha256/aes-256-cbc"):
            self.assertIsNone(p524._LABEL.match(label), label)

    def test_derive_body_round_trip_on_synthetic_blob(self):
        import cb_common as cb
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        salt = bytes(range(8))
        plaintext = b"synthetic body " * 5
        key, iv = cb.evp_bytes_to_key(b"pw", salt, "sha256", 32, 16)
        ct = Cipher(algorithms.AES(key), modes.CFB(iv)).encryptor().update(plaintext)
        cb.BLOBS["SYNTH"] = (salt, ct)
        try:
            self.assertEqual(p524._derive_body("pw", "legacy-sha256/aes-256-cfb", "SYNTH"), plaintext)
            self.assertNotEqual(p524._derive_body("wrong", "legacy-sha256/aes-256-cfb", "SYNTH"), plaintext)
        finally:
            del cb.BLOBS["SYNTH"]

    def test_missing_output_is_empty(self):
        counts, notable = p524.summarize_output("/nonexistent/hits.jsonl")
        self.assertEqual(sum(counts.values()), 0)
        self.assertEqual(notable, [])


if __name__ == "__main__":
    unittest.main()
