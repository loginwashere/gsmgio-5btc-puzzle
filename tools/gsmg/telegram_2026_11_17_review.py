#!/usr/bin/env python3
"""Read-only checks for the November 17 Telegram export; never execute attachments."""
import ast
import base64
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ROOT = Path(__file__).resolve().parents[2]
EXPORTS = Path('/home/loginwashere/Downloads/Telegram Desktop')
NEW = EXPORTS / 'ChatExport_2026-11-17'
OLD = EXPORTS / 'ChatExport_2026-11-04'
OUTPUT = ROOT / 'doc/evidence/TELEGRAM_REVIEW_2026_11_17.json'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def text(m):
    t = m.get('text', '')
    return t if isinstance(t, str) else ''.join(v if isinstance(v, str) else v.get('text', '') for v in t)


def constants():
    out = {}
    for n in ast.parse((ROOT / 'tools/gsmg/data.py').read_text()).body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            try:
                out[n.targets[0].id] = ast.literal_eval(n.value)
            except (ValueError, TypeError):
                pass
    return out


def decrypt(raw, password, digest):
    assert raw[:8] == b'Salted__' and len(raw[16:]) % 16 == 0
    material, previous = b'', b''
    while len(material) < 48:
        previous = hashlib.new(digest, previous + password + raw[8:16]).digest()
        material += previous
    dec = Cipher(algorithms.AES(material[:32]), modes.CBC(material[32:48])).decryptor()
    return dec.update(raw[16:]) + dec.finalize()


def unpad(b):
    n = b[-1]
    return b[:-n] if 1 <= n <= 16 and b[-n:] == bytes([n]) * n else None


