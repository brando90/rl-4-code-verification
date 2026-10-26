"""TLDR: Experiment 19 analysis (zero model calls): on the 11-system VeriBench V1 panel, which SCSC factors and task features explain and predict held-out (validation-split) strict and harsh success (E1-E3), and does an item response theory (IRT) forecast pick the prompts on which experiment 13's start policy gives mixed strict groups, the precondition for an IRT-selected RL prompt pool (G1); --synthetic runs the same pipeline on generated data."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import multiprocessing as mp
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.special import expit, logit
from scipy.stats import kendalltau, pearsonr, rankdata, spearmanr

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for _p in (REPO / "src", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import data_e19 as D  # noqa: E402
import features_e19 as FE  # noqa: E402
import irt_e19 as irt  # noqa: E402

EXPERIMENT = "19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013"
SEED = 20261020
BOOT = 10000  # evaluation bootstraps over validation task groups (fitted models held fixed)
BOOT_REFIT = 500  # refit bootstraps over train task groups for the explanatory coefficients (E2b)
BOOT_ITEM = 1000  # item-group bootstraps for the descriptive item-level correlations (E3b)
SLOPE_SD_GRID = (0.25, 0.5, 1.0)
SIGMA_E_GRID = (0.5, 1.0, 2.0, 4.0)
CV_FOLDS = 5
AUC_GATE = 0.70  # experiment 13 PROTOCOL.md section 4, gate F2 (protocol-defined threshold)
TOP_FRACTION = 0.25
G = 8
CLIP = 1e-6
N_CATS = D.N_FSC_CATS
INPUT_FILES = {"e12_input_manifest": D.E12_MANIFEST, "start_policy": D.START_POLICY_FILE, "a6_receipt": D.E13_A6,
               "task_features": D.FEATURES, "rc_rows": D.RC_ROWS, "split_manifest": D.E08 / "split/vbv1_split_manifest.csv",
               "train_ids": D.E08 / "split/vbv1_train_task_ids.txt", "validation_ids": D.E08 / "split/vbv1_validation_task_ids.txt",
               "test_ids_guard_only": D.E08 / "split/vbv1_test_task_ids.txt"}


# ------------------------------------------------------------------------------------------------ small utilities


def stable_hash(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest()[:15], 16)


def logloss(y: np.ndarray, p: np.ndarray) -> np.ndarray:
    p = np.clip(p, CLIP, 1 - CLIP)
    return -(y * np.log(p) + (1 - y) * np.log1p(-p))


def auc(score: np.ndarray, y: np.ndarray) -> float:
    """Mann-Whitney area under the ROC curve with ties counted one half; NaN if a class is empty."""
    pos, neg = int(y.sum()), int(len(y) - y.sum())
    if pos == 0 or neg == 0:
        return float("nan")
    r = rankdata(score)
    return float((r[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))


def corr3(x: np.ndarray, y: np.ndarray) -> dict:
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return {"pearson": None, "spearman": None, "kendall": None, "n": int(len(x))}
    return {"pearson": float(pearsonr(x, y)[0]), "spearman": float(spearmanr(x, y)[0]),
            "kendall": float(kendalltau(x, y)[0]), "n": int(len(x))}


def ci(draws: np.ndarray) -> list[float] | None:
    draws = draws[np.isfinite(draws)]
    if len(draws) == 0:
        return None
    return [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]


def p_two_sided(draws: np.ndarray) -> float | None:
    """Percentile-bootstrap two-sided p-value for a zero difference: 2 * min(P(d* <= 0), P(d* >= 0)), floored at 1/B."""
    draws = draws[np.isfinite(draws)]
    if len(draws) == 0:
        return None
    return float(min(1.0, max(1.0 / len(draws), 2.0 * min(np.mean(draws <= 0), np.mean(draws >= 0)))))


def contrast(est: float, draws: np.ndarray) -> dict:
    return {"estimate": float(est), "ci95": ci(draws), "p_two_sided": p_two_sided(draws)}


def group_index(tasks: list[str], group: dict[str, str]) -> tuple[list[np.ndarray], list[str]]:
    """Task positions per D-013 group (near-duplicate and safe/vulnerable pairs share a group): the bootstrap unit."""
    by: dict[str, list[int]] = {}
    for i, t in enumerate(tasks):
        by.setdefault(group[t], []).append(i)
    keys = sorted(by)
    return [np.array(by[k]) for k in keys], keys


def boot_indices(groups: list[np.ndarray], rng: np.random.Generator) -> np.ndarray:
    pick = rng.integers(0, len(groups), size=len(groups))
    return np.concatenate([groups[g] for g in pick])


def pool_map(fn, jobs: list, workers: int) -> list:
    if workers > 1 and len(jobs) > 1:
        with mp.get_context("spawn").Pool(min(workers, len(jobs))) as pool:
            return pool.map(fn, jobs, chunksize=1)
    return [fn(j) for j in jobs]


# ------------------------------------------------------------------------------------------------ data


def load_real(require_pins: bool = True) -> dict:
    split = D.load_split()
    pins = json.loads(D.PINS_FILE.read_text())["sha256"] if D.PINS_FILE.exists() else None
    if require_pins and pins is None:
        raise RuntimeError("input_pins_e19.json is missing: the locked run needs pinned inputs")
    digests = {k: D.sha256_file(p) for k, p in INPUT_FILES.items()}
    if pins is not None:
        for k in INPUT_FILES:
            if pins.get(k) != digests[k]:
                raise RuntimeError(f"input hash mismatch for {k}")
    feats = D.load_features(split)
    train_mask = np.array([i < len(split.train) for i in range(len(split.tasks))])
    X, names = FE.design_matrix(feats, train_mask)
    panel, sens_panel = D.load_panel(split), D.load_panel(split, zero_without_call_missing=False)
    gold_info = D.attach_gold_target(panel, split)
    D.attach_gold_target(sens_panel, split)
    return {"split": split, "panel": panel, "sens_panel": sens_panel, "gold_info": gold_info,
            "rc": D.load_rc(split), "start": D.load_start_policy(split), "a6": D.load_a6_rate(), "X": X,
            "feature_names": names, "digests": digests, "synthetic": False}


def synthetic(seed: int, n_sys: int = 11, n_train: int = 120, n_val: int = 60) -> dict:
    """Generated stand-in with the real structure: two correlated skills, features that shift intercepts, a weak extra
    person whose 8-sample counts play the start policy. Used for tests and timing only, never a result."""
    rng = np.random.default_rng(seed)
    n_tasks = n_train + n_val
    tasks = [f"t{j:04d}" for j in range(n_tasks)]
    group = {t: f"g{j // 2:04d}" for j, t in enumerate(tasks)}
    split = D.Split(tasks[:n_train], tasks[n_train:], group, frozenset())
    P = 4
    Z = rng.normal(size=(n_tasks, P))
    w = np.array([-0.8, 0.5, 0.0, 0.3])
    d = Z @ w + rng.normal(0, 1.0, n_tasks) - 0.5
    a = np.exp(rng.normal(0.3, 0.4, n_tasks))
    th = rng.multivariate_normal([0, 0], [[1, 0.7], [0.7, 1]], size=n_sys)
    strict = (rng.random((n_sys, n_tasks)) < expit(a * th[:, [0]] + d)).astype(float)
    b = np.exp(rng.normal(0, 0.3, n_tasks))
    cuts = np.sort(rng.normal(1.0, 1.2, (n_tasks, N_CATS - 1)), axis=1)[:, ::-1]
    cum = expit(b[None, :, None] * th[:, 1][:, None, None] + cuts[None])
    fcat = (rng.random((n_sys, n_tasks))[:, :, None] < cum).sum(2).astype(float)
    fsc = np.choose(fcat.astype(int), [0.0, 0.3, 0.7, 0.9, 1.0])
    mask = (rng.random((n_sys, n_tasks)) > 0.05).astype(float)
    harsh = strict * (fcat == N_CATS - 1)
    smooth = (strict * fsc) ** (1 / 3)
    panel = D.Panel([f"s{i}" for i in range(n_sys)], tasks, n_train, strict * mask, harsh * mask, smooth * mask,
                    fsc * mask, fcat * mask, mask, {})
    compiles = np.maximum(strict, (rng.random((n_sys, n_tasks)) < expit(th[:, [0]] + d + 1.0)).astype(float))
    gmask = mask * (rng.random((n_sys, n_tasks)) > 0.1)
    panel.gold, panel.gold_mask = compiles * gmask, gmask
    p0 = expit(a * -1.6 + d)
    k = rng.binomial(G, p0[n_train:]).astype(float)
    start = D.StartPolicy(tasks[n_train:], k, np.full(n_val, float(G)), np.zeros(n_val), np.zeros(n_val))
    a6_k = int(rng.binomial(G * 64, float(np.mean(p0[:n_train]))))
    rc = {"RC_tests": np.where(strict > 0, rng.random((n_sys, n_tasks)), np.nan),
          "RC_pbt": np.full((n_sys, n_tasks), np.nan),
          "RC_fspecs": np.where(strict > 0, (rng.random((n_sys, n_tasks)) < 0.7).astype(float), np.nan)}
    Zs = (Z - Z[:n_train].mean(0)) / Z[:n_train].std(0)
    return {"split": split, "panel": panel, "sens_panel": panel, "rc": rc, "start": start, "gold_info": {"synthetic": True},
            "a6": {"successes": a6_k, "measured": G * 64, "missing": 0, "declared": G * 64, "task_count": 64,
                   "rate": max(a6_k, 1) / (G * 64), "bounds": [max(a6_k, 1) / (G * 64), min(a6_k + 8, G * 64) / (G * 64)]},
            "X": np.column_stack([np.ones(n_tasks), Zs]), "feature_names": ["intercept"] + [f"x{i}" for i in range(P)],
            "digests": {}, "synthetic": True, "truth": {"w": w.tolist(), "rho": 0.7}}


def ri(n: int) -> np.ndarray:
    return irt.random_intercept(n)


TARGETS = ("strict", "harsh", "gold")  # gold = VeriBench 111 strict gold-check pass@1 (tests + PBTs)
TWO_SKILL_TARGETS = ("strict", "harsh")


def target_arrays(P, target: str) -> tuple[np.ndarray, np.ndarray]:
    """Responses and observation mask for a target; gold has its own missingness (VeriBench 111 rules)."""
    if target == "gold":
        return P.gold, P.gold_mask
    return getattr(P, target), P.mask


# ------------------------------------------------------------------------------------------------ R0: regularization


def cell_folds(systems: list[str], tasks: list[str], group: dict[str, str]) -> np.ndarray:
    """Fold of every (system, train task) cell, by a hash of the system and the task's D-013 group."""
    return np.array([[stable_hash(f"{s}|{group[t]}") % CV_FOLDS for t in tasks] for s in systems])


