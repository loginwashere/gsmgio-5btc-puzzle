#!/usr/bin/env python3
"""Phase 454 recipient-side artifact acquisition audit.

The network search was executed once under the frozen Phase 454 protocol.  This
module validates the sanitized acquisition ledger and the evidence snapshot; it
does not contact external services, generate password material, or invoke an
oracle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
MANIFEST_PATH = SCRIPT_DIR / "phase454_acquisition_manifest.json"
LEDGER_PATH = SCRIPT_DIR / "phase454_attachment_ledger.json"
RESULT_PATH = SCRIPT_DIR / "phase454_result.json"
EXPECTED_MANIFEST_SHA256 = (
    "0a3ccbedbf0d5b4e68d4a6e02594eedc74af23aef0a341fd39eae5404b230b44"
)
EXPECTED_CLASSIFICATIONS = (
    "new_primary_artifact",
    "new_recipient_copy_known_bytes",
    "new_community_derivative",
    "known_duplicate",
    "metadata_or_recollection_only",
    "fabricated_or_spam",
    "access_limited",
    "no_result",
)
ICON_PATHS = (
    "doc/img/gsmg_icon_black_banking_war.png",
    "doc/img/gsmg_icon_blue_ca.png",
    "doc/img/gsmg_icon_blue_dig_i.png",
    "doc/img/gsmg_icon_blue_lock_lo.png",
    "doc/img/gsmg_icon_red_crypto_gic.png",
    "doc/img/gsmg_icon_red_n_you.png",
    "doc/img/gsmg_icon_red_open_lock_n_ing.png",
    "doc/img/gsmg_icon_red_t.png",
)
EXPECTED_ICON_HASHES = (
    "907b489f6e77a828595805d7e370535a0aa85697ca951e0e09553e6c9a3410d2",
    "e59d42e85997d395d41eaad6fb64f343eadb752918bf33098093e96a8a9dd8be",
    "a6889a2e090d32920e47124f0187d2e61979409f9bb32a09bf0c990db56d05f9",
    "60b01e5bc4181ed4236df736f7f7841aa98dde1aac108d65a385f5dc7a97cc6b",
    "8aad87b987ee7d8ee8c7884ba47abc022cb31753fd1a16a7e59101e50dd4a6f6",
    "89a81a1b30cc399ca77dde6ffa2b01d0807e8db9b22636d157ca9f54eaf86aeb",
    "ea1cd545040c051a62e7695eb2dd2ad983be26849b54cd686feea12b11f3d203",
    "86fb2eff01d3b4f25e7bd9c64c736ce0ffd0e129b8c77fab81aac5d02fd04d35",
)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def load_manifest() -> dict:
    if sha256_path(MANIFEST_PATH) != EXPECTED_MANIFEST_SHA256:
        raise AssertionError("Phase 454 manifest digest drifted")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if tuple(manifest["classification_vocabulary"]) != EXPECTED_CLASSIFICATIONS:
        raise AssertionError("classification vocabulary drifted")
    for key, digest_key in (
        ("protocol", "sha256"),
        ("provenance_guard", "phase409_sha256"),
    ):
        row = manifest[key]
        path_key = "path" if key == "protocol" else "phase409_path"
        if sha256_path(ROOT / row[path_key]) != row[digest_key]:
            raise AssertionError(f"pinned source drifted: {row[path_key]}")
    ledger_row = manifest["lanes"]["fixed_discussion_roots"]["attachment_ledger"]
    if sha256_path(ROOT / ledger_row["path"]) != ledger_row["sha256"]:
        raise AssertionError("attachment ledger drifted")
    return manifest


def validate_provenance_guard(manifest: dict) -> None:
    guard = manifest["provenance_guard"]
    assert len(guard["spam_addresses"]) == 2
    assert len(set(guard["spam_addresses"])) == 2
    assert all(len(address) >= 26 for address in guard["spam_addresses"])
    assert len(guard["fabricated_claim_cluster"]) == 6
    assert len(set(guard["fabricated_claim_cluster"])) == 6


def validate_attachment_ledger(manifest: dict) -> dict:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    rows = ledger["attachments"]
    urls = [row["url"] for row in rows]
    if len(urls) != len(set(urls)):
        raise AssertionError("duplicate attachment URL")
    if urls != sorted(urls):
        raise AssertionError("attachment ledger order drifted")

    allowed_hosts = {"github.com", "user-images.githubusercontent.com"}
    for row in rows:
        parsed = urlparse(row["url"])
        assert parsed.scheme == "https" and parsed.netloc in allowed_hosts
        assert row["classification"] in {
            "new_community_derivative", "fabricated_or_spam", "access_limited"
        }
        assert row["occurrences"]
        for occurrence in row["occurrences"]:
            assert occurrence["issue"] > 0
            assert occurrence["author"]
            assert occurrence["created_at"].endswith("Z")
        if row["classification"] == "access_limited":
            assert row["http_result"] == 404
            assert row["sha256"] is None and row["bytes"] is None
            assert row["media"] is None
        else:
            assert row["http_result"] == 200
            assert is_sha256(row["sha256"])
            assert row["bytes"] > 0
            assert row["media"]["format"] in {"JPEG", "PNG"}
            assert row["media"]["width"] > 0 and row["media"]["height"] > 0

    classifications = Counter(row["classification"] for row in rows)
    observed = {
        "unique_urls": len(rows),
        "downloaded": sum(row["http_result"] == 200 for row in rows),
        "access_limited": classifications["access_limited"],
        "unique_downloaded_sha256": len(
            {row["sha256"] for row in rows if row["sha256"] is not None}
        ),
        "fabricated_or_spam_urls": classifications["fabricated_or_spam"],
        "new_community_derivative_urls": classifications[
            "new_community_derivative"
        ],
    }
    if observed != ledger["summary"]:
        raise AssertionError("attachment ledger summary mismatch")

    pinned = manifest["lanes"]["fixed_discussion_roots"]["attachment_ledger"]
    manifest_view = {
        "unique_urls": pinned["unique_urls"],
        "downloaded": pinned["downloaded"],
        "unique_downloaded_sha256": pinned["unique_downloaded_sha256"],
        "new_community_derivative_urls": pinned[
            "new_community_derivative_urls"
        ],
        "fabricated_or_spam_urls": pinned["fabricated_or_spam_urls"],
        "access_limited": pinned["access_limited_urls"],
    }
    if manifest_view != observed:
        raise AssertionError("manifest/attachment ledger count mismatch")
    return observed


def validate_recipient_copies(manifest: dict) -> None:
    local_hashes = tuple(sha256_path(ROOT / path) for path in ICON_PATHS)
    if local_hashes != EXPECTED_ICON_HASHES:
        raise AssertionError("local Stage-1 icon bytes drifted")
    urlscan = manifest["lanes"]["search_engine"]["urlscan_2019"]
    assert urlscan["recorded_icon_hashes"] == len(EXPECTED_ICON_HASHES)
    assert urlscan["exact_local_icon_matches"] == len(EXPECTED_ICON_HASHES)
    assert urlscan["classification"] == "new_recipient_copy_known_bytes"
    assert is_sha256(urlscan["main_response_sha256"])

    screenshots = manifest["lanes"]["search_engine"]["server_daten_2025"]
    assert screenshots["classification"] == "new_recipient_copy_known_bytes"
    assert all(is_sha256(value) for value in screenshots["screenshot_sha256"].values())
    assert screenshots["known_form_action_confirmed"].endswith(
        "/phase1verification"
    )


def validate_lane_contract(manifest: dict) -> None:
    lanes = manifest["lanes"]
    local = lanes["local_git_recovery"]
    assert local["mapped_to_unreachable_tree"] + local["unmapped"] == local[
        "unreachable_blobs"
    ]
    assert local["binary_blobs"] == 1
    assert local["result"] == "no_new_primary_artifact"

    github = lanes["github"]
    assert sum(row["total_count"] for row in github["repository_queries"]) == 8
    assert github["unique_repository_results"] == 5
    assert github["canonical_repo"]["public_forks_returned"] <= github[
        "canonical_repo"
    ]["advertised_forks"]
    assert github["result"] == "no_new_primary_artifact"
    assert all(
        row["classification"] in EXPECTED_CLASSIFICATIONS
        for row in github["repositories"] + github["fork_deltas"]
    )

    archive = lanes["internet_archive_metadata"]
    assert len(archive["queries"]) == 4
    assert sum(row["num_found"] for row in archive["queries"]) == 0
    assert archive["classification"] == "no_result"

    roots = lanes["fixed_discussion_roots"]
    assert roots["reddit_posts"] == 2 and roots["reddit_new_artifact_links"] == 0
    assert roots["bitcointalk_topics"] == 1
    assert roots["bitcointalk_new_artifact_links"] == 0
    assert roots["result"] == "no_new_primary_artifact"
    assert lanes["search_engine"]["queries_run"] == 8


def build_report(manifest: dict) -> dict:
    attachment_summary = validate_attachment_ledger(manifest)
    validate_provenance_guard(manifest)
    validate_recipient_copies(manifest)
    validate_lane_contract(manifest)
    summary = manifest["summary"]
    assert summary["new_primary_artifact"] == 0
    assert summary["new_recipient_copy_known_bytes"] == 2
    assert summary["gap_closures"] == 0
    assert not summary["oracle_run"]
    assert summary["password_materials_generated"] == 0
    assert not summary["external_outreach"]
    return {
        "phase": 454,
        "date": manifest["date"],
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "attachment_ledger_sha256": sha256_path(LEDGER_PATH),
        "attachment_summary": attachment_summary,
        "lane_results": {
            "local_git_recovery": manifest["lanes"]["local_git_recovery"]["result"],
            "github": manifest["lanes"]["github"]["result"],
            "internet_archive_metadata": manifest["lanes"][
                "internet_archive_metadata"
            ]["classification"],
            "fixed_discussion_roots": manifest["lanes"][
                "fixed_discussion_roots"
            ]["result"],
            "search_engine": "two_recipient_copies_known_bytes",
        },
        "recipient_copy_confirmations": [
            "urlscan_2019_stage1_hash_set",
            "server_daten_2025_stage1_screenshots",
        ],
        **summary,
    }


def self_test(manifest: dict) -> None:
    report = build_report(manifest)
    assert report["attachment_summary"] == {
        "unique_urls": 65,
        "downloaded": 64,
        "access_limited": 1,
        "unique_downloaded_sha256": 35,
        "fabricated_or_spam_urls": 49,
        "new_community_derivative_urls": 15,
    }
    assert report["disposition"] == "provenance_upgraded_no_new_clue_content"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--report", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()

    manifest = load_manifest()
    if args.self_test:
        self_test(manifest)
        print("Phase 454 self-test: PASS")
        return 0
    report = build_report(manifest)
    if args.run:
        RESULT_PATH.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"wrote {RESULT_PATH}")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
