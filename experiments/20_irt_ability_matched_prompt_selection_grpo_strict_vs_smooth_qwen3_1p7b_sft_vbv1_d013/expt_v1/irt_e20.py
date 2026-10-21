"""TLDR: Experiment 20's item response theory (IRT) layer on top of experiment 19's irt_e19.py: binomial-count 2PL fits (random-intercept, explanatory with task features, and the 1PL) by marginal maximum a posteriori on fixed ability grids, grouped cell-level cross-validation to choose the priors, the pre-registered gate G0 (held-out active-group AUC, log loss against the Beta(1,1) population baseline, ECE, predicted-vs-observed active share, with the panel-rate and features-only alternatives), the start policy's EAP ability, a graded response model on the smooth reward with the 8 sample indices as pseudo-respondents, and the two-skill held-out comparison under experiment 19's convergence gate."""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.special import expit, logsumexp

HERE = Path(__file__).resolve().parent
E19 = HERE.parents[1] / "19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/expt_v1"
sys.path.insert(0, str(E19))
import irt_e19 as I  # noqa: E402

sys.path.insert(0, str(HERE))
from samplers_e20 import forecast_active  # noqa: E402
from stats_e20 import auc, ece, group_bootstrap_indices, log_loss  # noqa: E402

G = 8
GRID, CHECK = I.BASE, I.CHECK
SLOPE_GRID = (0.1, 0.25, 0.5, 1.0)
SIGMA_GRID = (0.25, 0.5, 1.0, 2.0, 4.0)
SEED = 20261021


# ----------------------------------------------------------------------------------------------------- count 2PL fits


def _fraction(k: np.ndarray, n: np.ndarray) -> np.ndarray:
    k, n = np.asarray(k, float), np.asarray(n, float)
    return np.divide(k, n, out=np.zeros_like(k), where=n > 0)


def fit_2pl_counts(k: np.ndarray, n: np.ndarray, *, X: np.ndarray | None = None, sigma_e: float | None = None,
                   slope_sd: float = 1.0, fixed_slope: bool = False, grid: I.Grid = GRID, check: I.Grid | None = CHECK,
                   maxiter: int = 20000) -> dict:
    """Marginal MAP 2PL for binomial counts: persons x items arrays of successes k and trials n (n = 0 is missing).
    experiment 19's objective is linear in the counts, so y = k/n with m = n reproduces the binomial likelihood exactly.
    fixed_slope=True fits the 1PL (every log slope held at 0)."""
    k, n = np.asarray(k, float), np.asarray(n, float)
    if k.shape != n.shape or np.any(n < 0) or np.any(k < 0) or np.any(k > n):
        raise ValueError("counts must satisfy 0 <= k <= n elementwise")
    if (X is None) != (sigma_e is None):
        raise ValueError("a design matrix and the residual scale sigma_e go together")
    y, m = _fraction(k, n), n
    n_per, n_items = y.shape
    tot = np.maximum(m.sum(0), 1.0)
    rate = np.clip((k.sum(0) + 0.5) / (tot + 1.0), 1e-3, 1 - 1e-3)
    d0 = np.log(rate) - np.log1p(-rate)
    w0 = np.zeros(0) if X is None else np.linalg.lstsq(X, d0, rcond=None)[0]
    if fixed_slope:
        def fun(z):
            x = np.concatenate([np.zeros(n_items), z])
            v, g = I.objective_2pl(x, y, m, X, sigma_e, slope_sd, grid)
            return v, g[n_items:]
        res = I._minimize(fun, np.concatenate([d0, w0]), maxiter)
        x_full = np.concatenate([np.zeros(n_items), res.x])
    else:
        def fun(x):
            return I.objective_2pl(x, y, m, X, sigma_e, slope_sd, grid)
        res = I._minimize(fun, np.concatenate([np.zeros(n_items), d0, w0]), maxiter)
        x_full = res.x
    value, grad = I.objective_2pl(x_full, y, m, X, sigma_e, slope_sd, grid)
    if fixed_slope:
        grad = grad[n_items:]
    max_grad = I.max_abs(grad)
    check_grad = None
    if check is not None:
        cg = I.objective_2pl(x_full, y, m, X, sigma_e, slope_sd, check)[1]
        check_grad = I.max_abs(cg[n_items:] if fixed_slope else cg)
    ok = bool(np.isfinite(value) and np.all(np.isfinite(x_full)) and max_grad <= I.GRAD_TOL
              and (check_grad is None or check_grad <= I.GRAD_TOL))
    return {"x": x_full, "n_items": int(n_items), "n_persons": int(n_per), "objective": float(value), "max_abs_grad": max_grad,
            "check_grid_max_abs_grad": check_grad, "converged": ok, "nit": int(res.nit), "X": X, "sigma_e": sigma_e,
            "slope_sd": slope_sd, "fixed_slope": fixed_slope}


