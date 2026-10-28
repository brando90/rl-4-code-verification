"""Night 6 GRPO with per-step logs and an optional cosine learning-rate schedule (expt_v2/policy.py is never edited)."""
import math
from copy import deepcopy
from importlib import import_module
import numpy as np
import torch

V2 = 'experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v2'
g = import_module(f'{V2}.ginc')
pol = import_module(f'{V2}.policy')
K, rewards = g.K, g.rewards
generate, rollout_loss = pol.generate, pol.rollout_loss


def lr_at(schedule, lr0, update, horizon):
    """Learning rate used by update number `update` (1-based): constant, or cosine with floor 0 over `horizon` updates."""
    if schedule == 'constant':
        return lr0
    if schedule == 'cosine':
        return lr0 * .5 * (1 + math.cos(math.pi * (update - 1) / horizon))
    raise ValueError(schedule)


def grpo_logged(model, ref, pool, steps, eval_at, eval_fn, seed, batch=16, group=8, lr=1e-4, kl_coef=1.,
                schedule='constant', horizon=None, keep_checkpoints=False):
    """Same sampling, loss and update order as policy.grpo (constant schedule is bit-identical to it); also returns
    per-step logs (prompt index, group rewards, token counts, admitted flags, leave-one-out advantages, learning rate)."""
    horizon = horizon or steps
    gen = torch.Generator().manual_seed(seed)
    rng = np.random.default_rng(seed)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    out, ckpts = {}, {}
    log = {'prompt_idx': np.zeros((steps, batch), np.int32), 'reward': np.zeros((steps, batch, group), np.float32),
           'tokens': np.full((steps, batch, group), K, np.int16), 'admitted': np.ones((steps, batch, group), bool),
           'advantage': np.zeros((steps, batch, group), np.float32), 'lr': np.zeros(steps)}
    for step in range(1, steps + 1):
        idx = rng.integers(len(pool.x), size=batch)
        x, y = pool.x[idx], pool.y[idx]
        a = generate(model, x, group, gen)
        reward, _ = rewards(a, y)
        loss, kl = rollout_loss(model, ref, x, a, reward, kl_coef)
        cur = lr_at(schedule, lr, step, horizon)
        if schedule != 'constant':
            for pg in opt.param_groups:
                pg['lr'] = cur
        opt.zero_grad(); loss.backward(); opt.step()
        i = step - 1
        log['prompt_idx'][i], log['reward'][i], log['lr'][i] = idx, reward, cur
        log['advantage'][i] = reward - (reward.sum(1, keepdims=True) - reward) / (group - 1)
        if step in eval_at:
            out[step] = eval_fn(model)
            out[step]['last_train_kl'] = float(kl.detach())
            out[step]['lr_fraction'] = cur / lr
            if keep_checkpoints:
                ckpts[step] = {k: v.detach().clone() for k, v in model.state_dict().items()}
    return out, log, ckpts
