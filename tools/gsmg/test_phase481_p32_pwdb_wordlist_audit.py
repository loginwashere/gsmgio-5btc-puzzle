#!/usr/bin/env python3

import hashlib
import tempfile
import unittest
from pathlib import Path

import phase481_p32_pwdb_wordlist_audit as audit


class Phase481AuditTests(unittest.TestCase):
    def test_self_test(self):
        self.assertTrue(audit.self_test())

    def test_wordlist_stats_on_synthetic_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_bytes(b"alpha\nbeta\nalpha\n\ngamma")
            stats = audit.wordlist_stats(path)
            self.assertEqual(stats["line_count"], 5)
            self.assertEqual(stats["blank_lines"], 1)
            self.assertEqual(stats["duplicate_lines"], 1)
            self.assertEqual(stats["unique_lines"], 4)
            self.assertEqual(stats["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_iter_candidates_preserves_whitespace(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_bytes(b"abc\n  spaced  \nlast-no-newline")
            self.assertEqual(
                list(audit.iter_candidates(path)),
                [b"abc", b"  spaced  ", b"last-no-newline"],
            )

    def test_padding_alone_does_not_promote(self):
        weak = bytes(range(63)) + b"\x01"
        result = audit.classify_padded(weak)
        self.assertTrue(result["padding_valid"])
        self.assertFalse(result["promoted"])

    def test_binary_shape_promotes(self):
        body = hashlib.shake_256(b"phase481-test").digest(64)
        result = audit.classify_padded(body + b"\x10" * 16)
        self.assertTrue(result["structural_binary_64"])
        self.assertTrue(result["promoted"])

    def test_strong_text_promotes(self):
        password, salt = b"phase481-unit-test", b"UNITTEST"
        text = b"Deliberately printable synthetic control body for this unit test only."
        ciphertext = audit.encrypt_for_test(text, password, salt)
        padded = audit.decrypt_padded(password, salt, ciphertext)
        result = audit.classify_padded(padded)
        self.assertTrue(result["strong_text"])
        self.assertTrue(result["promoted"])

    def test_run_end_to_end_on_synthetic_wordlist(self):
        original = {
            "WORDLIST_PATH": audit.WORDLIST_PATH,
            "EXPECTED_WORDLIST_SHA256": audit.EXPECTED_WORDLIST_SHA256,
            "EXPECTED_LINE_COUNT": audit.EXPECTED_LINE_COUNT,
            "EXPECTED_BLANK_LINES": audit.EXPECTED_BLANK_LINES,
            "EXPECTED_DUPLICATE_LINES": audit.EXPECTED_DUPLICATE_LINES,
        }
        try:
            with tempfile.TemporaryDirectory() as directory:
                directory = Path(directory)
                wordlist = directory / "tiny_wordlist.txt"
                wordlist.write_bytes(b"correct-horse\nbattery-staple\nqwerty123\n")
                audit.WORDLIST_PATH = wordlist
                stats = audit.wordlist_stats(wordlist)
                audit.EXPECTED_WORDLIST_SHA256 = stats["sha256"]
                audit.EXPECTED_LINE_COUNT = stats["line_count"]
                audit.EXPECTED_BLANK_LINES = stats["blank_lines"]
                audit.EXPECTED_DUPLICATE_LINES = stats["duplicate_lines"]

                lock_path = directory / "lock.json"
                result_path = directory / "result.json"
                hits_path = directory / "hits.jsonl"
                weak_path = directory / "weak.jsonl"

                audit.issue_lock(lock_path)
                result = audit.run(lock_path, result_path, hits_path, weak_path, progress_every=0)

                self.assertEqual(result["attempted"], 3)
                self.assertEqual(result["promoted_count"], 0)
                self.assertEqual(result["verdict"], "bounded_negative")
                self.assertFalse(hits_path.exists())
                self.assertFalse(weak_path.exists())
        finally:
            for name, value in original.items():
                setattr(audit, name, value)

    def test_run_refuses_existing_hits_file(self):
        original = {
            "WORDLIST_PATH": audit.WORDLIST_PATH,
            "EXPECTED_WORDLIST_SHA256": audit.EXPECTED_WORDLIST_SHA256,
            "EXPECTED_LINE_COUNT": audit.EXPECTED_LINE_COUNT,
            "EXPECTED_BLANK_LINES": audit.EXPECTED_BLANK_LINES,
            "EXPECTED_DUPLICATE_LINES": audit.EXPECTED_DUPLICATE_LINES,
        }
        try:
            with tempfile.TemporaryDirectory() as directory:
                directory = Path(directory)
                wordlist = directory / "tiny_wordlist.txt"
                wordlist.write_bytes(b"one\ntwo\n")
                audit.WORDLIST_PATH = wordlist
                stats = audit.wordlist_stats(wordlist)
                audit.EXPECTED_WORDLIST_SHA256 = stats["sha256"]
                audit.EXPECTED_LINE_COUNT = stats["line_count"]
                audit.EXPECTED_BLANK_LINES = stats["blank_lines"]
                audit.EXPECTED_DUPLICATE_LINES = stats["duplicate_lines"]

                lock_path = directory / "lock.json"
                audit.issue_lock(lock_path)
                hits_path = directory / "hits.jsonl"
                hits_path.write_text("preexisting\n", encoding="utf-8")
                with self.assertRaises(FileExistsError):
                    audit.run(
                        lock_path,
                        directory / "result.json",
                        hits_path,
                        directory / "weak.jsonl",
                        progress_every=0,
                    )
        finally:
            for name, value in original.items():
                setattr(audit, name, value)


if __name__ == "__main__":
    unittest.main()
