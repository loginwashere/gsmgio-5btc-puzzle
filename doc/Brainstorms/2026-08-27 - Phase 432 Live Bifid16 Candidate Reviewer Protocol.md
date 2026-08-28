# Phase 432 — Live Bifid-16 Candidate Reviewer Protocol

Frozen before the reviewer is run on a checkpoint newer than the Phase-431
development snapshot.

## Purpose

Review Phase-430 retained block winners without changing its sealed GPU score
or search. The reviewer is descriptive and CPU-only. It must never promote a
candidate from the already-fixed `BTCSEED` prefix.

## Inputs and gates

- one atomic Phase-430 checkpoint snapshot;
- exact Phase-430 family, range, FAED, decoded-cell, quadgram, kernel, driver,
  architecture, and score fingerprint;
- `/usr/share/dict/words`, with its SHA-256 recorded;
- optional prior Phase-432 report for deterministic delta reporting.

Any fingerprint mismatch, malformed rank, missing dictionary, decode not
starting `BTCSEED`, or unequal scores for identical decodes is fatal.

## Frozen review

Collapse all retained rows by SHA-256 of the full decoded text, retain their
best score/minimum rank and raw member count, then review at most the 25
score-leading distinct tails. Remove `BTCSEED` before every metric.

For each reviewed tail report:

- exact dictionary substrings of length 5–12;
- maximum-weight non-overlapping dictionary segmentation using words of length
  4–12 and weight `length²`, including covered-character fraction;
- inclusive empirical upper-tail p-values for substring count and segmentation
  score against 200 deterministic exact-multiset shuffles of that same tail;
- exact hits from the source-frozen Bitcoin/puzzle vocabulary in the tool;
- index of coincidence;
- the five strongest equal-character lag fractions for lags 1–40;
- longest exact repeated-substring length and the strongest repeated n-grams
  of lengths 4–12.

The random seed is derived from the decoded SHA-256 plus the fixed Phase-432
seed, so repeated reviews of the same text are identical. These diagnostics
are not a multiple-testing-corrected discovery claim. A short word, isolated
keyword, or uncorrected p-value cannot promote plaintext.

When a prior report is supplied, report newly seen and departed decoded hashes,
whether the leader changed, and the score delta. Never call a password,
Bitcoin-address, key, blob, network, or GPU oracle.
