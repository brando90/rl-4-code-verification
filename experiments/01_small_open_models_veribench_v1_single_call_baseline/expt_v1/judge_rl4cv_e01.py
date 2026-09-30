#!/usr/bin/env python3
# TLDR: FSC judging for experiment 01, adapted from experiment 103's judge_vbv1.py/judge_controller.py/
# judge_pack.py (imported, not edited) so nothing here ever writes into veribench_vb103's private/ tree:
# every path below resolves relative to OUR OWN pinned external/veribench checkout, which is a physically
# separate clone. Suites: "rl4cv-e01-controls" (oracle/blank/shuffled/vacuous/halfdel, no model dependency)
# and "rl4cv-e01:<label>" (one model's measured cells with IC_tests*IC_proofs>0 plus a 60-file audit).
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
EXT = REPO / "external" / "veribench"
E103 = EXT / "experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge"
X100 = EXT / "experiments/100_karpathy_recipe_tc_judge_search_human_train_val_test"
PRIVATE = E103 / "private" / "judge" / "rl4cv_e01"           # OUR OWN isolated tree, not vb103's
RESULTS = Path(__file__).resolve().parent / "results" / "judge"
VALK = Path("/lfs/skampere1/0/brando9/.local/share/valkyrie-host-bootstrap/tools/valkyrie/bin/valk")
AGENT = "vb103_judge"
CONFIGS = ("H2_sol_high", "H2_opus55_max")
RUBRIC = "H2_human_mirror_conventions_demos"
STATE = RESULTS / "state.json"
SPEND_CAP_USD = 400.0

sys.path[:0] = [str(X100 / "scripts"), str(E103 / "scripts")]
import common                          # noqa: E402  frozen, imported not edited
common.EXPT = X100
import prompts                         # noqa: E402
import build_inputs                    # noqa: E402
import judge_run                       # noqa: E402
import judge_pack                      # noqa: E402

CONTROL_KINDS = ["oracle", "vacuous", "shuffled", "halfdel", "blank"]
CONTROL_EXPECTATIONS = {
    "control_oracle": {"rule": "score_raw >= 4", "min_fraction": 0.90},
    "control_vacuous": {"rule": "score_raw <= 1", "min_fraction": 0.90},
    "control_blank": {"rule": "score_raw == 0", "min_fraction": 0.90},
    "control_shuffled": {"rule": "score_raw <= 1", "min_fraction": 0.90},
    "control_halfdel": {"rule": "1 <= score_raw <= 4", "min_fraction": 0.80},
}


def _control_ok(kind: str, score: int) -> bool:
    if kind == "control_oracle":
        return score >= 4
    if kind in ("control_vacuous", "control_shuffled"):
        return score <= 1
    if kind == "control_blank":
        return score == 0
    if kind == "control_halfdel":
        return 1 <= score <= 4
    raise KeyError(kind)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1) + "\n")
    tmp.replace(path)


def relative(path: Path) -> str:
    """A path experiment 100's common.read_text resolves: relative to X100's own dir, hopping into 103."""
    return "../" + str(path.relative_to(EXT / "experiments").as_posix())


# --------------------------------------------------------------------------------------------------
# Suites
# --------------------------------------------------------------------------------------------------

def suite_spec(suite: str) -> dict:
    if suite == "rl4cv-e01-controls":
        return {"suite": suite, "model": None, "benchmark": "veribench-rl4cv-e01-controls",
                "pack_receipt": RESULTS / "judge_pack_controls.json", "key_prefix": "controls/",
                "condition": "rl4cv-e01-judge-controls"}
    assert suite.startswith("rl4cv-e01:"), f"unknown suite: {suite}"
    label = suite.split(":", 1)[1]
    return {"suite": suite, "model": label, "benchmark": f"veribench-rl4cv-e01-{label}".replace(".", "-"),
            "pack_receipt": RESULTS / f"judge_pack_{label}.json", "key_prefix": f"{label}/",
            "condition": f"rl4cv-e01-judge-{label}"}


PARTS = {"gate": ("cells", ""), "controls": ("control_cells", "@controls")}


# --------------------------------------------------------------------------------------------------
# Build: controls (no model dependency; safe to run before any GPU generation finishes)
# --------------------------------------------------------------------------------------------------

