"""Audit existing validation signal and inventory cached train-only expansion candidates."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
V1 = HERE.parent / "expt_v1" / "results"
MBPP = REPO / "experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3/results/sft_manifest.json"
SIZES = ("1p7B", "4B", "8B", "14B")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def validate_rows(rows, ids):
    """Reject missing/extra/duplicate tasks and incomplete eight-sample groups."""
    by_id = {r["task_id"]: r for r in rows}
    if len(by_id) != len(rows) or set(by_id) != set(ids):
        raise ValueError("Validation task manifest mismatch or duplicate task")
    for row in rows:
        if int(row["samples_known"]) != 8:
            raise ValueError("Incomplete group; unknown cells cannot count as failures")
        for key in ("k_kernel_binary", "k_ic_tests", "k_extracted", "k_capped"):
            if not 0 <= int(row[key]) <= 8:
                raise ValueError(f"Invalid {key}")
        k = int(row["k_kernel_binary"])
        if int(row["mixed"]) != int(0 < k < 8):
            raise ValueError("Mixed-group count disagrees with success count")
    return [by_id[tid] for tid in sorted(ids)]


def estimate(values, indices):
    values = np.asarray(values, dtype=float)
    low, high = np.quantile(values[indices].mean(axis=1), [0.025, 0.975])
    return {"mean": float(values.mean()), "ci95": [float(low), float(high)], "p_value": None}


def build(out):
    sources = {}

    def track(path):
        sources[str(path.relative_to(REPO))] = sha(path)
        return path

    split = read_csv(track(V1 / "split/vbv1_split_manifest.csv"))
    validation = {r["task_id"] for r in split if r["split"] == "validation"}
    train = {r["task_id"] for r in split if r["split"] == "train"}
    family = {r["task_id"]: r["family"] for r in split}
    if len(validation) != 135 or len(train) != 539:
        raise ValueError("Unexpected D-013 split")
    indices = np.random.default_rng(0).integers(0, 135, size=(10000, 135))
    systems, vectors = {}, {}
    for size in SIZES:
        rows = validate_rows(read_csv(track(V1 / f"ladder/sft_{size}_f1p0_validation_per_task.csv")), validation)
        k = np.array([int(r["k_kernel_binary"]) for r in rows])
        extracted = sum(int(r["k_extracted"]) for r in rows)
        capped = sum(int(r["k_capped"]) for r in rows)
        mixed = int(((k > 0) & (k < 8)).sum())
        vectors[size] = k / 8
        systems[size] = {
            "tasks": 135, "cells_known": 1080, "cells_declared": 1080,
            "success_count_histogram_0_to_8": np.bincount(k, minlength=9).tolist(),
            "successes": int(k.sum()), "pass_rate": estimate(k / 8, indices),
            "mixed_tasks": mixed, "mixed_share": estimate((k > 0) & (k < 8), indices),
            "tasks_with_2_to_6_successes": int(((k >= 2) & (k <= 6)).sum()),
            "observed_25_to_75_percent_share": estimate((k >= 2) & (k <= 6), indices),
            "extracted": extracted, "capped": capped,
            "additional_extractions_to_gate": max(0, 972 - extracted),
            "cap_reduction_to_gate": max(0, capped - 108),
            "historical_gate_pass": extracted >= 972 and capped <= 108 and mixed >= 7,
        }
    stats = json.loads(track(V1 / "sft_set_stats.json").read_text())
    selected = read_csv(track(V1 / "sft_set_manifest.csv"))
    if sha(V1 / "sft_set_manifest.csv") != stats["manifest_sha256"]:
        raise ValueError("Selected corpus manifest hash mismatch")
    if any(r["task_id"] not in train for r in selected):
        raise ValueError("Selected corpus contains a non-train task")
    scored = [json.loads(line) for line in track(V1 / "scored_cells.jsonl").read_text().splitlines() if line.strip()]
    by_cell = {}
    for row in scored:
        if row.get("phase", "main") != "main":
            continue
        cid = f"{row['teacher']}/{row['r']}/{row['task_id']}"
        if cid in by_cell:
            raise ValueError("Duplicate scored teacher cell")
        by_cell[cid] = row
    screen = json.loads(track(V1 / "generated_lean_screen.json").read_text())
    excluded_screen = set(screen["excluded_cells"])
    candidates = []
    for exclusion in stats["excluded"]:
        if exclusion["reason"] != "per_teacher_cap":
            continue
        cid = exclusion["cell"]
        row = by_cell[cid]
        if row["task_id"] not in train or row["kernel_binary"] != 1 or row["extraction_consistent"] is not True or cid in excluded_screen:
            raise ValueError(f"Candidate is not eligible train evidence: {cid}")
        candidates.append({"cell_id": cid, "task_id": row["task_id"], "family": family[row["task_id"]],
                           "teacher": row["teacher"], "sample": row["r"], "lean_sha256": row["lean_sha256"],
                           "response_sha256": row["response_text_sha256"], "response_path": row["response_path"],
                           "status": "candidate_needs_joint_normalized_dedup_and_render_recheck"})
    if len(candidates) != stats["exclusions_by_reason"]["per_teacher_cap"]:
        raise ValueError("Candidate count mismatch")
    mbpp = json.loads(track(MBPP).read_text())
    if len(mbpp["pairs"]) != mbpp["n_pairs"] or len({r["task_id"] for r in mbpp["pairs"]}) != mbpp["n_distinct_tasks"]:
        raise ValueError("MBPP manifest count mismatch")
    schedule = json.loads(track(V1 / "sft_schedule.json").read_text())
    selected_tasks = {r["task_id"] for r in selected}
    candidate_tasks = {r["task_id"] for r in candidates}
    payload = {
        "status": "existing_data_audit_only_no_new_training", "split": "VeriBench V1 validation",
        "method": "Post hoc; 10000 paired task bootstrap draws, seed 0, all eight samples together; percentile 95% intervals; single training seed; no hypothesis test.",
        "thresholds": {"historical": "extraction >=972/1080; capped <=108/1080; mixed >=7/135", "meeting_diagnostic": "2..6 successes out of 8; empirical task difficulty, not SCSC or a new pass gate"},
        "systems": systems,
        "paired_14B_minus_8B_pass_rate": estimate(vectors["14B"] - vectors["8B"], indices),
        "training": {"examples": len(selected), "tasks": len(selected_tasks), "loss_tokens": schedule["assistant_tokens_total"],
                     "cap_excluded_candidates": len(candidates), "candidate_tasks": len(candidate_tasks),
                     "new_source_tasks_from_cap_candidates": len(candidate_tasks - selected_tasks),
                     "candidate_families": dict(sorted(Counter(r["family"] for r in candidates).items())),
                     "candidate_raw_lean_hashes": len({r["lean_sha256"] for r in candidates}),
                     "mbpp_pairs_before_conversion": mbpp["n_pairs"], "mbpp_tasks_before_joint_screen": mbpp["n_distinct_tasks"],
                     "admitted_expanded_examples": None},
        "source_sha256": sources,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "continuation_audit.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    with (out / "cached_train_candidates.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(candidates[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(candidates)
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "results")
    args = parser.parse_args()
    result = build(args.out)
    print(json.dumps({"systems": result["systems"], "training": result["training"]}, indent=2))
