#!/usr/bin/env python3
"""Audit responsive soft-wrap readings of the SalPhaseIon textarea.

The authenticated source has one space between every logical character and no
authored newlines.  A retained historical community screenshot nevertheless
fixes one real rendered state: 45 logical symbols per visual row.  This audit
recovers that count from pixels, compares its segment-boundary behavior with
every width 20..100, and searches only vertical/diagonal reads for words frozen
from the creator's macro.  The null shuffles characters independently inside
each authenticated page segment and repeats the complete width/direction
family.  No horizontal read, cipher, password, or blob oracle is used.
"""

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

from PIL import Image

from page_structure_audit import DEFAULT_HTML, audit as page_audit
from salphaseion_presentation_binding_audit import PresentationParser, _text


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCREENSHOT = ROOT / "SalPhaselonCosmicDuality.png"
EXPECTED_SCREENSHOT_SHA256 = (
    "a3810ba24250c5a04908e1281c2202e73f7487f9d19f41bfd2c3e55fa9be57ed"
)
WIDTHS = tuple(range(20, 101))
SCREENSHOT_LINE_BANDS = ((116, 130), (132, 146), (148, 162))
EXPECTED_SCREENSHOT_WIDTH = 45
DEFAULT_TRIALS = 500
DEFAULT_SEED = 20260810
PROMOTION_P = 0.005

# Frozen before inspecting any responsive-grid output.  Short macro words are
# omitted because a-i ciphertext makes 2/3-letter matches uninformative.
MACRO_TARGETS = (
    "yellow", "blue", "primes", "matrix", "list", "last", "words",
    "before", "archi", "choice", "yang", "wont", "give", "away",
    "password", "front", "your", "eyes", "youre", "seeing", "very",
    "step", "true", "giveaway", "promised",
)


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def contiguous_groups(values):
    groups = []
    for value in values:
        if not groups or value > groups[-1][-1] + 1:
            groups.append([value])
        else:
            groups[-1].append(value)
    return tuple((group[0], group[-1]) for group in groups)


def recover_screenshot_width(path=DEFAULT_SCREENSHOT):
    path = Path(path)
    digest = sha256_file(path)
    if digest != EXPECTED_SCREENSHOT_SHA256:
        raise AssertionError(f"historical screenshot changed: {digest}")
    image = Image.open(path).convert("RGB")
    if image.size != (668, 619):
        raise AssertionError(f"historical screenshot dimensions changed: {image.size}")

    bands = []
    for y_start, y_end in SCREENSHOT_LINE_BANDS:
        dark_x = [
            x for x in range(image.width)
            if any(max(image.getpixel((x, y))) < 180 for y in range(y_start, y_end))
        ]
        groups = contiguous_groups(dark_x)
        if not groups or groups[0] != (6, 6):
            raise AssertionError("textarea left border was not recovered")
        glyphs = groups[1:]
        if len(glyphs) != EXPECTED_SCREENSHOT_WIDTH:
            raise AssertionError(f"screenshot wrap count changed: {len(glyphs)}")
        starts = tuple(group[0] for group in glyphs)
        steps = tuple(right - left for left, right in zip(starts, starts[1:]))
        if min(steps) < 14 or max(steps) > 16:
            raise AssertionError("screenshot glyph pitch is not monospaced")
        bands.append({
            "y_range": (y_start, y_end),
            "glyph_count": len(glyphs),
            "first_glyph_x": glyphs[0][0],
            "last_glyph_x": glyphs[-1][-1],
            "pitch_range_pixels": (min(steps), max(steps)),
        })
    return {
        "path": str(path),
        "sha256": digest,
        "image_size": image.size,
        "community_repository_commit": "99bd811 (2021-05-07)",
        "creator_authored_viewport": False,
        "recovered_logical_symbols_per_row": EXPECTED_SCREENSHOT_WIDTH,
        "measured_bands": tuple(bands),
    }


def source_text(html_path=DEFAULT_HTML):
    source = Path(html_path).read_text(encoding="utf-8")
    parser = PresentationParser()
    parser.feed(source)
    if len(parser.textareas) != 2:
        raise AssertionError("expected two authenticated textareas")
    raw = _text(parser.textareas[0])
    logical = "".join(raw.split())
    if raw != " ".join(logical):
        raise AssertionError("SalPhaseIon spacing changed")
    return source, raw, logical


