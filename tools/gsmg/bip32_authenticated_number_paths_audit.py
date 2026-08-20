#!/usr/bin/env python3
"""C1 from doc/Brainstorms/2026-08-20 - Creative Brute-Force Coverage
Expansion.md: "BIP32 paths from authenticated numbers."

Explicitly speculative wallet semantics -- unlike A1/A2/A3/B1, nothing in
this project's fact ledger says the creator used BIP32 derivation at all.
What makes it worth a bounded pilot regardless: it has an exact-address
endpoint (no threshold, no scoring) and every input number is one this
project has already independently authenticated elsewhere -- it doesn't
invent new numeric material. A negative result here says nothing about
whether those numbers matter to the puzzle; it only closes this one
speculative wallet-derivation reading of them. See "Disposition" below.

Pre-registration (frozen before any run, per the brainstorm's own
"Decisions"/stop-rule requirement and the user's explicit scope freeze):

  - Frozen inputs: the same 42 P0A/Phase-335 sentinel candidates, reused
    from half_better_half_algebra_audit.py -- identical corpus to Phase
    336/337/338 for direct comparability.
  - Frozen seed-byte forms, exactly two: SHA-256(candidate text, UTF-8) as
    a 32-byte seed, and SHA-512(candidate text, UTF-8) as a 64-byte seed
    (BIP32's own maximum allowed seed length) -- chosen because a BIP32
    seed must be 16-64 bytes and candidate text length varies, so a fixed
    hash-based seed avoids inventing a length-dependent rule.
  - Frozen path registry, exactly five authenticated-number sources, no
    others:
      * `23/16/7`  -> (23, 16, 7)
      * `401/400/73` -> (401, 400, 73)
      * `1/4/21` -> (1, 4, 21)
      * `14/8/1` -> (14, 8, 1)
      * `574061` -> three declared readings: as one single-level index
        (574,061); as the one 6-level path this project's own established
        `574061 -> [[5,7,4],[0,6,1]]` grouping gives, concatenated
        (5,7,4,0,6,1); and as that same grouping's two independent
        3-level halves (5,7,4) and (0,6,1), each derived separately from
        the same master (matching the bracket-pair structure
        `GSMG_HOME.md` already records, not a new invented split).
    8 total paths.
  - Frozen hardening policy: exactly two variants per path -- ALL levels
    hardened (index + 0x80000000 throughout) or ALL levels non-hardened.
    No mixed-hardening permutations (that would multiply each path by
    2^depth instead of 2, and this project has no source suggesting which
    levels, if any, should be hardened).
  - Frozen derivation standard: BIP32 HMAC-SHA512 private-parent-key-to-
    private-child-key derivation only (key_shape_classifier.py's existing
    bip32_ckd_priv/bip32_derive_path, already exercised by that module's
    own BIP39-seed self-test) -- no alternate KDF.
  - Frozen check points: the FINAL child key at the end of each path only
    (not every intermediate level), plus the SEED'S OWN MASTER KEY as a
    declared control (not itself expected to hit; included so a
    trivial "the seed IS the key" case isn't silently skipped while
    walking paths past it).
  - Frozen success criterion: an EXACT match against the prize address or
    one of Phase 331's 8 known EC-derived targets (checker::known_targets/
    half_better_half_algebra_audit.KNOWN_TARGET_HASH160S) -- no Bloom
    cache, no broad scoring, no probabilistic pre-filter of any kind.
  - Stop rule: run exactly once over the frozen scope above.

Scope note: 42 candidates x 2 seed forms x 8 paths x 2 hardening variants
x (final child + master control) is bounded in the hundreds of BIP32
derivation steps and low thousands of address checks -- see self_test()'s
own count assertion -- explicitly NOT the combine/window-style millions of
checks Phase 336/337/338 needed, because this idea has no AES-decrypt
step and no per-blob multiplication at all.

Disposition note (per the user's explicit instruction): a negative result
from this pilot is evidence against BIP32 derivation being the intended
use of these numbers, under this exact frozen scheme -- it is NOT evidence
against the underlying authenticated numbers (23/16/7, 401/400/73, 1/4/21,
14/8/1, 574061) mattering to the puzzle through some other mechanism. Do
not cite this phase as closing those numbers generally.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from half_better_half_algebra_audit import (  # noqa: E402
    EXPECTED_CANDIDATE_DIGEST,
    KNOWN_TARGET_HASH160S,
    PRIZE_HASH160_HEX,
    candidate_list_digest,
    frozen_candidates,
    frozen_candidates_with_provenance,
)
from binary_key_material_backfill import hash160, private_key_details  # noqa: E402
import key_shape_classifier  # noqa: E402

HARDENED_OFFSET = 0x80000000

# Exactly the 5 authenticated-number sources -> 8 concrete paths (see
# module docstring for the derivation of the 574061 entries). Frozen; not
# extended after seeing results.
PATH_REGISTRY = {
    "23_16_7": (23, 16, 7),
    "401_400_73": (401, 400, 73),
    "1_4_21": (1, 4, 21),
    "14_8_1": (14, 8, 1),
    "574061_single_index": (574061,),
    "574061_grouped_6level": (5, 7, 4, 0, 6, 1),
    "574061_grouped_part1_574": (5, 7, 4),
    "574061_grouped_part2_061": (0, 6, 1),
}

SEED_FORMS = ("sha256", "sha512")
HARDENING_MODES = ("all_hardened", "all_nonhardened")


def seed_bytes(text: str, form: str) -> bytes:
    data = text.encode()
    if form == "sha256":
        return hashlib.sha256(data).digest()
    if form == "sha512":
        return hashlib.sha512(data).digest()
    raise ValueError(f"unknown seed form {form!r}")


def hardened_path(path, mode):
    if mode == "all_hardened":
        return tuple(i + HARDENED_OFFSET for i in path)
    if mode == "all_nonhardened":
        return tuple(path)
    raise ValueError(f"unknown hardening mode {mode!r}")


def check_key(key_bytes, known_targets):
    """Exact-target-only check -- no Bloom, no scoring, per this idea's
    frozen success criterion."""
    addrs = private_key_details(key_bytes)
    if addrs is None:
        return None
    for address_type, info in addrs.items():
        h = bytes.fromhex(info["hash160"])
        if h in known_targets:
            return {"address_type": address_type, "target_label": known_targets[h], **info}
    return None


def run(candidates=None, known_targets=None):
    targets = KNOWN_TARGET_HASH160S if known_targets is None else known_targets

    if candidates is None:
        cand_records = frozen_candidates_with_provenance()
    else:
        cand_records = [(i, "external", f"candidate_{i}", text) for i, text in enumerate(candidates)]
    candidate_texts = [text for (_i, _model, _label, text) in cand_records]

    derivations = 0
    checks = 0
    hits = []
    for index, model, label, text in cand_records:
        candidate_sha256 = hashlib.sha256(text.encode()).hexdigest()
        for seed_form in SEED_FORMS:
            seed = seed_bytes(text, seed_form)
            master_key, master_chain = key_shape_classifier.bip32_master(seed)

            # Master-key control (once per candidate/seed-form, not once
            # per path -- it doesn't depend on the path at all).
            checks += 1
            master_hit = check_key(master_key, targets)
            if master_hit is not None:
                hits.append({
                    "candidate_index": index, "candidate_model": model, "candidate_label": label,
                    "candidate_sha256": candidate_sha256, "seed_form": seed_form,
                    "path_name": None, "hardening": None, "check_point": "master_control",
                    **master_hit,
                })

            for path_name, base_path in PATH_REGISTRY.items():
                for hardening in HARDENING_MODES:
                    path = hardened_path(base_path, hardening)
                    derivations += len(path)
                    final_key = key_shape_classifier.bip32_derive_path(master_key, master_chain, path)
                    if final_key is None:
                        continue  # spec-mandated skip (astronomically unlikely), not an error
                    checks += 1
                    hit = check_key(final_key, targets)
                    if hit is not None:
                        hits.append({
                            "candidate_index": index, "candidate_model": model, "candidate_label": label,
                            "candidate_sha256": candidate_sha256, "seed_form": seed_form,
                            "path_name": path_name, "hardening": hardening, "check_point": "final_child",
                            **hit,
                        })

    return {
        "candidate_count": len(cand_records),
        "candidate_digest": candidate_list_digest(candidate_texts),
        "seed_forms": len(SEED_FORMS),
        "path_count": len(PATH_REGISTRY),
        "hardening_modes": len(HARDENING_MODES),
        "bip32_derivation_steps": derivations,
        "address_checks": checks,
        "hits": hits,
        "total_hits": len(hits),
    }


def self_test():
    # 1. Official BIP32 Test Vector 1 (bip-0032.mediawiki), fetched
    #    directly from the BIP repository rather than hand-typed from
    #    memory -- exactly the kind of transcription risk Phase 336's own
    #    self-test correction already burned this project on once.
    official_seed = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    official_master_xprv = (
        "xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVvvNKmPGJxWUtg6LnF5"
        "kejMRNNU3TGtRBeJgk33yuGBxrMPHi"
    )
    official_m0h_xprv = (
        "xprv9uHRZZhk6KAJC1avXpDAp4MDc3sQKNxDiPvvkX8Br5ngLNv1TxvUxt4cV1rGL5hj6KCesnDYUhd7oW"
        "gT11eZG7XnxHrnYeSvkzY7d2bhkJ7"
    )

    def decode_xprv_key_and_chain(token):
        payload = key_shape_classifier.base58check_decode(token)
        assert payload is not None and len(payload) == 78, "malformed xprv payload"
        chain_code = payload[13:45]
        key = payload[46:78]  # skip the 0x00 private-key marker byte at 45
        assert payload[45] == 0x00
        return key, chain_code

    official_master_key, official_master_chain = decode_xprv_key_and_chain(official_master_xprv)
    official_m0h_key, official_m0h_chain = decode_xprv_key_and_chain(official_m0h_xprv)

    computed_master_key, computed_master_chain = key_shape_classifier.bip32_master(official_seed)
    assert computed_master_key == official_master_key, "master key does not match official BIP32 test vector 1"
    assert computed_master_chain == official_master_chain, "master chain code does not match official test vector 1"

    computed_m0h_key, computed_m0h_chain = key_shape_classifier.bip32_ckd_priv(
        computed_master_key, computed_master_chain, HARDENED_OFFSET
    )
    assert computed_m0h_key == official_m0h_key, "m/0H key does not match official BIP32 test vector 1"
    assert computed_m0h_chain == official_m0h_chain, "m/0H chain code does not match official BIP32 test vector 1"

    # 2. Seed-form sanity: two distinct, correctly-sized forms.
    s256 = seed_bytes("probe", "sha256")
    s512 = seed_bytes("probe", "sha512")
    assert len(s256) == 32 and len(s512) == 64
    assert s256 != s512

    # 3. Path registry contract: exactly 8 paths, exactly the 5 declared
    #    number sources, total depth matches the module docstring's count.
    assert len(PATH_REGISTRY) == 8
    assert PATH_REGISTRY["23_16_7"] == (23, 16, 7)
    assert PATH_REGISTRY["574061_grouped_part1_574"] + PATH_REGISTRY["574061_grouped_part2_061"] == (5, 7, 4, 0, 6, 1)
    assert PATH_REGISTRY["574061_grouped_6level"] == (5, 7, 4, 0, 6, 1)
    total_depth = sum(len(p) for p in PATH_REGISTRY.values())
    assert total_depth == 3 + 3 + 3 + 3 + 1 + 6 + 3 + 3 == 25

    # 4. Hardening sanity: all_hardened offsets every level; all_nonhardened changes nothing.
    assert hardened_path((1, 2, 3), "all_hardened") == (1 + HARDENED_OFFSET, 2 + HARDENED_OFFSET, 3 + HARDENED_OFFSET)
    assert hardened_path((1, 2, 3), "all_nonhardened") == (1, 2, 3)

    # 5. End-to-end planted-hit test: pick a seed/path/hardening
    #    combination, walk it forward with the real driver to get a final
    #    child key, then plant that child's OWN address as a known target
    #    and confirm run() actually recovers it at the exact right
    #    (candidate, seed_form, path_name, hardening) coordinates -- not
    #    just that BIP32 math is right in isolation.
    probe_text = "bip32-c1-self-test-probe"
    probe_seed = seed_bytes(probe_text, "sha256")
    probe_master_key, probe_master_chain = key_shape_classifier.bip32_master(probe_seed)
    probe_path = hardened_path(PATH_REGISTRY["1_4_21"], "all_nonhardened")
    probe_final_key = key_shape_classifier.bip32_derive_path(probe_master_key, probe_master_chain, probe_path)
    assert probe_final_key is not None
    probe_addrs = private_key_details(probe_final_key)
    synthetic_target = {bytes.fromhex(probe_addrs["compressed"]["hash160"]): "planted/compressed"}

    report = run(candidates=[probe_text], known_targets=synthetic_target)
    assert report["total_hits"] >= 1, "planted BIP32 final-child hit was not found by the real driver"
    hit = next(h for h in report["hits"]
              if h["path_name"] == "1_4_21" and h["hardening"] == "all_nonhardened"
              and h["seed_form"] == "sha256" and h["check_point"] == "final_child")
    assert hit["candidate_index"] == 0
    assert hit["candidate_sha256"] == hashlib.sha256(probe_text.encode()).hexdigest()

    # 6. Master-key control: plant a DIFFERENT target matching the seed's
    #    own master key (not any path's final child) and confirm it's
    #    reported as check_point "master_control", proving the declared
    #    control actually runs and is distinguishable from a path hit.
    master_addrs = private_key_details(probe_master_key)
    master_target = {bytes.fromhex(master_addrs["compressed"]["hash160"]): "planted/master"}
    master_report = run(candidates=[probe_text], known_targets=master_target)
    assert master_report["total_hits"] >= 1, "planted master-key control hit was not found"
    assert any(h["check_point"] == "master_control" and h["seed_form"] == "sha256"
              for h in master_report["hits"])

    # 7. Negative control: an unrelated candidate against the same planted
    #    target must not hit.
    wrong_report = run(candidates=["definitely-not-the-probe"], known_targets=synthetic_target)
    assert wrong_report["total_hits"] == 0, "unrelated candidate unexpectedly produced a hit"

    # 8. Frozen-corpus contract + bounded-scope contract (hundreds, not
    #    millions, of derivations -- per the user's explicit requirement).
    cands = frozen_candidates()
    assert len(cands) == 42
    assert candidate_list_digest(cands) == EXPECTED_CANDIDATE_DIGEST
    real_scope_report = run(candidates=[probe_text])  # 1 candidate, real KNOWN_TARGET_HASH160S
    # Per-candidate cost: 2 seed forms x (1 master check + 8 paths x 2
    # hardening final-child checks) = 2 x 17 = 34 checks; 42 candidates
    # would be 1,428 -- comfortably "hundreds, not millions".
    assert real_scope_report["address_checks"] == 34
    assert 42 * real_scope_report["address_checks"] < 2000

    # 9. Prize address is reachable as a target (not just the 8 EC-derived ones).
    assert bytes.fromhex(PRIZE_HASH160_HEX) in KNOWN_TARGET_HASH160S

    print("[*] self-test OK: official BIP32 Test Vector 1 (master + m/0H) matched exactly, "
          "seed-form sanity, 8-path/25-level registry contract, hardening-policy sanity, "
          "planted final-child hit recovered end-to-end with provenance, planted master-control "
          "hit recovered and distinguished from a path hit, negative control clean, "
          f"frozen-corpus digest {EXPECTED_CANDIDATE_DIGEST} enforced, "
          "34 checks/candidate confirmed bounded, 42 frozen candidates confirmed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    report = run() if args.run else {"note": "pass --run to execute against the oracle"}
    if args.json:
        print(json.dumps(report, indent=2, default=repr))
    else:
        for key, value in report.items():
            if key == "hits":
                continue
            print(f"{key}: {value}")
        for hit in report.get("hits", []):
            print("HIT:", hit)


if __name__ == "__main__":
    main()
