"""Diagnostic after pilot v2: does a KL-to-start penalty stop the target drop while keeping some in-environment gain?

Usage: python diag_kl.py --run results/pilot_v2 --scale n2 --env 2 --kls 0,0.1,1
"""
import argparse, copy, json, sys
from pathlib import Path
import torch
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ginc_toy import make_prompts
from policy import SCALES, TinyLM, grpo, greedy_accuracy
from run_pilot import CANDIDATES, G, RL_BATCH, RL_LR, TARGETS_V2, target_prompts

ap = argparse.ArgumentParser(); ap.add_argument("--run", type=Path); ap.add_argument("--scale"); ap.add_argument("--env", type=int)
ap.add_argument("--kls", default="0,0.1,1"); ap.add_argument("--steps", type=int, default=200)
a = ap.parse_args(); torch.set_num_threads(1)
spec = CANDIDATES[a.env]
tgt = target_prompts(TARGETS_V2[0], 4000, seed=99); envh = make_prompts(spec, 1000, seed=12); pool = make_prompts(spec, 20000, seed=13)
ev = lambda m: (round(greedy_accuracy(m, envh.x, envh.y), 4), round(greedy_accuracy(m, tgt.x, tgt.y), 4))
for kl in [float(x) for x in a.kls.split(",")]:
    m = TinyLM(*SCALES[a.scale]); m.load_state_dict(torch.load(a.run / f"start_{a.scale}.pt")); ref = copy.deepcopy(m).eval()
    c = grpo(m, pool.x, pool.y, a.steps, RL_BATCH, G, RL_LR, 0, ev, [0, 50, 100, a.steps], kl_coef=kl, ref=ref)
    print(json.dumps({"scale": a.scale, "env": spec.name, "kl_coef": kl, "lr": RL_LR, "(env_acc, tgtMix9_acc) by step": c}), flush=True)
