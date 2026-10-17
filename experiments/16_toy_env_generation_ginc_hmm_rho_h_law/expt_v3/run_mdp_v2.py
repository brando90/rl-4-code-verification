"""Experiment 16, expt_v3, Night 3 (mdp_v2): the known-MDP family with start-policy repeats and six scales.

Same chain, candidates, budgets, seeds, GRPO, KL and oracle as run_mdp.py (imported, unchanged). New:
  - six scales whose start target values clearly increase (smaller models get fewer behavior-cloning steps)
  - three start-policy repeats per scale (behavior-cloning seed 0, 1, 2)
  - every probe also measured on the noise-free twin of its candidate (same rollouts, sigma = 0), a
    diagnostic for the reward-noise failure; the law itself still uses the standard probe

One process per (scale, repeat):

    python run_mdp_v2.py --scale s6 --rep 0 --out results/mdp_v2
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_mdp as R  # noqa: E402
from known_mdp import N_REGIONS, TARGET, exact_value, make_chain  # noqa: E402

# (width, hidden layers) and behavior-cloning steps; chosen from start policies only (PROTOCOL.md, Night 3 addendum)
SCALES_V2 = {"s1": (2, 1), "s2": (4, 1), "s3": (8, 1), "s4": (16, 1), "s5": (32, 1), "s6": (64, 2)}
BC_STEPS_V2 = {"s1": 30, "s2": 60, "s3": 60, "s4": 60, "s5": 80, "s6": 100}
REPS = [0, 1, 2]
R.SCALES, R.BC_STEPS = SCALES_V2, BC_STEPS_V2  # start_policy reads these module globals


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", required=True, choices=list(SCALES_V2))
    ap.add_argument("--rep", type=int, required=True, choices=REPS)
    ap.add_argument("--out", default="results/mdp_v2")
    ap.add_argument("--stage", choices=["start", "all"], default="all")
    args = ap.parse_args()
    out = HERE / args.out
    out.mkdir(parents=True, exist_ok=True)
    sc, rep = args.scale, args.rep
    chain = make_chain()
    cands = R.candidates()
    t0 = time.time()
    ref = R.start_policy(sc, chain, seed=rep)
    with torch.no_grad():
        pc = R.p_correct(ref, chain)
        base = float(exact_value(pc, TARGET))
    start = {"scale": sc, "rep": rep, "n_params": ref.n_params(), "width_layers": SCALES_V2[sc], "bc_steps": BC_STEPS_V2[sc],
             "target_value": base, "p_correct_by_region": [float(pc[chain.region == r].mean()) for r in range(N_REGIONS)]}
    print(json.dumps(start), flush=True)
    tag = f"{sc}_r{rep}"
    (out / f"start_{tag}.json").write_text(json.dumps(start, indent=1))
    if args.stage == "start":
        return 0
    with open(out / f"probe_{tag}.jsonl", "w") as f:
        for k, c in enumerate(cands):
            seed = 10_000 + k + 100_000 * rep
            m = R.probe(ref, chain, c, seed=seed)
            nf = m if c.sigma == 0 else R.probe(ref, chain, dataclasses.replace(c, sigma=0.0), seed=seed)  # same rollouts, no noise
            f.write(json.dumps({"scale": sc, "rep": rep, "n_params": ref.n_params(), "env": c.name, **m,
                                "rho_noise_free": nf["rho"], "H_noise_free": nf["H"]}) + "\n")
    print(f"{tag} probes done {time.time() - t0:.0f}s", flush=True)
    with open(out / f"rl_{tag}.jsonl", "w") as f:
        for c in cands:
            for seed in R.SEEDS:
                pol = R.start_policy(sc, chain, seed=rep)
                torch.manual_seed(seed)
                rows, steps = R.grpo(pol, ref, chain, c, seed=1000 * seed + 7 + 100_000 * rep)
                oracle = R.exact_gradient(R.start_policy(sc, chain, seed=rep), ref, chain, c, steps)
                for row in rows:
                    f.write(json.dumps({"scale": sc, "rep": rep, "n_params": ref.n_params(), "env": c.name, "seed": seed, **row,
                                        "start_target_value": base, "utility": row["target_value"] - base,
                                        "oracle_exact_grad_utility": oracle - base}) + "\n")
    print(f"{tag} rl done {time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