def grid_lines(text, width):
    rows = tuple(text[offset:offset + width] for offset in range(0, len(text), width))
    vertical = tuple(
        "".join(row[column] for row in rows if column < len(row))
        for column in range(width)
    )

    down_right = []
    for start_column in range(width):
        line = []
        row_index, column = 0, start_column
        while row_index < len(rows) and column < len(rows[row_index]):
            line.append(rows[row_index][column])
            row_index += 1
            column += 1
        down_right.append("".join(line))
    for start_row in range(1, len(rows)):
        line = []
        row_index, column = start_row, 0
        while row_index < len(rows) and column < len(rows[row_index]):
            line.append(rows[row_index][column])
            row_index += 1
            column += 1
        down_right.append("".join(line))

    down_left = []
    for start_column in range(width):
        line = []
        row_index, column = 0, start_column
        while row_index < len(rows) and 0 <= column < len(rows[row_index]):
            line.append(rows[row_index][column])
            row_index += 1
            column -= 1
        down_left.append("".join(line))
    for start_row in range(1, len(rows)):
        line = []
        row_index, column = start_row, width - 1
        while row_index < len(rows) and 0 <= column < len(rows[row_index]):
            line.append(rows[row_index][column])
            row_index += 1
            column -= 1
        down_left.append("".join(line))

    return {
        "vertical": vertical,
        "diagonal_down_right": tuple(down_right),
        "diagonal_down_left": tuple(down_left),
    }


def vocabulary_hits(text, widths=WIDTHS):
    hits = []
    for width in widths:
        for direction, lines in grid_lines(text.lower(), width).items():
            corpus = "\0".join(lines)
            for token in MACRO_TARGETS:
                orientations = []
                if token in corpus:
                    orientations.append("forward")
                if token[::-1] in corpus:
                    orientations.append("reverse")
                if orientations:
                    hits.append({
                        "width": width,
                        "direction": direction,
                        "token": token,
                        "token_length": len(token),
                        "orientations": tuple(orientations),
                    })
    return tuple(hits)


def score_hits(hits):
    if not hits:
        return (0, 0, 0)
    return (
        max(hit["token_length"] for hit in hits),
        len({hit["token"] for hit in hits}),
        len(hits),
    )


def shuffle_within_segments(logical, segments, rng):
    output = []
    cursor = 0
    for segment in segments:
        if segment["start"] != cursor:
            raise AssertionError("segment coverage is not contiguous")
        values = list(logical[segment["start"]:segment["end"]])
        rng.shuffle(values)
        output.extend(values)
        cursor = segment["end"]
    if cursor != len(logical):
        raise AssertionError("segments do not cover the logical stream")
    return "".join(output)


def calibration(logical, segments, real_score, trials=DEFAULT_TRIALS, seed=DEFAULT_SEED):
    rng = random.Random(seed)
    exceedances = 0
    score_counts = {}
    maximum = (0, 0, 0)
    for _ in range(trials):
        shuffled = shuffle_within_segments(logical, segments, rng)
        score = score_hits(vocabulary_hits(shuffled))
        score_counts[score] = score_counts.get(score, 0) + 1
        maximum = max(maximum, score)
        exceedances += score >= real_score
    return {
        "trials": trials,
        "seed": seed,
        "comparison": "lexicographic (max token length, distinct tokens, total hits)",
        "exceedances": exceedances,
        "empirical_p": (exceedances + 1) / (trials + 1),
        "null_max_score": maximum,
        "distinct_null_scores": len(score_counts),
    }


def boundary_inventory(segments, widths=WIDTHS):
    rows = []
    for width in widths:
        aligned = tuple(
            segment["name"] for segment in segments[:-1]
            if segment["end"] % width == 0
        )
        rows.append({"width": width, "aligned_segment_ends": aligned})
    return tuple(rows)


