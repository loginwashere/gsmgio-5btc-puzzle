"""Phase 478 harvest driver -- runs INSIDE an isolated subprocess, once per
target file, against a filesystem view that is itself a materialized
pinned-commit snapshot (the caller is responsible for that isolation; this
driver only assumes `cwd` and `sys.path[0]` already point into it).

Responsibility: patch cb_common's recognized oracle entrypoints to pure
recorders, execute the target file's own code exactly as specified by its
frozen invocation recipe (a CLI argv replay, or a direct call to a named
entry function that bypasses the file's own `__main__` guard), and dump
every captured candidate byte string -- plus its exact call site -- to
stdout as JSON. Performs no cryptography, no network access, and writes to
no file other than what the caller already prepared and this driver's own
disposable capture file (below), which never leaves this process's scope.

Not imported directly; invoked by
`phase478_matrixsumlist_candidate_harvester.py` via `subprocess.run`.

Usage: phase478_harvest_driver.py <target_path> <recipe_json>

recipe_json is a JSON object:
    {"mode": "cli", "argv": [...]}
    {"mode": "call", "entry_function": "name", "argv": [...]}

`mode: call` additionally accepts `attr_overrides`: a mapping of
module-level attribute name to a REPOSITORY-RELATIVE path string, applied
to the TARGET's own namespace after import (so its own `if __name__ ==
"__main__":` guard has not yet fired) and before `entry_function` is
called. Use this when the target itself reads the attribute at CALL time
(a bare global lookup, e.g. inside `argparse.add_argument(..., default=
SOME_NAME)` evaluated when `main()` runs) -- it does nothing for a value
already baked into a function's own `__defaults__` at DEFINITION time
(`def f(path=SOME_NAME):`), since that capture already happened during
`runpy.run_path`, before this override is ever applied.

Either mode additionally accepts `dependency_overrides`: a mapping of
`{"module.name": {"ATTR": "repo/relative/path"}}`, applied by pre-
importing each named module and patching its own attribute BEFORE the
target is executed at all. Because Python caches imports in
`sys.modules`, when the target's own `from module.name import ATTR`
line runs, it binds to the ALREADY-PATCHED value. This is the mechanism
for a dependency-remap adapter whose default is baked in as a function's
own default-argument value (where `attr_overrides` cannot help) or lives
in a module the target imports rather than defines itself -- e.g.
replacing a target's or its dependency's hardcoded, unpinned,
out-of-repository path constant with the pinned snapshot's own tracked
equivalent, without editing any historical code.

CROSS-PROCESS CAPTURE (found only by running real targets, not by
inspection): several locked files parallelize their own AES checking via
`concurrent.futures.ProcessPoolExecutor`. On Linux this forks worker
processes AFTER `_patch_cb_common` has already run, so the patched
`cb_common` functions ARE correctly inherited and DO run inside workers
(no real cryptography leaks in) -- but a plain in-memory `RECORDED` list
is not shared across a fork: each worker's appends land in that worker's
own copy-on-write memory and vanish when it exits, so the parent process
that serializes the result sees nothing, even though every oracle call
genuinely happened. The fix is a disposable, process-agnostic capture
file: every recorder invocation -- main process or forked worker alike --
independently opens the same path with `O_APPEND` and writes ONE complete
JSON line in a single `os.write` call, which is atomic on POSIX for
writes at or under `PIPE_BUF` (4096 bytes on Linux; every candidate line
here is far smaller).

CAPTURE FILE OWNERSHIP: the path is named via the `PHASE478_CAPTURE_FILE`
environment variable, which the CALLER (this project's harvester, never
this driver itself) creates, sets before launching this process (so any
forked worker inherits it), and deletes afterward -- deliberately, so
that a killed-on-timeout subprocess (which never reaches its own `finally`
blocks) cannot leak the file. This driver only ever appends to a path it
did not create and will not remove; it does not read the file back or
include candidates in its own JSON output at all -- the caller reads the
shared file directly once this process has exited, by whatever means
(including a SIGKILL after a timeout).
"""

import base64
import importlib
import inspect
import json
import os
import runpy
import sys
from pathlib import Path

CAPTURE_FILE_ENV = "PHASE478_CAPTURE_FILE"

# Filenames whose frames are never the "real" caller for provenance
# purposes: cb_common.py's own str-argument wrappers (aes_try_open,
# aes_try_open_ecb, ...) forward to the patched _bytes/raw entrypoints via
# a plain in-module call, so the immediate caller frame (stack()[1]) is
# cb_common.py itself, not the target script that actually decided to
# submit this candidate. Walk past any such frame, and past this driver's
# own frames, to the first frame that is neither.
_INTERNAL_BASENAMES = {"cb_common.py", os.path.basename(__file__)}


def _originating_frame():
    for frame_info in inspect.stack()[1:]:
        if os.path.basename(frame_info.filename) not in _INTERNAL_BASENAMES:
            return frame_info
    # Every frame was internal (should not happen in practice -- something
    # outside cb_common/this driver must have started the call chain).
    # Fall back to the immediate caller rather than crashing.
    return inspect.stack()[1]


