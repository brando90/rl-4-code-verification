# TLDR: Measures, on experiment 08's existing validation cells (zero model calls), whether VeriBench's kernel-checked factors carry any reward signal beyond the strict pass/fail outcome.
"""Factor-redundancy check for experiment 13's design (zero model calls).

For each experiment 08 validation-ladder system (135 tasks x 8 samples), this reports:
- strict: mean kernel_binary (the strict verified-artifact outcome);
- compiled_not_strict: samples with IC_tests = 1 but kernel_binary = 0;
- binary_mixed_tasks: tasks whose 8 strict outcomes are not all equal (GRPO signal under the strict reward);
- dense_only_tasks: tasks whose strict outcomes are all equal but whose kernel smooth score
  sqrt(IC_tests * IC_proofs) varies (extra GRPO signal a factored kernel reward would add);
- failure composition: no extracted Lean, output capped, extracted but not compiling.

Usage (from the repository root): python experiments/13_.../design_evidence/factor_redundancy_e08.py
"""
import collections
import csv
import glob
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 3))
LADDER = os.path.join(
    ROOT,
    "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/ladder",
)
OUT = os.path.join(os.path.dirname(__file__), "factor_redundancy_e08.json")


def wilson(k: int, n: int, z: float = 1.96) -> list:
    """Wilson 95% interval for k successes out of n."""
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 4), round((c + h) / d, 4)]


def summarize(path: str) -> dict:
    """Summarize one system's known validation cells."""
    rows = [r for r in csv.DictReader(open(path)) if r["known"] == "True"]
    groups = collections.defaultdict(list)
    for r in rows:
        strict = float(r["kernel_binary"])
        ic_tests, ic_proofs = float(r["IC_tests"]), float(r["IC_proofs"])
        groups[r["task_id"]].append((strict, round(math.sqrt(ic_tests * ic_proofs), 9)))
    n_tasks = len(groups)
    binary_mixed = sum(1 for g in groups.values() if len({s for s, _ in g}) > 1)
    dense_only = sum(
        1 for g in groups.values() if len({s for s, _ in g}) == 1 and len({d for _, d in g}) > 1
    )
    return {
        "cells_known": len(rows),
        "tasks": n_tasks,
        "strict_mean": round(sum(float(r["kernel_binary"]) for r in rows) / len(rows), 4),
        "compiled_not_strict": sum(
            1 for r in rows if float(r["IC_tests"]) == 1 and float(r["kernel_binary"]) == 0
        ),
        "binary_mixed_tasks": binary_mixed,
        "binary_mixed_share_wilson95": wilson(binary_mixed, n_tasks),
        "dense_only_tasks": dense_only,
        "dense_only_share_wilson95": wilson(dense_only, n_tasks),
        "no_extraction": sum(1 for r in rows if r["extracted"] != "True"),
        "capped": sum(1 for r in rows if r["capped"] == "True"),
        "extracted_not_compiling": sum(
            1 for r in rows if r["extracted"] == "True" and float(r["IC_tests"]) == 0
        ),
    }


def main() -> int:
    paths = sorted(glob.glob(os.path.join(LADDER, "*_validation_cells.csv")))
    result = {}
    for p in paths:
        name = os.path.basename(p).replace("_validation_cells.csv", "")
        rows = [r for r in csv.DictReader(open(p)) if r["known"] == "True"]
        if not rows:
            result[name] = {"status": "no known cells (system incomplete)"}
            continue
        result[name] = summarize(p)
    json.dump(result, open(OUT, "w"), indent=2, sort_keys=True)
    hdr = f"{'system':16s} {'cells':>5s} {'strict':>6s} {'cmp!strict':>10s} {'binMix':>6s} {'denseOnly':>9s} {'noExtr':>6s} {'capped':>6s} {'extr!cmp':>8s}"
    print(hdr)
    for name, s in result.items():
        if "status" in s:
            print(f"{name:16s} {s['status']}")
            continue
        print(
            f"{name:16s} {s['cells_known']:5d} {s['strict_mean']:6.3f} {s['compiled_not_strict']:10d} "
            f"{s['binary_mixed_tasks']:6d} {s['dense_only_tasks']:9d} {s['no_extraction']:6d} "
            f"{s['capped']:6d} {s['extracted_not_compiling']:8d}"
        )
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
