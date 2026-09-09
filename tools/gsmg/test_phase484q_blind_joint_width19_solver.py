import itertools,sys,unittest
from pathlib import Path
import numpy as np
SCRIPT_DIR=Path(__file__).resolve().parent;sys.path.insert(0,str(SCRIPT_DIR))
import phase484q_blind_joint_width19_solver as subject
class Phase484QTests(unittest.TestCase):
    def test_initial_board_is_permutation(self):self.assertEqual(sorted(subject.initial_board(subject.SEED,(7,3,11,2)).tolist()),list(range(25)))
    def test_fragment_seed_depends_on_path_not_shortlist_position(self):
        path=(7,3,11,2)
        self.assertEqual(subject.fragment_seed(subject.SEED,path),subject.fragment_seed(subject.SEED,tuple(path)))
        self.assertNotEqual(subject.fragment_seed(subject.SEED,path),subject.fragment_seed(subject.SEED,(3,7,11,2)))
    def test_cpu_recompute_matches_partial_probe(self):
        fixture=subject.base.make_fixture(19,subject.learned.PAIR_INDEX,23,seed=subject.learned.SEED,board_mode="vic_profile",split="dev");blocks=subject.prefix.blocks_from_observed(fixture);quad,_=subject.base.load_language_model();path=next(itertools.permutations(range(19),8));board=np.arange(25);score,windows=subject.cpu_recompute(blocks,tuple(fixture["pair"]),quad,path,board);rows=subject.partial.token_rows(blocks,tuple(fixture["pair"]),path);self.assertEqual(windows,subject.partial.row_windows(rows));self.assertAlmostEqual(score,subject.partial.row_score(board,rows,quad)/max(1,windows))
    def test_multistart_keeps_each_paths_best_score(self):
        old=subject.gpu_coarse_screen
        try:
            calls=[]
            def fake(*args,**kwargs):
                restart=len(calls);calls.append(restart);scores=np.array([restart,2-restart],dtype=float);return scores,np.array([3,4]),np.tile(np.arange(25,dtype=np.uint8),(2,1))
            subject.gpu_coarse_screen=fake
            scores,windows,boards,restarts=subject.gpu_multistart_screen(None,None,None,None,[(),()],restarts=3)
            np.testing.assert_array_equal(scores,[2,2]);np.testing.assert_array_equal(windows,[3,4]);np.testing.assert_array_equal(restarts,[2,0])
        finally:subject.gpu_coarse_screen=old
    def test_extend_population_deduplicates_terminal_orders(self):
        old=subject.extend_seed
        try:
            subject.extend_seed=lambda *a,**k:([(2.0,(0,1)),(1.0,(1,0))],[])
            records=[{"rank":1,"shortlist_index":3},{"rank":2,"shortlist_index":4}]
            terminal,diagnostics=subject.extend_population(None,None,None,records,seed_count=2,terminals_per_seed=2)
            self.assertEqual(len(terminal),2);self.assertEqual(terminal[0]["extension_rank"],1);self.assertEqual(len(diagnostics),2)
        finally:subject.extend_seed=old
    def test_extension_backend_rejects_unknown_name(self):
        with self.assertRaisesRegex(ValueError,"unknown extension backend"):
            subject.run_extension_backend(None,None,None,[],backend="bogus")
    def test_shortlist_capacity_only_expands_final_depth(self):
        self.assertEqual(subject.shortlist_capacity(7,262144,1048576),262144)
        self.assertEqual(subject.shortlist_capacity(8,262144,1048576),1048576)
    def test_fixture_override_rejects_wrong_width(self):
        fixture=subject.base.make_fixture(10,0,0,board_mode="vic_profile",split="dev")
        with self.assertRaisesRegex(ValueError,"width 19"):
            subject.screen_fixture(fixture_override=fixture)
    def test_quadgram_verification_uses_wide_integer_keys(self):
        quad=np.arange(25**4,dtype=float);letters=np.array([24,24,24,24],dtype=np.uint8)
        narrow=subject.base.score_indices(letters,quad);wide=subject.base.score_indices(letters.astype(np.int64),quad)
        self.assertNotEqual(narrow,wide);self.assertEqual(wide,25**4-1)
    def test_complete_token_slots_nonstrict_returns_none_on_failed_segmentation(self):
        fixture=subject.base.make_fixture(19,subject.learned.PAIR_INDEX,23,seed=subject.learned.SEED,board_mode="vic_profile",split="dev");blocks=subject.prefix.blocks_from_observed(fixture);pair=tuple(fixture["pair"]);truth=subject.prefix.order_to_sequence(fixture["order"])
        good=subject.complete_token_slots(blocks,pair,truth,strict=False);self.assertIsNotNone(good)
        old=subject.base.segment_raw
        try:
            subject.base.segment_raw=lambda raw,pair:None
            self.assertIsNone(subject.complete_token_slots(blocks,pair,truth,strict=False))
            with self.assertRaises(ValueError):subject.complete_token_slots(blocks,pair,truth,strict=True)
        finally:subject.base.segment_raw=old
    def test_resolve_terminals_skips_invalid_segmentations_instead_of_crashing(self):
        old_complete,old_multistart=subject.complete_token_slots,subject.gpu_full_multistart
        try:
            def fake_complete(blocks,pair,order,strict=True):
                return None if order==(0,) else np.array([1,2,3,4],dtype=np.int64)
            subject.complete_token_slots=fake_complete
            def fake_multistart(binary,token_rows,quad,restarts,iterations):
                n=len(token_rows);return np.arange(n,dtype=float),np.tile(np.arange(25,dtype=np.uint8),(n,1)),np.zeros(n,dtype=np.int64)
            subject.gpu_full_multistart=fake_multistart
            terminals=[{"order":(0,),"extension_rank":1},{"order":(1,),"extension_rank":2},{"order":(2,),"extension_rank":3}]
            ranked,skipped=subject.resolve_terminals(None,None,None,terminals)
            self.assertEqual([r["order"] for r in skipped],[(0,)])
            self.assertEqual(len(ranked),2);self.assertEqual(ranked[0]["order"],(2,));self.assertEqual(ranked[1]["order"],(1,))
        finally:subject.complete_token_slots,subject.gpu_full_multistart=old_complete,old_multistart
    def test_resolve_terminals_skips_all_returns_empty_ranked(self):
        old_complete=subject.complete_token_slots
        try:
            subject.complete_token_slots=lambda blocks,pair,order,strict=True:None
            ranked,skipped=subject.resolve_terminals(None,None,None,[{"order":(0,),"extension_rank":1}])
            self.assertEqual(ranked,[]);self.assertEqual(len(skipped),1)
        finally:subject.complete_token_slots=old_complete
if __name__=="__main__":unittest.main()
