#!/usr/bin/env python3
"""Phase 541 (pilot round 2): lock, sandboxed execution of agent proposals, validators.

Modes
  --self-test      harness controls (static check, sandbox, key-shape exactness, data
                   integrity, end-to-end plumbing). Reads no agent output.
  --lock           runs the controls and hashes protocol, prompts, dossier, data and code.
  --collect        verifies the lock, runs every proposal exactly as written (never repaired),
                   scans outputs for key shapes against the eleven target hash160s, writes the
                   GPU base list and a counts-only summary.
  --verify-oracle  summarizes the GPU output with the Phase 524 helpers.

No key material is ever printed; key-shaped hits go to a mode-0600 file under _work.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

ROOT = SCRIPT_DIR.parents[1]
WORK = ROOT / "_work" / "phase541_round2"
LOCK = SCRIPT_DIR / "phase541_round2_lock.json"
PROTOCOL = ROOT / "doc/Brainstorms/2026-09-20 - Phase 541 Fresh-Context Agent Round 2 Protocol.md"
AGENTS = ("B1", "B2", "B3", "B4", "B5", "B6")
ALLOWED_IMPORTS = {"math", "itertools", "string", "re", "collections", "hashlib", "base64",
                   "binascii", "functools", "struct", "operator", "textwrap"}
BANNED_NAMES = {"open", "eval", "exec", "compile", "__import__", "input", "globals", "locals", "vars",
                "breakpoint", "getattr", "setattr", "delattr", "type", "object", "memoryview", "help", "exit", "quit"}
SAFE_BUILTINS = ["abs", "all", "any", "bin", "bool", "bytes", "bytearray", "chr", "dict", "divmod",
                 "enumerate", "filter", "float", "format", "frozenset", "hasattr", "hex", "int", "isinstance",
                 "iter", "len", "list", "map", "max", "min", "next", "oct", "ord", "pow", "range", "repr",
                 "reversed", "round", "set", "slice", "sorted", "str", "sum", "tuple", "zip",
                 "Exception", "ValueError", "TypeError", "IndexError", "KeyError", "ZeroDivisionError",
                 "StopIteration", "ArithmeticError", "OverflowError", "True", "False", "None"]
RUN_TIMEOUT = 30
MAX_RETURN = 3000
MAX_TRIED_PER_PROPOSAL = 1000
MAX_TRIED_PER_AGENT = 6000
MAX_LEN = 200

WRAPPER = r"""
import json, sys, resource, builtins
resource.setrlimit(resource.RLIMIT_CPU, (25, 25))
resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 ** 3, 2 * 1024 ** 3))
resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
code = open(sys.argv[1]).read()
data = json.load(open(sys.argv[2]))
ALLOWED = set(json.loads(sys.argv[3]))
SAFE = json.loads(sys.argv[4])
real_import = builtins.__import__
def guarded(name, *a, **k):
    if name.split('.')[0] not in ALLOWED:
        raise ImportError(name)
    return real_import(name, *a, **k)
safe = {k: getattr(builtins, k) for k in SAFE if hasattr(builtins, k)}
safe['__import__'] = guarded
ns = {'__builtins__': safe}
exec(compile(code, 'proposal', 'exec'), ns)
out = ns['run'](data)
if not isinstance(out, list) or not all(isinstance(x, str) for x in out):
    raise TypeError('run() must return a list of strings')
