"""Invoke the measured Claude CLI with no tools and preserve one bounded receipt."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


MAX_WALL_SECONDS = 300
MAX_CAPTURE_BYTES = 40 * 1024


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def exclusive_write(path, value):
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite receipt: {path}")
    payload = canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(payload).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--claude", default="claude")
    args = parser.parse_args()
    if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        parser.error("CLAUDE_CODE_OAUTH_TOKEN must be supplied by the authorized launcher")
    request_bytes = args.request.read_bytes()
    request = json.loads(request_bytes)
    required = {"request_id", "kind", "prompt", "panel_manifest_sha256"}
    if not isinstance(request, dict) or set(request) - {"request_id", "kind", "prompt", "panel_manifest_sha256", "cell_id", "context_sha256"} or not required <= set(request):
        parser.error("request has an unexpected or incomplete schema")
    if request["kind"] not in {"diagnostic_author", "solver"}:
        parser.error("request kind must be diagnostic_author or solver")
    if not all(isinstance(request[key], str) and request[key] for key in required):
        parser.error("required request values must be nonempty strings")
    if len(request["prompt"]) > 96_000:
        parser.error("prompt exceeds the frozen 96,000-character input limit")
    command = [
        args.claude,
        "--print",
        "--output-format",
        "json",
        "--no-session-persistence",
        "--restricted",
        "--tools",
        "",
        "--strict-mcp-config",
        "--permission-prompts",
        "none",
        "--model",
        "claude-sonnet-5",
        "--effort",
        "medium",
        request["prompt"],
    ]
    environment = os.environ.copy()
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_BASE_URL", "OPENAI_BASE_URL"):
        environment.pop(name, None)
    started = time.monotonic()
    timed_out = False
    try:
        completed = subprocess.run(command, cwd=args.cwd, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=MAX_WALL_SECONDS)
        stdout, stderr, returncode = completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout, stderr, returncode = exc.stdout or b"", exc.stderr or b"", None
    elapsed_seconds = round(time.monotonic() - started, 3)
    stdout = stdout if isinstance(stdout, bytes) else stdout.encode("utf-8", "replace")
    stderr = stderr if isinstance(stderr, bytes) else stderr.encode("utf-8", "replace")
    capture_limited = len(stdout) > MAX_CAPTURE_BYTES
    captured_stdout = stdout[:MAX_CAPTURE_BYTES]
    native = None
    if not timed_out and not capture_limited:
        try:
            native = json.loads(captured_stdout.decode("utf-8"))
        except json.JSONDecodeError:
            native = None
    status = "completed"
    if timed_out:
        status = "timeout"
    elif capture_limited:
        status = "capture_limit_exceeded"
    elif returncode:
        status = "client_failure"
    elif native is None:
        status = "unparseable_native_response"
    receipt = {
        "schema_version": 1,
        "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
        "request_id": request["request_id"],
        "kind": request["kind"],
        "panel_manifest_sha256": request["panel_manifest_sha256"],
        "cell_id": request.get("cell_id"),
        "context_sha256": request.get("context_sha256"),
        "command": command[:-1] + ["<prompt-redacted>"],
        "model_requested": "claude-sonnet-5",
        "effort_requested": "medium",
        "tool_isolation": "--restricted --tools '' --strict-mcp-config --permission-prompts none --no-session-persistence",
        "wall_limit_seconds": MAX_WALL_SECONDS,
        "output_capture_limit_bytes": MAX_CAPTURE_BYTES,
        "output_capture_limit_meaning": "A 40,960-byte persisted-response cap; the CLI exposes no enforced output-token parameter, so this is not claimed as an output-token cap.",
        "elapsed_seconds": elapsed_seconds,
        "status": status,
        "returncode": returncode,
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "stdout_bytes": len(stdout),
        "stderr_bytes": len(stderr),
        "captured_stdout": captured_stdout.decode("utf-8", "replace"),
        "captured_stderr": stderr[:MAX_CAPTURE_BYTES].decode("utf-8", "replace"),
        "native_response": native,
    }
    print(json.dumps({"status": status, "receipt_sha256": exclusive_write(args.output, receipt)}, sort_keys=True))
    if status != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
