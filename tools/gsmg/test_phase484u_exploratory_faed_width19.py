import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(SCRIPT_DIR))
import phase484u_exploratory_faed_width19 as subject


class Phase484UExploratoryFaedTests(unittest.TestCase):
    def test_scope_and_input(self):
        subject.self_test()
        self.assertEqual(subject.budgets()["width"],19)
        self.assertEqual(subject.budgets()["pair_count"],36)

    def test_ranking(self):
        cells=[{"pair_index":1,"top1_final_normalized_score":-5.0},{"pair_index":0,"top1_final_normalized_score":-4.0},{"pair_index":2,"top1_final_normalized_score":None}]
        self.assertEqual([c["pair_index"] for c in subject.rank_cells(cells)],[0,1,2])

    def test_resume_rejects_hash_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"result.json";artifact=subject.new_artifact();artifact["implementation_sha256"]["runner"]="0"*64;path.write_text(json.dumps(artifact))
            with self.assertRaisesRegex(ValueError,"implementation_sha256"):subject.load_or_create(path)

    def test_observed_input_validation(self):
        with self.assertRaisesRegex(ValueError,"570"):subject.solver.screen_observed("abc",0)
        with self.assertRaisesRegex(ValueError,"outside a-i"):subject.solver.screen_observed("z"+subject.FAED[1:],0)
        with self.assertRaisesRegex(ValueError,"pair index"):subject.solver.screen_observed(subject.FAED,36)


if __name__=="__main__":unittest.main()
