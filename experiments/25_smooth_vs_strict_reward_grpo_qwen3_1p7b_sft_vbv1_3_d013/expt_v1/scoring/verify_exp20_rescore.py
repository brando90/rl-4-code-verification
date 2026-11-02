"""TLDR: Re-score saved Exp 20 phase-0 rollouts (job dirs copied from Sherlock) with the Exp 25 local scorer and compare with the saved Exp 20 strict, compiles and smooth (factored_reward) values.
Use after setup_local_grading.sh, on skampere1 or mercury1/2, with a subset made from Sherlock's e20/phase0 (jobs/<job>/<task>/verifier/solution.lean, train_pack, saved_cells_subset.csv = rows of phase0_cells_e20.csv plus job, stratum). Needs python3.12 and a grading tree.
Example: python3.12 verify_exp20_rescore.py --root /lfs/skampere1/0/brando9/rl4cv_e25 --data /lfs/skampere1/0/brando9/at1799 --workers 24 --out /lfs/skampere1/0/brando9/at1799/out
"""
from __future__ import annotations

import argparse, csv, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_local_scoring import run_chunk  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=24)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    root, G = a.root.resolve(), a.root.resolve() / "grading"
    saved = list(csv.DictReader(open(a.data / "saved_cells_subset.csv", newline="", encoding="utf-8")))
    jobs = sorted({r["job"] for r in saved})
    pack = a.data / "pack"
    sys.path.insert(0, str(G / "rl4cv/src"))
    from rl4cv.rewards import reward_kernel_binary  # noqa: E402
    from rl4cv.veribench.jobs import scored_response  # noqa: E402
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTHONPATH": str(G / "rl4cv/src"), "PATH": f"{G / 'bin'}:{os.environ['PATH']}",
           "RL4CV_SRC": str(G / "rl4cv/src"), "E20_GRADING": str(G), "PYTHON": sys.executable}
    a.out.mkdir(parents=True, exist_ok=True)
    t_all, futs = time.monotonic(), []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for mode in ("strict", "smooth"):
            for j in jobs:
                futs.append(ex.submit(run_chunk, root, a.data / "jobs" / j, pack, a.out / "scores" / mode / j, mode, env))
        runs = [f.result() for f in futs]
    wall = time.monotonic() - t_all
    rows, dis = [], []
    for s in saved:
        j, t = s["job"], s["task_id"]
        new = {}
        for f in (a.out / "scores/strict" / j).glob("*_per_task.csv"):
            new = {r["task"]: r for r in csv.DictReader(open(f, newline="", encoding="utf-8"))}
        n = new.get(t)
        pf = a.out / "scores/smooth" / j / f"partial_{j}.json"
        p = {r["task_id"]: r for r in json.load(open(pf))["records"]}.get(t) if pf.exists() else None
        gen = {"lean": True, "truncated": False}
        new_strict = reward_kernel_binary(scored_response(n, gen)) if n and n["scoring_status"] == "scored" else None
        new_compiles = (n["agent_compiles"] == "True") if n and n["scoring_status"] == "scored" else None
        sf = float(s["factored_reward"]) if s["factored_reward"] not in ("", None) else None
        nf = float(p["factored_reward"]) if p and p.get("factored_reward") is not None else None
        rec = {"job": j, "task": t, "sample_idx": s["sample_idx"], "stratum": s["stratum"], "saved_partial_status": s["partial_status"],
               "saved_strict": float(s["strict"]), "new_strict": new_strict, "strict_agree": new_strict == float(s["strict"]),
               "saved_compiles": s["compiles"] == "1", "new_compiles": new_compiles, "compiles_agree": new_compiles == (s["compiles"] == "1"),
               "new_scoring_status": n and n["scoring_status"], "saved_smooth": sf, "new_smooth_status": p and p["status"], "new_smooth": nf,
               "smooth_agree": (sf is not None and nf is not None and abs(sf - nf) < 1e-9) or (sf == nf),
               "smooth_diff": (abs(sf - nf) if sf is not None and nf is not None else None), "smooth_error": p and p.get("error")}
        rows.append(rec)
        if not (rec["strict_agree"] and rec["compiles_agree"] and rec["smooth_agree"]):
            dis.append(rec)
    by = {}
    for r in rows:
        d = by.setdefault(r["stratum"], {"n": 0, "strict_agree": 0, "smooth_agree": 0})
        d["n"] += 1; d["strict_agree"] += r["strict_agree"]; d["smooth_agree"] += r["smooth_agree"]
    summ = {"host": os.uname().nodename, "n": len(rows), "jobs": len(jobs), "wall_seconds_all": round(wall, 1), "workers": a.workers,
            "strict_agree": sum(r["strict_agree"] for r in rows), "compiles_agree": sum(r["compiles_agree"] for r in rows),
            "smooth_agree": sum(r["smooth_agree"] for r in rows), "by_stratum": by,
            "run_exit_codes": {f"{r['mode']}:{r['job']}": r["rc"] for r in runs}, "disagreements": dis}
    json.dump({"summary": summ, "rows": rows}, open(a.out / "verify_exp20_result.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k != "disagreements"}, indent=1))
    print(f"disagreements: {len(dis)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
