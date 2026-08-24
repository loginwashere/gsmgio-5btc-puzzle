#!/usr/bin/env python3
"""P32 Family 2: trace the two authenticated GSMG Bitcoin addresses.

The family was pre-registered in
``doc/Brainstorms/2026-08-14 - P32 New Attack Surfaces Beyond Text
Recombination.md``.  This implementation deliberately stops after:

* complete transaction histories for the two seed addresses;
* transactions in which a seed address actually signs an input;
* direct common-input candidates on those transactions;
* every output of those transactions and its one-hop outspend; and
* exact raw bytes for the creator-signed transactions.

Blockstream provides the complete enumeration; BlockCypher independently
confirms each full-history count; mempool.space's available newest subset must
match Blockstream semantically; and all three sources must return identical raw
hex for every creator-signed transaction.  The output cache is the bounded
input intended for P32 Family 9; it is not a wallet-ownership claim.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import time
from pathlib import Path


API_BASES = {
    "blockstream": "https://blockstream.info/api",
    "mempool": "https://mempool.space/api",
}
BLOCKCYPHER_BASE = "https://api.blockcypher.com/v1/btc/main"

PRIZE_ADDRESS = "1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe"
HALVING_ADDRESS = "17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa"
SEED_ADDRESSES = (PRIZE_ADDRESS, HALVING_ADDRESS)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT = REPO_ROOT / "doc/evidence/GSMG_P32_FAMILY2_TRANSACTION_GRAPH.json"
DEFAULT_CACHE = REPO_ROOT / "doc/evidence/GSMG_P32_FAMILY2_SIGNED_TRANSACTION_CACHE.json"

# These two spends and their output roles were already recorded in
# doc/GSMG_PUZZLE.md and independently re-derived in Phase 331.  They are a
# regression control, not a newly selected target.
KNOWN_SELF_SPENDS = {
    "2aa9a4a90be819d5122d70c993280785a0508f163521e7b38cebb4db0b071b13": {
        "block_height": 630001,
        "outputs": {
            (PRIZE_ADDRESS, 249_815_966),
            (HALVING_ADDRESS, 250_000_000),
        },
    },
    "88cdb3cdca12b471551b1b26188508a14ca5fd8a415223ffb7c190381c9b9df3": {
        "block_height": 840725,
        "outputs": {
            (PRIZE_ADDRESS, 125_324_300),
            (HALVING_ADDRESS, 125_000_000),
        },
    },
}


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256_json(value) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def legacy_txid(raw_hex: str) -> str:
    raw = bytes.fromhex(raw_hex)
    if raw[4:6] == b"\x00\x01":
        raise ValueError("witness transaction requires stripped serialization")
    return hashlib.sha256(hashlib.sha256(raw).digest()).digest()[::-1].hex()


def curl_text(url: str, timeout: int = 45) -> str:
    completed = subprocess.run(
        [
            "curl",
            "-fsS",
            "-L",
            "--retry",
            "3",
            "--retry-delay",
            "1",
            "--max-time",
            str(timeout),
            url,
        ],
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise RuntimeError(
            f"curl failed ({completed.returncode}) for {url}: "
            f"{completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def curl_json(url: str, timeout: int = 45):
    return json.loads(curl_text(url, timeout))


def fetch_history(api_base: str, address: str, delay: float = 0.15):
    """Return an Esplora address history, de-duplicated by txid."""
    records = []
    page = curl_json(f"{api_base}/address/{address}/txs")
    records.extend(page)
    while len(page) == 25:
        last_txid = page[-1]["txid"]
        time.sleep(delay)
        page = curl_json(f"{api_base}/address/{address}/txs/chain/{last_txid}")
        if not page:
            break
        records.extend(page)
    by_txid = {}
    for record in records:
        by_txid.setdefault(record["txid"], record)
    return by_txid


def fetch_blockcypher_count(address: str):
    """Obtain an independent full-history transaction count cheaply."""
    row = curl_json(f"{BLOCKCYPHER_BASE}/addrs/{address}?limit=1")
    if row.get("address") != address:
        raise AssertionError(f"BlockCypher returned the wrong address for {address}")
    return int(row["n_tx"])


def normalize_status(status):
    return {
        "confirmed": bool(status.get("confirmed")),
        "block_height": status.get("block_height"),
        "block_hash": status.get("block_hash"),
        "block_time": status.get("block_time"),
    }


def normalize_tx(tx):
    """Keep consensus/graph fields common to both Esplora deployments."""
    return {
        "txid": tx["txid"],
        "version": tx.get("version"),
        "locktime": tx.get("locktime"),
        "size": tx.get("size"),
        "weight": tx.get("weight"),
        "fee": tx.get("fee"),
        "status": normalize_status(tx.get("status", {})),
        "vin": [
            {
                "txid": vin.get("txid"),
                "vout": vin.get("vout"),
                "is_coinbase": bool(vin.get("is_coinbase")),
                "sequence": vin.get("sequence"),
                "prevout_address": (vin.get("prevout") or {}).get(
                    "scriptpubkey_address"
                ),
                "prevout_type": (vin.get("prevout") or {}).get(
                    "scriptpubkey_type"
                ),
                "prevout_value": (vin.get("prevout") or {}).get("value"),
            }
            for vin in tx.get("vin", [])
        ],
        "vout": [
            {
                "address": vout.get("scriptpubkey_address"),
                "type": vout.get("scriptpubkey_type"),
                "value": vout.get("value"),
                "scriptpubkey": vout.get("scriptpubkey"),
            }
            for vout in tx.get("vout", [])
        ],
    }


def input_addresses(tx):
    return {
        vin["prevout_address"]
        for vin in normalize_tx(tx)["vin"]
        if vin["prevout_address"]
    }


def history_digest(history):
    normalized = [normalize_tx(history[txid]) for txid in sorted(history)]
    return sha256_json(normalized)


def normalize_outspends(rows):
    return [
        {
            "spent": bool(row.get("spent")),
            "txid": row.get("txid"),
            "vin": row.get("vin"),
            "status": normalize_status(row.get("status", {})),
        }
        for row in rows
    ]


def fetch_tx_pair(txid: str):
    records = {
        name: curl_json(f"{base}/tx/{txid}")
        for name, base in API_BASES.items()
    }
    normalized = {name: normalize_tx(tx) for name, tx in records.items()}
    if normalized["blockstream"] != normalized["mempool"]:
        raise AssertionError(f"explorer transaction JSON disagrees for {txid}")
    return records["blockstream"]


def fetch_raw_pair(txid: str):
    raw = {
        name: curl_text(f"{base}/tx/{txid}/hex")
        for name, base in API_BASES.items()
    }
    raw["blockcypher"] = curl_json(
        f"{BLOCKCYPHER_BASE}/txs/{txid}?includeHex=true"
    )["hex"]
    if len(set(raw.values())) != 1:
        raise AssertionError(f"three-explorer raw hex disagrees for {txid}")
    bytes.fromhex(raw["blockstream"])
    return raw["blockstream"]


def fetch_outspends_pair(txid: str):
    rows = {
        name: curl_json(f"{base}/tx/{txid}/outspends")
        for name, base in API_BASES.items()
    }
    normalized = {name: normalize_outspends(value) for name, value in rows.items()}
    if normalized["blockstream"] != normalized["mempool"]:
        raise AssertionError(f"explorer outspends disagree for {txid}")
    return normalized["blockstream"]


def expected_self_spend_check(tx):
    expected = KNOWN_SELF_SPENDS.get(tx["txid"])
    if expected is None:
        return False
    normalized = normalize_tx(tx)
    outputs = {
        (row["address"], row["value"])
        for row in normalized["vout"]
        if row["address"]
    }
    return (
        normalized["status"]["block_height"] == expected["block_height"]
        and outputs == expected["outputs"]
    )


def audit(delay: float = 0.15):
    observed_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    histories = {name: {} for name in API_BASES}
    for source_name, api_base in API_BASES.items():
        for address in SEED_ADDRESSES:
            histories[source_name][address] = fetch_history(api_base, address, delay)

    blockcypher_counts = {
        address: fetch_blockcypher_count(address)
        for address in SEED_ADDRESSES
    }

    address_history = {}
    for address in SEED_ADDRESSES:
        esplora_sets = {
            name: set(histories[name][address])
            for name in API_BASES
        }
        if len(esplora_sets["blockstream"]) != blockcypher_counts[address]:
            raise AssertionError(
                f"full history count disagrees between Blockstream and "
                f"BlockCypher for {address}"
            )
        # mempool.space currently caps this address-history walk at the newest
        # 50 transactions.  Treat it as an authenticated subset, never as a
        # second full-history source.
        if not esplora_sets["mempool"] <= esplora_sets["blockstream"]:
            raise AssertionError(
                f"mempool.space returned txids absent from the full history for {address}"
            )
        mempool_subset = sorted(esplora_sets["mempool"])
        blockstream_subset_digest = sha256_json(
            [
                normalize_tx(histories["blockstream"][address][txid])
                for txid in mempool_subset
            ]
        )
        mempool_subset_digest = history_digest(histories["mempool"][address])
        if blockstream_subset_digest != mempool_subset_digest:
            raise AssertionError(
                f"normalized newest-history subset disagrees for {address}"
            )
        address_history[address] = {
            "transaction_count": len(esplora_sets["blockstream"]),
            "full_history_sources": {
                "blockstream": len(esplora_sets["blockstream"]),
                "blockcypher_count": blockcypher_counts[address],
            },
            "mempool_authenticated_subset_count": len(esplora_sets["mempool"]),
            "transaction_ids_sha256": sha256_json(sorted(esplora_sets["blockstream"])),
            "normalized_history_sha256": history_digest(
                histories["blockstream"][address]
            ),
            "mempool_subset_normalized_sha256": mempool_subset_digest,
        }

    union = {}
    for address in SEED_ADDRESSES:
        union.update(histories["blockstream"][address])

    seed_set = set(SEED_ADDRESSES)
    signed = {
        txid: tx
        for txid, tx in union.items()
        if input_addresses(tx) & seed_set
    }

    signed_rows = []
    raw_cache_rows = []
    coinput_candidates = set()
    new_output_addresses = set()
    one_hop_spender_ids = set()

    for txid in sorted(signed):
        tx = fetch_tx_pair(txid)
        raw_hex = fetch_raw_pair(txid)
        outspends = fetch_outspends_pair(txid)
        normalized = normalize_tx(tx)
        inputs = {row["prevout_address"] for row in normalized["vin"]}
        inputs.discard(None)
        coinput_candidates.update(inputs - seed_set)

        outputs = []
        for index, (vout, outspend) in enumerate(zip(normalized["vout"], outspends)):
            address = vout["address"]
            if address and address not in seed_set:
                new_output_addresses.add(address)
            if outspend["spent"] and outspend["txid"]:
                one_hop_spender_ids.add(outspend["txid"])
            outputs.append(
                {
                    "vout": index,
                    "address": address,
                    "type": vout["type"],
                    "value_sats": vout["value"],
                    "spent": outspend["spent"],
                    "spending_txid": outspend["txid"],
                    "spending_vin": outspend["vin"],
                }
            )

        input_value = sum(row["prevout_value"] or 0 for row in normalized["vin"])
        output_value = sum(row["value"] or 0 for row in normalized["vout"])
        signed_rows.append(
            {
                "txid": txid,
                "block_height": normalized["status"]["block_height"],
                "block_time": normalized["status"]["block_time"],
                "input_count": len(normalized["vin"]),
                "input_addresses": sorted(inputs),
                "input_value_sats": input_value,
                "output_value_sats": output_value,
                "fee_sats": input_value - output_value,
                "outputs": outputs,
                "matches_preexisting_self_spend_record": expected_self_spend_check(tx),
                "raw_byte_length": len(bytes.fromhex(raw_hex)),
                "raw_sha256": hashlib.sha256(bytes.fromhex(raw_hex)).hexdigest(),
            }
        )
        raw_cache_rows.append(
            {
                "txid": txid,
                "raw_hex": raw_hex,
                "raw_sha256": hashlib.sha256(bytes.fromhex(raw_hex)).hexdigest(),
                "normalized_transaction": normalized,
            }
        )

    one_hop_spenders = []
    for txid in sorted(one_hop_spender_ids):
        spender = fetch_tx_pair(txid)
        normalized = normalize_tx(spender)
        one_hop_spenders.append(
            {
                "txid": txid,
                "input_addresses": sorted(input_addresses(spender)),
                "output_addresses": sorted(
                    {
                        row["address"]
                        for row in normalized["vout"]
                        if row["address"]
                    }
                ),
                "seed_signed": bool(input_addresses(spender) & seed_set),
            }
        )

    report = {
        "schema_version": 1,
        "observed_at_utc": observed_at,
        "source_apis": API_BASES,
        "independent_history_count_api": BLOCKCYPHER_BASE,
        "seed_addresses": list(SEED_ADDRESSES),
        "cross_source_agreement": True,
        "cross_source_contract": (
            "Blockstream's full enumeration count agrees with BlockCypher; "
            "mempool.space's available newest subset agrees semantically; "
            "all creator-signed raw bytes agree across all three"
        ),
        "address_history": address_history,
        "union_transaction_count": len(union),
        "shared_transaction_count": sum(
            1
            for txid in histories["blockstream"][PRIZE_ADDRESS]
            if txid in histories["blockstream"][HALVING_ADDRESS]
        ),
        "creator_signed_transaction_count": len(signed_rows),
        "creator_signed_transactions": signed_rows,
        "direct_common_input_candidate_addresses": sorted(coinput_candidates),
        "new_output_addresses": sorted(new_output_addresses),
        "one_hop_spenders": one_hop_spenders,
        "all_creator_signed_transactions_match_preexisting_record": bool(signed_rows)
        and all(row["matches_preexisting_self_spend_record"] for row in signed_rows),
        "new_authenticated_address_found": bool(
            coinput_candidates or new_output_addresses
        ),
        "verdict": (
            "new-address-candidate"
            if coinput_candidates or new_output_addresses
            else "closed-negative-no-new-address-or-route"
        ),
    }
    cache = {
        "schema_version": 1,
        "observed_at_utc": observed_at,
        "scope": "transactions in which either authenticated seed address signs an input",
        "source_apis": API_BASES,
        "independent_raw_transaction_api": BLOCKCYPHER_BASE,
        "seed_addresses": list(SEED_ADDRESSES),
        "transactions": raw_cache_rows,
    }
    return report, cache


def self_test():
    sample = {
        "txid": "00" * 32,
        "version": 1,
        "locktime": 0,
        "size": 100,
        "weight": 400,
        "fee": 10,
        "status": {"confirmed": True, "block_height": 1},
        "vin": [
            {
                "txid": "11" * 32,
                "vout": 0,
                "sequence": 0xFFFFFFFF,
                "prevout": {
                    "scriptpubkey_address": PRIZE_ADDRESS,
                    "scriptpubkey_type": "p2pkh",
                    "value": 20,
                },
            }
        ],
        "vout": [
            {
                "scriptpubkey_address": HALVING_ADDRESS,
                "scriptpubkey_type": "p2pkh",
                "scriptpubkey": "76a914" + "22" * 20 + "88ac",
                "value": 10,
            }
        ],
    }
    normalized = normalize_tx(sample)
    assert input_addresses(sample) == {PRIZE_ADDRESS}
    assert normalized["vin"][0]["prevout_value"] == 20
    assert normalized["vout"][0]["address"] == HALVING_ADDRESS
    assert normalize_outspends([{"spent": False}]) == [
        {
            "spent": False,
            "txid": None,
            "vin": None,
            "status": normalize_status({}),
        }
    ]
    assert sha256_json(normalized) == sha256_json(json.loads(canonical_json(normalized)))
    if DEFAULT_REPORT.exists() and DEFAULT_CACHE.exists():
        report = json.loads(DEFAULT_REPORT.read_text())
        cache = json.loads(DEFAULT_CACHE.read_text())
        validate_artifacts(report, cache)
    print(
        "[*] self-test OK: normalization, address extraction, canonical digest, "
        "and pinned artifacts"
    )


def validate_artifacts(report, cache):
    assert report["cross_source_agreement"] is True
    assert report["creator_signed_transaction_count"] == 2
    assert report["union_transaction_count"] == 164
    assert report["shared_transaction_count"] == 5
    assert report["direct_common_input_candidate_addresses"] == []
    assert report["new_output_addresses"] == []
    assert report["new_authenticated_address_found"] is False
    assert report["verdict"] == "closed-negative-no-new-address-or-route"

    report_rows = {
        row["txid"]: row for row in report["creator_signed_transactions"]
    }
    cache_rows = {row["txid"]: row for row in cache["transactions"]}
    assert set(report_rows) == set(cache_rows) == set(KNOWN_SELF_SPENDS)
    for txid, row in cache_rows.items():
        raw = bytes.fromhex(row["raw_hex"])
        digest = hashlib.sha256(raw).hexdigest()
        assert legacy_txid(row["raw_hex"]) == txid
        assert row["raw_sha256"] == digest
        assert report_rows[txid]["raw_sha256"] == digest
        assert report_rows[txid]["raw_byte_length"] == len(raw)
        assert report_rows[txid]["matches_preexisting_self_spend_record"] is True
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--delay", type=float, default=0.15)
    args = parser.parse_args()

    if args.self_test:
        self_test()
    if not args.run:
        return

    if args.report is None or args.cache is None:
        parser.error("--run requires --report and --cache")
    report, cache = audit(args.delay)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.cache.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.cache.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")
    print(
        "[*] histories: "
        + ", ".join(
            f"{address}={row['transaction_count']}"
            for address, row in report["address_history"].items()
        )
    )
    print(
        f"[*] union={report['union_transaction_count']}; "
        f"shared={report['shared_transaction_count']}; "
        f"creator-signed={report['creator_signed_transaction_count']}"
    )
    print(
        f"[*] co-input candidates={len(report['direct_common_input_candidate_addresses'])}; "
        f"new outputs={len(report['new_output_addresses'])}; "
        f"verdict={report['verdict']}"
    )


if __name__ == "__main__":
    main()
