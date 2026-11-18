# Telegram independent verification scope

2026-11-04. Verify the existing November 4 review against the actual export,
without overwriting its result or executing downloaded scripts.

Inputs are the November 4 and October 7 Telegram JSON exports, the November
4 attachments, the existing review/checker, and canonical local puzzle bytes.
Pin all input hashes in the result. Preserve the distinction between original
messages, poster interpretations, and our own derived candidates.

## Existing result replay

Run the existing 21-string/315-material check once with its output redirected
to a separate verification path. Compare its full JSON with the saved result.
Compare every registered WIF and literal string to the actual message, allowing
only explicitly documented case/spacing and recipe-derived forms.

## Supplemental closed set

Before any new oracle result, freeze these additions:

- Msg 76367: exact quoted ASCII string `2iyGJ!4@?uebzY`.
- Msgs 77024 and 77045: each complete posted string, without mutations.
- Msg 77049: exact interior text `Wh 173 R4b B17` and its space-free form.
- Msg 76333: exact 12-word zoo/winner mnemonic as posted. Separately verify
  its BIP39 checksum; a failed checksum is not a reason to drop literal text
  from this finite password test.
- Msgs 77069, 77071, 77253, 77646: exact posted WIF-shaped strings as password
  text, including invalid-WIF strings because they were presented as passwords.
  Recheck 76360's WIF as a control that reaches the already-reproduced chain.

Use the existing 15 raw/SHA/newline forms and existing CBC, stream, ECB,
key-wrap, raw-digest-key and address consumers over the four local targets.
Also check Rabbit/RabbitLegacy under MD5 and SHA-256 using the same finite
material set, with the existing 64/80 printable-byte screen and all four
targets. This is a compatibility screen, not a universal binary-plaintext test.
Test decoded valid WIF scalars directly as keys as well.

For the claimed level-3 passwords (77069/77071/77253/77646), add the three
known solved encrypted stages as targets. Verify the control passwords first.
No typo repair, new suffix, changed casing, wordlist, or derived-key chain.

## Structural and source checks

- Count new rows/media, validate the source hash and creator ID, and compare
  full overlapping objects as well as text. Describe metadata changes honestly.
- Hash every referenced attachment; compare Cosmic bytes, the uploaded
  alleged plaintext, the corrected monologue's normalized letters, the live
  soup, and Decentraland audio with canonical local objects.
- Rebuild the uploaded address-list construction independently from bytes.
  Address validity or equality to another derived list does not authenticate
  an arbitrary plaintext or its intended interpretation.
- Reproduce the reported 83/84-token parses, prime-bit streams and payload
  split. State the relation to source URL bits, without importing a source
  interpretation as a proved selector.
- Give a counterexample to the attachment's universal keyword-square
  confinement claim using the already-established key THEMATRIXHASYOU.
- Inspect the posted knight-walk code statically. Check whether every declared
  input slice has nine distinct symbols despite requiring an injection into
  eight moves. Do not run its DFS or the pasted multiprocessing fragment.
- Index all 238 named entries in the 25,442-page JSON-printout PDF; read the
  relevant source/coverage/result summaries. Do not equate an indexed entry
  with an independently verified computation. Do not repair line-wrapped JSON
  silently or import unvalidated chain artifacts as ground truth.

## Acceptance and stop

Keep the old result unchanged. Report new exact matches only with their full
source and consumer. Strong printable-screen events require inspection;
one-byte padding, prime output length, a repeated derived hash, or an arbitrary
Bitcoin address do not establish a puzzle step. An undisclosed output remains
unverifiable; in particular, message 78605 does not state its byte length.
Stop after this finite replay and source audit, and record residual limitations.
