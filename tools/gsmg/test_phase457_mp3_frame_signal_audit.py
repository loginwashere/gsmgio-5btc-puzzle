#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase457_mp3_frame_signal_audit as audit


class Phase457Test(unittest.TestCase):
    def test_reproduces_signal_and_headers(self):
        result = audit.self_test()
        self.assertEqual(result["mpeg_frames"]["internal_mid_side_disabled_frames_1_based"], [4, 15, 131])
        self.assertEqual(result["interpretation"]["known_channel_payload"], "HASHTHETEXT")


if __name__ == "__main__":
    unittest.main()
