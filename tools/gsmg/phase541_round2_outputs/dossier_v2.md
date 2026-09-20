# GSMG.IO 5 BTC puzzle: artifact dossier

This dossier holds the puzzle's own artifacts and nothing else. There is a 5 BTC
prize at address 1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe. The last stage is described
in the puzzle's own text as a regular Bitcoin private key ("half and better half").

## Stage 0: the first image
A 14x14 pixel-art grid (a white rabbit). Reading it from the top-left counter-clockwise
in a spiral, classifying black/blue as 1 and white/yellow as 0, gives the URL
`gsmg.io/theseedisplanted`. The grid has 24 coloured cells (15 blue, 9 yellow), which
fall on the byte boundaries of that URL, and exactly one off-white pixel (254,254,254).

## Stage 1: gsmg.io/theseedisplanted
Eight coloured icon fragments: war+ning, ca, dig i, lo (in a lock), crypto/gic, n you, t.
They resolve to "WARNING", "CAN YOU DIG IT" and the song "The Warning" by Logic. The
lyric line used as the passphrase was
`theflowerblossomsthroughwhatseemstobeaconcretesurface`. It unlocks the next page.

## Stage 2: the Phase 2/3 page
The page URL is `gsmg.io/choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutaveryspecialdessertiwroteitmyself`.
The riddle is the sentence in the URL. Its answer, `causality`, is hashed with SHA-256; the
hex digest is the AES-256-CBC passphrase (OpenSSL, base64) for the next material.

## Stage 3: seven-part password
Seven answers concatenated with preserved case and no spaces, then SHA-256:
`causality`, `Safenet`, `Luna`, `HSM`, `11110`, a hex string decoding to text, and the
post-move chess FEN `B5KR/1r5B/2R5/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 b - - 0 1`.

