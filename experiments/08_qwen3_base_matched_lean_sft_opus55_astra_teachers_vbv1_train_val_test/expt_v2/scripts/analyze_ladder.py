#!/usr/bin/env python3
"""TLDR: Experiment 08 validation ladder (PROTOCOL § 9): join every system's scored cells to the frozen 135 × 8 manifest (duplicates and extras rejected, missing cells listed as unknown), recompute `kernel_binary` with the same non-vacuity screen as the teacher adapter (Base 1.7B / 4B / 8B from experiment 05's preserved files, written as new experiment 08 receipts; the trained checkpoints and Base 14B from this experiment's runs), apply gates (a) extraction >= 90%, (b) capped <= 10%, (c) `kernel_binary` mixed-group share >= 0.05 with all 1,080 cells known, report the diagnostics (pass@8, all-pass, mean pass rate, IC_tests rate, mean proof fraction, mean generated tokens, within-task word-5-gram diversity) with Wilson 95% intervals, and select f* (RL-READY / PARTIAL / NOT READY / BLOCKED). Writes `validation_ladder.json`, per-task CSVs and `selection.json` with the frozen test manifest; zero model calls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "expt_v1/scripts"))
EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
E05_OUT = Path("/lfs/skampere1/0/brando9/rl4cv_e05/out")
G = 8
GATE_EXTRACT, GATE_CAP, GATE_MIXED = 0.90, 0.10, 0.05
SIZES = ("1.7B", "4B", "8B", "14B")
FRACTIONS = ("0.125", "0.25", "0.5", "0.75", "1.0")
BASE_E05 = {"1.7B": "qwen3-1.7b-base", "4B": "qwen3-4b-base", "8B": "qwen3-8b-base"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def wilson(k: int, n: int, z: float = 1.959964):
    if n == 0:
        return None, None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(p, 4), round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)


def read_ids(path: Path) -> list[str]:
    return [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.startswith("#")]


def cells_for(system: dict, ids: list[str], split: str) -> tuple[dict, dict]:
    """(cells keyed by (task, sample), notes). Each cell: known, extracted, capped, kernel_binary, IC_tests, IC_proofs, generated_tokens, lean text."""
    from rl4cv.rewards import ScoredResponse, reward_kernel_binary
    from score_teacher_files import vacuity

    if system["source"] == "e05":
        scored = E05_OUT / "scored" / f"scored_{system['e05_label']}_g8.jsonl"
        jobs = E05_OUT / "jobs"
        name = f"{system['e05_label']}_g8"
    else:
        scored = Path(system.get("runtime_root", WORK)) / "ladder" / split / "scored" / f"scored_{system['label']}_g8.jsonl"
        jobs = Path(system.get("runtime_root", WORK)) / "ladder" / split / "jobs"
        name = f"{system['label']}_g8"
    want = {(t, s) for t in ids for s in range(G)}
    cells, dups, extras = {}, 0, 0
    if not scored.exists():
        return {}, {"scored_file": str(scored), "missing_file": True}
    for line in scored.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        key = (r["task_id"], int(r["sample_idx"]))
        if key not in want:
            extras += 1 if r["task_id"] in ids else 0   # rows for other splits (experiment 05 holds all 896) are simply ignored
            continue
        if key in cells:
            dups += 1
            continue
        lean_path = jobs / f"{name}_s{key[1]}" / key[0] / "verifier" / "solution.lean"
        lean = lean_path.read_text(encoding="utf-8") if lean_path.is_file() else ""
        known = r.get("status") == "scored"
        kb, unparseable, n_vac = None, False, 0
        if known:
            vac = vacuity(lean) if lean.strip() else None
            n_vac = vac["n_vacuous"] if vac else 0
            unparseable = bool(vac and vac["unparseable"])
            s = ScoredResponse(extracted=bool(lean.strip()), compiles=bool(r.get("compiles")), n_examples=int(r.get("n_examples") or 0),
                               n_theorems_stated=int(r.get("n_theorems_stated") or 0), n_theorems_proved=int(r.get("n_theorems_proved") or 0),
                               vacuous_theorems=n_vac, truncated=bool(r.get("truncated")))
            kb = reward_kernel_binary(s)
            if unparseable and kb == 1.0:
                kb = 0.0   # conservative for a policy gate: an unparseable theorem type never counts as a pass (listed in notes)
        cells[key] = {"known": known, "extracted": r.get("extraction") != "no_lean_block" and bool(lean.strip()), "capped": bool(r.get("truncated")),
                      "kernel_binary": kb, "IC_tests": r.get("IC_tests"), "IC_proofs": r.get("IC_proofs"), "generated_tokens": r.get("generated_tokens"),
                      "n_vacuous": n_vac, "unparseable": unparseable, "lean": lean, "lean_sha256": sha(lean.encode("utf-8")) if lean else None}
    missing = sorted(k for k in want if k not in cells)
    return cells, {"scored_file": str(scored), "duplicates_rejected": dups, "extras_rejected": extras, "n_missing": len(missing), "missing": [f"{t}#{s}" for t, s in missing[:50]],
                   "n_unparseable_theorem_types": sum(1 for c in cells.values() if c["unparseable"]), "n_vacuous_cells": sum(1 for c in cells.values() if c["n_vacuous"])}


def evaluate(system: dict, ids: list[str], split: str, per_task_dir: Path) -> dict:
    from rl4cv.screens import jaccard, shingles

    cells, notes = cells_for(system, ids, split)
    n_declared = len(ids) * G
    known = [c for c in cells.values() if c["known"]]
    complete = len(known) == n_declared
    n_ext = sum(1 for c in known if c["extracted"])
    n_cap = sum(1 for c in known if c["capped"])
    per_task, diversity = [], []
    for t in ids:
        cs = [cells.get((t, s)) for s in range(G)]
        ks = [c["kernel_binary"] for c in cs if c and c["known"]]
        passes = sum(1 for k in ks if k == 1.0)
        leans = [c["lean"] for c in cs if c and c["known"] and c["lean"].strip()]
        if len(leans) >= 2:
            sh = [shingles(x) for x in leans]
            diversity.append(sum(jaccard(x, y) for x, y in combinations(sh, 2)) / math.comb(len(sh), 2))
        per_task.append({"task_id": t, "samples_known": len(ks), "k_kernel_binary": passes, "mixed": int(0 < passes < G) if len(ks) == G else None,
                         "k_ic_tests": sum(1 for c in cs if c and c["known"] and c["IC_tests"] == 1.0), "k_extracted": sum(1 for c in cs if c and c["known"] and c["extracted"]),
                         "k_capped": sum(1 for c in cs if c and c["known"] and c["capped"]),
                         "mean_proof_fraction": round(sum((c["IC_proofs"] or 0.0) for c in cs if c and c["known"]) / max(1, len(ks)), 5),
                         "mean_generated_tokens": round(sum((c["generated_tokens"] or 0) for c in cs if c and c["known"]) / max(1, len(ks)), 1)})
    mixed = sum(1 for p in per_task if p["mixed"] == 1)
    pass8 = sum(1 for p in per_task if p["k_kernel_binary"] > 0)
    allp = sum(1 for p in per_task if p["k_kernel_binary"] == G)
    gates = {"a_extraction": {"n": n_ext, "of": len(known), "share": round(n_ext / max(1, len(known)), 4), "threshold": GATE_EXTRACT, "pass": complete and n_ext >= math.ceil(GATE_EXTRACT * n_declared)},
             "b_capped": {"n": n_cap, "of": len(known), "share": round(n_cap / max(1, len(known)), 4), "threshold": GATE_CAP, "pass": complete and n_cap <= math.floor(GATE_CAP * n_declared)},
             "c_mixed": {"n": mixed, "of": len(ids), "share": round(mixed / len(ids), 4), "wilson95": list(wilson(mixed, len(ids))[1:]), "threshold": GATE_MIXED,
                         "pass": complete and mixed >= math.ceil(GATE_MIXED * len(ids))}, "complete": complete, "n_known": len(known), "n_declared": n_declared}
    gates["pass"] = complete and gates["a_extraction"]["pass"] and gates["b_capped"]["pass"] and gates["c_mixed"]["pass"]
    per_task_dir.mkdir(parents=True, exist_ok=True)
    csv_path = per_task_dir / f"{system['label']}_{split}_per_task.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(per_task[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(per_task)
    cells_csv = per_task_dir / f"{system['label']}_{split}_cells.csv"
    with cells_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["task_id", "sample_idx", "known", "extracted", "capped", "kernel_binary", "IC_tests", "IC_proofs", "n_vacuous", "unparseable", "generated_tokens", "lean_sha256"])
        for (t, s), c in sorted(cells.items()):
            w.writerow([t, s, c["known"], c["extracted"], c["capped"], c["kernel_binary"], c["IC_tests"], c["IC_proofs"], c["n_vacuous"], c["unparseable"], c["generated_tokens"], c["lean_sha256"]])
    return {"system": {k: v for k, v in system.items()}, "split": split, "gates": gates, "status": "COMPLETE" if complete else "INCOMPLETE",
            "diagnostics": {"pass_at_8_share": round(pass8 / len(ids), 4), "all_pass_share": round(allp / len(ids), 4),
                            "mean_pass_rate": round(sum(p["k_kernel_binary"] for p in per_task) / max(1, len(known)), 5),
                            "ic_tests_rate": round(sum(1 for c in known if c["IC_tests"] == 1.0) / max(1, len(known)), 5),
                            "mean_proof_fraction": round(sum(p["mean_proof_fraction"] for p in per_task) / len(ids), 5),
                            "mean_generated_tokens": round(sum((c["generated_tokens"] or 0) for c in known) / max(1, len(known)), 1),
                            "within_task_diversity_mean_pairwise_jaccard": round(sum(diversity) / len(diversity), 4) if diversity else None, "n_tasks_with_diversity": len(diversity)},
            "notes": notes, "per_task_csv": str(csv_path.relative_to(EXP)), "cells_csv": str(cells_csv.relative_to(EXP))}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=EXP / "results" / "ladder_manifest.json", help="frozen systems and cells (written before generation)")
    ap.add_argument("--split", default="validation", choices=["validation", "test"])
    ap.add_argument("--out", type=Path, default=EXP / "results" / "validation_ladder.json")
    ap.add_argument("--selection-out", type=Path, default=EXP / "results" / "selection.json")
    ap.add_argument("--per-task-dir", type=Path, default=EXP / "results" / "ladder")
    ap.add_argument("--no-selection", action="store_true")
    a = ap.parse_args(argv)
    manifest = json.loads(a.manifest.read_text())
    ids = read_ids(EXP.parent / "expt_v1" / "results" / "split" / f"vbv1_{a.split}_task_ids.txt")
    results = {}
    for system in manifest["systems"]:
        if a.split == "test" and not system.get("in_test", True):
            continue
        results[system["label"]] = evaluate(system, ids, a.split, a.per_task_dir)
    out = {"written_utc": stamp(), "split": a.split, "n_tasks": len(ids), "samples_per_task": G, "manifest_sha256": sha(a.manifest.read_bytes()),
           "gates": {"extraction_min_share": GATE_EXTRACT, "capped_max_share": GATE_CAP, "mixed_min_share": GATE_MIXED, "p_val": "n/a (prespecified point-estimate gate)"},
           "systems": results}
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    summary = {k: {"status": v["status"], "pass": v["gates"]["pass"], "mixed": v["gates"]["c_mixed"]["n"], "ext": v["gates"]["a_extraction"]["n"], "cap": v["gates"]["b_capped"]["n"]} for k, v in results.items()}
    print(json.dumps(summary, indent=1))
    if a.no_selection or a.split != "validation":
        return 0
    # Selection (PROTOCOL § 9): f* = smallest fraction at which all four sizes pass; incomplete inputs -> BLOCKED.
    table = {}
    for system in manifest["systems"]:
        if system.get("size") in SIZES and system.get("fraction") in FRACTIONS:
            table.setdefault(system["fraction"], {})[system["size"]] = results[system["label"]]
    incomplete = [lab for lab, r in results.items() if r["status"] == "INCOMPLETE" and r["system"].get("fraction") in FRACTIONS]
    f_star, verdict = None, None
    if incomplete:
        verdict = "BLOCKED"
    else:
        for f in FRACTIONS:
            if all(s in table.get(f, {}) and table[f][s]["gates"]["pass"] for s in SIZES):
                f_star = f
                break
        if f_star is not None:
            verdict = "RL-READY"
        elif any(table[f][s]["gates"]["pass"] for f in table for s in table[f]):
            verdict = "PARTIAL"
        else:
            verdict = "NOT READY"
    earliest = {s: next((f for f in FRACTIONS if f in table and s in table[f] and table[f][s]["gates"]["pass"]), None) for s in SIZES}
    selected = {}
    if verdict == "RL-READY":
        selected = {s: table[f_star][s]["system"] for s in SIZES}
    elif verdict == "PARTIAL":
        selected = {s: table[earliest[s]][s]["system"] for s in SIZES if earliest[s]}
    test_ids = read_ids(EXP.parent / "expt_v1" / "results" / "split" / "vbv1_test_task_ids.txt")
    test_systems = [{**sys_, "label": f"test_{sys_['label']}"} for sys_ in selected.values()] + [s for s in manifest["systems"] if s.get("role") == "base"]
    sel = {"written_utc": stamp(), "verdict": verdict, "f_star": f_star, "earliest_passing_fraction_per_size": earliest, "incomplete_systems": incomplete,
           "selected_systems": selected, "gate_table": {f: {s: {"pass": table[f][s]["gates"]["pass"], "mixed": table[f][s]["gates"]["c_mixed"]["n"], "status": table[f][s]["status"],
                                                                  "step": table[f][s]["system"].get("step"), "cumulative_assistant_tokens": table[f][s]["system"].get("cumulative_assistant_tokens")}
                                                             for s in SIZES if s in table.get(f, {})} for f in FRACTIONS if f in table},
           "tokens_needed": {s: selected[s].get("cumulative_assistant_tokens") for s in selected} if selected else None,
           "validation_ladder_sha256": sha(a.out.read_bytes()),
           "test_manifest": {"split": "test", "n_tasks": len(test_ids), "samples_per_task": G, "task_ids_sha256": sha("".join(t + "\n" for t in test_ids).encode()),
                             "systems": [{"label": s["label"], "size": s.get("size"), "role": s.get("role", "selected"), "source": s.get("source"), "hf_path": s.get("hf_path"),
                                          "weights_sha256_manifest": s.get("weights_sha256_manifest"), "e05_label": s.get("e05_label")} for s in test_systems],
                             "n_declared_cells": len(test_ids) * G * len(test_systems)},
           "rule": "f* = smallest fraction passing gates (a)-(c) at all four sizes; PARTIAL = some size passes some rung but no common one; NOT READY = none; BLOCKED = any gate input unknown"}
    a.selection_out.write_text(json.dumps(sel, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "f_star": f_star, "earliest": earliest, "tokens_needed": sel["tokens_needed"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
