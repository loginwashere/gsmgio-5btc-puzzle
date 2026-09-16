import json,tempfile,unittest
from pathlib import Path
from unittest import mock
import phase503_repaired_holdout_replacement as p

class Tests(unittest.TestCase):
    def test_self_test(self): self.assertTrue(p.self_test()['eligible'])
    def test_prior(self): self.assertTrue(p.prior_result()['top1_exact_order'])
    def test_marker_fails_closed(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(p,'WORK_DIR',Path(d)), mock.patch.object(p,'marker_payload',return_value={'phase':503}):
            p.ensure_marker(); (Path(d)/'objective_marker.json').write_text('{}\n')
            with self.assertRaises(RuntimeError): p.ensure_marker()
if __name__=='__main__': unittest.main()
