#!/usr/bin/env python3
"""Exact closed-corpus generators for DBBI's complete non-host residue."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re

from data import DBBI, VALIDATION_ANSWER
from phase525_dbbi_selection_a_reconstruction import enumerate_complete_parses, is_prime

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PROTOCOL = ROOT / 'doc/Brainstorms/2026-09-20 - Phase 536 Prime Scaffold Numeric Text Generator Protocol.md'
LOCK = HERE / 'phase536_execution_lock.json'
RESULT = HERE / 'phase536_numeric_text_result.json'
MODELS = ('R9', 'D10', 'B9')
CASES = ('upper', 'lower')
LENGTHS = (60, 61)
MIN_WINDOW, MAX_WINDOW = 16, 40


def digest(value):
    return hashlib.sha256(value).hexdigest()


def base9(value):
    if value == 0:
        return '0'
    digits = []
    while value:
        value, remainder = divmod(value, 9)
        digits.append(str(remainder))
    return ''.join(reversed(digits))


def encode(text, model):
    raw = text.encode('ascii')
    if model == 'R9':
        return base9(int.from_bytes(raw, 'big'))
    if model == 'D10':
        return str(int.from_bytes(raw, 'big'))
    if model == 'B9':
        return ''.join(base9(b).zfill(3) for b in raw)
    raise ValueError(model)


def decode(digits, model):
    if model == 'B9':
        if len(digits) % 3:
            raise ValueError('incomplete byte')
        return bytes(int(digits[i:i+3], 9) for i in range(0, len(digits), 3))
    value = int(digits, 9 if model == 'R9' else 10)
    return value.to_bytes((value.bit_length() + 7) // 8, 'big')


def pattern(value):
    labels = {}
    return bytes(labels.setdefault(ch, len(labels)) for ch in value)


def matching_map(digits, residue):
    if len(digits) != len(residue):
        return None
    forward, backward = {}, {}
    for digit, symbol in zip(digits, residue):
        if digit in forward and forward[digit] != symbol:
            return None
        if symbol in backward and backward[symbol] != digit:
            return None
        forward[digit], backward[symbol] = symbol, digit
    return forward


def eligible_lengths(model, case, digit_length):
    lo, hi = ('A', 'Z') if case == 'upper' else ('a', 'z')
    return [n for n in range(MIN_WINDOW, MAX_WINDOW + 1)
            if len(encode(lo * n, model)) <= digit_length <= len(encode(hi * n, model))]


def target_records():
    records = []
    for tokens in enumerate_complete_parses(DBBI):
        residue = ''.join(t for pos, t in enumerate(tokens, 1) if not is_prime(pos))
        records.append({'logical_length': len(tokens), 'tokens': list(tokens),
                        'residue': residue, 'residue_sha256': digest(residue.encode())})
    assert [len(r['residue']) for r in records] == list(LENGTHS)
    return records


def insert_hosts(residue, tokens):
    expected = sum(not is_prime(i) for i in range(1, len(tokens) + 1))
    if len(residue) != expected:
        raise ValueError('residue does not cover every non-host position')
    it = iter(residue)
    return ''.join(t if is_prime(i) else next(it) for i, t in enumerate(tokens, 1))


def source_documents():
    # Only decrypt already-solved inputs; no unresolved blob is queried.
    import phase482a_faed_frequency_signature_audit as corpus
    docs = corpus.source_documents()
    readme = (ROOT / 'README.md').read_text()
    extra = [
        ('phase322_answer', VALIDATION_ANSWER),
        ('stage0_decoded_url', 'gsmg.io/theseedisplanted'),
        ('stage1_credential', 'theflowerblossomsthroughwhatseemstobeaconcretesurface'),
    ]
    for name, text in extra:
        if name != 'phase322_answer':
            assert text in readme
        docs.append({'name': name, 'tier': 'puzzle_native', 'text': text,
                     'extracted_sha256': digest(text.encode())})
    assert len(docs) == 9 and len({d['name'] for d in docs}) == 9
    return docs


def normalized_documents():
    out = []
    for source in source_documents():
        letters = ''.join(re.findall('[A-Za-z]', source['text']))
        for case in CASES:
            value = getattr(letters, case)()
            out.append({'source': source['name'], 'tier': source['tier'], 'case': case,
                        'text': value, 'sha256': digest(value.encode())})
    return out


def candidates(documents):
    for doc in documents:
        for model in MODELS:
            ns = sorted(set(n for length in LENGTHS for n in eligible_lengths(model, doc['case'], length)))
            for n in ns:
                for start in range(len(doc['text']) - n + 1):
                    text = doc['text'][start:start+n]
                    digits = encode(text, model)
                    yield doc, model, start, text, digits


def scan(documents, targets):
    target_patterns = {}
    for target in targets:
        target_patterns.setdefault(pattern(target['residue']), []).append(target)
    matches, counts = [], Counter()
    for doc, model, start, text, digits in candidates(documents):
        counts['windows_encoded'] += 1
        counts[model] += 1
        if len(digits) not in LENGTHS:
            continue
        counts['exact_digit_length'] += 1
        if len(set(digits)) != 9:
            continue
        counts['nine_distinct_digits'] += 1
        for target in target_patterns.get(pattern(digits), ()):
            mapping = matching_map(digits, target['residue'])
            assert mapping is not None
            remapped = ''.join(mapping[d] for d in digits)
            raw = insert_hosts(remapped, target['tokens'])
            expected_raw = ''.join(target['tokens'])
            # Synthetic target tokens include synthetic non-host symbols too.
            assert raw == expected_raw
            assert decode(digits, model) == text.encode()
            matches.append({'source': doc['source'], 'case': doc['case'], 'model': model,
                            'start': start, 'window_length': len(text), 'plaintext': text,
                            'logical_length': target['logical_length'], 'digits': digits,
                            'digit_to_symbol': mapping, 'reconstructed_raw_sha256': digest(raw.encode())})
    return {'counts': dict(counts), 'matches': matches, 'match_count': len(matches)}


def planted_gate():
    rng = random.Random(536001)
    originals = {len(t['residue']): t for t in target_records()}
    rows = []
    for model in MODELS:
        for case in CASES:
            for length in LENGTHS:
                ns = eligible_lengths(model, case, length)
                row = {'model': model, 'case': case, 'digit_length': length, 'eligible_lengths': ns}
                if not ns:
                    rows.append({**row, 'status': 'structurally_ineligible'})
                    continue
                alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if case == 'upper' else 'abcdefghijklmnopqrstuvwxyz'
                for attempt in range(20000):
                    text = ''.join(rng.choice(alphabet) for _ in range(ns[attempt % len(ns)]))
                    digits = encode(text, model)
                    if len(digits) == length and len(set(digits)) == 9:
                        break
                else:
                    raise RuntimeError(f'fixture generation failed: {row}')
                symbols = list('abcdefghi')
                rng.shuffle(symbols)
                mapping = dict(zip(sorted(set(digits)), symbols))
                residue = ''.join(mapping[d] for d in digits)
                template = originals[length]
                it = iter(residue)
                tokens = [t if is_prime(i) else next(it) for i, t in enumerate(template['tokens'], 1)]
                fixture = {'logical_length': len(tokens), 'tokens': tokens, 'residue': residue}
                distractor = 'DISTRACTOR' if case == 'upper' else 'distractor'
                doc = {'source': 'planted', 'case': case, 'text': distractor + text + distractor}
                found = scan([doc], [fixture])['matches']
                recovered = [m for m in found if m['model'] == model and m['start'] == len(distractor)
                             and m['plaintext'] == text and m['digit_to_symbol'] == mapping]
                if len(recovered) != 1:
                    raise AssertionError(f'planted recovery failed: {row}')
                rows.append({**row, 'status': 'exactly_recovered', 'attempts': attempt + 1,
                             'plaintext_sha256': digest(text.encode())})
    assert matching_map('0012', 'aabc') == {'0': 'a', '1': 'b', '2': 'c'}
    assert matching_map('0012', 'abbc') is None  # one-symbol corruption
    assert matching_map('0012', 'aabb') is None  # two digits alias one symbol
    try:
        insert_hosts(originals[61]['residue'][:-1], originals[61]['tokens'])
    except ValueError:
        pass
    else:
        raise AssertionError('incomplete terminal residue accepted')
    return rows


def input_hashes():
    import phase482a_faed_frequency_signature_audit as corpus
    paths = [Path(__file__), PROTOCOL, HERE / 'data.py',
             HERE / 'phase525_dbbi_selection_a_reconstruction.py',
             HERE / 'phase482a_faed_frequency_signature_audit.py',
             HERE / 'phase410_solved_vector_toolchain_provenance_audit.py',
             HERE / 'p32_sibling_password_audit.py', HERE / 'cb_common.py',
             ROOT / 'README.md', corpus.MATRIX_FILE, corpus.BOOK_FILE,
             corpus.p410.WAYBACK_ARTIFACT_PATH,
             HERE / 'test_phase536_prime_scaffold_numeric_text.py']
    return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in paths}


def lock_payload():
    gate = planted_gate()
    docs = normalized_documents()
    counts = Counter()
    for doc in docs:
        for model in MODELS:
            ns = set(n for length in LENGTHS for n in eligible_lengths(model, doc['case'], length))
            counts[model] += sum(max(0, len(doc['text']) - n + 1) for n in ns)
    return {'phase': 536, 'files_sha256': input_hashes(), 'targets': target_records(),
            'corpus': [{k:v for k,v in d.items() if k != 'text'} | {'length':len(d['text'])} for d in docs],
            'windows_to_encode': dict(counts), 'planted_gate': gate,
            'models': list(MODELS), 'cases': list(CASES), 'window_bounds': [MIN_WINDOW, MAX_WINDOW]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--run', action='store_true')
    mode.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(planted_gate(), indent=2))
        return
    payload = lock_payload()
    if args.prepare:
        if LOCK.exists():
            raise RuntimeError('execution lock already exists; refusing replacement')
        LOCK.write_text(json.dumps(payload, indent=2) + '\n')
        print(json.dumps({'lock': str(LOCK), 'windows': payload['windows_to_encode'],
                          'gate': payload['planted_gate']}, indent=2))
        return
    if json.loads(LOCK.read_text()) != payload:
        raise RuntimeError('execution lock mismatch; no real scan performed')
    result = scan(normalized_documents(), payload['targets'])
    assert result['counts']['windows_encoded'] == sum(payload['windows_to_encode'].values())
    result.update({'phase': 536, 'lock_sha256': digest(LOCK.read_bytes()),
                   'unresolved_oracle_calls': 0,
                   'disposition': 'candidate_requires_downstream_validation' if result['matches']
                                  else 'bounded_negative_exact_numeric_text_generators'})
    RESULT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
