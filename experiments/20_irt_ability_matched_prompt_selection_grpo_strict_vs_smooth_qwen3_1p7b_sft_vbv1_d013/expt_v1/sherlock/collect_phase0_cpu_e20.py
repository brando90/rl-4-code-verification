"""TLDR: Audit Phase 0 compiler evidence and immutable strict retries and bundles it without mutating original score tables."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import tarfile
import time
from collections import Counter
from pathlib import Path

E = Path(os.environ.get("E20_ROOT", "/scratch/users/brando9/rl4cv_sherlock/e20")).resolve()
P = E / "phase0"
O = P / "collected_cpu"
FROZEN = {
    "run_real_eval.py": "6e82b3d1cd6d3686aaec3d45f273cd902b03b962c0c2eca48f2c2b4f25f41fa9",
    "kernel_axioms.py": "5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287",
    "score_scsc.py": "b3713c48e0fdb24adec93b77be8785d20e48897ee8d1fd8ce31fdf37101e81d6",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolved(value: str) -> Path:
    p = Path(value)
    return (p if p.is_absolute() else E / p).resolve()


def add_file(rows: list[dict], path: Path, kind: str) -> None:
    if path.is_file():
        rows.append({"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size, "kind": kind})


def verify_execution(execution_path: Path, errors: list[str], *, retry: bool) -> tuple[dict, list[dict]]:
    """Verify D-109 call evidence. Native TIMEOUT is a scored outcome, never an infra retry."""
    x = json.loads(execution_path.read_text())
    folder = execution_path.parent
    state, code, timed = x.get("state"), x.get("exit_code"), x.get("timed_out")
    timeout = state == "TIMEOUT" and code is None and timed is True
    normal_complete = state == "COMPLETE" and type(code) is int and code >= 0 and not timed
    negative = type(code) is int and code < 0
    if retry and not (timeout or normal_complete):
        errors.append(f"retry execution invalid: {execution_path} state={state} exit={code}")
    stream_meta = {}
    for stream in ("stdout", "stderr"):
        q = folder / f"{stream}.log"
        if not q.is_file():
            errors.append(f"{q}: missing")
            stream_meta[stream + "_sha256"] = ""
            stream_meta[stream + "_bytes"] = 0
        else:
            actual = sha(q)
            stream_meta[stream + "_sha256"] = actual
            stream_meta[stream + "_bytes"] = q.stat().st_size
            if x.get(stream + "_sha256") and actual != x[stream + "_sha256"]:
                errors.append(f"{q}: hash mismatch")
    sources = []
    for source in x.get("sources", []):
        q = folder / source["snapshot"]
        if not q.is_file() or sha(q) != source["sha256"]:
            errors.append(f"{q}: source missing/hash mismatch")
        sources.append({"path": str(resolved(source["path"])), "sha256": source["sha256"]})
    return ({
        "path": str(execution_path), "sha256": sha(execution_path), "state": state,
        "exit_code": code, "timed_out": timed, "negative_exit": negative,
        "timeout_scored_failure": timeout, "compiler_sha256": x.get("compiler", {}).get("sha256", ""),
        **stream_meta, "sources": sources,
    }, sources)


def original_negative_audit(manifest: dict, errors: list[str]) -> list[dict]:
    """List intact frozen scorer negative exits as resource-bounded failures; overrides are optional diagnostics."""
    overrides = manifest.get("overrides", []) if manifest else []
    by_source = {}
    for entry in overrides:
        key = (int(entry["chunk"]), int(entry["sample_idx"]), entry["task_id"], entry["original_source_sha256"])
        if key in by_source:
            errors.append("duplicate strict retry override: " + repr(key))
        by_source[key] = entry
    out = []
    for c in range(4):
        for k in range(8):
            name = f"e20_p0_c{c}_s{k}"
            base = P / "scores" / name
            for ep in sorted((base / "compiler_diagnostics").glob("call_*/execution.json")):
                rec, sources = verify_execution(ep, errors, retry=False)
                if not rec["negative_exit"]:
                    continue
                matches = []
                for (cc, kk, task, h), entry in by_source.items():
                    expected_path = str((E / f"phase0/jobs/{name}/{task}/verifier/solution.lean").resolve())
                    if cc == c and kk == k and any(source["path"] == expected_path and source["sha256"] == h for source in sources):
                        matches.append((entry, h))
                if len(matches) > 1:
                    errors.append(f"original negative call has ambiguous retry overrides: {ep} matches={len(matches)}")
                    continue
                entry, source_sha = matches[0] if matches else (None, "")
                # No override is an intact native scorer outcome, not missing data or an audit error.
                source_paths = [x["path"] for x in sources]
                original_root = (P / "jobs" / name).resolve()
                originals = [(Path(x["path"]), x["sha256"]) for x in sources
                             if Path(x["path"]).is_relative_to(original_root)
                             and Path(x["path"]).parts[-2:] == ("verifier", "solution.lean")]
                original_task = originals[0][0].relative_to(original_root).parts[0] if len(originals) == 1 else ""
                if not source_sha and len(originals) == 1: source_sha = originals[0][1]
                out.append({
                    "original_job_name": name, "chunk": c, "sample_idx": k,
                    "task_id": entry["task_id"] if entry else original_task, "original_execution_path": str(ep),
                    "original_execution_sha256": sha(ep), "original_exit_code": rec["exit_code"],
                    "original_source_sha256": source_sha, "original_source_paths_json": json.dumps(source_paths, sort_keys=True),
                    "retry_job_name": entry["retry_job_name"] if entry else "", "retry_source_sha256": entry["retry_source_sha256"] if entry else "",
                    "classification": "recovered_named_retry" if entry else "recorded_native_resource_failure_no_override",
                })
    return out


def audit_retry_manifest(manifest_path: Path | None, errors: list[str]) -> tuple[list[dict], dict]:
    """Audit schema v1 retry artifacts; this collector never overlays or edits original score rows."""
    if manifest_path is None:
        return [], {"present": False, "overrides": []}
    m = json.loads(manifest_path.read_text())
    if m.get("version") != 1 or not isinstance(m.get("overrides"), list):
        errors.append("strict_retry_manifest.json: unsupported schema")
        return [], m
    provenance, seen = [], set()
    for entry in m["overrides"]:
        try:
            c, k, task = int(entry["chunk"]), int(entry["sample_idx"]), entry["task_id"]
            key = (c, k, task)
            if key in seen: raise ValueError("duplicate override key")
            seen.add(key)
            if entry["expected_scorer_pin"] != "59059a2": raise ValueError("scorer pin changed")
            name = entry["retry_job_name"]
            if not name or Path(name).name != name: raise ValueError("retry job basename")
            old = E / f"phase0/jobs/e20_p0_c{c}_s{k}/{task}/verifier/solution.lean"
            new = resolved(entry["retry_source_path"])
            expected = entry["original_source_sha256"]
            if not old.is_file() or not new.is_file() or sha(old) != expected or sha(new) != expected or entry["retry_source_sha256"] != expected:
                raise ValueError("source identity/hash")
            receipt = resolved(entry["terminal_receipt_path"])
            terminal = json.loads(receipt.read_text())
            if not (terminal.get("slurm_state") == "COMPLETED" and terminal.get("slurm_exit_code") == "0:0" and terminal.get("scorer_exit_code") == 0 and terminal.get("job_id")):
                raise ValueError("terminal receipt not successful")
            if terminal.get("retry_job_name") and terminal["retry_job_name"] != name: raise ValueError("terminal retry name")
            launcher_path = resolved(entry["launcher_path"])
            launcher = json.loads(launcher_path.read_text())
            if launcher.get("state") != "COMPLETE" or launcher.get("exit_code") != 0 or launcher.get("frozen_sha256") != FROZEN:
                raise ValueError("launcher completion/frozen scorer")
            argv = launcher.get("argv", [])
            if "--skip-tc" not in argv or "--job-dir" not in argv: raise ValueError("launcher frozen arguments")
            retry_job = resolved(argv[argv.index("--job-dir") + 1])
            if retry_job.name != name or new != retry_job / task / "verifier/solution.lean": raise ValueError("retry job/source path")
            sources = launcher.get("evaluated_sources", {})
            if task not in sources or resolved(sources[task]["path"]) != new or sources[task]["sha256"] != expected:
                raise ValueError("launcher evaluated source")
            table = resolved(entry["retry_table_path"])
            if sha(table) != entry["retry_table_sha256"] or table.parent != launcher_path.parent.parent:
                raise ValueError("retry table provenance")
            matching = [r for r in csv.DictReader(table.open(newline="")) if r.get("task") == task]
            if len(matching) != 1 or matching[0].get("scoring_status") != "scored": raise ValueError("retry target row")
            executions = sorted(launcher_path.parent.glob("call_*/execution.json"))
            if not executions: raise ValueError("retry compiler evidence absent")
            initial = False
            for ep in executions:
                rec, call_sources = verify_execution(ep, errors, retry=True)
                for source in call_sources:
                    if source["path"] == str(new):
                        if source["sha256"] != expected: raise ValueError("compiled retry source hash")
                        raw = json.loads(ep.read_text())
                        if raw.get("stage") == "initial_compile":
                            if raw.get("timeout_seconds") != 600: raise ValueError("initial timeout changed")
                            initial = True
            if not initial: raise ValueError("missing target initial 600s compile")
            provenance.append({"task_id": task, "chunk": c, "sample_idx": k, "retry_job_name": name,
                "retry_slurm_job_id": terminal["job_id"], "source_sha256": expected, "expected_scorer_pin": "59059a2",
                "original_source_path": str(old), "retry_source_path": str(new), "retry_table_path": str(table),
                "retry_table_sha256": sha(table), "terminal_receipt_path": str(receipt), "terminal_receipt_sha256": sha(receipt),
                "launcher_path": str(launcher_path), "launcher_sha256": sha(launcher_path),
                "manifest_path": str(manifest_path), "manifest_sha256": sha(manifest_path)})
        except (KeyError, IndexError, OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append("strict retry audit failed: " + str(exc))
    return provenance, m


def failed_attempt_pointers() -> list[dict]:
    """Retain compact pointers for archived attempts and direct retry roots, never archive their raw payloads."""
    rows, seen = [], set()
    roots = []
    for d in P.rglob("*"):
        if d.is_dir() and d.name in {"attempts", "failed_attempts", "archived_attempts"}:
            roots.append((d, "attempt_artifact"))
    for d in (P / "retries/strict", P / "retry_jobs"):
        if d.is_dir(): roots.append((d, "retry_artifact"))
    for p in P.glob("strict_retry*_submit.json"):
        if p.is_file(): roots.append((p, "retry_submission"))
    for root, default_kind in roots:
        files = [root] if root.is_file() else root.rglob("*")
        for p in files:
            if not p.is_file() or p in seen:
                continue
            seen.add(p)
            if p.name == "execution.json": kind = "attempt_execution_json" if default_kind == "attempt_artifact" else "retry_execution_json"
            elif p.name in {"stdout.log", "stderr.log"}: kind = "attempt_compiler_stream" if default_kind == "attempt_artifact" else "retry_compiler_stream"
            elif p.suffix == ".lean" or "snapshot" in p.name: kind = "attempt_source_snapshot" if default_kind == "attempt_artifact" else "retry_source_snapshot"
            else: kind = default_kind
            rows.append({"path": str(p), "sha256": sha(p), "bytes": p.stat().st_size, "kind": kind})
    return sorted(rows, key=lambda r: r["path"])


def main() -> int:
    O.mkdir(parents=True, exist_ok=True)
    manifest, calls, errors = [], [], []
    completion_checks = []
    call_states = Counter()
    builder = E / "code/build_phase0_cells_e20.py"
    if not builder.is_file():
        errors.append(f"{builder}: missing")
    # Keep all original output and diagnostic files immutable and bundle pointers/hashes.
    for stage in ("scores", "partial"):
        for c in range(4):
            for k in range(8):
                name = f"e20_p0_c{c}_s{k}"
                d = P / stage / name
                receipt = d / "completion_receipt.txt"
                completion_checks.append({"stage": stage, "job": name, "receipt": str(receipt), "present": receipt.is_file()})
                if not receipt.is_file(): errors.append(f"{stage}/{name}: no completion receipt")
                for pattern in ("*_per_task.csv", "*.json", "completion_receipt.txt"):
                    for p in d.glob(pattern): add_file(manifest, p, "original_score_output")
                for p in (d / "compiler_diagnostics").glob("call_*/execution.json"):
                    rec, _ = verify_execution(p, errors, retry=False)
                    rec.update({"stage": stage, "job": name})
                    calls.append(rec)
                    call_states[f"{stage}:{rec['state']}"] += 1
                    valid_terminal = ((rec["state"] == "COMPLETE" and type(rec["exit_code"]) is int and rec["exit_code"] >= 0 and not rec["timed_out"])
                                      or rec["timeout_scored_failure"])
                    if not valid_terminal and not rec["negative_exit"]:
                        errors.append(f"{stage}/{name}: nonterminal or raised compiler call {p} state={rec['state']} exit={rec['exit_code']}")
                launcher = d / "compiler_diagnostics/launcher.json"
                if launcher.is_file():
                    add_file(manifest, launcher, "D109_launcher")
                    if stage == "scores":
                        lx = json.loads(launcher.read_text())
                        if lx.get("state") != "COMPLETE" or lx.get("exit_code") != 0:
                            errors.append(f"{launcher}: expected COMPLETE/0, got {lx.get('state')}/{lx.get('exit_code')}")
                        if lx.get("frozen_sha256") != FROZEN or "--skip-tc" not in lx.get("argv", []):
                            errors.append(f"{launcher}: frozen scorer pin or --skip-tc mismatch")
                elif stage == "scores": errors.append(f"{launcher}: missing")
    if len(completion_checks) != 64 or not all(x["present"] for x in completion_checks):
        errors.append("expected 64 preserved normal completion receipts")
    # Raw diagnostics and retry source/log payloads remain immutable in their original directories;
    # the call manifests below are their compact, hashes-and-paths retrieval pointers.
    manifest_path = P / "strict_retry_manifest.json"
    retry_provenance, retry_manifest = audit_retry_manifest(manifest_path if manifest_path.is_file() else None, errors)
    negatives = original_negative_audit(retry_manifest if manifest_path.is_file() else {}, errors)
    # Include retry D-109 calls in the same compact call pointer table; their source/log bytes stay remote.
    for prov in retry_provenance:
        retry_launcher = Path(prov["launcher_path"])
        for execution_path in sorted(retry_launcher.parent.glob("call_*/execution.json")):
            rec, _ = verify_execution(execution_path, errors, retry=True)
            rec.update({"stage": "strict_retry", "job": prov["retry_job_name"]})
            calls.append(rec)
            call_states[f"strict_retry:{rec['state']}"] += 1
    failed_attempts = failed_attempt_pointers()
    if manifest_path.is_file(): add_file(manifest, manifest_path, "strict_retry_manifest")
    for prov in retry_provenance:
        for key, kind in (("retry_table_path", "strict_retry_table"), ("terminal_receipt_path", "strict_retry_terminal_receipt"),
                          ("launcher_path", "strict_retry_launcher")):
            add_file(manifest, Path(prov[key]), kind)
        receipt = Path(prov["launcher_path"]).parent.parent / "completion_receipt.txt"
        add_file(manifest, receipt, "strict_retry_completion_receipt")
    # Builder-owned overlay and unresolved-infrastructure records are independently bundled when present.
    for explicit, kind in ((P / "phase0_strict_retry_provenance.csv", "builder_strict_retry_provenance"),
                           (P / "phase0_infrastructure_issues.csv", "infrastructure_issues")):
        add_file(manifest, explicit, kind)
    for name, rows in (("score_output_manifest.csv", manifest), ("compiler_call_manifest.csv", calls),
                       ("normal_completion_receipts.csv", completion_checks), ("original_negative_compiler_calls.csv", negatives),
                       ("strict_retry_provenance.csv", retry_provenance), ("failed_attempt_manifest.csv", failed_attempts)):
        # Always emit headers even for optional retry streams, preserving an auditable empty result.
        fields = list(rows[0]) if rows else {"score_output_manifest.csv":["path","sha256","bytes","kind"],
            "compiler_call_manifest.csv":["stage","job","path","sha256","state","exit_code","timed_out","negative_exit","timeout_scored_failure","compiler_sha256","stdout_sha256","stdout_bytes","stderr_sha256","stderr_bytes","sources"],
            "normal_completion_receipts.csv":["stage","job","receipt","present"],
            "original_negative_compiler_calls.csv":["original_job_name","chunk","sample_idx","task_id","original_execution_path","original_execution_sha256","original_exit_code","original_source_sha256","original_source_paths_json","retry_job_name","retry_source_sha256","classification"],
            "strict_retry_provenance.csv":["task_id","chunk","sample_idx","retry_job_name","retry_slurm_job_id","source_sha256","expected_scorer_pin","original_source_path","retry_source_path","retry_table_path","retry_table_sha256","terminal_receipt_path","terminal_receipt_sha256","launcher_path","launcher_sha256","manifest_path","manifest_sha256"],
            "failed_attempt_manifest.csv":["path","sha256","bytes","kind"]}[name]
        with (O / name).open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(rows)
    summary = {"created_unix": time.time(), "cpu_only": True, "collector_source_sha256": sha(Path(__file__)),
        "builder_source_sha256": sha(builder) if builder.is_file() else None,
        "original_outputs": len(manifest), "compiler_calls": len(calls), "call_states": dict(call_states), "normal_completion_checks": len(completion_checks),
        "normal_completion_receipts_present": sum(x["present"] for x in completion_checks), "strict_retry_overrides": len(retry_provenance),
        "original_negative_calls": len(negatives), "original_negative_calls_recovered": sum(x["classification"] == "recovered_named_retry" for x in negatives), "failed_attempt_pointer_rows": len(failed_attempts), "errors": errors}
    (O / "diagnostic_audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    archive = P / "phase0_cpu_tables.tgz"
    with tarfile.open(archive, "w:gz") as tf:
        for p in (P / "phase0_gen_receipts.csv", P / "phase0_cells_e20.csv", P / "phase0_summary_e20.json", *O.iterdir()):
            if p.is_file(): tf.add(p, arcname=str(p.relative_to(P)))
        for row in manifest:
            p = Path(row["path"])
            if p.is_file(): tf.add(p, arcname=str(p.relative_to(P)))
    print(json.dumps(summary, sort_keys=True))
    print(sha(archive), str(archive))
    return int(bool(errors))

if __name__ == "__main__":
    raise SystemExit(main())
