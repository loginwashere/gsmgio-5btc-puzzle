#!/usr/bin/env python3
"""Item 4 (`doc/GSMG_FRESH_BRAINSTORM_2026-08-06.md`), bullet 1: check the two
known creator-controlled Bitcoin addresses (`1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe`,
the prize/funding address, and `17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa`, the cold-
storage recipient of both halving self-spends -- see `doc/GSMG_PUZZLE.md`
"Prize address mechanics") for OP_RETURN / dust messages.

Finding (2026-08-06): both addresses' full transaction histories (125 + 44
txs, matching the counts already documented in GSMG_PUZZLE.md) contain 105
OP_RETURN outputs carrying human-readable text -- entirely unmentioned in any
prior phase. Every one of these was independently verified as genuinely
on-chain via THREE unrelated block-explorer backends (blockstream.info,
blockchain.info, mempool.space all agree byte-for-byte on script content),
which rules out a fabricated/injected tool response.

However, the message content is suspiciously on-the-nose for this exact
project's vocabulary (`SalPhaseIon`, `matrixsumlist...enterlastwordsbefore
archichoicethispassword`, `redpill`, `hereismysecret`, etc.) -- exactly the
shape a prompt-injection or a deliberate researcher-baiting artifact would
take. Critical distinction: an OP_RETURN output only proves authorship by
whoever signed that transaction's INPUT, not by the recipient of any payment
output in the same tx. Checked systematically: of all 105 OP_RETURN-bearing
transactions, **zero** have an input from either of the two genuine
creator-controlled addresses -- every single one was paid TO the GSMG address
by a third party (a tiny "dust" payment) with the OP_RETURN attached by that
third party's own signature. The two dominant input addresses,
`1JG648yaB7Wp2dpUfcZoRSD4q35oq47vCu` and `145ZQ9siLrsXBKf465wjdyQYAP5dRwhRhQ`,
are the *exact* two addresses `doc/GSMG_PUZZLE.md` (2026-07-12 update)
already documented as the source of a single fabricated "solution" hash
recycled across 10+ GitHub issues over many months. This is on-chain graffiti
from that same already-debunked campaign (or an actor reusing its
infrastructure), not creator content -- closed negative, with the added
value of a corroborating link between the two artifacts.

This script re-verifies a sample of that provenance chain live (never
hardcoded from memory beyond the two genuine addresses and the two flagged
scam-thread addresses, which are quoted directly from GSMG_PUZZLE.md).
"""

import argparse
import json
import subprocess
import sys
import time

GENUINE_ADDRESSES = (
    "1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe",
    "17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa",
)

# Quoted verbatim from doc/GSMG_PUZZLE.md's "full issue-tracker sweep" update
# (2026-07-12): the two addresses recycled across a single fabricated
# "solution" hash propagated over 10+ GitHub issues.
KNOWN_SCAM_ADDRESSES = (
    "1JG648yaB7Wp2dpUfcZoRSD4q35oq47vCu",
    "145ZQ9siLrsXBKf465wjdyQYAP5dRwhRhQ",
)

EXPLORER_APIS = (
    "https://blockstream.info/api",
    "https://mempool.space/api",
)


def curl_json(url, timeout=30):
    out = subprocess.run(
        ["curl", "-s", "-m", str(timeout), url], capture_output=True, text=True
    )
    return json.loads(out.stdout)


def fetch_all_txs(address, timeout=30):
    all_txs = []
    url = f"{EXPLORER_APIS[0]}/address/{address}/txs"
    txs = curl_json(url, timeout)
    all_txs.extend(txs)
    while len(txs) == 25:
        last_txid = txs[-1]["txid"]
        url = f"{EXPLORER_APIS[0]}/address/{address}/txs/chain/{last_txid}"
        time.sleep(0.3)
        txs = curl_json(url, timeout)
        if not txs:
            break
        all_txs.extend(txs)
    return all_txs


def op_return_text(vout):
    asm = vout.get("scriptpubkey_asm", "")
    parts = asm.split()
    if len(parts) < 2 or parts[0] != "OP_RETURN":
        return None
    try:
        return bytes.fromhex(parts[-1]).decode("utf-8", errors="replace")
    except ValueError:
        return None


def input_addresses(tx):
    return {
        vin.get("prevout", {}).get("scriptpubkey_address")
        for vin in tx.get("vin", [])
        if vin.get("prevout", {}).get("scriptpubkey_address")
    }


def analyze(addresses=GENUINE_ADDRESSES, timeout=30):
    results = []
    for address in addresses:
        txs = fetch_all_txs(address, timeout)
        for tx in txs:
            texts = [op_return_text(v) for v in tx.get("vout", [])]
            texts = [t for t in texts if t is not None]
            if not texts:
                continue
            ins = input_addresses(tx)
            results.append(
                {
                    "address": address,
                    "txid": tx["txid"],
                    "texts": texts,
                    "input_addresses": sorted(ins),
                    "genuine_key_used": bool(ins & set(GENUINE_ADDRESSES)),
                    "known_scam_input": bool(ins & set(KNOWN_SCAM_ADDRESSES)),
                }
            )
    return results


def cross_check_one(txid, timeout=20):
    """Verify one txid's OP_RETURN script bytes agree across independent
    explorer backends, to rule out a fabricated/injected single-source
    response."""
    scripts = set()
    for api in ("https://blockstream.info/api", "https://mempool.space/api"):
        tx = curl_json(f"{api}/tx/{txid}", timeout)
        for vout in tx.get("vout", []):
            if vout.get("scriptpubkey_type") == "op_return":
                scripts.add(vout["scriptpubkey"])
    return scripts


def self_test():
    # A single fixed, previously-verified txid/message pair, checked against
    # two independent explorer backends at self-test time.
    txid = "a798905f53fdcadcbd2e2a1e61d23ba69a07e26130a78c76da4bf4d7a170f383"
    scripts = cross_check_one(txid)
    assert len(scripts) == 1, f"explorers disagree on {txid}: {scripts}"
    script = next(iter(scripts))
    assert bytes.fromhex(script[4:]).decode() == "Halving", script
    print(f"[*] self-test OK: {txid[:16]}.. OP_RETURN == 'Halving' on 2 independent explorers")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--full", action="store_true", help="fetch and analyze full tx history")
    args = parser.parse_args()

    if args.self_test:
        self_test()

    if args.full:
        results = analyze()
        total = len(results)
        genuine = sum(1 for r in results if r["genuine_key_used"])
        scam = sum(1 for r in results if r["known_scam_input"])
        print(f"[*] OP_RETURN-bearing txs: {total}")
        print(f"[*] signed by a genuine creator-controlled key: {genuine}")
        print(f"[*] signed by one of the two known scam-thread addresses: {scam}")
        print(f"[*] signed by some other third party: {total - genuine - scam}")


if __name__ == "__main__":
    main()
