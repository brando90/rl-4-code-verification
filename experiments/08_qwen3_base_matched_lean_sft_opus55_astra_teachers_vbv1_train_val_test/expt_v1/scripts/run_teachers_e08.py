#!/usr/bin/env python3
"""TLDR: Drive experiment 08's Valkyrie teacher runs (PROTOCOL § 3): admit one `vb103_single_call` run per (teacher, sample) with the locked selectors and settings (2 preflight samples on the first 2 train ids, then r = 1…4 over the 539 train ids), poll status, harvest results and output artifacts into the host-only raw tree, check every delivered prompt hash and the § 5 extraction consistency, and write secret-free per-cell receipts plus the cells JSONL the scorer adapter consumes; every model call goes through `valk run start` (D-108, D-015). Adapted from experiment 02A v3's `run_teachers.py`."""
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

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "src"))
EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
PRIVATE = WORK / "private"
RAW = WORK / "raw"
BENCHMARK = "rl4cv-e08-vbv1-train"
AGENT = "vb103_single_call"
STATE = EXP / "results" / "runs_state.json"
TRAIN_IDS = EXP / "results" / "split" / "vbv1_train_task_ids.txt"
PREFLIGHT_IDS = WORK / "preflight_ids.txt"
# PROTOCOL § 3 teachers, confirmed against the 10-07-2026 registry dump (results/route_identity_e08.json).
TEACHERS = {
    "opus55": {"model_name": "Claude Opus 5.5", "selector": "anthropic/claude-opus-5-5-no-fallback",
               "kwargs": {"addendum": "vbv1", "max_tokens": "128000", "compute_effort": "max"},
               "why": "the only Opus 5.5 selector with fallback_models = []; compute_effort max is the highest the registry allows (its default); temperature not passed"},
    "astra": {"model_name": "GPT-6 Astra", "selector": "openai/gpt-6-astra-max",
              "kwargs": {"addendum": "vbv1", "max_tokens": "128000", "reasoning_effort": "max"},
              "why": "the highest reasoning-effort selector the registry serves (max > xhigh > high > medium > low); no fallback models; temperature unsupported, not sent"},
}
SAMPLES = {"preflight": ("p1", "p2"), "main": ("s1", "s2", "s3", "s4")}
PROVIDER_ENV = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "MODEL_GATEWAY_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN",
                "ANTHROPIC_AUTH_TOKEN", "VALKYRIE_API_KEY", "TRACKER_SERVICE_URL", "PYTHONPATH", "PYTHONHOME")
RECEIPT_KEYS = ("condition", "task_id", "selector", "benchmark", "addendum", "started", "ended", "updated", "status", "requests_sent", "attempt",
                "wall_seconds", "usage", "cost_usd", "finish_reason", "fallback", "provider_endpoint", "config", "instruction_sha256",
                "addendum_sha256", "prompt_sha256", "system_prompt_sha256", "prompt_bytes", "required_paths", "response_sha256",
                "output_text_sha256", "output_text_bytes", "extraction", "model_labels", "unmapped_labels", "written_files", "missing_paths",
                "reason", "error_kind", "http_status", "error", "error_type", "note")
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
CLEAN_FINISH = {"stop", "end_turn", "completed", "finished", "eos"}
TERMINAL = {"finished", "completed", "error", "failed", "stopped", "cancelled", "canceled", "success", "succeeded"}


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
    return read_json(STATE, {"created_utc": stamp(), "benchmark": BENCHMARK, "agent": AGENT, "runs": {}})


def save_state(state: dict) -> None:
    state["updated_utc"] = stamp()
    write_json(STATE, state)


def read_ids(path: Path) -> list[str]:
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def ids_file(phase: str) -> Path:
    if phase == "main":
        return TRAIN_IDS
    if not PREFLIGHT_IDS.exists():
        PREFLIGHT_IDS.write_text("".join(t + "\n" for t in read_ids(TRAIN_IDS)[:2]), encoding="utf-8")
    return PREFLIGHT_IDS


def labels(phase: str, teacher: str, sample: str) -> tuple[str, str]:
    """(run label, -k benchmark) per PROTOCOL § 3 / § 12.7; the -k benchmark makes the gateway query_id distinct per sample."""
    if phase == "main":
        return f"rl4cv-e08-v1-{teacher}-{sample}", f"rl4cv-e08-{teacher}-{sample}"
    return f"rl4cv-e08-preflight-{teacher}-{sample}", f"rl4cv-e08-preflight-{teacher}-{sample}"