def audit(
    html_path=DEFAULT_HTML,
    screenshot_path=DEFAULT_SCREENSHOT,
    trials=DEFAULT_TRIALS,
    seed=DEFAULT_SEED,
):
    screenshot = recover_screenshot_width(screenshot_path)
    source, raw, logical = source_text(html_path)
    page = page_audit(Path(html_path))
    segments = page["salphaseion"]["segments"]
    if len(logical) != 1075 or len(raw) != 2149:
        raise AssertionError("authenticated SalPhaseIon lengths changed")

    authored_presentation = {
        "body_font_rule": "arial",
        "textarea_inline_style": "width: 100%; height: 200px",
        "textarea_font_authored": False,
        "cols_attribute": False,
        "wrap_attribute": False,
        "authored_line_breaks": raw.count("\n"),
        "single_space_between_logical_symbols": True,
        "viewport_or_column_count_authored": False,
    }
    if "font-family: 'arial'" not in source:
        raise AssertionError("body font rule changed")

    boundaries = boundary_inventory(segments)
    by_width = {row["width"]: row for row in boundaries}
    faed_end_widths = tuple(
        row["width"] for row in boundaries
        if "faed" in row["aligned_segment_ends"]
    )
    if faed_end_widths != (45, 51, 85):
        raise AssertionError(f"FAED boundary divisors changed: {faed_end_widths}")

    real_hits = vocabulary_hits(logical)
    real_score = score_hits(real_hits)
    null = calibration(logical, segments, real_score, trials, seed)
    screenshot_hits = tuple(hit for hit in real_hits if hit["width"] == 45)
    invariant_tokens = tuple(
        sorted(
            token for token in MACRO_TARGETS
            if all(any(hit["width"] == width and hit["token"] == token for hit in real_hits) for width in WIDTHS)
        )
    )
    promoted = (
        screenshot["creator_authored_viewport"]
        and null["empirical_p"] < PROMOTION_P
        and bool(screenshot_hits)
    )
    return {
        "scope": {
            "widths": WIDTHS,
            "directions": ("vertical", "diagonal_down_right", "diagonal_down_left"),
            "orientations": ("forward", "reverse"),
            "targets": MACRO_TARGETS,
            "horizontal_reads_excluded": True,
            "oracle_run": False,
        },
        "source_presentation": authored_presentation,
        "historical_screenshot": screenshot,
        "screenshot_grid": {
            "width": 45,
            "row_count": math.ceil(len(logical) / 45),
            "full_rows": len(logical) // 45,
            "last_row_length": len(logical) % 45,
            "aligned_segment_ends": by_width[45]["aligned_segment_ends"],
        },
        "boundary_controls": {
            "faed_end_aligned_widths": faed_end_widths,
            "screenshot_width_unique_for_faed_end": faed_end_widths == (45,),
            "all_widths": boundaries,
        },
        "responsive_vocabulary": {
            "real_score": real_score,
            "all_hits": real_hits,
            "screenshot_width_hits": screenshot_hits,
            "tokens_present_at_every_width": invariant_tokens,
            "calibration": null,
        },
        "promotion": {
            "promoted": promoted,
            "new_compute_authorized": promoted,
            "required": (
                "creator-authored width/viewport or width-invariant read",
                f"matched-control p < {PROMOTION_P}",
                "non-horizontal authenticated macro-vocabulary output",
            ),
        },
        "verdict": (
            "The one-space encoding genuinely creates responsive visual grids, "
            "and the historical community screenshot mechanically fixes a 45-column "
            "24-row state whose FAED segment ends on a row boundary. That boundary "
            "does not select 45 uniquely (51 and 85 also divide the same endpoint), "
            "the HTML authors no font/cols/wrap/viewport, and the screenshot viewport "
            "is not creator-authored. Promotion additionally requires the complete "
            "vertical/diagonal vocabulary family to beat its segment-preserving null."
        ),
    }


def self_test(html_path=DEFAULT_HTML, screenshot_path=DEFAULT_SCREENSHOT, trials=DEFAULT_TRIALS, seed=DEFAULT_SEED):
    report = audit(html_path, screenshot_path, trials, seed)
    assert report["historical_screenshot"]["recovered_logical_symbols_per_row"] == 45
    assert report["screenshot_grid"]["row_count"] == 24
    assert report["screenshot_grid"]["full_rows"] == 23
    assert report["screenshot_grid"]["last_row_length"] == 40
    assert report["screenshot_grid"]["aligned_segment_ends"] == ("faed",)
    assert report["boundary_controls"]["faed_end_aligned_widths"] == (45, 51, 85)
    assert not report["source_presentation"]["viewport_or_column_count_authored"]
    assert report["responsive_vocabulary"]["calibration"]["trials"] == trials
    assert not report["promotion"]["promoted"]
    print(json.dumps(report, indent=2))
    print("[*] self-test OK: screenshot width recovered and responsive family calibrated")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML)
    parser.add_argument("--screenshot", type=Path, default=DEFAULT_SCREENSHOT)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = self_test(args.html, args.screenshot, args.trials, args.seed) if args.self_test else audit(args.html, args.screenshot, args.trials, args.seed)
    if args.json and not args.self_test:
        print(json.dumps(report, indent=2))
    elif not args.self_test:
        print(report["verdict"])


if __name__ == "__main__":
    main()
