"""Phase 478 dedicated adapter for `cosmic_raw_digest_checkpoint_audit.py`.

That file is a `direct-crypto-bypass` construction: it decrypts directly
via `cryptography.hazmat` (`Cipher(algorithms.AES(key), modes.CBC(iv))`)
inside its own local `decrypt(password, digest_name)` function, never
going through any of `cb_common`'s recognized oracle entrypoints, so the
standard `phase478_harvest_driver.py` interception (which only patches
`cb_common`) cannot see its candidates at all.

This adapter intercepts that local boundary instead. It reproduces --
does not reinterpret -- exactly two pieces of the file's own historical
candidate-generation logic:

1. The two "default" password forms `audit()` itself builds
   (`xor_sha256_digests()`'s raw 32 bytes, and its 64-character lowercase-
   hex rendering), each historically submitted under both `digest_name`
   values ("md5", "sha256").
2. The complete, frozen 210-member "published uniqueness family"
   (`published_uniqueness_family_report()`, `P5_CANDIDATES x
   P6_CANDIDATES x P7_CANDIDATES = 7 x 5 x 6 = 210`), which itself calls
   the same local `decrypt` once per member, always under `digest_name =
   "md5"`.

It deliberately does NOT call the file's own `audit()`, `main()`, or
`downstream_report()`/`matrix_report()`/`compressed_p2pkh()` chain: those
consume a real decrypted `payload` (EC scalar derivation, base58check,
103x103 bit-matrix indexing) and would raise on the synthetic empty
payload this adapter's stub `decrypt` returns, potentially aborting
`audit()` before it ever reaches `published_uniqueness_family_report()`
(the two calls are sequential in `audit()`'s own body, in that order) --
a silent under-count, not a crash-safety nicety. Calling the two
candidate-generating pieces directly, independent of `audit()`, sidesteps
that failure mode entirely and is unaffected by it either way.

No AES execution (the stub `decrypt` never touches `Cipher`/`algorithms`).
No SHA-256 of any recorded candidate byte string (the file's OWN internal
`hashlib.sha256` calls inside `xor_sha256_digests` are historical
candidate-CONSTRUCTION logic -- exactly analogous to any other script's
"hash a token to build a password" step -- not Phase 478 scoring, and are
therefore untouched and allowed to run normally).

CAPTURE FILE OWNERSHIP: same contract as `phase478_harvest_driver.py` --
the `PHASE478_CAPTURE_FILE` environment variable names a path the CALLER
(the harvester) creates, sets, reads back, and deletes; this adapter only
ever appends to it and never includes candidates in its own JSON output.
This adapter doesn't fork, so it isn't at risk of the cross-process
capture-loss bug the standard driver's own docstring describes, but it
shares the same ownership contract for consistency and so the harvester
never needs to know which kind of driver produced a given result.

Usage: phase478_adapter_cosmic_raw_digest.py <target_path> <recipe_json>
(recipe_json is accepted for interface symmetry with the standard driver
but is not otherwise used -- this adapter's behavior is fully bespoke and
pinned by this file's own content, not by caller-supplied parameters.)
"""

import base64
import inspect
import json
import os
import runpy
import sys

CAPTURE_FILE_ENV = "PHASE478_CAPTURE_FILE"


def _append_capture_line(entry: dict) -> None:
    path = os.environ[CAPTURE_FILE_ENV]
    line = (json.dumps(entry) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


def _make_recorder():
    def _recorder(password, digest_name):
        if isinstance(password, str):
            password = password.encode("utf-8")
        caller = inspect.stack()[1]
        _append_capture_line({
            "entrypoint": "cosmic_raw_digest_checkpoint_audit.decrypt",
            "caller_file": caller.filename,
            "caller_line": caller.lineno,
            "caller_function": caller.function,
            "digest_name": digest_name,
            "bytes_b64": base64.b64encode(password).decode("ascii"),
        })
        # Shape matches the real decrypt()'s return dict closely enough
        # for published_uniqueness_family_report's own `if
        # result["valid_padding"]:` check to run safely without ever
        # reporting a (necessarily fabricated) hit.
        return {
            "digest": digest_name,
            "padding_length": 0,
            "valid_padding": False,
            "raw_length": 0,
            "raw_sha256": "",
            "payload": b"",
            "payload_length": 0,
            "payload_sha256": "",
        }
    return _recorder


def _submit_default_forms(module_globals):
    # Reproduces audit()'s own password_forms construction (its own
    # xor_sha256_digests() over the default TOKENS, raw and hex-rendered),
    # each historically submitted under both digest_name values -- without
    # calling audit() itself, which also runs the crash-prone downstream
    # chain on the real (here, fabricated/empty) payload. `module_globals`
    # must be a target function's own `__globals__` (see `main`, below) --
    # not runpy.run_path's returned namespace copy -- so that the `decrypt`
    # patch is visible here.
    xor_sha256_digests = module_globals["xor_sha256_digests"]
    decrypt = module_globals["decrypt"]
    raw_password = xor_sha256_digests()
    password_forms = {"raw32": raw_password, "hex64": raw_password.hex().encode()}
    for _form_name, password in password_forms.items():
        for digest_name in ("md5", "sha256"):
            decrypt(password, digest_name)


def main():
    if len(sys.argv) != 3:
        print(json.dumps({"error": "usage: phase478_adapter_cosmic_raw_digest.py <target_path> <recipe_json>"}))
        sys.exit(1)
    target_path = sys.argv[1]
    # recipe_json accepted for interface symmetry; unused.

    if CAPTURE_FILE_ENV not in os.environ:
        raise RuntimeError(
            f"{CAPTURE_FILE_ENV} must be set by the caller before launching this adapter"
        )

    # CAUTION: `runpy.run_path` returns a COPY of the execution namespace,
    # not the live dict the target's own functions actually close over as
    # `__globals__` -- patching the returned dict is silently invisible to
    # `published_uniqueness_family_report`'s own internal call to
    # `decrypt`. The patch must go through a function object's own
    # `__globals__` instead (found via a failing synthetic test whose
    # fixture `decrypt` deliberately raises if ever really invoked).
    module_stem = target_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    namespace = runpy.run_path(target_path, run_name=f"phase478_isolated_{module_stem}")
    module_globals = namespace["published_uniqueness_family_report"].__globals__
    module_globals["decrypt"] = _make_recorder()

    status = "ok"
    error = None
    try:
        _submit_default_forms(module_globals)
        module_globals["published_uniqueness_family_report"]()
    except BaseException as exc:  # noqa: BLE001 -- must capture and report, never crash silently
        status = "harvest_failed"
        error = f"{type(exc).__name__}: {exc}"

    # No "candidates" key here by design: the caller owns the capture
    # file and reads it directly, exactly as for the standard driver.
    out = {"status": status, "error": error}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
