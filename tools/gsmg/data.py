"""Inlined data for the GSMG.io "Cosmic Duality" investigation.

All constants below are copied verbatim from the community's most rigorous public
effort on this puzzle (`halbgott29a/gsmgio-5btc-puzzle` fork: `cb2.py`,
`joint_attack.py`, `faed_base9.py`), re-extracted programmatically (not retyped) to
avoid transcription errors in security-sensitive fixed strings. See
`../../doc/GSMG_PUZZLE.md` for the full writeup of what these represent.
"""

# The two still-undecoded strings from the SalPhaseIon page (9-symbol alphabet a-i).
# dbbi: 91 symbols, IoC 0.151 (structured / key-like)
DBBI = "dbbibfbhccbegbihabebeihbeggegebebbgehhebhhfbabfdhbeffcdbbfcccgbfbeeggecbedcibfbffgigbeeeabe"

# faed: 570 symbols, IoC 0.118 (~uniform / high-entropy payload)
FAED = (
    "faedggeedfcbdabhhggcadcfeddgfdgbgigaaedggiafaecghggcdaihehahbahigceifgbfgefgaifabifagaegeac"
    "gbbeagfggeeggafbacgfcdbeiffaafcidahgdeefghhcggaegdebhhegeghcegadfbdiagefcicggifdcgaaggfbiga"
    "icfbhecaecbceiaicebgbgiecdeggfgegaedggfiiciiififhggcgfgdcdggefcbeeigefibgibggghhfbcgifdehed"
    "fdagicdbhicgaiedaehahghhcihdghfhbiicecbiichihiiigiddgehhdfdchcbafgfbhaheagegecafehgcfggggca"
    "gfhhghbaihidiehhfdeggdgcihggggghadahigigbgecgedfcdggaccdehiicigfbffhggaeidbbeibbeiifdgfdhie"
    "eeieeecifdgdahdiggfhegfiaffiggbcbcehceabfbedbiibfbfdedeehgigfaaiggagbeiichiedifbehgbccahhbi"
    "ibibbibdcbahaidhfahiihic"
)

# Literal base64 "Salted__" AES blob embedded directly in the SalPhaseIon page text
# (no checkerboard decode needed to reach this — see Naddiseo/gsmgio-5btc-puzzle,
# cell 6: the "AES Blob" section). Target for the Phase 0 "last command" probe.
SALPHASEION_BLOB_B64 = (
    "U2FsdGVkX186tYU0hVJBXXUnBUO7C0+X4KUWnWkCvoZSxbRD3wNsGWVHefvdrd9z"
    "QvX0t8v3jPB4okpspxebRi6sE1BMl5HI8Rku+KejUqTvdWOX6nQjSpepXwGuN/jJ"
)

# Third unsolved target, discovered 2026-07-24 during path-3 (command-
# provenance) chat-archive triage -- NOT previously tracked by this project.
# Found repeated verbatim across dozens of independent community chat
# messages (wordlists/gsmg/chat_mined_lines.txt, e.g. lines 7179/28815/58825),
# labeled "3.2.3" and "PHASE3_3.2_CYPHERTEXT_BLOB_AES" there. Confirmed real
# GSMG provenance (not chat noise/a fabricated example) via two independent
# primary sources: it appears verbatim in the OFFICIAL community repo
# puzzlehunt/gsmgio-5btc-puzzle's README, and the actively-maintained fork
# HosterjackAGV/gsmg-5btc-puzzle documents it in detail as "p32_trailing" --
# an 80-byte OpenSSL blob embedded at the END of the already-solved Phase 3.2
# plaintext (i.e. a genuinely separate artifact from SALPHASEION_BLOB_B64/
# COSMIC_BLOB_B64 below, confirmed by salt: b45a5e3d827593ca, vs SALPH's
# 3ab585348552415d and COSMIC's 2d3f6fe06dc950e6). That fork's own extensive
# catalog (~1.5M+ dictionary/thematic/structural attempts, per its
# docs/ATTEMPTS.md) reports it is STILL UNSOLVED as of the fork's latest
# update, and explicitly flags "universally assumed to be aes-256-cbc" as an
# unverified premise for this exact blob -- i.e. independent public
# confirmation of the same cipher/KDF blind spot this project's own path-1
# review found, before either side knew of the other's work.
P32_TRAILING_BLOB_B64 = (
    "U2FsdGVkX1+0Wl49gnWTyiimluu7V3+vl7st0gUt9sWDzNLxDmlPMsDSiuW2a46z"
    "gKlIi8aaqY5gpJPPEzW1n9n3/26qs4zstWtPKF8Zs/BTNN4IiEh4qu18mdC0NAv4"
)

