#!/usr/bin/env python3
"""Phase 457: reproduce the Decentraland MP3 signal and frame-header claims."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MP3 = ROOT / "decentraland-assets" / "puzzlepiece.mp3"
DEFAULT_OUTPUT = Path(__file__).with_name("phase457_result.json")
EXPECTED_SHA256 = "ef17a96dce37b4dd7cbf79f210c5cbaf37fcae60e5faf8004de4e0832bd0dfee"
SAMPLE_RATE = 44_100
PERIOD = 684


def decode_stereo(path: Path) -> np.ndarray:
    raw = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-f", "f64le",
            "-acodec", "pcm_f64le", "-ac", "2", "-",
        ]
    )
    samples = np.frombuffer(raw, dtype="<f8")
    if len(samples) % 2:
        raise AssertionError("decoded stereo stream has an odd sample count")
    return samples.reshape(-1, 2)


def correlation(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.corrcoef(left, right)[0, 1])


def parse_mpeg1_layer3_frames(path: Path) -> list[dict]:
    data = path.read_bytes()
    offset = 0
    if data[:3] == b"ID3":
        size = data[6:10]
        tag_size = (size[0] << 21) | (size[1] << 14) | (size[2] << 7) | size[3]
        offset = 10 + tag_size

    bitrates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
    sample_rates = [44_100, 48_000, 32_000]
    frames = []
    while offset < len(data):
        if offset + 4 > len(data):
            raise AssertionError("truncated MPEG header")
        header = int.from_bytes(data[offset : offset + 4], "big")
        if header & 0xFFE00000 != 0xFFE00000:
            raise AssertionError(f"MPEG sync missing at byte {offset}")
        version = (header >> 19) & 0b11
        layer = (header >> 17) & 0b11
        bitrate_index = (header >> 12) & 0b1111
        sample_rate_index = (header >> 10) & 0b11
        padding = (header >> 9) & 1
        mode = (header >> 6) & 0b11
        mode_extension = (header >> 4) & 0b11
        if version != 0b11 or layer != 0b01 or sample_rate_index == 0b11:
            raise AssertionError("expected MPEG-1 Layer III frames")
        bitrate = bitrates[bitrate_index]
        sample_rate = sample_rates[sample_rate_index]
        if not bitrate:
            raise AssertionError("free/bad bitrate index is unsupported")
        frame_size = 144_000 * bitrate // sample_rate + padding
        frames.append(
            {
                "number_1_based": len(frames) + 1,
                "byte_offset": offset,
                "byte_length": frame_size,
                "mode": mode,
                "mode_extension": mode_extension,
                "mid_side_enabled": bool(mode_extension & 0b10),
            }
        )
        offset += frame_size
    if offset != len(data):
        raise AssertionError("frame walk did not consume the complete file")
    return frames


def audit(path: Path = DEFAULT_MP3) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    stereo = decode_stereo(path)
    difference = stereo[:, 0] - stereo[:, 1]
    phase_average = np.array([difference[index::PERIOD].mean() for index in range(PERIOD)])
    spectrum_power = np.abs(np.fft.rfft(phase_average)) ** 2
    dominant_bin = int(np.argmax(spectrum_power[1:]) + 1)
    frames = parse_mpeg1_layer3_frames(path)
    ms_disabled = [row["number_1_based"] for row in frames if not row["mid_side_enabled"]]

    return {
        "phase": 457,
        "artifact": {
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": digest,
        },
        "decoded_audio": {
            "sample_rate_hz": SAMPLE_RATE,
            "channels": 2,
            "samples_per_channel": int(len(stereo)),
            "duration_seconds": len(stereo) / SAMPLE_RATE,
        },
        "periodic_difference_signal": {
            "period_samples": PERIOD,
            "fundamental_hz": SAMPLE_RATE / PERIOD,
            "lag_684_correlation": correlation(difference[:-PERIOD], difference[PERIOD:]),
            "lag_342_correlation": correlation(difference[: -(PERIOD // 2)], difference[PERIOD // 2 :]),
            "folded_half_wave_correlation": correlation(
                phase_average[: PERIOD // 2], -phase_average[PERIOD // 2 :]
            ),
            "phase_average_dominant_fft_bin": dominant_bin,
            "dominant_bin_power_fraction": float(
                spectrum_power[dominant_bin] / spectrum_power.sum()
            ),
        },
        "mpeg_frames": {
            "count": len(frames),
            "all_joint_stereo": all(row["mode"] == 0b01 for row in frames),
            "mid_side_enabled_count": sum(row["mid_side_enabled"] for row in frames),
            "mid_side_disabled_count": len(ms_disabled),
            "mid_side_disabled_frames_1_based": ms_disabled,
            "internal_mid_side_disabled_frames_1_based": [
                number for number in ms_disabled if number not in {1, len(frames) - 1, len(frames)}
            ],
        },
        "interpretation": {
            "structured_periodic_signal_reproduced": True,
            "half_wave_is_creator_selected_yinyang": False,
            "frames_4_15_131_contain_recovered_payload": False,
            "known_channel_payload": "HASHTHETEXT",
            "creator_authentication_changed": False,
        },
    }


def self_test(path: Path = DEFAULT_MP3) -> dict:
    result = audit(path)
    assert result["artifact"]["sha256"] == EXPECTED_SHA256
    assert result["artifact"]["bytes"] == 212_031
    assert result["decoded_audio"]["samples_per_channel"] == 229_248
    signal = result["periodic_difference_signal"]
    assert math.isclose(signal["lag_684_correlation"], 0.918238151220151, abs_tol=1e-12)
    assert math.isclose(signal["lag_342_correlation"], -0.9184493972551334, abs_tol=1e-12)
    assert math.isclose(signal["folded_half_wave_correlation"], 0.9996937163160535, abs_tol=1e-12)
    assert math.isclose(signal["fundamental_hz"], 64.47368421052632, abs_tol=1e-12)
    assert math.isclose(signal["dominant_bin_power_fraction"], 0.9474218118778587, abs_tol=1e-12)
    frames = result["mpeg_frames"]
    assert frames["count"] == 199
    assert frames["all_joint_stereo"]
    assert frames["mid_side_enabled_count"] == 193
    assert frames["mid_side_disabled_frames_1_based"] == [1, 4, 15, 131, 198, 199]
    assert frames["internal_mid_side_disabled_frames_1_based"] == [4, 15, 131]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mp3", type=Path, default=DEFAULT_MP3)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    result = self_test(args.mp3)
    if args.self_test and not args.run:
        print("[*] Phase 457 self-test OK")
        return
    args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[*] wrote {args.json_out}")


if __name__ == "__main__":
    main()
