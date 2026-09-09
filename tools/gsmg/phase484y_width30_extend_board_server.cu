// Width-30 fixed-board extension scorer for the blind joint solver.
//
// Deliberately uses the DEFAULT identity NEXT_INDEX (unlike
// phase484y_width30_board_score_server.cu's {g,i}-corrected oracle kernel):
// boards fed to this kernel come from phase484y_width30_coarse_board_server.
// cu's free anneal, which lays out its own board in the same uncorrected
// "7+symbol*9+next" convention.  Composing two kernels that both use that
// convention self-consistently is correct; mixing this kernel with the
// absolute-alphabet convention (planted_board()/slot_codes()) is not.  See
// the Phase 484Y write-up in doc/Brainstorms for the derivation.
#define PHASE484_BOARD_WIDTH 30
#define PHASE484_BOARD_ROWS 19
#define PHASE484_BOARD_MAGIC "P484YE1\0"
#include "phase484o_board_score_server.cu"
