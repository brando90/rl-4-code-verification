#!/usr/bin/env python3
"""TLDR: FSC judging for experiment 08's test evaluation (PROTOCOL § 10, D-102), adapted from experiment 01's `judge_rl4cv_e01.py`: experiment 103's frozen judge modules (`judge_pack`, experiment 100's `prompts`/`build_inputs`/`judge_run`) are imported from this clone's pinned checkout, never edited, and every path resolves inside this clone. Suites: `rl4cv-e08v2-controls` (oracle / vacuous / shuffled / halfdel / blank on TRAIN files, the D-108 route controls) and `rl4cv-e08v2:<system>` (every IC_tests = 1 test cell plus the fixed 60-file audit, keyed by system, task_id and sample_idx; three byte-identical repeats per cell and per ensemble member, i.e. six declared ratings per file). `fsc` combines member medians (mean of the two medians / 5) per cell. All model calls go through `valk run start --agent vb103_judge`."""
from __future__ import annotations

import argparse
import base64
import csv
import fcntl
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08/v2"))
EXT = REPO / "external" / "veribench"
E103 = EXT / "experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge"
X100 = EXT / "experiments/100_karpathy_recipe_tc_judge_search_human_train_val_test"
PRIVATE = E103 / "private" / "judge" / "rl4cv_e08v2"          # inside THIS clone's git-ignored pinned checkout (the frozen pack builder resolves paths under E103)
RESULTS = EXP / "results" / "judge"
PACK = Path("/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896")
E05_OUT = Path("/lfs/skampere1/0/brando9/rl4cv_e05/out")
AGENT = "vb103_judge"
CONFIGS = ("H2_sol_high", "H2_opus55_max")
RUBRIC = "H2_human_mirror_conventions_demos"
REPEATS = (1, 2, 3)
STATE = RESULTS / "state.json"
CORE_SPLITS = ("easy_set", "cs_set", "humaneval_set", "realcode_set", "security_set")
CONTROL_KINDS = ["oracle", "vacuous", "shuffled", "halfdel", "blank"]
CONTROL_EXPECTATIONS = {"control_oracle": ("score_raw >= 4", 0.90), "control_vacuous": ("score_raw <= 1", 0.90), "control_blank": ("score_raw == 0", 0.90),
                        "control_shuffled": ("score_raw <= 1", 0.90), "control_halfdel": ("1 <= score_raw <= 4", 0.80)}
PROVIDER_ENV = ("VALKYRIE_API_KEY", "TRACKER_SERVICE_URL", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "MODEL_GATEWAY_API_KEY",
                "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN", "PYTHONPATH", "PYTHONHOME")
UUID_RE = re.compile(r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}")
BENCH_PREFIX = "veribench-rl4cv-e08v2"
ROUTE_V1 = EXP / "results" / "route_identity_v2.json"                 # 10-13-2026 record (old per-user AWS route); never rewritten
ROUTE = EXP / "results" / "route_identity_hosted_v2.json"             # hosted-route evidence written by `preflight`
SERVICES = WORK / "private" / "services.json"                         # written by deploy_service_e08v2.py deploy/register
BUNDLE_SAME_AS_V1 = ("contract.yaml", "judge_call.py", "setup.sh")    # byte-identical, except contract.yaml may carry the slash-free secret name

sys.path[:0] = [str(X100 / "scripts"), str(E103 / "scripts"), str(REPO / "src")]
from rl4cv import valkyrie_hosted as hosted   # noqa: E402  hosted transport (10-14-2026); scientific settings unchanged
import common                          # noqa: E402  frozen, imported not edited
common.EXPT = X100
import prompts                         # noqa: E402
import build_inputs                    # noqa: E402
import judge_run                       # noqa: E402
import judge_pack                      # noqa: E402


def _control_ok(kind: str, score: int) -> bool:
    return {"control_oracle": score >= 4, "control_vacuous": score <= 1, "control_shuffled": score <= 1, "control_blank": score == 0,
            "control_halfdel": 1 <= score <= 4}[kind]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    tmp.replace(path)


