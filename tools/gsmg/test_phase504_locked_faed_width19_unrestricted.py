import json,tempfile,unittest
from pathlib import Path
from unittest import mock
import phase504_locked_faed_width19_unrestricted as p

class Tests(unittest.TestCase):
    def test_self_test(self): self.assertTrue(p.self_test()['qualified'])
    def test_adapter(self):
        f=p.real_fixture(); self.assertEqual(f['observed'],p.FAED); self.assertEqual(f['pair'],['g','i'])
    def test_sanitize_removes_sentinel_truth(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'continuation').mkdir()
            path=root/'continuation/depth9.json'; path.write_text(json.dumps({'before_selection':{'true_segments':1,'candidate_count':2},'after_selection':{'best_true_rank':1}}))
            p.sanitize(root); r=json.loads(path.read_text())
            self.assertNotIn('true_segments',r['before_selection']); self.assertNotIn('best_true_rank',r['after_selection'])
if __name__=='__main__': unittest.main()
