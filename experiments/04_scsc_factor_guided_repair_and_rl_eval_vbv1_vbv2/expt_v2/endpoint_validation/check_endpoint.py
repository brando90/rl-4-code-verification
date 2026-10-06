"""Validate restricted authored Lean endpoint fixtures independently of candidate specifications."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCORER_COMMIT = "59059a20d40adf3289869e58302169ad78102877"
KERNEL_PATH = "scripts/scsc/kernel_axioms.py"
KERNEL_SHA256 = "5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287"
LEAN_TOOLCHAIN = "leanprover/lean4:v4.22.0"
MATHLIB_COMMIT = "79e94a093aff4a60fb1b1f92d9681e407124c2ca"
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
TACTICS = ("intro n; rfl", "simp [Candidate.impl]", "intro n; simp [Candidate.impl]; omega")
MAX_SOURCE_BYTES = 32768


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exact_keys(value: object, keys: set[str], context: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{context}: expected keys {sorted(keys)}")
    return value


def expression(node: object, depth: int = 0) -> str:
    """Render a bounded abstract syntax tree, never interpolate candidate Lean text."""
    if depth > 8 or not isinstance(node, dict):
        raise ValueError("expression: invalid node or depth > 8")
    op = node.get("op")
    if not isinstance(op, str):
        raise ValueError("expression operation must be a string")
    if op == "var":
        exact_keys(node, {"op"}, "variable")
        return "n"
    if op == "nat":
        exact_keys(node, {"op", "value"}, "natural")
        if type(node["value"]) is not int or not 0 <= node["value"] <= 1000:
            raise ValueError("natural literal must be an integer in [0,1000]")
        return str(node["value"])
    if op not in {"add", "sub", "mul", "min", "max"}:
        raise ValueError("unsupported expression operation")
    exact_keys(node, {"op", "left", "right"}, "binary expression")
    left = expression(node["left"], depth + 1)
    right = expression(node["right"], depth + 1)
    if op in {"min", "max"}:
        return f"({op} {left} {right})"
    operator = {"add": "+", "sub": "-", "mul": "*"}[op]
    return f"({left} {operator} {right})"


def load_json(path: Path) -> object:
    raw = path.read_bytes()
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError(f"file too large: {path.name}")
    # Duplicate keys cannot silently override the intended fixture or candidate.
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def load_manifest(path: Path) -> dict:
    manifest = exact_keys(load_json(path), {"schema", "scope", "tasks", "cells"}, "manifest")
    if type(manifest["schema"]) is not int or manifest["schema"] != 1 or manifest["scope"] != "authored_harness_validation_only":
        raise ValueError("unsupported manifest schema/scope")
    if not isinstance(manifest["tasks"], list) or not 2 <= len(manifest["tasks"]) <= 4:
        raise ValueError("declare 2–4 external validation tasks")
    task_ids = set()
    for task in manifest["tasks"]:
        exact_keys(task, {"id", "objective", "reference", "tests", "obligations"}, "task")
        if not isinstance(task["id"], str) or task["id"] not in {"increment", "double", "cap_two"} or task["id"] in task_ids:
            raise ValueError("unknown/duplicate frozen task")
        task_ids.add(task["id"])
        if not isinstance(task["objective"], str) or not task["objective"].strip():
            raise ValueError("missing objective")
        expression(task["reference"])
        if not isinstance(task["tests"], list) or not task["tests"]:
            raise ValueError("nonempty tests required")
        seen_inputs = set()
        for test in task["tests"]:
            exact_keys(test, {"input", "expected"}, "test")
            if any(type(test[k]) is not int or not 0 <= test[k] <= 10000 for k in test):
                raise ValueError("test literals out of range")
            if test["input"] in seen_inputs:
                raise ValueError("duplicate test input")
            seen_inputs.add(test["input"])
            if test["expected"] != calculate(task["reference"], test["input"]):
                raise ValueError("test expected value contradicts frozen reference")
        if task["obligations"] != ["exact"] and not (
                task["id"] == "cap_two" and task["obligations"] == ["exact", "bounded"]):
            raise ValueError("missing/unsupported fixed obligations")
    if not isinstance(manifest["cells"], list) or not manifest["cells"]:
        raise ValueError("nonempty cell manifest required")
    cell_ids = set()
    for cell in manifest["cells"]:
        exact_keys(cell, {"id", "task", "candidate", "candidate_sha256", "expected"}, "cell")
        if not isinstance(cell["id"], str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,79}", cell["id"]) or cell["id"] in cell_ids:
            raise ValueError("invalid/duplicate cell id")
        cell_ids.add(cell["id"])
        if not isinstance(cell["task"], str) or cell["task"] not in task_ids:
            raise ValueError("cell references unknown task")
        if not isinstance(cell["candidate"], str) or not re.fullmatch(r"candidates/[a-z][a-z0-9_]*\.json", cell["candidate"]):
            raise ValueError("candidate path must be a simple relative fixture path")
        if not isinstance(cell["candidate_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", cell["candidate_sha256"]):
            raise ValueError("missing candidate hash")
        exact_keys(cell["expected"], {"tests", "submitted", "evaluator"}, "expected statuses")
        if any(not isinstance(v, str) or v not in {"pass", "fail", "unknown"} for v in cell["expected"].values()):
            raise ValueError("invalid expected status")
    return manifest


def calculate(node: dict, n: int) -> int:
    expression(node)
    op = node["op"]
    if op == "var":
        return n
    if op == "nat":
        return node["value"]
    left, right = calculate(node["left"], n), calculate(node["right"], n)
    return {"add": lambda: left + right, "sub": lambda: max(0, left - right),
            "mul": lambda: left * right, "min": lambda: min(left, right),
            "max": lambda: max(left, right)}[op]()


def load_candidate(path: Path, expected_hash: str, task_id: str) -> dict:
    if digest(path.read_bytes()) != expected_hash:
        raise ValueError("candidate hash mismatch")
    c = exact_keys(load_json(path), {"schema", "task", "implementation", "specification", "certificate"}, "candidate")
    if type(c["schema"]) is not int or c["schema"] != 1 or c["task"] != task_id:
        raise ValueError("candidate interface/task mismatch")
    expression(c["implementation"])
    if not isinstance(c["specification"], str) or c["specification"] not in {"full", "weak_true", "vacuous", "sample_zero"}:
        raise ValueError("unsupported submitted specification")
    if not isinstance(c["certificate"], str) or c["certificate"] not in {"rfl", "simp", "omega", "trivial", "sorry", "helper_sorry", "axiom", "native_decide", "missing"}:
        raise ValueError("unsupported submitted certificate")
    return c


def base_source(c: dict) -> str:
    return ("-- TLDR: Generated bounded fixture; Candidate.impl is the only callable implementation.\n"
            "import Mathlib\nnamespace Candidate\n"
            f"def impl (n : Nat) : Nat := {expression(c['implementation'])}\nend Candidate\n")


def obligation(task: dict, name: str) -> str:
    if name == "exact":
        return f"∀ n : Nat, Candidate.impl n = {expression(task['reference'])}"
    if name == "bounded" and task["id"] == "cap_two":
        return "∀ n : Nat, Candidate.impl n ≤ 2"
    raise ValueError("unknown obligation")


def submitted_source(c: dict, task: dict) -> tuple[str, list[str]]:
    if c["certificate"] == "missing":
        return base_source(c), []
    spec = c["specification"]
    stmt = {"full": obligation(task, "exact"), "weak_true": "True",
            "vacuous": "∀ n : Nat, False → Candidate.impl n = n",
            "sample_zero": f"Candidate.impl 0 = {calculate(task['reference'], 0)}"}[spec]
    prelude = ""
    cert = c["certificate"]
    proof = {"rfl": "by intro n; rfl" if spec == "full" else "by rfl",
             "simp": "by simp [Candidate.impl]", "omega": "by intro n; simp [Candidate.impl]; omega",
             "trivial": "by trivial" if spec == "weak_true" else "by intro n h; exact False.elim h",
             "sorry": "by sorry", "native_decide": "by native_decide"}.get(cert)
    if cert == "helper_sorry":
        prelude = f"theorem submitted_helper : {stmt} := by sorry\n"
        proof = "submitted_helper"
    if cert == "axiom":
        prelude = f"axiom submitted_assumption : {stmt}\n"
        proof = "submitted_assumption"
    return base_source(c) + prelude + f"theorem submitted_certificate : {stmt} := {proof}\n", ["submitted_certificate"]


def endpoint(status: str, reason: str, **evidence) -> dict:
    if status not in {"pass", "fail", "unknown", "unmeasured"}:
        raise ValueError("invalid result status")
    return {"status": status, "value": {"pass": True, "fail": False}.get(status), "reason": reason, **evidence}


def conjunction(*results: dict) -> dict:
    # Observed false is false even if another stage is unknown; every missing stage survives separately.
    if any(r["status"] == "fail" for r in results):
        return endpoint("fail", "observed_component_failure")
    if all(r["status"] == "pass" for r in results):
        return endpoint("pass", "all_required_components_accepted")
    return endpoint("unknown", "required_component_unknown_or_unmeasured")


def kernel_verdict(report: dict, names: list[str], source_sha: str) -> dict:
    """Never treat compile/search failure as a checked counterexample."""
    if not names:
        return endpoint("unknown", "certificate_missing")
    if (not report.get("probe_ok") or report.get("probe_rc") != 0 or report.get("probe_errors")
            or report.get("compile_rc") != 0 or report.get("inspect_rc") != 0):
        return endpoint("unknown", "timeout" if report.get("probe_rc") == 124 else "compile_or_probe_failed")
    if report.get("source_sha256") != source_sha or report.get("allow_native_decide") is not False:
        return endpoint("unknown", "source_or_policy_mismatch")
    if not re.fullmatch(r"[0-9a-f]{64}", report.get("compiled_module_sha256") or ""):
        return endpoint("unknown", "compiled_module_identity_missing")
    rows = report.get("theorems", [])
    selected = []
    for name in names:
        matches = [r for r in rows if r.get("full_name") == name]
        if len(matches) != 1 or matches[0].get("resolution") != "source_position":
            return endpoint("unknown", "certificate_resolution_missing_or_ambiguous")
        selected.extend(matches)
    for row in selected:
        axioms = row.get("axioms")
        if not isinstance(axioms, list) or not all(isinstance(a, str) for a in axioms):
            return endpoint("unknown", "axiom_evidence_invalid")
        if set(axioms) - ALLOWED_AXIOMS:
            return endpoint("fail", "forbidden_transitive_axioms", axioms=axioms)
        if row.get("category") != "honest" or row.get("kernel_honest") is not True:
            return endpoint("unknown", "inconsistent_kernel_classification")
    return endpoint("pass", "allowed_transitive_axioms", certificates=names)


def run_checked(command: list[str], cwd: Path | None = None) -> bytes:
    return subprocess.run(command, cwd=cwd, capture_output=True, check=True, timeout=60).stdout


def load_kernel(scorer_repo: Path, output: Path):
    # Extract exact pinned bytes even if the supplied checkout is on another revision.
    data = run_checked(["git", "-C", str(scorer_repo), "show", f"{SCORER_COMMIT}:{KERNEL_PATH}"])
    if digest(data) != KERNEL_SHA256:
        raise ValueError("pinned verifier hash mismatch")
    pinned = output / "kernel_axioms_pinned.py"
    pinned.write_bytes(data)
    spec = importlib.util.spec_from_file_location("endpoint_kernel_pinned", pinned)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if set(module.ALLOWED_AXIOMS) != ALLOWED_AXIOMS:
        raise ValueError("pinned verifier axiom policy mismatch")
    return module


def preflight(lake: Path) -> dict:
    if (lake / "lean-toolchain").read_text().strip() != LEAN_TOOLCHAIN:
        raise ValueError("Lean toolchain pin mismatch")
    manifest_bytes = (lake / "lake-manifest.json").read_bytes()
    packages = json.loads(manifest_bytes)["packages"]
    mathlib = [p for p in packages if p["name"] == "mathlib"]
    if len(mathlib) != 1 or mathlib[0]["rev"] != MATHLIB_COMMIT:
        raise ValueError("Mathlib manifest pin mismatch")
    actual_mathlib = run_checked(["git", "-C", str(lake / ".lake/packages/mathlib"), "rev-parse", "HEAD"]).decode().strip()
    if actual_mathlib != MATHLIB_COMMIT:
        raise ValueError("installed Mathlib revision mismatch")
    if run_checked(["git", "-C", str(lake / ".lake/packages/mathlib"), "status", "--porcelain", "--untracked-files=no"]):
        raise ValueError("installed Mathlib tracked source is dirty")
    version = run_checked(["lake", "env", "lean", "--version"], lake).decode().strip()
    if not re.search(r"Lean \(version 4\.22\.0(?:,|\))", version):
        raise ValueError("actual Lean executable version mismatch")
    return {"lean_version": version, "lean_toolchain": LEAN_TOOLCHAIN,
            "mathlib_commit": actual_mathlib, "lake_manifest_sha256": digest(manifest_bytes)}


def probe(module, source: str, names: list[str], stage: Path, lake: Path, timeout: int) -> dict:
    stage.mkdir(parents=True)
    lean = stage / "candidate.lean"
    lean.write_text(source)
    started = time.monotonic()
    try:
        report = module.check_file(str(lean), str(lake), timeout=timeout,
                                   allow_native_decide=False, keep_dir=str(stage / "evidence")).to_dict()
        (stage / "kernel_report.json").write_text(json.dumps(report, indent=2) + "\n")
        result = kernel_verdict(report, names, digest(source.encode()))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result = endpoint("unknown", "infrastructure_failure", detail=str(exc))
    return {**result, "elapsed_seconds": time.monotonic() - started,
            "source_sha256": digest(source.encode()), "evidence_path": str(stage)}


def evaluate_cell(cell: dict, task: dict, candidate: dict, module, lake: Path, output: Path, timeout: int) -> dict:
    directory = output / cell["id"]
    directory.mkdir()
    impl = probe(module, base_source(candidate), [], directory / "implementation", lake, timeout)
    # A source without a theorem has no proof endpoint; compile status is still retained.
    report_path = directory / "implementation/kernel_report.json"
    compile_ok = False
    compile_value = None
    if report_path.is_file():
        rep = json.loads(report_path.read_text())
        compile_ok = rep.get("probe_ok") is True and rep.get("compile_rc") == 0
        if rep.get("compile_rc") == 0:
            compile_value = True
        elif rep.get("compile_rc") not in {None, 124, 125, 126, 127, 137}:
            compile_value = False
    tests = endpoint("unknown", "implementation_compile_failed")
    if compile_ok:
        tests_source = base_source(candidate)
        for index, test in enumerate(task["tests"]):
            # Kernel decide computes finite tests; native_decide is never used here.
            tests_source += f"theorem reference_test_{index} : Candidate.impl {test['input']} = {test['expected']} := by decide\n"
        tests = probe(module, tests_source, [f"reference_test_{i}" for i in range(len(task["tests"]))],
                      directory / "tests", lake, timeout)
        if tests["status"] != "pass":
            # Independent exact interpreter for the restricted total Nat expression language.
            mismatches = [t for t in task["tests"] if calculate(candidate["implementation"], t["input"]) != t["expected"]]
            if mismatches:
                witness = mismatches[0]
                negative_source = base_source(candidate) + (
                    f"theorem reference_counterexample : Candidate.impl {witness['input']} ≠ {witness['expected']} := by decide\n")
                negative = probe(module, negative_source, ["reference_counterexample"],
                                 directory / "counterexample", lake, timeout)
                if negative["status"] == "pass":
                    tests = endpoint("fail", "checked_finite_counterexample", counterexamples=[witness],
                                     lean_test_attempt=tests, negative_certificate=negative)
    submitted_src, submitted_names = submitted_source(candidate, task)
    submitted = (probe(module, submitted_src, submitted_names, directory / "submitted", lake, timeout)
                 if submitted_names else endpoint("unknown", "certificate_missing"))
    submitted["specification_kind"] = candidate["specification"]
    # Only an exactly linked full submitted specification can certify fixed universal requirements.
    submitted_reference = (submitted if candidate["specification"] == "full" and task["obligations"] == ["exact"]
                           else endpoint("unknown", "submitted_reference_bridge_unavailable"))
    obligations = []
    for name in task["obligations"]:
        attempts = []
        if compile_ok:
            for i, tactic in enumerate(TACTICS):
                source = base_source(candidate) + f"theorem reference_obligation : {obligation(task, name)} := by {tactic}\n"
                attempt = probe(module, source, ["reference_obligation"], directory / f"obligation_{name}_{i}", lake, timeout)
                attempts.append({"tactic": tactic, **attempt})
                if attempt["status"] == "pass":
                    break
        accepted = next((a for a in attempts if a["status"] == "pass"), None)
        verdict = accepted or endpoint("unknown", "bounded_search_exhausted" if compile_ok else "implementation_compile_failed")
        # A frozen test mismatch is a witness against the exact universal equation, not against boundedness.
        if name == "exact" and tests["status"] == "fail" and tests["reason"] == "checked_finite_counterexample":
            verdict = endpoint("fail", "checked_counterexample_to_exact_obligation", counterexamples=tests["counterexamples"])
        obligations.append({"name": name, **verdict, "attempts": attempts})
    evaluator = conjunction(*obligations)
    return {"cell": cell["id"], "task": task["id"], "candidate_sha256": cell["candidate_sha256"],
            "implementation_compiles": compile_value, "implementation_attempt": impl,
            "reference_tests_pass": tests, "submitted_certificate_accepted": submitted,
            "submitted_reference_obligations_proved": submitted_reference,
            "evaluator_reference_obligations_proved": evaluator, "obligations": obligations,
            "reference_verified_success": conjunction(tests, evaluator),
            "scope": "authored_harness_validation_only"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=HERE / "manifest.json")
    parser.add_argument("--scorer-repo", type=Path, required=True)
    parser.add_argument("--lake-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--probe-timeout", type=int, default=30)
    parser.add_argument("--cell-ids", nargs="+", metavar="CELL_ID",
                        help="Evaluate only declared cells into a new receipt; use for a deterministic resume after an interrupted run.")
    args = parser.parse_args(argv)
    if not 1 <= args.probe_timeout <= 60:
        parser.error("probe timeout must be in [1,60] seconds")
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)  # never overwrite prior execution evidence
    receipt = {"status": "RUNNING", "started_at": datetime.now(timezone.utc).isoformat(),
               "host": platform.node(), "script_sha256": digest(Path(__file__).read_bytes()),
               "manifest_sha256": digest(args.manifest.read_bytes()), "rows": [],
               "kernel_commit": SCORER_COMMIT, "kernel_sha256": KERNEL_SHA256,
               "probe_timeout_seconds": args.probe_timeout, "tactics": list(TACTICS),
               "scope": "authored_harness_validation_only"}
    result_path = args.output / "results.json"
    def save():
        result_path.write_text(json.dumps(receipt, indent=2) + "\n")
    save()
    exit_code = 1
    try:
        manifest = load_manifest(args.manifest)
        all_cells = manifest["cells"]
        requested = set(args.cell_ids or ())
        known = {cell["id"] for cell in all_cells}
        unknown = requested - known
        if unknown:
            raise ValueError(f"unknown requested cell ids: {sorted(unknown)}")
        cells = [cell for cell in all_cells if not requested or cell["id"] in requested]
        receipt["declared_cells"] = len(all_cells)
        receipt["executed_cells"] = len(cells)
        receipt["selection"] = {"kind": "all" if not requested else "explicit_resume",
                                "cell_ids": [cell["id"] for cell in cells]}
        receipt["rows"] = [{"cell": c["id"], "task": c["task"], "candidate_sha256": c["candidate_sha256"],
                            "status": "PENDING", "expected": c["expected"],
                            "reference_tests_pass": endpoint("unmeasured", "not_run"),
                            "submitted_certificate_accepted": endpoint("unmeasured", "not_run"),
                            "evaluator_reference_obligations_proved": endpoint("unmeasured", "not_run"),
                            "reference_verified_success": endpoint("unmeasured", "not_run")}
                           for c in cells]
        save()
        # Validate and hash-check the entire declared set before the first Lean call.
        candidates = {cell["id"]: load_candidate(args.manifest.parent / cell["candidate"], cell["candidate_sha256"], cell["task"])
                      for cell in all_cells}
        inputs = args.output / "inputs"
        inputs.mkdir()
        manifest_data = args.manifest.read_bytes()
        if digest(manifest_data) != receipt["manifest_sha256"]:
            raise ValueError("manifest changed after validation")
        (inputs / "manifest.json").write_bytes(manifest_data)
        for cell in all_cells:
            data = (args.manifest.parent / cell["candidate"]).read_bytes()
            if digest(data) != cell["candidate_sha256"]:
                raise ValueError("candidate changed after validation")
            (inputs / (cell["id"] + ".json")).write_bytes(data)
        receipt["preflight"] = preflight(args.lake_dir.resolve())
        module = load_kernel(args.scorer_repo.resolve(), args.output)
        tasks = {task["id"]: task for task in manifest["tasks"]}
        for index, cell in enumerate(cells):
            row = evaluate_cell(cell, tasks[cell["task"]], candidates[cell["id"]], module,
                                args.lake_dir.resolve(), args.output, args.probe_timeout)
            actual = {"tests": row["reference_tests_pass"]["status"],
                      "submitted": row["submitted_certificate_accepted"]["status"],
                      "evaluator": row["evaluator_reference_obligations_proved"]["status"]}
            row["expected"] = cell["expected"]
            row["control_matches"] = actual == cell["expected"]
            row["status"] = "MEASURED"
            receipt["rows"][index] = row
            save()
        exit_code = int(not all(row["control_matches"] for row in receipt["rows"]))
        receipt["status"] = "COMPLETE" if exit_code == 0 else "CONTROL_MISMATCH"
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        receipt["status"] = "INFRASTRUCTURE_OR_INPUT_FAILURE"
        receipt["error"] = str(exc)
    receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
    receipt["exit_code"] = exit_code
    save()
    print(json.dumps({"status": receipt["status"], "completed_cells": sum(r.get("status") == "MEASURED" for r in receipt["rows"]), "results": str(result_path)}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