def _cv_worker(args):
    y, m, X, slope_sd, sigma_e, folds, k = args
    m_in = m * (folds != k)
    f = irt.fit_2pl(y, m_in, X=X, sigma_e=sigma_e, slope_sd=slope_sd, check=None)
    a, d = irt.item_params(f)
    p = irt.predictive_1d(a, d, irt.posterior_1d(a, d, y, m_in))
    held = m * (folds == k)
    return float((logloss(y, p) * held).sum()), float(held.sum()), bool(f["converged"])


def select_regularization(data: dict, workers: int) -> dict:
    """R0: choose (slope prior SD, intercept residual SD) for the random-intercept and the explanatory 2PL by grouped
    5-fold cell-level cross-validation on train-split strict responses only (held-out cells of seen items and seen
    systems, the regime E1 and G1 predict in)."""
    P = data["panel"]
    n_tr = P.n_train
    y, m = P.strict[:, :n_tr], P.mask[:, :n_tr]
    folds = cell_folds(P.systems, data["split"].train, data["split"].group)
    models = {"random_intercept": ri(n_tr), "explanatory": data["X"][:n_tr]}
    grid = list(itertools.product(SLOPE_SD_GRID, SIGMA_E_GRID))
    jobs, keys = [], []
    for name, X in models.items():
        for sa, se in grid:
            for k in range(CV_FOLDS):
                jobs.append((y, m, X, sa, se, folds, k))
                keys.append((name, sa, se))
    out = pool_map(_cv_worker, jobs, workers)
    agg: dict = {}
    for key, (ll, n, conv) in zip(keys, out):
        a = agg.setdefault(key, [0.0, 0.0, 0])
        a[0] += ll
        a[1] += n
        a[2] += int(conv)
    res = {"criterion": "mean held-out train-cell log loss, 5 folds by hash(system | group)", "grid": {}, "chosen": {}}
    for name in models:
        scores = {(sa, se): agg[(name, sa, se)][0] / agg[(name, sa, se)][1] for sa, se in grid}
        res["grid"][name] = [{"slope_sd": sa, "sigma_e": se, "cv_logloss": scores[(sa, se)],
                              "folds_converged": agg[(name, sa, se)][2]} for sa, se in grid]
        best = min(grid, key=lambda g: (scores[g], -g[1], -g[0]))
        res["chosen"][name] = {"slope_sd": best[0], "sigma_e": best[1], "cv_logloss": scores[best]}
    return res


