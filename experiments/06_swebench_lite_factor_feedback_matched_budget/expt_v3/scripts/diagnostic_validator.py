"""Validate and freeze public diagnostic transport without executing authored code."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys


SCHEMA_VERSION = 1
KINDS = ("syntax", "regression", "issue")
MAX_RESPONSE_BYTES = 65_536
MAX_CHECKS_PER_KIND = 8
MAX_ARGUMENTS = 64
MAX_ARGUMENT_BYTES = 16_384
PYTHON = {"python", "python3"}
PYTEST = {"pytest", "py.test"}
PYTEST_FLAGS = {"-q", "--disable-warnings", "--tb=short"}
RELATIVE_PATH = re.compile(r"[A-Za-z0-9_./-]+")
SELECTOR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class DiagnosticValidationError(ValueError):
    """A stable rejection code; never quote untrusted response text in errors."""


def reject(code):
    raise DiagnosticValidationError(code)


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            reject("duplicate_json_key")
        result[key] = value
    return result


def _no_constant(_value):
    reject("nonfinite_json_number")


def parse_response(text):
    """Accept one bare JSON object only; do not strip fences or salvage a prefix."""
    if not isinstance(text, str):
        reject("response_not_text")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeError:
        reject("invalid_utf8")
    if not 0 < size <= MAX_RESPONSE_BYTES:
        reject("response_size")
    try:
        value = json.loads(text, object_pairs_hook=_unique_object,
                           parse_constant=_no_constant)
    except DiagnosticValidationError:
        raise
    except (ValueError, RecursionError):
        reject("invalid_json_transport")
    if not isinstance(value, dict):
        reject("response_not_object")
    return value


def _relative_path(value, *, pytest_selector=False):
    pieces = value.split("::") if pytest_selector else [value]
    path = pieces[0]
    if (not RELATIVE_PATH.fullmatch(path) or path.startswith("-")
            or PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
            or any(not SELECTOR.fullmatch(part) for part in pieces[1:])):
        reject("unsupported_relative_path")


def _python_assertion(source):
    try:
        tree = ast.parse(source, mode="exec")
        # Compile, but never run: catches semantic syntax errors such as `return`
        # outside a function that ast.parse alone accepts.
        compile(tree, "<public-diagnostic>", "exec", dont_inherit=True, optimize=0)
    except (SyntaxError, ValueError, RecursionError, TypeError):
        reject("invalid_python_source")
    # Conservative authoring contract. An assertion inside a dead function or a
    # catch-all try block does not qualify. This is NOT behavioral validation:
    # `assert True` is structurally valid and will fail the separate base gate.
    if not any(isinstance(statement, ast.Assert) for statement in tree.body):
        reject("missing_top_level_assertion")


def validate_argv(argv, kind):
    """Check a small command grammar, not code safety; run only in task sandboxes.

    Python source remains untrusted arbitrary code. A future caller MUST pass
    argv directly to an isolated runner with shell=False, bounded resources,
    no secrets/network/evaluator files, a fixed working directory/environment,
    and assertions enabled (including no inherited PYTHONOPTIMIZE).
    """
    if kind not in KINDS:
        reject("unknown_kind")
    if not isinstance(argv, list) or not 1 <= len(argv) <= MAX_ARGUMENTS:
        reject("argv_not_nonempty_list")
    for argument in argv:
        if not isinstance(argument, str) or not argument or "\0" in argument:
            reject("invalid_argument")
        try:
            size = len(argument.encode("utf-8"))
        except UnicodeError:
            reject("invalid_argument_utf8")
        if size > MAX_ARGUMENT_BYTES:
            reject("argument_too_large")

    if argv[0] in PYTHON and len(argv) == 3 and argv[1] == "-c":
        if kind == "syntax":
            reject("syntax_requires_compileall")
        _python_assertion(argv[2])
        return

    if kind == "syntax":
        if (argv[0] not in PYTHON or len(argv) < 5
                or argv[1:4] != ["-m", "compileall", "-q"]):
            reject("syntax_requires_compileall")
        for path in argv[4:]:
            _relative_path(path)
        return

    if kind == "issue":
        reject("issue_requires_python_assertion")

    if argv[0] in PYTEST:
        arguments = argv[1:]
    elif argv[0] in PYTHON and argv[1:3] == ["-m", "pytest"]:
        arguments = argv[3:]
    else:
        reject("unapproved_entry_point")
    paths = []
    for argument in arguments:
        if argument in PYTEST_FLAGS:
            continue
        _relative_path(argument, pytest_selector=True)
        paths.append(argument)
    if not paths:
        reject("regression_requires_test_path")


def validate_response(text, expected_instance_id):
    """Return a normalized, fixed-membership bundle or a deterministic rejection.

    Acceptance is structural only. Before solver use, all regression checks
    must pass and every issue check must fail by assertion on the exact public
    base in isolation. Import, collection, timeout and other infrastructure
    failures are not reproductions. This module cannot establish issue fidelity.
    """
    candidate = parse_response(text)
    if set(candidate) != {"schema_version", "instance_id", "checks"}:
        reject("unexpected_bundle_fields")
    if type(candidate["schema_version"]) is not int or candidate["schema_version"] != SCHEMA_VERSION:
        reject("unsupported_schema_version")
    if not isinstance(expected_instance_id, str) or not expected_instance_id:
        reject("missing_expected_instance_id")
    if candidate["instance_id"] != expected_instance_id:
        reject("instance_id_mismatch")
    checks = candidate["checks"]
    if not isinstance(checks, list) or not 3 <= len(checks) <= 3 * MAX_CHECKS_PER_KIND:
        reject("invalid_check_count")
    counts = dict.fromkeys(KINDS, 0)
    checked = []
    for check in checks:
        if not isinstance(check, dict) or set(check) != {"id", "kind", "argv"}:
            reject("unexpected_check_fields")
        kind = check["kind"]
        if not isinstance(kind, str) or kind not in KINDS:
            reject("unknown_kind")
        counts[kind] += 1
        if counts[kind] > MAX_CHECKS_PER_KIND:
            reject("too_many_checks_for_kind")
        if check["id"] != f"{kind}_{counts[kind]:02d}":
            reject("check_id_membership_or_order")
        validate_argv(check["argv"], kind)
        checked.append({"id": check["id"], "kind": kind, "argv": list(check["argv"])})
    if any(count == 0 for count in counts.values()):
        reject("empty_kind_denominator")
    return {"schema_version": SCHEMA_VERSION, "instance_id": expected_instance_id,
            "checks": checked}


def inspect_response(response_bytes, expected_instance_id):
    """Bind a structural receipt to exact response bytes without running checks."""
    record = {
        "schema_version": SCHEMA_VERSION,
        "instance_id": expected_instance_id,
        "response_sha256": sha256(response_bytes),
        "validator_sha256": sha256(Path(__file__).read_bytes()),
        "structural_status": "rejected",
        "execution_status": "not_measured",
        "behavioral_status": "not_measured",
        "invalid_reason": None,
        "bundle_sha256": None,
        "denominators": None,
        "bundle": None,
    }
    try:
        try:
            text = response_bytes.decode("utf-8")
        except UnicodeError:
            reject("invalid_utf8")
        bundle = validate_response(text, expected_instance_id)
    except DiagnosticValidationError as exc:
        record["invalid_reason"] = str(exc)
    else:
        record.update(structural_status="accepted", bundle=bundle,
                      bundle_sha256=sha256(canonical_bytes(bundle)),
                      denominators={kind: sum(c["kind"] == kind for c in bundle["checks"])
                                    for kind in KINDS})
    return record


def exclusive_write(path, value):
    """Write one immutable receipt, refusing existing files and symlinks."""
    payload = canonical_bytes(value) + b"\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return sha256(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--response", type=Path, required=True,
                        help="Exact raw author response bytes; not a client envelope")
    parser.add_argument("--instance-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = inspect_response(args.response.read_bytes(), args.instance_id)
    receipt_hash = exclusive_write(args.output, record)
    print(json.dumps({"structural_status": record["structural_status"],
                      "invalid_reason": record["invalid_reason"],
                      "receipt_sha256": receipt_hash}, sort_keys=True))
    return 0 if record["structural_status"] == "accepted" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"diagnostic validation failed: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(2)