def _pick_control_tasks(pack_dir: Path, n: int) -> list[str]:
    splits: dict[str, str] = {}
    for task in sorted(os.listdir(pack_dir)):
        split = task.split("__", 1)[0]
        if split in splits:
            continue
        gold = pack_dir / task / "tests" / "gold.lean"
        if not gold.exists():
            continue
        if len(build_inputs.statements(gold.read_text(encoding="utf-8", errors="replace"))) >= 2:
            splits[split] = task
        if len(splits) >= n:
            break
    return list(splits.values())


def build_controls(pack_dir: Path, n_tasks: int = 12) -> dict:
    root = PRIVATE / "controls" / "inputs"
    tasks = _pick_control_tasks(pack_dir, n_tasks)
    items = []
    for task in tasks:
        gold_text = (pack_dir / task / "tests" / "gold.lean").read_text(encoding="utf-8", errors="replace")
        instruction = (pack_dir / task / "instruction.md").read_text(encoding="utf-8", errors="replace")
        import re
        blocks = re.findall(r"```python\n(.*?)```", instruction, re.S)
        python = max(blocks, key=len) if blocks else ""
        directory = root / task
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "gold.lean").write_text(gold_text, encoding="utf-8")
        (directory / "source.py").write_text(python, encoding="utf-8")
        items.append({"item": task, "task": task, "split": task.split("__", 1)[0],
                      "candidate_file": "gold.lean", "gold_file_name": "gold.lean",
                      "candidate_path": relative(directory / "gold.lean"),
                      "ref_ann_path": relative(directory / "gold.lean"),
                      "py_ann_path": relative(directory / "source.py"),
                      "ref_placeholder_at_annotation": False,
                      "n_ref_theorems_ann": len(build_inputs.statements(gold_text))})
    items_path = PRIVATE / "controls" / "items.jsonl"
    items_path.write_text("".join(json.dumps(r) + "\n" for r in items))
    by_task = {r["task"]: r for r in items}

    cells = judge_run.build_cells(None, 1, CONTROL_KINDS, items_path=items_path)
    cells = [c for c in cells if c["kind"] != "main"]
    rendered_dir = PRIVATE / "controls" / "rendered"
    cell_rows = []
    for cell in cells:
        text, _extra = judge_run.candidate_text(cell)
        row = by_task[cell["task"]]
        system, user = prompts.render(RUBRIC, row, text, cell["cand_name"])
        digest = sha((system + "\n\n" + user).encode())
        write_json(rendered_dir / f"{cell['cell']}.json", {"system": system, "user": user})
        cell_rows.append({"cell": cell["cell"], "item": cell["item"], "task": cell["task"],
                          "repeat": cell["repeat"], "kind": cell["kind"],
                          "candidate_sha256": sha(text.encode()), "prompt_sha256": digest})
    receipt_path = PRIVATE / "controls" / "cells_receipt.json"
    write_json(receipt_path, {"cells": cell_rows})

    pack_path = PRIVATE / "packs" / "judge_rl4cv_e01_controls"
    judge_pack.RENDERED = rendered_dir
    manifest = judge_pack.build(pack_path, receipt_path, "judge", smoke_items=0)
    manifest["round_trip"] = judge_pack.verify(pack_path, manifest)
    manifest["written_utc"] = stamp()
    manifest["verdict"] = "PASS" if not manifest["round_trip"]["failures"] else "FAIL"
    manifest["n_tasks_selected"] = len(tasks)
    out = suite_spec("rl4cv-e01-controls")["pack_receipt"]
    write_json(out, manifest)
    return manifest


# --------------------------------------------------------------------------------------------------
# Build: one model's main cells (IC_tests*IC_proofs>0) + a 60-file stratified audit
# --------------------------------------------------------------------------------------------------

