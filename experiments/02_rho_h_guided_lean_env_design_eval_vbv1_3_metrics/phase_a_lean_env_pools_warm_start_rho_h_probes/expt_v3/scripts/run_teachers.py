#!/usr/bin/env python3
"""TLDR: Drive the Valkyrie teacher runs for experiment 02A v3 (admit one `vb103_single_call` run per teacher with the locked settings, poll status, harvest results and output artifacts into the host-only raw tree, and write secret-free per-cell receipts plus the cells JSONL the scorer adapter consumes); every model call goes through `valk run start` (D-108, D-014)."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "src"))
EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E02A_WORK", "/lfs/skampere1/0/brando9/rl4cv_e02a_v3"))
PRIVATE = WORK / "private"
RAW = WORK / "raw"
BENCHMARK = "rl4cv-e02a-v3-mbpp"
AGENT = "vb103_single_call"
STATE = EXP / "results" / "runs_state.json"
# PROTOCOL § 4 teachers, pinned against the registry dump in results/route_identity_e02a_v3.json (10-07-2026).
TEACHERS = {
    "anthropic": {"family": "Anthropic", "model_name": "Claude Fable 5.1", "selector": "anthropic/claude-fable-5-1-no-fallback",
                  "kwargs": {"max_tokens": "128000", "compute_effort": "max", "addendum": "vbv1", "benchmark": BENCHMARK},
                  "why": "the only Fable 5.1 selector with fallback_models = []; compute_effort max is the highest the registry allows (its default)"},
    "openai": {"family": "OpenAI", "model_name": "GPT-6 Astra", "selector": "openai/gpt-6-astra-max",
               "kwargs": {"max_tokens": "128000", "reasoning_effort": "max", "addendum": "vbv1", "benchmark": BENCHMARK},
               "why": "the highest reasoning-effort selector the registry serves (max > xhigh > high); no fallback models; temperature unsupported, not sent"},
    "google": {"family": "Google", "model_name": "Gemini 4 Argon", "selector": "google/gemini-4-argon",
               "kwargs": {"max_tokens": "128000", "reasoning_effort": "high", "temperature": "1.0", "addendum": "vbv1", "benchmark": BENCHMARK},
               "why": "reasoning_effort high is its highest; temperature 1.0 as the registry default; max_tokens 128,000 (registry allows 262,144) "
                      "to give every teacher the same output budget"},
}
PROVIDER_ENV = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN",
                "VALKYRIE_API_KEY", "TRACKER_SERVICE_URL", "PYTHONPATH", "PYTHONHOME")
RECEIPT_KEYS = ("condition", "task_id", "selector", "benchmark", "addendum", "started", "ended", "updated", "status", "requests_sent", "attempt",
                "wall_seconds", "usage", "cost_usd", "finish_reason", "fallback", "provider_endpoint", "config", "instruction_sha256",
                "addendum_sha256", "prompt_sha256", "system_prompt_sha256", "prompt_bytes", "required_paths", "response_sha256",
                "output_text_sha256", "output_text_bytes", "extraction", "model_labels", "unmapped_labels", "written_files", "missing_paths",
                "reason", "error_kind", "http_status", "error", "error_type", "note")
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
CLEAN_FINISH = {"stop", "end_turn", "completed", "finished", "eos"}


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    tmp.replace(path)


def valk(*args: str, timeout: float = 1800) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in PROVIDER_ENV}
    env.update(VALKYRIE_ENV="bench", VALKYRIE_CONFIG_PATH=str(PRIVATE / "valkyrie.yaml"))
    return subprocess.run(["valk", *args], env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)


def load_state() -> dict:
    return read_json(STATE, {"created_utc": stamp(), "runs": {}})


def save_state(state: dict) -> None:
    state["updated_utc"] = stamp()
    write_json(STATE, state)


def cmd_admit(a) -> int:
    t = TEACHERS[a.teacher]
    state = load_state()
    key = f"{a.phase}/{a.teacher}"
    if key in state["runs"] and state["runs"][key].get("run_id") and not a.force:
        raise SystemExit(f"{key}: already admitted as {state['runs'][key]['run_id']}; refusing a second admission")
    if not (PRIVATE / "valkyrie.yaml").exists():
        raise SystemExit("private Valkyrie config missing; deploy the service first")
    cmd = ["run", "start", "--agent", AGENT, "--benchmark", BENCHMARK, "--dataset", "default", "--model", t["selector"],
           "--concurrency", str(a.concurrency), "--label", a.label or f"rl4cv-e02a-v3-{a.phase}-{a.teacher}"]
    if a.task_ids_file:
        cmd += ["--task-ids-file", str(a.task_ids_file)]
        n_tasks = len([l for l in Path(a.task_ids_file).read_text().splitlines() if l.strip()])
    else:
        cmd += ["--task-ids", a.task_ids]
        n_tasks = len(a.task_ids.split(","))
    for k, v in t["kwargs"].items():
        cmd += ["-k", k, v]
    entry = {"phase": a.phase, "teacher": a.teacher, "selector": t["selector"], "kwargs": t["kwargs"], "concurrency": a.concurrency,
             "expected_cells": n_tasks, "task_ids_file": str(a.task_ids_file) if a.task_ids_file else None,
             "task_ids": None if a.task_ids_file else a.task_ids, "command": ["valk", *cmd], "admitted_utc": stamp(), "status": "admitting"}
    state["runs"][key] = entry
    save_state(state)
    done = valk(*cmd, timeout=900)
    (PRIVATE / f"admit_{a.phase}_{a.teacher}.log").write_text(done.stdout + "\n" + done.stderr)
    found = UUID_RE.findall(done.stdout + done.stderr)
    if done.returncode or not found:
        entry.update(status="admission_failed", returncode=done.returncode, stderr_tail=(done.stderr or done.stdout)[-800:])
        save_state(state)
        print(json.dumps({key: entry["status"], "rc": done.returncode, "tail": (done.stderr or done.stdout)[-400:]}))
        return 2
    entry.update(status="running", run_id=found[0])
    save_state(state)
    print(json.dumps({key: "running", "run_id": found[0], "expected_cells": n_tasks, "selector": t["selector"], "kwargs": t["kwargs"]}))
    return 0


def _status_row(payload):
    runs = payload.get("runs") if isinstance(payload, dict) else payload
    if isinstance(runs, list):
        return runs[0] if runs else {}
    return runs if isinstance(runs, dict) else {}


def cmd_status(a) -> int:
    state = load_state()
    summary = {}
    for key, entry in state["runs"].items():
        run_id = entry.get("run_id")
        if not run_id or (a.phase and not key.startswith(a.phase + "/")):
            continue
        done = valk("run", "status", "--ids", run_id, "--format", "json", timeout=600)
        try:
            row = _status_row(json.loads(done.stdout))
        except json.JSONDecodeError:
            summary[key] = {"poll_error": True, "tail": (done.stderr or done.stdout)[-300:]}
            continue
        counts = row.get("task_state_counts") or row.get("task_states") or row.get("task_counts") or {}
        status = str(row.get("status") or row.get("state") or "").lower()
        entry.update(run_status=status, task_state_counts=counts, polled_utc=stamp(), status_raw_keys=sorted(row.keys()))
        terminal = status in {"finished", "completed", "error", "failed", "stopped", "cancelled", "canceled", "success", "succeeded"}
        entry["status"] = "terminal" if terminal else "running"
        summary[key] = {"run_status": status, "counts": counts, "expected": entry["expected_cells"], "phase_state": entry["status"]}
    save_state(state)
    print(json.dumps(summary, indent=1))
    return 0


def _rows_of(results_path: Path) -> dict[str, dict]:
    payload = json.loads(results_path.read_text())
    blob = payload[0] if isinstance(payload, list) and payload else payload
    raw = blob.get("evaluation_results") or blob.get("results") or blob.get("task_results") or {}
    out = {}
    for task_id, value in raw.items():
        row = value.get("result", value) if isinstance(value, dict) else value
        out[task_id] = row if isinstance(row, dict) else {}
    return out


def _receipts(artifacts: Path) -> dict[str, tuple[dict, Path]]:
    """task_id -> (receipt, directory holding receipt.json and, when the agent wrote one, response.txt).

    `valk run output` delivers each task's `receipt.json` next to `agent_output.tar.gz` (the agent's /logs/vb103 final
    output, which also carries response.txt); the tarball is always unpacked beside the receipt.
    """
    found = {}
    for tb in sorted(artifacts.rglob("*.tar.gz")):
        try:
            with tarfile.open(tb) as tf:
                members = {m.name.rsplit("/", 1)[-1]: m for m in tf.getmembers() if m.isfile()}
                dest = tb.parent / "extracted"
                dest.mkdir(exist_ok=True)
                for name in ("receipt.json", "response.txt"):
                    if name in members:
                        (dest / name).write_bytes(tf.extractfile(members[name]).read())
        except tarfile.TarError:
            continue
    for path in sorted(artifacts.rglob("receipt.json")):
        try:
            receipt = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        tid = receipt.get("task_id") or path.parent.name
        prev = found.get(tid)
        if prev is None or ((path.parent / "response.txt").exists() and not (prev[1] / "response.txt").exists()):
            found[tid] = (receipt, path.parent)
    return found


def _run_record_rows(artifacts: Path) -> dict[str, dict]:
    """The per-task rows from the run record `valk run output` delivers (`<benchmark>.json` → evaluation_results)."""
    for path in sorted(artifacts.glob("*.json")):
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("evaluation_results"):
            return {tid: (v.get("result", v) if isinstance(v, dict) else {}) for tid, v in payload["evaluation_results"].items()}
    return {}


def cmd_harvest(a) -> int:
    from rl4cv.veribench.exp103 import extract_lean

    state = load_state()
    key = f"{a.phase}/{a.teacher}"
    entry = state["runs"][key]
    run_id = entry["run_id"]
    raw = RAW / a.phase / a.teacher
    raw.mkdir(parents=True, exist_ok=True)
    results_path, artifacts = raw / "results.json", raw / "artifacts"
    if results_path.exists():
        results_path.unlink()
    shutil.rmtree(artifacts, ignore_errors=True)
    log = []
    for cmd in (["run", "results", run_id, "--path", str(results_path)], ["run", "output", run_id, "-o", str(artifacts)]):
        done = valk(*cmd, timeout=3600)
        log.append(f"{stamp()} valk {' '.join(cmd[:2])} rc={done.returncode}\n{done.stdout[-1500:]}\n{done.stderr[-1500:]}\n")
    (raw / "harvest.log").write_text("".join(log))
    rows = _rows_of(results_path) if results_path.exists() else {}
    rows_source = "valk run results"
    if not rows and artifacts.exists():
        # `valk run results` has returned "tracker returned a malformed response" since experiment 01's Argon test; the run
        # record delivered by `valk run output` carries the same per-cell rows (service-collected bytes and hashes).
        rows, rows_source = _run_record_rows(artifacts), "run record from valk run output"
    receipts = _receipts(artifacts) if artifacts.exists() else {}
    expected = [l.strip() for l in Path(entry["task_ids_file"]).read_text().splitlines() if l.strip()] if entry.get("task_ids_file") else entry["task_ids"].split(",")
    pack_manifest = read_json(EXP / "results" / "pack_manifest.json")
    prompt_sha = {r["task_id"]: r["prompt_sha256"] for r in pack_manifest["tasks"]}
    prompt_sha[pack_manifest["preflight"]["task_id"]] = pack_manifest["preflight"]["prompt_sha256"]
    cells, receipts_out, counts = [], [], {}
    for tid in expected:
        row = rows.get(tid, {})
        receipt, rdir = receipts.get(tid, ({}, None))
        lean, lean_source = None, None
        if row.get("solution_b64"):
            lean, lean_source = base64.b64decode(row["solution_b64"]).decode("utf-8", errors="replace"), "service_collected"
        elif rdir is not None and (rdir / "response.txt").exists() and receipt.get("required_paths"):
            ext = extract_lean((rdir / "response.txt").read_text(encoding="utf-8", errors="replace"), tuple(receipt["required_paths"]))
            if ext.lean:
                lean, lean_source = ext.lean if ext.lean.endswith("\n") else ext.lean + "\n", "recovered_from_run_output"
        status = receipt.get("status")
        responded = bool(receipt.get("response_sha256")) or status in {"measured", "incomplete", "model_error"}
        requests_sent = int(receipt.get("requests_sent") or 0)
        http = receipt.get("http_status")
        if not receipt:
            served, unserved_evidence = False, "no agent receipt (sandbox or service failed before the agent started)"
        elif responded:
            served, unserved_evidence = True, None
        elif requests_sent == 0:
            served, unserved_evidence = False, "requests_sent = 0"
        elif receipt.get("error_kind") == "HTTPError" and http in (429, 500, 502, 503, 504):
            served, unserved_evidence = False, f"every request ended in HTTP {http} with no response"
        else:
            served, unserved_evidence = True, None   # a timeout or unknown failure may have been served: never re-sent
        finish = receipt.get("finish_reason")
        finish_s = str((finish or {}).get("reason") if isinstance(finish, dict) else finish or "").lower()
        if receipt.get("prompt_sha256") and prompt_sha.get(tid) and receipt["prompt_sha256"] != prompt_sha[tid]:
            raise RuntimeError(f"{tid}: delivered prompt hash {receipt['prompt_sha256']} != pack {prompt_sha[tid]}")
        cell = {"task_id": tid, "teacher": a.teacher, "model": entry["selector"], "run_id": run_id, "phase": a.phase, "status": status or "missing",
                "served": served, "unserved_evidence": unserved_evidence, "measured": served and bool(lean), "finish_reason": finish_s or None,
                "truncated": bool(responded and finish_s and finish_s not in CLEAN_FINISH), "extraction": receipt.get("extraction"),
                "requests_sent": requests_sent, "cost_usd": receipt.get("cost_usd"), "generated_tokens": (receipt.get("usage") or {}).get("out_tokens"),
                "reasoning_tokens": (receipt.get("usage") or {}).get("reasoning_tokens"), "in_tokens": (receipt.get("usage") or {}).get("in_tokens"),
                "prompt_sha256": receipt.get("prompt_sha256") or prompt_sha.get(tid), "prompt_hash_matches_pack": (receipt.get("prompt_sha256") == prompt_sha.get(tid)) if receipt.get("prompt_sha256") else None,
                "submission_status": row.get("submission_status"), "solution_sha256_service": row.get("solution_sha256"),
                "lean_source": lean_source, "lean_sha256": sha(lean.encode("utf-8")) if lean else None, "lean_bytes": len(lean.encode("utf-8")) if lean else 0,
                "fallback": receipt.get("fallback"), "wall_seconds": receipt.get("wall_seconds"), "lean": lean}
        cells.append(cell)
        receipts_out.append({"run_id": run_id, "phase": a.phase, "teacher": a.teacher, "served": served, "unserved_evidence": unserved_evidence,
                             "lean_source": lean_source, "lean_sha256": cell["lean_sha256"], "submission_status": row.get("submission_status"),
                             **{k: receipt[k] for k in RECEIPT_KEYS if k in receipt}})
        counts[cell["status"]] = counts.get(cell["status"], 0) + 1
    with (raw / "cells.jsonl").open("w", encoding="utf-8") as fh:
        for c in cells:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    rdir_out = EXP / "results" / "receipts" / a.phase
    rdir_out.mkdir(parents=True, exist_ok=True)
    with (rdir_out / f"{a.teacher}.jsonl").open("w", encoding="utf-8") as fh:
        for r in receipts_out:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    charges = round(sum(c["cost_usd"] or 0.0 for c in cells), 4)
    summary = {"run_id": run_id, "n_expected": len(expected), "n_results_rows": len(rows), "n_receipts": len(receipts), "status_counts": counts,
               "n_served": sum(c["served"] for c in cells), "n_with_lean": sum(bool(c["lean"]) for c in cells),
               "n_unserved": sum(not c["served"] for c in cells), "charges_usd_reported": charges, "harvested_utc": stamp(),
               "results_json_ok": results_path.exists(), "rows_source": rows_source, "cells_jsonl": str(raw / "cells.jsonl")}
    entry["harvest"] = summary
    save_state(state)
    print(json.dumps(summary, indent=1))
    return 0


def cmd_merge(a) -> int:
    """Final cells for a teacher: the main run's cells, with a positively unserved main cell replaced by its one identical
    recovery re-send (PROTOCOL § 4); every other main cell, served or not, is kept exactly as harvested."""
    main = {c["task_id"]: c for c in (json.loads(l) for l in (RAW / "main" / a.teacher / "cells.jsonl").read_text().splitlines() if l.strip())}
    rec_path = RAW / "recovery" / a.teacher / "cells.jsonl"
    recovery = {c["task_id"]: c for c in (json.loads(l) for l in rec_path.read_text().splitlines() if l.strip())} if rec_path.exists() else {}
    replaced, kept_unserved = [], []
    out = []
    for tid, c in main.items():
        if not c["served"] and tid in recovery:
            r = dict(recovery[tid])
            r.update(recovered_from_main=True, main_unserved_evidence=c["unserved_evidence"], requests_sent_total=(c.get("requests_sent") or 0) + (r.get("requests_sent") or 0))
            out.append(r)
            replaced.append(tid)
        else:
            if not c["served"]:
                kept_unserved.append(tid)
            out.append(c)
    final = RAW / "final" / a.teacher
    final.mkdir(parents=True, exist_ok=True)
    with (final / "cells.jsonl").open("w", encoding="utf-8") as fh:
        for c in out:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    summary = {"teacher": a.teacher, "n_main": len(main), "n_recovery_cells": len(recovery), "replaced_by_recovery": replaced, "still_unserved": kept_unserved,
               "n_served_final": sum(c["served"] for c in out), "n_with_lean_final": sum(bool(c.get("lean")) for c in out), "merged_utc": stamp()}
    state = load_state()
    state["runs"].setdefault(f"final/{a.teacher}", {}).update(summary)
    save_state(state)
    print(json.dumps({k: v for k, v in summary.items()}))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("admit")
    p.add_argument("--teacher", choices=sorted(TEACHERS), required=True)
    p.add_argument("--phase", choices=["preflight", "main", "recovery"], required=True)
    p.add_argument("--task-ids-file", type=Path)
    p.add_argument("--task-ids")
    p.add_argument("--concurrency", type=int, default=1)
    p.add_argument("--label")
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("status")
    p.add_argument("--phase")
    p = sub.add_parser("harvest")
    p.add_argument("--teacher", choices=sorted(TEACHERS), required=True)
    p.add_argument("--phase", choices=["preflight", "main", "recovery"], required=True)
    p = sub.add_parser("merge")
    p.add_argument("--teacher", choices=sorted(TEACHERS), required=True)
    p = sub.add_parser("teachers")
    a = ap.parse_args()
    if a.cmd == "teachers":
        print(json.dumps(TEACHERS, indent=1))
        return 0
    return {"admit": cmd_admit, "status": cmd_status, "harvest": cmd_harvest, "merge": cmd_merge}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