def read_json(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def relative(path: Path) -> str:
    """A path experiment 100's common.read_text resolves: relative to X100's own dir, hopping into 103."""
    return "../" + str(path.relative_to(EXT / "experiments").as_posix())


def read_ids(path: Path) -> list[str]:
    return [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.startswith("#")]


def python_of(task_id: str) -> str:
    instruction = (PACK / task_id / "instruction.md").read_text(encoding="utf-8", errors="replace")
    blocks = re.findall(r"```python\n(.*?)```", instruction, re.S)
    return max(blocks, key=len) if blocks else ""


def suite_spec(suite: str) -> dict:
    if suite == "rl4cv-e08v2-controls":
        return {"suite": suite, "system": None, "benchmark": f"{BENCH_PREFIX}-controls", "pack_receipt": RESULTS / "judge_pack_controls.json", "key_prefix": "controls/",
                "part_field": "control_cells"}
    assert suite.startswith("rl4cv-e08v2:"), f"unknown suite: {suite}"
    system = suite.split(":", 1)[1]
    return {"suite": suite, "system": system, "benchmark": f"{BENCH_PREFIX}-test", "pack_receipt": RESULTS / "judge_pack_test.json", "key_prefix": f"{system}/",
            "part_field": "cells"}


# --------------------------------------------------------------------------------------------------
# Build: route controls on TRAIN files (D-108), zero model calls
# --------------------------------------------------------------------------------------------------
def build_controls(n_tasks: int = 6) -> dict:
    train = read_ids(EXP.parent / "expt_v1" / "results" / "split" / "vbv1_train_task_ids.txt")
    chosen: dict[str, str] = {}
    for tid in train:                         # first train task per core family (task-id order) whose gold states >= 2 theorems
        split = tid.split("__", 1)[0]
        if split not in CORE_SPLITS or split in chosen:
            continue
        gold = PACK / tid / "tests" / "gold.lean"
        if gold.exists() and len(build_inputs.statements(gold.read_text(encoding="utf-8", errors="replace"))) >= 2:
            chosen[split] = tid
    tasks = list(chosen.values())[:n_tasks]
    root = PRIVATE / "controls" / "inputs"
    items = []
    for task in tasks:
        gold_text = (PACK / task / "tests" / "gold.lean").read_text(encoding="utf-8", errors="replace")
        d = root / task
        d.mkdir(parents=True, exist_ok=True)
        (d / "gold.lean").write_text(gold_text, encoding="utf-8")
        (d / "source.py").write_text(python_of(task), encoding="utf-8")
        items.append({"item": task, "task": task, "split": task.split("__", 1)[0], "candidate_file": "gold.lean", "gold_file_name": "gold.lean",
                      "candidate_path": relative(d / "gold.lean"), "ref_ann_path": relative(d / "gold.lean"), "py_ann_path": relative(d / "source.py"),
                      "ref_placeholder_at_annotation": False, "n_ref_theorems_ann": len(build_inputs.statements(gold_text))})
    items_path = PRIVATE / "controls" / "items.jsonl"
    items_path.write_text("".join(json.dumps(r) + "\n" for r in items))
    by_task = {r["task"]: r for r in items}
    cells = [c for c in judge_run.build_cells(None, 1, CONTROL_KINDS, items_path=items_path) if c["kind"] != "main"]
    rendered_dir = PRIVATE / "controls" / "rendered"
    rows = []
    for cell in cells:
        text, _extra = judge_run.candidate_text(cell)
        system, user = prompts.render(RUBRIC, by_task[cell["task"]], text, cell["cand_name"])
        write_json(rendered_dir / f"{cell['cell']}.json", {"system": system, "user": user})
        rows.append({"cell": cell["cell"], "item": cell["item"], "task": cell["task"], "repeat": cell["repeat"], "kind": cell["kind"], "candidate_sha256": sha(text.encode()),
                     "prompt_sha256": sha((system + "\n\n" + user).encode())})
    receipt_path = PRIVATE / "controls" / "cells_receipt.json"
    write_json(receipt_path, {"cells": rows})
    pack_path = PRIVATE / "packs" / "judge_rl4cv_e08v2_controls"
    judge_pack.RENDERED = rendered_dir
    manifest = judge_pack.build(pack_path, receipt_path, "judge", smoke_items=0)
    manifest["round_trip"] = judge_pack.verify(pack_path, manifest)
    manifest.update(written_utc=stamp(), verdict="PASS" if not manifest["round_trip"]["failures"] else "FAIL", tasks=tasks, split="train",
                    pack_abs=str(pack_path), rubric=RUBRIC, rubric_fingerprint=prompts.rubric_fingerprint(RUBRIC), configs=list(CONFIGS))
    write_json(suite_spec("rl4cv-e08v2-controls")["pack_receipt"], manifest)
    return manifest


# --------------------------------------------------------------------------------------------------
# Build: every IC_tests = 1 test cell per system + the fixed 60-file audit; 3 repeats; one pack for all systems
# --------------------------------------------------------------------------------------------------
def audit_cells(test_ids: list[str], per_core_split: int = 12) -> list[tuple[str, int]]:
    """12 cells per core family ranked by sha256('rl4cv-e08-audit-v1:' + task_id + '|' + sample_idx), identical across systems."""
    out = []
    for split in CORE_SPLITS:
        pool = [(t, k) for t in test_ids if t.split("__", 1)[0] == split for k in range(8)]
        pool.sort(key=lambda x: sha(f"rl4cv-e08-audit-v1:{x[0]}|{x[1]}".encode()))
        out.extend(pool[:per_core_split])
    return out


def build_test(systems_path: Path, cells_dir: Path, smoke_items: int = 1) -> dict:
    systems = [s for s in json.loads(systems_path.read_text())["systems"] if s.get("generation") == "new"]
    test_ids = read_ids(EXP.parent / "expt_v1" / "results" / "split" / "vbv1_test_task_ids.txt")
    audit = set(audit_cells(test_ids))
    root = PRIVATE / "test" / "inputs"
    rendered_dir = PRIVATE / "test" / "rendered"
    items, rows, per_system, skipped = [], [], {}, {}
    for s in systems:
        label = s["label"]
        jobs = (E05_OUT / "jobs") if s.get("source") == "e05" else (WORK / "ladder" / "test" / "jobs")
        name = f"{s['e05_label']}_g8" if s.get("source") == "e05" else f"{label}_g8"
        with (cells_dir / f"{label}_test_cells.csv").open(encoding="utf-8", newline="") as fh:
            cells = {(r["task_id"], int(r["sample_idx"])): r for r in csv.DictReader(fh)}
        main = {k for k, r in cells.items() if r["known"] == "True" and r["IC_tests"] in ("1.0", "1")}
        chosen = sorted(main | audit)
        per_system[label] = {"n_main": len(main), "n_audit": len(audit), "n_audit_only": len(audit - main), "n_cells": len(chosen)}
        for task_id, k in chosen:
            sol = jobs / f"{name}_s{k}" / task_id / "verifier" / "solution.lean"
            gold_src = PACK / task_id / "tests" / "gold.lean"
            if not sol.exists() or not gold_src.exists():
                skipped[f"{label}/{task_id}/{k}"] = "missing_solution_or_gold_on_disk"
                continue
            lean = sol.read_text(encoding="utf-8", errors="replace")
            item = f"{label}__{task_id}__s{k}"
            d = root / label / task_id / f"s{k}"
            d.mkdir(parents=True, exist_ok=True)
            (d / "solution.lean").write_text(lean, encoding="utf-8")
            (d / "source.py").write_text(python_of(task_id), encoding="utf-8")
            gold_text = gold_src.read_text(encoding="utf-8", errors="replace")
            (d / "gold.lean").write_text(gold_text, encoding="utf-8")
            row = {"item": item, "task": task_id, "split": task_id.split("__", 1)[0], "system": label, "sample_idx": k, "candidate_file": "solution.lean", "gold_file_name": "gold.lean",
                   "candidate_path": relative(d / "solution.lean"), "ref_ann_path": relative(d / "gold.lean"), "py_ann_path": relative(d / "source.py"),
                   "ref_placeholder_at_annotation": False, "n_ref_theorems_ann": len(build_inputs.statements(gold_text)), "is_audit_only": (task_id, k) not in main,
                   "ic_tests": cells[(task_id, k)]["IC_tests"], "lean_sha256": sha(lean.encode("utf-8"))}
            items.append(row)
            system, user = prompts.render(RUBRIC, row, lean, "solution.lean")
            digest = sha((system + "\n\n" + user).encode())
            for r in REPEATS:
                cell = f"{item}__r{r}"
                write_json(rendered_dir / f"{cell}.json", {"system": system, "user": user})
                rows.append({"cell": cell, "item": item, "task": task_id, "repeat": r, "kind": "main", "system": label, "sample_idx": k, "candidate_sha256": sha(lean.encode()),
                             "prompt_sha256": digest, "is_audit_only": row["is_audit_only"]})
    (PRIVATE / "test" / "items.jsonl").write_text("".join(json.dumps(r) + "\n" for r in items))
    receipt_path = PRIVATE / "test" / "cells_receipt.json"
    write_json(receipt_path, {"cells": rows})
    pack_path = PRIVATE / "packs" / "judge_rl4cv_e08v2_test"
    judge_pack.RENDERED = rendered_dir
    manifest = judge_pack.build(pack_path, receipt_path, "judge", smoke_items=smoke_items)
    manifest["round_trip"] = judge_pack.verify(pack_path, manifest)
    by_cell = {r["cell"]: r for r in rows}
    for c in manifest["cells"]:
        c.update(system=by_cell[c["cell"]]["system"], sample_idx=by_cell[c["cell"]]["sample_idx"], is_audit_only=by_cell[c["cell"]]["is_audit_only"], task_id_vb=by_cell[c["cell"]]["task"])
    manifest.update(written_utc=stamp(), verdict="PASS" if not manifest["round_trip"]["failures"] else "FAIL", per_system=per_system, cells_not_judged=skipped, repeats=list(REPEATS),
                    pack_abs=str(pack_path), rubric=RUBRIC, rubric_fingerprint=prompts.rubric_fingerprint(RUBRIC), configs=list(CONFIGS), systems_manifest_sha256=sha(systems_path.read_bytes()),
                    n_declared_ratings=len(rows) * len(CONFIGS))
    write_json(suite_spec("rl4cv-e08v2:all")["pack_receipt"], manifest)
    for label in per_system:
        ids = [c["task_id"] for c in manifest["cells"] if c["system"] == label]
        (RESULTS / f"task_ids_{label}.txt").write_text("".join(t + "\n" for t in ids))
    return manifest


# --------------------------------------------------------------------------------------------------
# Admit / poll / harvest (one Valkyrie run per (suite, config); every rating is one declared call)
# --------------------------------------------------------------------------------------------------
def env() -> dict[str, str]:
    # The hosted CLI reads only its login (or VALKYRIE_API_KEY / VALKYRIE_URL); cron may supply only system paths,
    # so the experiment interpreter's installed CLI comes first.
    return hosted.cli_env(PROVIDER_ENV)


def cli(args: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    return subprocess.run(["valk"] + args, env=env(), stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)


def load_state() -> dict:
    return read_json(STATE, {"runs": {}, "created": stamp()})


def save_state(state: dict) -> None:
    state["updated"] = stamp()
    write_json(STATE, state)


def judge_config(name: str) -> dict:
    return json.loads((X100 / f"configs/{name}.json").read_text())


def preflight() -> int:
    """Hosted-route evidence before any admission (D-108): organization, credential kind, sandbox provider, the gateway
    secret's name and the judge bundle, which must be byte-identical to version 1's except, in contract.yaml, the gateway
    secret renamed to the slash-free name (every `run start` also remaps it, see `hosted.secret_args`). Zero model calls."""
    out = hosted.preflight(require_secrets=[hosted.GATEWAY_SECRET], require_agents=[AGENT], env=env())
    out.update(route="Vals Valkyrie (hosted): valk run start --agent " + AGENT, model_calls_so_far=0,
               payer=f"Vals model gateway credential mapped only inside Valkyrie by organization secret {hosted.GATEWAY_SECRET} (D-108)",
               credential_source=f"Valkyrie organization secret {hosted.GATEWAY_SECRET}; no provider key on host", frozen_reference=relative(ROUTE_V1))
    out["identity"] = {k: v for k, v in out.get("identity", {}).items() if k != "account"}
    problems = out["problems"]
    if not problems:
        frozen = read_json(ROUTE_V1, {}).get("bundle_hashes", {})
        dest = WORK / "private" / "bundle_check" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest.mkdir(parents=True, exist_ok=True)
        got = cli(["agent", "download", AGENT, "--output-dir", str(dest)], timeout=600)
        files = {p.name: p for p in dest.rglob("*") if p.is_file()}
        match = {n: hosted.matches_frozen(files[n].read_bytes(), frozen.get(n), allow_secret_rename=n == "contract.yaml")
                 for n in BUNDLE_SAME_AS_V1 if n in files}
        out["bundle_hashes"] = {n: sha(files[n].read_bytes()) for n in match}
        out["bundle_match_vs_version1"] = match
        if got.returncode or not match:
            problems.append(f"valkyrie agent download {AGENT} failed (rc={got.returncode})")
        else:
            problems += [f"{n} differs from version 1's frozen bundle" for n in BUNDLE_SAME_AS_V1 if not match.get(n)]
            out["bundle_matches_version1"] = not problems
        out["run_secret_override"] = hosted.secret_args()
    out["verdict"] = "FAIL" if problems else "PASS"
    write_json(ROUTE, out)
    print(json.dumps({"verdict": out["verdict"], "organization": out.get("identity", {}).get("organization"),
                      "default_provider": out.get("default_provider"), "problems": problems}))
    return 0 if out["verdict"] == "PASS" else 1


def request_benchmark(spec: dict, name: str) -> str:
    return f"rl4cv-e08v2-judge-{spec['benchmark']}-{(spec['system'] or 'controls')}-{name}"[:120]


def admit(suite: str, configs: list[str], concurrency: int) -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    with (RESULTS / "admission.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _admit_locked(suite, configs, concurrency)


def _admit_locked(suite: str, configs: list[str], concurrency: int) -> int:
    spec = suite_spec(suite)
    pack = read_json(spec["pack_receipt"])
    assert pack and pack.get("verdict") == "PASS", f"{suite}: pack verdict is not PASS"
    published = subprocess.run(["git", "show", f"origin/main:{spec['pack_receipt'].relative_to(REPO)}"], cwd=REPO, capture_output=True)
    assert published.returncode == 0 and published.stdout == spec['pack_receipt'].read_bytes(), 'Judge pack is not the exact published manifest'
    route = read_json(ROUTE)
    assert route and route.get('verdict') == 'PASS', 'Hosted Vals route not verified: run `judge_rl4cv_e08v2.py preflight`'
    if spec['system']:
        assert read_json(RESULTS / 'controls_check.json', {}).get('verdict') == 'PASS', 'Route controls have not passed'
    if spec["system"]:
        ids_file = RESULTS / f"task_ids_{spec['system']}.txt"
    else:
        ids_file = RESULTS / "task_ids_controls.txt"
        ids_file.write_text("".join(c["task_id"] + "\n" for c in pack["control_cells"]))
    n_tasks = len(read_ids(ids_file))
    task_slice = None
    task_filter = ['--task-ids-file', str(ids_file)]
    if spec['system']:
        wanted_ids = sorted(read_ids(ids_file))
        all_ids = sorted(p.name for p in Path(pack['pack_abs']).iterdir() if p.is_dir())
        start = all_ids.index(wanted_ids[0])
        end = start + len(wanted_ids)
        assert all_ids[start:end] == wanted_ids, 'Manifest IDs are not one exact ordered slice'
        task_slice = f'{start}:{end}'
        url, auth = hosted.lookup_local(SERVICES, spec['benchmark'])
        request = urllib.request.Request(url + '/verify-task-ids?' + urllib.parse.urlencode({'slice': task_slice, 'dataset': 'default'}), headers={'Authorization': auth})
        with urllib.request.urlopen(request, timeout=60) as response:
            assert json.load(response)['task_ids'] == wanted_ids, 'Live service slice differs from the manifest'
        task_filter = ['--slice', task_slice]
    state = load_state()
    failed = False
    for name in configs:
        key = spec["key_prefix"] + name
        if key in state["runs"] and state["runs"][key].get("run_id"):
            print(f"{key}: already admitted as {state['runs'][key]['run_id']}; refusing to re-admit")
            continue
        if key in state["runs"]:
            # A missing run identifier does not prove the service admitted no requests.
            # Preserve the entry, including "admitting" after an abrupt client exit.
            print(f"{key}: prior admission has no verified run id; receipt recovery required, not re-admitting")
            failed = True
            continue
        cfg = judge_config(name)
        kwargs = {"judge_config": name, "max_tokens": str(cfg["max_tokens"]), "benchmark": request_benchmark(spec, name)}
        if cfg.get("reasoning_effort"):
            kwargs["reasoning_effort"] = cfg["reasoning_effort"]
        if cfg.get("compute_effort"):
            kwargs["compute_effort"] = cfg["compute_effort"]
        args = ["run", "start", "--agent", AGENT, "--benchmark", spec["benchmark"], "--dataset", "default", "--model", cfg["selector"], "--concurrency", str(concurrency),
                "--label", f"rl4cv-e08v2-judge-{(spec['system'] or 'controls')}-{name}"[:96], *task_filter, *hosted.secret_args()]
        for k, v in kwargs.items():
            args += ["-k", k, v]
        entry = {"config": name, "selector": cfg["selector"], "kwargs": kwargs, "concurrency": concurrency, "expected_cells": n_tasks, "suite": suite, "benchmark": spec["benchmark"],
                 "admitted_at": stamp(), "phase": "admitting", "command": args, "task_ids_sha256": sha(ids_file.read_bytes()), "verified_task_slice": task_slice}
        state["runs"][key] = entry
        save_state(state)
        try:
            result = cli(args)
        except OSError as exc:
            # Popen failed before a client existed. Record that evidence, but never
            # automatically replay an admission: recovery owns the bounded decision.
            entry.update(phase="admission_failed", retry_blocked=True,
                         subprocess_started=False, launch_error=type(exc).__name__,
                         launch_errno=exc.errno)
            failed = True
            save_state(state)
            print(f"{key}: client could not start ({type(exc).__name__}); recovery required")
            continue
        except subprocess.TimeoutExpired:
            entry.update(phase="admission_failed", retry_blocked=True,
                         subprocess_started=True, launch_error="TimeoutExpired")
            failed = True
            save_state(state)
            print(f"{key}: admission timed out; receipt recovery required")
            continue
        found = UUID_RE.findall(result.stdout + result.stderr)
        if result.returncode or not found:
            failed = True
            entry.update(phase="admission_failed", retry_blocked=True, returncode=result.returncode, stderr_tail=(result.stderr or result.stdout or "")[-800:])
            print(f"{key}: ADMISSION FAILED rc={result.returncode}\n{(result.stderr or result.stdout or '')[-600:]}")
        else:
            entry.update(phase="running", run_id=found[0])
            print(f"{key}: run_id={found[0]} over {n_tasks} cells at concurrency {concurrency}")
        save_state(state)
    return 1 if failed else 0


def poll() -> int:
    state = load_state()
    summary = {}
    for name, entry in state["runs"].items():
        run_id = entry.get("run_id")
        if not run_id:
            summary[name] = {"phase": entry.get("phase")}
            continue
        result = cli(["run", "status", "--ids", run_id, "--format", "json"], timeout=600)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            summary[name] = {"phase": entry.get("phase"), "poll_error": True}
            continue
        runs = payload.get("runs") if isinstance(payload, dict) else payload
        row = runs[0] if isinstance(runs, list) and runs else (runs if isinstance(runs, dict) else {})
        counts = row.get("task_state_counts") or row.get("task_states") or {}
        status = str(row.get("status") or row.get("state") or "").lower()
        terminal = sum(int(counts.get(k, 0)) for k in ("FINISHED", "ERROR", "STOPPED"))
        entry.update(run_status=status, task_state_counts=counts, cells_terminal=terminal, polled_at=stamp())
        if status in {"finished", "completed", "error", "failed", "stopped", "cancelled", "canceled", "success", "succeeded"}:
            entry["phase"] = "terminal"
        summary[name] = {"phase": entry["phase"], "run_status": status, "cells_terminal": terminal, "expected": entry["expected_cells"]}
    save_state(state)
    print(json.dumps(summary, indent=1))
    return 0 if summary and all(v.get("phase") == "terminal" for v in summary.values()) else 1


def rows_of(results_path: Path) -> dict[str, dict]:
    payload = json.loads(results_path.read_text())
    blob = payload[0] if isinstance(payload, list) and payload else payload
    raw = blob.get("evaluation_results") or blob.get("results") or blob.get("task_results") or {}
    out = {}
    for task_id, value in raw.items():
        row = value.get("result", value) if isinstance(value, dict) else value
        out[task_id] = row if isinstance(row, dict) else {}
    return out


def harvest(suite: str, configs: list[str]) -> int:
    spec = suite_spec(suite)
    pack = read_json(spec["pack_receipt"])
    field = spec["part_field"]
    pack_cells = {c["task_id"]: c for c in pack[field] if (spec["system"] is None or c.get("system") == spec["system"])}
    state = load_state()
    for name in configs:
        key = spec["key_prefix"] + name
        entry = state["runs"].get(key)
        if not entry or not entry.get("run_id"):
            print(f"{key}: not admitted, nothing to harvest")
            continue
        raw = WORK / "judge" / "raw" / key.replace("/", "__")
        raw.mkdir(parents=True, exist_ok=True)
        results_path, artifacts = raw / "results.json", raw / "artifacts"
        if results_path.exists():
            results_path.unlink()
        for args in (["run", "results", entry["run_id"], "--path", str(results_path)], ["run", "output", entry["run_id"], "-o", str(artifacts)]):
            cli(args, timeout=3600)
        rows = rows_of(results_path) if results_path.exists() else {}
        if not rows:
            cands = sorted(artifacts.glob(f"{spec['benchmark']}*.json"))
            rows = rows_of(cands[0]) if cands else {}
        receipts = {}
        duplicate_receipts = []
        for path in sorted(artifacts.rglob("receipt.json")):
            try:
                receipt = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            receipt_id = receipt.get("task_id") or path.parent.name
            if receipt_id in receipts:
                duplicate_receipts.append(receipt_id)
            receipts[receipt_id] = receipt
        cells, charges = [], 0.0
        for task_id, meta in sorted(pack_cells.items()):
            row, receipt = rows.get(task_id, {}), receipts.get(task_id, {})
            cell = {"task_id": task_id, "cell": meta["cell"], "item": meta["item"], "repeat": meta["repeat"], "kind": meta.get("kind", "main"), "system": meta.get("system"),
                    "task_id_vb": meta.get("task_id_vb", meta.get("task")), "sample_idx": meta.get("sample_idx"), "is_audit_only": meta.get("is_audit_only"), "config": name,
                    "agent_status": receipt.get("status"), "requests_sent": receipt.get("requests_sent"), "cost_usd": receipt.get("cost_usd"), "prompt_sha256_served": receipt.get("prompt_sha256"),
                    "prompt_hash_matches": (receipt.get("prompt_sha256") == meta["prompt_sha256"]) if receipt.get("prompt_sha256") else None, "error_type": receipt.get("error_type")}
            cell["transport_receipt"] = {k: receipt[k] for k in (
                "selector", "judge_config", "benchmark", "config", "wire_provider_config",
                "fallback", "system_sha256", "user_sha256", "prompt_sha256", "expected",
                "requests_sent", "status") if k in receipt}
            cell["transport_matches"] = transport_matches(receipt, meta, judge_config(name), name, request_benchmark(spec, name))
            charges += cell["cost_usd"] or 0.0
            blob_b64 = row.get("solution_b64")
            if blob_b64:
                text = base64.b64decode(blob_b64).decode("utf-8", errors="replace")
                try:
                    raw_score, norm, verdict = prompts.parse(judge_config(name)["rubric"], text)
                    cell.update(status="measured" if cell["transport_matches"] else "unmeasured_transport", score_raw=raw_score, score=norm, base_score=verdict.get("base_score"))
                except ValueError as exc:
                    cell.update(status="parse_error", error=str(exc)[:200])
            else:
                cell.update(status="unmeasured_infra", reason=receipt.get("reason") or receipt.get("error_type") or "no verdict")
            cells.append(cell)
        counts: dict[str, int] = {}
        for cell in cells:
            counts[cell["status"]] = counts.get(cell["status"], 0) + 1
        out = {"written_utc": stamp(), "suite": suite, "config": name, "run_id": entry["run_id"], "n_cells": len(cells), "status_counts": counts, "charges_usd": round(charges, 4), "cells": cells,
               "receipt_inventory": {"missing": sorted(set(pack_cells) - set(receipts)),
                                     "extra": sorted(set(receipts) - set(pack_cells)),
                                     "duplicates": sorted(set(duplicate_receipts))}}
        write_json(RESULTS / "harvests" / f"cells_{key.replace('/', '__')}.json", out)
        entry.update(harvested_at=stamp(), status_counts=counts, charges_usd=round(charges, 4))
        save_state(state)
        print(json.dumps({key: counts, "charges_usd": round(charges, 4)}))
    return 0



def transport_matches(receipt: dict, meta: dict, cfg: dict, name: str, benchmark: str) -> bool:
    """Verify the frozen request envelope and returned no-fallback receipt, not an invented response identity."""
    wanted = {"max_tokens": cfg["max_tokens"]}
    for key in ("compute_effort", "reasoning_effort"):
        if cfg.get(key):
            wanted[key] = cfg[key]
    expected = receipt.get("expected") or {}
    hashes = all(receipt.get(f"{k}_sha256") and receipt[f"{k}_sha256"] == expected.get(k)
                 for k in ("system", "user", "prompt"))
    requests = receipt.get("requests_sent")
    return bool(
        receipt.get("selector") == cfg["selector"] and receipt.get("judge_config") == name
        and receipt.get("benchmark") == benchmark and receipt.get("config") == wanted
        and receipt.get("status") == "measured" and "fallback" in receipt and receipt["fallback"] is None
        and hashes and receipt["prompt_sha256"] == meta["prompt_sha256"]
        and isinstance(requests, int) and not isinstance(requests, bool) and 1 <= requests <= 2
        and (not cfg.get("compute_effort") or (receipt.get("wire_provider_config") or {}).get("fallback_models") == []))



def controls_check() -> int:
    pack = read_json(RESULTS / "judge_pack_controls.json", {})
    declared = pack.get("control_cells", [])
    wanted = {c["task_id"]: c for c in declared}
    pack_ok = (bool(wanted) and len(wanted) == len(declared)
               and pack.get("verdict") == "PASS" and pack.get("rubric") == RUBRIC
               and pack.get("rubric_fingerprint") == prompts.rubric_fingerprint(RUBRIC))
    out = {"written_utc": stamp(), "configs": {}, "verdict": "PASS" if pack_ok else "FAIL",
           "pack_matches_frozen_rubric": pack_ok,
           "identity_evidence": "Frozen request envelope and returned no-fallback receipt; provider-returned model/effort fields are unavailable in the validated bundle."}
    for name in CONFIGS:
        h = read_json(RESULTS / "harvests" / f"cells_controls__{name}.json")
        if not h:
            out["configs"][name] = {"missing": True}
            out["verdict"] = "FAIL"
            continue
        cells_by_id = {c["task_id"]: c for c in h["cells"]}
        inventory = h.get("receipt_inventory")
        exact = (len(cells_by_id) == len(h["cells"]) == len(wanted) and set(cells_by_id) == set(wanted)
                 and inventory == {"missing": [], "extra": [], "duplicates": []})
        transport_ok = exact and all(
            c["status"] == "measured"
            and transport_matches(c.get("transport_receipt", {}), wanted[c["task_id"]],
                                  judge_config(name), name, request_benchmark(suite_spec("rl4cv-e08v2-controls"), name))
            for c in h["cells"])
        if not transport_ok:
            out["verdict"] = "FAIL"
        per_kind = {}
        for kind, (rule, min_frac) in CONTROL_EXPECTATIONS.items():
            declared_kind = [c for c in declared if c["kind"] == kind]
            cells = [cells_by_id[c["task_id"]] for c in declared_kind if c["task_id"] in cells_by_id]
            measured = [c for c in cells if c["status"] == "measured"]
            ok = [c for c in measured if _control_ok(kind, c["score_raw"])]
            frac = len(ok) / len(declared_kind) if declared_kind else None
            per_kind[kind] = {"rule": rule, "min_fraction": min_frac, "n": len(declared_kind), "measured": len(measured), "ok": len(ok), "fraction": round(frac, 3) if frac is not None else None,
                              "pass": bool(declared_kind) and len(measured) == len(declared_kind) and frac >= min_frac, "scores": [c["score_raw"] for c in measured]}
            if not per_kind[kind]["pass"]:
                out["verdict"] = "FAIL"
        out["configs"][name] = {"run_id": h["run_id"], "charges_usd": h["charges_usd"], "status_counts": h["status_counts"], "per_kind": per_kind,
                                "exact_receipt_inventory": exact, "transport_matches": transport_ok,
                                "expected_envelope": {"selector": judge_config(name)["selector"], "effort": judge_config(name).get("compute_effort") or judge_config(name).get("reasoning_effort"),
                                              "max_tokens": judge_config(name)["max_tokens"], "rubric": judge_config(name)["rubric"]}}
    write_json(RESULTS / "controls_check.json", out)
    print(json.dumps({"verdict": out["verdict"], **{n: {k: v["fraction"] for k, v in c.get("per_kind", {}).items()} for n, c in out["configs"].items()}}))
    return 0 if out["verdict"] == "PASS" else 1


def fsc(system: str) -> int:
    """FSC per (system, task_id, sample_idx): each member's median over its measured repeats, mean of the two member medians / 5 (D-102, experiment 100 H2)."""
    members: dict[str, dict[tuple, list[int]]] = {c: {} for c in CONFIGS}
    meta: dict[tuple, dict] = {}
    charges, n_ratings_declared, n_measured = 0.0, 0, 0
    for name in CONFIGS:
        h = read_json(RESULTS / "harvests" / f"cells_{system}__{name}.json")
        if not h:
            print(f"{system}/{name}: no harvest")
            return 1
        charges += h["charges_usd"]
        for c in h["cells"]:
            key = (c["task_id_vb"], int(c["sample_idx"]))
            meta.setdefault(key, {"is_audit_only": c["is_audit_only"], "item": c["item"]})
            n_ratings_declared += 1
            if c["status"] == "measured":
                n_measured += 1
                members[name].setdefault(key, []).append(int(c["score_raw"]))
    per_cell = {}
    for key, m in sorted(meta.items()):
        reps = {c: members[c].get(key, []) for c in CONFIGS}
        medians = {c: statistics.median(v) for c, v in reps.items() if v}
        complete = all(len(reps[c]) == len(REPEATS) for c in CONFIGS)
        value = statistics.fmean(medians.values()) / 5.0 if complete else None
        per_cell[f"{key[0]}#{key[1]}"] = {"task_id": key[0], "sample_idx": key[1], "FSC": value, "member_medians_0_5": medians, "repeats_measured": {c: len(v) for c, v in reps.items()},
                                           "complete_3x2": complete, "is_audit_only": m["is_audit_only"]}
    out = {"written_utc": stamp(), "system": system, "configs": list(CONFIGS), "repeats": list(REPEATS), "n_files": len(per_cell), "n_ratings_declared": n_ratings_declared,
           "n_ratings_measured": n_measured, "n_files_with_fsc": sum(1 for v in per_cell.values() if v["FSC"] is not None),
           "n_files_complete_3x2": sum(1 for v in per_cell.values() if v["complete_3x2"]), "charges_usd": round(charges, 4),
           "rule": "median of all 3 declared ratings per member, FSC = mean of the two member medians / 5; any missing rating leaves FSC unknown",
           "cells": per_cell}
    write_json(RESULTS / f"fsc_{system}.json", out)
    print(json.dumps({k: out[k] for k in ("system", "n_files", "n_ratings_declared", "n_ratings_measured", "n_files_with_fsc", "n_files_complete_3x2", "charges_usd")}))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build-controls")
    p = sub.add_parser("build-test")
    p.add_argument("--systems", type=Path, required=True, help="JSON with 'systems' (label, source, e05_label); normally results/selection.json's test_manifest")
    p.add_argument("--cells-dir", type=Path, default=EXP / "results" / "ladder", help="dir with <label>_test_cells.csv from analyze_ladder.py --split test")
    sub.add_parser("preflight")
    p = sub.add_parser("admit")
    p.add_argument("--suite", required=True)
    p.add_argument("--configs", nargs="+", default=list(CONFIGS))
    p.add_argument("--concurrency", type=int, default=8)
    sub.add_parser("poll")
    p = sub.add_parser("harvest")
    p.add_argument("--suite", required=True)
    p.add_argument("--configs", nargs="+", default=list(CONFIGS))
    sub.add_parser("controls-check")
    p = sub.add_parser("fsc")
    p.add_argument("--system", required=True)
    a = ap.parse_args()
    if a.cmd == "build-controls":
        m = build_controls()
        print(json.dumps({"verdict": m["verdict"], "tasks": m["tasks"], "n_control_tasks": m["n_control_tasks"], "pack": m["pack_abs"]}))
        return 0 if m["verdict"] == "PASS" else 1
    if a.cmd == "build-test":
        m = build_test(a.systems, a.cells_dir)
        print(json.dumps({"verdict": m["verdict"], "per_system": m["per_system"], "n_tasks": m["n_tasks"], "n_declared_ratings": m["n_declared_ratings"], "skipped": len(m["cells_not_judged"])}))
        return 0 if m["verdict"] == "PASS" else 1
    if a.cmd == "preflight":
        return preflight()
    if a.cmd == "admit":
        return admit(a.suite, a.configs, a.concurrency)
    if a.cmd == "poll":
        return poll()
    if a.cmd == "harvest":
        return harvest(a.suite, a.configs)
    if a.cmd == "controls-check":
        return controls_check()
    if a.cmd == "fsc":
        return fsc(a.system)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