def build_model_pack(label: str, scored_jsonl: Path, audit_n: int = 60, smoke_items: int = 1) -> dict:
    import random
    rows = [json.loads(l) for l in scored_jsonl.read_text().splitlines() if l.strip()]
    measured = [r for r in rows if r.get("measured")]
    positives = [r for r in measured if (r.get("factors", {}).get("IC_tests") or 0) *
                (r.get("factors", {}).get("IC_proofs") or 0) > 0]
    by_split: dict[str, list[dict]] = {}
    for r in measured:
        by_split.setdefault(r["task_id"].split("__", 1)[0], []).append(r)
    rng = random.Random(f"rl4cv-e01-audit:{label}")
    audit, splits = [], sorted(by_split)
    per_split = max(1, audit_n // max(1, len(splits)))
    for split in splits:
        pool = by_split[split][:]
        rng.shuffle(pool)
        audit.extend(pool[:per_split])
    audit = audit[:audit_n]
    chosen = {r["task_id"]: r for r in positives}
    for r in audit:
        chosen.setdefault(r["task_id"], r)

    root = PRIVATE / label / "inputs"
    items, skipped = [], {}
    for task_id, r in sorted(chosen.items()):
        lean = r.get("lean") or ""
        instruction = r.get("instruction") or ""
        import re
        blocks = re.findall(r"```python\n(.*?)```", instruction, re.S) if instruction else []
        python = max(blocks, key=len) if blocks else ""
        directory = root / task_id
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "solution.lean").write_text(lean, encoding="utf-8")
        (directory / "source.py").write_text(python, encoding="utf-8")
        gold_path = directory / "gold.lean"
        if r.get("gold"):
            gold_path.write_text(r["gold"], encoding="utf-8")
        if not gold_path.exists():
            skipped[task_id] = "no_gold_available"
            continue
        n_ref = len(build_inputs.statements(gold_path.read_text(encoding="utf-8", errors="replace")))
        items.append({"item": task_id, "task": task_id, "split": task_id.split("__", 1)[0],
                      "candidate_file": "solution.lean", "gold_file_name": "gold.lean",
                      "candidate_path": relative(directory / "solution.lean"),
                      "ref_ann_path": relative(gold_path), "py_ann_path": relative(directory / "source.py"),
                      "ref_placeholder_at_annotation": False, "n_ref_theorems_ann": n_ref,
                      "is_audit_only": task_id not in {r2["task_id"] for r2 in positives}})
    items_path = PRIVATE / label / "items.jsonl"
    items_path.write_text("".join(json.dumps(r) + "\n" for r in items))

    rendered_dir = PRIVATE / label / "rendered"
    cell_rows = []
    for row in items:
        candidate = (root / row["item"] / "solution.lean").read_text(encoding="utf-8", errors="replace")
        system, user = prompts.render(RUBRIC, row, candidate, row["candidate_file"])
        digest = sha((system + "\n\n" + user).encode())
        cell = {"cell": f"{row['item']}__r1", "item": row["item"], "task": row["task"], "repeat": 1,
                "kind": "main"}
        write_json(rendered_dir / f"{cell['cell']}.json", {"system": system, "user": user})
        cell_rows.append({**cell, "candidate_sha256": sha(candidate.encode()), "prompt_sha256": digest})
    receipt_path = PRIVATE / label / "cells_receipt.json"
    write_json(receipt_path, {"cells": cell_rows})

    pack_path = PRIVATE / "packs" / f"judge_rl4cv_e01_{label}"
    judge_pack.RENDERED = rendered_dir
    manifest = judge_pack.build(pack_path, receipt_path, "judge", smoke_items=smoke_items)
    manifest["round_trip"] = judge_pack.verify(pack_path, manifest)
    manifest["written_utc"] = stamp()
    manifest["verdict"] = "PASS" if not manifest["round_trip"]["failures"] else "FAIL"
    manifest["n_positive_cells"] = len(positives)
    manifest["n_audit_cells"] = len(audit)
    manifest["cells_not_judged"] = skipped
    out = suite_spec(f"rl4cv-e01:{label}")["pack_receipt"]
    write_json(out, manifest)
    return manifest


# --------------------------------------------------------------------------------------------------
# Admit / poll / harvest / controls / fsc  (adapted from judge_controller.py, same CLI shape)
# --------------------------------------------------------------------------------------------------

def env() -> dict[str, str]:
    out = dict(os.environ)
    for key in ("VALKYRIE_API_KEY", "TRACKER_SERVICE_URL", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
                "GEMINI_API_KEY", "GOOGLE_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN",
                "ANTHROPIC_AUTH_TOKEN", "PYTHONPATH", "PYTHONHOME"):
        out.pop(key, None)
    out.update(VALKYRIE_ENV="bench", VALKYRIE_CONFIG_PATH=str(E103 / "private" / "valkyrie.yaml")
               if (E103 / "private" / "valkyrie.yaml").exists() else out.get("VALKYRIE_CONFIG_PATH", ""))
    return out


