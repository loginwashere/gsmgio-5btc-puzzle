#!/usr/bin/env python3
"""Repository-wide exact fingerprint search for the Phase-356/357 7x7 tile.

Scans every repository raster (excluding .git and build targets) for:
  1. byte-exact RGB copies of the canonical 250/255 7x7 module patch; and
  2. color-remapped copies having the identical two-class geometry, under all
     eight dihedral symmetries, where every target-0 site is one constant RGB
     color and every target-1 site is a different constant RGB color.

The second test is exact, not perceptual. It can find a palette-changed source
asset without accepting approximate shapes. Uniform windows cannot match
because the two class colors must differ.
"""

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from qr_fafafa_scale_inversion_audit import canonical_patch

REPO_ROOT=Path(__file__).resolve().parents[2]
IMAGE_PATH=REPO_ROOT/"doc"/"img"/"gsmg_puzzle_stage1.png"
EXPECTED_SHA256="38125bbdf1ea58b9b30b075bc6bf71e4089d04bba37098317e47097e2f2a1830"
RASTER_SUFFIXES={".png",".jpg",".jpeg",".bmp",".webp",".gif",".tif",".tiff"}
SKIP_PARTS={".git","target","__pycache__"}

def sha256_of(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def raster_paths():
    return sorted(p for p in REPO_ROOT.rglob("*") if p.is_file() and p.suffix.lower() in RASTER_SUFFIXES
                  and not any(part in SKIP_PARTS for part in p.relative_to(REPO_ROOT).parts))

def transforms(mask):
    out=[]
    for k in range(4):
        r=np.rot90(mask,k);out.append((f"rot{k*90}",r));out.append((f"rot{k*90}_hflip",np.fliplr(r)))
    unique=[];seen=set()
    for name,m in out:
        key=m.tobytes()
        if key not in seen:seen.add(key);unique.append((name,m))
    return unique

def constant_class_candidates(channel,class_mask):
    src=channel.astype(np.float32);kernel=class_mask.astype(np.float32);n=int(class_mask.sum())
    sums=cv2.matchTemplate(src,kernel,cv2.TM_CCORR)
    sumsqs=cv2.matchTemplate(src*src,kernel,cv2.TM_CCORR)
    # Float32 is only a candidate filter; every survivor is rechecked exactly.
    return np.abs(n*sumsqs-sums*sums)<32.0,sums/n

def scan_array(rgb,target,geometry=True):
    h,w=rgb.shape[:2]
    if h<7 or w<7:return []
    matches=[]
    exact_target=np.repeat(target[:,:,None],3,axis=2).astype(np.uint8)
    exact_score=cv2.matchTemplate(rgb,exact_target,cv2.TM_SQDIFF)
    for y,x in zip(*np.where(exact_score<128.0)):
        if not np.array_equal(rgb[y:y+7,x:x+7],exact_target):continue
        matches.append({"kind":"byte_exact","x":int(x),"y":int(y),"transform":"identity",
                        "color_0":[255,255,255],"color_1":[250,250,250]})
    if not geometry:
        return matches
    binary=(target==250)
    for name,m1 in transforms(binary):
        m0=~m1;valid=np.ones((h-6,w-6),dtype=bool);different=np.zeros_like(valid)
        for c in range(3):
            v0,mean0=constant_class_candidates(rgb[:,:,c],m0);v1,mean1=constant_class_candidates(rgb[:,:,c],m1)
            valid &= v0&v1;different |= np.abs(mean0-mean1)>0.25
        valid &= different
        for y,x in zip(*np.where(valid)):
            window=rgb[y:y+7,x:x+7];vals0=window[m0];vals1=window[m1]
            if not (np.all(vals0==vals0[0]) and np.all(vals1==vals1[0])):continue
            c0=[int(v) for v in vals0[0]];c1=[int(v) for v in vals1[0]]
            if c0==c1:continue
            matches.append({"kind":"geometry_exact","x":int(x),"y":int(y),"transform":name,
                            "color_0":c0,"color_1":c1})
    # Remove byte-exact duplicates from the broader geometry class and symmetry duplicates.
    dedup={}
    for m in matches:
        key=(m["x"],m["y"],m["color_0"][0],tuple(m["color_0"]),tuple(m["color_1"]))
        prior=dedup.get(key)
        if prior is None or m["kind"]=="byte_exact":dedup[key]=m
    return sorted(dedup.values(),key=lambda m:(m["y"],m["x"],m["kind"],m["transform"]))

def run():
    target,canonical_modules,_=canonical_patch();rows=[];errors=[]
    paths=raster_paths();geometry_scanned=0
    for p in paths:
        try:
            im=Image.open(p).convert("RGB");rgb=np.array(im)
        except Exception as e:errors.append({"file":str(p.relative_to(REPO_ROOT)),"error":repr(e)});continue
        # Palette-remapped exact geometry is meaningful only where an exact
        # two-color primitive can survive: lossless, flat graphics. Byte-exact
        # matching still runs over every raster, including JPEG/screenshots.
        flat_lossless=p.suffix.lower() in {".png",".bmp",".gif",".tif",".tiff"} and im.getcolors(maxcolors=257) is not None
        geometry_scanned+=int(flat_lossless)
        hits=scan_array(rgb,target,geometry=flat_lossless)
        if hits:rows.append({"file":str(p.relative_to(REPO_ROOT)),"width":rgb.shape[1],"height":rgb.shape[0],
                             "hits":hits,"hit_count":len(hits)})
    return {"source_sha256":sha256_of(IMAGE_PATH),"canonical_modules":canonical_modules,
            "raster_files_scanned":len(paths),"files_with_hits":len(rows),
            "flat_lossless_geometry_files_scanned":geometry_scanned,
            "total_hits":sum(r["hit_count"] for r in rows),"results":rows,"read_errors":errors}

def self_test():
    assert sha256_of(IMAGE_PATH)==EXPECTED_SHA256
    target,mods,_=canonical_patch();assert mods==[(1,5),(2,5),(3,5),(4,5)]
    rgb=np.zeros((12,13,3),dtype=np.uint8);rgb[:]=[12,34,56]
    mask=target==250
    patch=np.empty((7,7,3),dtype=np.uint8);patch[~mask]=[10,20,30];patch[mask]=[200,150,100]
    rgb[3:10,4:11]=patch
    hits=scan_array(rgb,target)
    assert any(h["x"]==4 and h["y"]==3 and h["color_0"]==[10,20,30] and
               h["color_1"]==[200,150,100] for h in hits),hits
    blank=np.full((10,10,3),99,dtype=np.uint8);assert not scan_array(blank,target)
    source=np.array(Image.open(IMAGE_PATH).convert("RGB"));source_hits=scan_array(source,target,geometry=True)
    assert len(source_hits)==12 and all(h["kind"]=="byte_exact" for h in source_hits),source_hits
    print("[*] self-test OK: source/canonical tile pinned; planted palette-remapped geometry found "
          "at the exact coordinate; uniform-image negative produces zero hits; source has exactly "
          "the 12 expected byte-exact module copies and no extra/remapped hit.")

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--self-test",action="store_true");p.add_argument("--json",action="store_true")
    a=p.parse_args();self_test()
    if a.self_test:return
    report=run()
    if a.json:print(json.dumps(report,indent=2));return
    print(f"[*] scanned={report['raster_files_scanned']} files_with_hits={report['files_with_hits']} total_hits={report['total_hits']}")
    for row in report["results"]:print(f"  {row['file']}: {row['hit_count']}")

if __name__=="__main__":main()