## Stage 3.2: three clues
`jacquefresco`, `giveitjustonesecond` (Alice: "How long is forever? White Rabbit:
Sometimes, just one second."), `heisenbergsuncertaintyprinciple`. Concatenated, then
SHA-256, then used as the AES passphrase. Decrypted text, verbatim:

I've been waiting for you. You have many questions, and although the process has altered your consciousness, you remain irrevocably human. Ergo, some of my answers you will understand, and some of them you will not. Concordantly, while your first question may be the most pertinent, you may or may not realize it is also irrelevant.

... am I here? Wake up, you... I've designed you a beautiful strategic position. One for one, four for one.

[a block of box-drawing characters, an EBCDIC 1141 ciphertext]

[a 149-digit decimal string]

Raising the stakes without extra chances of winning. A fubcd-king & oracle-queen, thingky mvps, on a sad board but as wide as the first one seen.

[a base64 OpenSSL blob, "Salted__", unresolved]

### Stage 3.2.1 output (EBCDIC 1141 then Beaufort with key THEMATRIXHASYOU)
```
YOUR LIFE IS THE SUM OF A REMAINDER OF AN UNBALANCED EQUATION INHERENT TO THE PROGRAMMING OF THIS PUZZLE 
YOU ARE THE EVENTUALITY OF AN ANOMALY WHICH DESPITE MY SINCEREST EFFORTS I HAVE BEEN UNABLE TO ELIMINATE 
FROM WHAT IS OTHERWISE A HARMONY OF MATHEMATICAL PRECISION WHILE IT REMAINS A BURDEN TO SEDULOUSLY AVOID IT 
IT IS NOT UNEXPECTED AND THUS NOT BEYOND A MEASURE OF CONTROL WHICH HAS LED YOU INEXORABLY HERE YOU 
YOU HAVEN'T ANSWERED MY QUESTION ME QUITE RIGHT INTERESTING THAT WAS QUICKER THAN THE OTHERS PLEASE IF YOU 
FIND A WAY TO COMPLETE THE LAST PART OF THE PUZZLE TAKE THE PRIVATE KEY YOUVE EARNED IT BUT PLEASE TAKE 
THIS TO HEART THAT WHAT A WISEMAN ABOVE HINTED AT IS WORTH HUNDRED FOURTY OF THE INVESTMENT THAT'S 
WHAT US GUYS AT GSMG ARE TRYING TO ACCOMPLISH IN THE END PLEASE JUST HELP US BUILD IT INSTEAD OF JUST 
WAISTING YOUR LIFETIME BY HUNTING FOR WORTHLESS PRICES AND THROPHIES LIKE THIS I'M SORRY TO 
TELL YOU THAT YOUVE COME THIS FAR BUT YOU'LL NEVER FINISH THE LAST TASK I EXPECT YOU TO SAY BULLSHIT 
WELL DENIAL IS THE MOST PREDICTABLE OF ALL HUMAN RESPONSES BUT REST ASSURED THIS WILL NOT BE THE LAST TIME 
I HAVE DESTROYED A RESTLESS SOUL AND I HAVE BECOME EXCEEDINGLY EFFICIENT AT IT THE FUNCTION OF THE YOU IS 
NOW TO RETURN TO THE SOURCE CODES ALLOWING A TEMPORARY DISSEMINATION OF THE CODE YOU HOPEFULLY CARRY 
REINSERTING THE PRIME BASICS AFTER WHICH YOU WILL BE REQUIRED TO SELECT FROM OVER TWENTY-THREE CIPHERS 
SIXTEEN ENCRYPTIONS AND OR SEVEN INTERTWINED PASSWORDS TO FIND THE ACTUAL PRIVATE KEYNOTE THAT ALSO 
BRUTE FORCING MIGHT BE REQUIRED FAILURE TO COMPLY WITH THIS PROCESS WILL RESULT IN A CATACLYSMIC 
SYSTEM CRASH KILLING YOUR WILLPOWER WHICH COUPLED WITH THE EXTERMINATION OF YOUR WILL TO LIVE AND WILL 
ULTIMATELY RESULT IN THE EXTINCTION OF THE ENTIRENESS OF YOURSELF SELF GOOD LUCK NEVERTHELESS I REALLY
HOPE YOURE THE ONE CIAO BELLA O 
```

### Stage 3.2.2 output (keyed straddling checkerboard, alphabet FUBCDORA.LETHINGKYMVPS.JQZXW, escape digits 1 and 4)
IN CASE YOU MANAGE TO CRACK THIS THE PRIVATE KEYS BELONG TO HALF AND BETTER HALF AND THEY ALSO NEED FUNDS TO LIVE

## Route to the final page
`SHA-256("GSMGIO5BTCPUZZLECHALLENGE" + "1GSMG1JC9wtdSwfwApgj2xcmJPAwx7prBe")` =
`89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32`, which is the URL path
of the final page (title "SalPhaseIon"; a second page, "Cosmic Duality", exists).

## The final page (SalPhaseIon): stream layout, in order
1. `DBBI`, 91 letters over a-i: `dbbibfbhccbegbihabebeihbeggegebebbgehhebhhfbabfdhbeffcdbbfcccgbfbeeggecbedcibfbffgigbeeeabe`
2. a binary block that decodes to the text `matrixsumlist`
3. `FAED`, 570 letters over a-i: `faedggeedfcbdabhhggcadcfeddgfdgbgigaaedggiafaecghggcdaihehahbahigceifgbfgefgaifabifagaegeacgbbeagfggeeggafbacgfcdbeiffaafcidahgdeefghhcggaegdebhhegeghcegadfbdiagefcicggifdcgaaggfbigaicfbhecaecbceiaicebgbgiecdeggfgegaedggfiiciiififhggcgfgdcdggefcbeeigefibgibggghhfbcgifdehedfdagicdbhicgaiedaehahghhcihdghfhbiicecbiichihiiigiddgehhdfdchcbafgfbhaheagegecafehgcfggggcagfhhghbaihidiehhfdeggdgcihggggghadahigigbgecgedfcdggaccdehiicigfbffhggaeidbbeibbeiifdgfdhieeeieeecifdgdahdiggfhegfiaffiggbcbcehceabfbedbiibfbfdedeehgigfaaiggagbeiichiedifbehgbccahhbiibibbibdcbahaidhfahiihic`
4. a decimal block that decodes to `lastwordsbeforearchichoice`
5. a decimal block that decodes to `thispassword`
6. the literal text `sha256 our first hint is your last command`
7. the first half of a base64 OpenSSL "Salted__" AES blob (called SALPH), a binary block
   that decodes to `enter`, then the second half of the blob
8. the raw text `shabefanstoo`

A reversed binary message on the page decodes to the ordered phrase:
`yellowblueprimes matrixsumlist lastwordsbeforearchichoice yinyang wewontgiveawaythepassword itsinfrontofyoureyesbutyourenotseeingit verylaststepisatruegiveaway promised`

## The unsolved problem and how answers are checked
A passphrase for the SALPH blob (and the other encrypted blobs on the final pages) is
unknown. An automatic checker will try each candidate you give as a base phrase, in
several forms: the raw text, lowercase, spaces removed, the SHA-256 hex digest of these,
with and without a trailing newline. So give the phrase itself, not a hash. Earlier
passphrases were: a lyric line (Stage 1); the SHA-256 of a one-word riddle answer
(Stage 2); the SHA-256 of concatenated clue answers (Stages 3, 3.2). Every earlier
answer was a word or phrase recognizable from the clue text and general culture.

## Derived facts (reconstructions from the artifacts above; use them, verify if you like)

**D1. DBBI has a prime-position scaffold.** Read DBBI as tokens at logical positions
1, 2, 3, ...: at a prime logical position the token is `b` (one character) or `be`
(two characters); at every other position it is one character. Exactly two complete
parses of the 91 characters exist: an 83-token parse (23 hosts: 15 `b` and 8 `be`) and
an 84-token parse (23 hosts: 16 `b` and 7 `be`; its last `e` is an unhosted token).
Raw 1-based host positions, 83-token parse (31 positions):
`2 3 5 7 11 12 14 18 20 24 25 31 32 34 40 44 46 50 51 57 63 65 66 72 73 77 79 85 86 90 91`
84-token parse (30 positions): the same list without 91. The non-host symbols in stream order:
- 83-token payload (60): `difhccgihaeeihggegebgehhehhfafdhffcdbfcccgfeggecdcifffgigeea`
- 84-token payload (61): `difhccgihaeeihggegebgehhehhfafdhffcdbfcccgfeggecdcifffgigeeae`

**D2. The first image supplies the same structure.** Its 24 coloured cells read in spiral
order, plus the off-white cell (`F`, the single FEFE pixel, at 0-based spiral index 163, inserted
before colour object 21), give a 25-event sequence of colours `BBBBYBBBYYBBBBYBBYYBFYYBY`
(B blue, Y yellow). The 84-token parse's host kinds (blue = `b`, yellow = `be`) match events
1 to 23 with events 22 and 25 omitted (the FEFE cell stands for byte 21). Events
`[rank, kind, source byte, character, colour, spiral index (0-based), row, column]`:
`[[1, "ordinary_endpoint", 1, "g", "B", 7, 8, 1], [2, "ordinary_endpoint", 2, "s", "B", 15, 14, 3], [3, "ordinary_endpoint", 3, "m", "B", 23, 14, 11], [4, "ordinary_endpoint", 4, "g", "B", 31, 9, 14], [5, "ordinary_endpoint", 5, ".", "Y", 39, 1, 14], [6, "ordinary_endpoint", 6, "i", "B", 47, 1, 6], [7, "ordinary_endpoint", 7, "o", "B", 55, 5, 2], [8, "ordinary_endpoint", 8, "/", "B", 63, 13, 2], [9, "ordinary_endpoint", 9, "t", "Y", 71, 13, 10], [10, "ordinary_endpoint", 10, "h", "Y", 79, 8, 13], [11, "ordinary_endpoint", 11, "e", "B", 87, 2, 11], [12, "ordinary_endpoint", 12, "s", "B", 95, 2, 3], [13, "ordinary_endpoint", 13, "e", "B", 103, 10, 3], [14, "ordinary_endpoint", 14, "e", "B", 111, 12, 9], [15, "ordinary_endpoint", 15, "d", "Y", 119, 7, 12], [16, "ordinary_endpoint", 16, "i", "B", 127, 3, 8], [17, "ordinary_endpoint", 17, "s", "B", 135, 7, 4], [18, "ordinary_endpoint", 18, "p", "Y", 143, 11, 8], [19, "ordinary_endpoint", 19, "l", "Y", 151, 6, 11], [20, "ordinary_endpoint", 20, "a", "B", 159, 4, 5], [21, "fefe", 21, "n", "F", 163, 8, 5], [22, "ordinary_endpoint", 21, "n", "Y", 167, 10, 7], [23, "ordinary_endpoint", 22, "t", "Y", 175, 5, 10], [24, "ordinary_endpoint", 23, "e", "B", 183, 9, 6], [25, "ordinary_endpoint", 24, "d", "Y", 191, 6, 7]]`
Yellow read as 1 and blue as 0 over the 24 cells gives the binary value 574061, which is prime.

**D3. The same walk, applied to the Stage 3.2.2 answer.** Selecting the 83-token host
positions above from the 91-character answer gives `ncsyangcahiriasogaleafayanestve`; the 60
remaining letters are `iaeoumaetorcktsthepvtekeybelntohfandbtterhlndthelsoedfundoli`; one-character hosts give `ncsygcaasogeane`,
two-character hosts give `anhirialfayastve` (16 letters; the one-character rail has 15, of which 14 are
blue and one is the FEFE cell, so 7 blue pairs). The numbers 23 (hosts), 16 and 7 also appear in the
Stage 3.2.1 text as 23 ciphers, 16 encryptions and 7 passwords.

**D4. Matrix placement.** Placing the 84-token parse's host chunks backwards from their
image endpoints on the 14x14 spiral, with values a=1..i=9 and `be`=25, and summing rows, gives
row sums `[34, 51, 37, 36, 30, 44, 62, 58, 32, 34, 41, 15, 56, 13]`. Rendered as letters A0 mod 26 (A=0) this is `IZLKESKGGIPPEN`.
The unhosted final `e` stays unplaced. Hosts only give `BECCBZBDECZCBE`
(row sums [27, 4, 2, 2, 27, 25, 27, 29, 4, 2, 25, 2, 27, 4]); payload only gives
`HVJIDTJDCGQNDJ` (row sums [7, 47, 35, 34, 3, 19, 35, 29, 28, 32, 16, 13, 29, 9]).

**D5. A Bifid reading of FAED.** Take DBBI's nine symbols in order of first appearance,
then the rest of the alphabet without J, as a 5x5 square: `DBIFHCEGAKLMNOPQRSTUVWXYZ`. Bifid-decrypt the whole
570-letter FAED as one block (row-column coordinates): the 570 letters begin `BTCSEED`, then
`DEOEMCKEADHBSCHDKBDCSDKDVBXCPCOCHCRDICIBQEEBDDBCNDSBDCPDGCPDNCNCSESCGDDCLENBMCUDUCQCACDELDZELCMEFDFESDODWCKBYCUBW...`. The only `Z` is at 0-based index 97. The letters `B C D E` make up 57% of the output.

**D6. Sizes and counts.** DBBI = 91 = 7x13 = 1+2+...+13. FAED = 570 = 6x91 + 24 = 2x285.
`matrixsumlist` decodes from a 104-bit block (13x8); DBBI plus that block is 195 = 14x14 - 1.
FAED letter counts: {"a": 54, "b": 49, "c": 52, "d": 49, "e": 69, "f": 57, "g": 107, "h": 58, "i": 75}. FAED's best-scoring escape pair (for a
straddling checkerboard) is `g,i`; DBBI's is `b,e`.

