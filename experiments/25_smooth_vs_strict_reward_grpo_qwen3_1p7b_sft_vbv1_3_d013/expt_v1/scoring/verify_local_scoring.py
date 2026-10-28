"""TLDR: Check Exp 25's local scoring wrapper against saved scores: re-score N saved rollouts (strict via code/score_e20.sh and smooth via code/partial_credit_e20.py, exactly as train_e25.py calls them) and compare with the saved per-task rows.
Use after setup_local_grading.sh, on skampere1 or mercury1/2. Needs only python3.12 (scorer is stdlib-only) and a grading tree.
Example: python3 verify_local_scoring.py --root /lfs/skampere1/0/brando9/rl4cv_e25 --saved-job /lfs/skampere1/0/brando9/rl4cv_e08/jobs/opus55_s1_s0 --saved-scores /lfs/skampere1/0/brando9/rl4cv_e08/scores/opus55_s1_s0/scsc_opus55_s1_s0_opus55_s1_s0_per_task.csv --pack /lfs/skampere1/0/brando9/rl4cv_e08/pack_views/teachers/opus55_s1 --n 48 --workers 8 --out /lfs/skampere1/0/brando9/at1786/verify_skampere1
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def run_chunk(root: Path, job: Path, pack: Path, out: Path, mode: str, env: dict) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    if mode == "strict":
        cmd = ["bash", str(root / "code/score_e20.sh"), str(job), str(pack), str(out)]
    else:
        cmd = [sys.executable, str(root / "code/partial_credit_e20.py"), "--job-dir", str(job),
               "--out", str(out / f"partial_{job.name}.json"), "--evidence-root", str(out / "compiler_diagnostics")]
    with open(out / "stdout.log", "w") as fh:
        rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT, env=env)
    return {"mode": mode, "job": job.name, "rc": rc, "seconds": time.monotonic() - t0, "out": str(out)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--saved-job", type=Path, required=True)
    ap.add_argument("--saved-scores", type=Path, required=True)
    ap.add_argument("--pack", type=Path, required=True)
    ap.add_argument("--n", type=int, default=48)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=25)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--no-smooth", action="store_true")
    a = ap.parse_args()
    root, G = a.root.resolve(), a.root.resolve() / "grading"
    saved = {r["task"]: r for r in csv.DictReader(open(a.saved_scores, newline="", encoding="utf-8"))}
    ok = [t for t, r in saved.items() if r["scoring_status"] == "scored" and r["IC_ap"] == "1.0" and r["IC_pp"] == "1.0"]
    half_ok = [t for t, r in saved.items() if r["scoring_status"] == "scored" and r["agent_compiles"] == "True" and t not in ok]
    bad = [t for t, r in saved.items() if r["scoring_status"] == "scored" and r["agent_compiles"] != "True"]
    rng = random.Random(a.seed)
    for L in (ok, half_ok, bad):
        L.sort(); rng.shuffle(L)
    rest = a.n - len(half_ok[: a.n // 4])
    pick = half_ok[: a.n // 4] + ok[: rest // 2] + bad[: rest - rest // 2]
    print(f"pool: pass={len(ok)} compiles_not_full={len(half_ok)} compile_fail={len(bad)}; picked {len(pick)}", flush=True)
    a.out.mkdir(parents=True, exist_ok=True)
    # one job dir per chunk (one sample index each), written by the trainer's own materialize_jobs from the saved Lean sources
    sys.path.insert(0, str(G / "rl4cv/src"))
    from rl4cv.veribench.jobs import materialize_jobs  # noqa: E402
    chunks = [pick[i::a.workers] for i in range(a.workers)]
    jr = a.out / "jobs"
    if jr.exists():
        shutil.rmtree(jr)
    rows_in = [{"task_id": t, "sample_idx": i, "lean": (a.saved_job / t / "verifier/solution.lean").read_bytes().decode("utf-8"),
                "finish_reason": "stop", "measured": True, "extraction": "file_blocks"} for i, ch in enumerate(chunks) for t in ch]
    jobs = [jobs_ for _, jobs_ in sorted(materialize_jobs(rows_in, jr, "v").items())]
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTHONPATH": str(G / "rl4cv/src"), "PATH": f"{G / 'bin'}:{os.environ['PATH']}",
           "RL4CV_SRC": str(G / "rl4cv/src"), "E20_GRADING": str(G), "PYTHON": sys.executable}
    modes = ["strict"] + ([] if a.no_smooth else ["smooth"])
    futs, t_all = [], time.monotonic()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for mode in modes:
            for j in jobs:
                futs.append(ex.submit(run_chunk, root, j, a.pack, a.out / "scores" / mode / j.name, mode, env))
        runs = [f.result() for f in futs]
    wall = time.monotonic() - t_all
    from rl4cv.rewards import reward_kernel_binary  # noqa: E402
    from rl4cv.veribench.jobs import scored_response  # noqa: E402
    rows, dis = [], []
    for j in jobs:
        sd = a.out / "scores/strict" / j.name
        new = {}
        for f in sd.glob("*_per_task.csv"):
            new = {r["task"]: r for r in csv.DictReader(open(f, newline="", encoding="utf-8"))}
        part = {}
        pf = a.out / "scores/smooth" / j.name / f"partial_{j.name}.json"
        if pf.exists():
            part = {r["task_id"]: r for r in json.load(open(pf))["records"]}
        for t in sorted(p.name for p in j.iterdir()):
            o, n, p = saved[t], new.get(t), part.get(t)
            gen = {"lean": True, "truncated": False}
            so = reward_kernel_binary(scored_response(o, gen))
            sn = reward_kernel_binary(scored_response(n, gen)) if n and n["scoring_status"] == "scored" else None
            fields = ["scoring_status", "agent_compiles", "IC_ap", "IC_pp", "kernel_n_theorems", "kernel_n_honest", "kernel_probe_ok", "submission_status"]
            same_fields = bool(n) and all(o.get(f) == n.get(f) for f in fields)
            rec = {"task": t, "saved_strict": so, "new_strict": sn, "strict_agree": sn == so, "fields_identical": same_fields,
                   "smooth_status": p and p["status"], "smooth": p and p.get("factored_reward"), "adapter_strict": p and p.get("strict"),
                   "parse_failure_zero_credit": bool(p) and p.get("status") == "unresolved_measurement" and "malformed source" in str(p.get("error", "")),
                   "adapter_strict_agrees": bool(p) and ((p.get("status") == "measured" and float(p["strict"]) == so)
                                                         or (p.get("status") == "unresolved_measurement" and "malformed source" in str(p.get("error", "")) and so == 0.0)),
                   "smooth_seconds": p and p.get("wall_seconds"), "smooth_error": p and p.get("error")}
            rows.append(rec)
            if not (rec["strict_agree"] and rec["fields_identical"]) or (p and not rec["adapter_strict_agrees"]):
                dis.append({**rec, "saved_row": {f: o.get(f) for f in fields}, "new_row": n and {f: n.get(f) for f in fields}})
    summ = {"root": str(root), "host": os.uname().nodename, "n": len(rows), "wall_seconds_all": round(wall, 1), "workers": a.workers,
            "strict_agree": sum(r["strict_agree"] for r in rows), "fields_identical": sum(r["fields_identical"] for r in rows),
            "saved_strict_pass": sum(1 for r in rows if r["saved_strict"] == 1.0),
            "smooth_measured": sum(1 for r in rows if r["smooth_status"] == "measured"),
            "adapter_strict_agrees": sum(r["adapter_strict_agrees"] for r in rows),
            "parse_failure_zero_credit": sum(r["parse_failure_zero_credit"] for r in rows),
            "run_exit_codes": {f"{r['mode']}:{r['job']}": r["rc"] for r in runs},
            "strict_chunk_seconds": {r["job"]: round(r["seconds"], 1) for r in runs if r["mode"] == "strict"},
            "smooth_chunk_seconds": {r["job"]: round(r["seconds"], 1) for r in runs if r["mode"] == "smooth"},
            "mean_trials_per_chunk": len(rows) / max(1, len(jobs)), "disagreements": dis}
    json.dump({"summary": summ, "rows": rows}, open(a.out / "verify_result.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k != "disagreements"}, indent=1))
    print(f"disagreements: {len(dis)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
