#!/usr/bin/env python3
"""Render three bounded DBBI/FAED tone maps and inspect their spectrograms.

Phase 8 documents a from-scratch NumPy STFT reproduction of the Decentraland
audio clue, but neither that script nor the source MP3 remains in this tree.
This audit therefore reuses the documented core operation, not unknowable
renderer parameters.  It emits deterministic WAV/PNG artifacts and optionally
runs Tesseract as a mechanical embedded-text screen.
"""

import argparse
from collections import Counter
import hashlib
import json
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image

from data import DBBI, FAED


SAMPLE_RATE = 8_000
NOTE_SECONDS = 0.08
NOTE_SAMPLES = round(SAMPLE_RATE * NOTE_SECONDS)
RAMP_SAMPLES = 40
FFT_SIZE = 512
HOP_SIZE = 128
MAPPINGS = {
    "chromatic_a_root": (60, 61, 62, 63, 64, 65, 66, 67, 68),
    "major_a_root": (60, 62, 64, 65, 67, 69, 71, 72, 74),
    "major_i_root_cyclic": (62, 64, 65, 67, 69, 71, 72, 74, 60),
}
SOURCES = {"dbbi": DBBI, "faed": FAED}


def midi_frequency(note):
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def render_tones(stream, midi_notes):
    envelope = np.ones(NOTE_SAMPLES, dtype=np.float64)
    ramp = np.sin(np.linspace(0, np.pi / 2, RAMP_SAMPLES, endpoint=True)) ** 2
    envelope[:RAMP_SAMPLES] = ramp
    envelope[-RAMP_SAMPLES:] = ramp[::-1]
    time = np.arange(NOTE_SAMPLES, dtype=np.float64) / SAMPLE_RATE
    chunks = []
    for symbol in stream:
        note = midi_notes[ord(symbol) - ord("a")]
        chunks.append(0.8 * envelope * np.sin(2 * np.pi * midi_frequency(note) * time))
    return np.concatenate(chunks)