def cmd_admit(a) -> int:
    if a.sample not in SAMPLES[a.phase]:
        raise SystemExit(f"sample {a.sample} is not one of {SAMPLES[a.phase]} for phase {a.phase}")
    t = TEACHERS[a.teacher]
    state = load_state()
    key = f"{a.phase}/{a.teacher}/{a.sample}"
    if key in state["runs"] and state["runs"][key].get("run_id") and not a.force:
        raise SystemExit(f"{key}: already admitted as {state['runs'][key]['run_id']}; refusing a second admission")
    if not (PRIVATE / "valkyrie.yaml").exists():
        raise SystemExit("private Valkyrie config missing; deploy the service first")
    label, kbench = labels(a.phase, a.teacher, a.sample)
    ids_path = ids_file(a.phase)
    n_tasks = len(read_ids(ids_path))
    cmd = ["run", "start", "--agent", AGENT, "--benchmark", BENCHMARK, "--dataset", "default", "--model", t["selector"], "--task-ids-file", str(ids_path),
           "--concurrency", str(a.concurrency), "--label", label]
    for k, v in {**t["kwargs"], "benchmark": kbench}.items():
        cmd += ["-k", k, v]
    entry = {"phase": a.phase, "teacher": a.teacher, "sample": a.sample, "selector": t["selector"], "kwargs": {**t["kwargs"], "benchmark": kbench}, "label": label,
             "concurrency": a.concurrency, "expected_cells": n_tasks, "task_ids_file": str(ids_path), "task_ids_sha256": sha(ids_path.read_bytes()),
             "command": ["valk", *cmd], "admitted_utc": stamp(), "status": "admitting"}
    state["runs"][key] = entry
    save_state(state)
    done = valk(*cmd, timeout=900)
    (PRIVATE / f"admit_{a.phase}_{a.teacher}_{a.sample}.log").write_text(done.stdout + "\n" + done.stderr)
    found = UUID_RE.findall(done.stdout + done.stderr)
    if done.returncode or not found:
        entry.update(status="admission_failed", returncode=done.returncode, stderr_tail=(done.stderr or done.stdout)[-800:])
        save_state(state)
        print(json.dumps({key: entry["status"], "rc": done.returncode, "tail": (done.stderr or done.stdout)[-400:]}))
        return 2
    entry.update(status="running", run_id=found[0])
    save_state(state)
    print(json.dumps({key: "running", "run_id": found[0], "expected_cells": n_tasks, "selector": t["selector"], "kwargs": entry["kwargs"], "label": label}))
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
        entry["status"] = "terminal" if status in TERMINAL else "running"
        summary[key] = {"run_status": status, "counts": counts, "expected": entry["expected_cells"], "phase_state": entry["status"], "run_id": run_id}
    save_state(state)
    print(json.dumps(summary, indent=1))
    all_terminal = all(v.get("phase_state") == "terminal" for v in summary.values()) if summary else False
    return 0 if all_terminal else 1


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
    found = {}
    for path in sorted(artifacts.rglob("receipt.json")):
        try:
            receipt = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        tid = receipt.get("task_id") or path.parent.name
        found[tid] = (receipt, path.parent)
    for tb in sorted(artifacts.rglob("*.tar.gz")):   # some runs deliver the final_output directory as a tarball per task
        try:
            with tarfile.open(tb) as tf:
                members = {m.name.rsplit("/", 1)[-1]: m for m in tf.getmembers() if m.isfile()}
                if "receipt.json" in members:
                    receipt = json.loads(tf.extractfile(members["receipt.json"]).read())
                    tid = receipt.get("task_id") or tb.parent.name
                    if tid not in found:
                        dest = tb.parent / "extracted"
                        dest.mkdir(exist_ok=True)
                        for name in ("receipt.json", "response.txt"):
                            if name in members:
                                (dest / name).write_bytes(tf.extractfile(members[name]).read())
                        found[tid] = (receipt, dest)
        except (tarfile.TarError, json.JSONDecodeError):
            continue
    return found