# ------------------------------------------------------------------------------------------------ E2: features


def _boot_refit_worker(args):
    seed, y, m, X, reg, groups = args
    rng = np.random.default_rng(seed)
    idx = boot_indices(groups, rng)
    f = irt.fit_2pl(y[:, idx], m[:, idx], X=X[idx], sigma_e=reg["sigma_e"], slope_sd=reg["slope_sd"], check=None)
    return irt.coefficients(f), bool(f["converged"])


def explanatory_coefficients(data: dict, reg: dict, target: str, n_boot: int, workers: int) -> dict:
    """E2b: explanatory 2PL on all train items; coefficients in logit-intercept units per SD of the feature (positive =
    easier), train-group refit-bootstrap 95% intervals, and the share of intercept variance the features explain."""
    P = data["panel"]
    n_tr = P.n_train
    ya, ma = target_arrays(P, target)
    y, m, X = ya[:, :n_tr], ma[:, :n_tr], data["X"][:n_tr]
    f = irt.fit_2pl(y, m, X=X, sigma_e=reg["sigma_e"], slope_sd=reg["slope_sd"])
    a, d = irt.item_params(f)
    w = irt.coefficients(f)
    e = d - X @ w
    groups, _ = group_index(data["split"].train, data["split"].group)
    ss = np.random.SeedSequence(SEED + 1 + TARGETS.index(target))
    jobs = [(int(s.generate_state(1)[0]), y, m, X, reg, groups) for s in ss.spawn(n_boot)]
    out = pool_map(_boot_refit_worker, jobs, workers)
    W = np.array([o[0] for o in out]) if out else np.zeros((0, len(w)))
    rows = [{"feature": name, "coef": float(w[k]), "ci95": ci(W[:, k]) if len(W) else None,
             "p_two_sided": p_two_sided(W[:, k]) if len(W) else None} for k, name in enumerate(data["feature_names"])]
    return {"target": target, "regularization": reg, "converged": f["converged"], "max_abs_grad": f["max_abs_grad"],
            "check_grid_max_abs_grad": f["check_grid_max_abs_grad"], "coefficients": rows,
            "intercept_variance_explained": float(1 - np.var(e) / np.var(d)), "boot_draws": n_boot,
            "boot_converged": int(sum(o[1] for o in out)),
            "boot_unit": "train task groups (D-013 group_id), refit each draw on the fitting grid only"}


def new_task_heldout(data: dict, regs: dict, target: str, groups, rng) -> dict:
    """E2c: validation tasks treated as unseen (no system's responses on them used): abilities from train responses;
    validation items predicted from features (explanatory fit) or from the random-intercept population (no features)."""
    P = data["panel"]
    n_tr = P.n_train
    (y, m), X = target_arrays(P, target), data["X"]
    n_val = y.shape[1] - n_tr
    rx, r0 = regs["explanatory"], regs["random_intercept"]
    f_x = irt.fit_2pl(y[:, :n_tr], m[:, :n_tr], X=X[:n_tr], sigma_e=rx["sigma_e"], slope_sd=rx["slope_sd"])
    f_0 = irt.fit_2pl(y[:, :n_tr], m[:, :n_tr], X=ri(n_tr), sigma_e=r0["sigma_e"], slope_sd=r0["slope_sd"])
    def pred(f, Xn):
        a, d = irt.item_params(f)
        return irt.posterior_1d(a, d, y[:, :n_tr], m[:, :n_tr]) @ irt.new_item_curves(f, Xn, n_val).T
    p_x, p_0 = pred(f_x, X[n_tr:]), pred(f_0, ri(n_val))
    yv, mv = y[:, n_tr:], m[:, n_tr:]
    feat, nofeat, cnt = (logloss(yv, p_x) * mv).sum(0), (logloss(yv, p_0) * mv).sum(0), mv.sum(0)
    diff = np.empty(BOOT)
    for b in range(BOOT):
        idx = boot_indices(groups, rng)
        diff[b] = (nofeat[idx].sum() - feat[idx].sum()) / cnt[idx].sum()
    return {"mean_logloss_features": float(feat.sum() / cnt.sum()), "mean_logloss_no_features": float(nofeat.sum() / cnt.sum()),
            "nofeat_minus_feat": contrast((nofeat.sum() - feat.sum()) / cnt.sum(), diff), "cells": int(cnt.sum()),
            "converged": [f_x["converged"], f_0["converged"]]}


