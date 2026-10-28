"""Night 6: dense versus independent checkpoint reuse on the GINC toy, plus the cosine-schedule control (plan v5, Stage 1).

Starting policies, probes, mixtures and the RL strength are Night 5's committed files (E16_PRETRAIN_SEED=1), read only.
Stages (CPU, resumable, one torch thread per process):
  jobs     print the ordered job list (one JSON per line)
  run      one trajectory -> results/<name>.json (committed, small) and logs/<name>.npz (per-step logs, not committed)
  drive    run a job list with a multiprocessing pool, skipping finished jobs
"""
import argparse
import base64
import json
import time
from functools import lru_cache
from importlib import import_module
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import torch
from copy import deepcopy

V2 = 'experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v2'
g = import_module(f'{V2}.ginc')
r2 = import_module(f'{V2}.run')
from rl4cv.experience import Response, measure_environment
from . import policy6

K, TARGET, make_prompts = g.K, g.TARGET, g.make_prompts
read, write, sha, specs, load_model, evaluate = r2.read, r2.write, r2.sha, r2.specs, r2.load_model, r2.evaluate

HERE = Path(__file__).resolve().parent
NIGHT5 = HERE.parents[1] / '16_toy_env_generation_ginc_hmm_rho_h_law/expt_v5/results/night5'
RESULTS, LOGS, CKPTS = HERE / 'results', HERE / 'logs', HERE / 'ckpt'
BATCH, GROUP = 16, 8
EVAL_EVERY, LONG = 25, 400
CHECKPOINT_STEPS = list(range(EVAL_EVERY, LONG + 1, EVAL_EVERY))   # 16 checkpoints
TARGET_N, POOL_N, HELD_N = 4000, 20000, 512
SETTING = {'lr': 3e-4, 'kl_coef': 0.1}                              # S2, Night 4/5 frozen setting
POOL_ENVS = ('e00', 'e10', 'm02', 'm01')                            # fixed from Night 5's n3 3-seed mean at step 100, before any run
A_SEEDS, POOL_SEEDS = (0, 1, 2), tuple(range(1000, 1012))
B_SEEDS = {100: (2000, 2001, 2002, 2003), 200: (2004, 2005), 400: (2006,)}
COS_LONG_SEEDS = (3000, 3001, 3002)
COS_SHORT_SEEDS = {100: (3100, 3101, 3102, 3103), 200: (3200, 3201)}
BASE_SCALES, ALL_SCALES = ('n1', 'n2', 'n3'), ('n1', 'n2', 'n3', 'n4')


def job_name(j):
    return f"{j['arm']}_{j['scale']}_{j['env']}_{j['schedule']}_T{j['horizon']}_s{j['seed']}"


def jobs(out=NIGHT5, include_n4=True):
    """Ordered job list; the order is the plan's run order so each stage is scorable alone."""
    names = [s.name for s in specs(out)]
    pool_ix = [names.index(e) for e in POOL_ENVS]
    J = []

    def add(stage, arm, scale, env, seed, steps, schedule='constant', horizon=None):
        J.append({'stage': stage, 'arm': arm, 'scale': scale, 'env': names[env], 'env_index': env, 'seed': seed,
                  'steps': steps, 'schedule': schedule, 'horizon': horizon or steps})

    def main(scales, stage):
        for s in scales:
            for e in range(len(names)):
                for seed in A_SEEDS:
                    add(stage, 'A', s, e, seed, LONG)

    def pool(scales, stage):
        for s in scales:
            for e in pool_ix:
                for seed in POOL_SEEDS:
                    add(stage, 'pool', s, e, seed, LONG)

    def indep(scales, stage):
        for s in scales:
            for e in pool_ix:
                for steps, seeds in B_SEEDS.items():
                    for seed in seeds:
                        add(stage, 'B', s, e, seed, steps)

    def cosine(scales, stage):
        for s in scales:
            for e in pool_ix:
                for seed in COS_LONG_SEEDS:
                    add(stage, 'cosL', s, e, seed, LONG, 'cosine', LONG)
                for steps, seeds in COS_SHORT_SEEDS.items():
                    for seed in seeds:
                        add(stage, 'cosS', s, e, seed, steps, 'cosine', steps)

    main(BASE_SCALES, 's1_main_n1_n3')
    pool(('n1', 'n2'), 's2_pool_n1_n2')
    indep(('n1', 'n2'), 's3_B_n1_n2')
    cosine(('n2',), 's4_cosine_n2')
    pool(('n3',), 's5_pool_n3')
    indep(('n3',), 's5_B_n3')
    cosine(('n3',), 's6_cosine_n3')
    if include_n4:
        main(('n4',), 's7_main_n4')
    return J


@lru_cache(maxsize=None)
def prompts_for(env_name, kind):
    out_specs = {s.name: s for s in specs(NIGHT5)}
    if kind == 'target':
        return make_prompts(TARGET, TARGET_N, 99)
    if kind == 'pool':
        return make_prompts(out_specs[env_name], POOL_N, 13)
    return make_prompts(out_specs[env_name], HELD_N, 12)