# Fourth candidate target, "urlblob" -- surfaced by the same HosterjackAGV
# fork provenance triage that confirmed P32TRAILING (see FINDINGS.md Phase
# 25), but INDEPENDENTLY re-verified against the real Internet Archive
# Wayback CDX API directly (not just the fork's own docs), 2026-07-24:
#
#   curl "http://web.archive.org/cdx/search/cdx?url=gsmg.io&matchType=domain
#         &output=json&limit=100000&fl=original,timestamp"
#
# turned up a literal hex-encoded Salted__ blob living in a gsmg.io URL
# PATH itself (the page body at that URL is just the site's generic ~36KB
# SPA shell -- confirmed byte-identical, modulo a per-request CSRF token,
# to a second, shorter capture of the same path; the payload was never in
# the response body). Two captures exist:
#   - 2026-01-05 01:59:08 -- the COMPLETE path, 112 raw bytes decoded from
#     hex: "Salted__" + salt 74c974e3f92e64b5 + 96-byte ciphertext (6 clean
#     AES blocks).
#   - 2026-02-07 19:00:55 -- a TRUNCATED duplicate of the same path (only
#     40 raw bytes: header + salt + a 24-byte, non-block-aligned remainder).
#     The fork's own docs cite this later date as the capture timestamp,
#     which is the truncated one, not the complete one -- an inaccuracy
#     this project's own re-verification caught and corrects here.
# The complete-capture hex, decoded, matches this constant byte-for-byte
# (independently cross-checked against the fork's own `demos.js`, which
# embeds the same blob as a UI-demo literal). Unlike SALPH/COSMIC/
# P32TRAILING, there is no official-README or solved-plaintext corroboration
# of this blob's authenticity as a genuine puzzle artifact (the fork's own
# docs call it "orphaned" and report no tested key decrypts it). It retains a
# QUARANTINED provenance label (see cb_common.QUARANTINED_BLOBS), while Phase
# 192 also folds it into default BLOBS so subsequent general-purpose checks
# cover all four known targets. Inclusion does not imply equal corroboration.
URLBLOB_B64 = (
    "U2FsdGVkX190yXTj+S5ktZ9+oipQ3LDUKJ0XbUzp26f5mmlbjQeXtcd5HmWo0raK"
    "WHn10xrl6KJjUgXeMbhRz0OyU09YdlaW08KgH386QfcoT7vMg2UXy/e6YTxDqRnZ"
    "3GaeSCS6umpcrrd9/D4GBw=="
)

