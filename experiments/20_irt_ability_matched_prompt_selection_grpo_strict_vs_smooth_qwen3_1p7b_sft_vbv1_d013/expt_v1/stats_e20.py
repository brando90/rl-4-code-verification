"""TLDR: Experiment 20's statistics helpers (Hard Rule 11): paired bootstrap over task groups (near-duplicate and safe/vulnerable pairs move together) for means and differences of per-task quantities with two-sided percentile p-values, a paired sign-swap test over seeds, rank-based AUC, binary log loss and expected calibration error (ECE) with equal-width bins, and the x [lo, hi] p-val=Z formatter."""
from __future__ import annotations

import numpy as np

DRAWS = 10_000
SEED = 20261021


def group_bootstrap_indices(groups: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Resample task groups with replacement and return the task indices of the resampled set (cluster bootstrap)."""
    groups = np.asarray(groups)
    uniq, inverse = np.unique(groups, return_inverse=True)
    members = [np.flatnonzero(inverse == g) for g in range(uniq.size)]
    pick = rng.integers(0, uniq.size, size=uniq.size)
    return np.concatenate([members[g] for g in pick])


def paired_group_bootstrap(stat, groups: np.ndarray, draws: int = DRAWS, seed: int = SEED) -> dict:
    """`stat(idx)` maps resampled task indices to a scalar; returns the point estimate, the 95% percentile interval,
    the two-sided p-value of a zero value (2 * min(P(stat* <= 0), P(stat* >= 0)), floored at 1/draws) and the draws."""
    rng = np.random.default_rng(seed)
    n = np.asarray(groups).size
    point = float(stat(np.arange(n)))
    boot = np.array([float(stat(group_bootstrap_indices(groups, rng))) for _ in range(draws)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    p = max(2.0 * min(np.mean(boot <= 0.0), np.mean(boot >= 0.0)), 1.0 / draws)
    return {"point": point, "lo": float(lo), "hi": float(hi), "p_two_sided": float(min(p, 1.0)), "draws": int(draws),
            "groups": int(np.unique(groups).size), "tasks": int(n), "seed": int(seed)}


def sign_swap_test(paired_diffs: np.ndarray) -> dict:
    """Exact paired sign-swap (permutation) test of a zero mean difference over the paired units (e.g. seeds)."""
    x = np.asarray(paired_diffs, float)
    m = x.size
    signs = np.array(np.meshgrid(*[[-1, 1]] * m)).reshape(m, -1).T if m <= 12 else None
    if signs is None:
        raise ValueError("sign-swap test is exact only for <= 12 paired units")
    means = signs @ x / m
    observed = x.mean()
    p = float(np.mean(np.abs(means) >= abs(observed) - 1e-12))
    return {"mean": float(observed), "p_two_sided": p, "units": int(m)}


def auc(score: np.ndarray, label: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney, ties count 1/2); NaN when one class is empty."""
    score, label = np.asarray(score, float), np.asarray(label).astype(bool)
    pos, neg = score[label], score[~label]
    if pos.size == 0 or neg.size == 0:
        return float("nan")
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(order.size)
    ranks[order] = np.arange(1, order.size + 1)
    # average ranks for ties
    s = np.concatenate([pos, neg])
    for v in np.unique(s):
        tie = s == v
        if tie.sum() > 1:
            ranks[tie] = ranks[tie].mean()
    return float((ranks[: pos.size].sum() - pos.size * (pos.size + 1) / 2) / (pos.size * neg.size))


def log_loss(p: np.ndarray, y: np.ndarray, eps: float = 1e-12) -> float:
    p, y = np.clip(np.asarray(p, float), eps, 1 - eps), np.asarray(y, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    """Expected calibration error with equal-width probability bins (textbook chapter 4 / lecture 3)."""
    p, y = np.asarray(p, float), np.asarray(y, float)
    edges = np.linspace(0, 1, bins + 1)
    out = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi) if hi < 1 else (p >= lo) & (p <= hi)
        if m.any():
            out += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(out)


def fmt(r: dict, scale: float = 1.0, digits: int = 2, pval: bool = True) -> str:
    s = f"{r['point'] * scale:.{digits}f} [{r['lo'] * scale:.{digits}f}, {r['hi'] * scale:.{digits}f}]"
    return s + (f" p-val={r['p_two_sided']:.4g}" if pval else "")
