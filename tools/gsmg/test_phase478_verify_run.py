#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from phase478_verify_run import VerificationError, verify


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Phase478VerifyRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        gsmg = self.root / 'tools/gsmg'
        gsmg.mkdir(parents=True)

        self.pattern = '012345'
        self.report = {
            'eligible_scored': 1,
            'target_pattern': self.pattern,
            'match_found': False,
        }
        self.files = {
            'manifest': gsmg / 'manifest.jsonl',
            'annotations': gsmg / 'annotations.json',
            'builder': gsmg / 'builder.py',
            'matcher': gsmg / 'matcher.py',
            'common': gsmg / 'phase478_common.py',
            'report': gsmg / 'report.json',
            'lock': gsmg / 'lock.json',
        }
        self.files['manifest'].write_text(
            json.dumps({'eligible': False, 'bytes_b64': ''}) + '\n'
        )
        self.files['annotations'].write_text('{}\n')
        self.files['builder'].write_text('# pinned builder\n')
        self.files['common'].write_text(
            f"DBBI_PATTERN = {self.pattern!r}\n"
            "def equality_pattern(values):\n"
            "    return ''.join(values)\n"
        )
        self.files['matcher'].write_text(
            'from phase478_common import DBBI_PATTERN\n'
            f'_REPORT = {self.report!r}\n'
            'def run_matcher(_manifest_path):\n'
            '    return dict(_REPORT)\n'
        )
        self.files['report'].write_text(json.dumps(self.report))

        self.lock = {
            'phase': 478,
            'lock_kind': 'oracle_lock',
            'manifest_path': 'tools/gsmg/manifest.jsonl',
            'manifest_sha256': digest(self.files['manifest']),
            'manifest_annotations_path': 'tools/gsmg/annotations.json',
            'manifest_annotations_sha256': digest(self.files['annotations']),
            'manifest_builder_script': 'tools/gsmg/builder.py',
            'manifest_builder_script_sha256': digest(self.files['builder']),
            'matcher_script': 'tools/gsmg/matcher.py',
            'matcher_script_sha256': digest(self.files['matcher']),
            'phase478_common_sha256': digest(self.files['common']),
            'dbbi_pattern': self.pattern,
        }
        self.write_lock()

    def tearDown(self):
        self.temp.cleanup()

    def write_lock(self):
        self.files['lock'].write_text(json.dumps(self.lock))

    def run_verify(self):
        return verify(
            self.files['lock'],
            self.files['report'],
            repo_root=self.root,
        )

    def assert_hash_rejected(self, key, path):
        path.write_text(path.read_text() + '# tampered\n')
        with self.assertRaisesRegex(VerificationError, key):
            self.run_verify()

    def test_valid_fixture_verifies(self):
        record = self.run_verify()
        self.assertTrue(record['consistent'])
        self.assertEqual(record['eligible_scored'], 1)
        self.assertFalse(record['match_found'])
        self.assertEqual(set(record['checked_hashes']), {
            'manifest',
            'manifest_annotations',
            'manifest_builder_script',
            'matcher_script',
            'phase478_common',
        })

    def test_common_hash_mismatch_is_rejected(self):
        self.assert_hash_rejected('phase478_common', self.files['common'])

    def test_manifest_hash_mismatch_is_rejected(self):
        self.assert_hash_rejected('manifest', self.files['manifest'])

    def test_annotations_hash_mismatch_is_rejected(self):
        self.assert_hash_rejected('manifest_annotations', self.files['annotations'])

    def test_builder_hash_mismatch_is_rejected(self):
        self.assert_hash_rejected('manifest_builder_script', self.files['builder'])

    def test_matcher_hash_mismatch_is_rejected(self):
        self.assert_hash_rejected('matcher_script', self.files['matcher'])

    def test_dbbi_pattern_mismatch_is_rejected(self):
        self.lock['dbbi_pattern'] = '654321'
        self.write_lock()
        with self.assertRaisesRegex(VerificationError, 'DBBI pattern'):
            self.run_verify()

    def test_saved_report_mismatch_is_rejected(self):
        self.files['report'].write_text(json.dumps({
            **self.report,
            'eligible_scored': 2,
        }))
        with self.assertRaisesRegex(VerificationError, 'saved report'):
            self.run_verify()


if __name__ == '__main__':
    unittest.main()
