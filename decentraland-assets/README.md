# Decentraland puzzle audio

`puzzlepiece.mp3` is the canonical audio artifact associated with the GSMG
Decentraland deployment at `(-41, -17)`. It is stored under the same relative
path used by the upstream Naddiseo investigation so experiments can refer to a
stable local byte stream.

## Provenance

- Retrieved: 2026-08-30
- Decentraland content ID: `QmeRy5MjmEZ2W6J3DwhQfht5HKBKXBFpoGzSkzmjeGKiDK`
- Source: <https://peer.decentraland.org/content/contents/QmeRy5MjmEZ2W6J3DwhQfht5HKBKXBFpoGzSkzmjeGKiDK>
- Size: 212,031 bytes
- SHA-256: `ef17a96dce37b4dd7cbf79f210c5cbaf37fcae60e5faf8004de4e0832bd0dfee`
- Audio: MP3, stereo, 44.1 kHz, approximately 5.198 seconds

The bytes are also identical to `test.mp3` in the public
`lelicopter/mp3hacker` repository. That comparison is corroborating provenance,
not a claim about authorship or licensing.

The established stereo-difference/spectrogram reading is `HASHTHETEXT`.
Further signal or codec patterns should be treated as experimental observations
until independently calibrated.

Verify the checked-in artifact from the repository root:

```sh
sha256sum -c decentraland-assets/SHA256SUMS
```
