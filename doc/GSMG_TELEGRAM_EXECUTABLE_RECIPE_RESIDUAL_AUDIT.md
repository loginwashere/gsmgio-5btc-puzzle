# Telegram executable-recipe residual audit

Date: 2026-08-24

## Phase 393: frozen discovery lane

Phase 388 reviewed the original 1,828-message Stage-1 keyword universe and
the 77-message technique-plus-surprise intersection. It left a distinct
discovery axis: technique messages outside both sets, regardless of sender.

Before any selected message was read for substance, Phase 393 froze this
universe and one recipe-shape gate. A message enters the review lane only if
it contains both a result/password/key-style claim and executable-looking
material (for example `sha256(...)`, OpenSSL/AES, `key=`/`iv=`, a 64-hex
value, a Salted__ Base64 prefix, or a Bitcoin address).

| Set | Count |
| --- | ---: |
| Technique hits | 1,629 |
| Technique hits outside Stage 1 | 1,475 |
| Previously reviewed surprise intersection outside Stage 1 | 59 |
| Technique-only residual | 1,416 |
| Frozen executable-recipe review lane | 142 |

The lane is content-pinned:

```text
ID digest:      dbc380cde28d6f4847c1c5373165573eac6998df57afc6423a561c4ff6950287
content digest: 759e491c5caaacc372cef5cecf997cdab44769641031095bf0d03edf9531c836
```

All 142 complete texts were read. The committed audit stores ID, timestamp,
sender, matched technique terms, full-text SHA-256, disposition, and reason;
it does not store private Telegram-export text in a generated repository
artifact.

| Disposition | Messages |
| --- | ---: |
| Covered by a solved step, existing finite family, or Phase 394 oracle | 88 |
| Question, joke, unrelated example, false positive, or incomplete claim | 51 |
| Reproducible construction promoted to separate verification | 3 |
| **Total** | **142** |

The three promoted messages form two constructions: `65082` (the FEFE/GF(2)
matrix claim) and `66244`/`66245` (one BIP39 claim split between explanation
and code).

## Phase 394A: FEFE/GF(2) construction

Message `65082` changes the unique FEFE cell at row 8, column 5 of the
authenticated 14×14 Stage-0 matrix from `0` to `1`. Its algebra is correct:
the source matrix has GF(2) rank 13; the changed matrix has rank 12 and the
two posted row/column dependencies reproduce exactly (with their third
nonzero kernel combination also enumerated).

The construction does not discriminate a solution:

- the source value is already authenticated by the positive-control spiral
  decode; changing it turns `gsmg.io/theseedisplanted` into
  `gsmg.io/theseedispla~ted`;
- 27 of all 196 possible single-cell changes produce the same rank-12 result
  (`13.78%`), so the FEFE cell is one of many;
- a uniform random 14×14 binary matrix has exact-rank-12 probability
  `12.833%` and rank-at-most-12 probability `13.362%`.

Disposition: mechanically verified, statistically ordinary, and incompatible
with the known Stage-0 decode. It supplies no output or consumer and is not
promoted.

## Phase 394B: BTCSEED-rail BIP39 construction

Messages `66244`/`66245` take the Phase-386 Bifid output's unique alternating
rail whose alphabet is exactly `{b,c,d,e}`, map `d,c,b,e` to `0,1,2,3`, and
select 132 symbols at full-rail offset 30 (equivalent to the post's “drop six,
then offset 27”). The claimed mnemonic and checksum reproduce exactly:

```text
dust trophy mule tragic corn cupboard sand crunch salt like inspire radar
hunt twice wolf empower sweet glimpse update turtle copy satoshi fee allow

entropy: 445d1e457373066bafc9a7beb035d55856f7d6bf3248dbac67ba7573017ed520
checksum: 00110101
```

The adjacent words `satoshi fee` are noteworthy, but the checksum is not an
independent authentication after the mapping and window are selected. The
complete natural family is 24 bijections of four symbols to two-bit values ×
154 possible 132-symbol windows = 3,696 trials. It contains 13 checksum-valid
24-word mnemonics; chance expectation is 3,696/256 = 14.4375. The posted
mnemonic is one of those 13, not a unique checksum solution. No earlier or
neighboring Telegram message fixes its mapping or offset before the words are
seen.

Downstream wallet authentication is negative. With an empty BIP39 passphrase,
none of these direct 32-byte interpretations matches the prize-address
HASH160: recovered entropy, the first 32 seed bytes, or the BIP32 master key.
Six fixed legacy derivation templates were then checked through index 999:

```text
m/44'/0'/0'/0/i   m/44'/0'/0'/1/i
m/0'/0/i          m/0'/1/i
m/0/i             m/1/i
```

That is 6,000 child private keys and 12,000 compressed/uncompressed P2PKH
address encodings, with zero prize-address matches. Testing uncompressed
forms is already conservative: BIP32 specifies compressed public keys, while
Phase 390 independently established that the real prize key was used with an
uncompressed public key.

Disposition: a real, reproducible, semantically interesting community
construction, but not the puzzle seed. The checksum is expected under the
actual selection family, and standard wallet derivation does not authenticate
it. Arbitrary BIP39 passphrases or hidden derivation paths are excluded because
no source selects them.

## Exact claim oracle

The remaining precise but unauthenticated password/key claims in the lane
were not dismissed from screenshots or reported padding alone. Twenty-two
literal roots were frozen, each tested as literal, SHA-256 hex, and
double-SHA-256 hex against SALPH, COSMIC, P32TRAILING, and URLBLOB under the
current CBC/ECB/stream/AES-Key-Wrap oracle:

| Roots | Materials | Effective decrypt attempts | Hits |
| ---: | ---: | ---: | ---: |
| 22 | 66 | 31,680 | **0** |

## Result

The technique-only residual axis is exhausted as frozen. It found two real
constructions worth reproducing, but neither authenticates and neither closes
a registered gap. The next useful work should move to a genuinely different
evidence source, not expand this gate or tune its keywords around these finds.

## Artifacts

- `tools/gsmg/telegram_executable_recipe_residual_audit.py`
- `tools/gsmg/phase394_telegram_recipe_leads_authentication_audit.py`

