"""Dedupe and summarize cb_common.WEAK_CANDIDATE_LOG for human review.

The log is append-only JSONL (see cb_common._log_candidate) -- every sweep run
across every subprocess worker appends to it, so the same candidate can show up
many times (e.g. the Phase 3.2 self-test used to re-log its own known-positive
vector on every import, before that was trimmed to weak-tier-only; see
FINDINGS.md's "Weak/strong AES oracle tiers implemented" section). This script
collapses re-discoveries of the same (blob, kdf, passphrase) down to one row
and sorts by z-score so a human can scan what's actually new.
"""
import argparse
import json
from collections import OrderedDict
from pathlib import Path

LOG_PATH = Path(__file__).parent / "weak_candidates_log.txt"


def load_records(path, tier):
    seen = OrderedDict()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if tier is not None and rec["tier"] != tier:
                continue
            key = (rec["blob"], rec["kdf"], rec["passphrase_hex"])
            seen.setdefault(key, rec)  # first-seen copy; later repeats are re-discoveries
    return list(seen.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", default=str(LOG_PATH))
    ap.add_argument("--tier", default="weak", choices=["weak", "strong", "all"])
    ap.add_argument("--min-z", type=float, default=0.0)
    args = ap.parse_args()
    tier = None if args.tier == "all" else args.tier

    if not Path(args.log).exists():
        print(f"no log at {args.log} -- nothing to review")
        return

    records = load_records(args.log, tier)
    records = [r for r in records if r["z_score"] >= args.min_z]
    records.sort(key=lambda r: r["z_score"], reverse=True)

    print(f"{len(records)} unique candidate(s) after dedup (tier={args.tier}, min_z={args.min_z})\n")
    header = (f"{'z':>7}  {'blob':<8} {'kdf':<14} {'ratio':>6} {'len':>6} "
               f"{'run':>4} utf8  passphrase_hex (first 32 chars)")
    print(header)
    print("-" * len(header))
    for r in records:
        print(f"{r['z_score']:7.3f}  {r['blob']:<8} {r['kdf']:<14} "
              f"{r['printable_ratio']:6.3f} {r['plaintext_length']:6d} "
              f"{r['longest_printable_run']:4d} {'Y' if r['utf8_valid'] else 'N':<4}  "
              f"{r['passphrase_hex'][:32]}")


if __name__ == "__main__":
    main()