def cmd_harvest(a) -> int:
    from rl4cv.veribench.exp103 import extract_lean

    state = load_state()
    key = f"{a.phase}/{a.teacher}/{a.sample}"
    entry = state["runs"][key]
    run_id = entry["run_id"]
    raw = RAW / a.teacher / a.sample if a.phase == "main" else RAW / "preflight" / a.teacher / a.sample
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
    receipts = _receipts(artifacts) if artifacts.exists() else {}
    expected = read_ids(Path(entry["task_ids_file"]))
    pack_check = read_json(EXP / "results" / "pack_check.json")
    prompt_sha = {r["task_id"]: r["prompt_sha256"] for r in pack_check["tasks"]}
    required_path = {r["task_id"]: r["required_path"] for r in pack_check["tasks"]}
    cells, receipts_out, counts = [], [], {}
    for tid in expected:
        row = rows.get(tid, {})
        receipt, rdir = receipts.get(tid, ({}, None))
        lean, lean_source = None, None
        if row.get("solution_b64"):
            lean, lean_source = base64.b64decode(row["solution_b64"]).decode("utf-8", errors="replace"), "service_collected"
        response_text = None
        if rdir is not None and (rdir / "response.txt").exists():
            response_text = (rdir / "response.txt").read_text(encoding="utf-8", errors="replace")
        extracted = None
        if response_text is not None:
            ext = extract_lean(response_text, (required_path[tid],))
            if ext.lean:
                extracted = ext.lean if ext.lean.endswith("\n") else ext.lean + "\n"
        if lean is None and extracted is not None:
            lean, lean_source = extracted, "recovered_from_run_output"
        # PROTOCOL § 5 consistency: host-side extraction of the full response must reproduce the scored file byte for byte.
        consistent = (lean is not None and extracted is not None and lean == extracted) if lean is not None else None
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
        if receipt.get("system_prompt_sha256") and receipt["system_prompt_sha256"] != pack_check["prompt"]["system_prompt_sha256"]:
            raise RuntimeError(f"{tid}: delivered system prompt hash differs from the pack check")
        if receipt.get("addendum_sha256") and receipt["addendum_sha256"] != pack_check["prompt"]["addendum_sha256"]:
            raise RuntimeError(f"{tid}: delivered addendum hash differs from the pack check")
        usage = receipt.get("usage") or {}
        cell = {"task_id": tid, "teacher": a.teacher, "r": a.sample, "phase": a.phase, "model": entry["selector"], "run_id": run_id, "status": status or "missing",
                "served": served, "unserved_evidence": unserved_evidence, "measured": served and bool(lean), "finish_reason": finish_s or None,
                "truncated": bool(responded and finish_s and finish_s not in CLEAN_FINISH), "extraction": receipt.get("extraction"),
                "requests_sent": requests_sent, "cost_usd": receipt.get("cost_usd"), "generated_tokens": usage.get("out_tokens"),
                "reasoning_tokens": usage.get("reasoning_tokens"), "in_tokens": usage.get("in_tokens"),
                "prompt_sha256": receipt.get("prompt_sha256") or prompt_sha.get(tid),
                "prompt_hash_matches_pack": (receipt.get("prompt_sha256") == prompt_sha.get(tid)) if receipt.get("prompt_sha256") else None,
                "submission_status": row.get("submission_status"), "solution_sha256_service": row.get("solution_sha256"),
                "lean_source": lean_source, "lean_sha256": sha(lean.encode("utf-8")) if lean else None, "lean_bytes": len(lean.encode("utf-8")) if lean else 0,
                "response_sha256": receipt.get("response_sha256"), "response_text_sha256": sha(response_text.encode("utf-8")) if response_text is not None else None,
                "response_text_bytes": len(response_text.encode("utf-8")) if response_text is not None else None, "response_path": str(rdir / "response.txt") if response_text is not None else None,
                "extraction_consistent": consistent, "fallback": receipt.get("fallback"), "wall_seconds": receipt.get("wall_seconds"), "lean": lean}
        cells.append(cell)
        receipts_out.append({"run_id": run_id, "phase": a.phase, "teacher": a.teacher, "r": a.sample, "served": served, "unserved_evidence": unserved_evidence,
                             "lean_source": lean_source, "lean_sha256": cell["lean_sha256"], "response_text_sha256": cell["response_text_sha256"],
                             "extraction_consistent": consistent, "submission_status": row.get("submission_status"),
                             **{k: receipt[k] for k in RECEIPT_KEYS if k in receipt}})
        counts[cell["status"]] = counts.get(cell["status"], 0) + 1
    with (raw / "cells.jsonl").open("w", encoding="utf-8") as fh:
        for c in cells:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    rdir_out = EXP / "results" / "receipts" / a.phase
    rdir_out.mkdir(parents=True, exist_ok=True)
    with (rdir_out / f"{a.teacher}_{a.sample}.jsonl").open("w", encoding="utf-8") as fh:
        for r in receipts_out:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    charges = round(sum(c["cost_usd"] or 0.0 for c in cells), 4)
    summary = {"run_id": run_id, "n_expected": len(expected), "n_results_rows": len(rows), "n_receipts": len(receipts), "status_counts": counts,
               "n_served": sum(c["served"] for c in cells), "n_with_lean": sum(bool(c["lean"]) for c in cells), "n_unserved": sum(not c["served"] for c in cells),
               "n_truncated": sum(c["truncated"] for c in cells), "n_inconsistent_extraction": sum(1 for c in cells if c["extraction_consistent"] is False),
               "charges_usd_reported": charges, "harvested_utc": stamp(), "results_json_ok": results_path.exists(), "cells_jsonl": str(raw / "cells.jsonl")}
    entry["harvest"] = summary
    save_state(state)
    print(json.dumps(summary, indent=1))
    return 0