def item_params(fitted: dict) -> tuple[np.ndarray, np.ndarray]:
    return I.item_params(fitted)


def posterior_theta(fitted: dict, k: np.ndarray, n: np.ndarray, grid: I.Grid = GRID) -> np.ndarray:
    """Posterior node weights (persons x Q) of abilities given the counts under the fitted item parameters."""
    a, d = item_params(fitted)
    return I.posterior_1d(a, d, _fraction(k, n), np.asarray(n, float), grid)


def eap(post: np.ndarray, grid: I.Grid = GRID) -> tuple[np.ndarray, np.ndarray]:
    return I.eap(post, grid)


def predictive_p(fitted: dict, post: np.ndarray, grid: I.Grid = GRID) -> np.ndarray:
    a, d = item_params(fitted)
    return I.predictive_1d(a, d, post, grid)


def predictive_active(curves: np.ndarray, post_row: np.ndarray, g: int = G) -> np.ndarray:
    """Posterior-predictive P(active group) for items with success curves `curves` (items x Q) under one person's
    posterior node weights: E_theta[1 - p^g - (1 - p)^g]."""
    return forecast_active(curves, g) @ post_row


def item_curves(fitted: dict, idx: np.ndarray, grid: I.Grid = GRID) -> np.ndarray:
    a, d = item_params(fitted)
    return expit(a[idx, None] * grid.nodes[None, :] + d[idx, None])


# ----------------------------------------------------------------------------------------- grouped cross-validation


def cell_folds(n_persons: int, item_groups: np.ndarray, n_folds: int = 5, seed: int = SEED) -> np.ndarray:
    """Fold id per (person, item) cell from a hash of (seed, person, task group), as experiment 19's R0."""
    out = np.zeros((n_persons, len(item_groups)), int)
    for i in range(n_persons):
        for j, g in enumerate(item_groups):
            h = hashlib.sha256(f"{seed}|{i}|{g}".encode()).digest()
            out[i, j] = int.from_bytes(h[:4], "big") % n_folds
    return out


def heldout_log_loss(k: np.ndarray, n: np.ndarray, folds: np.ndarray, *, X, sigma_e, slope_sd, fixed_slope=False,
                     grid: I.Grid = GRID) -> dict:
    """Mean per-trial binomial log loss on held-out cells over the folds (fits on the remaining cells)."""
    k, n = np.asarray(k, float), np.asarray(n, float)
    loss, trials, converged = 0.0, 0.0, []
    for f in np.unique(folds):
        held = folds == f
        fit = fit_2pl_counts(k * ~held, n * ~held, X=X, sigma_e=sigma_e, slope_sd=slope_sd, fixed_slope=fixed_slope, grid=grid, check=None)
        converged.append(bool(fit["converged"]))
        post = posterior_theta(fit, k * ~held, n * ~held, grid)
        p = np.clip(predictive_p(fit, post, grid), 1e-12, 1 - 1e-12)
        kk, nn = k[held], n[held]
        loss += float(-(kk * np.log(p[held]) + (nn - kk) * np.log(1 - p[held])).sum())
        trials += float(nn.sum())
    return {"log_loss": loss / trials, "trials": trials, "converged_folds": int(sum(converged)), "folds": int(len(converged))}


def _cv_job(args):
    k, n, folds, X, sigma_e, slope_sd, fixed = args
    r = heldout_log_loss(k, n, folds, X=X, sigma_e=sigma_e, slope_sd=slope_sd, fixed_slope=fixed)
    return {"slope_sd": slope_sd, "sigma_e": sigma_e, **r}