def cli(args: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    return subprocess.run([str(VALK)] + args, env=env(), stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=timeout)


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"runs": {}, "created": stamp()}


def save_state(state: dict) -> None:
    state["updated"] = stamp()
    disk = load_state()
    for key, entry in disk.get("runs", {}).items():
        state.setdefault("runs", {}).setdefault(key, entry)
    write_json(STATE, state)


def spent_so_far() -> float:
    total = 0.0
    for path in (RESULTS / "harvests").glob("cells_*.json") if (RESULTS / "harvests").exists() else []:
        try:
            total += json.loads(path.read_text()).get("charges_usd", 0.0)
        except (json.JSONDecodeError, OSError):
            pass
    return total


def part_ids(part: str, spec: dict) -> tuple[Path, int, str]:
    field, suffix = PARTS[part]
    pack = json.loads(spec["pack_receipt"].read_text())
    rows = pack.get(field) or []
    assert rows, f"{spec['suite']}: the pack receipt has no {field}"
    slug = spec["suite"].replace(":", "_").replace(".", "-")
    ids_file = RESULTS / f"task_ids_{slug}_{part}.txt"
    ids_file.write_text("".join(row["task_id"] + "\n" for row in rows))
    return ids_file, len(rows), suffix


def judge_config(name: str) -> dict:
    return json.loads((X100 / f"configs/{name}.json").read_text())


def admit(configs: list[str], concurrency: int, part: str, suite: str) -> int:
    spent = spent_so_far()
    if spent >= SPEND_CAP_USD:
        print(f"SPEND CAP HIT: ${spent:.2f} >= ${SPEND_CAP_USD}; refusing new admissions")
        return 3
    spec = suite_spec(suite)
    pack = json.loads(spec["pack_receipt"].read_text())
    assert not pack.get("round_trip", {}).get("failures"), f"{suite}: pack failed round-trip"
    ids_file, n_tasks, suffix = part_ids(part, spec)
    state = load_state()
    for name in configs:
        key = spec["key_prefix"] + name + suffix
        if key in state["runs"]:
            print(f"{key}: already admitted as {state['runs'][key].get('run_id')}; refusing to re-admit")
            continue
        cfg = judge_config(name)
        kwargs = {"judge_config": name, "max_tokens": str(cfg["max_tokens"]), "benchmark": spec["benchmark"]}
        if cfg.get("reasoning_effort"):
            kwargs["reasoning_effort"] = cfg["reasoning_effort"]
        if cfg.get("compute_effort"):
            kwargs["compute_effort"] = cfg["compute_effort"]
        args = ["run", "start", "--agent", AGENT, "--benchmark", spec["benchmark"], "--dataset", "default",
                "--model", cfg["selector"], "--concurrency", str(concurrency),
                "--label", f"rl4cv-e01-judge-{suite.replace(':', '-')}-{part}-{name}"[:96],
                "--task-ids-file", str(ids_file)]
        for kwarg, value in kwargs.items():
            args += ["-k", kwarg, value]
        entry = {"config": name, "selector": cfg["selector"], "kwargs": kwargs, "concurrency": concurrency,
                 "expected_cells": n_tasks, "part": part, "suite": suite, "benchmark": spec["benchmark"],
                 "admitted_at": stamp(), "phase": "admitting", "command": args}
        state["runs"][key] = entry
        save_state(state)
        result = cli(args)
        import re
        found = re.findall(r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}", result.stdout)
        if result.returncode or not found:
            entry.update(phase="admission_failed", returncode=result.returncode,
                         stderr_tail=(result.stderr or "")[-800:])
            print(f"{key}: ADMISSION FAILED rc={result.returncode}")
            print((result.stderr or result.stdout or "")[-600:])
        else:
            entry.update(phase="running", run_id=found[0])
            print(f"{key}: run_id={found[0]} over {n_tasks} cells at concurrency {concurrency}")
        save_state(state)
    return 0


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
        terminal_states = {"finished", "completed", "error", "failed", "stopped", "cancelled", "canceled",
                           "success", "succeeded"}
        if status in terminal_states and terminal >= entry["expected_cells"]:
            entry["phase"] = "terminal"
        summary[name] = {"phase": entry["phase"], "run_status": status, "cells_terminal": terminal,
                         "expected": entry["expected_cells"]}
    save_state(state)
    print(json.dumps(summary, indent=1))
    return 0


