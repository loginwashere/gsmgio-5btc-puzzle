#!/usr/bin/env python3
"""Canonical inventory of *Cosmic Duality*'s decorated body drop caps.

The inventory was reconstructed by visually reviewing all 73 screenshots from
the 2026-07-12 book capture, supplemented by the later photographs of missing
pages 57-58.  Pages 57-58 contain no decorated drop caps.

The two decorated interior-title initials (C, D) are stored separately because
they are title typography rather than numbered body-page drop caps.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DropCap:
    chapter: int
    page: int
    letter: str


TITLE_INITIALS = "CD"

DROP_CAPS = (
    # Chapter 1
    DropCap(1, 16, "T"),
    DropCap(1, 18, "S"),
    DropCap(1, 23, "A"),
    DropCap(1, 24, "A"),
    DropCap(1, 25, "A"),
    DropCap(1, 26, "O"),
    DropCap(1, 31, "D"),
    DropCap(1, 32, "T"),
    DropCap(1, 35, "T"),
    DropCap(1, 38, "D"),
    # Chapter 2
    DropCap(2, 48, "W"),
    DropCap(2, 50, "O"),
    DropCap(2, 55, "O"),
    DropCap(2, 56, "T"),
    DropCap(2, 59, "T"),
    DropCap(2, 60, "T"),
    DropCap(2, 63, "W"),
    DropCap(2, 64, "B"),
    DropCap(2, 66, "A"),
    DropCap(2, 68, "T"),
    # Chapter 3
    DropCap(3, 80, "S"),
    DropCap(3, 82, "T"),
    DropCap(3, 84, "M"),
    DropCap(3, 85, "D"),
    DropCap(3, 86, "T"),
    DropCap(3, 91, "C"),
    DropCap(3, 93, "S"),
    DropCap(3, 94, "Z"),
    DropCap(3, 96, "F"),
    # Chapter 4
    DropCap(4, 106, "H"),
    DropCap(4, 109, "W"),
    DropCap(4, 111, "H"),
    DropCap(4, 115, "S"),
    DropCap(4, 116, "T"),
    DropCap(4, 120, "S"),
    DropCap(4, 121, "T"),
    DropCap(4, 122, "A"),
    DropCap(4, 124, "W"),
    DropCap(4, 127, "A"),
)

EXPECTED_CHAPTER_SEQUENCES = {
    1: "TSAAAODTTD",
    2: "WOOTTTWBAT",
    3: "STMDTCSZF",
    4: "HWHSTSTAWA",
}
EXPECTED_FULL_SEQUENCE = "TSAAAODTTDWOOTTTWBATSTMDTCSZFHWHSTSTAWA"


def chapter_sequence(chapter):
    return "".join(item.letter for item in DROP_CAPS if item.chapter == chapter)


def formatted_inventory():
    lines = []
    for chapter in EXPECTED_CHAPTER_SEQUENCES:
        entries = " ".join(
            f"{item.letter}{item.page}"
            for item in DROP_CAPS
            if item.chapter == chapter
        )
        lines.append(f"Chapter {chapter}: {entries}")
    return "\n".join(lines)


def self_test():
    assert TITLE_INITIALS == "CD"
    assert len(DROP_CAPS) == 39
    assert len({item.page for item in DROP_CAPS}) == 39
    assert all(item.letter.isalpha() and len(item.letter) == 1 for item in DROP_CAPS)
    assert all(a.page < b.page for a, b in zip(DROP_CAPS, DROP_CAPS[1:]))
    assert {
        chapter: chapter_sequence(chapter)
        for chapter in EXPECTED_CHAPTER_SEQUENCES
    } == EXPECTED_CHAPTER_SEQUENCES
    assert "".join(item.letter for item in DROP_CAPS) == EXPECTED_FULL_SEQUENCE
    assert not ({57, 58} & {item.page for item in DROP_CAPS})
    print("[*] self-test OK: 39 numbered body drop caps plus title initials CD")


if __name__ == "__main__":
    self_test()
    print(formatted_inventory())
    print(f"Letters only: {EXPECTED_FULL_SEQUENCE}")
    print(f"Decorated title initials: {TITLE_INITIALS}")
