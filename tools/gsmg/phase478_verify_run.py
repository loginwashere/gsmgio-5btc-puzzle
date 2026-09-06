#!/usr/bin/env python3
"""Fail-closed post-run verifier for Phase 478.

Usage:
    phase478_verify_run.py <oracle_lock_json> <match_report_json>
                           [verification_record_json]

Every file hash named by the oracle lock is checked before the locked
matcher is imported. The verifier then recomputes the matcher report from
the locked manifest and requires exact equality with the saved report.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent


class VerificationError(Exception):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_locked_path(repo_root: Path, value: str) -> Path:
    repo_root = repo_root.resolve()
    path = (repo_root / value).resolve()
    try:
        path.relative_to(repo_root)
    except ValueError as exc:
        raise VerificationError(f'locked path escapes repository: {value}') from exc
    if not path.is_file():
        raise VerificationError(f'locked file is missing: {value}')
    return path


def verify_lock_files(lock: dict, repo_root: Path) -> dict[str, dict[str, str]]:
    if lock.get('phase') != 478:
        raise VerificationError(f"expected phase 478, got {lock.get('phase')!r}")
    if lock.get('lock_kind') != 'oracle_lock':
        raise VerificationError(
            f"expected lock_kind 'oracle_lock', got {lock.get('lock_kind')!r}"
        )

    specifications = (
        ('manifest', lock['manifest_path'], lock['manifest_sha256']),
        (
            'manifest_annotations',
            lock['manifest_annotations_path'],
            lock['manifest_annotations_sha256'],
        ),
        (
            'manifest_builder_script',
            lock['manifest_builder_script'],
            lock['manifest_builder_script_sha256'],
        ),
        ('matcher_script', lock['matcher_script'], lock['matcher_script_sha256']),
        (
            'phase478_common',
            'tools/gsmg/phase478_common.py',
            lock['phase478_common_sha256'],
        ),
    )

    checked = {}
    for label, relative_path, expected in specifications:
        path = resolve_locked_path(repo_root, relative_path)
        actual = sha256_file(path)
        if actual != expected:
            raise VerificationError(
                f'{label} SHA-256 mismatch: locked {expected}, actual {actual}'
            )
        checked[label] = {
            'path': relative_path,
            'sha256': actual,
        }
    return checked


def load_locked_matcher(path: Path):
    module_name = '_phase478_locked_matcher_for_verification'
    prior_common = sys.modules.pop('phase478_common', None)
    prior_matcher = sys.modules.pop(module_name, None)
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise VerificationError(f'cannot import locked matcher: {path}')
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)
        sys.modules.pop(module_name, None)
        sys.modules.pop('phase478_common', None)
        if prior_common is not None:
            sys.modules['phase478_common'] = prior_common
        if prior_matcher is not None:
            sys.modules[module_name] = prior_matcher


def verify(
    oracle_lock_path,
    match_report_path,
    *,
    repo_root: Path = REPO_ROOT,
    matcher_loader=load_locked_matcher,
) -> dict:
    oracle_lock_path = Path(oracle_lock_path)
    match_report_path = Path(match_report_path)
    with oracle_lock_path.open() as handle:
        lock = json.load(handle)

    checked = verify_lock_files(lock, repo_root)
    matcher_path = resolve_locked_path(repo_root, lock['matcher_script'])
    manifest_path = resolve_locked_path(repo_root, lock['manifest_path'])

    # Import happens only after every lock-named hash, including common.py,
    # has been checked.
    matcher = matcher_loader(matcher_path)
    if matcher.DBBI_PATTERN != lock['dbbi_pattern']:
        raise VerificationError(
            'locked DBBI pattern differs from the verified matcher/common value'
        )

    with match_report_path.open() as handle:
        saved_report = json.load(handle)
    reproduced_report = matcher.run_matcher(manifest_path)
    if reproduced_report != saved_report:
        raise VerificationError('recomputed matcher report differs from saved report')

    return {
        'phase': 478,
        'consistent': True,
        'oracle_lock_sha256': sha256_file(oracle_lock_path),
        'match_report_sha256': sha256_file(match_report_path),
        'checked_hashes': checked,
        'eligible_scored': reproduced_report['eligible_scored'],
        'match_found': reproduced_report['match_found'],
    }


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print(__doc__)
        return 2
    try:
        record = verify(sys.argv[1], sys.argv[2])
    except (KeyError, OSError, ValueError, VerificationError) as exc:
        print(json.dumps({'phase': 478, 'consistent': False, 'error': str(exc)}, indent=2))
        return 1

    rendered = json.dumps(record, indent=2, sort_keys=True) + '\n'
    if len(sys.argv) == 4:
        Path(sys.argv[3]).write_text(rendered)
    print(rendered, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
