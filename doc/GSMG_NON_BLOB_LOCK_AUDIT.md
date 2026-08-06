# GSMG Non-Blob Lock Audit

## Scope

This audit followed the reconstructed Architect rails:

```text
BUT / HYE
-> B <-> H around fixed E
-> H | YE | BUT
```

The goal was to determine whether `H` addresses a real puzzle input or operation
outside the tracked ciphertext blobs.

## Authentic interactive inputs

The three authenticated archived puzzle pages contain only one actual input:

```html
<form method="POST" action="https://gsmg.io/phase1verification">
    <input type="password" name="password"/>
</form>
```

The known Phase-1 password produced a `302` redirect to the documented
`choiceisanillusion...` page. No creator statement, archived response, route
artifact, or source code demonstrates that a second password selected a
different destination.

The alternative-password idea is therefore technically possible but unsupported.
It also conflicts with the creator's statements that the extra door is in the
first/zero puzzle piece and that the team could not check whether someone had
found it. The offline color/prime reconstruction is a much better fit for that
door than a hidden server branch.

## `H` as SHA-256

`H` can naturally abbreviate “hash,” and the final page explicitly says:

```text
sha256 our first hint is your last command
```

`tools/gsmg/first_hint_hash_audit.py` tests five exact first-hint materials:

- normalized visible banner;
- visible prize address;
- banner plus address;
- byte-exact full Stage-0 PNG;
- byte-exact cropped rabbit-grid PNG.

It reproduces the known entry route:

```text
SHA256(GSMGIO5BTCPUZZLECHALLENGE || prize address)
= 89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32
```

For every digest, the audit checked:

- compressed and uncompressed P2PKH derivation;
- equality to the prize and halving-recipient addresses;
- raw and hexadecimal digest forms as CBC passphrases;
- AES Key Wrap;
- digest bytes as a direct AES/3DES key.

Result: zero address, CBC, Key-Wrap, or raw-key hits.

The hash reading explains an already-solved transition but does not supply a new
lock or password.

## `Hush hush` / zeroing

The extra-door poem ends `Hush hush`, and the creator later says that some
characters must be “zeroed out.” `tools/gsmg/hush_zero_sweep.py` tests exactly
three bounded readings of the polarity symbols derived from the rails:

| Target | Pole | Operations |
|---|---|---|
| DBBI | `b` | delete; replace with `a` (`a=0`); collapse to center `e` |
| FAED | `h` | delete; replace with `a` (`a=0`); collapse to center `e` |

Each operation used all 19 exact Architect-derived seeds, both relevant escape
orders and topologies, all 26 dropped letters, all three tail fills, both merge
directions, and all six standard AES KDF variants.

Result:

```text
71,136 structural configurations
0 strong hits
0 new weak candidates
```

This closes these three literal pole-neutralization mechanics. It does not prove
what “zeroed out” means under an as-yet-unidentified prime-selected object.

## Twenty-seven boundary alignment

The natural segmentation:

```text
yin yang we wont give away the password its in front of your eyes but
youre not seeing it very last step is a true giveaway promised
```

contains 27 words. Cosmic Duality has 28 authored 64-character lines and thus
exactly 27 authored line boundaries.

`tools/gsmg/cosmic_boundary_word_audit.py` tests four fixed readings:

- choose the character before/after each boundary by word-length parity, both
  polarities;
- take the word-length-th character inward from the line before/after each
  boundary.

All four 27-character rails were Base64-decoded and scored by byte printability.
A shuffle gate permutes the same 27-word multiset across the fixed boundaries
and uses the maximum score across all four readings.

Results:

| Trials | Seed | Family-wise empirical p |
|---:|---:|---:|
| 10,000 | 20260725 | 0.056494 |
| 50,000 | 12345 | 0.049399 |

The winning real output was:

```text
7620fe87a93e5231f466702e6ee8c342545b66ce
```

It is non-language binary data with only a modest printable excess. The nominal
`p≈0.05` is not promotable because:

- the 27-word segmentation was selected after noticing the 27 boundaries;
- the project-wide multiple-testing burden is much larger than this one family;
- the output has no semantic or cryptographic validation.

No AES escalation was performed.

## Verdict

The local non-blob audit found no actionable lock:

- the Stage-1 form has no evidence for alternative-password routing;
- `H` as SHA-256 explains the already-known page-entry hash only;
- bounded `Hush`/zeroing mechanics are negative;
- the 27-boundary alignment is an unpromoted, non-semantic nominal anomaly.

The formerly missing `barrystyle` post is now semantically identified from
the surrounding 2022/2023/2024 transcript as the search result that led to
the *Cosmic Duality: Mysteries of the Unknown* book. Its exact media bytes are
still absent, but it is no longer an unknown operation or prime diagram. The
book's available text has already been investigated; its physical pages
57-58 remain the associated primary-evidence gap. Further transform families
are less grounded than recovering those pages or resolving another explicit
creator-chain edge.