# The "Cosmic" blob (larger AES ciphertext referenced by the community as the
# eventual target once dbbi/faed are decoded into a passphrase).
COSMIC_BLOB_B64 = (
    "U2FsdGVkX18tP2/gbclQ5tNZuD4shoV3axuUd8J8aycGCAMoYfhZK0JecHTDpTFe"
    "dGJh4SJIP66qRtXvo7PTpvsIjwO8prLiC/sNHthxiGMuqIrKoO224rOisFJZgARi"
    "c7PaJPne4nab8XCFuV3NbfxGX2BUjNkef5hg7nsoadZx08dNyU2b6eiciWiUvu7D"
    "SATSFO7IFBiAMz7dDqIETKuGlTAP4EmMQUZrQNtfbJsURATW6V5VSbtZB5RFk0O+"
    "IymhstzrQHsU0Bugjv2nndmOEhCxGi/lqK2rLNdOOLutYGnA6RDDbFJUattggELh"
    "2SZx+SBpCdbSGjxOap27l9FOyl02r0HU6UxFdcsbfZ1utTqVEyNs91emQxtpgt+6"
    "BPZisil74Jv4EmrpRDC3ufnkmWwR8NfqVPIKhUiGDu5QflYjczT6DrA9vLQZu3ko"
    "k+/ZurtRYnqqsj49UhwEF9GfUfl7uQYm0UunatW43C3Z1tyFRGAzAHQUFS6jRCd+"
    "vZGyoTlOsThjXDDCSAwoX2M+yM+oaEQoVvDwVkIqRhfDNuBmEfi+HpXuJLPBS1Pb"
    "UjrgoG/Uv7o8IeyST4HBv8+5KLx7IKQS8f1kPZ2YUME+8XJx0caFYs+JS2Jdm0oj"
    "Jm3JJEcYXdKEzOQvRzi4k+6dNlJ05TRZNTJvn0fPG5cM80aQb/ckUHsLsw9a4Wzh"
    "HsrzBQRTIhog9sTm+k+LkXzIJiFfSzRgf250pbviFGoQaIFl1CTQPT2w29DLP900"
    "6bSiliywwnxXOor03Hn+7MJL27YxeaGQn0sFGgP5X0X4jm3vEBkWvtF4PZl0bXWZ"
    "LvVL/zTn87+2Zi/u7LA6y6b2yt7YVMkpheeOL0japXaiAf3bSPeUPGz/eu8ZX/Nn"
    "O3259hG1XwoEVcGdDBV0Nh0A4/phPCR0x5BG04U0OeWAT/5Udc/gGM0TT2FrEzs/"
    "AJKtmsnj31OSsqWb9wD+CoduYY2JrkzJYihE3ZcgcvqqffZXqxQkaI/83ro6JZ4P"
    "ubml0PUnAnkdmnBCpbClbZMzmo3ELZ0EQwsvkJFDMQmiRhda4nBooUW7zXOIb7Wx"
    "bE9THrt3cdZP5uAgVfgguUNE4fZMN8ATEDhdSsLklJe2GvihKuZVA6uuSkWAsK6u"
    "MGo76xpPwYs3eUdLjtANS83a6/F/fhkX1GXs7zbQjh+Inzk8jhEdEogl9jPs/oDj"
    "KjbkUpFlsCWwAZGoeKlmX7c4OGuD5c+FEH+2nYHvYl8y1E/K5SDt9Uocio8XuxbD"
    "ZOzhw7LMSGkD1MZxpDzsCZY1emkSNd88NFj+9U8VssIDDVMYwKMsHKfjc0x5OlzQ"
    "1f6ST0xCkwydDHHGRKKxFC4y6H6fV9sgf9OPK/65z94Rx72+mfvTyizShjxYSRpl"
    "sH9otU4parl8roD0KsVTfXZoYrYXzK6cXBn1BO/OEqWlu++Dd9MiGaUGKd22fXER"
    "qNWoRAKlNn2b6EehD2D8WaAoliPURjkB0Lb/FpP9unI93Twg6NxBXAj734nctukR"
    "b3kE08RydJV70eJsvEftF5hbED4HacGx9pzisaSz6t9AKiuSoF6uoCtlTIYatyfZ"
    "kQA4wg50hAJqTynOQ09ArRHEchtB/7uvWZSBGJ7+zlzRGKx99P3oDZD+Y5D8bmUs"
    "3PV6FnAp+IRSlnsQ6hChkwBoQUcngcfGSkBRvmGjsGercCetRRwBOfh9fbX2ruw4"
    "mzRYrGnz9eBtepkJXDRjD6yvhNfQMCSkm6l9zMWxKvFbv5g2ae2SLrEt/x3MP2/G"
)