def write_wav(path, signal):
    samples = np.clip(np.rint(signal * 32767), -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(samples.tobytes())


def stft_image(signal):
    if len(signal) < FFT_SIZE:
        signal = np.pad(signal, (0, FFT_SIZE - len(signal)))
    frames = np.lib.stride_tricks.sliding_window_view(signal, FFT_SIZE)[::HOP_SIZE]
    spectrum = np.abs(np.fft.rfft(frames * np.hanning(FFT_SIZE), axis=1)).T
    frequencies = np.fft.rfftfreq(FFT_SIZE, 1 / SAMPLE_RATE)
    keep = (frequencies >= 180) & (frequencies <= 700)
    decibels = 20 * np.log10(spectrum[keep] + 1e-9)
    low, high = np.percentile(decibels, (5.0, 99.5))
    normalized = np.clip((decibels - low) / (high - low), 0, 1)
    pixels = np.rint(255 * (1 - normalized[::-1])).astype(np.uint8)
    image = Image.fromarray(pixels, mode="L")
    target_width = min(2400, max(800, image.width))
    target_height = 420
    return image.resize((target_width, target_height), Image.Resampling.NEAREST)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def ocr_image(path):
    texts = []
    for page_mode in (6, 7, 11):
        process = subprocess.run(
            ["tesseract", str(path), "stdout", "--psm", str(page_mode)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        texts.append(process.stdout.strip())
    token_sets = tuple({
        token.lower() for token in re.findall(r"[A-Za-z0-9]{3,}", text)
    } for text in texts)
    support = Counter(token for tokens in token_sets for token in tokens)
    tokens = tuple(sorted(support))
    consensus = tuple(sorted(token for token, count in support.items() if count >= 2))
    return tuple(texts), tokens, consensus


def audit(output_dir, run_ocr=True):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for source_name, stream in SOURCES.items():
        for mapping_name, midi_notes in MAPPINGS.items():
            stem = f"{source_name}_{mapping_name}"
            wav_path = output_dir / f"{stem}.wav"
            png_path = output_dir / f"{stem}.png"
            signal = render_tones(stream, midi_notes)
            write_wav(wav_path, signal)
            image = stft_image(signal)
            image.save(png_path, format="PNG", optimize=False)
            ocr_texts, ocr_tokens, ocr_consensus = (
                ocr_image(png_path) if run_ocr else ((), (), ())
            )
            rows.append({
                "source": source_name,
                "mapping": mapping_name,
                "midi_notes": midi_notes,
                "duration_seconds": len(signal) / SAMPLE_RATE,
                "wav_path": str(wav_path),
                "spectrogram_path": str(png_path),
                "wav_sha256": sha256_file(wav_path),
                "spectrogram_sha256": sha256_file(png_path),
                "spectrogram_size": image.size,
                "ocr_texts": ocr_texts,
                "ocr_tokens": ocr_tokens,
                "ocr_consensus_tokens": ocr_consensus,
                "ocr_repeated_token_noise": bool(ocr_consensus),
            })
    return {
        "provenance": {
            "documented_operation": "Phase 8 from-scratch NumPy STFT",
            "original_script_present": False,
            "original_mp3_present": False,
            "claim": "core operation reused; exact historical parameters unavailable",
        },
        "render": {
            "sample_rate": SAMPLE_RATE,
            "note_seconds": NOTE_SECONDS,
            "amplitude_role": "constant; symbol selects pitch only",
            "mapping_count": len(MAPPINGS),
            "source_count": len(SOURCES),
        },
        "stft": {
            "fft_size": FFT_SIZE,
            "hop_size": HOP_SIZE,
            "window": "Hann",
            "display_band_hz": (180, 700),
        },
        "rows": tuple(rows),
        "ocr_run": run_ocr,
        "ocr_nonempty_consensus_count": sum(
            row["ocr_repeated_token_noise"] for row in rows
        ),
        "ocr_is_promotion_oracle": False,
        "visual_review_required": True,
        "candidate_text_generated": False,
        "password_oracle_run": False,
    }


def self_test():
    signal = render_tones("ai", MAPPINGS["chromatic_a_root"])
    assert len(signal) == 2 * NOTE_SAMPLES
    assert np.max(np.abs(signal)) <= 0.8 + 1e-12
    with tempfile.TemporaryDirectory(prefix="gsmg-audio-selftest-") as directory:
        report = audit(directory, run_ocr=False)
        assert len(report["rows"]) == 6
        assert all(Path(row["wav_path"]).is_file() for row in report["rows"])
        assert all(Path(row["spectrogram_path"]).is_file() for row in report["rows"])
        assert report["render"]["mapping_count"] == 3
        assert report["ocr_is_promotion_oracle"] is False
        assert not report["candidate_text_generated"]
    print("[*] self-test OK: deterministic WAV and NumPy-STFT render family verified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="/tmp/gsmg-dbbi-faed-audio")
    parser.add_argument("--no-ocr", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    report = audit(args.output_dir, run_ocr=not args.no_ocr)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print("[*] provenance:", report["provenance"])
    print("[*] render:", report["render"])
    print("[*] STFT:", report["stft"])
    for row in report["rows"]:
        print(
            f"[*] {row['source']}/{row['mapping']}: "
            f"duration={row['duration_seconds']:.2f}s "
            f"wav_sha256={row['wav_sha256']} "
            f"png_sha256={row['spectrogram_sha256']} "
            f"ocr_consensus_tokens={row['ocr_consensus_tokens']}"
        )
    print("[*] OCR renders with repeated token noise:",
          report["ocr_nonempty_consensus_count"])
    print("[*] OCR is not a promotion oracle for tonal ridge images")
    print("[*] visual review remains required; no candidate/password oracle was used")


if __name__ == "__main__":
    main()
