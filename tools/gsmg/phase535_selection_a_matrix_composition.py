#!/usr/bin/env python3
"""Compose Phase 525's five mappings with Phase 53's fixed matrix rule.

Exploratory bounded reconstruction, not an oracle or language search. All five
color-compatible mappings from both parses are retained. Use the historical
token values, backward placement ending at selected endpoints, 14x14 CCW
spiral and row-sum A0/mod26 rendering. Keep all three already-existing collision
policies; do not choose a policy by its text. Explicitly report unplaced tails.
"""
import hashlib
import json
from pathlib import Path

from data import DBBI
from phase525_dbbi_selection_a_reconstruction import (
    enumerate_complete_parses, picture_events, compatible_selections, parse_record,
)
from phase528_dbbi_84_token_consequence_audit import grouped_parse
from telegram_yellow_blue_guide_audit import token_value, output_from_row_sums
from telegram_yellow_blue_fefe_sweep import (
    POLICIES, historical_baseline, place_chunks, row_sums_from_spiral,
)
from first_piece_color_reconstruction import DEFAULT_IMAGE
from architect_choice_boundary_audit import audit as architect_audit, edge_letters


def run():
    baseline = historical_baseline()
    assert baseline.output == 'IZLKESEEDQPPEN'
    events = picture_events()
    rows = []
    for tokens in enumerate_complete_parses(DBBI):
        groups = grouped_parse(tokens)
        # Token boundaries come from the full grammatical parse, not greedy BE.
        chunks = [tuple(token_value(ch) for ch in g['payload']) + (token_value(g['host']),)
                  for g in groups['groups']]
        assert sum(map(len, chunks)) == 83
        assert ''.join(g['payload'] + g['host'] for g in groups['groups']) + groups['tail'] == DBBI
        matches = compatible_selections(events, parse_record(tokens)['host_colors'])
        for match in matches:
            selected = [e for e in events if e['event_rank'] not in match['omitted_event_ranks']]
            endpoints = [e['spiral_0'] for e in selected]
            variants = []
            for policy in POLICIES:
                cells, collisions = place_chunks(chunks, endpoints, policy)
                sums = row_sums_from_spiral(cells)
                variants.append({'policy': policy, 'collisions': collisions,
                                 'occupied_cells': sum(bool(v) for v in cells),
                                 'row_sums': list(sums), 'output': output_from_row_sums(sums),
                                 'spiral_cells': list(cells)})
            if match['represents_source_bytes_1_through_23_once']:
                assert len({tuple(v['spiral_cells']) for v in variants}) == 1
                assert all(v['collisions'] == 0 and v['occupied_cells'] == 83 for v in variants)
            rows.append({'logical_length': len(tokens), **match,
                         'endpoints_zero_based': endpoints,
                         'unplaced_tail': groups['tail'], 'variants': variants})
    assert len(rows) == 5
    # A single literal consumer: raw sums as one-based backward word indices
    # before CHOICE, using both already-frozen sources and their existing scope.
    # No modulus, new window, indexing direction search, or password test.
    selection_a = next(r for r in rows if r['represents_source_bytes_1_through_23_once'])
    sums = selection_a['variants'][0]['row_sums']
    architect = architect_audit()
    def consume(sums):
        consumers = []
        for name in ('film', 'screenplay'):
            tokens = architect['sources'][name]['moment_to_choice']['tokens']
            invalid = [index for index in sums if not 1 <= index <= len(tokens)]
            if invalid:
                consumers.append({'source': name, 'invalid_indices': invalid})
                continue
            selected = [tokens[-index] for index in sums]
            consumers.append({'source': name, 'word_count': len(tokens),
                              'backward_one_words': selected, 'edges': edge_letters(selected)})
        return consumers
    consumers = consume(sums)
    # Follow-up fixed in the dated reassessment before inspecting these values:
    # zero either host cells or payload cells, retaining all coordinates and the
    # same row-sum / backward-word consumer. Never move the unplaced tail.
    all_cells = selection_a['variants'][0]['spiral_cells']
    host_positions = set(selection_a['endpoints_zero_based'])
    host_cells = [v if i in host_positions else 0 for i, v in enumerate(all_cells)]
    payload_cells = [0 if i in host_positions else v for i, v in enumerate(all_cells)]
    assert all(a == h + p for a, h, p in zip(all_cells, host_cells, payload_cells))
    assert sum(host_cells) == 16 * 2 + 7 * 25 and sum(payload_cells) == 336
    partitions = []
    for name, cells in (('host_only', host_cells), ('payload_only', payload_cells)):
        partition_sums = row_sums_from_spiral(cells)
        partitions.append({'name': name, 'row_sums': list(partition_sums),
                           'output': output_from_row_sums(partition_sums),
                           'literal_last_words': consume(partition_sums)})
    return {'scope': 'fixed historical matrix rule composed with all five Phase-525 mappings',
            'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'image_sha256': hashlib.sha256(Path(DEFAULT_IMAGE).read_bytes()).hexdigest(),
            'dbbi_sha256': hashlib.sha256(DBBI.encode()).hexdigest(),
            'historical_baseline': baseline.output, 'rows': rows,
            'selection_a_literal_last_words': consumers,
            'selection_a_zeroing_comparison': partitions,
            'architect_source_hashes': architect['hashes'],
            'oracle_calls': 0, 'language_search': False}


if __name__ == '__main__':
    result = run()
    output = Path(__file__).with_name('phase535_selection_a_matrix_result.json')
    output.write_text(json.dumps(result, indent=2) + '\n')
    for row in result['rows']:
        print(json.dumps({k: v for k, v in row.items() if k != 'variants'}))
        for variant in row['variants']:
            print(json.dumps({k: v for k, v in variant.items() if k != 'spiral_cells'}))
    print(json.dumps(result['selection_a_literal_last_words'], indent=2))
    print(json.dumps(result['selection_a_zeroing_comparison'], indent=2))
