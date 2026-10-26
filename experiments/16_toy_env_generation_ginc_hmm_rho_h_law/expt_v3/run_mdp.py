"""Experiment 16, expt_v3: the known-MDP sanity family, end to end on CPU.

Stages (all in one process, a few minutes in total):
  1. start policies: MLPs of four widths, behavior-cloned for a few steps on a noisy demonstrator
  2. probes: rho and H (rl4cv.experience.measure_environment) for every (scale, candidate)
  3. GRPO with KL to the start policy on each candidate, exact target value at three token budgets
  4. exact-gradient oracle: the same number of optimizer steps on the exact (noise-free) objective

    python run_mdp.py --out results/mdp_v1
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "src"))  # rl4cv

from known_mdp import A, N_REGIONS, N_STATES, TARGET, EnvSpec, exact_value, make_chain, region_states, rollout_groups  # noqa: E402
from rl4cv.experience import Response, measure_environment  # noqa: E402

torch.set_num_threads(1)

SCALES = {"n1": (4, 1), "n2": (16, 1), "n3": (32, 2), "n4": (128, 2)}  # (width, hidden layers)
BC_STEPS = {"n1": 60, "n2": 80, "n3": 100, "n4": 140}
BUDGETS = [25_600, 51_200, 102_400]  # generated tokens (actions)
SEEDS = [0, 1, 2, 3, 4]
GROUP = 8
BATCH = 16
LR = 3e-3
KL = 1.0
PROBE_GROUPS = 512


class Policy(nn.Module):
    def __init__(self, d_in: int, width: int, layers: int):
        super().__init__()
        mods, d = [], d_in
        for _ in range(layers):
            mods += [nn.Linear(d, width), nn.Tanh()]
            d = width
        mods.append(nn.Linear(d, A))
        self.net = nn.Sequential(*mods)

    def forward(self, x):
        return self.net(x)

    def n_params(self) -> int:
        return sum(p.numel() for p in self.parameters())


def candidates() -> list[EnvSpec]:
    """The generator's pool: 16 single-region base settings, then 6 random mixtures of regions/slack/noise."""
    out = []
    for r, slack, sigma in itertools.product(range(N_REGIONS), (0, 6), (0.0, 0.5)):
        out.append(EnvSpec(f"b{len(out):02d}_r{r}_sl{slack}_sg{sigma}", region_states([r]), slack, sigma))
    rng = np.random.default_rng(1616)
    for k in range(6):
        size = int(rng.integers(2, N_REGIONS + 1))
        regs = sorted(rng.choice(N_REGIONS, size=size, replace=False).tolist())
        slack = int(rng.choice([0, 2, 6]))
        sigma = float(rng.choice([0.0, 0.5]))
        out.append(EnvSpec(f"m{k:02d}_r{''.join(map(str, regs))}_sl{slack}_sg{sigma}", region_states(regs), slack, sigma))
    return out


def start_policy(scale: str, chain, seed: int = 0) -> Policy:
    """Behavior cloning on a noisy demonstrator (correct w.p. 0.5, else uniform); late regions are rarer."""
    torch.manual_seed(seed)
    width, layers = SCALES[scale]
    pol = Policy(chain.phi.shape[1], width, layers)
    rng = np.random.default_rng(seed)
    w = np.where(chain.region >= 2, 0.25, 1.0)
    w = w / w.sum()
    opt = torch.optim.Adam(pol.parameters(), lr=1e-2)
    phi = torch.as_tensor(chain.phi)
    for _ in range(BC_STEPS[scale]):
        s = rng.choice(N_STATES, size=256, p=w)
        lab = np.where(rng.random(256) < 0.5, chain.correct[s], rng.integers(0, A, 256))
        loss = F.cross_entropy(pol(phi[s]), torch.as_tensor(lab))
        opt.zero_grad()
        loss.backward()
        opt.step()
    return pol


def p_correct(pol: Policy, chain) -> torch.Tensor:
    probs = F.softmax(pol(torch.as_tensor(chain.phi)), -1)
    return probs[torch.arange(N_STATES), torch.as_tensor(chain.correct)]