def select_priors(k: np.ndarray, n: np.ndarray, folds: np.ndarray, X: np.ndarray, *, slope_grid=SLOPE_GRID,
                  sigma_grid=SIGMA_GRID, workers: int = 8) -> dict:
    """Grid over (slope SD, residual SD); the lowest held-out log loss wins, ties to the larger sigma_e then slope SD."""
    jobs = [(k, n, folds, X, se, sa, False) for sa in slope_grid for se in sigma_grid]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        table = list(pool.map(_cv_job, jobs))
    ok = [r for r in table if r["converged_folds"] == r["folds"]] or table
    best = sorted(ok, key=lambda r: (r["log_loss"], -r["sigma_e"], -r["slope_sd"]))[0]
    return {"table": table, "chosen": {"slope_sd": best["slope_sd"], "sigma_e": best["sigma_e"], "log_loss": best["log_loss"]}}


# ------------------------------------------------------------------------------------------------------------- gate G0


def task_folds(group_ids: np.ndarray, n_folds: int = 5, seed: int = SEED) -> np.ndarray:
    """Fold per task, whole groups together, balanced by a seeded permutation of the groups."""
    uniq = np.unique(group_ids)
    perm = np.random.default_rng(seed).permutation(uniq.size)
    fold_of_group = {uniq[g]: i % n_folds for i, g in enumerate(perm)}
    return np.array([fold_of_group[g] for g in group_ids])


@dataclass
class G0Inputs:
    k_sp: np.ndarray            # (J,) start-policy successes
    n_sp: np.ndarray            # (J,) trials (8, or 0 when unmeasured)
    panel_k: np.ndarray         # (P, J) panel successes (0/1)
    panel_n: np.ndarray         # (P, J) panel trials (0/1 measured)
    X: np.ndarray               # (J, F) design matrix for the explanatory model (intercept first)
    group_ids: np.ndarray       # (J,)
    task_ids: list


