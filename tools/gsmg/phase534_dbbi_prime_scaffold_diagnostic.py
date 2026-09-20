#!/usr/bin/env python3
"""Conditional diagnostic: prime-host structure versus checkerboard evidence."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import random

from data import DBBI
from phase525_dbbi_selection_a_reconstruction import enumerate_complete_parses, is_prime

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / 'doc/Brainstorms/2026-09-20 - DBBI Prime Scaffold Conditional Diagnostic.md'
PAIRS = tuple(itertools.combinations('abcdefghi', 2))
REFERENCE_IC = 0.067


def pair_metrics(raw, pair):
    codes = []
    offset = 0
    while offset < len(raw):
        width = 2 if raw[offset] in pair else 1
        if offset + width > len(raw):
            return None
        codes.append(raw[offset:offset + width])
        offset += width
    n = len(codes)
    counts = Counter(codes)
    ic = sum(v * (v - 1) for v in counts.values()) / (n * (n - 1))
    return {'ic': ic, 'distance': abs(ic - REFERENCE_IC),
            'tokens': n, 'types': len(counts)}


def metrics(raw):
    rows = {''.join(p): pair_metrics(raw, p) for p in PAIRS}
    valid = {p: r for p, r in rows.items() if r is not None}
    best = min(r['distance'] for r in valid.values())
    winners = [p for p, r in valid.items() if r['distance'] == best]
    return {'be': rows['be'], 'best_distance': best, 'winners': winners,
            'be_unique_first': winners == ['be']}


def scaffold(tokens):
    host_indices = [i for i in range(len(tokens)) if is_prime(i + 1)]
    free_indices = [i for i in range(len(tokens)) if not is_prime(i + 1)]
    host = ''.join(tokens[i] for i in host_indices)
    residue = ''.join(tokens[i] for i in free_indices)
    return host_indices, free_indices, host, residue


def shuffled_scaffold(tokens, rng):
    host_indices, free_indices, _, residue = scaffold(tokens)
    shuffled = list(residue)
    rng.shuffle(shuffled)
    output = list(tokens)
    for i, symbol in zip(free_indices, shuffled):
        output[i] = symbol
    assert all(output[i] == tokens[i] for i in host_indices)
    raw = ''.join(output)
    assert Counter(raw) == Counter(DBBI) and len(raw) == len(DBBI)
    return raw


def summarize_null(draw, trials, real):
    counts = Counter()
    be_ic_sum = 0.0
    for _ in range(trials):
        value = metrics(draw())
        counts['be_unique_first'] += value['be_unique_first']
        counts['family_distance_at_least_as_close'] += value['best_distance'] <= real['best_distance']
        if value['be'] is not None:
            counts['be_valid'] += 1
            be_ic_sum += value['be']['ic']
            counts['be_distance_at_least_as_close'] += value['be']['distance'] <= real['be']['distance']
    return {'trials': trials, 'counts': dict(counts),
            'be_mean_ic_when_valid': be_ic_sum / counts['be_valid'] if counts['be_valid'] else None,
            'be_unique_first_rate': counts['be_unique_first'] / trials,
            'be_distance_conditional_tail_add_one': (1 + counts['be_distance_at_least_as_close']) / (1 + trials),
            'family_distance_conditional_tail_add_one': (1 + counts['family_distance_at_least_as_close']) / (1 + trials)}


def self_test():
    from checkerboard_code_ic_oracle import segment_codes, code_ic
    parses = enumerate_complete_parses(DBBI)
    assert [len(t) for t in parses] == [83, 84]
    for tokens in parses:
        assert ''.join(tokens) == DBBI
        host_indices, _, host, residue = scaffold(tokens)
        assert len(host_indices) == 23 and host.count('b') == 23
        assert Counter(host) + Counter(residue) == Counter(DBBI)
        rng = random.Random(len(tokens))
        fixture = shuffled_scaffold(tokens, rng)
        assert len(tokens) in [len(p) for p in enumerate_complete_parses(fixture)]
        for raw in (DBBI, fixture):
            for pair in PAIRS:
                old = segment_codes(raw, *pair)
                new = pair_metrics(raw, pair)
                assert (old is None) == (new is None)
                if old is not None:
                    assert new['ic'] == code_ic(old)
                    assert new['tokens'] == len(old)
    # A toy literal scaffold has no cipher construction at all.
    toy = tuple('be' if is_prime(i) else 'a' for i in range(1, 15))
    assert toy in enumerate_complete_parses(''.join(toy))
    assert metrics(DBBI)['winners'] == ['be']
    return {'status': 'passed', 'parse_lengths': [len(t) for t in parses]}


def run(trials):
    real = metrics(DBBI)
    reports = []
    for tokens in enumerate_complete_parses(DBBI):
        n = len(tokens)
        _, _, host, residue = scaffold(tokens)
        rng = random.Random(534000 + n)
        report = {'logical_length': n, 'seed': 534000 + n,
                  'host_counts': dict(sorted(Counter(host).items())),
                  'residue': residue, 'residue_counts': dict(sorted(Counter(residue).items()))}
        report.update(summarize_null(lambda: shuffled_scaffold(tokens, rng), trials, real))
        reports.append(report)
    rng = random.Random(534091)
    def raw_shuffle():
        values = list(DBBI)
        rng.shuffle(values)
        return ''.join(values)
    baseline = summarize_null(raw_shuffle, trials, real)
    baseline['seed'] = 534091
    return {'diagnostic': 'exploratory_conditional_not_discovery_p_value',
            'dbbi_sha256': hashlib.sha256(DBBI.encode()).hexdigest(),
            'protocol_sha256': hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'raw_counts': dict(sorted(Counter(DBBI).items())),
            'real': real, 'scaffold_nulls': reports, 'raw_histogram_null': baseline,
            'self_test': self_test(), 'oracle_calls': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trials', type=int, default=10000)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.trials < 1:
        parser.error('--trials must be positive')
    if args.self_test:
        print(json.dumps(self_test(), indent=2))
    else:
        self_test()
        result = run(args.trials)
        rendered = json.dumps(result, indent=2) + '\n'
        if args.output:
            args.output.write_text(rendered)
        print(rendered)
