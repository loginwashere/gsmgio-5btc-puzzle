#!/usr/bin/env python3
"""Local renderer calibration for the Phase-356 canonical QR module tile.

Renders one ideal 49x49 finder (7 modules x 7px) with a constant #FAFAFA white
ring and black outer/center shapes through Pillow, OpenCV, and Cairo. Cairo is
tested at four subpixel phases and its available antialias modes. Exact 7x7
right-side module patches are compared to the real canonical patch.

This tests the constant-fill vector/rasterizer class, not arbitrary patterned
fills. A browser SVG/canvas lane was attempted but the local synthetic page was
blocked by the browser URL security policy; it is explicitly not counted.
"""

import argparse
import json
import math
from pathlib import Path

import cairo
import cv2
import numpy as np
from PIL import Image, ImageDraw

from qr_fafafa_scale_inversion_audit import canonical_patch

SIZE=49; PATCH_Y=14; PATCH_X=35
OFFSETS=(0.0,0.25,0.5,0.75)

def score(image,label):
    rgb=np.asarray(image,dtype=np.uint8);patch=rgb[PATCH_Y:PATCH_Y+7,PATCH_X:PATCH_X+7,0]
    target,_,_=canonical_patch();errors=int(np.count_nonzero(patch!=target))
    return {"label":label,"byte_errors":errors,"unique_values":sorted(int(v) for v in np.unique(patch)),
            "distinct_row_patterns":len({tuple(int(v) for v in row) for row in patch}),
            "patch_rows":[" ".join(str(int(v)) for v in row) for row in patch]}

def pillow_render():
    im=Image.new("RGB",(49,49),(0,0,0));d=ImageDraw.Draw(im)
    d.rectangle((7,7,41,41),fill=(250,250,250));d.rectangle((14,14,34,34),fill=(0,0,0))
    return np.array(im)

def opencv_render(line_type):
    im=np.zeros((49,49,3),dtype=np.uint8)
    cv2.rectangle(im,(7,7),(41,41),(250,250,250),thickness=-1,lineType=line_type)
    cv2.rectangle(im,(14,14),(34,34),(0,0,0),thickness=-1,lineType=line_type)
    return im

def cairo_render(offset,antialias):
    surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,49,49);ctx=cairo.Context(surface)
    ctx.set_antialias(antialias);ctx.set_source_rgb(0,0,0);ctx.paint()
    ctx.set_source_rgb(250/255,250/255,250/255);ctx.rectangle(7+offset,7+offset,35,35);ctx.fill()
    ctx.set_source_rgb(0,0,0);ctx.rectangle(14+offset,14+offset,21,21);ctx.fill();surface.flush()
    raw=np.frombuffer(surface.get_data(),dtype=np.uint8).reshape(49,surface.get_stride()//4,4)[:,:49]
    # Cairo ARGB32 is native-endian BGRA on this little-endian host; opaque output.
    return raw[:,:,[2,1,0]]

def run():
    reports=[score(pillow_render(),"pillow_integer"),score(opencv_render(cv2.LINE_8),"opencv_line8"),
             score(opencv_render(cv2.LINE_AA),"opencv_lineAA")]
    modes=(("default",cairo.ANTIALIAS_DEFAULT),("none",cairo.ANTIALIAS_NONE),
           ("gray",cairo.ANTIALIAS_GRAY),("subpixel",cairo.ANTIALIAS_SUBPIXEL))
    for name,mode in modes:
        for off in OFFSETS:reports.append(score(cairo_render(off,mode),f"cairo_{name}_offset_{off}"))
    return {"renderers":{"pillow":Image.__version__ if hasattr(Image,"__version__") else "10.2.0",
                         "opencv":cv2.__version__,"cairo":cairo.cairo_version_string()},
            "variants":len(reports),"exact_matches":sum(r["byte_errors"]==0 for r in reports),
            "best":min(reports,key=lambda r:(r["byte_errors"],r["label"])),"reports":reports,
            "browser_lane":"not tested: local synthetic data URL blocked by browser URL security policy"}

def self_test():
    target,mods,_=canonical_patch();assert target.shape==(7,7) and mods==[(1,5),(2,5),(3,5),(4,5)]
    planted=np.zeros((49,49,3),dtype=np.uint8);planted[PATCH_Y:PATCH_Y+7,PATCH_X:PATCH_X+7]=target[:,:,None]
    assert score(planted,"planted")["byte_errors"]==0
    report=run();assert report["variants"]==19
    assert report["exact_matches"]==0
    assert len({tuple(row) for row in target})==4
    assert all(r["distinct_row_patterns"]<4 for r in report["reports"])
    print("[*] self-test OK: canonical patch pinned; planted exact match detected; 19 Pillow/OpenCV/Cairo "
          "variants reproduce zero exact tiles and none reaches the target's four distinct row patterns.")

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--json",action="store_true")
    a=p.parse_args();self_test()
    if a.self_test:return
    report=run();print(json.dumps(report,indent=2) if a.json else
                       f"[*] variants={report['variants']} exact={report['exact_matches']} best={report['best']}")

if __name__=="__main__":main()
