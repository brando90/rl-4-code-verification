"""Experiment 16 pilot, one scale per process: pretrain the start policy, probe rho/H on every candidate
environment, run GRPO per (environment, seed) and record held-out target accuracy at each budget.

Usage (CPU, one thread per process; every stage runs in the foreground and finishes):
    python run_pilot.py --scale n4 --out results/pilot_v1 --stage pretrain     # writes start_n4.pt + n4_meta.json
    python run_pilot.py --scale n4 --out results/pilot_v1 --stage rl --envs 0:4 # candidates 0..3
    python run_pilot.py --scale n1 --out results/smoke --stage all --smoke      # seconds, pipeline check only

Writes <out>/<scale>_probe_<i>-<j>.jsonl, <out>/<scale>_rl_<i>-<j>.jsonl and <out>/<scale>_meta.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "src"))  # rl4cv

from ginc_toy import EnvSpec, PromptSet, make_prompts, pretraining_docs  # noqa: E402
from policy import SCALES, TinyLM, grpo, greedy_accuracy, sample_groups  # noqa: E402
from rl4cv.experience import Response, measure_environment  # noqa: E402

PRETRAIN_SETTINGS = [(S, sh) for S in (4, 8, 12) for sh in (2.0, 4.0, 8.0)]
PRETRAIN_PER_SETTING = 64  # concepts per (S, sharpness) in the pretraining bank (family_seed 1)
DOC_LEN = 32

# Candidate training environments: a fixed fractional design over the four knobs, all from the
# pretraining bank (family_seed 1). n_concepts=2 means the environment uses only the first two concepts.
CANDIDATES = [
    EnvSpec("e01_S4_sh2_n2_L4", 4, 2.0, 2, 4),
    EnvSpec("e02_S4_sh8_n64_L16", 4, 8.0, 64, 16),
    EnvSpec("e03_S8_sh4_n64_L12", 8, 4.0, 64, 12),
    EnvSpec("e04_S8_sh4_n2_L12", 8, 4.0, 2, 12),
    EnvSpec("e05_S8_sh2_n64_L4", 8, 2.0, 64, 4),
    EnvSpec("e06_S8_sh8_n64_L24", 8, 8.0, 64, 24),
    EnvSpec("e07_S12_sh4_n64_L8", 12, 4.0, 64, 8),
    EnvSpec("e08_S12_sh8_n2_L16", 12, 8.0, 2, 16),
    EnvSpec("e09_S12_sh2_n64_L24", 12, 2.0, 64, 24),
    EnvSpec("e10_S4_sh4_n64_L24", 4, 4.0, 64, 24),
    EnvSpec("e11_S8_sh8_n2_L4", 8, 8.0, 2, 4),
    EnvSpec("e12_S12_sh4_n2_L4", 12, 4.0, 2, 4),
]
# Target benchmarks. v1 (pilot_v1): two held-out-concept targets (family_seed 2, concepts the start
# policies never saw). v2 (pilot_v2, after diag_lr.py showed RL gains do not reach unseen concepts):
# the GINC-faithful target, prompts over the pretraining concepts (as GINC's in-context test does) in a
# format no candidate uses (all nine (S, sharpness) settings mixed, prefix length 10), plus the v1
# held-out-concept target kept as the far-transfer secondary.
TARGETS_V1 = [
    EnvSpec("tgtA_S8_sh4_n64_L12_heldout", 8, 4.0, 64, 12, family_seed=2),
    EnvSpec("tgtB_S12_sh8_n64_L16_heldout", 12, 8.0, 64, 16, family_seed=2),
]
TARGET_MIX9 = [EnvSpec(f"mix9_S{S}_sh{sh:g}", S, sh, 64, 10) for S, sh in PRETRAIN_SETTINGS]
TARGETS_V2 = ["tgtMix9_L10_pretrain_concepts", TARGETS_V1[0]]
TARGETS = TARGETS_V1


def target_name(t) -> str:
    return t if isinstance(t, str) else t.name


def target_prompts(t, n: int, seed: int):
    """A target's fixed evaluation prompts; the string target is the nine-setting mixture."""
    if not isinstance(t, str):
        return make_prompts(t, n, seed)
    parts = [make_prompts(spec, n // len(TARGET_MIX9), seed + k) for k, spec in enumerate(TARGET_MIX9)]
    return PromptSet(np.concatenate([p.x for p in parts]), np.concatenate([p.y for p in parts]),
                     np.concatenate([p.bayes_acc for p in parts]), np.concatenate([p.concept_idx for p in parts]))

G = 8
PROBE_PROMPTS = 512
POOL_PROMPTS = 20000
TARGET_PROMPTS = 4000
RL_BATCH = 32
EVAL_AT = [0, 50, 100, 200]
RL_LR = 5e-4
SEEDS = [0, 1]
PRETRAIN = {"steps": 1500, "batch": 64, "lr": 3e-3}


def state_hash(model: torch.nn.Module) -> str:
    h = hashlib.sha256()
    for k, v in model.state_dict().items():
        h.update(k.encode())
        h.update(v.numpy().tobytes())
    return h.hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", required=True, choices=list(SCALES))
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--stage", choices=["pretrain", "rl", "all"], default="all")
    ap.add_argument("--envs", default=None, help="slice i:j of the candidate list")
    ap.add_argument("--targets", choices=["v1", "v2"], default="v1")
    args = ap.parse_args()
    global TARGETS
    TARGETS = TARGETS_V2 if args.targets == "v2" else TARGETS_V1
    torch.set_num_threads(1)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    pre = dict(PRETRAIN)
    eval_at, cands, seeds, n_target = EVAL_AT, CANDIDATES, SEEDS, TARGET_PROMPTS
    if args.smoke:
        pre["steps"], eval_at, cands, seeds, n_target = 30, [0, 5, 10], CANDIDATES[:2], [0], 500

    if args.envs:
        i, j = (int(v) for v in args.envs.split(":"))
        cands = cands[i:j]
    else:
        i, j = 0, len(cands)
    t0 = time.time()
    d, layers, heads = SCALES[args.scale]
    torch.manual_seed(1234)
    model = TinyLM(d, layers, heads)
    ckpt = out / f"start_{args.scale}.pt"
    meta_path = out / f"{args.scale}_meta.json"
    if args.stage == "rl":
        model.load_state_dict(torch.load(ckpt))
        start_state = {k: v.clone() for k, v in model.state_dict().items()}
        meta = json.loads(meta_path.read_text())
        targets = {target_name(t): target_prompts(t, n_target, seed=99) for t in TARGETS}
        start_target = eval_targets(model, targets)
        return run_rl(args, model, start_state, meta, start_target, targets, cands, seeds, eval_at, out, i, j, t0)
    docs = pretraining_docs(200_000, DOC_LEN, seed=7, settings=PRETRAIN_SETTINGS, per_setting=PRETRAIN_PER_SETTING)
    losses = pretrain(model, docs, pre["steps"], pre["batch"], pre["lr"], seed=0)
    start_state = {k: v.clone() for k, v in model.state_dict().items()}
    t_pre = time.time() - t0
    torch.save(start_state, ckpt)

    targets = {target_name(t): target_prompts(t, n_target, seed=99) for t in TARGETS}

    def eval_fn(m):
        return {name: greedy_accuracy(m, p.x, p.y) for name, p in targets.items()}

    start_target = eval_fn(model)
    meta = {
        "scale": args.scale,
        "d_model": d,
        "layers": layers,
        "heads": heads,
        "n_params": model.n_params(),
        "pretrain": pre,
        "pretrain_final_loss_mean_last50": float(np.mean(losses[-50:])),
        "pretrain_seconds": round(t_pre, 1),
        "start_state_sha16": state_hash(model),
        "start_target_greedy_acc": start_target,
        "G": G,
        "rl": {"batch": RL_BATCH, "lr": RL_LR, "eval_at_steps": eval_at, "tokens_per_step": RL_BATCH * G, "seeds": seeds},
        "smoke": args.smoke,
    }
    print(json.dumps(meta), flush=True)
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    if args.stage == "pretrain":
        return 0
    return run_rl(args, model, start_state, meta, start_target, targets, cands, seeds, eval_at, out, i, j, t0)


def eval_targets(m, targets):
    return {name: greedy_accuracy(m, p.x, p.y) for name, p in targets.items()}


def run_rl(args, model, start_state, meta, start_target, targets, cands, seeds, eval_at, out, i, j, t0) -> int:
    tag = "" if args.targets == "v1" else f"_{args.targets}"
    probe_f = open(out / f"{args.scale}_probe{tag}_{i}-{j}.jsonl", "w")
    rl_f = open(out / f"{args.scale}_rl{tag}_{i}-{j}.jsonl", "w")
    for spec in cands:
        model.load_state_dict(start_state)
        probe = make_prompts(spec, PROBE_PROMPTS, seed=11)
        a = sample_groups(model, probe.x, G, torch.Generator().manual_seed(5))
        rewards = (a == probe.y[:, None]).astype(float)
        m = measure_environment([[Response(float(r), 1, True) for r in row] for row in rewards])
        row = {"scale": args.scale, "n_params": meta["n_params"], "env": spec.name, **spec.to_dict(), **m.to_dict(),
               "start_greedy_acc_env": greedy_accuracy(model, probe.x, probe.y), "bayes_acc_mean": float(probe.bayes_acc.mean())}
        probe_f.write(json.dumps(row) + "\n")
        probe_f.flush()
        pool = make_prompts(spec, POOL_PROMPTS, seed=13)
        env_held = make_prompts(spec, 1000, seed=12)  # in-environment held-out prompts (diagnostic)
        eval_fn = lambda m: {**eval_targets(m, targets), "_env": greedy_accuracy(m, env_held.x, env_held.y)}  # noqa: E731
        final = []
        for seed in seeds:
            model.load_state_dict(start_state)
            torch.manual_seed(seed)
            curve = grpo(model, pool.x, pool.y, max(eval_at), RL_BATCH, G, RL_LR, seed, eval_fn, eval_at)
            for step, accs in curve.items():
                rl_f.write(json.dumps({"scale": args.scale, "n_params": meta["n_params"], "env": spec.name, "seed": seed, "step": step,
                                       "tokens": step * RL_BATCH * G, "env_acc": accs.pop("_env"), "target_acc": accs,
                                       "utility": {k: accs[k] - start_target[k] for k in accs}}) + "\n")
            rl_f.flush()
            final.append(curve[max(eval_at)][target_name(TARGETS[0])] - start_target[target_name(TARGETS[0])])
        print(f"{args.scale} {spec.name} rho={m.rho:.4g} H={m.H:.3f} p={m.mean_reward:.3f} "
              f"dTgt0@{max(eval_at)}={np.mean(final):+.3f} t={time.time() - t0:.0f}s", flush=True)
    print(f"{args.scale} envs {i}:{j} done in {time.time() - t0:.0f}s", flush=True)
    return 0


from policy import pretrain  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
