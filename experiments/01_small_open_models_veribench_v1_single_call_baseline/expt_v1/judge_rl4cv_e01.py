#!/usr/bin/env python3
# TLDR: FSC judging for experiment 01, adapted from experiment 103's judge_vbv1.py/judge_controller.py/
# judge_pack.py (imported, not edited) so nothing here ever writes into veribench_vb103's private/ tree:
# every path below resolves relative to OUR OWN pinned external/veribench checkout, which is a physically
# separate clone. Suites: "rl4cv-e01-controls" (oracle/blank/shuffled/vacuous/halfdel, no model dependency)
# and "rl4cv-e01:<label>" (one model's measured cells with IC_tests*IC_proofs>0 plus a 60-file audit).
# Part "r23" (10-07-2026) completes PROTOCOL.md's locked "median of 3 each": repeats 2 and 3 of every
# repeat-1 main cell, byte-identical prompts, own pack/benchmark/harvest; `fsc-median3` combines them.
# Suite "rl4cv-e01-probe:<label>" (10-07-2026) judges the G = 8 probe's proving cells (IC_tests*IC_proofs>0;
# 4 for qwen3.5-9b, 7 for qwen3-14b): one item per (task, sample), all 3 repeats in one pack, own
# benchmark; `fsc-probe` aggregates them and exports FSC for rl4cv.veribench.collect's --fsc-root.
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
PACK = Path("/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896")
GEN_OUT = Path("/lfs/skampere1/0/brando9/rl4cv_e01/out")           # run_model.sh's $OUT
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

# experiment 103's veribench_valkyrie_service.py: CORE_SPLITS = ("easy_set", "cs_set", "humaneval_set",
# "realcode_set", "security_set"); PROTOCOL.md's 60-file audit is 12 per core split, 5*12=60.
CORE_SPLITS = ("easy_set", "cs_set", "humaneval_set", "realcode_set", "security_set")
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

def suite_spec(suite: str, part: str = "gate") -> dict:
    if suite == "rl4cv-e01-controls":
        return {"suite": suite, "model": None, "benchmark": "veribench-rl4cv-e01-controls",
                "pack_receipt": RESULTS / "judge_pack_controls.json", "key_prefix": "controls/",
                "condition": "rl4cv-e01-judge-controls"}
    if suite.startswith("rl4cv-e01-probe:"):
        # The G = 8 probe's proving cells: one pack carries all three repeats, so there is no r23 part.
        assert part == "gate", f"{suite}: the probe pack carries all 3 repeats in part 'gate'"
        label = suite.split(":", 1)[1]
        return {"suite": suite, "model": label,
                "benchmark": f"veribench-rl4cv-e01-probe-{label}".replace(".", "-"),
                "pack_receipt": RESULTS / f"judge_pack_probe_{label}.json", "key_prefix": f"probe-{label}/",
                "condition": f"rl4cv-e01-judge-probe-{label}"}
    assert suite.startswith("rl4cv-e01:"), f"unknown suite: {suite}"
    label = suite.split(":", 1)[1]
    if part == "r23":
        # Repeats 2-3 are a separate pack served by a separate benchmark instance (a judge service serves
        # one pack's bytes), so they never touch the repeat-1 pack, service or harvest.
        return {"suite": suite, "model": label,
                "benchmark": f"veribench-rl4cv-e01-{label}-r23".replace(".", "-"),
                "pack_receipt": RESULTS / f"judge_pack_{label}_r23.json", "key_prefix": f"{label}/",
                "condition": f"rl4cv-e01-judge-{label}-r23"}
    return {"suite": suite, "model": label, "benchmark": f"veribench-rl4cv-e01-{label}".replace(".", "-"),
            "pack_receipt": RESULTS / f"judge_pack_{label}.json", "key_prefix": f"{label}/",
            "condition": f"rl4cv-e01-judge-{label}"}


# part -> (pack-receipt field holding its cells, state-key / harvest-file suffix)
PARTS = {"gate": ("cells", ""), "controls": ("control_cells", "@controls"), "r23": ("cells", "@r23")}
REPEATS_R23 = (2, 3)


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

