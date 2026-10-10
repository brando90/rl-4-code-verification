#!/usr/bin/env python3
"""Parser-backed Lean declaration diagnostics for Experiment 13; never changes strict scoring."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from rl4cv.e13 import PartialCredit
from rl4cv.rewards import ScoredResponse, reward_kernel_binary

HERE = Path(__file__).resolve().parent
PROBE = HERE / "DeclarationProbe.lean"
ERROR = re.compile(r"^.+?:(\d+):(\d+): error:", re.MULTILINE)


class AdapterError(ValueError):
    """The submitted source cannot yield a source-bound partial-credit receipt."""


@dataclass(frozen=True)
class Declaration:
    """One Lean-parser command span, retaining identity rather than a regex match."""

    start: int
    stop: int
    declaration_kind: str
    full_name: str | None
    is_example: bool
    is_axiom: bool
    clean: bool


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AdapterError(f"cannot load pinned module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _probe(source: Path, *, lake_dir: Path, lake: str = "lake") -> list[dict[str, Any]]:
    """Run the pinned Lean parser helper; parser errors are terminal, not guessed around."""
    completed = subprocess.run(
        ["nice", "-n", "10", lake, "env", "lean", "--run", str(PROBE), str(source)], cwd=lake_dir,
        capture_output=True, text=True, check=False, timeout=900,
    )
    if completed.returncode:
        raise AdapterError(f"Lean parser probe failed rc={completed.returncode}: {completed.stderr[-500:]}")
    rows: list[dict[str, Any]] = []
    try:
        for line in completed.stdout.splitlines():
            if line.strip():
                rows.append(json.loads(line))
    except json.JSONDecodeError as exc:
        raise AdapterError("Lean parser probe emitted non-JSON output") from exc
    if not rows or rows[-1].get("event") != "terminal" or rows[-1].get("parse_error") is not False:
        raise AdapterError("Lean parser recovered from malformed source; declaration evidence is unknown")
    return rows[:-1]


def _byte_offset(source: str, line: int, column: int) -> int | None:
    lines = source.splitlines(keepends=True)
    if not 1 <= line <= len(lines) or column < 1:
        return None
    prefix = "".join(lines[: line - 1])
    body = lines[line - 1].rstrip("\r\n")
    if column - 1 > len(body):
        return None
    return len(prefix.encode()) + len(body[: column - 1].encode())


def _error_offsets(source: str, log: str) -> list[int]:
    return [offset for line, col in ERROR.findall(log)
            if (offset := _byte_offset(source, int(line), int(col))) is not None]


def inspect_source(
    source_path: Path,
    *,
    lake_dir: Path,
    scorer_root: Path,
    expected_sha256: str | None = None,
    vacuous_count: int = 0,
    truncated: bool = False,
    lake: str = "lake",
) -> dict[str, Any]:
    """Measure one immutable source with Lean spans, official compilation, and kernel cones."""
    source_path = source_path.resolve()
    actual_sha = sha256(source_path)
    if expected_sha256 is not None and actual_sha != expected_sha256:
        raise AdapterError("source hash mismatch; deleted or replaced cell rejected")
    if type(vacuous_count) is not int or vacuous_count < 0:
        raise AdapterError("vacuous_count must be a nonnegative integer")
    if type(truncated) is not bool:
        raise AdapterError("truncated must be a boolean")
    parsed = _probe(source_path, lake_dir=lake_dir, lake=lake)
    source = source_path.read_text(encoding="utf-8")
    command_rows = [row for row in parsed if row.get("event") == "command" and row.get("declaration_kind")]
    declarations: list[Declaration] = []
    for row in command_rows:
        if type(row.get("start")) is not int or type(row.get("stop")) is not int or row["start"] >= row["stop"]:
            raise AdapterError("Lean parser returned an invalid command span")
        declarations.append(Declaration(
            start=row["start"], stop=row["stop"], declaration_kind=str(row["declaration_kind"]),
            full_name=row.get("full_name"), is_example=row.get("is_example") is True,
            is_axiom=row.get("is_axiom") is True, clean=True,
        ))
    names = [d.full_name for d in declarations if d.full_name]
    if len(names) != len(set(names)):
        raise AdapterError("duplicate fully qualified declaration identity")
    scorer = _load("e13_pinned_scorer", scorer_root / "scripts/scsc/run_real_eval.py")
    kernel_axioms = _load("e13_kernel_axioms", scorer_root / "scripts/scsc/kernel_axioms.py")
    compilation = scorer.compile_lean_file(str(source_path), str(lake_dir))
    error_offsets = _error_offsets(source, compilation.log)
    declarations = [Declaration(**{**asdict(d), "clean": not any(d.start <= offset < d.stop for offset in error_offsets)})
                    for d in declarations]
    theorem_decls = [d for d in declarations if d.declaration_kind == "Lean.Parser.Command.theorem"]
    kernel = kernel_axioms.check_file(str(source_path), str(lake_dir), timeout=900).to_dict()
    if kernel["probe_ok"]:
        kernel_names = {row["full_name"] for row in kernel["theorems"]}
        parser_names = {d.full_name for d in theorem_decls if d.full_name}
        if kernel_names != parser_names:
            raise AdapterError("kernel theorem identities disagree with Lean command spans")
    named = [d for d in declarations if d.full_name]
    implementations = [d for d in declarations if d.is_example or d.declaration_kind in {
        "Lean.Parser.Command.definition", "Lean.Parser.Command.abbrev", "Lean.Parser.Command.opaque",
    }]
    d_num, d_den = sum(item.clean for item in named), len(named)
    t_num, t_den = sum(item.clean for item in implementations), len(implementations)
    p_num, p_den = kernel["n_honest"], len(theorem_decls)
    dense = PartialCredit(
        extracted=bool(source.strip()), compiles=bool(compilation.success and kernel["probe_ok"]),
        n_examples=sum(d.is_example for d in declarations), theorem_count=p_den, proved_count=p_num,
        vacuous_count=vacuous_count, declarations_ok=d_num / d_den if d_den else 0.0,
        implementation_and_examples_ok=bool(t_den and t_num == t_den),
        proved_fraction=p_num / p_den if p_den else 0.0,
        truncated=truncated,
    )
    strict = reward_kernel_binary(ScoredResponse(
        extracted=dense.extracted, compiles=dense.compiles, n_examples=dense.n_examples,
        n_theorems_stated=dense.theorem_count, n_theorems_proved=dense.proved_count,
        vacuous_theorems=vacuous_count, truncated=truncated,
    ))
    return {
        "source_sha256": actual_sha, "declarations": [asdict(d) for d in declarations],
        "theorems": [d.full_name for d in theorem_decls],
        "axioms": [d.full_name for d in declarations if d.is_axiom],
        "kernel": kernel, "compile": asdict(compilation),
        "d": {"numerator": d_num, "denominator": d_den},
        "t": {"numerator": t_num, "denominator": t_den},
        "p": {"numerator": p_num, "denominator": p_den},
        "strict": strict, "factored_reward": dense.factored_reward(),
    }
