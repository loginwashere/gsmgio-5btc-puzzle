#!/usr/bin/env python3
"""Test three bounded pole-neutralization readings of the BUT/HYE rails."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cosmic_sweep_9ary  # noqa: E402
from cb_common import KDF_VARIANTS  # noqa: E402
from cosmic_sweep_9ary import SweepConfig, load_wordlist, test_keyword  # noqa: E402
from data import DBBI, FAED  # noqa: E402

WORDLIST = (
    Path(__file__).resolve().parents[2]
    / "wordlists"
    / "gsmg"
    / "matrixsumlist_choice_candidates.txt"
)
TARGETS = {
    "dbbi": (DBBI, "b", (("b", "e"), ("e", "b"))),
    "faed": (FAED, "h", (("h", "e"), ("e", "h"))),
}
MODES = ("delete", "to_a", "to_e")


def neutralize(stream, pole, mode):
    if mode == "delete":
        return stream.replace(pole, "")
    if mode == "to_a":
        return stream.replace(pole, "a")
    if mode == "to_e":
        return stream.replace(pole, "e")
    raise ValueError(f"unknown neutralization mode: {mode!r}")


def self_test():
    assert neutralize("bhhe", "h", "delete") == "be"
    assert neutralize("bhhe", "h", "to_a") == "baae"
    assert neutralize("bhhe", "h", "to_e") == "beee"
    try:
        neutralize("bhhe", "h", "typo")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown mode was not rejected")


def config_for(escape_orders):
    return SweepConfig(
        escape_orders=escape_orders,
        drop_letters=tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        topologies=("top_first", "escapes_first"),
        tail_fills=("forward", "reverse", "keyboard"),
        merge_directions=("backward", "forward"),
        kdf_variants=tuple(KDF_VARIANTS),
        input_transforms=("identity",),
        output_transforms=("identity",),
        newline_variants=False,
    )


def main():
    self_test()
    candidates = load_wordlist(str(WORDLIST))
    original_targets = dict(cosmic_sweep_9ary.TARGETS)
    total_configurations = 0
    all_hits = []
    try:
        for target, (stream, pole, escape_orders) in TARGETS.items():
            config = config_for(escape_orders)
            per_candidate = (
                len(config.drop_letters)
                * len(config.topologies)
                * len(config.tail_fills)
                * len(config.merge_directions)
                * len(config.escape_orders)
            )
            for mode in MODES:
                transformed = neutralize(stream, pole, mode)
                cosmic_sweep_9ary.TARGETS[target] = transformed
                mode_hits = []
                for candidate in candidates:
                    mode_hits.extend(test_keyword(candidate, target, config))
                configurations = len(candidates) * per_candidate
                total_configurations += configurations
                for hit in mode_hits:
                    hit["neutralization"] = mode
                    hit["pole"] = pole
                all_hits.extend(mode_hits)
                print(
                    target,
                    mode,
                    f"length={len(transformed)}",
                    f"configurations={configurations}",
                    f"hits={len(mode_hits)}",
                )
    finally:
        cosmic_sweep_9ary.TARGETS.clear()
        cosmic_sweep_9ary.TARGETS.update(original_targets)
    print(
        "totals:",
        f"candidates={len(candidates)}",
        f"configurations={total_configurations}",
        f"hits={len(all_hits)}",
    )
    for hit in all_hits:
        print(hit)


if __name__ == "__main__":
    main()
