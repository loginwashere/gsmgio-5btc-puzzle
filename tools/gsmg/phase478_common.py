"""Shared, frozen pieces for Phase 478 (DBBI {b,g} substituted-digest match).

Both the harvester and the matcher import this module so the equality-
pattern definition and the frozen DBBI target are computed exactly once,
identically, in both directions -- per the protocol's requirement that no
new normalization or scoring logic be introduced between discovery and
scoring.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from checkerboard_code_ic_oracle import segment_codes  # noqa: E402
from data import DBBI  # noqa: E402

HEX_DIGITS = "0123456789abcdef"

DBBI_ESCAPE_PAIR = ("b", "g")

# Frozen 2026-09-05, independently recomputed from tools/gsmg/data.py's DBBI
# constant -- not copied from the unauthenticated PROGRESS.md source. See
# "doc/Brainstorms/2026-09-05 - Phase 478 ... Protocol.md".
DBBI_PATTERN = "01234556728966286abc61c88b48de3086dd501d5557d6bab5605233df7bbb96"


def equality_pattern(seq):
    """Label positions by order of first occurrence of their value, render
    each label as one lowercase hex digit. Well-defined for ANY sequence
    using at most 16 distinct values -- which every 64-character
    lowercase-hex digest satisfies unconditionally (hex has exactly 16
    possible characters). A digest using fewer than 16 distinct hex digits
    is not a special case: it produces a normal pattern over however many
    labels it needs, which then simply fails to string-equal a 16-label
    target -- a definite mismatch, not a skip. The `None` return below is
    generic library robustness for sequences needing MORE than 16 labels;
    it is mathematically unreachable for a 64-character hex-digest input
    and never fires in Phase 478."""
    label_of = {}
    labels = []
    for item in seq:
        if item not in label_of:
            if len(label_of) >= 16:
                return None
            label_of[item] = len(label_of)
        labels.append(label_of[item])
    return "".join(HEX_DIGITS[label] for label in labels)


def dbbi_tokens():
    return segment_codes(DBBI, *DBBI_ESCAPE_PAIR)


def _self_test():
    tokens = dbbi_tokens()
    assert tokens is not None, "DBBI does not validly segment under {b,g}"
    assert len(tokens) == 64, f"expected 64 tokens, got {len(tokens)}"
    assert len(set(tokens)) == 16, f"expected 16 types, got {len(set(tokens))}"
    pattern = equality_pattern(tokens)
    assert pattern == DBBI_PATTERN, (
        f"recomputed DBBI {{b,g}} equality pattern does not match the frozen "
        f"target.\n  recomputed: {pattern}\n  frozen:     {DBBI_PATTERN}"
    )

    # equality_pattern basic behaviour checks, independent of DBBI.
    assert equality_pattern(list("abab")) == "0101"
    assert equality_pattern(list("aabb")) == "0011"
    assert equality_pattern(list(range(17))) is None  # 17 distinct > 16

    # A digest using FEWER than 16 distinct hex digits is a normal,
    # well-defined, definite mismatch against a 16-label target -- not a
    # skip. Simulate a 64-char "digest" using only 15 distinct values: it
    # must still produce a real (non-None) pattern, and that pattern must
    # not equal the (16-label) DBBI target.
    fifteen_distinct = list(range(15)) * 5
    fifteen_distinct = fifteen_distinct[:64]
    under_pattern = equality_pattern(fifteen_distinct)
    assert under_pattern is not None
    assert len(under_pattern) == 64
    assert under_pattern != DBBI_PATTERN

    assert equality_pattern([]) == ""


_self_test()

if __name__ == "__main__":
    print("phase478_common self-test OK")
    print("DBBI {b,g} pattern:", DBBI_PATTERN)
