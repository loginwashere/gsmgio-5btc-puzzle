#!/usr/bin/env python3
"""Reproduce the bounded urlscan history check for the SalPhaseIon route.

The frozen result table is an offline integrity record. ``--live`` performs
one exact urlscan search and fetches exactly the 12 result pages returned by
that search.  It does not expand to related domains, URLs, or searches.
"""

import argparse
import json
import re
import urllib.parse
import urllib.request

from salphaseion_wayback_history_audit import CAPTURES, ROUTE

SEARCH_URL = "https://urlscan.io/api/v1/search/"
RESULT_URL = "https://urlscan.io/result/{uuid}/"
ROUTE_HASH = ROUTE.rsplit("/", 1)[-1]

# date, uuid, HTTP status, main-document resource SHA-256.  The final scan is
# a 503 response and therefore deliberately has no puzzle-page hash.
SCANS = (
    ("2023-05-31T02:49:16.549Z", "041d4223-28bb-4ca1-99ba-505701b83e6e", 200, "18a8369df1364911d5e94fcac341ef85480ff194f4500f509fbed34f19e6308b"),
    ("2024-03-04T20:47:37.705Z", "88a38141-7d6d-4caf-baee-312d9f53d7f7", 200, "ed6c395890553a2ef3e156f91111ef0ab503951c631717cb60ab1f72858459af"),
    ("2024-04-12T01:45:13.506Z", "5bdb6b24-62ef-494a-9e82-2db287db7060", 200, "ed6c395890553a2ef3e156f91111ef0ab503951c631717cb60ab1f72858459af"),
    ("2024-04-16T13:00:06.015Z", "bd8b8370-1bd2-41d5-975a-b97f16997305", 200, "ed6c395890553a2ef3e156f91111ef0ab503951c631717cb60ab1f72858459af"),
    ("2024-12-04T06:29:00.261Z", "0a289fcc-df1f-4cc9-aa29-e93c266fe3b3", 200, "0eeb42e361a2781846ce16d2fdadd1a879793d969aa624c5fa43552347d6c4d0"),
    ("2025-02-28T23:37:02.425Z", "0f379d8c-ab22-48d8-954b-3aa487943b09", 200, "0eeb42e361a2781846ce16d2fdadd1a879793d969aa624c5fa43552347d6c4d0"),
    ("2025-06-06T04:20:41.269Z", "01974378-2485-7501-989d-7a58d48d85f0", 200, "0eeb42e361a2781846ce16d2fdadd1a879793d969aa624c5fa43552347d6c4d0"),
    ("2025-08-07T14:19:14.283Z", "019884e6-67a1-739d-b94b-d554fe09f7ea", 200, "0eeb42e361a2781846ce16d2fdadd1a879793d969aa624c5fa43552347d6c4d0"),
    ("2025-09-08T01:09:32.850Z", "019926de-eddc-7081-97d9-1abcdba01481", 200, "0eeb42e361a2781846ce16d2fdadd1a879793d969aa624c5fa43552347d6c4d0"),
    ("2025-09-24T08:21:26.516Z", "01997ad0-16c5-7138-9cea-4a6617244826", 200, "0eeb42e361a2781846ce16d2fdadd1a879793d969aa624c5fa43552347d6c4d0"),
    ("2026-02-11T02:19:59.088Z", "019c4a7f-7648-7164-aa60-2efcaa0ba109", 200, "0eeb42e361a2781846ce16d2fdadd1a879793d969aa624c5fa43552347d6c4d0"),
    ("2026-05-05T21:05:33.121Z", "019df9f5-c18c-70dc-ac5f-05150fd41a82", 503, None),
)

RESOURCE_HASH_RE = re.compile(r"Resource Hash</b></dt><dd><tt><a href=\"/search/#hash:([a-f0-9]{64})\"")


def request_bytes(url):
    request = urllib.request.Request(url, headers={"User-Agent": "GSMG provenance audit"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def expected_page_hashes():
    return {capture["sha256"] for capture in CAPTURES}


def self_test():
    successful = [scan for scan in SCANS if scan[2] == 200]
    assert len(SCANS) == 12
    assert len(successful) == 11
    assert len({scan[1] for scan in SCANS}) == 12
    assert all(scan[3] in expected_page_hashes() for scan in successful)
    assert {scan[3] for scan in successful} == {
        CAPTURES[0]["sha256"], CAPTURES[1]["sha256"], CAPTURES[2]["sha256"]
    }
    assert SCANS[0][0] < "2023-06-01T22:27:52"
    assert SCANS[-1][2:] == (503, None)
    print("[*] self-test OK: 11 successful scans map to 3 authenticated Wayback variants; 1 scan is HTTP 503")


def live_audit():
    query = urllib.parse.urlencode({"q": f'page.url:"{ROUTE_HASH}"', "size": 100})
    results = json.loads(request_bytes(f"{SEARCH_URL}?{query}"))["results"]
    observed = {(row["task"]["time"], row["_id"], int(row["page"]["status"] or 0)) for row in results}
    expected = {(date, uuid, status) for date, uuid, status, _ in SCANS}
    if observed != expected:
        raise AssertionError(f"urlscan search result set changed: {observed!r}")

    for _, uuid, status, expected_hash in SCANS:
        html = request_bytes(RESULT_URL.format(uuid=uuid)).decode("utf-8")
        hashes = set(RESOURCE_HASH_RE.findall(html))
        if status == 200 and expected_hash not in hashes:
            raise AssertionError(f"{uuid}: expected main-document hash {expected_hash} absent")
    print("[*] live audit OK: exact 12-result set and all 11 puzzle-page resource hashes verified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.self_test or not args.live:
        self_test()
    if args.live:
        live_audit()


if __name__ == "__main__":
    main()
