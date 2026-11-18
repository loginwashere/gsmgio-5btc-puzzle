#!/usr/bin/env python3
"""Exploratory replay of the October 7 Telegram mirror and index recipes."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random

import numpy as np

from data import DBBI, FAED, VALIDATION_ANSWER
from phase386_btcseed_bifid_faed_decode_audit import build_grid, bifid_decrypt
from phase525_dbbi_selection_a_reconstruction import enumerate_complete_parses, is_prime

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / 'doc/Brainstorms/2026-10-07 - Telegram DBBI Mirror Replay Protocol.md'
OUTPUT = ROOT / '_work/telegram_2026_10_07/structural_replay.json'
TRIALS = 9999
CENTERS = (2, 3, 4)
INDICES = (51, 49, 43, 45, 32, 50, 36, 12, 44, 14, 40, 34, 41, 43, 20, 30, 56, 52)


def matrix(raw):
    assert len(raw) == 91
    return np.array(list(raw)).reshape(7, 13)


def counts(raw):
    m = matrix(raw)
    return [int(sum(np.count_nonzero(m[c-d] == m[c+d]) for d in (1, 2)))
            for c in CENTERS]


def explicit_counts(raw):
    return [sum(raw[(c-d)*13+j] == raw[(c+d)*13+j]
                for d in (1, 2) for j in range(13)) for c in CENTERS]


def pair_stat(values):
    return sum(sorted(values)[-2:])


def controls(draw, seed, observed):
    rng = random.Random(seed)
    samples = []
    witnesses = []
    for _ in range(TRIALS):
        raw = draw(rng)
        assert Counter(raw) == Counter(DBBI)
        values = counts(raw)
        assert values == explicit_counts(raw)
        score = pair_stat(values)
        samples.append(score)
        if score >= pair_stat(observed) and len(witnesses) < 3:
            witnesses.append({'raw': raw, 'axis_counts': values, 'pair_statistic': score})
    at_least = sum(v >= pair_stat(observed) for v in samples)
    return {'seed': seed, 'trials': TRIALS, 'at_least_observed': at_least,
            'tail_add_one': (1+at_least)/(1+TRIALS),
            'mean': float(np.mean(samples)), 'max': max(samples),
            'quantiles_50_90_95_99': np.quantile(samples, [.5, .9, .95, .99]).tolist(),
            'histogram': dict(sorted(Counter(samples).items())), 'witnesses': witnesses}


def main():
    assert counts('a'*91) == [26]*3
    assert counts(''.join(c*13 for c in 'abcdefg')) == [0]*3
    observed = counts(DBBI)
    assert observed == explicit_counts(DBBI)

    def raw_shuffle(rng):
        values = list(DBBI)
        rng.shuffle(values)
        return ''.join(values)

    nulls = {'raw_multiset': controls(raw_shuffle, 202610070, observed)}
    parses = enumerate_complete_parses(DBBI)
    assert [len(t) for t in parses] == [83, 84]
    for tokens in parses:
        host = [i for i in range(len(tokens)) if is_prime(i+1)]
        free = [i for i in range(len(tokens)) if not is_prime(i+1)]
        assert all(len(tokens[i]) == 1 for i in free)

        def draw(rng):
            values = [tokens[i] for i in free]
            rng.shuffle(values)
            output = list(tokens)
            for i, ch in zip(free, values):
                output[i] = ch
            assert all(output[i] == tokens[i] for i in host)
            return ''.join(output)

        nulls[f'prime_scaffold_{len(tokens)}'] = controls(draw, 202610000+len(tokens), observed)

    m = matrix(DBBI)
    grid_word, grid, pos = build_grid(DBBI[:13])
    decoded = bifid_decrypt(FAED, pos, grid)
    assert decoded.startswith('BTCSEEDDEOEM') and len(decoded) == 570
    index_outputs = {label: ''.join(decoded[i-shift] for i in INDICES)
                     for label, shift in [('zero_based', 0), ('one_based', 1)]}
    values = [ord(c)-96 for c in DBBI]
    report = {
        'diagnostic': 'exploratory_conditional_not_discovery_significance',
        'dbbi_sha256': hashlib.sha256(DBBI.encode()).hexdigest(),
        'protocol_sha256': hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'rows': [DBBI[i:i+13] for i in range(0, 91, 13)],
        'aligned_validation_rows': [VALIDATION_ANSWER[i:i+13] for i in range(0, 91, 13)],
        'center_rows_zero_based': list(CENTERS), 'comparisons_per_axis': 26,
        'axis_counts': observed, 'pair_statistic': pair_stat(observed),
        'cyclic_three_pair_counts': [int(sum(np.count_nonzero(m[(c-d)%7] == m[(c+d)%7])
                                             for d in (1, 2, 3))) for c in range(7)],
        'nulls': nulls,
        'indices_75172': list(INDICES), 'bifid_grid': grid_word,
        'index_outputs': index_outputs,
        'dbbi_a1i9_column_sums': np.array(values).reshape(7, 13).sum(axis=0).tolist(),
        'dbbi_a1i9_column_sums_i_zero': np.array([0 if c == 'i' else ord(c)-96 for c in DBBI]).reshape(7, 13).sum(axis=0).tolist(),
        'dbbi_a1i9_total': sum(values),
        'dbbi_a1i9_first_three_digits': ''.join(str(v) for v in values[:3]),
        'verification': 'planted controls, explicit counts, histograms and host retention passed',
        'password_oracle_calls': 0,
    }
    OUTPUT.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('axis_counts', 'pair_statistic',
        'cyclic_three_pair_counts', 'index_outputs', 'dbbi_a1i9_total')}, indent=2))
    print(json.dumps({k: {s: v[s] for s in ('tail_add_one', 'mean', 'max',
        'quantiles_50_90_95_99')} for k, v in nulls.items()}, indent=2))


if __name__ == '__main__':
    main()
