"""TLDR: Experiment 20 Phase 0b driver (CPU, zero model calls): load the committed Phase 0 per-cell table, experiment 12's 11-system panel (train tasks), experiment 19's task features and the D-013 groups; choose priors by grouped cross-validation (R0); fit the random-intercept, explanatory and 1PL item models; run the pre-registered gate G0 with its baselines and alternatives; fit the graded model on the smooth reward; run the descriptive dimensionality check and the experiment 05 Base-model sensitivity; write phase0b_analysis_e20.json + phase0b_tables_e20.md, pin every input hash (input_pins_e20.json) and freeze the item parameters for arm C (forecasts/e20_item_params.json) with rl4cv.forecast.freeze_forecast. --synthetic fabricates the start policy's cells from the panel to exercise the pipeline without real data (outputs go to a separate directory)."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.special import expit
from scipy.stats import kendalltau, pearsonr, spearmanr

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
E19 = REPO / "experiments/19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/expt_v1"
E05 = REPO / "experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/expt_v1/results"
sys.path.insert(0, str(E19))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "src"))
import data_e19 as D  # noqa: E402
import features_e19 as F  # noqa: E402
import irt_e20 as M  # noqa: E402
from rl4cv.forecast import freeze_forecast  # noqa: E402
from samplers_e20 import forecast_active  # noqa: E402

G = 8
CELLS = HERE / "results/phase0_cells_e20.csv"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_cells(path: Path, train: list[str]) -> dict:
    rows = list(csv.DictReader(path.open()))
    k = {t: 0 for t in train}
    n = {t: 0 for t in train}
    cat = np.zeros((G, len(train)))
    mc = np.zeros((G, len(train)))
    idx = {t: j for j, t in enumerate(train)}
    for r in rows:
        t = r["task_id"]
        if t not in idx:
            raise D.SplitViolation(f"non-train task {t} in the Phase 0 table")
        if r["status"] == "measured":
            k[t] += int(r["strict"])
            n[t] += 1
        if r["factored_reward"] != "":
            cat[int(r["sample_idx"]), idx[t]] = M.factored_category(float(r["factored_reward"]))
            mc[int(r["sample_idx"]), idx[t]] = 1.0
    return {"k": np.array([k[t] for t in train], float), "n": np.array([n[t] for t in train], float), "cat": cat, "mc": mc,
            "rows": len(rows), "measured": int(sum(r["status"] == "measured" for r in rows))}


def load_base_models(train: list[str]) -> dict:
    out = {}
    for name in ("qwen3-1.7b-base", "qwen3-4b-base", "qwen3-8b-base"):
        rows = {r["task_id"]: r for r in csv.DictReader((E05 / f"per_task_{name}_g8.csv").open())}
        out[name] = {"k": np.array([float(rows[t]["k_kernel_binary"]) if t in rows else 0.0 for t in train]),
                     "n": np.array([float(rows[t]["samples_present"]) if t in rows else 0.0 for t in train])}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cells", type=Path, default=CELLS)
    ap.add_argument("--out", type=Path, default=HERE / "results")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--draws", type=int, default=10_000)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--skip-cv", action="store_true", help="use experiment 19's R0 priors instead of re-selecting (debug only)")
    ap.add_argument("--two-skill", action="store_true", help="also run the expensive two-skill held-out comparison")
    args = ap.parse_args()
    t_start = time.time()
    split = D.load_split()
    train = split.train
    panel = D.load_panel(split)
    n_train = panel.n_train
    assert panel.tasks[:n_train] == train
    panel_k = panel.strict[:, :n_train] * panel.mask[:, :n_train]
    panel_n = panel.mask[:, :n_train].copy()
    feats = D.load_features(split)
    train_mask = np.array([r["split"] == "train" for r in feats])
    X_all, names = F.design_matrix(feats, train_mask)
    X = X_all[train_mask]
    groups = np.array([split.group[t] for t in train])
    if args.synthetic:
        rng = np.random.default_rng(0)
        pre = M.fit_2pl_counts(panel_k, panel_n, X=M.I.random_intercept(len(train)), sigma_e=1.0, slope_sd=0.5, check=None)
        a, d = M.item_params(pre)
        p = expit(a * (-1.5) + d)
        k_sp = rng.binomial(G, p).astype(float)
        cells = {"k": k_sp, "n": np.full(len(train), float(G)), "cat": rng.integers(0, 5, size=(G, len(train))).astype(float),
                 "mc": np.ones((G, len(train))), "rows": G * len(train), "measured": G * len(train)}
        args.out = args.out / "synthetic"
    else:
        cells = load_cells(args.cells, train)
    args.out.mkdir(parents=True, exist_ok=True)
    k_sp, n_sp = cells["k"], cells["n"]
    K = np.vstack([panel_k, k_sp[None, :]])
    N = np.vstack([panel_n, n_sp[None, :]])
    out = {"inputs": {"train_tasks": len(train), "panel_systems": len(panel.systems), "panel_measured_cells": int(panel_n.sum()),
                      "start_policy_cells_measured": int(n_sp.sum()), "start_policy_strict": int(k_sp.sum()),
                      "start_policy_pass1": float(k_sp.sum() / max(n_sp.sum(), 1)), "active_tasks": int(((k_sp >= 1) & (k_sp <= G - 1)).sum()),
                      "solved_all": int((k_sp == G).sum()), "unsolved": int((k_sp == 0).sum()), "feature_columns": names},
           "synthetic": args.synthetic}
    # ---- R0: priors by grouped cell-level cross-validation (all respondents' train cells)
    folds = M.cell_folds(K.shape[0], groups, 5, seed=M.SEED)
    if args.skip_cv:
        priors = {"random_intercept": {"slope_sd": 0.25, "sigma_e": 0.5}, "explanatory": {"slope_sd": 0.25, "sigma_e": 0.5}}
        out["R0"] = {"note": "skip-cv: experiment 19's R0 priors"}
    else:
        r0 = {}
        for name, Xm in (("random_intercept", M.I.random_intercept(len(train))), ("explanatory", X)):
            r0[name] = M.select_priors(K, N, folds, Xm, workers=args.workers)
        priors = {name: {"slope_sd": r0[name]["chosen"]["slope_sd"], "sigma_e": r0[name]["chosen"]["sigma_e"]} for name in r0}
        out["R0"] = r0
    out["priors"] = priors
    # ---- full fits
    fits = {}
    for name, Xm in (("random_intercept", M.I.random_intercept(len(train))), ("explanatory", X)):
        fits[name] = M.fit_2pl_counts(K, N, X=Xm, sigma_e=priors[name]["sigma_e"], slope_sd=priors[name]["slope_sd"])
    fits["1pl"] = M.fit_2pl_counts(K, N, X=M.I.random_intercept(len(train)), sigma_e=priors["random_intercept"]["sigma_e"],
                                   slope_sd=priors["random_intercept"]["slope_sd"], fixed_slope=True)
    out["fits"] = {}
    for name, fit in fits.items():
        a, d = M.item_params(fit)
        post = M.posterior_theta(fit, K, N)
        mean, sd = M.eap(post)
        out["fits"][name] = {"converged": fit["converged"], "max_abs_grad": fit["max_abs_grad"], "check_grid_max_abs_grad": fit["check_grid_max_abs_grad"],
                             "nit": fit["nit"], "objective": fit["objective"], "theta_start_policy": float(mean[-1]), "theta_sd_start_policy": float(sd[-1]),
                             "theta_panel": {s: float(m) for s, m in zip(panel.systems, mean[:-1])},
                             "slope_mean": float(a.mean()), "slope_sd_empirical": float(a.std()), "difficulty_sd": float((-d / a).std()),
                             "coefficients": ({n_: float(w) for n_, w in zip(names, M.I.coefficients(fit))} if name == "explanatory" else None)}
    # ---- gate G0
    inp = M.G0Inputs(k_sp=k_sp, n_sp=n_sp, panel_k=panel_k, panel_n=panel_n, X=X, group_ids=groups, task_ids=list(train))
    g0 = M.gate_g0(inp, priors, draws=args.draws)
    per_task = g0.pop("per_task")
    out["G0"] = g0
    with (args.out / "g0_per_task_e20.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        keys = list(per_task)
        w.writerow(keys)
        for i in range(len(train)):
            w.writerow([per_task[k][i] for k in keys])
    # ---- experiment 05 Base models sensitivity (report both; primary excludes them)
    base = load_base_models(train)
    Kb = np.vstack([K] + [base[b]["k"][None, :] for b in base])
    Nb = np.vstack([N] + [base[b]["n"][None, :] for b in base])
    sel = g0["selected_model"]
    Xs = M.I.random_intercept(len(train)) if sel == "random_intercept" else X
    fit_b = M.fit_2pl_counts(Kb, Nb, X=Xs, sigma_e=priors[sel]["sigma_e"], slope_sd=priors[sel]["slope_sd"], check=None)
    a0, d0 = M.item_params(fits[sel])
    ab, db = M.item_params(fit_b)
    inp_b = M.G0Inputs(k_sp=k_sp, n_sp=n_sp, panel_k=Kb[:-1][np.r_[:len(panel.systems), len(panel.systems) + 1: Kb.shape[0]]] if False else np.vstack([panel_k] + [base[b]["k"][None, :] for b in base]),
                       panel_n=np.vstack([panel_n] + [base[b]["n"][None, :] for b in base]), X=X, group_ids=groups, task_ids=list(train))
    g0_b = M.gate_g0(inp_b, priors, draws=min(args.draws, 1000))
    g0_b.pop("per_task")
    out["base_models_sensitivity"] = {"base_strict": {b: int(base[b]["k"].sum()) for b in base}, "base_cells": {b: int(base[b]["n"].sum()) for b in base},
                                      "difficulty_correlation_with_primary": float(np.corrcoef(-d0 / a0, -db / ab)[0, 1]),
                                      "slope_correlation_with_primary": float(np.corrcoef(a0, ab)[0, 1]), "converged": fit_b["converged"],
                                      "G0_with_base_models": {k: g0_b[k] for k in ("models", "selected_model", "gate")},
                                      "primary_excludes_base_models": True}
    # ---- graded model on the smooth reward (8 pseudo-respondents)
    grm = M.fit_graded_pseudo(cells["cat"], cells["mc"], slope_sd=priors["random_intercept"]["slope_sd"], sigma_e=priors["random_intercept"]["sigma_e"])
    cat_counts = np.bincount(cells["cat"][cells["mc"] > 0].astype(int), minlength=5)
    out["graded_smooth"] = {"converged": grm["converged"], "max_abs_grad": grm["max_abs_grad"], "check_grid_max_abs_grad": grm["check_grid_max_abs_grad"],
                            "category_counts": cat_counts.tolist(), "category_edges": "0 | (0, .5] | (.5, .8] | (.8, 1) | 1",
                            "cells": int(cells["mc"].sum()), "mean_slope": float(grm["b"].mean()),
                            "tasks_with_nonconstant_smooth_reward_observed": int(sum(len(set(cells["cat"][:, j][cells["mc"][:, j] > 0])) > 1 for j in range(len(train)))),
                            "tasks_with_nonconstant_strict_observed": int(((k_sp >= 1) & (k_sp <= G - 1)).sum())}
    # ---- dimensionality (descriptive): strict difficulty vs graded first threshold
    diff = -d0 / a0
    thr = -grm["cuts"][:, 0] / grm["b"]
    rng = np.random.default_rng(M.SEED)
    boot = []
    for _ in range(1000):
        idx = M.group_bootstrap_indices(groups, rng)
        boot.append(spearmanr(diff[idx], thr[idx]).correlation)
    out["dimensionality_descriptive"] = {"pearson": float(pearsonr(diff, thr)[0]), "spearman": float(spearmanr(diff, thr).correlation),
                                         "kendall": float(kendalltau(diff, thr).correlation),
                                         "spearman_ci95_item_group_bootstrap": [float(np.nanpercentile(boot, 2.5)), float(np.nanpercentile(boot, 97.5))],
                                         "items": len(train), "note": "strict 2PL difficulty (-d/a, selected model) against the graded model's first threshold on the smooth reward"}
    if args.two_skill:
        P = len(panel.systems)
        ys = np.vstack([panel_k, (cells["cat"] * 0)])  # placeholder rows replaced below
        ys = np.vstack([panel_k, np.zeros((G, len(train)))])
        ms = np.vstack([panel_n, np.zeros((G, len(train)))])
        strict_rows = {}
        for r in csv.DictReader(args.cells.open()) if not args.synthetic else []:
            if r["status"] == "measured":
                strict_rows[(int(r["sample_idx"]), r["task_id"])] = int(r["strict"])
        for s in range(G):
            for j, t in enumerate(train):
                if (s, t) in strict_rows:
                    ys[P + s, j], ms[P + s, j] = strict_rows[(s, t)], 1.0
        cat = np.vstack([np.zeros((P, len(train))), cells["cat"]])
        mc = np.vstack([np.zeros((P, len(train))), cells["mc"]])
        out["two_skill"] = M.two_skill_heldout(ys, ms, cat, mc, np.arange(P, P + G), groups, slope_sd=priors["random_intercept"]["slope_sd"], sigma_e=priors["random_intercept"]["sigma_e"])
    else:
        out["two_skill"] = {"status": "not run (use --two-skill)"}
    # ---- frozen item parameters for arm C (selected model) and pins
    a_sel, d_sel = M.item_params(fits[sel])
    post_sel = M.posterior_theta(fits[sel], K, N)[-1]
    theta0, theta0_sd = M.eap(post_sel[None, :])
    p0 = expit(a_sel * float(theta0[0]) + d_sel)
    item_payload = {"experiment": "20", "model": sel, "priors": priors[sel], "task_ids": list(train), "a": a_sel.tolist(), "d": d_sel.tolist(),
                    "theta0": float(theta0[0]), "theta0_sd": float(theta0_sd[0]), "grid": {"lo": M.GRID.lo, "hi": M.GRID.hi, "count": M.GRID.count},
                    "p_at_theta0": p0.tolist(), "p_active_at_theta0": forecast_active(p0).tolist(), "fisher_weight_at_theta0": (a_sel**2 * p0 * (1 - p0)).tolist(),
                    "fitted_on": {"panel_systems": panel.systems, "start_policy_cells": int(n_sp.sum())}, "G0": g0["gate"], "synthetic": args.synthetic}
    fdir = args.out / "forecasts" if args.synthetic else HERE / "forecasts"
    entry = freeze_forecast(item_payload, fdir, "e20_item_params" + ("_synthetic" if args.synthetic else ""))
    out["frozen_item_params"] = entry
    pins = {"note": "SHA-256 of every input the Phase 0b analysis reads (experiment 20); the test id list is read only as a guard.",
            "paths": {"phase0_cells": str(args.cells.relative_to(REPO)) if not args.synthetic else "synthetic",
                      "e12_input_manifest": str(D.E12_MANIFEST.relative_to(REPO)), "task_features": str(D.FEATURES.relative_to(REPO)),
                      "split_manifest": str((D.E08 / "split/vbv1_split_manifest.csv").relative_to(REPO)),
                      "train_ids": str((D.E08 / "split/vbv1_train_task_ids.txt").relative_to(REPO)), "test_ids_guard_only": str((D.E08 / "split/vbv1_test_task_ids.txt").relative_to(REPO)),
                      **{f"e05_{b}": str((E05 / f"per_task_{b}_g8.csv").relative_to(REPO)) for b in base}}}
    pins["sha256"] = {k: (sha256_file(REPO / v) if v != "synthetic" else "synthetic") for k, v in pins["paths"].items()}
    (args.out / "input_pins_e20.json").write_text(json.dumps(pins, indent=1) + "\n")
    out["wall_seconds"] = time.time() - t_start
    (args.out / "phase0b_analysis_e20.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    # ---- tables
    g = out["G0"]
    lines = ["# Experiment 20 Phase 0b tables", "", f"Generated {time.strftime('%m-%d-%Y %H:%M %Z')}; synthetic={args.synthetic}", "",
             "| Model | AUC (active 1-7 of 8) | log loss | ECE | predicted active share | observed active share |", "|---|---|---|---|---|---|"]
    for name, r in g["models"].items():
        lines.append(f"| {name} | {r.get('auc', float('nan')):.3f} | {r.get('log_loss', float('nan')):.4f} | {r.get('ece', float('nan')):.3f} | {r.get('predicted_active_share', float('nan')):.3f} | {r.get('observed_active_share', float('nan')):.3f} |")
    b = g["bootstrap"]
    lines += ["", f"Selected model: **{g['selected_model']}**; gate G0 {'PASS' if g['gate']['pass'] else 'FAIL'}: AUC {g['gate']['auc']:.3f} [{b['auc_ci'][0]:.3f}, {b['auc_ci'][1]:.3f}] (threshold 0.70, experiment 13 F2; {b['auc_draws_below_0_70']}/{b['draws']} draws below 0.70); log loss {g['gate']['log_loss']:.4f} vs Beta(1,1) baseline {g['gate']['baseline_log_loss']:.4f}, gain {b['log_loss_gain_vs_baseline'][0]:.4f}..{b['log_loss_gain_vs_baseline'][1]:.4f} p-val={b['log_loss_gain_p']:.4g}; AUC minus panel strict rate [{b['auc_minus_panel_rate'][0]:.3f}, {b['auc_minus_panel_rate'][1]:.3f}] p-val={b['auc_minus_panel_rate_p']:.4g}.",
              "", f"Priors (R0): {json.dumps(priors)}; start policy θ̂₀ = {item_payload['theta0']:.3f} (SD {item_payload['theta0_sd']:.3f}); strict pass@1 {out['inputs']['start_policy_pass1']:.4f} over {out['inputs']['start_policy_cells_measured']} measured cells; active tasks {out['inputs']['active_tasks']}/539."]
    (args.out / "phase0b_tables_e20.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"selected": sel, "gate": g["gate"], "priors": priors, "wall_s": out["wall_seconds"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
