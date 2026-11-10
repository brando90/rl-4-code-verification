"""TLDR: Experiment 25 analysis (PROTOCOL sections 1, 6): validation strict pass@1 per run, update-0 baseline, paired group bootstrap of B minus A at update 48 (seeds pooled, 10,000 draws, seed 20261021), per-seed numbers, Goodhart audit (smooth reward, compile rate, theorem counts, truncation), training curves from log.jsonl.
Run on skampere1 after all 12 evaluations are scored: VENV python with numpy; needs the grading tree (RL4CV_SRC) and stats_e20.py beside this file.
Example: python analyze_e25.py --evals /lfs/skampere1/0/brando9/at1788/evals --full /lfs/skampere1/0/brando9/at1788/full --out results/full_run_at1788
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from stats_e20 import paired_group_bootstrap, fmt, DRAWS, SEED  # noqa: E402

RL4CV = "/lfs/skampere1/0/brando9/rl4cv_e25/grading/rl4cv/src"
MANIFEST = "/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/inputs/vbv1_split_manifest.csv"
VAL_IDS = "/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/inputs/vbv1_validation_task_ids.txt"
BASE = "/lfs/skampere1/0/brando9/at1787/eval_u0_fp16"


def load_eval(root: Path, name: str, tasks: list[str], nsamp: int, rewards):
    """Per-cell arrays [task, sample] for one evaluation dir; NaN where the sample was not scored."""
    reward_kernel_binary, scored_response, read_scorer_per_task = rewards
    idx = {t: i for i, t in enumerate(tasks)}
    shape = (len(tasks), nsamp)
    out = {k: np.full(shape, np.nan) for k in ("strict", "compiles", "n_thm", "n_honest", "s_tilde", "truncated")}
    for k in range(nsamp):
        csvs = glob.glob(str(root / "scores" / f"{name}_s{k}" / "*_per_task.csv"))
        if not csvs:
            continue
        job = root / "jobs" / f"{name}_s{k}"
        for task, row in read_scorer_per_task(csvs[0]).items():
            if task not in idx:
                raise SystemExit(f"task {task} not in validation ids")
            i = idx[task]
            tr = job / task
            receipt = json.loads((tr / "receipt.json").read_text()) if (tr / "receipt.json").exists() else {}
            sol = tr / "verifier" / "solution.lean"
            lean = sol.read_text(encoding="utf-8") if sol.exists() else ""
            gen = {"lean": lean, "truncated": receipt.get("finish_reason") == "length"}
            if row.get("scoring_status") == "scored":
                r = float(reward_kernel_binary(scored_response(row, gen)))
            else:
                r = 0.0
            out["strict"][i, k] = r
            out["compiles"][i, k] = float(str(row.get("agent_compiles")).lower() == "true")
            nt = row.get("kernel_n_theorems")
            out["n_thm"][i, k] = float(nt) if nt not in (None, "", "nan") else float(row.get("agent_n_thm") or 0)
            nh = row.get("kernel_n_honest")
            out["n_honest"][i, k] = float(nh) if nh not in (None, "", "nan") else 0.0
            st = row.get("S_tilde")
            out["s_tilde"][i, k] = float(st) if st not in (None, "", "nan") else 0.0
            out["truncated"][i, k] = float(gen["truncated"])
    return out


def task_mean(a):  # per-task mean over scored samples
    return np.nanmean(a, axis=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evals", required=True)
    ap.add_argument("--full", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sys.path.insert(0, RL4CV)
    from rl4cv.rewards import reward_kernel_binary
    from rl4cv.veribench.jobs import read_scorer_per_task, scored_response
    rewards = (reward_kernel_binary, scored_response, read_scorer_per_task)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tasks = sorted(Path(VAL_IDS).read_text().split())
    grp = {}
    with open(MANIFEST, newline="") as fh:
        for r in csv.DictReader(fh):
            if r["split"] == "validation":
                grp[r["task_id"]] = r["group_id"]
    groups = np.array([grp[t] for t in tasks])
    ev = Path(a.evals)
    R, runs = {}, {}
    base = load_eval(Path(BASE), "eval_u0_fp16", tasks, 8, rewards)
    R["u0"] = base
    for arm in "AB":
        for s in (0, 1):
            for u, ns in ((16, 8), (32, 8), (48, 32)):
                nm = f"{arm}_s{s}_u{u:03d}"
                R[nm] = load_eval(ev / nm, f"eval_{nm}", tasks, ns, rewards)

    def summ(d):
        n = int(np.sum(~np.isnan(d["strict"])))
        return {"cells": n, "strict_successes": int(np.nansum(d["strict"])), "pass_at_1": float(np.nanmean(d["strict"])),
                "compile_rate": float(np.nanmean(d["compiles"])), "mean_theorems_stated": float(np.nanmean(d["n_thm"])),
                "mean_theorems_honest": float(np.nanmean(d["n_honest"])), "mean_S_tilde": float(np.nanmean(d["s_tilde"])),
                "truncated_rate": float(np.nanmean(d["truncated"])),
                "mean_theorems_given_compiles": float(np.nanmean(np.where(d["compiles"] == 1, d["n_thm"], np.nan))),
                "strict_given_not_truncated": float(np.nanmean(np.where(d["truncated"] == 0, d["strict"], np.nan))),
                "tasks_pass_any": int(np.sum(np.nansum(d["strict"], axis=1) > 0)),
                "samples_scored": int(np.sum(~np.all(np.isnan(d["strict"]), axis=0)))}
    runs = {k: summ(v) for k, v in R.items()}

    res = {"draws": DRAWS, "seed": SEED, "groups": int(np.unique(groups).size), "tasks": len(tasks), "runs": runs}
    # primary: update 48, seeds pooled, per-task mean over seeds of per-task pass rate
    def pooled(arm, u, key="strict"):
        return np.mean([task_mean(R[f"{arm}_s{s}_u{u:03d}"][key]) for s in (0, 1)], axis=0)

    prim = {}
    for u in (16, 32, 48):
        pa, pb = pooled("A", u), pooled("B", u)
        d = pb - pa
        prim[f"u{u}"] = {"B_minus_A": paired_group_bootstrap(lambda i, d=d: d[i].mean() * 100, groups),
                         "A": paired_group_bootstrap(lambda i, p=pa: p[i].mean() * 100, groups),
                         "B": paired_group_bootstrap(lambda i, p=pb: p[i].mean() * 100, groups)}
    p0 = task_mean(base["strict"])
    for arm in "AB":
        for u in (16, 32, 48):
            p = pooled(arm, u)
            prim[f"{arm}_u{u}_minus_u0"] = paired_group_bootstrap(lambda i, p=p: (p[i] - p0[i]).mean() * 100, groups)
    res["bootstrap_points"] = prim
    # secondary Goodhart metrics at update 48, B minus A, same bootstrap
    good = {}
    for key in ("compiles", "n_thm", "n_honest", "s_tilde", "truncated"):
        d = pooled("B", 48, key) - pooled("A", 48, key)
        good[key] = paired_group_bootstrap(lambda i, d=d: d[i].mean(), groups)
        for arm in "AB":
            p = pooled(arm, 48, key)
            good[f"{arm}_{key}_minus_u0"] = paired_group_bootstrap(lambda i, p=p, b=task_mean(base[key]): (p[i] - b[i]).mean(), groups)
    res["goodhart_u48"] = good
    # per-seed pairs at 48 (points)
    res["per_seed_u48_points"] = {f"{arm}_s{s}": runs[f"{arm}_s{s}_u048"]["pass_at_1"] * 100 for arm in "AB" for s in (0, 1)}
    # strict pass@1 of seed-paired differences (A_s0 vs B_s0, A_s1 vs B_s1)
    res["per_seed_pair_diff_u48_points"] = {f"s{s}": (runs[f"B_s{s}_u048"]["pass_at_1"] - runs[f"A_s{s}_u048"]["pass_at_1"]) * 100 for s in (0, 1)}
    # training curves from log.jsonl (last entry per update)
    curves = {}
    for arm in "AB":
        for s in (0, 1):
            f = Path(a.full) / f"{arm}_s{s}_lr5e-6" / f"{arm}_s{s}" / "log.jsonl"
            by = {}
            for line in f.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    by[r["update"]] = r
            ups = sorted(by)
            curves[f"{arm}_s{s}"] = {
                "updates": ups,
                "mean_strict": [by[u]["mean_strict"] for u in ups],
                "mean_smooth": [by[u].get("mean_smooth") for u in ups],
                "truncated": [by[u].get("truncated") for u in ups],
                "active_fraction": [by[u].get("active_fraction") for u in ups],
                "gate_share_max": max(by[u].get("train_gate_share", 0) for u in ups),
                "nonfinite": sum(by[u].get("train_nonfinite_sequences", 0) for u in ups),
                "gpu_seconds_last": by[ups[-1]].get("generated_rollouts_total"),
            }
    res["training_curves"] = curves
    (out / "analysis_e25.json").write_text(json.dumps(res, indent=1) + "\n")
    # per-task table for pooled u48
    with open(out / "per_task_u48.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["task", "group", "u0_p", "A_p", "B_p", "B_minus_A"])
        pa, pb = pooled("A", 48), pooled("B", 48)
        for i, t in enumerate(tasks):
            w.writerow([t, groups[i], f"{p0[i]:.4f}", f"{pa[i]:.4f}", f"{pb[i]:.4f}", f"{pb[i]-pa[i]:.4f}"])
    print("B-A u48 (points):", fmt(prim["u48"]["B_minus_A"]))
    for k, v in runs.items():
        print(k, v["strict_successes"], v["cells"], round(v["pass_at_1"] * 100, 2), "compile", round(v["compile_rate"], 3), "thm", round(v["mean_theorems_stated"], 2), "thm|compiles", round(v["mean_theorems_given_compiles"], 2), "strict|not trunc", round(v["strict_given_not_truncated"], 3), "trunc", round(v["truncated_rate"], 3))


if __name__ == "__main__":
    main()
