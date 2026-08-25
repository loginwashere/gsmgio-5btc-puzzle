#!/usr/bin/env python3
"""Phase 410: P32 Family 7 / Post-Phase-340 Seed 3 -- the standalone
solved-vector authoring-toolchain provenance artifact. Consolidates the
2026-08-20 "three-vector KDF profile" investigation pass (which found the
result but was never built into a dedicated, reproducible deliverable)
into a frozen, machine-verified audit of all three authenticated
AES-256-CBC boundaries this puzzle chain has actually solved: Phase 2,
Phase 3, and Phase 3.2.

**Origin:** requested directly by the user as the final deliverable of
`doc/Brainstorms/2026-08-14 - P32 New Attack Surfaces Beyond Text
Recombination.md`'s Candidate family 7 and its duplicate,
`doc/Brainstorms/2026-08-20 - Post-Phase-340 Future Search Portfolio.md`'s
Seed 3. Per the backlog ledger, this is the only ungated deliverable of
comparable scope remaining after Phase 409 closed P32 Family 5 and the
BTCSEED/P91/Z branch was paused (Phase 408). It will not generate a new
password -- it formally closes the last finite backlog item and
establishes the correct provenance ranking for every future oracle run.

**Frozen contract (proposed and approved before this script was
written):**

- inputs: Phase 2 and Phase 3 ciphertexts extracted from the authenticated
  Wayback HTML artifact `doc/html/choiceisanillusion...html`
  (SHA-256 `647744a2957219a4084ede994719124e7445bab1dfdeb68258fbeff2615a8d43`,
  independently reproduced here, not assumed); the Phase 3.2 positive
  vector from the pinned project data (`data.PHASE32_BLOB_B64`/
  `PHASE32_PASSWORD`); the exact known preimages, password digests,
  containers, salts, and recovered plaintexts already established
  elsewhere in this project (`data.VERIFIED_PRIOR_COMMAND_HASHES`, the
  public `puzzlehunt/gsmgio-5btc-puzzle` README's own worked derivations);
- per vector, record: ciphertext/preimage/password/decryption-procedure
  provenance; creator-authored evidence versus community-authored
  reproduction instructions; exact Base64 text layout, wrapping, and
  trailing whitespace; decoded container length, `Salted__` header, salt,
  and ciphertext digest; exact password bytes; derived key/IV digests
  (never the raw key/IV themselves); plaintext digest and structural
  description;
- mechanical verification: `password = SHA256(preimage).hexdigest().
  encode("ascii")` -- lowercase 64-byte ASCII hex; single-round legacy
  `EVP_BytesToKey` with SHA-256; AES-256-CBC and PKCS#7; decrypt each
  original exactly; re-encrypt the recovered plaintext using its original
  salt and reproduce the complete original container byte-for-byte;
- frozen representation controls (all tested under the correct SHA-256
  KDF): lowercase hex, uppercase hex, raw 32-byte digest, lowercase hex
  plus LF, lowercase hex plus CRLF, literal preimage bytes -- only
  lowercase hex is expected to succeed;
- KDF controls for the correct lowercase-hex form: legacy
  `EVP_BytesToKey` with MD5, and with SHA-1 -- both expected to fail;
- explicitly no PBKDF2 iteration sweep: successful exact EVP reproduction
  already establishes compatibility, and an absent PBKDF2 hit cannot
  prove every parameter impossible, so that sweep is out of scope here;
- stopping rule: report either one consistent three-vector profile or an
  explicit incompatibility; do not infer an OpenSSL version, operating
  system, command line, or creator tooling beyond what the authenticated
  artifacts demonstrate.

**Method:** wrote this script, reusing `cb_common.evp_bytes_to_key()` and
`cb_common._load_blob()` verbatim (both already the project's own legacy-
KDF/Salted__-container primitives), `data.PHASE32_BLOB_B64`/
`PHASE32_PASSWORD`/`PHASE32_PLAINTEXT_PREFIX`/
`VERIFIED_PRIOR_COMMAND_HASHES` verbatim -- no primitive or password
constant re-derived. The Phase 2/Phase 3 ciphertexts and their exact
Base64 layout (line length, line-ending bytes, trailing-newline presence)
are extracted directly from the pinned HTML artifact's raw bytes via a
regex over the two `<textarea>` elements, not retyped or reformatted.
`cryptography`'s `Cipher(algorithms.AES(key), modes.CBC(iv))` supplies
both the decryptor and (for the round-trip requirement) the encryptor,
with a hand-rolled strict PKCS#7 pad/unpad matching the project's
existing `p32_sibling_password_audit.py` convention.

**Result:** see `self_test()`'s asserted values for the exact pinned
per-vector provenance/layout facts, the 8-way representation/KDF control
matrix (1 success, 7 failures per vector), and the byte-for-byte
round-trip confirmation.

**Disposition:** decided strictly by the contract's stopping rule -- a
consistent three-vector profile (confirmed) or an explicit
incompatibility (not found). No password search is performed; this is a
provenance/calibration artifact only, ranking future oracle KDF
priority without deleting any lower-ranked variant from `cb_common.
KDF_VARIANTS`.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from cb_common import _load_blob, evp_bytes_to_key  # noqa: E402
from data import (  # noqa: E402
    PHASE32_BLOB_B64,
    PHASE32_PASSWORD,
    PHASE32_PLAINTEXT_PREFIX,
    VERIFIED_PRIOR_COMMAND_HASHES,
)

WAYBACK_ARTIFACT_PATH = REPO_ROOT / "doc" / "html" / (
    "choiceisanillusioncreatedbetweenthosewithpowerandthosewithoutavery"
    "specialdessertiwroteitmyself.html"
)
WAYBACK_ARTIFACT_SHA256 = (
    "647744a2957219a4084ede994719124e7445bab1dfdeb68258fbeff2615a8d43"
)

# Part 7 is the *post-move* FEN the puzzle asks the solver to derive
# ("And now a buddhist is forced to move. What will be the next
# situation?") -- distinct from the pre-move FEN shown on the page itself.
PHASE3_PREIMAGE = (
    "causality" + "Safenet" + "Luna" + "HSM" + "11110"
    + "0x736B6E616220726F662074756F6C69616220646E6F63657320666F206B6E69"
    "7262206E6F20726F6C6C65636E61684320393030322F6E614A2F333020736"
    "56D695420656854"
    + "B5KR/1r5B/2R5/2b1p1p1/2P1k1P1/1p2P2p/1P2P2P/3N1N2 b - - 0 1"
)

VECTORS = {
    "phase2": {
        "label": "Phase 2",
        "preimage": "causality",
        "preimage_source": (
            "community README (puzzlehunt/gsmgio-5btc-puzzle, lines 92-105) "
            "-- narrative password-derivation VALUE not present verbatim in "
            "the pinned Wayback artifact itself, which contains only the "
            "ciphertext and the follow-on Phase-2-vs-Phase-3 riddle text"
        ),
        "expected_password_hex": VERIFIED_PRIOR_COMMAND_HASHES["phase2_causality"],
        "expected_plaintext_prefix": (
            b"The ironic 2name of the keymakers trying to protect the "
            b"current digital powers"
        ),
        "textarea_index": 0,
    },
    "phase3": {
        "label": "Phase 3",
        "preimage": PHASE3_PREIMAGE,
        "preimage_source": (
            "community README (puzzlehunt/gsmgio-5btc-puzzle, lines 172-192) "
            "for parts 1-6 and the worked concatenation; the derivation "
            "STRUCTURE (concatenate 7 parts, SHA-256, AES-256-CBC/Base64) "
            "and part 7's pre-move FEN/riddle text ARE present verbatim in "
            "the pinned Wayback artifact -- the post-move FEN (part 7's "
            "actual value) requires solving a well-known chess problem the "
            "artifact poses but does not itself state the answer to"
        ),
        "expected_password_hex": VERIFIED_PRIOR_COMMAND_HASHES["phase3_parts"],
        "expected_plaintext_prefix": (
            b"What if the merovingian is wrong. What instead of causality "
            b"something else could be ours?"
        ),
        "textarea_index": 1,
    },
    "phase32": {
        "label": "Phase 3.2",
        "preimage": "jacquefrescogiveitjustonesecond" + "heisenbergsuncertaintyprinciple",
        "preimage_source": (
            "pinned project data (data.py's own comment cites the community "
            "README as the source of the two clue-answer tokens); this "
            "project has no separate Wayback-authenticated capture of the "
            "Phase-3.2 entry page pinned alongside the Phase-2/3 artifact"
        ),
        "expected_password_hex": VERIFIED_PRIOR_COMMAND_HASHES["phase32_clues"],
        "expected_plaintext_prefix": PHASE32_PLAINTEXT_PREFIX.encode("ascii"),
        "textarea_index": None,  # sourced from data.PHASE32_BLOB_B64 directly
    },
}

REPRESENTATION_LABELS = (
    "lowercase_hex", "uppercase_hex", "raw_digest",
    "lowercase_hex_lf", "lowercase_hex_crlf", "literal_preimage",
)
KDF_CONTROL_DIGESTS = ("md5", "sha1")


def build_representations(preimage, password_hex):
    digest = bytes.fromhex(password_hex)
    return {
        "lowercase_hex": password_hex.encode("ascii"),
        "uppercase_hex": password_hex.upper().encode("ascii"),
        "raw_digest": digest,
        "lowercase_hex_lf": (password_hex + "\n").encode("ascii"),
        "lowercase_hex_crlf": (password_hex + "\r\n").encode("ascii"),
        "literal_preimage": preimage.encode("utf-8"),
    }


def extract_wayback_textareas(path):
    raw = path.read_bytes()
    matches = re.findall(rb"<textarea[^>]*>(.*?)</textarea>", raw, re.S)
    return matches


def describe_b64_layout(raw_bytes):
    lines = raw_bytes.split(b"\n")
    has_trailing_newline = lines[-1] == b""
    body_lines = lines[:-1] if has_trailing_newline else lines
    line_lengths = sorted({len(line.rstrip(b"\r")) for line in body_lines[:-1]}) if len(body_lines) > 1 else []
    return {
        "total_bytes": len(raw_bytes),
        "line_count": len(body_lines),
        "full_line_lengths": line_lengths,
        "last_line_length": len(body_lines[-1].rstrip(b"\r")) if body_lines else 0,
        "has_cr": b"\r" in raw_bytes,
        "has_trailing_newline": has_trailing_newline,
    }


def pkcs7_unpad(padded):
    pad = padded[-1]
    if not (1 <= pad <= 16 and padded[-pad:] == bytes((pad,)) * pad):
        return None
    return padded[:-pad]


def pkcs7_pad(plaintext):
    pad = 16 - (len(plaintext) % 16)
    return plaintext + bytes((pad,)) * pad


def decrypt_container(salt, ciphertext, password_bytes, digest_name, key_len=32):
    key, iv = evp_bytes_to_key(password_bytes, salt, digest_name, key_len)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    plaintext = pkcs7_unpad(padded)
    return key, iv, plaintext


def encrypt_container(plaintext, salt, password_bytes, digest_name, key_len=32):
    key, iv = evp_bytes_to_key(password_bytes, salt, digest_name, key_len)
    padded = pkcs7_pad(plaintext)
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return b"Salted__" + salt + ciphertext


def run_controls(salt, ciphertext, preimage, password_hex):
    reps = build_representations(preimage, password_hex)
    results = {}
    for label in REPRESENTATION_LABELS:
        _, _, plaintext = decrypt_container(salt, ciphertext, reps[label], "sha256")
        results[f"representation_{label}"] = {
            "kdf_digest": "sha256",
            "padding_valid": plaintext is not None,
            "plaintext_length": len(plaintext) if plaintext is not None else None,
        }
    for digest_name in KDF_CONTROL_DIGESTS:
        _, _, plaintext = decrypt_container(salt, ciphertext, reps["lowercase_hex"], digest_name)
        results[f"kdf_{digest_name}"] = {
            "kdf_digest": digest_name,
            "padding_valid": plaintext is not None,
            "plaintext_length": len(plaintext) if plaintext is not None else None,
        }
    return results


def audit():
    artifact_bytes = WAYBACK_ARTIFACT_PATH.read_bytes()
    artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
    assert artifact_sha256 == WAYBACK_ARTIFACT_SHA256, artifact_sha256

    textareas = extract_wayback_textareas(WAYBACK_ARTIFACT_PATH)
    assert len(textareas) == 2, len(textareas)

    manifest = {}
    for key, spec in VECTORS.items():
        if spec["textarea_index"] is not None:
            raw_b64 = textareas[spec["textarea_index"]]
            layout = describe_b64_layout(raw_b64)
            salt, ciphertext = _load_blob(raw_b64.decode("ascii"))
            source_label = "authenticated Wayback HTML artifact"
        else:
            layout = {
                "total_bytes": len(PHASE32_BLOB_B64),
                "line_count": 1,
                "full_line_lengths": [],
                "last_line_length": len(PHASE32_BLOB_B64),
                "has_cr": False,
                "has_trailing_newline": False,
                "note": "stored pre-flattened in data.py; original page-native wrapping not independently pinned by this audit",
            }
            salt, ciphertext = _load_blob(PHASE32_BLOB_B64)
            source_label = "pinned project data (data.PHASE32_BLOB_B64)"

        password_hex = hashlib.sha256(spec["preimage"].encode("utf-8")).hexdigest()
        assert password_hex == spec["expected_password_hex"], (key, password_hex)
        assert len(password_hex) == 64 and password_hex == password_hex.lower()
        password_bytes = password_hex.encode("ascii")

        key_bytes, iv_bytes, plaintext = decrypt_container(salt, ciphertext, password_bytes, "sha256")
        assert plaintext is not None, f"{key}: primary decrypt lost PKCS7 padding"
        assert plaintext.startswith(spec["expected_plaintext_prefix"]), key

        container_bytes = b"Salted__" + salt + ciphertext
        reencrypted = encrypt_container(plaintext, salt, password_bytes, "sha256")
        roundtrip_matches = reencrypted == container_bytes

        controls = run_controls(salt, ciphertext, spec["preimage"], password_hex)

        manifest[key] = {
            "label": spec["label"],
            "source": source_label,
            "preimage_source": spec["preimage_source"],
            "base64_layout": layout,
            "container_sha256": hashlib.sha256(container_bytes).hexdigest(),
            "container_length": len(container_bytes),
            "ciphertext_length": len(ciphertext),
            "salt_hex": salt.hex(),
            "password_hex": password_hex,
            "key_sha256": hashlib.sha256(key_bytes).hexdigest(),
            "iv_sha256": hashlib.sha256(iv_bytes).hexdigest(),
            "plaintext_length": len(plaintext),
            "plaintext_sha256": hashlib.sha256(plaintext).hexdigest(),
            "plaintext_prefix_matches": True,
            "roundtrip_matches_original_container": roundtrip_matches,
            "controls": controls,
        }

    return {
        "artifact_path": str(WAYBACK_ARTIFACT_PATH.relative_to(REPO_ROOT)),
        "artifact_sha256": artifact_sha256,
        "vector_count": len(manifest),
        "manifest": manifest,
    }


def self_test():
    report = audit()

    assert report["artifact_sha256"] == WAYBACK_ARTIFACT_SHA256
    assert report["vector_count"] == 3
    assert set(report["manifest"].keys()) == {"phase2", "phase3", "phase32"}

    expected = {
        "phase2": {"salt": "06286612d43ed7ed", "container_length": 672, "ciphertext_length": 656},
        "phase3": {"salt": "9fbc451d13d071f4", "container_length": 4112, "ciphertext_length": 4096},
        "phase32": {"salt": "eefc4c5befc1656a", "container_length": 2448, "ciphertext_length": 2432},
    }
    for key, entry in report["manifest"].items():
        assert entry["salt_hex"] == expected[key]["salt"], (key, entry["salt_hex"])
        assert entry["container_length"] == expected[key]["container_length"], key
        assert entry["ciphertext_length"] == expected[key]["ciphertext_length"], key
        assert entry["roundtrip_matches_original_container"] is True, key
        assert entry["plaintext_prefix_matches"] is True, key

        controls = entry["controls"]
        assert len(controls) == 8, key
        successes = [label for label, r in controls.items() if r["padding_valid"]]
        assert successes == ["representation_lowercase_hex"], (key, successes)
        for label, r in controls.items():
            if label == "representation_lowercase_hex":
                assert r["padding_valid"] is True
            else:
                assert r["padding_valid"] is False, (key, label)

    # Pinned Base64 layout facts, extracted directly from the artifact's raw bytes.
    phase2_layout = report["manifest"]["phase2"]["base64_layout"]
    assert phase2_layout["full_line_lengths"] == [64]
    assert phase2_layout["has_trailing_newline"] is True
    assert phase2_layout["has_cr"] is False

    phase3_layout = report["manifest"]["phase3"]["base64_layout"]
    assert phase3_layout["full_line_lengths"] == [64]
    assert phase3_layout["last_line_length"] == 44
    assert phase3_layout["has_trailing_newline"] is False
    assert phase3_layout["has_cr"] is False

    print(
        f"[*] self-test OK: artifact SHA-256 confirmed "
        f"({report['artifact_sha256'][:16]}...); all 3 vectors "
        f"(Phase 2/3/3.2) decrypt exactly under lowercase-hex password/"
        f"legacy-SHA-256-EVP_BytesToKey/AES-256-CBC/PKCS7, matching their "
        f"documented plaintext prefixes; all 3 byte-for-byte round-trips "
        f"(decrypt -> re-encrypt with the original salt) reproduce the "
        f"original container exactly; 24 total representation/KDF control "
        f"tests (8 per vector), exactly 3 successes (one per vector, all "
        f"lowercase_hex/sha256) -- one consistent three-vector profile, no "
        f"incompatibility found"
    )
    return report


def write_manifest(report, path):
    manifest_out = {
        "artifact_path": report["artifact_path"],
        "artifact_sha256": report["artifact_sha256"],
        "vectors": {
            key: {
                k: v for k, v in entry.items()
                if k not in ("controls",)
            } | {
                "control_summary": {
                    label: r["padding_valid"] for label, r in entry["controls"].items()
                }
            }
            for key, entry in report["manifest"].items()
        },
    }
    path.write_text(json.dumps(manifest_out, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    report = self_test() if args.self_test else audit()
    if args.write_manifest:
        out_path = SCRIPT_DIR / "solved_vector_manifest.json"
        write_manifest(report, out_path)
        print(f"[*] wrote {out_path}")
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
