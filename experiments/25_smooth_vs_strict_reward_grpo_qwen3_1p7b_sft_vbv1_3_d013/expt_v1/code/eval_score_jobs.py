"""TLDR: Score the 8 sample job dirs of one validation evaluation with Exp 25's local strict scorer (score_e20.sh) and report strict pass@1, pass@8 and per-job counts; optionally compare with saved per-task csvs.
Use for update-0 validation of the start checkpoint and for later checkpoints (non-Slurm replacement of Exp 20's eval_score.sbatch). Needs python3.12, the grading tree from scoring/setup_local_grading.sh and RL4CV_SRC on PYTHONPATH.
Example: E20_ROOT=$ROOT python3 eval_score_jobs.py --root $ROOT --jobs-root <dir with <name>_s0.._s7> --name eval_u0 --pack <validation pack> --out <dir> --workers 8 [--saved-scores-root <ladder/validation/scores> --saved-prefix sft_1p7B_f1p0_g8]
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def lean_row(job: Path, task: str) -> dict:
    trial = job / task
    receipt = json.loads((trial / "receipt.json").read_text()) if (trial / "receipt.json").exists() else {}
    lean = (trial / "verifier" / "solution.lean").read_text(encoding="utf-8") if (trial / "verifier" / "solution.lean").exists() else ""
    return {"lean": lean, "truncated": receipt.get("finish_reason") == "length"}


def run_job(args, k: int, env: dict) -> tuple[int, int, float]:
    job = Path(args.jobs_root) / f"{args.name}_s{k}"
    out = Path(args.out) / "scores" / f"{args.name}_s{k}"
    if glob.glob(str(out / "*_per_task.csv")):
        return k, 0, 0.0
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    p = subprocess.run(["bash", str(Path(args.root) / "code/score_e20.sh"), str(job), str(args.pack), str(out)], env=env,
                       stdout=open(out / "stdout.log", "w"), stderr=subprocess.STDOUT)
    return k, p.returncode, time.time() - t0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True)
    ap.add_argument("--jobs-root", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--pack", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--samples", type=int, default=8)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--saved-scores-root", default=None)
    ap.add_argument("--saved-prefix", default=None, help="saved score dirs are <root>/<prefix>_s<k>/*_per_task.csv")
    ap.add_argument("--summarize-only", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)
    g = root / "grading"
    os.environ.update({"E20_ROOT": str(root), "E20_GRADING": str(g), "RL4CV_SRC": str(g / "rl4cv/src")})
    sys.path.insert(0, str(g / "rl4cv/src"))
    from rl4cv.rewards import reward_kernel_binary
    from rl4cv.veribench.jobs import read_scorer_per_task, scored_response
    Path(args.out).mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTHONPATH": str(g / "rl4cv/src"), "PATH": f"{g / 'bin'}:{os.environ['PATH']}", "PYTHON": sys.executable}
    t_all = time.time()
    rcs = {}
    if not args.summarize_only:
        with ThreadPoolExecutor(args.workers) as ex:
            for k, rc, secs in ex.map(lambda k: run_job(args, k, env), range(args.samples)):
                rcs[k] = {"rc": rc, "seconds": secs}
                print(f"job s{k} rc={rc} {secs:.0f}s", flush=True)
    wall = time.time() - t_all
    per_sample, task_hits, disagreements = [], {}, []
    for k in range(args.samples):
        job = Path(args.jobs_root) / f"{args.name}_s{k}"
        csvs = glob.glob(str(Path(args.out) / "scores" / f"{args.name}_s{k}" / "*_per_task.csv"))
        if not csvs:
            per_sample.append({"k": k, "scored": 0, "strict": None}); continue
        per = read_scorer_per_task(csvs[0])
        saved = None
        if args.saved_scores_root:
            sc = glob.glob(str(Path(args.saved_scores_root) / f"{args.saved_prefix}_s{k}" / "*_per_task.csv"))
            saved = read_scorer_per_task(sc[0]) if sc else None
        n_ok = 0
        for task, row in per.items():
            r = reward_kernel_binary(scored_response(row, lean_row(job, task))) if row.get("scoring_status") == "scored" else 0.0
            n_ok += int(r)
            task_hits.setdefault(task, []).append(int(r))
            if saved is not None and task in saved:
                s_row = saved[task]
                rs = reward_kernel_binary(scored_response(s_row, lean_row(job, task))) if s_row.get("scoring_status") == "scored" else 0.0
                if rs != r or any(str(row.get(f)) != str(s_row.get(f)) for f in ("scoring_status", "agent_compiles", "kernel_n_theorems", "kernel_n_honest")):
                    disagreements.append({"k": k, "task": task, "local_strict": r, "saved_strict": rs})
        per_sample.append({"k": k, "scored": len(per), "unscored": sum(1 for r in per.values() if r.get("scoring_status") != "scored"), "strict": n_ok})
    cells = sum(p["scored"] for p in per_sample)
    strict = sum(p["strict"] or 0 for p in per_sample)
    summary = {"name": args.name, "cells": cells, "strict_successes": strict, "pass_at_1": strict / cells if cells else None,
               "tasks": len(task_hits), "pass_at_8_tasks": sum(1 for v in task_hits.values() if any(v)), "per_sample": per_sample,
               "disagreements_vs_saved": disagreements if args.saved_scores_root else None, "job_runs": rcs, "scoring_wall_seconds": wall}
    (Path(args.out) / f"summary_{args.name}.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: summary[k] for k in ("name", "cells", "strict_successes", "pass_at_1", "pass_at_8_tasks", "tasks")}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
