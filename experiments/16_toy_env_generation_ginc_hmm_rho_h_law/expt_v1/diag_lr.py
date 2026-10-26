"""Diagnostic for pilot v1: does GRPO raise in-environment accuracy, and at what learning rate does the held-out target stop dropping?

Usage: python diag_lr.py --run results/pilot_v1 --scale n2 --env 2 --lrs 5e-4,1e-4,3e-5
"""
import argparse, json, sys
from pathlib import Path
import numpy as np, torch
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ginc_toy import make_prompts
from policy import SCALES, TinyLM, grpo, greedy_accuracy
from run_pilot import CANDIDATES, TARGETS, G, RL_BATCH

ap = argparse.ArgumentParser(); ap.add_argument("--run", type=Path); ap.add_argument("--scale"); ap.add_argument("--env", type=int)
ap.add_argument("--lrs", default="5e-4,1e-4,3e-5"); ap.add_argument("--steps", type=int, default=400)
a = ap.parse_args(); torch.set_num_threads(1)
spec = CANDIDATES[a.env]
tgt = make_prompts(TARGETS[0], 4000, seed=99); envh = make_prompts(spec, 4000, seed=12); pool = make_prompts(spec, 20000, seed=13)
ev = lambda m: (round(greedy_accuracy(m, envh.x, envh.y), 4), round(greedy_accuracy(m, tgt.x, tgt.y), 4))
for lr in [float(x) for x in a.lrs.split(",")]:
    m = TinyLM(*SCALES[a.scale]); m.load_state_dict(torch.load(a.run / f"start_{a.scale}.pt"))
    c = grpo(m, pool.x, pool.y, a.steps, RL_BATCH, G, lr, 0, ev, [0, 50, 100, 200, a.steps])
    print(json.dumps({"scale": a.scale, "env": spec.name, "lr": lr, "env_acc,target_acc by step": c}), flush=True)
