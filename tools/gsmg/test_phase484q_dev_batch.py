import sys,unittest
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent;sys.path.insert(0,str(SCRIPT_DIR))
import phase484q_dev_batch as subject
class Phase484QBatchTests(unittest.TestCase):
    def test_fixed_batch_has_ten_fresh_indices_and_two_modes(self):
        self.assertEqual(subject.FIXTURE_INDICES,tuple(range(40,50)));self.assertEqual(len(subject.BOARD_MODES),2)
    def test_summary_separates_gate_and_conditional_recovery(self):
        cells=[{"board_mode":"vic_profile","true_segments_retained":0},{"board_mode":"vic_profile","true_segments_retained":1,"full_result":{"top1_exact_order":True}}]
        s=subject.summarize(cells)["vic_profile"];self.assertEqual(s["shortlist_retention_rate"],.5);self.assertEqual(s["conditional_exact_order_top1_rate"],1);self.assertEqual(s["unconditional_exact_order_top1_rate"],.5)
if __name__=="__main__":unittest.main()