# ------------------------------------------------------------------------------------------------ E1: leave one system out


def _loso_worker(args):
    i, arrays, n_tr, reg = args
    strict, harsh, fcat, mask, gold, gold_mask = arrays
    n_sys, n_tasks = strict.shape
    others = np.array([k for k in range(n_sys) if k != i])
    val = np.arange(n_tr, n_tasks)
    obs = mask[i].copy()
    obs[n_tr:] = 0.0  # the held-out system is observed on train tasks only
    out = {"system": i, "fits": {}}
    for name, y, mk in (("m2_strict", strict, mask), ("m2_harsh", harsh, mask), ("m2_gold", gold, gold_mask)):
        f = irt.fit_2pl(y[others], mk[others], X=ri(n_tasks), sigma_e=reg["sigma_e"], slope_sd=reg["slope_sd"])
        a, d = irt.item_params(f)
        ob = mk[i].copy()
        ob[n_tr:] = 0.0
        post = irt.posterior_1d(a, d, y[i:i + 1], ob[None, :])
        out[name] = irt.predictive_1d(a[val], d[val], post)[0]
        out["fits"][name] = {k: f[k] for k in ("converged", "max_abs_grad", "check_grid_max_abs_grad", "nit")}
        out["fits"][name]["endpoint_mass"] = float(irt.endpoint_mass(post)[0])
    for name, tied in (("m3", False), ("m3t", True)):
        kw = dict(tied=tied, slope_sd=reg["slope_sd"], sigma_e=reg["sigma_e"])
        f = irt.fit_two_skill(strict[others], mask[others], fcat[others], mask[others], N_CATS, **kw)
        refit = False
        if not tied and not f["converged"]:  # PROTOCOL.md section 5: one refit on 801 nodes per axis
            f = irt.fit_two_skill(strict[others], mask[others], fcat[others], mask[others], N_CATS,
                                  grid=irt.Grid(-9.0, 9.0, 801), **kw)
            refit = True
        pr = irt.two_skill_predict(f, strict[i:i + 1], obs[None, :], fcat[i:i + 1], obs[None, :], val)
        out[f"{name}_strict"], out[f"{name}_harsh"], out[f"{name}_catprobs"] = pr["strict"][0], pr["both"][0], pr["cat_probs"][0]
        out["fits"][name] = {k: f[k] for k in ("converged", "max_abs_grad", "check_grid_max_abs_grad", "nit", "rho")}
        out["fits"][name].update(endpoint_mass=pr["endpoint_mass"], refit_801=refit)
    return out


def loso(data: dict, reg: dict, workers: int) -> dict:
    P = data["panel"]
    arrays = (P.strict, P.harsh, P.fcat, P.mask, P.gold, P.gold_mask)
    res = pool_map(_loso_worker, [(i, arrays, P.n_train, reg) for i in range(len(P.systems))], workers)
    return {r["system"]: r for r in res}


def e1_predictions(data: dict, lo: dict) -> dict:
    """Validation-cell predictions per held-out system and method; M0 and M1 are the non-IRT baselines."""
    P = data["panel"]
    n_sys, n_tasks = P.strict.shape
    n_tr = P.n_train
    out = {}
    for target in TARGETS:
        y, mk = target_arrays(P, target)
        methods = ("m0", "m1", "m2", "m3", "m3t") if target in TWO_SKILL_TARGETS else ("m0", "m1", "m2")
        pr = {k: np.zeros((n_sys, n_tasks - n_tr)) for k in methods}
        for i in range(n_sys):
            others = [k for k in range(n_sys) if k != i]
            tr = mk[i, :n_tr] > 0
            rate_i = (y[i, :n_tr][tr].sum() + 0.5) / (tr.sum() + 1.0)
            mo = mk[others]
            r_j = ((y[others] * mo).sum(0) + 0.5) / (mo.sum(0) + 1.0)
            r_bar = float((y[others] * mo).sum() / mo.sum())
            pr["m0"][i] = rate_i
            pr["m1"][i] = expit(logit(rate_i) + logit(r_j[n_tr:]) - logit(r_bar))
            for k in methods[2:]:
                pr[k][i] = lo[i][f"{k}_{target}"]
        out[target] = pr
    return out


def e1_cells(data: dict, preds: dict, groups, rng) -> dict:
    P = data["panel"]
    n_tr = P.n_train
    res = {}
    for target, pr in preds.items():
        ya, ma = target_arrays(P, target)
        yv, mv = ya[:, n_tr:], ma[:, n_tr:]
        cnt = mv.sum(0)
        per_task = {k: (logloss(yv, p) * mv).sum(0) for k, p in pr.items()}
        means = {k: float(v.sum() / cnt.sum()) for k, v in per_task.items()}
        pairs = {"m1_minus_m2": ("m1", "m2"), "m0_minus_m2": ("m0", "m2"), "m2_minus_m3": ("m2", "m3"),
                 "m0_minus_m1": ("m0", "m1"), "m3t_minus_m3": ("m3t", "m3"), "m1_minus_m3": ("m1", "m3")}
        pairs = {c: uv for c, uv in pairs.items() if uv[0] in pr and uv[1] in pr}
        draws = {c: np.empty(BOOT) for c in pairs}
        for b in range(BOOT):
            idx = boot_indices(groups, rng)
            n = cnt[idx].sum()
            for c, (u, v) in pairs.items():
                draws[c][b] = (per_task[u][idx].sum() - per_task[v][idx].sum()) / n
        res[target] = {
            "cells": int(cnt.sum()), "positives": int((yv * mv).sum()), "mean_logloss": means,
            "mean_brier": {k: float((((p - yv) ** 2) * mv).sum() / cnt.sum()) for k, p in pr.items()},
            "contrasts": {c: contrast(means[u] - means[v], draws[c]) for c, (u, v) in pairs.items()},
            "per_system_logloss": {P.systems[i]: {k: float((logloss(yv[i], p[i]) * mv[i]).sum() / max(mv[i].sum(), 1))
                                                  for k, p in pr.items()} for i in range(len(P.systems))},
        }
    return res


