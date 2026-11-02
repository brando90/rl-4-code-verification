"""TLDR: Check partial_credit_fixedpath.py reproduces saved Exp 20 smooth values for given jobs of the AT-1799 sample.
Use on skampere1 after copying partial_credit_fixedpath.py into ROOT/code. Example: python3.12 verify_fixedpath.py --jobs e20_p0_c0_s3 ...
"""
import argparse, csv, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--jobs", nargs="+", required=True); ap.add_argument("--out", default="/lfs/skampere1/0/brando9/at2442/out")
a = ap.parse_args()
R = Path("/lfs/skampere1/0/brando9/rl4cv_e25"); G = R / "grading"; D = Path("/lfs/skampere1/0/brando9/at1799")
env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "PYTHONPATH": str(G / "rl4cv/src"), "PATH": f"{G/'bin'}:{os.environ['PATH']}", "RL4CV_SRC": str(G/"rl4cv/src"), "E20_GRADING": str(G)}
def run(j):
    o = Path(a.out) / j; o.mkdir(parents=True, exist_ok=True)
    with open(o / "stdout.log", "w") as fh:
        return subprocess.call([sys.executable, str(R/"code/partial_credit_fixedpath.py"), "--job-dir", str(D/"jobs"/j), "--out", str(o/f"partial_{j}.json"), "--evidence-root", str(o/"compiler_diagnostics")], stdout=fh, stderr=subprocess.STDOUT, env=env)
with ThreadPoolExecutor(len(a.jobs)) as ex: rcs = list(ex.map(run, a.jobs))
saved = {(r["job"], r["task_id"]): r for r in csv.DictReader(open(D/"saved_cells_subset.csv"))}
res = []
for j, rc in zip(a.jobs, rcs):
    d = json.load(open(Path(a.out)/j/f"partial_{j}.json"))
    for r in d["records"]:
        s = saved[(j, r["task_id"])]
        sf = float(s["factored_reward"]); nf = r.get("factored_reward")
        res.append({"job": j, "task": r["task_id"], "saved": sf, "new": nf, "diff": abs(sf-nf) if nf is not None else None, "d": r.get("d"), "rc": rc, "dir_len": d.get("fixed_job_dir_len")})
json.dump(res, open(Path(a.out)/"result.json", "w"), indent=1)
for r in res: print(r)