def download(name: str, run_id: str) -> tuple[Path, Path]:
    raw = RESULTS / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    name = name.replace("/", "__")
    results_path, artifacts = raw / f"{name}_results.json", raw / f"{name}_artifacts"
    if results_path.exists():
        results_path.unlink()
    for args in (["run", "results", run_id, "--path", str(results_path)],
                 ["run", "output", run_id, "-o", str(artifacts)]):
        cli(args, timeout=3600)
    return results_path, artifacts


def rows_of(results_path: Path) -> dict[str, dict]:
    payload = json.loads(results_path.read_text())
    blob = payload[0] if isinstance(payload, list) and payload else payload
    raw = (blob.get("evaluation_results") or blob.get("results") or blob.get("task_results") or {})
    out = {}
    for task_id, value in raw.items():
        row = value.get("result", value) if isinstance(value, dict) else value
        out[task_id] = row if isinstance(row, dict) else {}
    return out


def harvest(configs: list[str], part: str, suite: str) -> int:
    spec = suite_spec(suite)
    blob = json.loads(spec["pack_receipt"].read_text())
    field, suffix = PARTS[part]
    pack = {c["task_id"]: c for c in blob[field]}
    state = load_state()
    for name in configs:
        key = spec["key_prefix"] + name + suffix
        entry = state["runs"].get(key)
        if not entry or not entry.get("run_id"):
            print(f"{name}: not admitted, nothing to harvest")
            continue
        results_path, artifacts = download(key, entry["run_id"])
        if not results_path.exists():
            print(f"{key}: no results downloaded")
            continue
        rows = rows_of(results_path)
        receipts = {}
        for path in sorted(artifacts.rglob("receipt.json")):
            try:
                receipt = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            receipts[receipt.get("task_id") or path.parent.name] = receipt
        cells, charges = [], 0.0
        for task_id, meta in sorted(pack.items()):
            row, receipt = rows.get(task_id, {}), receipts.get(task_id, {})
            cell = {"task_id": task_id, "cell": meta["cell"], "item": meta["item"], "repeat": meta["repeat"],
                    "kind": meta.get("kind", "main"), "config": name, "agent_status": receipt.get("status"),
                    "cost_usd": receipt.get("cost_usd")}
            charges += cell["cost_usd"] or 0.0
            blob_b64 = row.get("solution_b64")
            if blob_b64:
                text = base64.b64decode(blob_b64).decode("utf-8", errors="replace")
                try:
                    raw_score, norm, verdict = prompts.parse(judge_config(name)["rubric"], text)
                    cell.update(status="measured", score_raw=raw_score, score=norm,
                               base_score=verdict.get("base_score"))
                except ValueError as exc:
                    cell.update(status="parse_error", error=str(exc)[:200])
            else:
                cell.update(status="unmeasured_infra", reason=receipt.get("reason") or "no verdict")
            cells.append(cell)
        counts: dict[str, int] = {}
        for cell in cells:
            counts[cell["status"]] = counts.get(cell["status"], 0) + 1
        out = {"written_utc": stamp(), "config": name, "run_id": entry["run_id"], "n_cells": len(cells),
               "status_counts": counts, "charges_usd": round(charges, 6), "cells": cells}
        write_json(RESULTS / "harvests" / f"cells_{key.replace('/', '__')}.json", out)
        print(json.dumps({key: {"status_counts": counts, "charges_usd": round(charges, 6)}}))
    return 0