def build_model_pack(label: str, scored_jsonl: Path, per_core_split: int = 12, smoke_items: int = 1) -> dict:
    import re
    # NAME is run_model.sh's job name, e.g. "qwen3.5-4b_g1"; scored_<name>.jsonl -> strip the prefix.
    name = scored_jsonl.stem.removeprefix("scored_")
    jobs_dir = GEN_OUT / "jobs" / f"{name}_s0"
    rows = [json.loads(l) for l in scored_jsonl.read_text().splitlines() if l.strip()]
    measured = [r for r in rows if r.get("measured")]
    positives = [r for r in measured if (r.get("IC_tests") or 0) * (r.get("IC_proofs") or 0) > 0]
    by_split: dict[str, list[dict]] = {}
    for r in measured:
        by_split.setdefault(r["task_id"].split("__", 1)[0], []).append(r)
    # PROTOCOL.md's 60-file audit: 12 per core split, outcome-blind hash order (never based on score).
    audit = []
    for split in CORE_SPLITS:
        pool = sorted(by_split.get(split, []),
                     key=lambda r: sha(f"rl4cv-e01-audit:{label}:{r['task_id']}".encode()))
        audit.extend(pool[:per_core_split])
    chosen = {r["task_id"]: r for r in positives}
    for r in audit:
        chosen.setdefault(r["task_id"], r)

    root = PRIVATE / label / "inputs"
    items, skipped = [], {}
    for task_id, r in sorted(chosen.items()):
        solution_path = jobs_dir / task_id / "verifier" / "solution.lean"
        gold_src = PACK / task_id / "tests" / "gold.lean"
        instr_src = PACK / task_id / "instruction.md"
        if not solution_path.exists() or not gold_src.exists():
            skipped[task_id] = "missing_solution_or_gold_on_disk"
            continue
        lean = solution_path.read_text(encoding="utf-8", errors="replace")
        instruction = instr_src.read_text(encoding="utf-8", errors="replace")
        blocks = re.findall(r"```python\n(.*?)```", instruction, re.S)
        python = max(blocks, key=len) if blocks else ""
        directory = root / task_id
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "solution.lean").write_text(lean, encoding="utf-8")
        (directory / "source.py").write_text(python, encoding="utf-8")
        gold_path = directory / "gold.lean"
        gold_path.write_text(gold_src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
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
# Build: repeats 2-3 of one model's repeat-1 main cells (zero model calls, byte-identical prompts)
# --------------------------------------------------------------------------------------------------

def repeat_rows(r1_rows: list[dict], rendered_of, repeats: tuple[int, ...] = REPEATS_R23
                ) -> tuple[list[dict], dict[str, dict]]:
    """Pure: derive repeat-r cell rows from repeat-1 main cell rows.

    `rendered_of(cell_name) -> {"system", "user"}` returns the repeat-1 rendered prompt. Every derived row
    keeps the item's candidate_sha256 and prompt_sha256; the prompt text is re-hashed and must equal the
    recorded repeat-1 digest (a mismatch is a hard stop: the served bytes would not be the locked ones).
    Returns (rows, {new_cell_name: rendered}) so the caller writes the rendered files and the receipt.
    """
    rows, rendered_out = [], {}
    for row in r1_rows:
        assert row["kind"] == "main" and row["repeat"] == 1, row["cell"]
        rendered = rendered_of(row["cell"])
        system, user = rendered["system"], rendered["user"]
        digest = sha((system + "\n\n" + user).encode())
        if digest != row["prompt_sha256"]:
            raise SystemExit(f"{row['cell']}: rendered repeat-1 prompt sha256 {digest[:12]} != receipt "
                             f"{row['prompt_sha256'][:12]}; refusing to build repeats")
        for r in repeats:
            cell = f"{row['item']}__r{r}"
            rows.append({"cell": cell, "item": row["item"], "task": row["task"], "repeat": r,
                         "kind": "main", "candidate_sha256": row["candidate_sha256"],
                         "prompt_sha256": row["prompt_sha256"]})
            rendered_out[cell] = {"system": system, "user": user}
    return rows, rendered_out


def served_prompt_hashes(label: str) -> dict[str, str]:
    """prompt_sha256 the Valkyrie agent recorded for each served repeat-1 cell, from the raw receipts."""
    out = {}
    for name in CONFIGS:
        for path in (RESULTS / "raw" / f"{label}__{name}_artifacts").rglob("receipt.json"):
            try:
                receipt = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if receipt.get("cell") and receipt.get("prompt_sha256"):
                out.setdefault(receipt["cell"], receipt["prompt_sha256"])
    return out


def build_repeats(label: str, repeats: tuple[int, ...] = REPEATS_R23) -> dict:
    receipt_r1 = PRIVATE / label / "cells_receipt.json"
    rendered_dir = PRIVATE / label / "rendered"
    r1_rows = [r for r in json.loads(receipt_r1.read_text())["cells"]
               if r["kind"] == "main" and r["repeat"] == 1]
    assert r1_rows, f"{label}: no repeat-1 main cells in {receipt_r1}"
    rows, rendered_new = repeat_rows(
        r1_rows, lambda cell: json.loads((rendered_dir / f"{cell}.json").read_text()), repeats)
    # The agent's own receipts for repeat 1 carry the prompt hash it verified before calling the model;
    # the repeats must match those served bytes too (cells without a receipt were never served).
    served = served_prompt_hashes(label)
    served_mismatch = [r["cell"] for r in r1_rows
                       if r["cell"] in served and served[r["cell"]] != r["prompt_sha256"]]
    if served_mismatch:
        raise SystemExit(f"{label}: served repeat-1 prompt hash differs from receipt for {served_mismatch[:3]}")
    for cell, rendered in rendered_new.items():
        write_json(rendered_dir / f"{cell}.json", rendered)
    receipt_path = PRIVATE / label / "cells_receipt_r23.json"
    write_json(receipt_path, {"cells": rows, "derived_from": str(receipt_r1), "repeats": list(repeats),
                              "r1_receipt_sha256": sha(receipt_r1.read_bytes())})

    pack_path = PRIVATE / "packs" / f"judge_rl4cv_e01_{label}_r23"
    judge_pack.RENDERED = rendered_dir
    manifest = judge_pack.build(pack_path, receipt_path, "judge", smoke_items=0)
    manifest["round_trip"] = judge_pack.verify(pack_path, manifest)
    by_r1 = {r["item"]: r["prompt_sha256"] for r in r1_rows}
    hash_mismatch = [c["cell"] for c in manifest["cells"] if c["prompt_sha256"] != by_r1[c["item"]]]
    manifest["written_utc"] = stamp()
    manifest["repeats"] = list(repeats)
    manifest["n_r1_main_cells"] = len(r1_rows)
    manifest["n_cells"] = len(manifest["cells"])
    manifest["n_served_r1_receipts_checked"] = sum(1 for r in r1_rows if r["cell"] in served)
    manifest["prompt_sha256_mismatches_vs_r1"] = hash_mismatch
    ok = (not manifest["round_trip"]["failures"] and not hash_mismatch
          and manifest["n_cells"] == len(repeats) * len(r1_rows) and manifest["n_smoke_tasks"] == 0)
    manifest["verdict"] = "PASS" if ok else "FAIL"
    write_json(suite_spec(f"rl4cv-e01:{label}", "r23")["pack_receipt"], manifest)
    if hash_mismatch:
        raise SystemExit(f"{label}: pack prompt hash != repeat-1 hash for {hash_mismatch[:3]}")
    return manifest


# --------------------------------------------------------------------------------------------------
# Probe (G = 8): list the proving cells, build one pack per model with all 3 repeats (zero model calls)
# --------------------------------------------------------------------------------------------------

PROBE_LABELS = ("qwen3.5-0.8b", "qwen3.5-2b", "qwen3.5-4b", "qwen3.5-9b", "qwen3-1.7b", "qwen3-4b",
                "qwen3-8b", "qwen3-14b")
PROBE_EXPECTED = {"qwen3.5-9b": 4, "qwen3-14b": 7}      # REPORT.md 17 / the runbook: 11 cells in all
REPEATS_PROBE = (1, 2, 3)
PROBE_CELLS = RESULTS / "probe_proving_cells.json"


def probe_cells_from_scored(label: str, rows: list[dict]) -> list[dict]:
    """Pure: the scored G = 8 rows with IC_tests * IC_proofs > 0, one item per (task, sample)."""
    out = []
    for r in rows:
        if r.get("status") != "scored":
            continue
        ic_t, ic_p = float(r.get("IC_tests") or 0.0), float(r.get("IC_proofs") or 0.0)
        if ic_t * ic_p > 0:
            k = int(r["sample_idx"])
            out.append({"model": label, "task_id": r["task_id"], "sample_idx": k,
                        "item": f"{r['task_id']}__s{k}", "split": r.get("split"),
                        "IC_tests": ic_t, "IC_proofs": ic_p, "measured": r.get("measured"),
                        "admitted": r.get("admitted"), "truncated": r.get("truncated"),
                        "generated_tokens": r.get("generated_tokens"), "rewards_before_judging": r.get("rewards")})
    return sorted(out, key=lambda c: (c["task_id"], c["sample_idx"]))


def probe_solution_path(label: str, task_id: str, sample_idx: int) -> Path:
    return GEN_OUT / "jobs" / f"{label}_g8_s{sample_idx}" / task_id / "verifier" / "solution.lean"


def list_probe_cells() -> dict:
    """Find every proving probe cell over all 8 probe models and record it with its solution's SHA-256.

    The verdict is PASS only when the counts are exactly the expected 4 + 7 (every other model 0) and
    every solution file on disk hashes to what the generation receipt recorded.
    """
    cells, per_label = [], {}
    for label in PROBE_LABELS:
        path = GEN_OUT / "scored" / f"scored_{label}_g8.jsonl"
        rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        found = probe_cells_from_scored(label, rows)
        for c in found:
            sol = probe_solution_path(label, c["task_id"], c["sample_idx"])
            receipt = sol.parent.parent / "receipt.json"
            c["solution_path"] = str(sol)
            c["solution_sha256"] = sha(sol.read_bytes()) if sol.exists() else None
            c["receipt_solution_sha256"] = (json.loads(receipt.read_text()).get("solution_sha256")
                                            if receipt.exists() else None)
        per_label[label] = {"scored_jsonl": str(path), "scored_sha256": sha(path.read_bytes()), "n_rows": len(rows),
                            "n_ic_tests_positive": sum(1 for r in rows if (r.get("IC_tests") or 0) > 0),
                            "n_proving": len(found), "n_expected": PROBE_EXPECTED.get(label, 0)}
        cells += found
    counts_ok = all(v["n_proving"] == v["n_expected"] for v in per_label.values())
    hashes_ok = all(c["solution_sha256"] and c["solution_sha256"] == c["receipt_solution_sha256"] for c in cells)
    out = {"written_utc": stamp(), "rule": "status == scored and IC_tests * IC_proofs > 0 on scored_<label>_g8.jsonl",
           "expected": PROBE_EXPECTED, "n_cells": len(cells), "n_expected": sum(PROBE_EXPECTED.values()),
           "counts_match": counts_ok, "solution_hashes_match_receipts": hashes_ok,
           "verdict": "PASS" if counts_ok and hashes_ok else "FAIL", "per_label": per_label, "cells": cells}
    write_json(PROBE_CELLS, out)
    return out


def build_probe_pack(label: str, repeats: tuple[int, ...] = REPEATS_PROBE) -> dict:
    """One item per proving (task, sample) cell; the candidate is that sample's solution.lean, the gold
    file and Python source come from the pack exactly as build_model_pack assembles them; the prompt is
    rendered once per item and repeats 2-3 reuse its bytes (repeat_rows asserts the hash)."""
    import re
    listing = json.loads(PROBE_CELLS.read_text())
    assert listing.get("verdict") == "PASS", f"{PROBE_CELLS}: verdict is not PASS; run list-probe-cells first"
    wanted = [c for c in listing["cells"] if c["model"] == label]
    assert wanted, f"{label}: no proving probe cells listed"
    root = PRIVATE / f"probe-{label}" / "inputs"
    items = []
    for c in wanted:
        task_id, k = c["task_id"], int(c["sample_idx"])
        solution_path = probe_solution_path(label, task_id, k)
        gold_src, instr_src = PACK / task_id / "tests" / "gold.lean", PACK / task_id / "instruction.md"
        assert solution_path.exists() and gold_src.exists(), f"{c['item']}: missing solution or gold on disk"
        raw = solution_path.read_bytes()
        if sha(raw) != c["solution_sha256"]:
            raise SystemExit(f"{c['item']}: solution.lean sha256 {sha(raw)[:12]} != listed {c['solution_sha256'][:12]}")
        lean = raw.decode("utf-8", errors="replace")
        instruction = instr_src.read_text(encoding="utf-8", errors="replace")
        blocks = re.findall(r"```python\n(.*?)```", instruction, re.S)
        python = max(blocks, key=len) if blocks else ""
        directory = root / c["item"]
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "solution.lean").write_text(lean, encoding="utf-8")
        (directory / "source.py").write_text(python, encoding="utf-8")
        gold_path = directory / "gold.lean"
        gold_path.write_text(gold_src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        n_ref = len(build_inputs.statements(gold_path.read_text(encoding="utf-8", errors="replace")))
        # `task` stays the VeriBench task id: prompts.demo_items leaves that task out of the rated demos.
        items.append({"item": c["item"], "task": task_id, "sample_idx": k, "split": task_id.split("__", 1)[0],
                      "candidate_file": "solution.lean", "gold_file_name": "gold.lean",
                      "candidate_path": relative(directory / "solution.lean"),
                      "ref_ann_path": relative(gold_path), "py_ann_path": relative(directory / "source.py"),
                      "ref_placeholder_at_annotation": False, "n_ref_theorems_ann": n_ref,
                      "solution_sha256": c["solution_sha256"], "is_audit_only": False})
    (PRIVATE / f"probe-{label}" / "items.jsonl").write_text("".join(json.dumps(r) + "\n" for r in items))

    rendered_dir = PRIVATE / f"probe-{label}" / "rendered"
    r1_rows = []
    for row in items:
        candidate = (root / row["item"] / "solution.lean").read_text(encoding="utf-8", errors="replace")
        system, user = prompts.render(RUBRIC, row, candidate, row["candidate_file"])
        digest = sha((system + "\n\n" + user).encode())
        cell = f"{row['item']}__r1"
        write_json(rendered_dir / f"{cell}.json", {"system": system, "user": user})
        r1_rows.append({"cell": cell, "item": row["item"], "task": row["task"], "repeat": 1, "kind": "main",
                        "candidate_sha256": sha(candidate.encode()), "prompt_sha256": digest})
    later = tuple(r for r in repeats if r != 1)
    more, rendered_new = repeat_rows(
        r1_rows, lambda cell: json.loads((rendered_dir / f"{cell}.json").read_text()), later)
    for cell, rendered in rendered_new.items():
        write_json(rendered_dir / f"{cell}.json", rendered)
    rows = sorted(r1_rows + more, key=lambda r: (r["item"], r["repeat"]))
    receipt_path = PRIVATE / f"probe-{label}" / "cells_receipt.json"
    write_json(receipt_path, {"cells": rows, "repeats": list(repeats), "source": str(PROBE_CELLS),
                              "source_sha256": sha(PROBE_CELLS.read_bytes())})

    pack_path = PRIVATE / "packs" / f"judge_rl4cv_e01_probe_{label}"
    judge_pack.RENDERED = rendered_dir
    manifest = judge_pack.build(pack_path, receipt_path, "judge", smoke_items=0)
    manifest["round_trip"] = judge_pack.verify(pack_path, manifest)
    by_item = {r["item"]: r["prompt_sha256"] for r in r1_rows}
    hash_mismatch = [c["cell"] for c in manifest["cells"] if c["prompt_sha256"] != by_item[c["item"]]]
    manifest["written_utc"] = stamp()
    manifest["repeats"] = list(repeats)
    manifest["n_items"] = len(items)
    manifest["n_cells"] = len(manifest["cells"])
    manifest["items"] = [{k: row[k] for k in ("item", "task", "sample_idx", "split", "solution_sha256")}
                         for row in items]
    manifest["prompt_sha256_mismatches_vs_r1"] = hash_mismatch
    ok = (not manifest["round_trip"]["failures"] and not hash_mismatch
          and manifest["n_cells"] == len(repeats) * len(items) and manifest["n_smoke_tasks"] == 0
          and manifest["n_control_tasks"] == 0)
    manifest["verdict"] = "PASS" if ok else "FAIL"
    write_json(suite_spec(f"rl4cv-e01-probe:{label}")["pack_receipt"], manifest)
    if hash_mismatch:
        raise SystemExit(f"{label}: pack prompt hash != repeat-1 hash for {hash_mismatch[:3]}")
    return manifest


def probe_fsc_export(per_task: dict[str, dict]) -> dict[int, dict[str, float]]:
    """Pure: {sample_idx: {task_id: FSC}} over complete items only (rl4cv.veribench.collect's --fsc-root
    layout, one <job>_s<k>.json per sample); an incomplete item is left out, so its judged channels
    stay null (unmeasured), never 0."""
    out: dict[int, dict[str, float]] = {}
    for row in per_task.values():
        if row.get("complete"):
            out.setdefault(int(row["sample_idx"]), {})[row["task_id"]] = row["FSC"]
    return out


def fsc_probe(suite: str) -> int:
    """Aggregate a probe suite's harvests (median of 3 per member, mean of the 2, / 5) per (task, sample)
    item, write fsc_probe_<label>.json and export GEN_OUT/fsc/<label>_g8_s<k>.json for collect."""
    spec = suite_spec(suite)
    label = spec["model"]
    listing = json.loads(PROBE_CELLS.read_text())
    meta = {c["item"]: c for c in listing["cells"] if c["model"] == label}
    members, bases, charges, counts, runs = {}, {}, {}, {}, {}
    for name in CONFIGS:
        by_item: dict[str, list[int]] = {}
        by_base: dict[str, list[float]] = {}
        for suffix in ("", RECOVERY_SUFFIX):
            path = RESULTS / "harvests" / f"cells_{(spec['key_prefix'] + name + suffix).replace('/', '__')}.json"
            if not path.exists():
                if suffix:
                    continue                       # no recovery pass was needed for this member
                print(f"{name}: harvest first ({path} missing)")
                return 2
            harvested = json.loads(path.read_text())
            for cell in sorted(harvested["cells"], key=lambda c: c["repeat"]):
                if cell["status"] == "measured":
                    by_item.setdefault(cell["item"], []).append(cell["score_raw"])
                    if cell.get("base_score") is not None:
                        by_base.setdefault(cell["item"], []).append(float(cell["base_score"]))
            charges[f"{name}{suffix}"] = harvested["charges_usd"]
            counts[f"{name}{suffix}"] = harvested["status_counts"]
            runs[f"{name}{suffix}"] = harvested.get("run_id")
        members[name], bases[name] = by_item, by_base
    per_task, incomplete = aggregate_median3(members, bases)
    for item, row in per_task.items():
        m = meta[item]
        row.update(task_id=m["task_id"], sample_idx=m["sample_idx"], split=m["split"],
                   IC_tests=m["IC_tests"], IC_proofs=m["IC_proofs"])
        row["SCSC"] = ((m["IC_tests"] * m["IC_proofs"] * row["FSC"]) ** (1 / 3)) if row["complete"] else None
    unjudged = sorted(set(meta) - set(per_task))
    complete = [r for r in per_task.values() if r["complete"]]
    lt3 = {c: sum(1 for r in complete if r["repeats"][c] < 3) for c in CONFIGS}
    export = probe_fsc_export(per_task)
    fsc_dir = GEN_OUT / "fsc"
    fsc_dir.mkdir(parents=True, exist_ok=True)
    exported = {}
    for k, mapping in sorted(export.items()):
        path = fsc_dir / f"{label}_g8_s{k}.json"
        path.write_text(json.dumps(mapping, indent=1, sort_keys=True) + "\n")
        exported[str(path)] = len(mapping)
    out = {"written_utc": stamp(), "suite": suite, "model": label,
           "judge": ("experiment 100 frozen H2 ensemble: per-member median of 3 repeats, mean of the two "
                     "members, integer 0-5 divided by 5 (PROTOCOL.md 'median of 3 each')"),
           "missing_repeat_rule": ("VeriBench experiment 103 scripts/judge_controller.py fsc() lines 622-635 at "
                                   "commit c11b99ba, applied verbatim (see aggregate_median3)"),
           "route": "Valkyrie (vb103_judge)", "runs": runs, "n_items_declared": len(meta),
           "n_items_judged": len(per_task), "n_items_complete": len(complete), "items_unjudged": unjudged,
           "items_with_missing_repeats": incomplete,
           "n_complete_items_with_fewer_than_3_repeats_per_member": lt3,
           "mean_FSC_complete_items": statistics.fmean(r["FSC"] for r in complete) if complete else None,
           "mean_SCSC_complete_items": statistics.fmean(r["SCSC"] for r in complete) if complete else None,
           "status_counts_per_member_and_part": counts, "charges_usd_per_member_and_part": charges,
           "charges_usd_total": round(sum(charges.values()), 6), "fsc_root_exports": exported,
           "per_task": per_task}
    write_json(RESULTS.parent / f"fsc_probe_{label}.json", out)
    print(json.dumps({k: out[k] for k in ("suite", "n_items_declared", "n_items_judged", "n_items_complete",
                                          "mean_FSC_complete_items", "mean_SCSC_complete_items",
                                          "charges_usd_total")}))
    return 0


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
    spec = suite_spec(suite, part)
    pack = json.loads(spec["pack_receipt"].read_text())
    assert not pack.get("round_trip", {}).get("failures"), f"{suite}: pack failed round-trip"
    assert pack.get("verdict") == "PASS", f"{suite}/{part}: pack verdict is not PASS"
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


RECOVERY_SUFFIX = "__recovery_1"


def rows_via_task(run_id: str, task_ids: list[str], workers: int = 8) -> dict[str, dict]:
    """Fallback for `valk run results` (tracker returned a malformed response for every run, old and new,
    on 10-07-2026): fetch each task's `evaluation_result` with `valk run task`, which carries the same
    `solution_b64` verdict bytes the run-level results file does. Same route, same bytes, per task."""
    from concurrent.futures import ThreadPoolExecutor
    def one(task_id: str) -> tuple[str, dict]:
        for attempt in range(3):
            result = cli(["run", "task", run_id, task_id, "--format", "json"], timeout=300)
            try:
                payload = json.loads(result.stdout)
                row = payload.get("evaluation_result") or {}
                return task_id, (row if isinstance(row, dict) else {})
            except json.JSONDecodeError:
                continue
        return task_id, {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return dict(pool.map(one, task_ids))


def harvest(configs: list[str], part: str, suite: str, recovery: bool = False) -> int:
    spec = suite_spec(suite, part)
    blob = json.loads(spec["pack_receipt"].read_text())
    field, suffix = PARTS[part]
    if recovery:
        suffix += RECOVERY_SUFFIX
    pack_all = {c["task_id"]: c for c in blob[field]}
    state = load_state()
    for name in configs:
        key = spec["key_prefix"] + name + suffix
        entry = state["runs"].get(key)
        if not entry or not entry.get("run_id"):
            print(f"{name}: not admitted, nothing to harvest")
            continue
        # A recovery harvest covers exactly the cells that recovery re-sent, nothing else.
        pack = ({t: pack_all[t] for t in entry["task_ids"]} if recovery else pack_all)
        results_path, artifacts = download(key, entry["run_id"])
        if results_path.exists():
            rows, results_source = rows_of(results_path), "valk run results"
        else:
            rows, results_source = rows_via_task(entry["run_id"], sorted(pack)), "valk run task (per task)"
            print(f"{key}: run-level results unavailable; fetched {len(rows)} per-task results")
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
                    "requests_sent": receipt.get("requests_sent"), "cost_usd": receipt.get("cost_usd")}
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
               "results_source": results_source, "status_counts": counts, "charges_usd": round(charges, 6),
               "cells": cells}
        write_json(RESULTS / "harvests" / f"cells_{key.replace('/', '__')}.json", out)
        print(json.dumps({key: {"status_counts": counts, "charges_usd": round(charges, 6)}}))
    return 0


