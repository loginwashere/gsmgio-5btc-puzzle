#!/usr/bin/env python3
"""Is Phase 354's 7x7 `#FAFAFA` tile locked to the QR's native modules?

Uses the complete logical 49x49 finder eyes (7 modules x 7 pixels), rather
than the earlier 48x49 pure-black-component bounding boxes. The three eyes are
182 pixels apart horizontally/vertically: exactly 26 Version-4 QR modules at
7 pixels/module. A standard finder has sixteen white-ring modules. Learn one
7x7 subpixel tile from 15 modules and predict the held-out sixteenth; rotate
the holdout over all modules. Controls preserve each module's exact number of
`#FAFAFA` pixels but shuffle their 7x7 positions independently, receiving the
same leave-one-module-out fitting freedom.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_PATH = REPO_ROOT / "doc" / "img" / "gsmg_puzzle_stage1.png"
EXPECTED_SHA256 = "38125bbdf1ea58b9b30b075bc6bf71e4089d04bba37098317e47097e2f2a1830"
EYE_BOXES = ((1, 1289, 49, 1337), (183, 1289, 231, 1337), (1, 1471, 49, 1519))
MODULE_PITCH = 7
EYE_MODULE_DELTA = 26
NULL_TRIALS = 500
NULL_SEED = 20260821
EXPECTED_TILE_ROWS = ["0000000","1111111","0110111","0100010","0000000","1111111","0100010"]
EXPECTED_AGGREGATE = {"tp":340,"tn":411,"fp":28,"fn":5}


def sha256_of(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def load_eyes():
    arr = np.array(Image.open(IMAGE_PATH).convert("RGB"))
    return [arr[y0:y1+1, x0:x1+1] for x0, y0, x1, y1 in EYE_BOXES]


def load_mask(): return np.all(load_eyes()[0] == 250, axis=2)


def white_ring_modules():
    out = []
    for my in range(7):
        for mx in range(7):
            outer = my in (0, 6) or mx in (0, 6)
            center = 2 <= my <= 4 and 2 <= mx <= 4
            if not outer and not center:
                out.append((my, mx))
    assert len(out) == 16
    return out


def module_patch(mask, module):
    my, mx = module
    return mask[my*7:(my+1)*7, mx*7:(mx+1)*7]


def metrics(actual, pred):
    a, p = actual.astype(bool), pred.astype(bool)
    tp = int(np.sum(a & p)); tn = int(np.sum(~a & ~p))
    fp = int(np.sum(~a & p)); fn = int(np.sum(a & ~p))
    n = a.size; accuracy = (tp + tn) / n
    tpr = tp/(tp+fn) if tp+fn else 0; tnr = tn/(tn+fp) if tn+fp else 0
    den = math.sqrt((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn))
    return {"n": n, "tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "accuracy": accuracy, "balanced_accuracy": (tpr+tnr)/2,
            "mcc": (tp*tn-fp*fn)/den if den else 0.0}


def fit_tile(mask, modules):
    stack = np.stack([module_patch(mask, m) for m in modules])
    return (stack.sum(axis=0) * 2 > len(modules))


def cross_validate(mask):
    modules = white_ring_modules(); actuals=[]; preds=[]; folds=[]
    for held in modules:
        train = [m for m in modules if m != held]
        tile = fit_tile(mask, train)
        actual = module_patch(mask, held)
        met = metrics(actual, tile)
        folds.append({"held_out_module": held, "fafafa_count": int(actual.sum()),
                      "metrics": met,
                      "residual_subpixels": [[int(y),int(x)] for y,x in zip(*np.where(actual != tile))]})
        actuals.append(actual.ravel()); preds.append(tile.ravel())
    return {"folds": folds,
            "aggregate": metrics(np.concatenate(actuals), np.concatenate(preds))}


def full_fit(mask):
    tile = fit_tile(mask, white_ring_modules())
    actual = np.concatenate([module_patch(mask,m).ravel() for m in white_ring_modules()])
    pred = np.tile(tile.ravel(), len(white_ring_modules()))
    return {"tile_rows": ["".join("1" if v else "0" for v in row) for row in tile],
            "metrics": metrics(actual,pred)}


def shuffled(mask, rng):
    out = mask.copy()
    for m in white_ring_modules():
        patch = module_patch(out,m); flat=patch.ravel().copy(); rng.shuffle(flat); patch[:]=flat.reshape(7,7)
    return out


def calibrate(mask, trials=NULL_TRIALS):
    real = cross_validate(mask); rng=np.random.default_rng(NULL_SEED); rows=[]
    for _ in range(trials): rows.append(cross_validate(shuffled(mask,rng))["aggregate"])
    summary={}
    for key in ("mcc","balanced_accuracy","accuracy"):
        vals=np.array([r[key] for r in rows]); rv=real["aggregate"][key]
        summary[key]={"real":rv,"null_mean":float(vals.mean()),"null_min":float(vals.min()),
                      "null_max":float(vals.max()),
                      "p_ge_real":float((1+np.sum(vals>=rv))/(trials+1))}
    return {"module_pitch":7,"eye_origin_deltas_pixels":{"x":182,"y":182},
            "eye_origin_deltas_modules":{"x":26,"y":26},
            "white_ring_modules":white_ring_modules(),"cross_validation":real,
            "full_fit":full_fit(mask),"null_trials":trials,"null_seed":NULL_SEED,
            "null_summary":summary}


def self_test():
    assert sha256_of(IMAGE_PATH)==EXPECTED_SHA256
    eyes=load_eyes(); assert [e.shape for e in eyes]==[(49,49,3)]*3
    assert all(np.array_equal(eyes[0],e) for e in eyes[1:])
    assert EYE_BOXES[1][0]-EYE_BOXES[0][0]==EYE_MODULE_DELTA*MODULE_PITCH
    assert EYE_BOXES[2][1]-EYE_BOXES[0][1]==EYE_MODULE_DELTA*MODULE_PITCH
    mask=load_mask(); assert int(mask.sum())==345
    assert sum(int(module_patch(mask,m).sum()) for m in white_ring_modules())==345
    planted=np.zeros((49,49),bool); tile=np.array([[((y+2*x)%5)<2 for x in range(7)] for y in range(7)])
    for m in white_ring_modules(): module_patch(planted,m)[:]=tile
    assert cross_validate(planted)["aggregate"]["accuracy"]==1.0
    real=cross_validate(mask); assert real["aggregate"]["n"]==16*49
    for key,value in EXPECTED_AGGREGATE.items(): assert real["aggregate"][key]==value
    assert full_fit(mask)["tile_rows"]==EXPECTED_TILE_ROWS
    print("[*] self-test OK: source and three complete 49x49 eyes pinned; eye spacing is exactly "
          "26x7px modules; all 345 #FAFAFA pixels lie in the 16 logical white-ring modules; "
          "planted shared module tile predicts perfectly; real tile and aggregate confusion pinned.")


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--self-test",action="store_true")
    p.add_argument("--trials",type=int,default=NULL_TRIALS); p.add_argument("--json",action="store_true")
    a=p.parse_args(); self_test()
    if a.self_test:return
    report=calibrate(load_mask(),a.trials)
    if a.json: print(json.dumps(report,indent=2)); return
    print("[*] full tile:","/".join(report["full_fit"]["tile_rows"]))
    print("[*] aggregate:",report["cross_validation"]["aggregate"])
    print("[*] null:",report["null_summary"])


if __name__=="__main__":main()