sys.stdout.write('\n@@RESULT@@' + json.dumps(out[:%d]) + '\n@@COUNT@@' + str(len(out)))
""" % MAX_RETURN


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def static_check(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"syntax: {e.msg}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    return False, f"import {a.name}"
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS or node.level:
                return False, f"import from {node.module}"
        elif isinstance(node, ast.Name) and (node.id in BANNED_NAMES or node.id.startswith("__")):
            return False, f"name {node.id}"
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return False, f"attribute {node.attr}"
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and "__" in node.value:
            return False, "string containing __"
    if not any(isinstance(n, ast.FunctionDef) and n.name == "run" for n in tree.body):
        return False, "no top-level run()"
    return True, ""


def run_sandboxed(code, data_path):
    with tempfile.TemporaryDirectory() as tmp:
        cpath = Path(tmp) / "proposal.py"
        cpath.write_text(code, encoding="utf-8")
        try:
            p = subprocess.run(
                [sys.executable, "-I", "-c", WRAPPER, str(cpath), str(data_path),
                 json.dumps(sorted(ALLOWED_IMPORTS)), json.dumps(SAFE_BUILTINS)],
                capture_output=True, text=True, timeout=RUN_TIMEOUT, cwd=tmp, env={}, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
    if p.returncode != 0:
        last = (p.stderr.strip().splitlines() or ["nonzero exit"])[-1]
        return {"ok": False, "error": last[:200]}
    text = p.stdout
    if "@@RESULT@@" not in text:
        return {"ok": False, "error": "no result"}
    body = text.split("@@RESULT@@", 1)[1]
    res, count = body.split("\n@@COUNT@@", 1)
    return {"ok": True, "outputs": json.loads(res), "returned": int(count.strip())}


# --------------------------------------------------------------------------
# key-shape check against the exact targets
# --------------------------------------------------------------------------
def load_targets():
    from phase539_base9_scalar_all_bijections import derive_targets
    return derive_targets()[0]


def keyshape_scan(strings, targets, bloom=None):
    """Exact hits against `targets` ({hash160 bytes: label}); Bloom hits are context only."""
    from binary_key_material_backfill import private_key_details
    from key_shape_classifier import classify_body
    exact, bloom_hits, shaped = [], 0, 0
    seen = set()
    for s in strings:
        for label, key in classify_body(s.encode("utf-8", errors="ignore")):
            if key in seen:
                continue
            seen.add(key)
            shaped += 1
            det = private_key_details(key)
            if not det:
                continue
            for enc, item in det.items():
                h = bytes.fromhex(item["hash160"])
                if h in targets:
                    exact.append({"label": label, "encoding": enc, "target": targets[h], "key_hex": key.hex()})
                elif bloom is not None and label not in ("raw_half", "raw_better_half") and bloom.contains(h):
                    bloom_hits += 1
    return {"key_shaped": shaped, "exact": exact, "bloom_context": bloom_hits}


# --------------------------------------------------------------------------
# reading agent output
# --------------------------------------------------------------------------
def read_jsonl(path):
    rows, bad = [], 0
    if not Path(path).exists():
        return None, 0
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            bad += 1
    return rows, bad


def collect(out_dir=None, data_path=None, targets=None, bloom=None, round1_path=None, exact_path=None):
    out_dir = Path(out_dir or WORK / "out")
    data_path = Path(data_path or WORK / "data.json")
    targets = targets if targets is not None else load_targets()
    r1 = set()
    rp = Path(round1_path or SCRIPT_DIR / "phase540_pilot_outputs" / "candidates_main.txt")
    if rp.exists():
        r1 = {norm(l) for l in rp.read_text().splitlines() if l.strip()}
    per, tried, seen = {}, [], set()
    all_exact, total_shaped, total_bloom = [], 0, 0
    summary_ops = []
    for name in AGENTS:
        ops, bad_ops = read_jsonl(out_dir / f"{name}.ops.jsonl")
        cands, bad_c = read_jsonl(out_dir / f"{name}.cands.jsonl")
        st = {"ops_lines": None if ops is None else len(ops), "ops_bad_json": bad_ops,
              "static_rejected": 0, "run_ok": 0, "run_failed": 0, "outputs_returned": 0,
              "tried_from_ops": 0, "cands_lines": None if cands is None else len(cands), "cands_tried": 0}
        agent_tried = 0
        for op in ops or []:
            code = str(op.get("code", ""))
            ok, why = static_check(code)
            rec = {"agent": name, "name": str(op.get("name", ""))[:80], "inputs": op.get("inputs"), "check": op.get("check"),
                   "retro": op.get("retro"), "static_ok": ok, "static_reason": why}
            if not ok:
                st["static_rejected"] += 1
                summary_ops.append(rec)
                continue
            res = run_sandboxed(code, data_path)
            rec.update({"run_ok": res["ok"], "error": res.get("error"), "returned": res.get("returned")})
            if not res["ok"]:
                st["run_failed"] += 1
                summary_ops.append(rec)
                continue
            st["run_ok"] += 1
            outs = list(dict.fromkeys(res["outputs"]))
            st["outputs_returned"] += res["returned"]
            ks = keyshape_scan(outs, targets, bloom)
            total_shaped += ks["key_shaped"]
            total_bloom += ks["bloom_context"]
            all_exact += [dict(e, agent=name, op=rec["name"]) for e in ks["exact"]]
            rec.update({"unique_outputs": len(outs), "key_shaped": ks["key_shaped"]})
            kept = [o for o in outs[:MAX_TRIED_PER_PROPOSAL] if o and len(o) <= MAX_LEN]
            for o in kept:
                if agent_tried >= MAX_TRIED_PER_AGENT:
                    break
                agent_tried += 1
                st["tried_from_ops"] += 1
                if o not in seen:
                    seen.add(o)
                    tried.append(o)
            summary_ops.append(rec)
        for c in cands or []:
            cand = str(c.get("candidate", "")).replace("\r", " ").replace("\n", " ").strip()
            if cand and len(cand) <= MAX_LEN:
                st["cands_tried"] += 1
                if cand not in seen:
                    seen.add(cand)
                    tried.append(cand)
                ks = keyshape_scan([cand], targets, bloom)
                total_shaped += ks["key_shaped"]
                all_exact += [dict(e, agent=name, op="candidate") for e in ks["exact"]]
        per[name] = st
    WORK.mkdir(parents=True, exist_ok=True)
    if out_dir == WORK / "out":
        (WORK / "bases.txt").write_text("\n".join(tried) + "\n", encoding="utf-8")
    new_vs_r1 = sum(1 for t in tried if norm(t) and norm(t) not in r1)
    summary = {"per_agent": per, "unique_bases": len(tried), "bases_not_in_round1": new_vs_r1,
               "bases_sha256": hashlib.sha256(("\n".join(tried) + "\n").encode()).hexdigest(),
               "key_shaped_strings": total_shaped, "bloom_context_hits": total_bloom, "exact_keyshape_hits": len(all_exact)}
    if all_exact:
        fd = os.open(exact_path or WORK / "keyshape_exact.jsonl", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            for e in all_exact:
                fh.write(json.dumps(e) + "\n")
    return summary, summary_ops


# --------------------------------------------------------------------------
# controls
# --------------------------------------------------------------------------
GOOD = "def run(data):\n    return [data['DBBI'][:5], 'x' * 3]\n"


def control_static():
    bad = ["import os\ndef run(d):\n    return []", "def run(d):\n    return [open('x').read()]",
           "def run(d):\n    return [eval('1')]", "def run(d):\n    return [d.__class__]",
           "from subprocess import run\ndef run(d):\n    return []", "def run(d):\n    return ['__x__']",
           "def run(d):\n    return [getattr(d, 'keys')]", "x = 1"]
    return static_check(GOOD)[0] and not any(static_check(b)[0] for b in bad)


def control_sandbox(data_path):
    r = run_sandboxed(GOOD, data_path)
    ok = r["ok"] and r["outputs"][1] == "xxx" and len(r["outputs"][0]) == 5
    loop = run_sandboxed("def run(d):\n    while True:\n        pass\n", data_path)
    boom = run_sandboxed("def run(d):\n    return [1 // 0]\n", data_path)
    nolist = run_sandboxed("def run(d):\n    return 'abc'\n", data_path)
    big = run_sandboxed("def run(d):\n    return [str(i) for i in range(5000)]\n", data_path)
    imp = run_sandboxed("def run(d):\n    import os\n    return []\n", data_path)
    return bool(ok and not loop["ok"] and not boom["ok"] and not nolist["ok"]
                and big["ok"] and len(big["outputs"]) == MAX_RETURN and big["returned"] == 5000 and not imp["ok"])


def control_keyshape():
    import coincurve
    from phase539_base9_scalar_all_bijections import hash160
    from binary_key_material_backfill import base58check
    k = hashlib.sha256(b"phase541 planted control key").digest()
    pk = coincurve.PublicKey.from_secret(k)
    tgt = {hash160(pk.format(compressed=True)): "planted"}
    wif = base58check(b"\x80" + k + b"\x01")
    hit_hex = keyshape_scan([k.hex()], tgt)["exact"]
    hit_wif = keyshape_scan([wif], tgt)["exact"]
    other = keyshape_scan([hashlib.sha256(b"other").hexdigest()], tgt)["exact"]
    real = keyshape_scan([k.hex()], load_targets())["exact"]
    return bool(len(hit_hex) == 1 and len(hit_wif) == 1 and not other and not real)


def control_data():
    d = json.loads((WORK / "data.json").read_text())
    from phase539_base9_scalar_all_bijections import target_strings
    ts = target_strings()
    ok = d["P83"] == ts["P83"] and d["P84"] == ts["P84"] and len(d["ANSWER_322"]) == 91
    from phase538_faed_lane_extraction import PHASE48_MASK
    ok &= d["MASK31"] == PHASE48_MASK and d["MASK30"] == PHASE48_MASK[:-1]
    ok &= d["BTCSEED_DECODE"].startswith("BTCSEED") and len(d["BTCSEED_DECODE"]) == 570
    ok &= len(d["EVENTS"]) == 25 and d["MATRIX_SELECTION_A"]["output"] == "IZLKESKGGIPPEN"
    sel = "".join(d["ANSWER_322"][p - 1] for p in d["MASK31"]).lower()
    ok &= sel == "ncsyangcahiriasogaleafayanestve"
    return bool(ok)


def control_plumbing():
    import coincurve
    from phase539_base9_scalar_all_bijections import hash160
    k = hashlib.sha256(b"phase541 plumbing key").digest()
    pk = coincurve.PublicKey.from_secret(k)
    tgt = {hash160(pk.format(compressed=False)): "planted"}
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        good = f"def run(d):\n    return ['{k.hex()}', 'plain phrase', 'a b c']\n"
        rows = [{"name": "good", "code": good}, {"name": "imp", "code": "import os\ndef run(d):\n    return []"},
                {"name": "loop", "code": "def run(d):\n    while True:\n        pass\n"}]
        (out / "B1.ops.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        (out / "B1.cands.jsonl").write_text(json.dumps({"candidate": "a b c"}) + "\n")
        summary, ops = collect(out_dir=out, data_path=WORK / "data.json", targets=tgt, round1_path=out / "none",
                               exact_path=out / "exact.jsonl")
    b1 = summary["per_agent"]["B1"]
    return bool(b1["ops_lines"] == 3 and b1["static_rejected"] == 1 and b1["run_ok"] == 1 and b1["run_failed"] == 1
                and summary["exact_keyshape_hits"] == 1 and summary["unique_bases"] == 3)


def self_test():
    dp = WORK / "data.json"
    checks = {"static_check": control_static(), "sandbox": control_sandbox(dp), "keyshape_exactness": control_keyshape(),
              "data_integrity": control_data(), "plumbing": control_plumbing()}
    return {"ok": all(checks.values()), "checks": checks}


# --------------------------------------------------------------------------
# lock
# --------------------------------------------------------------------------
def lock_files():
    return {
        "protocol": PROTOCOL, "prompts": SCRIPT_DIR / "phase541_round2_prompts.json",
        "build_script": SCRIPT_DIR / "phase541_round2_build.py", "exec_script": Path(__file__),
        "test_script": SCRIPT_DIR / "test_phase541_round2_exec.py",
        "dossier_v2": WORK / "dossier_v2.md", "data_json": WORK / "data.json",
        "phase525_result": SCRIPT_DIR / "phase525_selection_a_result.json",
        "phase535_result": SCRIPT_DIR / "phase535_selection_a_matrix_result.json",
        "key_shape_classifier": SCRIPT_DIR / "key_shape_classifier.py",
        "binary_key_material_backfill": SCRIPT_DIR / "binary_key_material_backfill.py",
        "phase539_script": SCRIPT_DIR / "phase539_base9_scalar_all_bijections.py",
        "phase540_prompts": SCRIPT_DIR / "phase540_pilot_prompts.json",
        "round1_candidates": SCRIPT_DIR / "phase540_pilot_outputs" / "candidates_main.txt",
    }


def lock_hashes():
    return {k: sha(v) for k, v in lock_files().items()}


def do_lock():
    if LOCK.exists():
        raise SystemExit("lock exists; refusing to overwrite")
    st = self_test()
    if not st["ok"]:
        print(json.dumps(st, indent=2))
        raise SystemExit("controls failed; no lock written")
    LOCK.write_text(json.dumps({"phase": 541, "sha256": lock_hashes(), "controls": st["checks"]}, indent=2, sort_keys=True) + "\n")
    return json.loads(LOCK.read_text())


def verify_lock():
    lock = json.loads(LOCK.read_text())
    now = lock_hashes()
    bad = [k for k in now if lock["sha256"].get(k) != now[k]]
    if bad:
        raise SystemExit(f"lock mismatch: {bad}")
    return lock


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for f in ("--self-test", "--lock", "--collect", "--verify-oracle"):
        ap.add_argument(f, action="store_true")
    ap.add_argument("--hits", default=str(ROOT / "tools/gpu_oracle/output_local/phase541.hits.jsonl"))
    ap.add_argument("--keyshape", default=str(ROOT / "tools/gpu_oracle/output_local/phase541.keyshape.jsonl"))
    ap.add_argument("--checkpoint", default=str(ROOT / "tools/gpu_oracle/output_local/phase541.checkpoint.jsonl"))
    a = ap.parse_args()
    if a.self_test:
        r = self_test()
        print(json.dumps(r, indent=2))
        return 0 if r["ok"] else 1
    if a.lock:
        print(json.dumps(do_lock(), indent=2))
    elif a.collect:
        verify_lock()
        from binary_key_material_backfill import BloomCache
        bloom = BloomCache(ROOT / "db/addresses.hash160.bloom")
        summary, ops = collect(bloom=bloom)
        (WORK / "ops_summary.json").write_text(json.dumps(ops, indent=2))
        print(json.dumps(summary, indent=2))
        if summary["exact_keyshape_hits"]:
            print(f"EXACT key-shape HIT written to {WORK / 'keyshape_exact.jsonl'} (0600). Tell the user; do not commit.")
            return 2
    elif a.verify_oracle:
        import phase524_slot_grammar_sweep_prep as p524
        n = len([l for l in (WORK / "bases.txt").read_text().splitlines() if l.strip()])
        print(json.dumps(p524.verify(a.hits, a.keyshape, a.checkpoint, n), indent=2))
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
