"""Reconcile every validation cell, apply the inherited non-vacuity gate, and compare the two 1.7B conditions."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = Path(os.environ["TINY_RUN_ROOT"])
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE.parent / "expt_v1/scripts"))
from rl4cv.rewards import ScoredResponse, reward_kernel_binary
from rl4cv.veribench.collect import collect
from score_teacher_files import vacuity


def read(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def evaluate(label, raw, scored, ids):
    want = {(tid, k) for tid in ids for k in range(8)}
    assert len(raw) == len(scored) == len(want) == 1080
    assert len({(r["task_id"], r["sample_idx"]) for r in raw}) == len(raw)
    assert len({(r["task_id"], r["sample_idx"]) for r in scored}) == len(scored)
    raw_index = {(r["task_id"], r["sample_idx"]): r for r in raw}
    score_index = {(r["task_id"], r["sample_idx"]): r for r in scored}
    assert set(raw_index) == set(score_index) == want
    cells = []
    for tid in ids:
        for k in range(8):
            r, s = raw_index[(tid, k)], score_index[(tid, k)]
            assert s["status"] == "scored", f"unknown score: {label}/{tid}/{k}"
            lean = r.get("lean") or ""
            vac = vacuity(lean) if lean.strip() else {"n_vacuous": 0, "unparseable": []}
            response = ScoredResponse(extracted=bool(lean.strip()), compiles=bool(s.get("compiles")),
                n_examples=int(s.get("n_examples") or 0), n_theorems_stated=int(s.get("n_theorems_stated") or 0),
                n_theorems_proved=int(s.get("n_theorems_proved") or 0),
                vacuous_theorems=vac["n_vacuous"], truncated=bool(r.get("truncated")))
            binary = 0.0 if vac["unparseable"] else reward_kernel_binary(response)
            cells.append({"system": label, "task_id": tid, "sample_idx": k, "binary_success": binary,
                "extracted": bool(lean.strip()), "compiles": response.compiles,
                "IC_tests": s["IC_tests"], "IC_proofs": s["IC_proofs"],
                "vacuous": vac["n_vacuous"], "unparseable": bool(vac["unparseable"]),
                "capped": bool(r.get("truncated")), "generated_tokens": r["generated_tokens"]})
    values = np.array([c["binary_success"] for c in cells]).reshape(135, 8)
    counts = values.sum(axis=1).astype(int)
    per_task = [{"task_id": tid, "successes": int(n), "attempts": 8, "success_rate": float(n / 8)}
        for tid, n in zip(ids, counts, strict=True)]
    result = {"declared_cells": 1080, "scored_cells": 1080, "successes": int(counts.sum()),
        "success_rate": float(values.mean()), "pass_at_8_tasks": int((counts > 0).sum()),
        "mixed_tasks_1_to_7": int(((counts > 0) & (counts < 8)).sum()),
        "target_tasks_2_to_6": int(((counts >= 2) & (counts <= 6)).sum()),
        "extracted": sum(c["extracted"] for c in cells), "compiles": sum(c["compiles"] for c in cells),
        "capped": sum(c["capped"] for c in cells),
        "mean_generated_tokens": float(np.mean([c["generated_tokens"] for c in cells])),
        "mean_IC_tests": float(np.mean([c["IC_tests"] for c in cells])),
        "mean_IC_proofs": float(np.mean([c["IC_proofs"] for c in cells])),
        "source_model_paths": sorted({r["model"] for r in raw})}
    out = RUN / "analysis"
    out.mkdir(exist_ok=True)
    for name, records in (("cells", cells), ("tasks", per_task)):
        with (out / f"{label}_{name}.csv").open("w") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    return result, values.mean(axis=1)


def main():
    ids = (HERE.parent / "expt_v1/results/split/vbv1_validation_task_ids.txt").read_text().splitlines()
    draws = np.random.default_rng(0).integers(0, 135, (10000, 135))
    results, vectors, baseline_errors = {}, {}, {}
    for label in ("1p7_control", "1p7_mixed", "4b_mixed"):
        root = RUN / "validation" / label
        scored = collect(root / "raw.jsonl", root / "scores", label)
        (root / "scored.jsonl").write_text("".join(json.dumps(r) + "\n" for r in scored))
        results[label], vectors[label] = evaluate(label, read(root / "raw.jsonl"), scored, ids)
    baseline_root = Path("/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/ladder/validation")
    for short in ("1p7b", "4b"):
        label = "starting_" + short
        name = f"v3_E_{short}_f1p0_g8"
        try:
            results[label], vectors[label] = evaluate(label, read(baseline_root / "raw" / f"gen_{name}.jsonl"),
                read(baseline_root / "scored" / f"scored_{name}.jsonl"), ids)
            results[label]["comparison_limit"] = "historical generation/runtime; descriptive baseline, not a new replay control"
        except (OSError, ValueError, AssertionError, KeyError) as exc:
            baseline_errors[label] = str(exc)
    comparisons = {}
    for a, b in (("1p7_mixed", "1p7_control"), ("1p7_mixed", "starting_1p7b"), ("4b_mixed", "starting_4b")):
        if a not in vectors or b not in vectors:
            continue
        delta = vectors[a] - vectors[b]
        ci = np.quantile(delta[draws].mean(axis=1), [0.025, 0.975])
        comparisons[a + "_minus_" + b] = {"difference": float(delta.mean()), "ci95": ci.tolist(),
            "bootstrap_draws": 10000, "bootstrap_unit": "task, keeping all eight attempts together", "seed": 0,
            "p_value": None, "interpretation": "positive" if ci[0] > 0 else "negative" if ci[1] < 0 else "inconclusive"}
    report = {"status": "COMPLETE", "systems": results, "comparisons": comparisons,
        "historical_baseline_errors": baseline_errors, "test_split_opened": False,
        "provider_spend_usd": 0, "formal_specification_coverage": "not measured; no aggregate requiring a judge reported"}
    for label, vector in vectors.items():
        results[label]["success_rate_ci95"] = np.quantile(vector[draws].mean(axis=1), [0.025, 0.975]).tolist()
    (RUN / "analysis/summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
