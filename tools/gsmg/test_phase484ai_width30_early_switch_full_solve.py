import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import phase484ai_width30_early_switch_full_solve as subject


class Phase484AIBlindControlFlowTests(unittest.TestCase):
    def test_schedule_hash_is_canonical_and_sensitive(self):
        reordered = dict(reversed(list(subject.SCHEDULE.items())))
        self.assertEqual(subject.schedule_sha256(),
                         subject.schedule_sha256(reordered))
        changed = dict(subject.SCHEDULE)
        changed["coarse_iterations"] += 1
        self.assertNotEqual(subject.schedule_sha256(),
                            subject.schedule_sha256(changed))

    def test_depth7_and_refine_run_even_when_truth_is_absent(self):
        fixture = {"order": list(range(30)), "pair": ["g", "i"]}
        paths6 = np.asarray([[0, 1, 2, 3, 4, 5]], dtype=np.uint8)
        scores6 = np.asarray([0.0])
        paths7 = np.asarray([[0, 1, 2, 3, 4, 5, 6]], dtype=np.uint8)
        score_calls = []

        def board_screen(paths, *args, **kwargs):
            score_calls.append(paths.shape[1])
            return np.zeros(len(paths), dtype=np.float64)

        def recovery_record(paths, scores, truth, depth):
            return {"true_segments": 0, "depth": depth}

        def select_diverse(paths, scores, keep):
            return paths, scores, len(paths)

        with tempfile.TemporaryDirectory() as directory, \
             mock.patch.object(subject.width30, "width30_fixture",
                               return_value=fixture), \
             mock.patch.object(subject.width30, "train_models",
                               return_value={}), \
             mock.patch.object(subject.prefix, "order_to_sequence",
                               return_value=list(range(30))), \
             mock.patch.object(subject.base, "load_language_model",
                               return_value=({}, None)), \
             mock.patch.object(subject.switch6, "invariant_to_switch_depth",
                               return_value=(paths6, scores6, [], [], ("g", "i"))), \
             mock.patch.object(subject.early, "board_screen",
                               side_effect=board_screen), \
             mock.patch.object(subject.early, "recovery_record",
                               side_effect=recovery_record), \
             mock.patch.object(subject.width30, "select_diverse",
                               side_effect=select_diverse), \
             mock.patch.object(subject.width30, "expand_bidirectional",
                               return_value=paths7):
            result = subject.initial_to_depth7(0, Path(directory), models={})

        self.assertEqual(score_calls, [6, 7, 7])
        self.assertIsNotNone(result["depth7_refined_checkpoint"])
        self.assertEqual(result["depth7"]["after_selection"]["true_segments"], 0)
        self.assertEqual(result["depth7"]["refine"]["after_selection"]["true_segments"], 0)


if __name__ == "__main__":
    unittest.main()