def e1_system_level(data: dict, preds: dict, groups, rng) -> dict:
    """E1c: forecasts of each held-out system's validation pass rate from its train data; absolute agreement (MAE,
    mean bias with both means) and Pearson/Spearman/Kendall across the 11 systems."""
    P = data["panel"]
    n_sys, n_tr = len(P.systems), P.n_train
    out = {}
    for target in TARGETS:
        y, m = target_arrays(P, target)
        irt_keys = ("m2", "m3") if target in TWO_SKILL_TARGETS else ("m2",)
        tr_rate = np.array([y[i, :n_tr][m[i, :n_tr] > 0].mean() for i in range(n_sys)])
        tr_smooth = np.array([P.smooth[i, :n_tr][P.mask[i, :n_tr] > 0].mean() for i in range(n_sys)])

        def forecasts(vidx):
            yv, mv = y[:, n_tr:][:, vidx], m[:, n_tr:][:, vidx]
            obs = (yv * mv).sum(1) / np.maximum(mv.sum(1), 1)
            fc = {"own_train_rate": tr_rate.copy(), "smooth_raw": tr_smooth.copy()}
            for name, xvar in (("rate_calibrated", tr_rate), ("smooth_calibrated", tr_smooth)):
                v = np.empty(n_sys)
                for i in range(n_sys):
                    o = np.arange(n_sys) != i
                    coef = np.linalg.lstsq(np.column_stack([np.ones(o.sum()), xvar[o]]), obs[o], rcond=None)[0]
                    v[i] = coef[0] + coef[1] * xvar[i]
                fc[name] = v
            for k in irt_keys:
                fc[f"irt_{k}"] = (preds[target][k][:, vidx] * mv).sum(1) / np.maximum(mv.sum(1), 1)
            return fc, obs

        fc, obs = forecasts(np.arange(len(data["split"].validation)))
        mae = {k: float(np.mean(np.abs(v - obs))) for k, v in fc.items()}
        pairs = [("rate_calibrated", "smooth_calibrated"), ("own_train_rate", "irt_m2"), ("rate_calibrated", "irt_m2"),
                 ("smooth_calibrated", "irt_m2")] + ([("irt_m2", "irt_m3")] if "m3" in irt_keys else [])
        draws = {f"{u}_minus_{v}": np.empty(BOOT) for u, v in pairs}
        for b in range(BOOT):
            fcb, obsb = forecasts(boot_indices(groups, rng))
            for u, v in pairs:
                draws[f"{u}_minus_{v}"][b] = np.mean(np.abs(fcb[u] - obsb)) - np.mean(np.abs(fcb[v] - obsb))
        out[target] = {
            "systems": P.systems, "observed_validation_rate": obs.tolist(), "forecasts": {k: v.tolist() for k, v in fc.items()},
            "mae": mae, "mean_bias_forecast_minus_observed": {k: float(np.mean(v - obs)) for k, v in fc.items()},
            "mean_forecast": {k: float(np.mean(v)) for k, v in fc.items()}, "mean_observed": float(np.mean(obs)),
            "correlation_with_observed": {k: corr3(v, obs) for k, v in fc.items()},
            "mae_contrasts": {c: contrast(mae[c.split("_minus_")[0]] - mae[c.split("_minus_")[1]], d) for c, d in draws.items()},
            "interval_scope": "validation task groups resampled; fitted IRT parameters and train-split inputs held fixed; n = 11 systems",
        }
    return out


# ------------------------------------------------------------------------------------------------ E3: one skill or two


def e3_heldout(data: dict, lo: dict, groups, rng) -> dict:
    """E3a: per-cell held-out log predictive density of validation strict and FSC-category responses, untied vs tied."""
    P = data["panel"]
    n_tr = P.n_train
    mv = P.mask[:, n_tr:]
    per = {}
    for name in ("m3", "m3t"):
        ll = np.zeros(mv.shape)
        for i in range(len(P.systems)):
            ps = np.clip(lo[i][f"{name}_strict"], CLIP, 1 - CLIP)
            ys = P.strict[i, n_tr:]
            cp = np.clip(lo[i][f"{name}_catprobs"], CLIP, 1.0)
            c = P.fcat[i, n_tr:].astype(int)
            ll[i] = ys * np.log(ps) + (1 - ys) * np.log1p(-ps) + np.log(cp[np.arange(len(c)), c])
        per[name] = (ll * mv).sum(0)
    cnt = mv.sum(0)
    diff = np.empty(BOOT)
    for b in range(BOOT):
        idx = boot_indices(groups, rng)
        diff[b] = (per["m3"][idx].sum() - per["m3t"][idx].sum()) / cnt[idx].sum()
    rhos = [lo[i]["fits"]["m3"]["rho"] for i in range(len(P.systems))]
    return {"mean_log_density": {k: float(v.sum() / cnt.sum()) for k, v in per.items()},
            "untied_minus_tied": contrast((per["m3"].sum() - per["m3t"].sum()) / cnt.sum(), diff),
            "rho_by_fold": rhos, "rho_median": float(np.median(rhos)), "rho_range": [float(min(rhos)), float(max(rhos))]}