def main():
    new_bytes, old_bytes = (NEW / 'result.json').read_bytes(), (OLD / 'result.json').read_bytes()
    export, before = json.loads(new_bytes), json.loads(old_bytes)
    rows, old = export['messages'], {m['id']: m for m in before['messages']}
    delta = [m for m in rows if m['id'] > max(old)]
    overlap = [m for m in rows if m['id'] in old]
    byid = {m['id']: m for m in rows}
    creator = [m for m in rows if m.get('from_id') == 'user9815232']
    manifest = []
    for m in rows:
        for kind in ['photo', 'file']:
            if m.get(kind):
                p = NEW / m[kind]
                manifest.append({'id': m['id'], 'kind': kind, 'path': m[kind], 'exists': p.is_file(),
                                 'bytes': p.stat().st_size if p.is_file() else None,
                                 'sha256': sha(p.read_bytes()) if p.is_file() else None})
    result = {
        'export': {k: export[k] for k in ['name', 'id', 'type']},
        'export_sha256': sha(new_bytes), 'previous_export_sha256': sha(old_bytes),
        'coverage': {'total': len(rows), 'new': len(delta), 'new_types': dict(Counter(m['type'] for m in delta)),
                     'first': rows[0]['date'], 'last': rows[-1]['date'],
                     'first_new_id': delta[0]['id'], 'last_new_id': delta[-1]['id'],
                     'overlap': len(overlap),
                     'overlap_text_changes': [m['id'] for m in overlap if text(m) != text(old[m['id']])],
                     'overlap_field_changes': [
                         {'id': m['id'], 'fields': sorted(k for k in m.keys() | old[m['id']].keys()
                                                       if m.get(k) != old[m['id']].get(k))}
                         for m in overlap if m != old[m['id']]],
                     'new_photos': sum('photo' in m for m in delta),
                     'new_file_types': dict(Counter(m.get('media_type', 'document') for m in delta if 'file' in m))},
        'creator': creator,
        'creator_forward_labels': [m for m in rows if m.get('forwarded_from') == 'Jrk Bgrt'],
        'j_followup_account': old[78605]['from_id'],
        'j_followup_messages': [m['id'] for m in rows if m.get('from_id') == old[78605]['from_id']],
        'attachments': manifest,
    }
    c = constants()
    raw = base64.b64decode(c['PHASE32_BLOB_B64'])
    plain = unpad(decrypt(raw, c['VERIFIED_PRIOR_COMMAND_HASHES']['phase32_clues'].encode(), 'sha256'))
    assert plain is not None
    coded = plain.split(b'\r\n\r\n')[2].decode('latin1').encode('cp273').decode('ascii')
    key = 'THEMATRIXHASYOU'
    speech = ''.join(chr((ord(key[i % 15]) - ord(v.upper())) % 26 + 65) for i, v in enumerate(coded))
    speech_checks = {}
    for name in ['architect_letters_1539.txt', 'architect-monologue.txt']:
        b = (NEW / 'files' / name).read_bytes()
        letters = ''.join(v for v in b.decode().upper() if 'A' <= v <= 'Z')
        speech_checks[name] = {'bytes': len(b), 'sha256': sha(b), 'letters': len(letters), 'native_equal': letters == speech}
    alleged = (NEW / 'files/cosmic_plain.bin').read_bytes()
    counts = Counter(alleged)
    opaque = (NEW / 'files/matrix_formula.py').read_bytes()
    result['byte_checks'] = {
        'speech': speech_checks,
        'phase32_attachment_matches_canonical': base64.b64decode((NEW / 'files/phase32_2020_blob.txt').read_bytes()) == raw,
        'cosmic_plain': {'bytes': len(alleged), 'sha256': sha(alleged),
                         'matches_previous_arbitrary_plaintext': sha(alleged) == '4f7a1e4efe4bf6c5581e32505c019657cb7b030e90232d33f011aca6a5e9c081',
                         'printable_fraction': sum(32 <= v < 127 or v in (9, 10, 13) for v in alleged) / len(alleged),
                         'entropy_bits_per_byte': -sum(n / len(alleged) * math.log2(n / len(alleged)) for n in counts.values())},
        'matrix_formula_attachment': {'bytes': len(opaque), 'sha256': sha(opaque), 'nul_bytes': opaque.count(b'\0')},
    }
    square = ''.join(dict.fromkeys('NEVERFAIL' + 'ABCDEFGHIKLMNOPQRSTUVWXYZ'))
    pos = {v: divmod(i, 5) for i, v in enumerate(square)}
    ciphertext, decoded = 'BGVUDIFGQEVPFI', ''
    assert ciphertext in text(byid[79784])
    for offset in range(0, len(ciphertext), 8):
        chunk = ciphertext[offset:offset + 8]
        coords = [z for v in chunk for z in pos[v]]
        decoded += ''.join(square[coords[i] * 5 + coords[i + len(chunk)]] for i in range(len(chunk)))
    bits = text(byid[79804])
    result['oleg_partial'] = {'input': ciphertext, 'square': square, 'period': 8, 'decoded': decoded,
                              'matches_posted': decoded == 'LOGINMXESGNCEG',
                              'pex_bits': bits, 'bit_count': len(bits), 'flag': bits[0],
                              'next_three_7bit_chars': ''.join(chr(int(bits[i:i + 7], 2)) for i in range(1, 22, 7)),
                              'tail_bits': len(bits[22:]),
                              'limitations': 'Does not reconstruct source image -> ciphertext or FAED -> 87 bits; those rules are missing.'}
    result['prime_counts'] = {str(n): sum(all(v % k for k in range(2, math.isqrt(v) + 1)) for v in range(2, n + 1))
                              for n in [91, 570]}
    # Finite check declared here: exact claim labels only; no repairs or search.
    seeds = ['NEVERFAIL', 'LOGIN', 'LOGINMXESGNCEG', 'USE PEX', 'USEPEX', 'PEX',
             'HASHTHETEXT-2019-COSMIC-DUALITY']
    checks = []
    for seed in seeds:
        for form, password in [('raw', seed.encode()), ('sha256_hex', hashlib.sha256(seed.encode()).hexdigest().encode())]:
            for digest in ['md5', 'sha256']:
                for label in ['P32_TRAILING_BLOB_B64', 'SALPHASEION_BLOB_B64', 'COSMIC_BLOB_B64']:
                    body = unpad(decrypt(base64.b64decode(c[label]), password, digest))
                    if body is not None:
                        checks.append({'seed': seed, 'form': form, 'evp_digest': digest, 'target': label,
                                       'bytes': len(body), 'sha256': sha(body),
                                       'printable_fraction': sum(32 <= v < 127 or v in (9, 10, 13) for v in body) / len(body)})
    result['finite_password_check'] = {'seeds': seeds, 'forms': ['raw', 'sha256_hex'], 'evp_digests': ['md5', 'sha256'],
                                       'targets': ['P32_TRAILING_BLOB_B64', 'SALPHASEION_BLOB_B64', 'COSMIC_BLOB_B64'],
                                       'attempts': len(seeds) * 2 * 2 * 3, 'padding_matches': checks,
                                       'scope': 'No newline/case/typo variants, other ciphers, or other KDFs tested. Padding alone is not authentication.'}
    dust = json.loads((NEW / 'files/dust_analysis_20261114.json').read_text())
    result['dust_attachment_claims_not_independently_fetched'] = {
        'fetched_at': dust['fetched_at'],
        **{k: {s: dust[k][s] for s in ['address', 'summary', 'dust_count', 'dust_from_target_count']}
           for k in ['half', 'better_half']}}
    assert len(creator) == 19 and len(delta) == 3507
    assert not result['coverage']['overlap_text_changes']
    assert all(row['exists'] for row in manifest)
    assert all(v['native_equal'] for v in speech_checks.values())
    assert decoded == 'LOGINMXESGNCEG' and len(bits) == 87
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output': str(OUTPUT), 'coverage': result['coverage'],
                      'creator_count': len(creator), 'byte_checks': result['byte_checks'],
                      'finite_password_check': result['finite_password_check']}, indent=2))


if __name__ == '__main__':
    main()
