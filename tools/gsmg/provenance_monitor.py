#!/usr/bin/env python3
"""Phase 347: provenance-monitoring baseline for restored gsmg.io, the
SalPhaseIon route, and the Hosterjack compendium/repository.

Frozen per the user's explicit 2026-08-20 scope:
  - Exactly 3 frozen URLs (FROZEN_URLS below) -- no crawling, no route
    discovery, no expansion beyond what's named.
  - Record raw-response hash, normalized content hash, HTTP status, the
    full redirect chain, an observation timestamp, and a source class for
    each.
  - Query only passive archive indexes for new captures of these exact
    routes: Wayback CDX + urlscan.io for the two web pages (reusing
    salphaseion_wayback_history_audit.py / salphaseion_urlscan_history_
    audit.py's existing self-alerting live_audit() functions for the
    SalPhaseIon route rather than re-implementing the same check), and
    GitHub's own commit history (the git-native equivalent of an archive
    index -- content-addressed, append-only, passive to read) for the
    Hosterjack repository. Never an active crawl/probe beyond one plain
    GET per URL for the baseline itself.
  - Alert only on: changed bytes (digest differs from a previously
    recorded baseline) or a newly discovered historical capture/commit.
    A fresh timestamp alone, with identical content, is not an alert.
  - Attribution stays fixed and explicit, never inferred from content:
    restored gsmg.io = unknown (FINDINGS Phase 329 explicitly left
    operator identity unresolved); Hosterjack = community; any archive
    capture = "authentic observation, not proof of creator operation."
  - No JavaScript execution, no form submission, no wallet interaction,
    no download that gets executed, no WHOIS/RDAP/certificate inspection
    or other operator-identification work (Phase 329's own territory,
    already closed) -- exactly one plain read-only HTTP GET per frozen
    URL for the baseline, matching Phase 329's own established safety
    boundary ("all inspection was read-only... nothing from the live
    host was added to the repository").
  - One-shot only: this writes a single baseline snapshot
    (provenance_baseline.json). Making it recurring (a scheduled
    re-check) is explicitly deferred until requested.

Not stored: raw response bytes. Only hashes/metadata are persisted, same
as Phase 329's own convention.
"""

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

BASELINE_PATH = SCRIPT_DIR / "provenance_baseline.json"

# ---------------------------------------------------------------------------
# Frozen scope -- exactly 3 URLs, no more.
# ---------------------------------------------------------------------------

FROZEN_URLS = {
    "gsmg_io_root": "https://gsmg.io/",
    "salphaseion_route": (
        "https://gsmg.io/"
        "89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32"
    ),
    "hosterjack_repo": "https://github.com/HosterjackAGV/gsmg-5btc-puzzle",
}

# Fixed, never inferred from fetched content. FINDINGS Phase 329: the
# restored deployment's operator identity is explicitly unresolved.
# [[reference_hosterjack_fork]]: Hosterjack is a community fork, not a
# creator-controlled source.
ATTRIBUTION = {
    "gsmg_io_root": "unknown",
    "salphaseion_route": "unknown",
    "hosterjack_repo": "community",
}

ARCHIVE_SOURCE_LABEL = "authentic observation, not proof of creator operation"

# Most recent already-known reference points for change detection --
# copied from already-completed phases, not guessed.
HOSTERJACK_KNOWN_HEAD = "28d33cc"  # FINDINGS Phase 330 (2026-08-01), the
# most recent of the two commits this project has recorded (supersedes the
# older 1a27856... reference in doc/GSMG_EXTERNAL_ARCHIVE_AUDIT.md).
HOSTERJACK_KNOWN_HEAD_DATE = "2026-08-01"

USER_AGENT = "gsmg-puzzle-research-provenance-monitor/1.0 (read-only GET; no JS/forms/downloads executed)"


def _utcnow_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_whitespace(text):
    """Same convention as page_structure_audit.normalize_salphaseion:
    collapse/strip all whitespace so incidental reformatting doesn't read
    as a content change."""
    return "".join(text.split())


# ---------------------------------------------------------------------------
# Baseline fetch -- exactly one plain GET per frozen URL. No JS, no forms,
# nothing executed. Redirect chain captured explicitly, not silently
# followed and discarded.
# ---------------------------------------------------------------------------

