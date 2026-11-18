#!/usr/bin/env python3
"""Locked FAED marginal-distribution boundary pilot; see Phase 548 protocol."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from data import FAED

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROTOCOL = ROOT / 'doc/Brainstorms/2026-09-29 - Phase 548 FAED Distribution Boundary Protocol.md'
LOCK = HERE / 'phase548_boundary_lock.json'
RESULT = HERE / 'phase548_boundary_result.json'
N = 570
EFFECTS = (.05, .10, .15, .20)
REAL_NULLS = 1999


def partitions():
    factors = [d for d in range(2, N) if N % d == 0]
    cuts = sorted({d for d in factors if 30 <= d <= N-30} |
                  {N-d for d in factors if 30 <= N-d <= N-30} | {91, 479})
    candidates = [(f'cut_{c}', (np.arange(N) >= c).astype(int)) for c in cuts]
    for rows in factors:
        cols = N // rows
        candidates += [(f'layout_{rows}x{cols}_rows', np.arange(N)//cols),
                       (f'layout_{rows}x{cols}_columns', np.arange(N)%cols)]
    seen, out = set(), []
    for name, groups in candidates:
        key = tuple(groups.tolist())
        if key not in seen:
            seen.add(key)
            out.append((name, groups, np.bincount(groups)))
    return out


PARTS = partitions()


def score(s):
    totals = np.bincount(s, minlength=9)
    present = totals > 0
    out = []
    for _, groups, sizes in PARTS:
        table = np.bincount(groups*9+s, minlength=len(sizes)*9).reshape(-1, 9)[:, present]
        expected = sizes[:, None] * totals[present][None, :] / N
        x2 = float(((table-expected)**2/expected).sum())
        df = (len(sizes)-1)*(int(present.sum())-1)
        out.append((x2-df)/np.sqrt(2*df))
    return np.array(out)


def nulls(s, count, rng):
    return [float(score(rng.permutation(s)).max()) for _ in range(count)]


def pvalue(value, distribution):
    return (1 + sum(x >= value for x in distribution)) / (1 + len(distribution))


def machinery():
    rng = np.random.default_rng(54800)
    s = rng.integers(0, 9, N)
    actual = score(s)
    direct = []
    for _, groups, sizes in PARTS:
        table = np.array([[sum(int(s[i]) == a for i in range(N) if groups[i] == g)
                           for a in range(9)] for g in range(len(sizes))])
        expected = sizes[:, None]*np.bincount(s, minlength=9)[None, :]/N
        df = (len(sizes)-1)*8
        direct.append((float(((table-expected)**2/expected).sum())-df)/np.sqrt(2*df))
    assert np.allclose(actual, direct, rtol=0, atol=1e-10)
    assert np.allclose(actual, score(rng.permutation(9)[s]), rtol=0, atol=1e-10)
    return {'direct_equals_optimized': True, 'symbol_relabeling_invariant': True}


def controls():
    checks = machinery()
    rng = np.random.default_rng(54802)
    power = []
    for effect in EFFECTS:
        a = np.full(9, 1/9)
        a[0] += effect/2
        a[8] -= effect/2
        b = a[::-1]
        trials = []
        for _ in range(10):
            s = np.concatenate([rng.choice(9, N//2, p=a), rng.choice(9, N//2, p=b)])
            value = float(score(s).max())
            p = pvalue(value, nulls(s, 199, rng))
            trials.append(p)
        entry = {'total_variation': effect, 'p_values': trials,
                 'detections': sum(p <= .01 for p in trials)}
        power.append(entry)
        print('CONTROL', json.dumps(entry), flush=True)
    checks['power'] = power
    checks['passed'] = power[-1]['detections'] >= 9
    checks['smallest_tested_effect_at_9_of_10'] = next(
        (r['total_variation'] for r in power if r['detections'] >= 9), None)
    return checks


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fields():
    return {'protocol_sha256': digest(PROTOCOL), 'script_sha256': digest(Path(__file__)),
            'data_sha256': digest(HERE/'data.py'), 'real_nulls': REAL_NULLS,
            'real_seed': 54801, 'bar': .01,
            'partitions': [name for name, _, _ in PARTS]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'run'])
    args = parser.parse_args()
    if args.mode == 'prepare':
        assert not LOCK.exists(), 'lock exists; do not silently overwrite'
        checks = controls()
        if not checks['passed']:
            raise SystemExit('insufficient planted recovery; no lock, no real scoring')
        lock = {'fields': fields(), 'controls': checks}
        LOCK.write_text(json.dumps(lock, indent=2)+'\n')
        print('LOCK', LOCK, flush=True)
        return
    assert not RESULT.exists(), 'real result exists; do not silently rerun'
    lock = json.loads(LOCK.read_text())
    assert lock['fields'] == fields() and lock['controls']['passed']
    s = np.array([ord(c)-ord('a') for c in FAED])
    assert len(s) == N and set(s) == set(range(9))
    scores = score(s)
    distribution = nulls(s, REAL_NULLS, np.random.default_rng(54801))
    best = int(scores.argmax())
    p = pvalue(float(scores[best]), distribution)
    result = {'lock_sha256': digest(LOCK), 'faed_sha256': hashlib.sha256(FAED.encode()).hexdigest(),
              'scores': dict(zip([x[0] for x in PARTS], scores.tolist())),
              'best_partition': PARTS[best][0], 'family_p': p,
              'null_maxima': distribution,
              'outcome': 'structural_checkpoint' if p <= .01 else 'bounded_negative'}
    RESULT.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['scores', 'null_maxima']}))


if __name__ == '__main__':
    main()
