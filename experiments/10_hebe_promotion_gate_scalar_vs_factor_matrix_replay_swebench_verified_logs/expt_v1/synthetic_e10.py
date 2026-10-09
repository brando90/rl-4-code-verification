"""Synthetic node-dependent SWE-bench-like factor matrices for experiment 10 (timing, sanity and bootstrap coverage)."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_e10 as a  # noqa: E402


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def generate(n_systems: int, n_tasks: int, seed: int, breakage_signal: bool) -> list[dict]:
    """Systems differ in ability and (if breakage_signal) in a propensity to break PASS_TO_PASS tests."""
    rng = np.random.default_rng(seed)
    theta = rng.normal(0, 1, n_systems)
    beta = 0.3 * theta + rng.normal(0, 1, n_systems) if breakage_signal else np.zeros(n_systems)
    d = rng.normal(0, 1.2, n_tasks)
    rows = []
    for i in range(n_systems):
        g = rng.random(n_tasks) < sigmoid(2.5 + 0.5 * theta[i])
        fix_full = rng.random(n_tasks) < sigmoid(theta[i] - d)
        tfix = np.where(fix_full, 1.0, np.where(rng.random(n_tasks) < 0.3, 0.5, 0.0))
        keep_full = rng.random(n_tasks) < sigmoid(2.0 - 0.8 * beta[i]) if breakage_signal else rng.random(n_tasks) < 0.85
        tkeep = np.where(keep_full, 1.0, rng.uniform(0.5, 0.99, n_tasks))
        for t in range(n_tasks):
            resolved = bool(g[t] and tfix[t] == 1 and tkeep[t] == 1)
            rows.append({"submission": f"sys{i:04d}", "instance_id": f"task{t:04d}", "included": True, "common_cohort": True,
                         "gate": int(g[t]), "t_fix": float(tfix[t]) if g[t] else None,
                         "t_keep": float(tkeep[t]) if g[t] else None, "resolved": resolved})
    return rows


def write(rows: list[dict], path: Path) -> None:
    path.write_bytes(gzip.compress("\n".join(json.dumps(r) for r in rows).encode()))


def coverage(args) -> dict:
    """Coverage of the dyadic-bootstrap interval for split-averaged near-pair estimands on a fixed task set."""
    pop_rows = generate(args.pop_systems, args.tasks, args.seed, breakage_signal=True)
    pop_path = Path(args.workdir) / "pop.jsonl.gz"
    write(pop_rows, pop_path)
    pop = a.load_matrix(pop_path, expect_sha=None)
    splits = a.make_splits(len(pop.tasks), args.splits, args.seed + 1)
    near_max = int(np.floor(0.05 * (len(pop.tasks) // 2)))
    hkey_full = a.pair_hash(pop.systems)
    keys = ("H1_hpr", "R0_minus_R2", "R2_minus_R3", "R0_minus_R3", "H2_hrm")

    def estimands(m, pt, hkey, w):
        vals = {k: [] for k in keys}
        for s in range(args.splits):
            st = a.split_pairs(m, pt, splits[s], near_max)
            r = a.split_statistics(st, "near", hkey, w, (0.5,))
            if r["n_pairs"] < 30:
                continue
            vals["H1_hpr"].append(r["H1"]["hpr"])
            for a_, b_ in (("R0", "R2"), ("R2", "R3"), ("R0", "R3")):
                vals[f"{a_}_minus_{b_}"].append(r["H3"][0.5][a_]["hpr"] - r["H3"][0.5][b_]["hpr"])
            vals["H2_hrm"].append(r["H2"]["hrm"])
        return {k: np.nanmean(np.stack(v), 0) for k, v in vals.items()}

    pt_pop = a.pair_tensors(pop)
    truth = {k: float(v[0]) for k, v in estimands(pop, pt_pop, hkey_full, np.ones((1, *hkey_full.shape), np.float32)).items()}
    rng = np.random.default_rng(args.seed + 2)
    hits = {k: 0 for k in keys}
    defined = {k: 0 for k in keys}
    for rep in range(args.reps):
        pick = np.sort(rng.choice(args.pop_systems, args.sample_systems, replace=False))
        m = a.Matrix([pop.systems[i] for i in pick], pop.tasks, pop.r[pick], pop.g[pick], pop.gf[pick], pop.gk[pick])
        pt = a.pair_tensors(m)
        w = a.bootstrap_weights(len(pick), args.draws, args.seed + 100 + rep).astype(np.float32)
        est = estimands(m, pt, hkey_full[np.ix_(pick, pick)], w)
        for k in keys:
            boot = est[k][1:]
            boot = boot[np.isfinite(boot)]
            if len(boot) < 20:
                continue
            lo, hi = np.percentile(boot, [2.5, 97.5])
            defined[k] += 1
            hits[k] += int(lo <= truth[k] <= hi)
    return {"truth_population": truth, "coverage": {k: (hits[k] / defined[k] if defined[k] else None) for k in keys},
            "reps_defined": defined, "settings": vars(args)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("write", "coverage"))
    ap.add_argument("--systems", type=int, default=164)
    ap.add_argument("--tasks", type=int, default=424)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--null", action="store_true", help="no system-level breakage signal")
    ap.add_argument("--out", default="synthetic.jsonl.gz")
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--pop-systems", type=int, default=600)
    ap.add_argument("--sample-systems", type=int, default=60)
    ap.add_argument("--splits", type=int, default=10)
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--reps", type=int, default=100)
    args = ap.parse_args(argv)
    if args.mode == "write":
        write(generate(args.systems, args.tasks, args.seed, breakage_signal=not args.null), Path(args.out))
        print(args.out)
    else:
        print(json.dumps(coverage(args), indent=1, default=float))


if __name__ == "__main__":
    main()
