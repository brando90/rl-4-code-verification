"""Freeze public-only base checkouts and deterministic lexical repair context."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


SOLVER_FIELDS = {"instance_id", "repo", "base_commit", "problem_statement"}
MAX_FILES = 8
MAX_FILE_CHARS = 6_000
MAX_CONTEXT_CHARS = 72_000
MAX_CANDIDATE_BYTES = 256_000
TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def run(command, cwd=None):
    completed = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\\n{completed.stderr.strip()}")
    return completed.stdout


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_inputs(manifest, solver_rows):
    if not isinstance(manifest, dict) or not isinstance(manifest.get("task_ids"), list):
        raise ValueError("public manifest must carry task_ids")
    if not isinstance(solver_rows, list) or len(solver_rows) != len(manifest["task_ids"]):
        raise ValueError("solver view must have exactly one row per declared task")
    by_id = {}
    for row in solver_rows:
        if not isinstance(row, dict) or set(row) != SOLVER_FIELDS:
            raise ValueError("solver rows must contain exactly the four public solver fields")
        if not all(isinstance(row[field], str) and row[field] for field in SOLVER_FIELDS):
            raise ValueError("solver fields must be nonempty strings")
        if not re.fullmatch(r"[0-9a-f]{40}", row["base_commit"]):
            raise ValueError("base_commit must be a full lowercase commit")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", row["repo"]):
            raise ValueError("repo must be an owner/name public GitHub repository")
        if row["instance_id"] in by_id:
            raise ValueError("duplicate solver instance_id")
        by_id[row["instance_id"]] = row
    if set(by_id) != set(manifest["task_ids"]):
        raise ValueError("solver view and manifest task IDs differ")
    return [by_id[task_id] for task_id in manifest["task_ids"]]


def safe_task_dir(root, instance_id):
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", instance_id)
    path = (root / name).resolve()
    if root not in path.parents:
        raise ValueError("unsafe task directory")
    return path


def checkout_base(row, source_root):
    task_dir = safe_task_dir(source_root, row["instance_id"])
    if task_dir.exists() or task_dir.is_symlink():
        raise FileExistsError(f"refusing to overwrite public checkout: {task_dir}")
    task_dir.mkdir(parents=True)
    run(["git", "init"], cwd=task_dir)
    run(["git", "remote", "add", "origin", f"https://github.com/{row['repo']}.git"], cwd=task_dir)
    run(["git", "fetch", "--depth=1", "origin", row["base_commit"]], cwd=task_dir)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=task_dir)
    observed = run(["git", "rev-parse", "HEAD"], cwd=task_dir).strip()
    if observed != row["base_commit"]:
        raise ValueError(f"base revision mismatch for {row['instance_id']}: {observed}")
    run(["git", "remote", "remove", "origin"], cwd=task_dir)
    if run(["git", "remote"], cwd=task_dir).strip():
        raise ValueError("public checkout retains a reachable remote")
    commit_count = int(run(["git", "rev-list", "--count", "HEAD"], cwd=task_dir).strip())
    if commit_count != 1:
        raise ValueError("public checkout is not an exact shallow base checkout")
    return task_dir


def issue_tokens(problem_statement):
    return {match.group(0).lower() for match in TOKEN.finditer(problem_statement)}


def public_files(checkout):
    files = []
    for line in run(["git", "ls-files", "-z"], cwd=checkout).split("\0"):
        if not line:
            continue
        relative = PurePosixPath(line)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe tracked path")
        candidate = checkout / relative
        if candidate.is_file() and candidate.stat().st_size <= MAX_CANDIDATE_BYTES:
            raw = candidate.read_bytes()
            if b"\0" not in raw:
                files.append((relative.as_posix(), raw))
    return files


def rank_files(problem_statement, files):
    tokens = issue_tokens(problem_statement)
    ranked = []
    for path, raw in files:
        text = raw.decode("utf-8", errors="replace")
        lowered_path = path.lower()
        lowered_text = text.lower()
        path_hits = sum(token in lowered_path for token in tokens)
        text_hits = sum(lowered_text.count(token) for token in tokens)
        score = 20 * path_hits + min(text_hits, 40)
        if score:
            ranked.append((score, path, raw))
    if not ranked:
        ranked = [(0, path, raw) for path, raw in files]
    return sorted(ranked, key=lambda item: (-item[0], item[1]))


def build_context(row, checkout):
    selected = []
    used_chars = 0
    for score, path, raw in rank_files(row["problem_statement"], public_files(checkout)):
        text = raw.decode("utf-8", errors="replace")
        excerpt = text[:MAX_FILE_CHARS]
        record_chars = len(path) + len(excerpt)
        if selected and used_chars + record_chars > MAX_CONTEXT_CHARS:
            continue
        selected.append({"path": path, "sha256": sha256_bytes(raw), "score": score, "excerpt": excerpt})
        used_chars += record_chars
        if len(selected) == MAX_FILES or used_chars >= MAX_CONTEXT_CHARS:
            break
    if not selected:
        raise ValueError(f"no public text files available for {row['instance_id']}")
    return {
        "instance_id": row["instance_id"],
        "repo": row["repo"],
        "base_commit": row["base_commit"],
        "problem_statement_sha256": sha256_bytes(row["problem_statement"].encode("utf-8")),
        "retrieval": {
            "version": 1,
            "token_pattern": TOKEN.pattern,
            "max_files": MAX_FILES,
            "max_file_chars": MAX_FILE_CHARS,
            "max_context_chars": MAX_CONTEXT_CHARS,
            "checkout": "exact shallow base commit with all Git remotes removed",
        },
        "files": selected,
    }


def exclusive_write(path, value):
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite frozen output: {path}")
    payload = canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return sha256_bytes(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-manifest", required=True, type=Path)
    parser.add_argument("--solver-view", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = read_json(args.public_manifest)
    rows = validate_inputs(manifest, read_json(args.solver_view))
    if args.output.resolve().is_relative_to(args.source_root.resolve()):
        parser.error("context output must not be written inside a public checkout")
    contexts = []
    for row in rows:
        checkout = checkout_base(row, args.source_root.resolve())
        contexts.append(build_context(row, checkout))
    output = {
        "schema_version": 1,
        "panel_manifest_sha256": sha256_bytes(args.public_manifest.read_bytes()),
        "solver_view_sha256": sha256_bytes(args.solver_view.read_bytes()),
        "contexts": contexts,
    }
    print(json.dumps({"contexts": len(contexts), "sha256": exclusive_write(args.output, output)}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"public-context preparation failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
