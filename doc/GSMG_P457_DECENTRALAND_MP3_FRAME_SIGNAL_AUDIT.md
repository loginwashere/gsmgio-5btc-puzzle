---
type: audit
phase: 457
date: 2026-08-30
status: complete
result: periodic-signal-and-frame-header-anomaly-reproduced-no-new-payload
disposition: historical-audio-thread-closed-no-gap-change
script: tools/gsmg/phase457_mp3_frame_signal_audit.py
---

# Phase 457 — Decentraland MP3 Periodicity and Frame-Header Audit

## Question and scope

Does the authenticated Decentraland `puzzlepiece.mp3` contain the reported
684-sample stereo-difference signal, and do MPEG frames 4, 15, and 131 carry
an unrecovered payload distinct from the established `HASHTHETEXT` channel?

This phase answers only the MP3/frame question raised in Telegram message
`69850`. That message also asks about yin-yang identity, prime reinsertion,
the post-Bifid DBBI/FAED path, the exact `lastwordsbeforearchichoice` answer,
and the Phase-3.2-tail AES blob. Those are separate questions. In particular,
the 80-byte blob with salt prefix `b45a5e3d` is already tracked in
`GSMG_COSMIC_DUALITY_UNTAKEN_PATHS.md` and `tools/gsmg/data.py`; it is not a
dropped MP3 thread.

## Frozen sources and provenance

### Audio

The checked-in [canonical MP3](../decentraland-assets/puzzlepiece.mp3) is
212,031 bytes with SHA-256
`ef17a96dce37b4dd7cbf79f210c5cbaf37fcae60e5faf8004de4e0832bd0dfee`.
It came from Decentraland content ID
`QmeRy5MjmEZ2W6J3DwhQfht5HKBKXBFpoGzSkzmjeGKiDK` and is byte-identical to
`test.mp3` in the public `lelicopter/mp3hacker` repository. Its local
provenance and checksum are recorded in `decentraland-assets/README.md` and
`decentraland-assets/SHA256SUMS`.

### Telegram history

The historical trail was checked in the project's pinned complete export,
`ChatExport_2026-07-26/result.json`:

| Message | Date (export) | Relevant content, paraphrased |
|---:|---|---|
| 5789 | 2021-02-13 | community summary says MP3 “blobs” were not recovered |
| 6688 | 2021-03-22 | describes retrieving parcel ownership, scripts, and raw resources |
| 6711 | 2021-03-22 | says code was assembled from several sources plus original work |
| 47157 | 2025-08-17 | points to `lelicopter/mp3hacker` and frames 4/15/131 |
| 47569 | 2025-08-21 | says an MP3 LSB path remained undecoded |
| 51648 | 2025-11-14 | identifies `test.mp3` and the repository's three-frame purpose |
| 61244 | 2026-04-02 | says “alphanoises” remained unrecovered |
| 61282 | 2026-04-06 | repeats frame numbers 4, 15, and 131 |

The live follow-up is **not** present in that frozen export, whose maximum
message ID is 67,267. It was checked in the bounded supplemental export
`ChatExport_2026-08-30/result.json` (1,722 messages, IDs 68,280–70,186,
2026-08-09 through 2026-08-30):

| Message | Date (export) | Relevant content, paraphrased |
|---:|---|---|
| 69850 | 2026-08-25 | reports the 684-sample signal and asks six questions |
| 69852 | 2026-08-25 | asks whether this is the known `HASHTHETEXT` channel |
| 69853 | 2026-08-25 | says frames 4/15/131 are separate and points to `MP3repack.py` |
| 69856 | 2026-08-25 | reports those frames as high L−R energy and proposes a codec explanation |

The supplementary-export distinction matters: these messages are real, but a
phase citing them must not imply they occur in the pinned July export. The
post-phase baseline follow-up is documented in
[GSMG_TELEGRAM_EXPORT_OVERLAY_BASELINE](GSMG_TELEGRAM_EXPORT_OVERLAY_BASELINE.md).

### Historical extractor

