"""Publish the complete two-condition 1.7B comparison as soon as its validation finishes, independently of 4B."""
import json

from analyze import HERE, RUN, Path, np, read, collect, evaluate


def main():
    ids = (HERE.parent / "expt_v1/results/split/vbv1_validation_task_ids.txt").read_text().splitlines()
    draws = np.random.default_rng(0).integers(0, 135, (10000, 135))
    results, vectors = {}, {}
    for label in ("1p7_control", "1p7_mixed"):
        root = RUN / "validation" / label
        scored = collect(root / "raw.jsonl", root / "scores", label)
        (root / "scored.jsonl").write_text("".join(json.dumps(r) + "\n" for r in scored))
        results[label], vectors[label] = evaluate(label, read(root / "raw.jsonl"), scored, ids)
    baseline_errors = {}
    baseline = Path("/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/ladder/validation")
    name = "v3_E_1p7b_f1p0_g8"
    try:
        results["starting_1p7b"], vectors["starting_1p7b"] = evaluate("starting_1p7b",
            read(baseline / "raw" / f"gen_{name}.jsonl"), read(baseline / "scored" / f"scored_{name}.jsonl"), ids)
        results["starting_1p7b"]["comparison_limit"] = "historical generation/runtime; descriptive baseline"
    except (OSError, ValueError, AssertionError, KeyError) as exc:
        baseline_errors["starting_1p7b"] = str(exc)
    comparisons = {}
    for other in ("1p7_control", "starting_1p7b"):
        if other not in vectors:
            continue
        delta = vectors["1p7_mixed"] - vectors[other]
        ci = np.quantile(delta[draws].mean(axis=1), [0.025, 0.975])
        comparisons["1p7_mixed_minus_" + other] = {"difference": float(delta.mean()), "ci95": ci.tolist(),
            "bootstrap_draws": 10000, "bootstrap_unit": "task, keeping all eight attempts together", "seed": 0,
            "p_value": None, "interpretation": "positive" if ci[0] > 0 else "negative" if ci[1] < 0 else "inconclusive"}
    for label, vector in vectors.items():
        results[label]["success_rate_ci95"] = np.quantile(vector[draws].mean(axis=1), [0.025, 0.975]).tolist()
    report = {"status": "PRIMARY_COMPLETE", "full_experiment_status": "4B pending", "cells": 2160,
        "full_declared_cells": 3240, "systems": results,
        "comparisons": comparisons, "historical_baseline_errors": baseline_errors,
        "test_split_opened": False, "formal_specification_coverage": "not measured"}
    (RUN / "analysis/summary_primary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