def e3_item_level(data: dict, reg: dict, rng) -> dict:
    """E3b (descriptive): do the same tasks look easy on strict success, on FSC = 1 and on the gold reference's
    obligations (RC_fspecs = 1)? Correlations of fitted random-intercept 2PL intercepts, item-group bootstrap intervals."""
    P = data["panel"]
    m = P.mask
    n = m.shape[1]
    rcf = data["rc"]["RC_fspecs"]
    rc_m = np.isfinite(rcf).astype(float)
    rc_y = np.where(np.isfinite(rcf), (rcf == 1.0).astype(float), 0.0)
    kw = dict(X=ri(n), sigma_e=reg["sigma_e"], slope_sd=reg["slope_sd"])
    fits = {"strict": irt.fit_2pl(P.strict, m, **kw), "fsc_eq_1": irt.fit_2pl((P.fsc == 1.0) * m, m, **kw),
            "rc_fspecs_eq_1": irt.fit_2pl(rc_y, rc_m, **kw)}
    d = {k: irt.item_params(f)[1] for k, f in fits.items()}
    enough = rc_m.sum(0) >= 3
    groups, _ = group_index(data["split"].tasks, data["split"].group)
    out = {"converged": {k: f["converged"] for k, f in fits.items()}, "items_with_3plus_rc_cells": int(enough.sum()),
           "rc_measured_cells": int(rc_m.sum())}
    for u, v, keep in (("strict", "fsc_eq_1", np.ones(n, bool)), ("strict", "rc_fspecs_eq_1", enough),
                       ("fsc_eq_1", "rc_fspecs_eq_1", enough)):
        est = corr3(d[u][keep], d[v][keep])
        draws = {k: np.full(BOOT_ITEM, np.nan) for k in ("pearson", "spearman", "kendall")}
        for b in range(BOOT_ITEM):
            idx = boot_indices(groups, rng)
            idx = idx[keep[idx]]
            c = corr3(d[u][idx], d[v][idx])
            for k in draws:
                draws[k][b] = np.nan if c[k] is None else c[k]
        out[f"{u}__{v}"] = {**est, **{f"{k}_ci95": ci(draws[k]) for k in draws}}
    return out


# ------------------------------------------------------------------------------------------------ G1: prompt pool


