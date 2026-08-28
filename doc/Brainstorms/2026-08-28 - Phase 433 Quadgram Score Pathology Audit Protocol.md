# Phase 433 — Quadgram Score Pathology Audit Protocol

Frozen before inspecting any Phase-430 leader newer than the Phase-432 snapshot.

## Question

Why does Phase 430's optimized quadgram score improve while its decode remains
unreadable? Is the gain English-like beyond Bifid mechanics, or an expected
selection/relabeling effect?

## Frozen candidates

1. Phase-430 rank zero;
2. Phase-429 exact winner, square `DBIFHCEGAKNMRUOPLSTWXYVQZ`;
3. Phase-432 snapshot leader, rank `6734809711440`, square
   `DBIFKCENAMUHOGPLRSTQVWXYZ`, score `-3507.5981`.

Every diagnostic excludes the leading `BTCSEED`.

## Controls

- 1,000 exact-tail-multiset shuffles per candidate;
- 1,000 shuffles of the 281 intact aligned Bifid output digraphs after the
  fixed tail singleton per candidate;
- 10,000 deterministic uniform global Phase-430 ranks;
- 10,000 deterministic random assignments of the fourteen non-`G/H` symbols
  conditional on each candidate's exact ordered `G/H` cells;
- first 563 normalized letters (`J→I`) of
  `doc/GSMG_PHASE425_BTCSEED_FAMILYWIDE_SIGNIFICANCE_AUDIT.md`, whose source
  SHA-256 is `126ebd33bbd1454de610c9bbd24064e134c9fc50cd3f11507d56a19dec10d5b5`.

Seeds are fixed in the implementation. Empirical upper-tail p-values are
inclusive with add one. Random-rank controls characterize scale only; they do
not correct the trillions-way optimized maximum.

## Metrics and decomposition

- frozen Phase-430 quadgram total/mean and unseen-floor fraction;
- score rank within every applicable control;
- character entropy, alphabet size, vowel fraction, index of coincidence;
- lag-1 mutual information, raw-DEFLATE saving, and longest repeated substring;
- distinct n-gram counts for lengths 1–4;
- quadgrams contributing the most repeated excess above the unseen floor and
  the fraction of total above-floor score supplied by the top ten grams.

No alternate language model, dictionary, keyword, password, Bitcoin, blob, or
GPU oracle is allowed. A high score against shuffled controls is not plaintext
evidence when it is the explicit optimization target. Promotion would require
the optimized tail to approach the pinned English control on absolute score
and broad distributional metrics, not merely beat random candidates.