def probe(pol: Policy, chain, spec: EnvSpec, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    with torch.no_grad():
        probs = F.softmax(pol(torch.as_tensor(chain.phi)), -1).double().numpy()
    probs = probs / probs.sum(1, keepdims=True)
    ro = rollout_groups(probs, chain, spec, PROBE_GROUPS, GROUP, rng)
    groups = [[Response(float(ro["reward"][i, j]), int(ro["tokens"][i, j]), not bool(ro["capped"][i, j])) for j in range(GROUP)]
              for i in range(PROBE_GROUPS)]
    m = measure_environment(groups).to_dict()
    m["success_rate"] = float(ro["success"].mean())
    return m


def grpo(pol: Policy, ref: Policy, chain, spec: EnvSpec, seed: int) -> tuple[list[dict], int]:
    """GRPO with leave-one-out advantages, capped episodes excluded from the loss, exact KL to ref on visited states."""
    rng = np.random.default_rng(seed)
    opt = torch.optim.Adam(pol.parameters(), lr=LR)
    phi = torch.as_tensor(chain.phi)
    with torch.no_grad():
        ref_logp = F.log_softmax(ref(phi), -1)
    tokens, rows, step = 0, [], 0
    todo = list(BUDGETS)
    while todo:
        logp = F.log_softmax(pol(phi), -1)
        probs = logp.detach().exp().double().numpy()
        probs = probs / probs.sum(1, keepdims=True)
        ro = rollout_groups(probs, chain, spec, BATCH, GROUP, rng)
        r = ro["reward"]
        adv = r - (r.sum(1, keepdims=True) - r) / (GROUP - 1)
        w_ep = adv * (~ro["capped"])  # admitted episodes only
        W = torch.as_tensor((w_ep[:, :, None, None] * ro["sa_counts"]).sum((0, 1)))  # N x A
        visits = torch.as_tensor(ro["sa_counts"].sum((0, 1, 3)))
        n_tok = int(ro["tokens"].sum())
        loss = -(W * logp).sum() / max(n_tok, 1)
        kl_s = (logp.exp() * (logp - ref_logp)).sum(1)
        loss = loss + KL * (visits * kl_s).sum() / max(visits.sum(), 1)
        opt.zero_grad()
        loss.backward()
        opt.step()
        tokens += n_tok
        step += 1
        while todo and tokens >= todo[0]:
            with torch.no_grad():
                rows.append({"budget": todo.pop(0), "tokens_used": tokens, "steps": step,
                             "target_value": float(exact_value(p_correct(pol, chain), TARGET)),
                             "env_value": float(exact_value(p_correct(pol, chain), spec))})
    return rows, step


def exact_gradient(pol: Policy, ref: Policy, chain, spec: EnvSpec, steps: int) -> float:
    """Oracle: `steps` Adam steps on the exact expected success of spec (noise-free, every state weighted by the exact objective)."""
    opt = torch.optim.Adam(pol.parameters(), lr=LR)
    phi = torch.as_tensor(chain.phi)
    with torch.no_grad():
        ref_logp = F.log_softmax(ref(phi), -1)
    for _ in range(steps):
        logp = F.log_softmax(pol(phi), -1)
        pc = logp.exp()[torch.arange(N_STATES), torch.as_tensor(chain.correct)]
        kl = (logp.exp() * (logp - ref_logp)).sum(1)
        states = torch.as_tensor(sorted(set(range(min(spec.starts), N_STATES))))
        loss = -exact_value(pc, spec) + KL * kl[states].mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
    with torch.no_grad():
        return float(exact_value(p_correct(pol, chain), TARGET))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/mdp_v1")
    ap.add_argument("--stage", choices=["start", "all"], default="all")
    ap.add_argument("--scales", default="n1,n2,n3,n4")
    args = ap.parse_args()
    out = HERE / args.out
    out.mkdir(parents=True, exist_ok=True)
    chain = make_chain()
    cands = candidates()
    t0 = time.time()
    meta = {"chain_correct": chain.correct.tolist(), "regions": chain.region.tolist(), "target": TARGET.to_dict(),
            "candidates": [c.to_dict() for c in cands], "budgets": BUDGETS, "seeds": SEEDS, "group": GROUP, "batch": BATCH,
            "lr": LR, "kl": KL, "scales": {}}
    starts = {}
    for sc in SCALES:
        pol = start_policy(sc, chain)
        starts[sc] = pol
        with torch.no_grad():
            pc = p_correct(pol, chain)
            meta["scales"][sc] = {"n_params": pol.n_params(), "bc_steps": BC_STEPS[sc],
                                  "target_value": float(exact_value(pc, TARGET)),
                                  "p_correct_by_region": [float(pc[chain.region == r].mean()) for r in range(N_REGIONS)]}
        print(sc, meta["scales"][sc], flush=True)
    if args.scales == "n1,n2,n3,n4":
        (out / "meta.json").write_text(json.dumps(meta, indent=1))
    if args.stage == "start":
        return 0
    starts = {sc: starts[sc] for sc in args.scales.split(",")}
    tag = args.scales.replace(",", "-")
    with open(out / f"probe_{tag}.jsonl", "w") as f:
        for sc, pol in starts.items():
            for k, c in enumerate(cands):
                m = probe(pol, chain, c, seed=10_000 + k)
                f.write(json.dumps({"scale": sc, "n_params": pol.n_params(), "env": c.name, **m}) + "\n")
    print(f"probes done {time.time() - t0:.0f}s", flush=True)
    with open(out / f"rl_{tag}.jsonl", "w") as f:
        for sc, ref in starts.items():
            base = meta["scales"][sc]["target_value"]
            for c in cands:
                for seed in SEEDS:
                    pol = start_policy(sc, chain)
                    torch.manual_seed(seed)
                    rows, steps = grpo(pol, ref, chain, c, seed=1000 * seed + 7)
                    oracle = exact_gradient(start_policy(sc, chain), ref, chain, c, steps)
                    for row in rows:
                        f.write(json.dumps({"scale": sc, "n_params": ref.n_params(), "env": c.name, "seed": seed, **row,
                                            "start_target_value": base, "utility": row["target_value"] - base,
                                            "oracle_exact_grad_utility": oracle - base}) + "\n")
            print(f"{sc} rl done {time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
