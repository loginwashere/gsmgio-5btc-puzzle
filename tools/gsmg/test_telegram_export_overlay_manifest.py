#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import telegram_export_overlay_manifest as overlay


class TelegramOverlayManifestTest(unittest.TestCase):
    def test_current_overlay_invariants(self):
        summary = overlay.self_test()
        self.assertEqual(summary["total_messages"], 60_375)
        self.assertEqual(summary["last_date_unixtime"], 1_788_071_394)


if __name__ == "__main__":
    unittest.main()
