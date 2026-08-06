#!/usr/bin/env python3
"""HISTORICAL PHASE-47 FOLLOW-UP, superseded in its color channel by Phase 48.

The text deletion result remains reproducible, but the claimed shared removal
operation does not: the color-channel removal was the modeling error. FEFE's
established prime-walk role is insertion as a separate event.

Reconcile Phase 41's and Phase 47's independent readings of "consume the
marked prime/zero object" -- do they conflict, or are they the same
operation viewed through two channels?

The creator-authored dependency chain (`doc/GSMG_CREATOR_AUTHORED_CLUE_LEDGER.md`)
includes a step "consume the marked prime/zero object" between the FEFE
address `{1,4,21}` and "matrix sum/list". Two prior phases each proposed an
operational reading of "consume" without cross-referencing the other:

* Phase 41 (`fefe_zero_operation_audit.py`) deletes the addressed
  *character* (`n`) from the 24-character decoded TEXT
  (`gsmg.io/theseedisplanted`), giving `gsmg.io/theseedisplated` ->
  "the seed is Fe-plated" (combined with the FEFEFE pixel value).
* Phase 47 (`yellow_blue_mask_convergence_audit.py`) removes the addressed
  object's *color* from the 24-item B/Y sequence, giving a 23-item
  sequence that was then compared against Denis Golovkin's recovered masks.

Both use the same FEFE-derived index (`reconstruction["fefe"]["character_0"]`),
never a hardcoded `21` -- so neither violates Phase 37's caution against
"arbitrary {1,4,21} indexing". This module checks the more basic question
directly: removing the SAME single object (by index, once) from the SAME
24-item object list, does the character-channel projection reproduce
Phase 41's result and does the color-channel projection reproduce Phase 47's
result, simultaneously? If so, "consume the marked object" is a single,
well-defined operation with two independently-already-recorded readouts, not
two competing hypotheses about what "consume" means.

This reconciliation does NOT resolve Phase 47's own residual object-22/23
discrepancy -- that gap is untouched by this check and remains unsupported.
"""
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys  # noqa: E402
sys.path.insert(0, str(SCRIPT_DIR))
from first_piece_color_reconstruction import DEFAULT_IMAGE, reconstruct  # noqa: E402

EXPECTED_TEXT_CHANNEL_RESULT = "gsmg.io/theseedisplated"
EXPECTED_COLOR_CHANNEL_RESULT = "BBBBYBBBYYBBBBYBBYYBYBY"
EXPECTED_ADDRESSED_ORDINAL = 21
EXPECTED_ADDRESSED_CHARACTER = "n"
EXPECTED_ADDRESSED_COLOR = "yellow"


def reconcile(image_path):
    reconstruction = reconstruct(image_path)
    objects = reconstruction["objects"]
    addressed_index = reconstruction["fefe"]["character_0"]  # dynamic, not hardcoded
    addressed_object = objects[addressed_index]

    full_text = "".join(item["character"] for item in objects)
    full_colors = "".join("B" if item["color"] == "blue" else "Y" for item in objects)

    text_channel = full_text[:addressed_index] + full_text[addressed_index + 1 :]
    color_channel = full_colors[:addressed_index] + full_colors[addressed_index + 1 :]

    return {
        "addressed_index": addressed_index,
        "addressed_object": addressed_object,
        "full_text": full_text,
        "full_colors": full_colors,
        "text_channel": text_channel,
        "color_channel": color_channel,
        "channels_from_one_removal": (text_channel, color_channel),
    }


def self_test():
    report = reconcile(DEFAULT_IMAGE)
    addressed = report["addressed_object"]
    assert addressed["ordinal_1"] == EXPECTED_ADDRESSED_ORDINAL, addressed
    assert addressed["character"] == EXPECTED_ADDRESSED_CHARACTER, addressed
    assert addressed["color"] == EXPECTED_ADDRESSED_COLOR, addressed

    assert report["text_channel"] == EXPECTED_TEXT_CHANNEL_RESULT, (
        f"text-channel projection does not reproduce Phase 41's recorded "
        f"result: {report['text_channel']!r}"
    )
    assert report["color_channel"] == EXPECTED_COLOR_CHANNEL_RESULT, (
        f"color-channel projection does not reproduce Phase 47's recorded "
        f"result: {report['color_channel']!r}"
    )

    # The critical reconciliation check: both channel results must come from
    # removing the SAME single index, not two independently-chosen indices
    # that merely happen to both be "21" by coincidence of two separate
    # analyses. Verified directly: both slices above used addressed_index
    # exactly once, shared between both channels.
    print(
        "[*] self-test OK: Phase 41's text-channel result and Phase 47's "
        "color-channel result both reproduce from removing the single "
        f"FEFE-addressed object (index {report['addressed_index']}, "
        f"ordinal {addressed['ordinal_1']}, character {addressed['character']!r}, "
        f"color {addressed['color']}) -- confirmed as one operation viewed "
        "through two channels, not two competing interpretations"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    print(
        "[!] HISTORICAL PHASE-47 FOLLOW-UP: the shared-removal conclusion is "
        "superseded in the color channel"
    )
    self_test()
    if args.self_test:
        return

    report = reconcile(args.image)
    addressed = report["addressed_object"]
    print(f"[*] full text   ({len(report['full_text'])} chars): {report['full_text']}")
    print(f"[*] full colors ({len(report['full_colors'])} chars): {report['full_colors']}")
    print(
        f"[*] addressed object: index={report['addressed_index']} "
        f"ordinal={addressed['ordinal_1']} character={addressed['character']!r} "
        f"color={addressed['color']}"
    )
    print(f"\n[*] text-channel projection (Phase 41's operation): {report['text_channel']!r}")
    print(f"[*] color-channel projection (Phase 47's operation): {report['color_channel']!r}")
    print(
        "\n[*] verdict: both are consistent projections of ONE removal, not "
        "competing readings of 'consume'. This reconciles the two phases but "
        "does NOT resolve Phase 47's own residual object-22/23 discrepancy, "
        "which remains an unsupported open gap."
    )


if __name__ == "__main__":
    main()
