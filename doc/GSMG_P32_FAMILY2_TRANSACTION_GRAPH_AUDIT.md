---
type: audit
phase: 383
date: 2026-08-24
status: closed
result: negative
disposition: provenance-only
evidence_level: authenticated-artifact
topics:
  - p32
  - bitcoin
  - transaction-graph
  - provenance
script: tools/gsmg/p32_transaction_graph_audit.py
---

# GSMG P32 Family 2 Transaction-Graph Audit

## Question

Does following the complete transaction histories of the two authenticated
GSMG addresses reveal another creator-controlled address, output route, or
on-chain fact not already recorded by the project?

This executes P32 Family 2 from the Brainstorm Backlog Ledger. It is separate
from Phase 156's OP_RETURN audit: Phase 156 classified third-party messages
sent *to* the known addresses, whereas this phase considers only transactions
where a known address actually signs an input.

## Frozen scope

The two seed addresses are:

```text
prize/funding: 1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe
halving store: 17ucy1K9ZUAaoY6JVtM932W9jUp5LXfyHa
```

The graph expansion is deliberately bounded to:

1. both seeds' complete transaction histories;
2. transactions containing a seed address in an input prevout;
3. direct co-input addresses on those transactions;
4. every output and its immediate outspend; and
5. exact raw bytes for the creator-signed transactions.

There is no recursive clustering, thematic address scoring, identity
attribution, private-key operation, or fund movement.

## Source authentication

Blockstream supplied the complete address histories. BlockCypher independently
confirmed the two full-history transaction counts. Mempool.space returned all
44 transactions for the halving address and its available newest 50-transaction
subset for the prize address; every normalized transaction in those subsets
matched Blockstream.

For each creator-signed transaction, raw transaction hex was required to agree
byte-for-byte across Blockstream, mempool.space, and BlockCypher. Both passed.
The initial implementation attempted to require two complete paginated history
sets, but mempool.space stops this address-history walk at 50 and
blockchain.info rate-limited repeated pagination. The final report states the
narrower source contract exactly instead of misrepresenting either provider as
a complete second enumeration.

## Results

| Measure | Result |
|---|---:|
| Prize-address transactions | 125 |
| Halving-address transactions | 44 |
| Unique union | 164 |
| Transactions present in both histories | 5 |
| Creator-signed transactions | 2 |
| Direct additional co-input addresses | 0 |
| Outputs to previously unknown addresses | 0 |
| New authenticated route or address | 0 |

Only the already-documented self-spends use an authenticated seed key:

| Date/block | Transaction | Inputs | Outputs | Fee | Raw bytes / SHA-256 |
|---|---|---|---|---:|---|
| 2020-05-11 / 630001 | `2aa9a4a9...071b13` | three prize-address UTXOs | `2.49815966 BTC` back to the prize address; `2.5 BTC` to the halving address | 185,400 sat | 617 / `6865119e...df9a04` |
| 2024-04-24 / 840725 | `88cdb3cd...9b9df3` | three prize-address UTXOs | `1.25 BTC` to the halving address; `1.253243 BTC` back to the prize address | 27,832 sat | 615 / `b1653abd...06352` |

Every input address in both spends is the prize address itself. The 2020 change
output is spent by the 2024 transaction; the other three outputs remain
unspent at the audit snapshot. The halving-storage address has no outgoing
transaction. Thus common-input clustering adds no address, and one-hop output
following returns only the already-known 2024 self-spend.

All amounts, dates, addresses, and the two transactions reproduce the existing
"Prize address mechanics" record in `GSMG_PUZZLE.md`; none is a new puzzle
artifact.

## Verdict

P32 Family 2 is **closed negative**: the authenticated signing graph contains
no new address, output route, or provenance fact beyond the two known halving
self-spends.

The result is still operationally useful. The exact two-transaction raw-byte
cache now supplies the previously missing bounded input for P32 Family 9's
transaction-serialization and wallet-style fingerprint audit. Family 9 may
compare only these two creator-signed transactions and must retain its original
caveat: a wallet-style match can corroborate a workflow but cannot prove common
ownership or generate a password by itself.

## Reproduction and artifacts

```bash
python3 tools/gsmg/p32_transaction_graph_audit.py --self-test --run \
  --report doc/evidence/GSMG_P32_FAMILY2_TRANSACTION_GRAPH.json \
  --cache doc/evidence/GSMG_P32_FAMILY2_SIGNED_TRANSACTION_CACHE.json
```

- Report SHA-256: `505f21f433693e50a5ec54ac8a6783d2d341df04990a1673b076219174cd367b`
- Signed-transaction cache SHA-256:
  `1e43aa98f8f756fa8d9fbe6c407f57d331ab839f57c04985142b9bd0336e2eb9`

The report records the observation time and the exact cross-source digests.
The cache pins the raw hex and normalized transaction fields for the two
creator-signed transactions so Family 9 need not rediscover its input set.
