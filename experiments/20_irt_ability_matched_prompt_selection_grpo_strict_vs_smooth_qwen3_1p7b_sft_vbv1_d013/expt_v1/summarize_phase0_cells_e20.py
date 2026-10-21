"""Summarize the complete saved Phase 0 score table with train-task-group uncertainty and explicit missing factors."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def summarize(scores: Path, tasks: Path) -> dict:
    rows = list(csv.DictReader(scores.open(newline="")))
    task_rows = list(csv.DictReader(tasks.open(newline="")))
    group_of = {r["task_id"]: r["group_id"] for r in task_rows}
    expected = {(t, k) for t in group_of for k in range(8)}
    keys = [(r["task_id"], int(r["sample_idx"])) for r in rows]
    if len(rows) != 4312 or len(group_of) != 539 or len(set(keys)) != len(keys) or set(keys) != expected:
        raise ValueError("Expected exactly the 539 train tasks and eight saved generations per task")
    if any(r["status"] != "measured" or r["partial_status"] not in ("measured", "parse_failure_zero_credit") for r in rows):
        raise ValueError("Unresolved cells require explicit missing-cohort reporting; no complete summary is emitted")
    if any(r["strict"] not in ("0", "1") or (r["partial_status"] == "parse_failure_zero_credit" and float(r["factored_reward"]) != 0) for r in rows):
        raise ValueError("Strict scores must be binary and malformed-source reward must be zero")
    if any(r["FSC"] not in ("", "unmeasured") for r in rows):
        raise ValueError("No formal-specification-coverage judge calls were authorized")
    groups = sorted(set(group_of.values()))
    if len(groups) != 400:
        raise ValueError("Expected the 400 frozen D-013 train groups")
    group_index = {g: i for i, g in enumerate(groups)}
    metrics = ("strict", "factored_reward", "IC_tests", "IC_proofs", "compiles", "capped")
    values = np.array([[float(r[k]) if k != "capped" else float(r[k] == "True") for k in metrics] for r in rows])
    if not np.isfinite(values).all() or np.any((values < 0) | (values > 1)):
        raise ValueError("Nonfinite or out-of-range observed score")
    sums = np.zeros((len(groups), len(metrics)))
    counts = np.zeros(len(groups))
    for r, value in zip(rows, values):
        i = group_index[group_of[r["task_id"]]]
        sums[i] += value
        counts[i] += 1
    rng = np.random.default_rng(20261021)
    # Multinomial counts are exactly a bootstrap over 400 whole task groups.
    weights = rng.multinomial(len(groups), np.full(len(groups), 1 / len(groups)), size=10000)
    boot = weights @ sums / (weights @ counts)[:, None]
    result = {}
    for j, name in enumerate(metrics):
        lo, hi = np.percentile(boot[:, j], [2.5, 97.5])
        means = [values[[int(r["sample_idx"]) == k for r in rows], j].mean() for k in range(8)]
        result[name] = dict(mean=float(values[:, j].mean()), lo=float(lo), hi=float(hi),
                            sample_index_means=means, sd_across_eight_sample_index_means=float(np.std(means, ddof=1)),
                            p_value=None)
    task_strict = Counter()
    for r in rows:
        task_strict[r["task_id"]] += int(r["strict"])
    both = [r for r in rows if r["adapter_strict"] != ""]
    confusion = Counter(f"scorer_{r['strict']}_adapter_{r['adapter_strict']}" for r in both)
    return dict(declared_cells=4312, measured_strict_and_reward=4312, train_tasks=539, train_groups=400,
                successes=int(values[:, 0].sum()), active_tasks=sum(0 < k < 8 for k in task_strict.values()),
                fully_solved_tasks=sum(k == 8 for k in task_strict.values()),
                strict_success_count_histogram=dict(sorted(Counter(task_strict.values()).items())),
                status_counts=dict(Counter(r["status"] for r in rows)),
                partial_status_counts=dict(Counter(r["partial_status"] for r in rows)),
                no_lean=sum(not r["lean_sha256"] for r in rows),
                generated_tokens=sum(int(r["generated_tokens"]) for r in rows),
                scorer_adapter_compared=len(both), scorer_adapter_confusion=dict(confusion),
                scorer_adapter_disagreements=sum(r["strict"] != r["adapter_strict"] for r in both),
                metrics=result, FSC="unmeasured: zero judge calls", SCSC="unmeasured: FSC unavailable",
                bootstrap=dict(draws=10000, seed=20261021, unit="D-013 train task group", groups=400,
                               limits="conditional on this policy and its eight saved generations per task; no refitting or new generation"),
                repeatability="One final deterministic score per generation; sample-index variation is generation variation, not repeated-score uncertainty",
                hashes={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (scores, tasks)})


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scores", type=Path, required=True)
    ap.add_argument("--tasks", type=Path, required=True, help="Phase 0 driver's phase0_tasks.csv")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = summarize(args.scores, args.tasks)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
