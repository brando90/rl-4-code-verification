#!/usr/bin/env python3
"""TLDR: Deterministically rewrite every MBPP `full` task into VeriBench's Python task layout (docstring, unchanged code, `check(candidate)`, `__main__`), keep only files that pass their own tests under `python3 -I`, and write the kept/dropped manifest with hashes (experiment 02A v3 PROTOCOL § 1; zero model calls)."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MBPP_REVISION = "4bb6404fdc6cacfda99d4ac4205087b89d32030c"
MBPP_FILES = ("prompt", "train", "validation", "test")
SPLIT = "mbpp"
GATE_TIMEOUT_S = 30
ROW_FIELDS = ("task_id", "text", "code", "test_list", "test_setup_code", "challenge_test_list")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def task_id_of(mbpp_task_id: int) -> str:
    return f"{SPLIT}__task_{int(mbpp_task_id)}"


def lean_stem_of(mbpp_task_id: int) -> str:
    return f"task_{int(mbpp_task_id)}"


def normalize_newlines(text: str) -> str:
    """MBPP stores `code` with CRLF line endings; only the line terminators change (LF), never the code."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def docstring_literal(text: str) -> str:
    body = normalize_newlines(text).strip().replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    return f'"""{body}"""'


class _Rename(ast.NodeTransformer):
    def __init__(self, old: str, new: str) -> None:
        self.old, self.new = old, new

    def visit_Name(self, node: ast.Name) -> ast.AST:  # noqa: N802 (ast API)
        if node.id == self.old:
            return ast.copy_location(ast.Name(id=self.new, ctx=node.ctx), node)
        return node


def _called_names(tree: ast.AST) -> set[str]:
    return {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}