def recover(configs: list[str], concurrency: int, part: str, suite: str) -> int:
    """The single declared recovery pass for a part: re-send, once and as the identical cell on the same
    benchmark, ONLY cells harvested `unmeasured_infra` whose receipt shows no model request was served
    (no receipt at all, or requests_sent == 0). Cells with a served or possibly served request stay
    unmeasured and are listed. Refuses to run twice for the same suite/member."""
    spent = spent_so_far()
    if spent >= SPEND_CAP_USD:
        print(f"SPEND CAP HIT: ${spent:.2f} >= ${SPEND_CAP_USD}; refusing new admissions")
        return 3
    spec = suite_spec(suite, part)
    field, suffix = PARTS[part]
    state = load_state()
    for name in configs:
        base_key = spec["key_prefix"] + name + suffix
        key = base_key + RECOVERY_SUFFIX
        if key in state["runs"]:
            print(f"{key}: recovery already admitted as {state['runs'][key].get('run_id')}; refusing a second pass")
            continue
        original = state["runs"].get(base_key, {})
        if original.get("phase") != "terminal":
            print(f"{base_key}: original run is {original.get('phase')}, not terminal; harvest it first")
            continue
        path = RESULTS / "harvests" / f"cells_{base_key.replace('/', '__')}.json"
        if not path.exists():
            print(f"{base_key}: harvest first ({path} missing)")
            continue
        unmeasured = [c for c in json.loads(path.read_text())["cells"] if c["status"] == "unmeasured_infra"]
        eligible = [c for c in unmeasured if not c.get("requests_sent")]
        served = [c["task_id"] for c in unmeasured if c.get("requests_sent")]
        if not eligible:
            print(json.dumps({key: {"eligible": 0, "kept_unmeasured_served": served}}))
            continue
        ids_file = RESULTS / f"task_ids_{suite.replace(':', '_').replace('.', '-')}_{part}{RECOVERY_SUFFIX}_{name}.txt"
        ids_file.write_text("".join(c["task_id"] + "\n" for c in eligible))
        cfg = judge_config(name)
        kwargs = dict(original["kwargs"])            # identical judge settings to the original admission
        assert kwargs["benchmark"] == spec["benchmark"] and kwargs["judge_config"] == name
        args = ["run", "start", "--agent", AGENT, "--benchmark", spec["benchmark"], "--dataset", "default",
                "--model", cfg["selector"], "--concurrency", str(concurrency),
                "--label", f"rl4cv-e01-judge-{suite.replace(':', '-')}-{part}-{name}-recovery-1"[:96],
                "--task-ids-file", str(ids_file)]
        for kwarg, value in kwargs.items():
            args += ["-k", kwarg, value]
        entry = {"config": name, "selector": cfg["selector"], "kwargs": kwargs, "concurrency": concurrency,
                 "expected_cells": len(eligible), "part": part, "suite": suite, "benchmark": spec["benchmark"],
                 "recovery_of": base_key, "task_ids": [c["task_id"] for c in eligible],
                 "kept_unmeasured_served": served, "admitted_at": stamp(), "phase": "admitting", "command": args}
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
            print(f"{key}: run_id={found[0]} over {len(eligible)} never-served cell(s); "
                  f"kept unmeasured (served): {served}")
        save_state(state)
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