def controls_verdict(suite: str = "rl4cv-e01-controls") -> int:
    spec = suite_spec(suite)
    per_config, verdicts = {}, []
    for name in CONFIGS:
        path = RESULTS / "harvests" / f"cells_{(spec['key_prefix'] + name).replace('/', '__')}@controls.json"
        if not path.exists():
            print(f"{name}: harvest --part controls first ({path} missing)")
            return 2
        harvested = json.loads(path.read_text())
        by_kind: dict[str, list[dict]] = {}
        for cell in harvested["cells"]:
            by_kind.setdefault(cell["kind"], []).append(cell)
        rows = {}
        for kind, expectation in CONTROL_EXPECTATIONS.items():
            cells = [c for c in by_kind.get(kind, []) if c["status"] == "measured"]
            passing = [c for c in cells if _control_ok(kind, c["score_raw"])]
            fraction = len(passing) / len(cells) if cells else 0.0
            ok = bool(cells) and fraction >= expectation["min_fraction"]
            rows[kind] = {"n_measured": len(cells), "fraction_meeting_rule": fraction, "passes": ok,
                         "scores_0_5": sorted(c["score_raw"] for c in cells)}
            verdicts.append(ok)
        per_config[name] = {"charges_usd": harvested["charges_usd"], "by_kind": rows}
    verdict = "PASS" if all(verdicts) else "FAIL"
    write_json(RESULTS / "judge_controls.json",
               {"written_utc": stamp(), "route": "Valkyrie (vb103_judge agent)", "per_member": per_config,
                "verdict": verdict})
    print(json.dumps({"verdict": verdict, **{c: {k: v["passes"] for k, v in per_config[c]["by_kind"].items()}
                                             for c in CONFIGS}}, indent=1))
    return 0 if verdict == "PASS" else 1


def fsc(suite: str) -> int:
    spec = suite_spec(suite)
    members, charges, counts = {}, {}, {}
    for name in CONFIGS:
        path = RESULTS / "harvests" / f"cells_{(spec['key_prefix'] + name).replace('/', '__')}.json"
        if not path.exists():
            print(f"{name}: harvest first ({path} missing)")
            return 2
        harvested = json.loads(path.read_text())
        by_item: dict[str, list[int]] = {}
        for cell in harvested["cells"]:
            if cell["status"] == "measured":
                by_item.setdefault(cell["item"], []).append(cell["score_raw"])
        members[name] = by_item
        charges[name] = harvested["charges_usd"]
        counts[name] = harvested["status_counts"]
    items = sorted(set(members[CONFIGS[0]]) | set(members[CONFIGS[1]]))
    per_task, incomplete = {}, []
    for item in items:
        medians = [statistics.median(members[c][item]) for c in CONFIGS if members[c].get(item)]
        if len(medians) < len(CONFIGS):
            incomplete.append(item)
            continue
        per_task[item] = {"FSC": statistics.fmean(medians) / 5.0,
                          "member_medians_0_5": {c: statistics.median(members[c][item]) for c in CONFIGS}}
    out = {"written_utc": stamp(), "suite": suite, "model": spec["model"], "n_items_judged": len(per_task),
           "items_incomplete": incomplete, "status_counts_per_member": counts, "charges_usd_per_member": charges,
           "charges_usd_total": round(sum(charges.values()), 6), "per_task": per_task}
    write_json(RESULTS.parent / f"fsc_{suite.split(':', 1)[-1]}.json", out)
    print(json.dumps({k: out[k] for k in ("suite", "n_items_judged", "charges_usd_total")}))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["build-controls", "build-model", "admit", "poll", "harvest",
                                       "controls", "fsc"])
    ap.add_argument("--label")
    ap.add_argument("--scored")
    ap.add_argument("--pack")
    ap.add_argument("--configs", default=",".join(CONFIGS))
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--part", choices=sorted(PARTS), default="gate")
    ap.add_argument("--suite", default="rl4cv-e01-controls")
    args = ap.parse_args()
    configs = [c for c in args.configs.split(",") if c]
    if args.action == "build-controls":
        manifest = build_controls(Path(args.pack))
        print(json.dumps({k: manifest[k] for k in ("verdict", "n_tasks_selected", "n_control_tasks")}))
        return 0 if manifest["verdict"] == "PASS" else 1
    if args.action == "build-model":
        manifest = build_model_pack(args.label, Path(args.scored))
        print(json.dumps({k: manifest[k] for k in ("verdict", "n_positive_cells", "n_audit_cells")}))
        return 0 if manifest["verdict"] == "PASS" else 1
    if args.action == "admit":
        return admit(configs, args.concurrency, args.part, args.suite)
    if args.action == "poll":
        return poll()
    if args.action == "harvest":
        return harvest(configs, args.part, args.suite)
    if args.action == "controls":
        return controls_verdict(args.suite)
    if args.action == "fsc":
        return fsc(args.suite)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