def gate_g0(inp: G0Inputs, priors: dict, *, n_folds: int = 5, seed: int = SEED, draws: int = 10_000, grid: I.Grid = GRID) -> dict:
    """Pre-registered G0 (PROTOCOL section 3): per task-group fold, drop the start policy's cells on the held-out tasks,
    refit, estimate its ability from the in-fold cells, and forecast P(active) for the held-out tasks; pool over folds.
    `priors` = {"random_intercept": {"slope_sd", "sigma_e"}, "explanatory": {...}}."""
    J = inp.k_sp.size
    folds = task_folds(inp.group_ids, n_folds, seed)
    observed_active = ((inp.k_sp >= 1) & (inp.k_sp <= G - 1)).astype(float)
    measured = inp.n_sp > 0
    K_all = np.vstack([inp.panel_k, inp.k_sp[None, :]])
    N_all = np.vstack([inp.panel_n, inp.n_sp[None, :]])
    sp = K_all.shape[0] - 1
    out = {"folds": n_folds, "seed": seed, "tasks": int(J), "measured_tasks": int(measured.sum()),
           "observed_active_share": float(observed_active[measured].mean()), "models": {}}
    pred = {"random_intercept": np.full(J, np.nan), "explanatory": np.full(J, np.nan), "features_only": np.full(J, np.nan),
            "baseline": np.full(J, np.nan)}
    pred_p = {"random_intercept": np.full(J, np.nan), "explanatory": np.full(J, np.nan)}
    theta_folds = []
    for f in range(n_folds):
        held = folds == f
        K, N = K_all.copy(), N_all.copy()
        K[sp, held], N[sp, held] = 0.0, 0.0
        in_k, in_n = inp.k_sp[~held & measured].sum(), inp.n_sp[~held & measured].sum()
        pbar = (in_k + 1.0) / (in_n + 2.0)
        pred["baseline"][held] = forecast_active(pbar)
        for name, X in (("random_intercept", I.random_intercept(J)), ("explanatory", inp.X)):
            pr = priors[name]
            fit = fit_2pl_counts(K, N, X=X, sigma_e=pr["sigma_e"], slope_sd=pr["slope_sd"], grid=grid, check=None)
            post = posterior_theta(fit, K, N, grid)[sp]
            curves = item_curves(fit, np.flatnonzero(held), grid)
            pred[name][held] = predictive_active(curves, post)
            pred_p[name][held] = curves @ post
            mean, sd = I.eap(post[None, :], grid)
            theta_folds.append({"fold": f, "model": name, "theta": float(mean[0]), "theta_sd": float(sd[0]), "converged": bool(fit["converged"])})
        # features only: held-out items removed from every respondent; their curves come from the feature prior alone
        K2, N2 = K_all.copy(), N_all.copy()
        K2[:, held], N2[:, held] = 0.0, 0.0
        keep = np.flatnonzero(~held)
        pr = priors["explanatory"]
        fit = fit_2pl_counts(K2[:, keep], N2[:, keep], X=inp.X[keep], sigma_e=pr["sigma_e"], slope_sd=pr["slope_sd"], grid=grid, check=None)
        post = posterior_theta(fit, K2[:, keep], N2[:, keep], grid)[sp]
        curves = I.new_item_curves(fit, inp.X[held], int(held.sum()), grid)
        pred["features_only"][held] = predictive_active(curves, post)
    # panel strict-rate heuristic (ranking only)
    with np.errstate(invalid="ignore", divide="ignore"):
        panel_rate = inp.panel_k.sum(0) / inp.panel_n.sum(0)
    panel_rate = np.where(np.isfinite(panel_rate), panel_rate, np.nanmean(panel_rate))
    m = measured
    y = observed_active[m]
    rng_groups = inp.group_ids[m]
    for name in ("random_intercept", "explanatory", "features_only", "baseline"):
        p = pred[name][m]
        res = {"auc": auc(p, y), "log_loss": log_loss(p, y), "ece": ece(p, y), "predicted_active_share": float(p.mean()),
               "observed_active_share": float(y.mean())}
        if name in pred_p:
            res["predicted_strict_rate"] = float(pred_p[name][m].mean())
            res["observed_strict_rate"] = float((inp.k_sp[m] / inp.n_sp[m]).mean())
        out["models"][name] = res
    out["models"]["panel_strict_rate"] = {"auc": auc(panel_rate[m], y)}
    out["theta_by_fold"] = theta_folds
    # selection and gate on the chosen model
    cand = {k: v for k, v in out["models"].items() if k in ("random_intercept", "explanatory")}
    selected = sorted(cand, key=lambda k: (cand[k]["log_loss"], k != "random_intercept"))[0]
    out["selected_model"] = selected
    base_ll = out["models"]["baseline"]["log_loss"]
    out["gate"] = {"auc_threshold": 0.70, "auc_source": "experiment 13 PROTOCOL gate F2",
                   "auc": cand[selected]["auc"], "log_loss": cand[selected]["log_loss"], "baseline_log_loss": base_ll,
                   "pass": bool(cand[selected]["auc"] >= 0.70 and cand[selected]["log_loss"] < base_ll)}
    # bootstrap over task groups: AUC of the selected model and the log-loss gain over the baseline
    rng = np.random.default_rng(seed)
    ps, pb = pred[selected][m], pred["baseline"][m]
    aucs, gains, auc_vs_panel = [], [], []
    for _ in range(draws):
        idx = group_bootstrap_indices(rng_groups, rng)
        aucs.append(auc(ps[idx], y[idx]))
        gains.append(log_loss(pb[idx], y[idx]) - log_loss(ps[idx], y[idx]))
        auc_vs_panel.append(auc(ps[idx], y[idx]) - auc(panel_rate[m][idx], y[idx]))
    aucs, gains, auc_vs_panel = np.array(aucs), np.array(gains), np.array(auc_vs_panel)
    out["bootstrap"] = {"draws": draws, "auc_ci": [float(np.nanpercentile(aucs, 2.5)), float(np.nanpercentile(aucs, 97.5))],
                        "auc_draws_below_0_70": int(np.sum(aucs < 0.70)),
                        "log_loss_gain_vs_baseline": [float(np.percentile(gains, 2.5)), float(np.percentile(gains, 97.5))],
                        "log_loss_gain_p": float(max(2 * min(np.mean(gains <= 0), np.mean(gains >= 0)), 1 / draws)),
                        "auc_minus_panel_rate": [float(np.nanpercentile(auc_vs_panel, 2.5)), float(np.nanpercentile(auc_vs_panel, 97.5))],
                        "auc_minus_panel_rate_p": float(max(2 * min(np.nanmean(auc_vs_panel <= 0), np.nanmean(auc_vs_panel >= 0)), 1 / draws))}
    out["per_task"] = {"task_id": list(inp.task_ids), "observed_active": observed_active.tolist(), "measured": measured.tolist(),
                       **{f"p_active_{k}": v.tolist() for k, v in pred.items()},
                       **{f"p_strict_{k}": v.tolist() for k, v in pred_p.items()}, "panel_rate": panel_rate.tolist(), "fold": folds.tolist()}
    return out