def cmd_preflight_check(a) -> int:
    """PROTOCOL § 12.7: 8 cells scored end to end elsewhere; here the per-teacher independence check on response hashes and the receipt summary."""
    out = {"written_utc": stamp(), "teachers": {}, "verdict": "PASS"}
    for teacher in TEACHERS:
        per = {}
        for sample in SAMPLES["preflight"]:
            p = RAW / "preflight" / teacher / sample / "cells.jsonl"
            if not p.exists():
                out["teachers"][teacher] = {"missing": str(p)}
                out["verdict"] = "FAIL"
                break
            per[sample] = {c["task_id"]: c for c in (json.loads(l) for l in p.read_text().splitlines() if l.strip())}
        else:
            tids = sorted(set(per["p1"]) | set(per["p2"]))
            differs = {t: (per["p1"].get(t, {}).get("response_text_sha256") != per["p2"].get(t, {}).get("response_text_sha256")) for t in tids}
            served = all(per[s][t]["served"] for s in per for t in tids if t in per[s])
            out["teachers"][teacher] = {"task_ids": tids, "response_hash_differs_between_samples": differs, "independent": any(differs.values()),
                                        "all_served": served, "cells": {s: {t: {k: c.get(k) for k in ("status", "finish_reason", "truncated", "extraction", "requests_sent",
                                                                                                        "cost_usd", "generated_tokens", "reasoning_tokens", "lean_sha256",
                                                                                                        "response_text_sha256", "extraction_consistent", "fallback", "wall_seconds")}
                                                                                for t, c in per[s].items()} for s in per},
                                        "charges_usd": round(sum(c.get("cost_usd") or 0.0 for s in per for c in per[s].values()), 4)}
            if not any(differs.values()):
                out["verdict"] = "BLOCKED: identical responses across samples (sampling suspected cached)"
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"verdict": out["verdict"], **{t: {"independent": v.get("independent"), "all_served": v.get("all_served"), "charges_usd": v.get("charges_usd")}
                                                   for t, v in out["teachers"].items()}}))
    return 0 if out["verdict"] == "PASS" else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("admit")
    p.add_argument("--teacher", choices=sorted(TEACHERS), required=True)
    p.add_argument("--phase", choices=["preflight", "main"], required=True)
    p.add_argument("--sample", required=True, help="p1/p2 for preflight, s1..s4 for main")
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("status")
    p.add_argument("--phase")
    p = sub.add_parser("harvest")
    p.add_argument("--teacher", choices=sorted(TEACHERS), required=True)
    p.add_argument("--phase", choices=["preflight", "main"], required=True)
    p.add_argument("--sample", required=True)
    p = sub.add_parser("preflight-check")
    p.add_argument("--out", type=Path, default=EXP / "results" / "preflight_e08.json")
    sub.add_parser("teachers")
    a = ap.parse_args()
    if a.cmd == "teachers":
        print(json.dumps(TEACHERS, indent=1))
        return 0
    return {"admit": cmd_admit, "status": cmd_status, "harvest": cmd_harvest, "preflight-check": cmd_preflight_check}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