## Already tested (do not just repeat these)

Password products from the strings above and their recombinations; DBBI-derived coordinates
and positions as passwords; the matrix placement and its row sums as word indices into the
Architect scene; numeric-text generators and arithmetic position functions over the payload; the
payload and whole DBBI as base-9 private-key scalars under every digit bijection; FAED's six
91-symbol lanes read through the host masks; joint DBBI plus FAED splice and shared-board
decodes; straddling-checkerboard, Bifid and VIC decodes of FAED across escape pairs, boards and
widths; the Bifid tail as key or seed material. Propose something outside these.

## Interface for operation proposals

A proposal is a Python function that receives a dict `data` and returns a list of strings.
`data` keys: `DBBI`, `FAED`, `ANSWER_322` (the 91-letter answer), `ARCH_321` (the Stage 3.2.1
text), `PAGE_STRINGS` (dict of the page's decoded strings and the macro phrase list), `P83`, `P84`,
`MASK31`, `MASK30`, `EVENTS`, `MATRIX_SELECTION_A` (dict `row_sums`, `output`), `BTCSEED_DECODE`.
Rules: standard library only, and only these imports: math, itertools, string, re, collections,
hashlib, base64, binascii, functools, struct, operator, textwrap. No files, network, `eval`, `exec`,
`open`, `getattr`, `type`, or names or strings containing two underscores. It must finish in 20
seconds and return at most 3,000 strings. The first 1,000 returned strings (200 characters or fewer)
are tried as passphrases; all returned strings are scanned for private-key shapes (64-hex, WIF, BIP39
mnemonic, 64 raw bytes) and checked against the prize address, the halving address and their EC neighbors. Each proposal must say which check would confirm
it and which earlier solved stage used a similar operation.