def g1_prompt_pool(data: dict, regs: dict, groups, rng) -> dict:
    """G1: forecast which validation prompts give experiment 13's start policy a mixed strict group of 8, using only
    other systems' outcomes and task content, with the start policy's ability set from its train-split A6 rate."""
    P = data["panel"]
    n_tr, n_all = P.n_train, P.strict.shape[1]
    val = np.arange(n_tr, n_all)
    sp = data["start"]
    k = sp.k
    mixed = ((k >= 1) & (k <= G - 1)).astype(float)
    solvable = (k >= 1).astype(float)
    rate = data["a6"]["rate"]
    r0, rx = regs["random_intercept"], regs["explanatory"]
    preds, fits = {}, {}

    def fit_and_place(name, y, m, X, reg, train_items):
        f = irt.fit_2pl(y, m, X=X, sigma_e=reg["sigma_e"], slope_sd=reg["slope_sd"]) if X is not None else irt.fit_2pl(y, m)
        a, d = irt.item_params(f)
        th = irt.calibrate_theta(a[train_items], d[train_items], rate)
        fits[name] = {"converged": f["converged"], "max_abs_grad": f["max_abs_grad"],
                      "check_grid_max_abs_grad": f["check_grid_max_abs_grad"], "theta0": th}
        return f, a, d, th

    f, a, d, th0 = fit_and_place("irt_2pl", P.strict, P.mask, ri(n_all), r0, slice(0, n_tr))
    preds["irt_2pl"] = expit(a[val] * th0 + d[val])
    info = a[val] ** 2 * preds["irt_2pl"] * (1 - preds["irt_2pl"])
    _, ax, dx, thx = fit_and_place("irt_2pl_features", P.strict, P.mask, data["X"], rx, slice(0, n_tr))
    preds["irt_2pl_features"] = expit(ax[val] * thx + dx[val])
    ff, af, df, thf = fit_and_place("features_only", P.strict[:, :n_tr], P.mask[:, :n_tr], data["X"][:n_tr], rx, slice(0, n_tr))
    curves = irt.new_item_curves(ff, data["X"][n_tr:], len(val))
    gi = int(np.argmin(np.abs(irt.BASE.nodes - thf)))
    preds["features_only"] = curves[:, gi]
    fits["features_only"]["theta0_grid_node"] = float(irt.BASE.nodes[gi])
    mo = P.mask[:, val]
    heur = {"panel_strict_rate": ((P.strict[:, val] * mo).sum(0) + 0.5) / (mo.sum(0) + 1.0),
            "panel_mean_smooth": (P.smooth[:, val] * mo).sum(0) / np.maximum(mo.sum(0), 1)}
    scores = {**{f"q8_{n}": 1 - p**G - (1 - p) ** G for n, p in preds.items()}, **heur}
    n_val = len(val)
    tie = np.array([stable_hash(t) for t in sp.tasks], dtype=float) / 2.0**60

    def topk_share(score, idx):
        s = score[idx] + 1e-12 * tie[idx]
        sel = idx[np.argsort(-s, kind="stable")[: int(round(TOP_FRACTION * len(idx)))]]
        return float(mixed[sel].mean())

    def armc_share(idx):
        w = 0.5 / len(idx) + 0.5 * info[idx] / info[idx].sum()
        return float((w * mixed[idx]).sum())

    all_idx = np.arange(n_val)
    est = {"auc_mixed": {n: auc(s, mixed) for n, s in scores.items()},
           "auc_solvable": {n: auc(s, solvable) for n, s in {**preds, **heur}.items()},
           "topk_mixed_share": {n: topk_share(s, all_idx) for n, s in scores.items()},
           "uniform_mixed_share": float(mixed.mean()), "armc_mixed_share": armc_share(all_idx)}
    B = {"auc": {n: np.empty(BOOT) for n in scores}, "topk": {n: np.empty(BOOT) for n in scores},
         "uniform": np.empty(BOOT), "armc": np.empty(BOOT)}
    for b in range(BOOT):
        idx = boot_indices(groups, rng)
        for n, s in scores.items():
            B["auc"][n][b] = auc(s[idx], mixed[idx])
            B["topk"][n][b] = topk_share(s, idx)
        B["uniform"][b] = mixed[idx].mean()
        B["armc"][b] = armc_share(idx)
    prim = "q8_irt_2pl"
    res = {
        "n_tasks": n_val, "n_groups": len(groups), "mixed_tasks": int(mixed.sum()), "solvable_tasks": int(solvable.sum()),
        "a6_rate": rate, "fits": fits, "estimates": est, "auc_ci95": {n: ci(B["auc"][n]) for n in scores},
        "auc_primary_vs_gate": {"gate": AUC_GATE, "gate_source": "experiment 13 PROTOCOL.md section 4, F2 (protocol-defined)",
                                "estimate": est["auc_mixed"][prim], "ci95": ci(B["auc"][prim]),
                                "p_one_sided_le_gate": float(np.mean(B["auc"][prim] <= AUC_GATE)),
                                "p_test": "percentile bootstrap over validation task groups: share of draws <= 0.70"},
        "auc_contrasts": {f"{prim}_minus_{o}": contrast(est["auc_mixed"][prim] - est["auc_mixed"][o], B["auc"][prim] - B["auc"][o])
                          for o in scores if o != prim},
        "topk_ci95": {n: ci(B["topk"][n]) for n in scores},
        "topk_minus_uniform": {n: contrast(est["topk_mixed_share"][n] - est["uniform_mixed_share"], B["topk"][n] - B["uniform"])
                               for n in scores},
        "armc_minus_uniform": contrast(est["armc_mixed_share"] - est["uniform_mixed_share"], B["armc"] - B["uniform"]),
        "expected_mixed_groups_per_256_rollout_update_G8": {
            "uniform": 32 * est["uniform_mixed_share"], "topk_irt": 32 * est["topk_mixed_share"][prim],
            "armc": 32 * est["armc_mixed_share"]},
        "calibration": {
            "mean_predicted": {n: float(np.mean(p)) for n, p in preds.items()}, "mean_observed": float(k.sum() / sp.n.sum()),
            "mean_bias_predicted_minus_observed": {n: float(np.mean(p) - k.sum() / sp.n.sum()) for n, p in preds.items()},
            "binomial_logloss": {n: float(np.mean(-(k * np.log(np.clip(p, CLIP, 1)) + (G - k) * np.log(np.clip(1 - p, CLIP, 1))) / G))
                                 for n, p in {**preds, "constant_a6_rate": np.full(n_val, rate)}.items()},
            "correlation_p_vs_k_over_8": {n: corr3(p, k / G) for n, p in preds.items()}},
        "per_task": {"task_id": sp.tasks, "k": k.tolist(), **{f"p_{n}": p.tolist() for n, p in preds.items()},
                     **{n: v.tolist() for n, v in heur.items()}},
    }
    sens = {}
    for label, rate_b in (("a6_lower_bound", data["a6"]["bounds"][0]), ("a6_upper_bound", data["a6"]["bounds"][1])):
        t = irt.calibrate_theta(a[:n_tr], d[:n_tr], rate_b)
        p = expit(a[val] * t + d[val])
        sens[label] = {"rate": rate_b, "theta0": t, "auc_mixed": auc(1 - p**G - (1 - p) ** G, mixed)}
    SP = data["sens_panel"]
    fs = irt.fit_2pl(SP.strict, SP.mask, X=ri(n_all), sigma_e=r0["sigma_e"], slope_sd=r0["slope_sd"])
    a_s, d_s = irt.item_params(fs)
    t_s = irt.calibrate_theta(a_s[:n_tr], d_s[:n_tr], rate)
    p_s = expit(a_s[val] * t_s + d_s[val])
    sens["zero_without_call_as_failures"] = {"theta0": t_s, "converged": fs["converged"],
                                             "auc_mixed": auc(1 - p_s**G - (1 - p_s) ** G, mixed)}
    fw = irt.fit_2pl(P.strict, P.mask)  # experiment 14/15's weak priors
    a_w, d_w = irt.item_params(fw)
    t_w = irt.calibrate_theta(a_w[:n_tr], d_w[:n_tr], rate)
    p_w = expit(a_w[val] * t_w + d_w[val])
    sens["weak_priors_e14"] = {"theta0": t_w, "converged": fw["converged"], "auc_mixed": auc(1 - p_w**G - (1 - p_w) ** G, mixed)}
    res["sensitivity"] = sens
    res["primary_model"] = {"a": a.tolist(), "d": d.tolist(), "theta0": th0, "tasks": data["split"].tasks,
                            "regularization": r0}
    return res


# ------------------------------------------------------------------------------------------------ verdicts and gates