def aggregate_median3(members: dict[str, dict[str, list[int]]],
                      bases: dict[str, dict[str, list[float]]] | None = None) -> tuple[dict, list]:
    """Pure: per-item FSC from each member's measured repeat scores (0-5), as experiment 103 does it.

    Rule applied verbatim from VeriBench experiment 103 `scripts/judge_controller.py` (pinned commit
    c11b99ba) `fsc()`, lines 622-635: a member's value is the median of its measured repeats, whatever
    their number; FSC = mean of the member medians / 5 and is reported whenever at least one member
    measured; an item is `complete` only when both members have at least one measured repeat, and it is
    listed under `items_with_missing_repeats` when any member has fewer than 2 measured repeats.
    """
    bases = bases or {}
    items = sorted(set().union(*[set(m) for m in members.values()]))
    per_task, incomplete = {}, []
    for item in items:
        medians = [statistics.median(members[c][item]) for c in CONFIGS if members[c].get(item)]
        repeats = {c: len(members[c].get(item, [])) for c in CONFIGS}
        if len(medians) < len(CONFIGS) or any(n < 2 for n in repeats.values()):
            incomplete.append({"item": item, "repeats": repeats})
        if not medians:
            continue
        base_medians = [statistics.median(bases[c][item]) for c in CONFIGS
                        if bases.get(c, {}).get(item)]
        per_task[item] = {"FSC": statistics.fmean(medians) / 5.0,
                          "member_medians_0_5": {c: statistics.median(members[c][item])
                                                 for c in CONFIGS if members[c].get(item)},
                          "member_repeat_scores_0_5": {c: list(members[c].get(item, [])) for c in CONFIGS},
                          "base_score_0_5": statistics.fmean(base_medians) if base_medians else None,
                          "repeats": repeats, "complete": len(medians) == len(CONFIGS)}
    return per_task, incomplete