def pack(bits):
    return base64.b64encode(np.packbits(np.asarray(bits, bool)).tobytes()).decode()


def unpack(text, n=TARGET_N):
    return np.unpackbits(np.frombuffer(base64.b64decode(text), np.uint8))[:n].astype(bool)


def rolling_rho_h(reward, window=EVAL_EVERY):
    """rho and H from the groups the run itself generated in the `window` steps before each checkpoint
    (one step has BATCH groups; the token-mean reward is the probe's reward, so this is `measure_environment` as at the start)."""
    rows = []
    for k in range(1, reward.shape[0] // window + 1):
        chunk = reward[(k - 1) * window:k * window].reshape(-1, reward.shape[2])
        m = measure_environment([[Response(float(v), K, True) for v in row] for row in chunk]).to_dict()
        rows.append({'rho_roll': m['rho'], 'H_roll': m['H'], 'n_groups_roll': int(m['n_groups']), 'mean_reward_roll': m['mean_reward']})
    return rows


def run_job(j, out_dir=RESULTS, log_dir=LOGS, ckpt_dir=CKPTS, save_ckpt=None):
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    name = job_name(j)
    dest = Path(out_dir) / f'{name}.json'
    if dest.exists():
        return name, 'exists'
    t0 = time.time()
    torch.manual_seed(1234)
    model = load_model(NIGHT5, j['scale'])
    ref = deepcopy(model).eval()
    for q in ref.parameters():
        q.requires_grad_(False)
    spec = next(s for s in specs(NIGHT5) if s.name == j['env'])
    target, pool, held = prompts_for(j['env'], 'target'), prompts_for(j['env'], 'pool'), prompts_for(j['env'], 'held')
    start = read(NIGHT5 / f"{j['scale']}_meta.json")['start_target']
    start_bits = np.array(start['token_hits']) == K
    ev = lambda m: {'target': evaluate(m, target), 'env_metrics': evaluate(m, held)}
    eval_at = [s for s in CHECKPOINT_STEPS if s <= j['steps']]
    keep = (j['arm'] == 'A' and j['scale'] != 'n4') if save_ckpt is None else save_ckpt
    curve, log, ckpts = policy6.grpo_logged(model, ref, pool, j['steps'], set(eval_at), ev, j['seed'], batch=BATCH, group=GROUP,
                                            schedule=j['schedule'], horizon=j['horizon'], keep_checkpoints=keep, **SETTING)
    roll = rolling_rho_h(log['reward'])
    rows = []
    for step in eval_at:
        v = curve[step]
        bits = np.array(v['target']['token_hits']) == K
        rows.append({'step': step, 'tokens': step * BATCH * GROUP * K, 'utility': float(bits.mean() - start_bits.mean()),
                     'token_utility': v['target']['token'] - start['token'], 'env_joint': v['env_metrics']['joint'],
                     'last_train_kl': v['last_train_kl'], 'lr_fraction': v['lr_fraction'],
                     'joint_bits': pack(bits), **roll[step // EVAL_EVERY - 1]})
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    np.savez_compressed(Path(log_dir) / f'{name}.npz', **log)
    if keep:
        Path(ckpt_dir).mkdir(parents=True, exist_ok=True)
        torch.save(ckpts, Path(ckpt_dir) / f'{name}.pt')
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    write(dest, {**{k: j[k] for k in ('stage', 'arm', 'scale', 'env', 'seed', 'steps', 'schedule', 'horizon')},
                 'start_checkpoint_sha256': sha(NIGHT5 / f"start_{j['scale']}.pt"), 'setting': SETTING,
                 'start_joint': float(start_bits.mean()), 'rows': rows, 'seconds': time.time() - t0,
                 'torch': torch.__version__, 'numpy': np.__version__})
    return name, f'U={rows[-1]["utility"]:+.5f} s={time.time() - t0:.0f}'


def _star(j):
    return run_job(j)


def drive(job_list, procs):
    todo = [j for j in job_list if not (RESULTS / f'{job_name(j)}.json').exists()]
    print(f'{len(todo)} of {len(job_list)} jobs to run on {procs} processes', flush=True)
    done = 0
    with Pool(procs) as p:
        for name, msg in p.imap_unordered(_star, todo, chunksize=1):
            done += 1
            print(f'[{done}/{len(todo)}] {name} {msg}', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['jobs', 'run', 'drive'])
    ap.add_argument('--stages', default='', help='comma-separated stage names to keep (default all)')
    ap.add_argument('--procs', type=int, default=4)
    ap.add_argument('--no-n4', action='store_true')
    ap.add_argument('--job', help='JSON job for stage run')
    a = ap.parse_args()
    if a.stage == 'run':
        print(*run_job(json.loads(a.job)))
        return
    J = jobs(include_n4=not a.no_n4)
    if a.stages:
        keep = set(a.stages.split(','))
        J = [j for j in J if j['stage'] in keep]
    if a.stage == 'jobs':
        print(f'{len(J)} jobs', flush=True)
        for j in J:
            print(json.dumps(j))
    else:
        drive(J, a.procs)


if __name__ == '__main__':
    main()