def reference_function(code: str, asserts: list[str]) -> tuple[str | None, str]:
    """The unique top-level function of `code` that the assert tests call, or (None, reason)."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return None, f"code_syntax_error: {exc.msg}"
    top = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    if not top:
        return None, "no_top_level_function"
    called: set[str] = set()
    for a in asserts:
        try:
            called |= _called_names(ast.parse(a))
        except SyntaxError as exc:
            return None, f"assert_syntax_error: {exc.msg}"
    cands = [name for name in top if name in called]
    if len(cands) != 1:
        return None, ("asserts_call_no_top_level_function" if not cands else f"asserts_call_several_top_level_functions:{','.join(cands)}")
    # The VeriBench layout reserves `check` and `candidate` for the test harness; MBPP code that defines
    # either name cannot keep its code unchanged inside that layout, so it is dropped and listed.
    reserved = {"check", "candidate"} & ({n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)} | set(top))
    if reserved:
        return None, f"harness_name_collision:{','.join(sorted(reserved))}"
    return cands[0], "ok"


def rewrite_assert(line: str, fn: str) -> str:
    tree = ast.parse(line)
    tree = _Rename(fn, "candidate").visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def rewrite_task(row: dict) -> tuple[str | None, dict]:
    """VeriBench py_src layout: docstring, MBPP code unchanged, check(candidate), __main__ runner."""
    code = normalize_newlines(row["code"]).rstrip("\n") + "\n"
    asserts = [normalize_newlines(a).strip() for a in list(row["test_list"]) + list(row["challenge_test_list"] or [])]
    asserts = [a for a in asserts if a]
    setup = normalize_newlines(row["test_setup_code"] or "").strip("\n")
    info = {"mbpp_task_id": int(row["task_id"]), "task_id": task_id_of(row["task_id"]), "lean_stem": lean_stem_of(row["task_id"]),
            "n_tests": len(row["test_list"]), "n_challenge_tests": len(row["challenge_test_list"] or []), "has_setup_code": bool(setup)}
    if not asserts:
        info.update(dropped="no_assert_tests")
        return None, info
    fn, reason = reference_function(code, asserts)
    if fn is None:
        info.update(dropped=reason)
        return None, info
    body: list[str] = []
    if setup:
        body += [f"    {ln}" if ln.strip() else "" for ln in setup.splitlines()]
    try:
        body += [f"    {rewrite_assert(a, fn)}" for a in asserts]
    except SyntaxError as exc:
        info.update(dropped=f"assert_syntax_error: {exc.msg}")
        return None, info
    body.append("    return True")
    src = (
        f"{docstring_literal(row['text'])}\n\n"
        f"{code}\n"
        "# -- Tests --\n\n"
        "from typing import Callable\n\n"
        "def check(candidate: Callable) -> bool:\n" + "\n".join(body) + "\n\n"
        'if __name__ == "__main__":\n'
        f"    assert check({fn}), f\"Failed: {{__file__}}\"\n"
        '    print("All tests passed.")\n'
    )
    info.update(function=fn)
    return src, info


def python_gate(src: str, python: str = sys.executable, timeout_s: int = GATE_TIMEOUT_S) -> dict:
    """Run the rewritten file with `python3 -I` in an empty temporary directory; keep only exit 0."""
    with tempfile.TemporaryDirectory(prefix="mbpp_gate_") as td:
        path = Path(td) / "task.py"
        path.write_text(src, encoding="utf-8")
        try:
            r = subprocess.run([python, "-I", path.name], cwd=td, capture_output=True, text=True, timeout=timeout_s,
                               env={"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8"})
            return {"exit_code": r.returncode, "stderr_tail": r.stderr[-300:], "timed_out": False}
        except subprocess.TimeoutExpired:
            return {"exit_code": None, "stderr_tail": "", "timed_out": True}


def load_rows(mbpp_dir: Path) -> tuple[list[dict], dict]:
    import pyarrow.parquet as pq

    rows, hashes = [], {}
    for name in MBPP_FILES:
        matches = sorted((mbpp_dir / "full").glob(f"{name}-*.parquet"))
        if len(matches) != 1:
            raise FileNotFoundError(f"expected one full/{name}-*.parquet, found {len(matches)}")
        f = matches[0]
        hashes[f"full/{f.name}"] = sha256_bytes(f.read_bytes())
        table = pq.read_table(f)
        missing = set(ROW_FIELDS) - set(table.column_names)
        if missing:
            raise ValueError(f"{f}: missing columns {sorted(missing)}")
        for r in table.to_pylist():
            r["_source_file"] = name
            rows.append(r)
    ids = [int(r["task_id"]) for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate MBPP task_id across files")
    return sorted(rows, key=lambda r: int(r["task_id"])), hashes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mbpp-dir", type=Path, required=True, help="snapshot_download dir holding full/*.parquet")
    ap.add_argument("--out-dir", type=Path, required=True, help="rewritten files land in <out-dir>/mbpp/task_<id>.py")
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args(argv)
    if args.manifest.exists():
        raise FileExistsError(f"refusing to overwrite {args.manifest}")
    rows, hashes = load_rows(args.mbpp_dir)
    out = args.out_dir / SPLIT
    out.mkdir(parents=True, exist_ok=True)
    kept, dropped = [], []
    for row in rows:
        src, info = rewrite_task(row)
        info["source_file"] = row["_source_file"]
        if src is None:
            dropped.append(info)
            continue
        gate = python_gate(src, args.python)
        info["gate"] = gate
        if gate["exit_code"] != 0:
            info["dropped"] = "python_gate_timeout" if gate["timed_out"] else f"python_gate_exit_{gate['exit_code']}"
            dropped.append(info)
            continue
        path = out / f"{info['lean_stem']}.py"
        path.write_text(src, encoding="utf-8")
        info.update(path=str(path), sha256=sha256_bytes(src.encode("utf-8")), bytes=len(src.encode("utf-8")))
        kept.append(info)
    reasons: dict[str, int] = {}
    for d in dropped:
        key = d["dropped"].split(":")[0]
        reasons[key] = reasons.get(key, 0) + 1
    manifest = {
        "manifest_kind": "mbpp_rewrite_manifest_e02a_v3",
        "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {"dataset": "google-research-datasets/mbpp", "configuration": "full", "revision": MBPP_REVISION,
                   "files_sha256": hashes, "n_rows": len(rows), "files": list(MBPP_FILES)},
        "rewrite": {"layout": "VeriBench py_src: module docstring = MBPP text; MBPP code unchanged except CRLF->LF line endings; "
                              "check(candidate) = test_setup_code + every test_list and challenge_test_list assert with the "
                              "reference function renamed to candidate (ast rename); __main__ runs check(<reference function>)",
                    "task_id": "mbpp__task_<task_id>", "lean_stem": "task_<task_id>", "split": SPLIT},
        "python_gate": {"command": "python3 -I task.py in an empty temporary directory", "timeout_s": GATE_TIMEOUT_S,
                        "interpreter": args.python, "python_version": platform.python_version()},
        "n_kept": len(kept), "n_dropped": len(dropped), "dropped_reasons": reasons,
        "kept": kept, "dropped": dropped,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"n_rows": len(rows), "n_kept": len(kept), "n_dropped": len(dropped), "dropped_reasons": reasons, "manifest": str(args.manifest)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