[`MP3repack.py`](https://github.com/lelicopter/mp3hacker/blob/master/MP3repack.py)
was inspected directly. It locates MP3 frames and writes selected frames into
separate/reassembled files. It contains no bit-reservoir recovery, PCM decode,
payload extraction, or interpretation logic. The repository therefore records
which frames were suspected; it does not itself demonstrate hidden content.

## Reproduction method

`phase457_mp3_frame_signal_audit.py` performs two independent checks:

1. decode the authenticated MP3 through `ffmpeg` to stereo 64-bit PCM, form
   `L−R`, compute raw lag correlations, fold samples modulo 684, compare the
   two 342-sample halves, and measure the folded waveform's FFT power; and
2. walk the original MP3 bytes from the ID3 boundary, parse every MPEG-1
   Layer III header, and read joint-stereo/mode-extension bits without using
   decoded audio or the historical repacker.

The frame-header result therefore does not depend on an encoder UI, a
spectrogram reading, or assumptions about frame-to-PCM delay alignment.

## Quantitative results

### Stereo-difference signal

The literal spectrogram rendering is now preserved as
[`GSMG_HASHTHETEXT_SPECTROGRAM.png`](evidence/GSMG_HASHTHETEXT_SPECTROGRAM.png),
with extraction method and checksums in its
[`provenance note`](evidence/GSMG_HASHTHETEXT_SPECTROGRAM_PROVENANCE.md).
It visibly spells the hexadecimal rail
`48 41 53 48 54 48 45 54 45 58 54`, which decodes to `HASHTHETEXT`.

| Observable | Reproduced value |
|---|---:|
| Decoded samples per channel | 229,248 |
| Duration at 44.1 kHz | 5.198367 s |
| Period | 684 samples |
| Fundamental | 64.473684 Hz |
| Raw `L−R` correlation at lag 684 | 0.9182381512 |
| Raw `L−R` correlation at lag 342 | −0.9184493973 |
| Folded half-wave correlation | 0.9996937163 |
| Folded-wave fundamental power fraction | 0.9474218119 |

The periodic, odd/half-wave-antisymmetric structure is real and highly
concentrated at the 684-sample fundamental. This is not a visual artifact of
a plotting program.

### MPEG frame headers

The file contains exactly 199 MPEG-1 Layer III frames. Every frame is joint
stereo. Mid/side stereo is enabled for 193 and disabled for exactly six:

`1, 4, 15, 131, 198, 199` (one-based frame numbering).

Removing the start/end boundary frames leaves exactly the historically named
internal set: `4, 15, 131`. This exact header-level coincidence is the
strongest reproducible fact behind the old “three blobs” thread.

An independent decoded-audio check places frames 131 and 15 as the two
largest low-frequency `L−R`-energy windows. Frame 4 ranks fourth under naive
uniform 1,152-sample windowing rather than third. The MP3 carries a 528-sample
encoder delay, so decoded-window rank is alignment-sensitive; no conclusion
depends on forcing an exact top-three ranking. The raw header set is exact.

## Interpretation

The evidence supports a codec-domain explanation for the broadband residual,
not a recovered second payload. The same three internal frames singled out by
the historical tool are exactly where the encoder turns mid/side stereo off.
At those locations left and right are quantized independently, so
stereo-difference energy can rise without a new message being embedded. This
explains why their residual behaves differently; it does **not** identify why
the encoder selected those three locations. The repacker merely isolates that
structural choice and supplies no extraction beyond it.

Four guardrails follow:

- Half-wave antisymmetry is a mathematically real thematic resemblance to a
  yin-yang/180-degree-opposition idea, but no creator evidence identifies it
  as the puzzle's required “ying yang.” It is not a discriminating identity
  test and does not change `G-YIN-001`.
- “The only payload is the parameters” is too strong. Phase 8 and the
  Naddiseo concordance already reproduce the intentional stereo-difference
  spectrogram channel as hexadecimal `HASHTHETEXT`.
- Frames 4/15/131 have not yielded an additional payload. Their exact
  mid/side-header status explains why they look exceptional.
- None of these observations authenticates a downstream password, operator,
  or creator-selected continuation.

## Verdict

`periodic_signal_and_frame_header_anomaly_reproduced_no_new_payload`.

The 684-sample difference signal and the three internal mid/side-disabled
frames are genuine, independently reproducible properties of the canonical
MP3. The old “unrecovered frames” trail is real history, not fabrication, but
the current evidence is fully accounted for by the known `HASHTHETEXT`
channel plus encoder mode decisions. No gap closes or reopens, no password
candidate is generated, and no oracle or decryption is invoked.

Artifacts:

- `decentraland-assets/puzzlepiece.mp3` and `SHA256SUMS`;
- `doc/evidence/GSMG_HASHTHETEXT_SPECTROGRAM.png` and its provenance note;
- `tools/gsmg/phase457_mp3_frame_signal_audit.py`;
- `tools/gsmg/test_phase457_mp3_frame_signal_audit.py`; and
- `tools/gsmg/phase457_result.json`
  (`ac2cb6f4f81631419644f8d180307c1e1b08ca97a5cb12f2da81f415dca758f3`).

Reproduce:

```sh
python3 tools/gsmg/phase457_mp3_frame_signal_audit.py --self-test
python3 tools/gsmg/phase457_mp3_frame_signal_audit.py --run
python3 -m unittest tools/gsmg/test_phase457_mp3_frame_signal_audit.py
```

## Stop rule

Do not continue carving, reassembling, or interpreting individual MP3 frames
without a new authenticated selector or a pre-registered codec-matched null.
A future claim must recover a stable payload under encoder-delay-aware
alignment and distinguish it from ordinary joint-stereo mode switching.

## Appendix — glyph/peak timing correction (2026-08-30)

A follow-up rendering reproduced the upstream notebook's exact operation,
`plt.specgram(L - R, Fs=44100)`, and inspected the three anomalies separately
in the 10–20 kHz band. That band lies above the digit-glyph image, which is
drawn in the 0–8 kHz band, and therefore isolates the broadband codec residual
from the picture itself.

None of the three anomalies is co-located with glyph ink:

| Frame | Delay-corrected frame window | Clean-band peak | Actual position |
|---:|---:|---:|---|
| 4 | 0.066–0.093 s | ~0.099 s | blank lead-in; the first `4` starts at ~0.142 s |
| 15 | 0.354–0.380 s | ~0.389 s | gap after the first `8`, before `41` |
| 131 | 3.384–3.410 s | ~3.42 s | gap between the `5` and `4` of the eighth `54` |

Accordingly, the conversation-level mapping `4 → H`, `15 → H`, `131 → T`
(or hex digits `4,8,5`) is withdrawn. The stronger statement is `gap, gap,
gap`: the three broadband peaks are adjacent to, not on, the spectrogram's
drawn digits.

This also rejects the proposed causal chain “strong glyph stroke → locally
complex `L−R` → M/S disabled.” The glyph strokes are narrowband power dips,
whereas the three anomalies are broadband power peaks in flat inter-glyph
regions. The raw headers still establish that all three internal anomalies
coincide exactly with M/S-disabled frames, so the codec state explains the
character of the residual after the switch. What caused the encoder to make
those three decisions remains unexplained. The phase verdict, gap disposition,
and stop rule are unchanged.