def verdicts(r: dict) -> dict:
    """The pre-registered decision rules of PROTOCOL.md section 4, applied mechanically."""
    def above(c):
        return c is not None and c.get("ci95") is not None and c["ci95"][0] > 0
    def below(c):
        return c is not None and c.get("ci95") is not None and c["ci95"][1] < 0
    out = {}
    for t in TARGETS:
        c = r["E1"][t]["contrasts"]
        out[f"E1_{t}_irt_beats_baselines"] = above(c["m1_minus_m2"]) and above(c["m0_minus_m2"])
        if t in TWO_SKILL_TARGETS:
            out[f"E1_{t}_fsc_skill_adds"] = above(c["m2_minus_m3"])
        s = r["E1_system"][t]["mae_contrasts"]["rate_calibrated_minus_smooth_calibrated"]
        out[f"E1_{t}_smooth_vs_rate"] = "smooth better" if above(s) else ("smooth worse" if below(s) else "no detectable difference")
        out[f"E2_{t}_features_predict_unseen_tasks"] = above(r["E2"]["new_task"][t]["nofeat_minus_feat"])
    out["E3_two_skills"] = above(r["E3"]["heldout"]["untied_minus_tied"])
    g = r["G1"]
    auc_p = g["auc_primary_vs_gate"]["estimate"]
    specific = all(above(g["auc_contrasts"][f"q8_irt_2pl_minus_{h}"]) for h in ("panel_strict_rate", "panel_mean_smooth"))
    heur_pass = any((g["estimates"]["auc_mixed"][h] or 0) >= AUC_GATE for h in ("panel_strict_rate", "panel_mean_smooth"))
    if auc_p is not None and auc_p >= AUC_GATE:
        out["G1"] = "PASS, IRT-SPECIFIC" if specific else "PASS, NOT IRT-SPECIFIC"
    else:
        out["G1"] = "FAIL FOR IRT, HEURISTIC PASSES" if heur_pass else "FAIL"
    return out


def gates(r: dict) -> dict:
    """Numerical gates (PROTOCOL.md section 5): every primary fit converged on its grid and its check grid."""
    fails = [f"E1 {s} {n}" for s, fs in r["E1_fits"].items() for n, f in fs.items() if not f["converged"]]
    fails += [f"G1 {n}" for n, f in r["G1"]["fits"].items() if not f["converged"]]
    fails += [f"E2 {t}" for t, c in r["E2"]["coefficients"].items() if not c["converged"]]
    fails += [f"E3b {k}" for k, v in r["E3"]["item_level"]["converged"].items() if not v]
    return {"all_primary_fits_converged": not fails, "failures": fails}


# ------------------------------------------------------------------------------------------------ driver


def to_jsonable(o):
    if isinstance(o, dict):
        return {str(k): to_jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return to_jsonable(o.tolist())
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def run(data: dict, *, workers: int, boot_refit: int) -> dict:
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    P = data["panel"]
    vgroups, _ = group_index(data["split"].validation, data["split"].group)
    r: dict = {"experiment": EXPERIMENT, "synthetic": data["synthetic"], "inputs": data["digests"],
               "settings": {"seed": SEED, "boot": BOOT, "boot_refit": boot_refit, "boot_item": BOOT_ITEM,
                            "slope_sd_grid": SLOPE_SD_GRID, "sigma_e_grid": SIGMA_E_GRID, "cv_folds": CV_FOLDS,
                            "auc_gate": AUC_GATE, "top_fraction": TOP_FRACTION, "G": G,
                            "fsc_categories": D.FSC_CATEGORY_EDGES, "zero_without_call": "missing (primary)",
                            "grids": {"one_skill": [irt.BASE.lo, irt.BASE.hi, irt.BASE.count],
                                      "two_skill": [irt.BASE2.lo, irt.BASE2.hi, irt.BASE2.count]}},
               "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                               "host": platform.node()},
               "panel": {"systems": P.systems, "n_train_tasks": P.n_train, "n_validation_tasks": P.strict.shape[1] - P.n_train,
                         "measured_cells": int(P.mask.sum()), "declared_cells": int(P.mask.size),
                         "gold_target": data["gold_info"], "gold_measured_cells": int(P.gold_mask.sum()),
                         "status_counts": P.status_counts}}
    reg = select_regularization(data, workers)
    r["R0_regularization"] = reg
    regs = reg["chosen"]
    r["E2"] = {"coefficients": {t: explanatory_coefficients(data, regs["explanatory"], t, boot_refit, workers)
                                for t in TARGETS},
               "new_task": {t: new_task_heldout(data, regs, t, vgroups, rng) for t in TARGETS}}
    lo = loso(data, regs["random_intercept"], workers)
    preds = e1_predictions(data, lo)
    r["E1"] = e1_cells(data, preds, vgroups, rng)
    r["E1_system"] = e1_system_level(data, preds, vgroups, rng)
    r["E1_fits"] = {P.systems[i]: lo[i]["fits"] for i in range(len(P.systems))}
    r["E3"] = {"heldout": e3_heldout(data, lo, vgroups, rng), "item_level": e3_item_level(data, regs["random_intercept"], rng)}
    r["G1"] = g1_prompt_pool(data, regs, vgroups, rng)
    r["verdicts"] = verdicts(r)
    r["gates"] = gates(r)
    r["wall_seconds"] = time.time() - t0
    return r


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--synthetic", type=int, default=None, help="seed for a generated stand-in (never a result)")
    ap.add_argument("--out", type=Path, default=HERE / "results")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--boot-refit", type=int, default=BOOT_REFIT)
    args = ap.parse_args()
    data = synthetic(args.synthetic) if args.synthetic is not None else load_real()
    r = to_jsonable(run(data, workers=args.workers, boot_refit=args.boot_refit))
    args.out.mkdir(parents=True, exist_ok=True)
    name = "analysis_e19_synthetic.json" if data["synthetic"] else "analysis_e19.json"
    (args.out / name).write_text(json.dumps(r, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"verdicts": r["verdicts"], "gates": r["gates"], "wall_seconds": r["wall_seconds"]}, indent=1))


if __name__ == "__main__":
    main()