def _append_capture_line(entry: dict) -> None:
    """Append one JSON line to the shared capture file, atomically, from
    whichever process (main or a forked worker) happens to call this."""
    path = os.environ[CAPTURE_FILE_ENV]
    line = (json.dumps(entry) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


def _make_recorder(entrypoint_name):
    def _recorder(candidate, *args, **kwargs):
        if isinstance(candidate, str):
            candidate = candidate.encode("utf-8")
        caller = _originating_frame()
        _append_capture_line({
            "entrypoint": entrypoint_name,
            "caller_file": caller.filename,
            "caller_line": caller.lineno,
            "caller_function": caller.function,
            "bytes_b64": base64.b64encode(candidate).decode("ascii"),
        })
        return []
    return _recorder


def _patch_cb_common():
    import cb_common

    for name in (
        "aes_try_open_bytes",
        "aes_try_open_stream_bytes",
        "aes_try_open_ecb_bytes",
        "aes_keywrap_try_open_bytes",
        "raw_key_try_open",
    ):
        if hasattr(cb_common, name):
            setattr(cb_common, name, _make_recorder(name))


def _snapshot_root_of(target_path):
    # Every pinned target lives at <snapshot_root>/tools/gsmg/<file>.py.
    return Path(target_path).resolve().parents[2]


def _apply_dependency_overrides(dependency_overrides, target_path):
    """Pre-import each named module and patch its own attribute, BEFORE
    the target is run at all, so the target's own `from module import
    ATTR` (or any transitive user of `module.ATTR`) picks up the patched
    value via sys.modules caching -- the only reliable way to override a
    value the target captures either as a function default (baked in at
    definition time) or via a dependency it merely imports, not defines."""
    snapshot_root = _snapshot_root_of(target_path)
    for module_name, attrs in dependency_overrides.items():
        module = importlib.import_module(module_name)
        for attr_name, repo_relative_value in attrs.items():
            if not hasattr(module, attr_name):
                raise LookupError(
                    f"dependency_overrides target {module_name}.{attr_name} not found"
                )
            setattr(module, attr_name, snapshot_root / repo_relative_value)


def _run_cli(target_path, argv):
    sys.argv = [target_path] + list(argv)
    runpy.run_path(target_path, run_name="__main__")


def _run_call(target_path, entry_function, argv=None, attr_overrides=None):
    # A run_name other than "__main__" means any `if __name__ ==
    # "__main__":` guard in the target is False -- module-level code still
    # executes, but the CLI/argparse path does not.
    #
    # CAUTION (found via a failing synthetic test, not by inspection):
    # `runpy.run_path` returns a COPY of the execution namespace, not the
    # live dict the defined functions actually close over as their
    # `__globals__`. Mutating the returned dict (e.g. `namespace[attr] =
    # ...`) is silently invisible to every function defined in the
    # target -- they keep reading the ORIGINAL dict. Any override must
    # go through `<some function from the target>.__globals__` instead.
    module_stem = target_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    namespace = runpy.run_path(target_path, run_name=f"phase478_isolated_{module_stem}")

    if entry_function not in namespace:
        raise LookupError(
            f"entry_function {entry_function!r} not found in {target_path}"
        )
    entry_func = namespace[entry_function]
    module_globals = entry_func.__globals__  # the REAL, live globals dict

    if attr_overrides:
        snapshot_root = _snapshot_root_of(target_path)
        for attr_name, repo_relative_value in attr_overrides.items():
            if attr_name not in module_globals:
                raise LookupError(
                    f"attr_overrides target {attr_name!r} not found in {target_path}"
                )
            module_globals[attr_name] = snapshot_root / repo_relative_value

    if argv is not None:
        sys.argv = [target_path] + list(argv)
    entry_func()


def main():
    if len(sys.argv) != 3:
        print(json.dumps({"error": "usage: phase478_harvest_driver.py <target_path> <recipe_json>"}))
        sys.exit(1)
    target_path, recipe_json = sys.argv[1], sys.argv[2]
    recipe = json.loads(recipe_json)

    if CAPTURE_FILE_ENV not in os.environ:
        raise RuntimeError(
            f"{CAPTURE_FILE_ENV} must be set by the caller before launching this driver"
        )

    _patch_cb_common()

    status = "ok"
    error = None
    try:
        if recipe.get("dependency_overrides"):
            _apply_dependency_overrides(recipe["dependency_overrides"], target_path)
        if recipe["mode"] == "cli":
            _run_cli(target_path, recipe.get("argv", []))
        elif recipe["mode"] == "call":
            _run_call(
                target_path, recipe["entry_function"],
                argv=recipe.get("argv"), attr_overrides=recipe.get("attr_overrides"),
            )
        else:
            raise ValueError(f"unknown recipe mode {recipe['mode']!r}")
    except SystemExit as exc:
        code = exc.code
        if code is None or code == 0:
            status, error = "ok", None
        else:
            status, error = "harvest_failed", f"SystemExit({code!r})"
    except BaseException as exc:  # noqa: BLE001 -- must capture and report, never crash silently
        status = "harvest_failed"
        error = f"{type(exc).__name__}: {exc}"

    # No "candidates" key here by design: the caller owns the capture
    # file (created and will delete it) and reads it directly. This
    # process never reads it back, and never touches it once it exits --
    # including a SIGKILL after a timeout, when this line never runs at
    # all.
    out = {"status": status, "error": error}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