def fsc_median3(suite: str) -> int:
    """Combine the repeat-1 harvest with the @r23 harvest per member and write fsc_median3_<label>.json.

    Never edits fsc_<label>.json or any harvest; the single-repeat FSC is carried beside the new value.
    """
    spec = suite_spec(suite)
    label = spec["model"]
    members, bases, charges, counts, runs = {}, {}, {}, {}, {}
    for name in CONFIGS:
        by_item: dict[str, list[int]] = {}
        by_base: dict[str, list[float]] = {}
        for suffix in ("", "@r23", "@r23" + RECOVERY_SUFFIX):
            path = RESULTS / "harvests" / f"cells_{label}__{name}{suffix}.json"
            if not path.exists():
                if suffix.endswith(RECOVERY_SUFFIX):
                    continue                       # no recovery pass was needed for this member
                print(f"{name}: harvest first ({path} missing)")
                return 2
            harvested = json.loads(path.read_text())
            for cell in sorted(harvested["cells"], key=lambda c: c["repeat"]):
                if cell["status"] == "measured":
                    by_item.setdefault(cell["item"], []).append(cell["score_raw"])
                    if cell.get("base_score") is not None:
                        by_base.setdefault(cell["item"], []).append(float(cell["base_score"]))
            charges[f"{name}{suffix}"] = harvested["charges_usd"]
            counts[f"{name}{suffix}"] = harvested["status_counts"]
            runs[f"{name}{suffix}"] = harvested.get("run_id")
        members[name], bases[name] = by_item, by_base
    per_task, incomplete = aggregate_median3(members, bases)
    old_path = RESULTS.parent / f"fsc_{label}.json"
    old = json.loads(old_path.read_text())["per_task"] if old_path.exists() else {}
    for item, row in per_task.items():
        row["FSC_single_repeat"] = old.get(item, {}).get("FSC")
    complete = [row for row in per_task.values() if row["complete"]]
    paired = [(row["FSC_single_repeat"], row["FSC"]) for row in complete
              if row["FSC_single_repeat"] is not None]
    lt3 = {c: sum(1 for row in complete if row["repeats"][c] < 3) for c in CONFIGS}
    out = {"written_utc": stamp(), "suite": suite, "model": label,
           "judge": ("experiment 100 frozen H2 ensemble: per-member median of 3 repeats, mean of the two "
                     "members, integer 0-5 divided by 5 (PROTOCOL.md 'median of 3 each')"),
           "missing_repeat_rule": ("VeriBench experiment 103 scripts/judge_controller.py fsc() lines "
                                   "622-635 at commit c11b99ba, applied verbatim: member value = median of "
                                   "its measured repeats; complete = both members measured at least once; "
                                   "items with any member < 2 repeats are listed, never dropped"),
           "route": "Valkyrie (vb103_judge)", "runs": runs,
           "n_items_judged": len(per_task), "n_items_complete": len(complete),
           "mean_FSC_complete_items": statistics.fmean(r["FSC"] for r in complete) if complete else None,
           "median_FSC_complete_items": statistics.median(r["FSC"] for r in complete) if complete else None,
           "n_paired_with_single_repeat": len(paired),
           "mean_FSC_single_repeat_same_items": statistics.fmean(o for o, _ in paired) if paired else None,
           "mean_FSC_median3_same_items": statistics.fmean(n for _, n in paired) if paired else None,
           "n_complete_items_with_fewer_than_3_repeats_per_member": lt3,
           "items_with_missing_repeats": incomplete,
           "status_counts_per_member_and_part": counts, "charges_usd_per_member_and_part": charges,
           "charges_usd_total": round(sum(charges.values()), 6), "per_task": per_task}
    write_json(RESULTS.parent / f"fsc_median3_{label}.json", out)
    print(json.dumps({k: out[k] for k in ("suite", "n_items_judged", "n_items_complete",
                                          "mean_FSC_complete_items", "mean_FSC_single_repeat_same_items",
                                          "mean_FSC_median3_same_items", "charges_usd_total")}))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["build-controls", "build-model", "build-repeats", "list-probe-cells",
                                       "build-probe", "admit", "poll", "harvest", "recover", "controls", "fsc",
                                       "fsc-median3", "fsc-probe"])
    ap.add_argument("--recovery", action="store_true", help="harvest: the part's recovery_1 run instead")
    ap.add_argument("--repeats", default="2,3", help="build-repeats: repeat indices to derive (default 2,3)")
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
    if args.action == "build-repeats":
        repeats = tuple(int(r) for r in args.repeats.split(",") if r)
        assert repeats == REPEATS_R23, f"only repeats {REPEATS_R23} are wired to the r23 part, got {repeats}"
        manifest = build_repeats(args.label, repeats)
        print(json.dumps({k: manifest[k] for k in ("verdict", "n_r1_main_cells", "n_cells", "n_smoke_tasks",
                                                    "n_served_r1_receipts_checked")}))
        return 0 if manifest["verdict"] == "PASS" else 1
    if args.action == "list-probe-cells":
        listing = list_probe_cells()
        print(json.dumps({k: listing[k] for k in ("verdict", "n_cells", "n_expected", "counts_match",
                                                   "solution_hashes_match_receipts")}))
        return 0 if listing["verdict"] == "PASS" else 1
    if args.action == "build-probe":
        manifest = build_probe_pack(args.label)
        print(json.dumps({k: manifest[k] for k in ("verdict", "n_items", "n_cells", "n_smoke_tasks")}))
        return 0 if manifest["verdict"] == "PASS" else 1
    if args.action == "fsc-median3":
        return fsc_median3(args.suite)
    if args.action == "fsc-probe":
        return fsc_probe(args.suite)
    if args.action == "admit":
        return admit(configs, args.concurrency, args.part, args.suite)
    if args.action == "poll":
        return poll()
    if args.action == "harvest":
        return harvest(configs, args.part, args.suite, recovery=args.recovery)
    if args.action == "recover":
        return recover(configs, args.concurrency, args.part, args.suite)
    if args.action == "controls":
        return controls_verdict(args.suite)
    if args.action == "fsc":
        return fsc(args.suite)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