# ── Known-good validation vector (Phase 3.2.2, already publicly solved) ──────
# Decoding this numeric string with alphabet ALPHA_322 and escapes (1,4) must
# yield the known answer below. Used as a startup self-test in cb_common.py so a
# porting bug can't silently cause false negatives in every other script here.
VALIDATION_NUM = (
    "1516594312197240916917121375895181314154313141242815419131218121943312117161713714911091"
    "6631213131281491109166131412199114371612126021664313711154112"
)
ALPHA_322 = "FUBCDORA.LETHINGKYMVPS.JQZXW"
VALIDATION_ESCAPES = (1, 4)
VALIDATION_ANSWER_PREFIX = "INCASEYOUMANAGE"
VALIDATION_ANSWER = (
    "INCASEYOUMANAGETOCRACKTHISTHEPRIVATEKEYSBELONGTOHALFANDBETTERHALF"
    "ANDTHEYALSONEEDFUNDSTOLIVE"
)

# SHA-256 outputs explicitly computed and then used by the solved puzzle chain.
# Each value and its exact preimage is documented in the original public
# `puzzlehunt/gsmgio-5btc-puzzle` README:
#   - phase2_causality = SHA256("causality"), used as the Phase 2 AES password;
#   - phase3_parts = SHA256(the exact seven-part concatenation), used for Phase 3;
#   - phase32_clues = SHA256(the three normalized clue answers), used for Phase 3.2;
#   - salphaseion_entry = SHA256(the puzzle banner text + BTC address), used as the
#     URL slug that enters SalPhaseIon/Cosmic Duality.
#
# These are actual prior command states, unlike hashes newly derived from stage URL
# slugs after the fact. The exact preimages for the two long values are retained in
# the public README and independently reproduce the constants.
VERIFIED_PRIOR_COMMAND_HASHES = {
    "phase2_causality": "eb3efb5151e6255994711fe8f2264427ceeebf88109e1d7fad5b0a8b6d07e5bf",
    "phase3_parts": "1a57c572caf3cf722e41f5f9cf99ffacff06728a43032dd44c481c77d2ec30d5",
    "phase32_clues": "250f37726d6862939f723edc4f993fde9d33c6004aab4f2203d9ee489d61ce4c",
    "salphaseion_entry": "89727c598b9cd1cf8873f27cb7057f050645ddb6a7a157a110239ac0152f6a32",
}
PRIOR_COMMAND_HASHES = VERIFIED_PRIOR_COMMAND_HASHES

# ── Known-positive AES/KDF ground truth (2026-07-23) ─────────────────────────
# The Phase 3.2 blob, copied verbatim from the primary public
# `puzzlehunt/gsmgio-5btc-puzzle` README (fetched fresh via `gh api`, not
# retyped). Password is SHA256("jacquefrescogiveitjustonesecond
# heisenbergsuncertaintyprinciple") = phase32_clues above. This is the only
# known-plaintext AES vector available for this project's actual decrypt code
# path (base64 -> Salted__ header -> legacy EVP_BytesToKey -> AES-256-CBC ->
# PKCS7 unpad), independent of the still-unsolved SALPH/COSMIC blobs. Used as
# a startup self-test in cb_common.py, the same way VALIDATION_NUM guards the
# checkerboard decoder.
#
# Decrypting this with the real oracle code found that its printable-ASCII
# ratio is only ~0.598 (it legitimately embeds a CP437/high-bit-set garbled
# sub-block as part of the puzzle's own multi-stage design) -- well below the
# >0.85 threshold this project's AES oracle required until this fix. That
# threshold would have silently rejected this exact, byte-for-byte-verified
# correct decryption. See cb_common.py's printable_z_score().
PHASE32_BLOB_B64 = (
    "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"
)
PHASE32_PASSWORD = VERIFIED_PRIOR_COMMAND_HASHES["phase32_clues"]
PHASE32_PLAINTEXT_PREFIX = "I've been waiting for you. You have many questions,"
