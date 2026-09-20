#!/usr/bin/env python3
"""Reproduce the review's fixed-grammar rarity check; no historical correction."""
import hashlib
import json
import math
from pathlib import Path
import random
from functools import lru_cache
from data import DBBI


def has_parse(raw):
    primes = {n for n in range(2, len(raw) + 1)
              if all(n % d for d in range(2, math.isqrt(n) + 1))}

    @lru_cache(None)
    def visit(offset, position):
        if offset == len(raw):
            return True
        if position in primes:
            return any(raw.startswith(t, offset) and visit(offset + len(t), position + 1)
                       for t in ('b', 'be'))
        return visit(offset + 1, position + 1)
    return visit(0, 1)


def run(trials=300000, seed=20260920):
    assert has_parse(DBBI) and has_parse('ab') and not has_parse('aa')
    rng = random.Random(seed)
    letters = list(DBBI)
    hits = 0
    for _ in range(trials):
        rng.shuffle(letters)
        hits += has_parse(''.join(letters))
    return {'trials': trials, 'seed': seed, 'hits': hits,
            'zero_hit_95pct_upper_bound': -math.expm1(math.log(.05) / trials) if hits == 0 else None,
            'scope': 'fixed observed grammar, fixed histogram; discovery search not corrected',
            'review_seed_replay_not_new_independent_replication': True,
            'dbbi_sha256': hashlib.sha256(DBBI.encode()).hexdigest(),
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    result = run()
    Path(__file__).with_name('phase534_scaffold_rarity_result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
