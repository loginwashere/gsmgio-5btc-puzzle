# GSMG External Archive Audit

Date: 2026-07-26

## Sources

- `https://gsmg-archive.org/`
- `https://github.com/HosterjackAGV/gsmg-5btc-puzzle`
- Hosterjack snapshot audited at commit
  `1a278563f64ea3134ab453a66179292bcae22034`

## Primary Mirror

`gsmg-archive.org` is a compact static mirror of the original puzzle pages.
Its HTML does not identify an author or preservation chain, so it is useful
as a corroborating mirror rather than an authenticated creator source.

All ten puzzle images referenced by the mirror were downloaded and compared
by SHA-256. Every image matches an existing local artifact exactly:

- the genesis image;
- the rabbit image;
- all eight Phase-1 icon fragments.

The mirror therefore adds no missing primary media or new page text to this
project. It does independently corroborate the bytes already retained here.

## Hosterjack Catalog

The audited snapshot contains 158 attempt records and 79 walkthrough assets.
It is a valuable attempt index, but it mixes primary artifacts, community
claims, and its own research conclusions. Its status labels are not evidence
by themselves, and several conclusions are stale relative to this project.

Examples of already-covered or stale entries include FEFE/prime-zeroing,
matrixsumlist masking, `p32_trailing`, URLBLOB, AES Key Wrap, the icon rebus,
and QR decoding. Two stronger items were absent from this project's record
and warranted direct audit.

## `YOUWON`

The community discovery is genuine. DBBI and the solved Phase-3.2 VIC
plaintext are both 91 characters. Interpreting DBBI as `a=0..i=8` and
subtracting the plaintext modulo 26 gives:

`VOZIJBDTIQBRGVEOMZNBCYOUWONXCPKWGBNAXDGJGDUNNVMPABTAFPAAXMJYLZBUWERDNXYDESKUOBXCAMVDJLQTSGA`

`YOUWON` begins at zero-based offset 21 and leaves exactly 64 characters.
Telegram provenance is community message `23912` (2024-04-07), later
explained in detail by message `26597`; it is not a creator-authored reveal.

Under uniform permutations of DBBI's exact symbol multiset, with the
plaintext, operation, alphabet values, and target word fixed, only offset 21
can produce `YOUWON`. Its exact probability is
`3.3755203466e-6`, approximately 1 in 296,251. This makes the relationship
noteworthy, although it is not a discovery p-value because the historical
search space of operations and noticed words is unknown.

The external catalog overstates the corroboration as three independent
signals:

- the six `YOUWON` positions themselves force six underflow bits to one;
- the unique seven-one underflow run at offset 21 extends that forced run by
  only one position;
- the VIC codeword-width run is a property of the fixed plaintext, and
  offset 21 is already the only alphabet-feasible `YOUWON` placement.

The rails reproduce, but they are alignment-dependent and must not be
multiplied as independent evidence. The safest status is **plausibly
engineered community find, downstream operation unresolved**. Existing
direct-key tests are negative.

A later external write-up re-proposed the 64-character tail as a raw private
key under a "custom 16-character alphabetic hex mapping," without running
its own proposed character-set audit -- the tail actually has 24 distinct
letters, ruling out any bijective 16-letter alphabet. The one coherent
surviving reading (a modulo-16 wraparound decode) was tested directly against
known addresses, as a raw AES key, and live against the Blockstream API for
any transaction history; all negative. See FINDINGS.md Phase 147 and
`tools/gsmg/youwon_direct_key_derivation_audit.py`.

## A007522

The mechanical observation also reproduces:

- blue prime spiral indices: `7,23,31,47,103,127`;
- yellow prime spiral indices: `71,79,151,167,191`.

All are primes congruent to 7 modulo 8, hence members of OEIS A007522.
However, the external catalog's statement that A007522 is
“creator-confirmed” is false. The exact list was posted by community member
gnomad in Telegram message `49487` on 2025-09-23.

The modular pattern is also partly structural rather than an independent
surprise: all 24 colored cells mark character LSB positions in the verified
spiral, so every colored index is necessarily 7 modulo 8. Filtering those
indices for primes necessarily yields A007522 members.

The creator-authored phrase `yellowblueprimes` still makes the color-split
prime subset a reasonable candidate value, but A007522's name contributes no
extra confirmation. The external catalog reports direct/combine tests as
negative; those counts were not independently rerun in this audit.

## Corrections

- The Stage-0 PNG filter anomaly reproduces, but an earlier local
  “mid-module” argument was invalid: the perspective-skewed QR has no single
  module fraction for one horizontal source-image scanline. That argument is
  retracted in Phase 73.
- Distinct salts and absent repeated ciphertext blocks establish separate
  containers, not independent passphrases or independent narrative roles.
- Negative book-keyword sweeps do not prove that the book is “purely
  thematic” or that the missing datum must be private.

## Recommended Use

The external archives are now exhausted as missing-primary-artifact sources.
The only newly recovered lead worth retaining is the DBBI/INCASE `YOUWON`
alignment, with its dependence caveat. The next bounded investigation should
ask whether offset 21 and the `21 | YOUWON | 64` partition select a
creator-supported operation on DBBI's residual information. It should not
resume broad passphrase spraying.