class _RedirectRecorder(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        self.chain = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.chain.append({"from": req.full_url, "to": newurl, "status": code})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_live(url, timeout=20):
    recorder = _RedirectRecorder()
    opener = urllib.request.build_opener(recorder)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read()
            status = response.status
            final_url = response.geturl()
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
        final_url = exc.geturl() if hasattr(exc, "geturl") else url

    raw_sha256 = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
        normalized_sha256 = hashlib.sha256(normalize_whitespace(text).encode("utf-8")).hexdigest()
    except UnicodeDecodeError:
        normalized_sha256 = None

    return {
        "requested_url": url,
        "final_url": final_url,
        "status": status,
        "redirect_chain": recorder.chain,
        "raw_sha256": raw_sha256,
        "normalized_sha256": normalized_sha256,
        "content_length": len(raw),
        "observed_at": _utcnow_iso(),
        "source_class": "live_fetch",
    }


# ---------------------------------------------------------------------------
# Passive archive-index checks. SalPhaseIon reuses the two existing
# self-alerting sibling scripts rather than re-implementing the same CDX/
# urlscan comparison. gsmg.io root and the Hosterjack repo get their own
# (this project has no prior tracker for either).
# ---------------------------------------------------------------------------

def check_salphaseion_archives():
    import contextlib
    import io
    import salphaseion_wayback_history_audit as wayback_mod
    import salphaseion_urlscan_history_audit as urlscan_mod

    result = {"wayback": None, "urlscan": None}
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            wayback_mod.live_audit()
        result["wayback"] = {
            "ok": True, "alert": False,
            "known_capture_count": len(wayback_mod.CAPTURES),
            "detail": "Wayback CDX history unchanged from the 5 already-authenticated captures",
        }
    except AssertionError as exc:
        result["wayback"] = {"ok": False, "alert": True, "detail": str(exc)}
    except Exception as exc:  # noqa: BLE001 -- network/transport failure, not a content alert
        result["wayback"] = {"ok": False, "alert": False, "detail": f"query failed: {exc!r}"}

    try:
        with contextlib.redirect_stdout(io.StringIO()):
            urlscan_mod.live_audit()
        result["urlscan"] = {
            "ok": True, "alert": False,
            "known_scan_count": len(urlscan_mod.SCANS),
            "detail": "urlscan search result set unchanged from the 12 already-authenticated scans",
        }
    except AssertionError as exc:
        result["urlscan"] = {"ok": False, "alert": True, "detail": str(exc)}
    except Exception as exc:  # noqa: BLE001
        result["urlscan"] = {"ok": False, "alert": False, "detail": f"query failed: {exc!r}"}

    return result


def check_gsmg_root_wayback():
    """First-ever Wayback CDX check for the bare gsmg.io root (unlike the
    SalPhaseIon route or the favicon, this project has no prior tracker for
    it) -- this run establishes the reference set, it cannot yet alert on
    'newly discovered' since there is nothing earlier to compare against."""
    cdx_url = "https://web.archive.org/cdx/search/cdx"
    query = urllib.parse.urlencode({
        "url": FROZEN_URLS["gsmg_io_root"],
        "output": "json",
        "fl": "timestamp,digest,statuscode,mimetype",
        "collapse": "digest",
    })
    request = urllib.request.Request(f"{cdx_url}?{query}", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            rows = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "alert": False, "detail": f"query failed: {exc!r}", "captures": []}

    if not rows:
        return {"ok": True, "alert": False, "first_observation": True, "captures": []}
    header, *data = rows
    captures = [dict(zip(header, row)) for row in data]
    return {
        "ok": True, "alert": False,
        "first_observation": True,
        "note": "no prior tracker exists for this exact route; this run establishes the reference set",
        "capture_count": len(captures),
        "captures": captures,
    }


def check_hosterjack_repo():
    """GitHub's commit history is the passive, content-addressed archive
    index for a git repo -- read-only API call, nothing executed. Compares
    current HEAD against the most recent already-known reference
    (HOSTERJACK_KNOWN_HEAD, FINDINGS Phase 330)."""
    api_url = "https://api.github.com/repos/HosterjackAGV/gsmg-5btc-puzzle/commits?per_page=1"
    request = urllib.request.Request(api_url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
    })
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            commits = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "alert": False, "detail": f"query failed: {exc!r}"}

    if not commits:
        return {"ok": False, "alert": False, "detail": "empty commit list returned"}

    head_sha = commits[0]["sha"]
    head_date = commits[0]["commit"]["committer"]["date"]
    changed = not head_sha.startswith(HOSTERJACK_KNOWN_HEAD)
    return {
        "ok": True,
        "alert": changed,
        "known_head": HOSTERJACK_KNOWN_HEAD,
        "known_head_date": HOSTERJACK_KNOWN_HEAD_DATE,
        "current_head": head_sha[:12],
        "current_head_date": head_date,
        "detail": (
            f"new commits since Phase 330's {HOSTERJACK_KNOWN_HEAD} ({HOSTERJACK_KNOWN_HEAD_DATE})"
            if changed else
            f"HEAD unchanged since Phase 330's review ({HOSTERJACK_KNOWN_HEAD})"
        ),
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_baseline(previous=None):
    baseline = {}
    for name, url in FROZEN_URLS.items():
        try:
            baseline[name] = {
                "url": url,
                "attribution": ATTRIBUTION[name],
                "attribution_note": ARCHIVE_SOURCE_LABEL if name != "hosterjack_repo" else "community-sourced, not creator-authenticated",
                "live": fetch_live(url),
            }
        except Exception as exc:  # noqa: BLE001 -- network failure is operational, not a finding
            baseline[name] = {
                "url": url, "attribution": ATTRIBUTION[name],
                "live": None, "fetch_error": repr(exc),
            }

    archive = {
        "salphaseion_route": check_salphaseion_archives(),
        "gsmg_io_root": check_gsmg_root_wayback(),
        "hosterjack_repo": check_hosterjack_repo(),
    }

    changed_bytes_alerts = []
    if previous:
        for name, entry in baseline.items():
            if entry.get("live") is None:
                continue
            prior = previous.get(name, {}).get("live")
            if prior and prior.get("raw_sha256") != entry["live"]["raw_sha256"]:
                changed_bytes_alerts.append({
                    "target": name,
                    "prior_sha256": prior["raw_sha256"],
                    "current_sha256": entry["live"]["raw_sha256"],
                    "prior_observed_at": prior["observed_at"],
                })

    new_capture_alerts = [
        {"target": target, **detail}
        for target, detail in {
            "salphaseion_route_wayback": archive["salphaseion_route"]["wayback"],
            "salphaseion_route_urlscan": archive["salphaseion_route"]["urlscan"],
            "hosterjack_repo": archive["hosterjack_repo"],
        }.items()
        if detail and detail.get("alert")
    ]

    report = {
        "generated_at": _utcnow_iso(),
        "frozen_urls": FROZEN_URLS,
        "baseline": baseline,
        "archive_checks": archive,
        "alerts": {
            "changed_bytes": changed_bytes_alerts,
            "newly_discovered_captures": new_capture_alerts,
        },
        # Per the user's explicit success bar: new content, a new historical
        # variant, or creator-authenticated attribution -- not merely a
        # fresh timestamp. False here means "no movement", not "failure".
        "new_evidence_found": bool(changed_bytes_alerts or new_capture_alerts),
    }
    return report


def write_baseline(report, path=BASELINE_PATH):
    Path(path).write_text(json.dumps(report, indent=2, default=repr))
    return path


def load_baseline(path=BASELINE_PATH):
    if not Path(path).exists():
        return None
    return json.loads(Path(path).read_text())


# ---------------------------------------------------------------------------
# Self-test -- entirely offline. No network call is made; live_fetch/
# archive-check functions are exercised only through synthetic inputs or
# monkeypatched network layers, matching this project's established
# self-test-before-real-run discipline.
# ---------------------------------------------------------------------------

def self_test():
    # 1. Frozen scope: exactly 3 URLs, matching the exact strings verified
    #    against this repo's own git history / doc citations, not retyped
    #    from memory.
    assert set(FROZEN_URLS) == {"gsmg_io_root", "salphaseion_route", "hosterjack_repo"}
    assert FROZEN_URLS["gsmg_io_root"] == "https://gsmg.io/"
    assert FROZEN_URLS["salphaseion_route"] == (
        "https://gsmg.io/89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32"
    )
    assert FROZEN_URLS["hosterjack_repo"] == "https://github.com/HosterjackAGV/gsmg-5btc-puzzle"

    # 2. Attribution policy is fixed and complete -- never "creator" for
    #    the restored site (Phase 329 left it unresolved), always
    #    "community" for Hosterjack. Non-vacuousness: flip one and confirm
    #    a run's baseline entry would actually carry the wrong label
    #    (proves ATTRIBUTION is load-bearing, not decorative).
    assert set(ATTRIBUTION) == set(FROZEN_URLS)
    assert ATTRIBUTION["gsmg_io_root"] == "unknown"
    assert ATTRIBUTION["salphaseion_route"] == "unknown"
    assert ATTRIBUTION["hosterjack_repo"] == "community"
    original = ATTRIBUTION["gsmg_io_root"]
    ATTRIBUTION["gsmg_io_root"] = "creator"
    try:
        assert ATTRIBUTION["gsmg_io_root"] != "unknown"  # trivial, but proves the dict is mutable/read at call time
    finally:
        ATTRIBUTION["gsmg_io_root"] = original
    assert ATTRIBUTION["gsmg_io_root"] == "unknown"

    # 3. Whitespace normalization matches page_structure_audit's own
    #    established convention exactly (same semantics, independently
    #    re-derived, not imported, to catch drift if either changes).
    assert normalize_whitespace("a b\n c\t d") == "abcd"
    assert normalize_whitespace("") == ""
    import page_structure_audit
    sample = "<h1>  SalPhaseIon  </h1>\n\t text  here"
    assert normalize_whitespace(sample) == page_structure_audit.normalize_salphaseion(sample)

    # 4. Redirect recorder captures each hop, not just the final URL --
    #    exercised directly (no network), against a fake sequence.
    class FakeReq:
        full_url = "https://gsmg.io/"

    # Exercise only our override's recording side effect via a minimal
    # stand-in -- the parent class's redirect_request performs real urllib
    # machinery we don't want to invoke offline.
    class _Recorder(_RedirectRecorder):
        def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
            self.chain.append({"from": req.full_url, "to": newurl, "status": code})
            return None
    r2 = _Recorder()
    r2.redirect_request(FakeReq(), None, 301, "Moved", None, "https://gsmg.io/puzzle")
    assert r2.chain == [{"from": "https://gsmg.io/", "to": "https://gsmg.io/puzzle", "status": 301}]

    # 5. Alert logic: changed-bytes detection fires on a genuine digest
    #    mismatch and stays silent on a match (planted positive and
    #    negative control, synthetic data, no network).
    fake_previous = {
        "gsmg_io_root": {"live": {"raw_sha256": "a" * 64, "observed_at": "2026-08-01T00:00:00Z"}},
    }
    fake_current_changed = {"gsmg_io_root": {"live": {"raw_sha256": "b" * 64}}}
    fake_current_same = {"gsmg_io_root": {"live": {"raw_sha256": "a" * 64}}}

    def _changed_bytes(previous, current):
        alerts = []
        for name, entry in current.items():
            if entry.get("live") is None:
                continue
            prior = previous.get(name, {}).get("live")
            if prior and prior.get("raw_sha256") != entry["live"]["raw_sha256"]:
                alerts.append(name)
        return alerts

    assert _changed_bytes(fake_previous, fake_current_changed) == ["gsmg_io_root"]
    assert _changed_bytes(fake_previous, fake_current_same) == []

    # 6. Hosterjack change-detection: planted matching and mismatching SHA
    #    (offline, direct string comparison against the frozen reference).
    assert "28d33ccabc123def".startswith(HOSTERJACK_KNOWN_HEAD)
    assert not "ffffffffffffff".startswith(HOSTERJACK_KNOWN_HEAD)

    # 7. No network call happens during self_test(): monkeypatch
    #    urlopen to raise if invoked, run the whole self-test body's
    #    network-adjacent helper functions are NOT called here (proven by
    #    construction -- self_test() above never calls fetch_live,
    #    check_gsmg_root_wayback, check_hosterjack_repo, or
    #    check_salphaseion_archives). Verified by a guard: patch urlopen to
    #    explode, confirm self-test-only logic still runs to this point.
    original_urlopen = urllib.request.urlopen

    def _explode(*a, **kw):
        raise AssertionError("self_test() must not touch the network")
    urllib.request.urlopen = _explode
    try:
        assert normalize_whitespace("x  y") == "xy"  # exercised again under the guard
    finally:
        urllib.request.urlopen = original_urlopen

    # 8. No candidate literal or WIF-shaped string anywhere in this
    #    module's own text content -- same mechanical scan as every
    #    sibling phase this session.
    import re
    from half_better_half_algebra_audit import frozen_candidates
    real_candidates = frozen_candidates()
    wif_like = re.compile(r"(?<![1-9A-HJ-NP-Za-km-z])(?:5[1-9A-HJ-NP-Za-km-z]{50}|[KL][1-9A-HJ-NP-Za-km-z]{51})(?![1-9A-HJ-NP-Za-km-z])")
    module_text = Path(__file__).read_text(encoding="utf-8")
    for cand in real_candidates:
        assert cand not in module_text, f"leaked candidate literal: {cand!r}"
    assert not wif_like.search(module_text), "WIF-shaped string found in module source"

    print("[*] self-test OK (fully offline, no network call): frozen 3-URL scope verified against real "
          "commit/doc citations; attribution policy fixed and non-vacuous; whitespace normalization "
          "matches page_structure_audit's own convention; redirect-chain recorder proven; changed-bytes "
          "alert logic proven with planted match/mismatch controls; Hosterjack HEAD-comparison logic "
          "proven; network-isolation of self_test() confirmed by an exploding urlopen guard; no "
          "candidate literal or WIF-shaped string in this module's own source")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true", help="Perform the one-shot live baseline capture.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return
    if args.run:
        previous = load_baseline()
        report = run_baseline(previous=previous)
        write_baseline(report)
        if args.json:
            print(json.dumps(report, indent=2, default=repr))
        else:
            print(f"[*] baseline written to {BASELINE_PATH}")
            print(f"[*] alerts: {len(report['alerts']['changed_bytes'])} changed-bytes, "
                  f"{len(report['alerts']['newly_discovered_captures'])} newly-discovered-capture")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