# -------------------------------------------------------------------------------------- graded model (smooth reward)


def factored_category(v: float) -> int:
    """Ordinal category of factored_reward: 0 | (0, .5] | (.5, .8] | (.8, 1) | 1 (experiment 19's FSC bins)."""
    if v <= 0.0:
        return 0
    if v <= 0.5:
        return 1
    if v <= 0.8:
        return 2
    if v < 1.0:
        return 3
    return 4


def fit_graded_pseudo(cat: np.ndarray, mc: np.ndarray, *, slope_sd: float, sigma_e: float, n_cats: int = 5) -> dict:
    """Graded response model for the smooth reward with the 8 sample indices as pseudo-respondents (persons x items
    categories); experiment 19's tied two-skill code is used with no strict data, so only the graded block is fitted."""
    cat, mc = np.asarray(cat), np.asarray(mc, float)
    ys, ms = np.zeros_like(mc), np.zeros_like(mc)
    fit = I.fit_two_skill(ys, ms, cat, mc, n_cats, tied=True, slope_sd=slope_sd, sigma_e=sigma_e)
    par = I.two_skill_params(fit["x"], fit["n_items"], n_cats, True)
    fit["b"], fit["cuts"] = par["b"], par["cuts"]
    return fit


def two_skill_heldout(ys: np.ndarray, ms: np.ndarray, cat: np.ndarray, mc: np.ndarray, pseudo_rows: np.ndarray,
                      group_ids: np.ndarray, *, slope_sd: float, sigma_e: float, n_cats: int = 5, n_folds: int = 5,
                      seed: int = SEED) -> dict:
    """Held-out (task-group folds, pseudo-respondent cells masked in both channels) log likelihood of the tied one-skill
    against the untied two-skill model; unavailable when any fit fails experiment 19's convergence gate."""
    folds = task_folds(group_ids, n_folds, seed)
    res = {"tied": 0.0, "untied": 0.0, "cells": 0, "converged": True, "rho": []}
    for f in range(n_folds):
        held = folds == f
        ms2, mc2 = ms.copy(), mc.copy()
        ms2[np.ix_(pseudo_rows, np.flatnonzero(held))] = 0.0
        mc2[np.ix_(pseudo_rows, np.flatnonzero(held))] = 0.0
        for tied in (True, False):
            fit = I.fit_two_skill(ys, ms2, cat, mc2, n_cats, tied=tied, slope_sd=slope_sd, sigma_e=sigma_e)
            if not fit["converged"]:
                res["converged"] = False
                return {**res, "status": "unavailable: convergence gate failed", "fold": f, "tied": tied}
            pred = I.two_skill_predict(fit, ys, ms2, cat, mc2, np.flatnonzero(held))
            ll = 0.0
            for r_i, r in enumerate(pseudo_rows):
                hm = (ms[r, held] > 0)
                ps = np.clip(pred["strict"][r][hm], 1e-12, 1 - 1e-12)
                ll += float(np.sum(ys[r, held][hm] * np.log(ps) + (1 - ys[r, held][hm]) * np.log(1 - ps)))
                hc = (mc[r, held] > 0)
                pc = np.clip(pred["cat_probs"][r][hc, cat[r, held][hc].astype(int)], 1e-300, 1.0)
                ll += float(np.sum(np.log(pc)))
            res["tied" if tied else "untied"] += ll
            if not tied:
                res["rho"].append(float(fit["rho"]))
        res["cells"] += int((ms[np.ix_(pseudo_rows, np.flatnonzero(held))] > 0).sum())
    res["status"] = "available"
    return res
