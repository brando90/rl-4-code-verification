"""TLDR: Experiment 14 analysis: on experiment 07's 164 × 424 SWE-bench Verified matrix and its exact H2 task splits, does item response theory (IRT) ability estimated from the n_A tasks of half A forecast each system's held-out pass@1 on half B better than its pass@1 on half A does, in rank and in level? Zero model calls."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import multiprocessing
import os
import platform
import socket
import sys
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.special import expit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for _p in (REPO / "src", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import irt_e14 as irt  # noqa: E402
from rl4cv.forecast import verify_forecast  # noqa: E402
from rl4cv.scs4c import kendall_tau_b, pearson, spearman  # noqa: E402

EXPERIMENT = "14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems"
E07 = REPO / "experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1"
PER_CELL = E07 / "results/per_cell_e07.jsonl.gz"
ANALYSIS_E07 = E07 / "results/analysis_e07.json"
PINS = {PER_CELL.name: "f064c3951860cf4d88879e7c3b81ec42c8b42780923c61198c71f98dc6463a4d",
        ANALYSIS_E07.name: "16d551328ab9aedaad399f50fd4d59cf12759e0b377c8040d063dd5ef2c5b3f5"}
FORECAST = HERE / "forecasts/e14_forecast.json"

SEED_E07, BOOT_E07, SPLITS, SIZES, PRIMARY = 20261007, 2000, 2000, (25, 50, 100, 250), 50
SEED, K, FOLD_SEEDS, BOOT, SIGNFLIPS = 20261012, 10, (0, 1, 2, 3, 4), 2000, 10000
EXPECTED = {"systems": 164, "tasks": 424, "cells": 69536, "inconsistent_cells": 1}
SHARE_RULE, ROUND = 0.60, 12  # experiment 07's frozen share; forecasts are rounded before ranking
IRT_KINDS = ("1pl", "2pl", "grm3")  # system K-fold item parameters (level forecasts)
WITHIN_KINDS = ("2pl", "grm3")  # refitted on half A of every system for each split (rank forecasts; no half-B data)
RANK_ONLY = ("rasch_common_check", "2pl_within_A", "grm3_within_A")
ARMS = ("pass1_A", "rasch_common_check", "2pl_within_A", "grm3_within_A", "1pl", "2pl", "grm3", "mean_equating", "linear_regression")
LEVEL_ARMS = tuple(a for a in ARMS if a not in RANK_ONLY)
COMPARED = tuple(a for a in ARMS if a != "pass1_A")
WITHIN_FAIL_SHARE = 0.01  # more than 1% unconverged within-half fits at n_A = 50 makes the rank verdict inconclusive
GATES = ("G0_scalar", "G1_pass1_1se", "G2_irt_1se", "G1m_pass1_top_matched_to_G2", "G2m_irt_top_matched_to_G1")


# ----------------------------------------------------------------------------- data

class Data:
    """Systems × tasks matrices in experiment 07's order: resolved, gated factors, per-cell score, categories."""

    def __init__(self, systems: list[str], tasks: list[str], resolved, t_fix, t_keep, score):
        self.systems, self.tasks = list(systems), list(tasks)
        self.R, self.TF, self.TK, self.SC = (np.asarray(m, float) for m in (resolved, t_fix, t_keep, score))
        self.n_sys, self.n_tasks = self.R.shape
        # Graded category: 2 resolved; 1 unresolved with partial credit (cell score > 0); 0 otherwise.
        self.cat = np.where(self.R == 1, 2, np.where(self.SC > 0, 1, 0))
        self.cats_bin = [1.0 - self.R, self.R]
        self.cats_grm = [(self.cat == c).astype(float) for c in range(3)]

    def subset(self, rows: np.ndarray) -> "Data":
        return Data([self.systems[i] for i in rows], self.tasks, self.R[rows], self.TF[rows], self.TK[rows], self.SC[rows])

    def inconsistent_cells(self) -> int:
        return int((((self.R == 1) & (self.SC < 1)) | ((self.R == 0) & (self.SC == 1))).sum())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_real() -> tuple[Data, dict]:
    """Experiment 07's included systems (sorted, as 07 ordered them) × its common cohort (07's order)."""
    for path in (PER_CELL, ANALYSIS_E07):
        if sha256(path) != PINS[path.name]:
            raise SystemExit(f"STOP: {path} differs from its pinned SHA-256")
    e07 = json.loads(ANALYSIS_E07.read_text())
    tasks = e07["common_cohort_ids"]
    rows = [json.loads(line) for line in gzip.open(PER_CELL, "rt")]
    systems = sorted({r["submission"] for r in rows if r["included"]})
    si, ti = {s: i for i, s in enumerate(systems)}, {t: j for j, t in enumerate(tasks)}
    mats = {k: np.full((len(systems), len(tasks)), np.nan) for k in ("R", "TF", "TK", "SC")}
    seen = 0
    for r in rows:
        if not r["common_cohort"]:
            continue
        i, j = si[r["submission"]], ti[r["instance_id"]]
        g = r["gate"]
        if g is None or r["score"] is None or not isinstance(r["resolved"], bool):
            raise SystemExit(f"STOP: unmeasured cohort cell {r['submission']} {r['instance_id']}")
        mats["R"][i, j] = float(r["resolved"])
        mats["TF"][i, j] = 0.0 if g == 0 else r["t_fix"]
        mats["TK"][i, j] = 0.0 if g == 0 else r["t_keep"]
        mats["SC"][i, j] = r["score"]
        seen += 1
    if seen != len(systems) * len(tasks) or any(np.isnan(m).any() for m in mats.values()):
        raise SystemExit("STOP: the common cohort is not a complete systems × tasks matrix")
    return Data(systems, tasks, mats["R"], mats["TF"], mats["TK"], mats["SC"]), e07


def synthetic(seed: int, n_sys: int = 164, n_tasks: int = 424) -> Data:
    """A 2PL-generated stand-in with the real shapes, for pipeline tests and timing only (never a result)."""
    rng = np.random.default_rng([SEED, 99, seed])
    theta, a, b = rng.normal(0, 1, n_sys), np.exp(rng.normal(0.5, 0.4, n_tasks)), rng.normal(-0.3, 1.5, n_tasks)
    resolved = (rng.random((n_sys, n_tasks)) < expit(a * (theta[:, None] - b))).astype(float)
    partial = (resolved == 0) & (rng.random((n_sys, n_tasks)) < 0.4 * expit(a * (theta[:, None] - b + 0.8)))
    score = np.where(resolved == 1, 1.0, np.where(partial, rng.uniform(0.05, 0.95, (n_sys, n_tasks)), 0.0))
    return Data([f"sys{i:03d}" for i in range(n_sys)], [f"task{j:03d}" for j in range(n_tasks)], resolved, score, score, score)


# ----------------------------------------------------------------------------- splits and folds

def burn_e07_bootstraps(rng: np.random.Generator, n_tasks: int, n_sys: int, boot: int = BOOT_E07) -> np.random.Generator:
    """Advance ``rng`` exactly as experiment 07's H1 and H1b bootstraps did before it drew its H2 splits."""
    for _ in range(2):
        for _ in range(boot):
            rng.integers(0, n_tasks, n_tasks)
        for _ in range(boot):
            rng.integers(0, n_sys, n_sys)
    return rng


def replay_e07_splits(n_tasks: int, n_sys: int, sizes=SIZES, splits: int = SPLITS) -> dict[int, np.ndarray]:
    """Experiment 07's H2 permutations: half A = perm[:n_A], half B = perm[n_A:]."""
    rng = burn_e07_bootstraps(np.random.default_rng(SEED_E07), n_tasks, n_sys)
    return {s: np.stack([rng.permutation(n_tasks) for _ in range(splits)]) for s in sizes}


def load_e07_module():
    spec = importlib.util.spec_from_file_location("analyze_e07", E07 / "analyze_e07.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["analyze_e07"] = module
    spec.loader.exec_module(module)
    return module


def reproduce_e07_h2(d: Data, published: dict, perms: dict[int, np.ndarray]) -> dict:
    """Stop rule: 07's own code on the replayed stream, and our replayed permutations, must reproduce 07's H2 exactly."""
    e07 = load_e07_module()
    m = {"t_fix": d.TF, "t_keep": d.TK, "resolved": d.R}
    rng = burn_e07_bootstraps(np.random.default_rng(SEED_E07), d.n_tasks, d.n_sys)
    got = json.loads(json.dumps(e07.held_out_prediction(m, list(SIZES), SPLITS, rng)))
    replay = {}
    for s in SIZES:
        deltas = []
        for perm in perms[s]:
            scs_a, p1_a = e07.system_scores(m, perm[:s])
            _, p1_b = e07.system_scores(m, perm[s:])
            deltas.append(spearman(scs_a, p1_b) - spearman(p1_a, p1_b))
        replay[str(s)] = {"delta_median": float(np.median(deltas)), "positive_splits": int((np.asarray(deltas) > 0).sum())}
    replay_ok = all(replay[k]["delta_median"] == published[k]["delta_median"]
                    and replay[k]["positive_splits"] == published[k]["positive_splits"] for k in replay)
    return {"e07_code_on_replayed_stream_equals_published_h2": got == published,
            "replayed_permutations_reproduce_published_medians_and_counts": replay_ok, "replayed": replay}


def assign_folds(n_sys: int, fold_seed: int, stream: int = 1) -> np.ndarray:
    """System K-fold: fold ids 0..K-1, balanced, from a seeded permutation."""
    perm = np.random.default_rng([SEED, stream, fold_seed]).permutation(n_sys)
    fold = np.empty(n_sys, dtype=int)
    fold[perm] = np.arange(n_sys) % K
    return fold


_WORK: dict = {}


def _fit_job(job: tuple[str, np.ndarray]) -> dict:
    kind, rows = job
    d = _WORK["data"]
    cats = d.cats_grm if kind == "grm3" else d.cats_bin
    t0 = time.time()
    f = irt.fit(kind, [c[rows] for c in cats])
    return f | {"seconds": round(time.time() - t0, 2)}


def _within_half_job(job: tuple[str, np.ndarray]) -> dict:
    """Fit ``kind`` on every system's responses to half A only, score every system by EAP on that fit, and
    record the numerical gates: convergence on both grids, endpoint mass, and the change when rescored on CHECK."""
    kind, a_items = job
    d = _WORK["data"]
    sub = [c[:, a_items] for c in (d.cats_grm if kind == "grm3" else d.cats_bin)]
    items = np.arange(len(a_items))
    fitted = irt.fit(kind, sub)
    sc = irt.Scorer(fitted)
    post = sc.posterior(sub, items)
    theta, psd = sc.eap(post)
    theta_c, psd_c = (sc_c := irt.Scorer(fitted, irt.CHECK)).eap(sc_c.posterior(sub, items))
    rescore = max(irt.max_abs(theta - theta_c), irt.max_abs(psd - psd_c))
    endpoint = irt.max_abs(irt.endpoint_mass(post))
    finite = bool(np.all(np.isfinite(theta)) and np.all(np.isfinite(psd)))
    ok = bool(fitted["converged"] and finite and endpoint <= irt.ENDPOINT_TOL and rescore <= irt.RESCORE_TOL)
    return {"theta": theta, "psd": psd, "ok": ok, "converged": fitted["converged"], "max_abs_grad": fitted["max_abs_grad"],
            "check_grid_max_abs_grad": fitted["check_grid_max_abs_grad"], "endpoint_mass_max": endpoint, "rescore_max_abs_change": rescore}


def _init_worker(data: Data) -> None:
    _WORK["data"] = data


class Runner:
    """Ordered map over independent jobs: sequential, or a spawn pool whose workers receive the data once.

    Spawn (not fork) because forking after threads or system frameworks have run can deadlock (seen on macOS
    during pre-lock tests). Each job is independent and deterministic, so results do not depend on the worker count.
    """

    def __init__(self, workers: int):
        self.workers = workers

    def map(self, fn, jobs: list, data: Data) -> list:
        _WORK["data"] = data
        if self.workers <= 1:
            return [fn(j) for j in jobs]
        ctx = multiprocessing.get_context("spawn")
        with ctx.Pool(self.workers, initializer=_init_worker, initargs=(data,)) as pool:
            return pool.map(fn, jobs, chunksize=max(1, len(jobs) // (4 * self.workers)))


def fit_folds(kind: str, d: Data, fold: np.ndarray, runner: Runner, log=print) -> list[dict]:
    """Item parameters for each fold from the other folds' systems only (all tasks of those systems)."""
    fits = runner.map(_fit_job, [(kind, np.where(fold != k)[0]) for k in range(K)], d)
    for k, f in enumerate(fits):
        f["fold"] = k
        log(f"  fit {kind} fold {k}: converged={f['converged']} max|grad|={f['max_abs_grad']:.2e} nit={f['nit']} {f['seconds']}s")
    return fits


def within_half(kind: str, d: Data, perms: np.ndarray, size: int, runner: Runner) -> dict:
    """Per-split within-half fits; a fit fails on any non-finite value or any numerical gate (NaN never passes)."""
    res = runner.map(_within_half_job, [(kind, perm[:size]) for perm in perms], d)
    failed = [s for s, r in enumerate(res) if not r["ok"]]
    theta = np.stack([r["theta"] for r in res])
    for s in failed:  # a failed fit gives no score; its split is undefined for ranking and bounded separately
        theta[s] = np.nan
    worst = lambda key: float(np.nanmax([r[key] if r[key] is not None else np.nan for r in res]))  # noqa: E731
    return {"theta": theta, "psd": np.stack([r["psd"] for r in res]), "fits": len(res), "failed": len(failed),
            "failed_splits": failed, "not_converged": sum(1 for r in res if not r["converged"]),
            "max_abs_grad_max": worst("max_abs_grad"), "check_grid_max_abs_grad_max": worst("check_grid_max_abs_grad"),
            "endpoint_mass_max": worst("endpoint_mass_max"), "rescore_max_abs_change_max": worst("rescore_max_abs_change")}


# ----------------------------------------------------------------------------- forecasts per split

class SplitScorer:
    """Every arm's held-out pass@1 forecast for one system K-fold assignment and fitted models."""

    def __init__(self, d: Data, fold: np.ndarray, fits: dict[str, list[dict]]):
        self.d, self.fold = d, fold
        self.idx = [np.where(fold == k)[0] for k in range(K)]
        self.ref = [np.where(fold != k)[0] for k in range(K)]
        self.scorers = {kind: [irt.Scorer(f) for f in fs] for kind, fs in fits.items()}
        self._fits = fits
        self.item_rate = [d.R[r].mean(0) for r in self.ref]  # reference-panel pass rate per task (Brier baseline)
        self.endpoint = {kind: {"max": 0.0, "violations": 0} for kind in fits}  # K-fold posteriors on the BASE grid

    def run(self, a_items: np.ndarray, b_items: np.ndarray, kinds=IRT_KINDS, controls: bool = True, detail: bool = False) -> dict:
        d = self.d
        y, p1a = d.R[:, b_items].mean(1), d.R[:, a_items].mean(1)
        out = {"y": y, "f": {"pass1_A": p1a}}
        if "1pl" in kinds:  # rank check: one parameter set for every system
            sc = self.scorers["1pl"][0]
            out["f"]["rasch_common_check"] = sc.posterior(d.cats_bin, a_items) @ sc.heldout_node_mean(a_items)
        if detail:
            sse = {"2pl": 0.0, "system_only_pass1_A": 0.0, "item_only_reference_rate": 0.0}
        for kind in kinds:
            cats = d.cats_grm if kind == "grm3" else d.cats_bin
            f = np.empty(d.n_sys)
            for k, idx in enumerate(self.idx):
                sc = self.scorers[kind][k]
                post = sc.posterior([c[idx] for c in cats], a_items)
                f[idx] = post @ sc.heldout_node_mean(a_items)
                em = irt.endpoint_mass(post)
                self.endpoint[kind]["max"] = max(self.endpoint[kind]["max"], irt.max_abs(em))
                self.endpoint[kind]["violations"] += int((~(em <= irt.ENDPOINT_TOL)).sum())
                if detail and kind == "2pl":
                    xb = d.R[idx][:, b_items]
                    sse["2pl"] += float(((post @ sc.p_resolved[b_items].T - xb) ** 2).sum())
                    sse["system_only_pass1_A"] += float(((p1a[idx][:, None] - xb) ** 2).sum())
                    sse["item_only_reference_rate"] += float(((self.item_rate[k][b_items][None, :] - xb) ** 2).sum())
            out["f"][kind] = f
        if controls:
            me, lr = np.empty(d.n_sys), np.empty(d.n_sys)
            for idx, ref in zip(self.idx, self.ref):
                xr, yr = p1a[ref], y[ref]
                me[idx] = p1a[idx] + (yr.mean() - xr.mean())
                xc = xr - xr.mean()
                slope = float(xc @ (yr - yr.mean()) / (xc @ xc)) if xc @ xc > 0 else 0.0
                lr[idx] = yr.mean() + slope * (p1a[idx] - xr.mean())
            out["f"]["mean_equating"], out["f"]["linear_regression"] = me, lr
        if detail:
            out["brier"] = {k: v / (d.n_sys * len(b_items)) for k, v in sse.items()}
        return out

    def rescore_check(self, perms: np.ndarray, size: int, n_check: int = 20) -> dict:
        """Largest change in K-fold forecasts, EAP and posterior SD when the fitted models are rescored on the CHECK
        grid, over the first ``n_check`` splits (deterministic subset); compared with irt.RESCORE_TOL."""
        out = {}
        for kind, scorers in self.scorers.items():
            cats = self.d.cats_grm if kind == "grm3" else self.d.cats_bin
            worst = 0.0
            for k, (idx, sc) in enumerate(zip(self.idx, scorers)):
                sc_c = irt.Scorer(self._fits[kind][k], irt.CHECK)
                sub = [c[idx] for c in cats]
                for perm in perms[:n_check]:
                    a_items = perm[:size]
                    post, post_c = sc.posterior(sub, a_items), sc_c.posterior(sub, a_items)
                    diffs = [post @ sc.heldout_node_mean(a_items) - post_c @ sc_c.heldout_node_mean(a_items)]
                    diffs += [u - v for u, v in zip(sc.eap(post), sc_c.eap(post_c))]
                    worst = max(worst, *(irt.max_abs(x) for x in diffs))
            out[kind] = {"splits_checked": min(n_check, len(perms)), "max_abs_change": worst, "ok": bool(worst <= irt.RESCORE_TOL)}
        return out


# ----------------------------------------------------------------------------- statistics

def rounded(f: np.ndarray) -> np.ndarray:
    return np.round(f, ROUND)


def rank_rows(m: np.ndarray) -> np.ndarray:
    """Average ranks (1-based) along each row, equal to scipy.stats.rankdata(method="average") but vectorized."""
    order = np.argsort(m, axis=1, kind="stable")
    s = np.take_along_axis(m, order, axis=1)
    n = m.shape[1]
    pos = np.broadcast_to(np.arange(n), m.shape)
    new = s[:, 1:] != s[:, :-1]
    first = np.ones(m.shape, bool)
    first[:, 1:] = new
    last = np.ones(m.shape, bool)
    last[:, :-1] = new
    start = np.maximum.accumulate(np.where(first, pos, 0), axis=1)
    end = np.minimum.accumulate(np.where(last, pos, n - 1)[:, ::-1], axis=1)[:, ::-1]
    out = np.empty(m.shape)
    np.put_along_axis(out, order, (start + end) / 2.0 + 1.0, axis=1)
    return out


def pearson_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a, b = a - a.mean(1, keepdims=True), b - b.mean(1, keepdims=True)
    den = np.sqrt((a * a).sum(1) * (b * b).sum(1))
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den > 0, (a * b).sum(1) / den, np.nan)


def pct(vals, q) -> list[float] | None:
    vals = np.asarray([v for v in vals if v is not None and np.isfinite(v)], float)
    return [float(v) for v in np.percentile(vals, q)] if len(vals) else None


def boot_p_two_sided(draws: np.ndarray, null: float) -> float:
    """Bootstrap p-value against ``null``: twice the smaller tail count, with the +1 correction, capped at 1."""
    draws = np.asarray(draws, float)
    draws = draws[np.isfinite(draws)]
    if not len(draws):
        return float("nan")
    tail = min(int((draws <= null).sum()), int((draws >= null).sum()))
    return float(min(1.0, 2 * (tail + 1) / (len(draws) + 1)))


def signflip_p(diff: np.ndarray, rng: np.random.Generator, draws: int) -> float:
    """Paired sign-flip permutation test over systems. Its null is that the per-system differences are symmetric
    about 0 (sign-exchangeable), which is stronger than a zero mean; reported only as a diagnostic."""
    obs = abs(diff.mean())
    flips = rng.choice((-1.0, 1.0), size=(draws, len(diff)))
    return float((1 + (np.abs(flips @ diff / len(diff)) >= obs - 1e-15).sum()) / (draws + 1))


def rank_summary(deltas: list[float | None], rhos: list[float | None], base_rhos: list[float | None]) -> dict:
    """Experiment 07's H2 summary: undefined splits are excluded from medians and count as not positive."""
    dv = np.asarray([v for v in deltas if v is not None], float)
    positive = int((dv > 0).sum())
    return {"splits": len(deltas), "defined": len(dv), "delta_median": float(np.median(dv)) if len(dv) else None,
            "delta_p05_p95": pct(dv, [5, 95]), "delta_mean": float(dv.mean()) if len(dv) else None,
            "exact_zero_splits": int((dv == 0).sum()), "positive_splits": positive, "share_delta_positive": positive / len(deltas),
            "spearman_arm_A_vs_pass1_B_median": float(np.median([v for v in rhos if v is not None])),
            "spearman_pass1_A_vs_pass1_B_median": float(np.median([v for v in base_rhos if v is not None]))}


def level_compare(err_base: np.ndarray, err_arm: np.ndarray, rng: np.random.Generator) -> dict:
    """Per-system split-averaged absolute errors; positive difference means the arm is closer to held-out pass@1."""
    diff = err_base - err_arm
    n = len(diff)
    draws = np.array([diff[rng.integers(0, n, n)].mean() for _ in range(BOOT)])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return {"mae_difference": float(diff.mean()), "ci95": [float(lo), float(hi)], "p_value": boot_p_two_sided(draws, 0.0),
            "p_value_signflip_symmetry_diagnostic": signflip_p(diff, rng, SIGNFLIPS),
            "systems_arm_better": int((diff > 0).sum()), "n_systems": n,
            "test": (f"system-cluster percentile bootstrap over systems ({BOOT} draws) for the CI and the p-value (null: zero mean "
                     f"difference; p = twice the smaller tail count, +1 corrected); sign-flip diagnostic ({SIGNFLIPS} flips) "
                     "assumes per-system differences symmetric about 0")}


def bootstrap_rank(F: dict[str, np.ndarray], Fb: np.ndarray, Y: np.ndarray, rng: np.random.Generator, draws: int) -> dict:
    """System-cluster bootstrap of the split-median Δ and split share Δ > 0, re-ranking all splits per draw.

    Splits whose forecast row has any non-finite value (a failed fit) stay undefined in every draw: excluded from
    the median and counted as not positive, as in the point estimate.
    """
    n = Y.shape[1]
    res = {arm: {"median": [], "share": []} for arm in F}
    valid = {arm: np.isfinite(Fa).all(1) for arm, Fa in F.items()}
    clean = {arm: np.where(np.isfinite(Fa), Fa, 0.0) for arm, Fa in F.items()}
    for _ in range(draws):
        idx = rng.integers(0, n, n)
        ry, rb = rank_rows(Y[:, idx]), rank_rows(Fb[:, idx])
        base = pearson_rows(rb, ry)
        for arm, Fa in clean.items():
            delta = pearson_rows(rank_rows(Fa[:, idx]), ry) - base
            delta[~valid[arm]] = np.nan
            res[arm]["median"].append(np.nanmedian(delta))
            res[arm]["share"].append(float((delta > 0).sum()) / len(delta))
    out = {}
    for arm, r in res.items():
        med, share = np.asarray(r["median"]), np.asarray(r["share"])
        out[arm] = {"delta_median_ci95": pct(med, [2.5, 97.5]), "delta_median_p_value": boot_p_two_sided(med, 0.0),
                    "share_ci95": pct(share, [2.5, 97.5]), "share_p_value_vs_0.60": boot_p_two_sided(share, SHARE_RULE),
                    "draws": draws, "test": f"system-cluster percentile bootstrap ({draws} draws); p = twice the smaller tail count, +1 corrected"}
    return out


def top_n(z: np.ndarray, mask: np.ndarray, n: int) -> np.ndarray:
    """The n valid pairs (in ``mask``, z not NaN; ±inf allowed) with the largest z, ties broken by flat index."""
    valid = (mask & ~np.isnan(z)).ravel()
    zf = np.where(valid, z.ravel(), -np.inf)
    order = np.lexsort((np.arange(zf.size), -zf, ~valid))  # valid first, then larger z, then index
    sel = np.zeros(zf.size, bool)
    sel[order[: min(n, int(valid.sum()))]] = True
    return sel.reshape(z.shape)


def signed_ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    """num / den with the degenerate convention: zero denominator gives +inf, -inf or 0 by the sign of num."""
    num, den = np.broadcast_arrays(np.asarray(num, float), np.asarray(den, float))
    out = np.zeros(num.shape)
    pos = den > 0
    out[pos] = num[pos] / den[pos]
    out[~pos & (num > 0)] = np.inf
    out[~pos & (num < 0)] = -np.inf
    return out


class GateAccumulator:
    """Promotion-gate replay over ordered pairs (incumbent row, candidate column) on half A, outcome on half B."""

    def __init__(self, n_sys: int):
        self.n = n_sys
        self.off = ~np.eye(n_sys, dtype=bool)
        self.acc = {g: {k: np.zeros((n_sys, n_sys), np.int64) for k in ("prom", "harm", "good")} for g in GATES}
        self.per_split = {g: {"prom": [], "harm": [], "good": []} for g in GATES}
        self.base = {"pairs": 0, "harm_pairs": 0}
        self.match_failures = 0

    def add(self, xa: np.ndarray, p1a: np.ndarray, y: np.ndarray, theta: np.ndarray, psd: np.ndarray) -> None:
        n_a = xa.shape[1]
        dp = p1a[None, :] - p1a[:, None]
        n10 = xa @ (1.0 - xa).T
        var = (n10 + n10.T - n_a * dp**2) / (n_a - 1)
        se = np.sqrt(np.maximum(var, 0.0) / n_a)
        zp = signed_ratio(dp, se)
        zt = signed_ratio(theta[None, :] - theta[:, None], np.sqrt(psd[None, :] ** 2 + psd[:, None] ** 2))
        dy = y[None, :] - y[:, None]
        harm, good = (dy < 0) & self.off, (dy > 0) & self.off
        gates = {"G0_scalar": (dp > 0) & self.off, "G1_pass1_1se": (zp > 1) & self.off, "G2_irt_1se": (zt > 1) & self.off}
        n2, n1 = int(gates["G2_irt_1se"].sum()), int(gates["G1_pass1_1se"].sum())
        gates["G1m_pass1_top_matched_to_G2"] = top_n(zp, self.off, n2)
        gates["G2m_irt_top_matched_to_G1"] = top_n(zt, self.off, n1)
        self.match_failures += int(gates["G1m_pass1_top_matched_to_G2"].sum() != n2) + int(gates["G2m_irt_top_matched_to_G1"].sum() != n1)
        for g, m in gates.items():
            for key, mm in (("prom", m), ("harm", m & harm), ("good", m & good)):
                self.acc[g][key] += mm
                self.per_split[g][key].append(int(mm.sum()))
        self.base["pairs"] += int(self.off.sum())
        self.base["harm_pairs"] += int(harm.sum())

    def summary(self, rng: np.random.Generator) -> dict:
        out = {"population": "all ordered pairs of distinct systems; harmful = candidate's held-out pass@1 below incumbent's",
               "splits": len(self.per_split["G0_scalar"]["prom"]), "ordered_pairs_per_split": int(self.off.sum()),
               "base_rate_harmful_if_promoted_at_random": self.base["harm_pairs"] / max(self.base["pairs"], 1),
               "matched_count_failures": self.match_failures,
               "degenerate_convention": "a zero standard error gives z = +inf, -inf or 0 by the sign of the gain"}
        for g in GATES:
            prom, harm, good = (self.acc[g][k].sum() for k in ("prom", "harm", "good"))
            out[g] = {"promotions_per_split_mean": float(np.mean(self.per_split[g]["prom"])),
                      "promotions_per_split_p05_p95": pct(self.per_split[g]["prom"], [5, 95]),
                      "harmful_promotion_rate": float(harm / prom) if prom else None,
                      "correct_promotion_rate": float(good / prom) if prom else None, "promotions_total": int(prom)}
        draws = {"G1m-G2": [], "G1-G2m": []}
        for _ in range(BOOT):
            w = np.bincount(rng.integers(0, self.n, self.n), minlength=self.n).astype(float)
            hpr = {}
            for g in GATES:
                p = w @ self.acc[g]["prom"] @ w
                hpr[g] = (w @ self.acc[g]["harm"] @ w) / p if p else np.nan
            draws["G1m-G2"].append(hpr["G1m_pass1_top_matched_to_G2"] - hpr["G2_irt_1se"])
            draws["G1-G2m"].append(hpr["G1_pass1_1se"] - hpr["G2m_irt_top_matched_to_G1"])
        for key, (a, b) in {"G1m-G2": ("G1m_pass1_top_matched_to_G2", "G2_irt_1se"),
                            "G1-G2m": ("G1_pass1_1se", "G2m_irt_top_matched_to_G1")}.items():
            arr = np.asarray(draws[key], float)
            ra, rb = out[a]["harmful_promotion_rate"], out[b]["harmful_promotion_rate"]
            available = self.match_failures == 0 and ra is not None and rb is not None
            out[f"matched_{key}"] = {"hpr_difference_pass1_minus_irt": (ra - rb) if available else None,
                                     "ci95": pct(arr, [2.5, 97.5]) if available else None,
                                     "p_value": boot_p_two_sided(arr, 0.0) if available else None,
                                     "undefined_draws": int((~np.isfinite(arr)).sum()), "available": available,
                                     "test": f"system-cluster percentile bootstrap ({BOOT} draws), conditional on each split's selections"}
        return out


# ----------------------------------------------------------------------------- the run

class SizeAccumulator:
    """Per-split statistics and per-system error sums for one n_A."""

    def __init__(self, n_sys: int, arms=ARMS, keep: bool = False, splits: int = SPLITS):
        self.arms, self.keep = arms, keep
        self.rows: list[dict] = []
        self.rho = {a: [] for a in arms}
        self.sum = {a: {k: np.zeros(n_sys) for k in ("abs", "err", "sq", "f", "f2")} for a in arms if a in LEVEL_ARMS}
        self.extra = {a: {"pearson": [], "kendall": []} for a in arms}
        self.brier: list[dict] = []
        if keep:
            self.F = {a: np.empty((splits, n_sys)) for a in arms}
            self.Y = np.empty((splits, n_sys))
        self.count = 0

    def add(self, s: int, res: dict, extra_corr: bool) -> None:
        y = res["y"]
        if self.keep:
            self.Y[s] = y
        base_rho = spearman(rounded(res["f"]["pass1_A"]), y)
        for a in self.arms:
            f = res["f"][a]
            rho = spearman(rounded(f), y) if np.all(np.isfinite(f)) else None
            self.rho[a].append(rho)
            row = {"split": s, "arm": a, "spearman_vs_pass1_B": rho,
                   "delta_vs_pass1_A": None if rho is None or base_rho is None else rho - base_rho, "mae": None, "rmse": None, "bias": None}
            if a in LEVEL_ARMS:
                e = f - y
                for key, v in (("abs", np.abs(e)), ("err", e), ("sq", e**2), ("f", f), ("f2", f**2)):
                    self.sum[a][key] += v
                row.update(mae=float(np.abs(e).mean()), rmse=float(np.sqrt((e**2).mean())), bias=float(e.mean()))
            if extra_corr:
                self.extra[a]["pearson"].append(pearson(f, y))
                self.extra[a]["kendall"].append(kendall_tau_b(rounded(f), y))
            if self.keep:
                self.F[a][s] = rounded(f) if np.all(np.isfinite(f)) else np.nan
            self.rows.append(row)
        if "brier" in res:
            self.brier.append(res["brier"])
        self.count += 1

    def per_system(self, arm: str) -> dict[str, np.ndarray]:
        s, n = self.sum[arm], self.count
        return {"mae": s["abs"] / n, "bias": s["err"] / n, "rmse": np.sqrt(s["sq"] / n),
                "sd_forecast": np.sqrt(np.maximum((s["f2"] - s["f"] ** 2 / n) / (n - 1), 0.0))}

    def summary(self, rng: np.random.Generator) -> dict:
        out = {}
        rows = {a: [r for r in self.rows if r["arm"] == a] for a in self.arms}
        base_rho = self.rho["pass1_A"]
        base_sys = self.per_system("pass1_A")
        for a in self.arms:
            deltas = [r["delta_vs_pass1_A"] for r in rows[a]]
            entry = {"rank": rank_summary(deltas, self.rho[a], base_rho)}
            if self.extra[a]["pearson"]:
                entry["correlations_median_over_splits"] = {
                    "pearson": float(np.median([v for v in self.extra[a]["pearson"] if v is not None])),
                    "spearman": float(np.median([v for v in self.rho[a] if v is not None])),
                    "kendall_tau_b": float(np.median([v for v in self.extra[a]["kendall"] if v is not None]))}
            out[a] = entry
            if a not in LEVEL_ARMS:
                continue
            mae = np.array([r["mae"] for r in rows[a]])
            ps = self.per_system(a)
            bias_all = float(np.mean([r["bias"] for r in rows[a]]))
            entry |= {"level": {"mae_mean_over_splits": float(mae.mean()), "rmse_mean_over_splits": float(np.mean([r["rmse"] for r in rows[a]])),
                               "mean_bias_forecast_minus_heldout": bias_all,
                               "mean_forecast": float(self.sum[a]["f"].sum() / (self.count * len(ps["mae"]))),
                               "mean_heldout_pass1": float(self.sum[a]["f"].sum() / (self.count * len(ps["mae"])) - bias_all),
                               "per_system_sd_of_forecast_across_splits_mean": float(ps["sd_forecast"].mean())}}
            out[a] = entry
            if a != "pass1_A":
                base_mae = np.array([r["mae"] for r in rows["pass1_A"]])
                entry["level"]["vs_pass1_A"] = level_compare(base_sys["mae"], ps["mae"], rng) | {
                    "splits_arm_mae_lower": int((mae < base_mae).sum()),
                    "split_mae_difference_p05_p95": pct(base_mae - mae, [5, 95]), "splits": len(mae)}
        return out


def score_size(scorer: SplitScorer, perms: np.ndarray, size: int, *, arms=ARMS, kinds=IRT_KINDS, controls=True, within=None,
               detail=False, gates: GateAccumulator | None = None, log=print) -> SizeAccumulator:
    acc = SizeAccumulator(scorer.d.n_sys, arms, keep=detail, splits=len(perms))
    t0 = time.time()
    for s, perm in enumerate(perms):
        a_items, b_items = perm[:size], perm[size:]
        res = scorer.run(a_items, b_items, kinds=kinds, controls=controls, detail=detail)
        for kind, w in (within or {}).items():
            res["f"][f"{kind}_within_A"] = w["theta"][s]
        acc.add(s, res, extra_corr=detail)
        if gates is not None:
            w = within["2pl"]
            gates.add(scorer.d.R[:, a_items], res["f"]["pass1_A"], res["y"], w["theta"][s], w["psd"][s])
        if (s + 1) % 500 == 0:
            log(f"  n_A={size}: {s + 1}/{len(perms)} splits ({time.time() - t0:.0f}s)")
    return acc


def item_param_stability(fits: list[dict]) -> dict:
    """Pairwise agreement of item parameters across the K fold fits (slopes and resolved-boundary locations)."""
    params = [irt.unpack(f["kind"], f["x"], f["n_items"]) for f in fits]
    loc = [-(p[2] if f["kind"] == "grm3" else p[1]) / p[0] for f, p in zip(fits, params)]
    slope = [p[0] for p in params]
    out = {}
    for name, vals in (("location_b", loc), ("slope_a", slope)):
        if fits[0]["kind"] == "1pl" and name == "slope_a":
            out[name] = {"values": [float(v[0]) for v in vals]}
            continue
        pr = [pearson(vals[i], vals[j]) for i in range(K) for j in range(i + 1, K)]
        sr = [spearman(vals[i], vals[j]) for i in range(K) for j in range(i + 1, K)]
        out[name] = {"pearson_mean": float(np.mean(pr)), "pearson_min": float(np.min(pr)),
                     "spearman_mean": float(np.mean(sr)), "spearman_min": float(np.min(sr))}
    return out


def rank_rule(deltas: list) -> bool:
    """Experiment 07's H2 rule over all splits: median of defined Δ > 0 and share(Δ > 0) ≥ 0.60 (undefined = not positive)."""
    dv = np.asarray([v for v in deltas if v is not None], float)
    return bool(len(dv) and np.median(dv) > 0 and (dv > 0).sum() / len(deltas) >= SHARE_RULE)


class RaschCheckFailed(RuntimeError):
    """The common-parameter Rasch forecast did not tie pass@1 on half A in rank: a code defect, so the run stops."""

    def __init__(self, size: int, nonzero: int):
        super().__init__(f"Rasch common-parameter check failed: {nonzero} splits with nonzero rank difference at n_A = {size}")
        self.size, self.nonzero = size, nonzero


def primary_verdicts(summary50: dict, boot50: dict, rank_arm: str, level_arm: str, *, rank_deltas: list,
                     failed_splits: list, level_gates: dict) -> dict:
    """Frozen rules with their numerical gates.

    Rank: failed within-half fits leave their splits undefined; the decision is also recomputed with every failed
    split at its worst (Δ = -inf) and best (Δ = +inf) case, and it stands only if both bounds agree and at most 1%
    of fits failed. Level: valid only if every K-fold fit of the level arm converged on both grids, no scored
    posterior exceeded the endpoint-mass bound, and check-grid rescoring stayed within tolerance.
    """
    rank, level = summary50[rank_arm]["rank"], summary50[level_arm]["level"]["vs_pass1_A"]
    failed = set(failed_splits)
    worst = rank_rule([-np.inf if s in failed else v for s, v in enumerate(rank_deltas)])
    best = rank_rule([np.inf if s in failed else v for s, v in enumerate(rank_deltas)])
    if len(failed) > WITHIN_FAIL_SHARE * len(rank_deltas):
        rank_status = f"inconclusive ({len(failed)} of {len(rank_deltas)} within-half fits failed, above 1%)"
    elif worst != best:
        rank_status = "inconclusive (the decision depends on failed within-half fits)"
    else:
        rank_status = "holds" if worst else "fails"
    level_ok = level["mae_difference"] > 0 and level["ci95"][0] > 0
    level_status = ("holds" if level_ok else "fails") if level_gates["valid"] else f"inconclusive ({level_gates['reason']})"
    return {"rank_arm": rank_arm, "level_arm": level_arm,
            "rank_rule": "median Δ > 0 and share(Δ > 0) ≥ 0.60 over 2,000 splits at n_A = 50 (experiment 07's frozen H2 rule)",
            "rank_status": rank_status, "rank_holds": rank_status == "holds", "rank_provisional_holds": rank_rule(rank_deltas),
            "rank_bounds_failed_splits_worst_best": [worst, best], "rank_failed_splits": sorted(failed),
            "rank": rank, "rank_bootstrap": boot50.get(rank_arm),
            "level_rule": "mean per-system absolute error lower than pass@1 on A, 95% system-bootstrap interval of the difference excluding 0",
            "level_status": level_status, "level_holds": level_status == "holds", "level_gates": level_gates, "level": level}


def q1_verdict(primary: dict, beyond_panel: bool) -> str:
    """CONTINUE if a valid rule holds; NO ADVANTAGE if both valid rules fail; INCONCLUSIVE otherwise."""
    r, lv = primary["rank_status"], primary["level_status"]
    held = [name for name, s in (("rank", r), ("level", lv)) if s == "holds"]
    if held:
        text = f"CONTINUE: 2PL forecasts held-out pass@1 better than pass@1 on half A ({' and '.join(held)} rule holds)"
        if lv == "holds":
            text += ("; the level gain also exceeds the non-IRT linear-regression forecast from the same reference systems"
                     if beyond_panel else
                     "; the level gain is not shown to exceed a non-IRT linear-regression forecast from the same reference systems, "
                     "so it is credited to using the reference panel, not to item-level IRT information")
        return text
    if r == "fails" and lv == "fails":
        return "NO ADVANTAGE: 2PL does not forecast held-out pass@1 better than pass@1 on half A by either frozen rule"
    return f"INCONCLUSIVE: rank {r}; level {lv}"



def run(d: Data, perms: dict[int, np.ndarray], runner: Runner, *, sensitivity_rows: np.ndarray | None, log=print) -> tuple[dict, dict, dict]:
    """Primary, secondary, stability and sensitivity analyses. Returns (analysis, per-split rows, fitted K-fold models)."""
    out: dict = {"timing_seconds": {}}
    t_all = time.time()
    fold = assign_folds(d.n_sys, FOLD_SEEDS[0])
    fits = {}
    for kind in IRT_KINDS:
        log(f"fitting {kind} (fold seed {FOLD_SEEDS[0]})")
        fits[kind] = fit_folds(kind, d, fold, runner, log)
    out["timing_seconds"]["primary_fits"] = round(time.time() - t_all, 1)
    out["fold_of_system"] = fold.tolist()
    out["fits"] = {kind: [{k: v for k, v in f.items() if k != "x"} for f in fs] for kind, fs in fits.items()}
    out["all_primary_fits_converged"] = all(f["converged"] for fs in fits.values() for f in fs)
    out["item_parameter_stability_across_folds"] = {kind: item_param_stability(fs) for kind, fs in fits.items()}
    scorer, rng, gates = SplitScorer(d, fold, fits), np.random.default_rng([SEED, 2]), GateAccumulator(d.n_sys)
    sizes, rows, within_report = {}, {}, {}
    for size in SIZES:
        t0 = time.time()
        log(f"n_A={size}: within-half fits ({', '.join(WITHIN_KINDS)}) on {len(perms[size])} splits")
        within = {kind: within_half(kind, d, perms[size], size, runner) for kind in WITHIN_KINDS}
        within_report[str(size)] = {kind: {k: v for k, v in w.items() if k not in ("theta", "psd")} for kind, w in within.items()}
        out["timing_seconds"][f"within_half_fits_n{size}"] = round(time.time() - t0, 1)
        t0 = time.time()
        scorer.endpoint = {kind: {"max": 0.0, "violations": 0} for kind in fits}
        acc = score_size(scorer, perms[size], size, within=within, detail=size == PRIMARY,
                         gates=gates if size == PRIMARY else None, log=log)
        nonzero = sum(1 for r in acc.rows if r["arm"] == "rasch_common_check" and r["delta_vs_pass1_A"] != 0)
        if nonzero:
            raise RaschCheckFailed(size, nonzero)
        sizes[str(size)] = {"n_A": size, "n_B": d.n_tasks - size, "rasch_common_check_nonzero_delta_splits": nonzero,
                            "within_half_fits": within_report[str(size)], "kfold_endpoint_mass": scorer.endpoint, "arms": acc.summary(rng)}
        rows[size] = acc.rows
        if size == PRIMARY:
            acc50 = acc
        out["timing_seconds"][f"score_n{size}"] = round(time.time() - t0, 1)
    out["sizes"] = sizes
    t0 = time.time()
    out["kfold_rescore_check_n50"] = scorer.rescore_check(perms[PRIMARY], PRIMARY)
    out["timing_seconds"]["kfold_rescore_check_n50"] = round(time.time() - t0, 1)
    t0 = time.time()
    boot50 = bootstrap_rank({a: acc50.F[a] for a in ("2pl_within_A", "grm3_within_A", "2pl")}, acc50.F["pass1_A"], acc50.Y,
                            np.random.default_rng([SEED, 3]), draws=BOOT)
    out["timing_seconds"]["rank_bootstrap_n50"] = round(time.time() - t0, 1)
    s50 = sizes[str(PRIMARY)]["arms"]

    def level_gates(kind: str) -> dict:
        conv = all(f["converged"] for f in fits[kind])
        em = sizes[str(PRIMARY)]["kfold_endpoint_mass"][kind]
        rs = out["kfold_rescore_check_n50"][kind]
        reasons = [r for r, bad in (("K-fold fit not converged on both grids", not conv),
                                    (f"{em['violations']} posteriors above the endpoint-mass bound", em["violations"] > 0),
                                    ("check-grid rescoring change above tolerance", not rs["ok"])) if bad]
        return {"valid": not reasons, "reason": "; ".join(reasons) or None, "fits_converged": conv, "endpoint_mass": em, "rescore_check": rs}

    def deltas(arm: str) -> list:
        return [r["delta_vs_pass1_A"] for r in rows[PRIMARY] if r["arm"] == arm]

    # Controls that also read the reference panel: does IRT add beyond a difficulty shift or linear shrinkage?
    rng_c = np.random.default_rng([SEED, 4])
    per_sys50 = {a: acc50.per_system(a) for a in LEVEL_ARMS}
    out["irt_vs_reference_panel_controls_n50"] = {
        ctl: {arm: level_compare(per_sys50[ctl]["mae"], per_sys50[arm]["mae"], rng_c) for arm in IRT_KINDS}
        for ctl in ("mean_equating", "linear_regression")}
    for key, rank_arm, level_arm in (("primary_2pl_n50", "2pl_within_A", "2pl"), ("key_secondary_grm3_n50", "grm3_within_A", "grm3")):
        kind = level_arm
        out[key] = primary_verdicts(s50, boot50, rank_arm, level_arm, rank_deltas=deltas(rank_arm),
                                    failed_splits=within_report[str(PRIMARY)][kind]["failed_splits"], level_gates=level_gates(level_arm))
    out["kfold_2pl_rank_bootstrap_n50"] = boot50["2pl"]
    lr2 = out["irt_vs_reference_panel_controls_n50"]["linear_regression"]["2pl"]
    out["level_win_beyond_reference_panel"] = bool(out["primary_2pl_n50"]["level_holds"] and lr2["mae_difference"] > 0 and lr2["ci95"][0] > 0)
    out["q1_verdict"] = q1_verdict(out["primary_2pl_n50"], out["level_win_beyond_reference_panel"])
    out["q1_continue"] = out["q1_verdict"].startswith("CONTINUE")
    out["q1_inconclusive"] = out["q1_verdict"].startswith("INCONCLUSIVE")

    # Stability: each system's forecast spread across random halves A, fold seeds, and item parameters across folds.
    sd_err = {a: (acc50.F[a] - acc50.Y).std(0, ddof=1) for a in LEVEL_ARMS}
    stab = {"pass1_A": {"mean_sd_forecast": float(per_sys50["pass1_A"]["sd_forecast"].mean()), "mean_sd_error": float(sd_err["pass1_A"].mean())}}
    for a in LEVEL_ARMS[1:]:
        ratios = []
        for _ in range(BOOT):
            i = rng_c.integers(0, d.n_sys, d.n_sys)
            ratios.append(sd_err[a][i].mean() / sd_err["pass1_A"][i].mean())
        stab[a] = {"mean_sd_forecast": float(per_sys50[a]["sd_forecast"].mean()), "mean_sd_error": float(sd_err[a].mean()),
                   "ratio_mean_sd_error_to_pass1_A": float(sd_err[a].mean() / sd_err["pass1_A"].mean()),
                   "ratio_ci95": pct(ratios, [2.5, 97.5])}
    out["split_variability_n50"] = stab
    p2 = s50["2pl"]
    seed_rows = [{"fold_seed": FOLD_SEEDS[0], "kfold_rank_median_delta": p2["rank"]["delta_median"],
                  "kfold_rank_share_delta_positive": p2["rank"]["share_delta_positive"],
                  "mae_difference": p2["level"]["vs_pass1_A"]["mae_difference"], "mae_difference_ci95": p2["level"]["vs_pass1_A"]["ci95"],
                  "all_fits_converged": all(f["converged"] for f in fits["2pl"])}]
    for fs in FOLD_SEEDS[1:]:
        t0 = time.time()
        log(f"fold-seed stability: 2pl with fold seed {fs}")
        fold_s = assign_folds(d.n_sys, fs)
        fits_s = fit_folds("2pl", d, fold_s, runner, log)
        summ = score_size(SplitScorer(d, fold_s, {"2pl": fits_s}), perms[PRIMARY], PRIMARY, arms=("pass1_A", "2pl"), kinds=("2pl",),
                          controls=False, log=log).summary(np.random.default_rng([SEED, 5, fs]))["2pl"]
        seed_rows.append({"fold_seed": fs, "kfold_rank_median_delta": summ["rank"]["delta_median"],
                          "kfold_rank_share_delta_positive": summ["rank"]["share_delta_positive"],
                          "mae_difference": summ["level"]["vs_pass1_A"]["mae_difference"], "mae_difference_ci95": summ["level"]["vs_pass1_A"]["ci95"],
                          "all_fits_converged": all(f["converged"] for f in fits_s)})
        out["timing_seconds"][f"fold_seed_{fs}"] = round(time.time() - t0, 1)
    out["fold_seed_stability_2pl_n50"] = seed_rows
    out["promotion_gates_n50"] = gates.summary(np.random.default_rng([SEED, 7]))
    out["heldout_cell_brier_n50"] = {k: float(np.mean([b[k] for b in acc50.brier])) for k in acc50.brier[0]}
    if sensitivity_rows is not None:
        t0 = time.time()
        sub = d.subset(sensitivity_rows)
        log(f"sensitivity: one system per base model ({sub.n_sys} systems)")
        fold_sub = assign_folds(sub.n_sys, FOLD_SEEDS[0], stream=6)
        fits_sub = fit_folds("2pl", sub, fold_sub, runner, log)
        w_sub = {"2pl": within_half("2pl", sub, perms[PRIMARY], PRIMARY, runner)}
        summ = score_size(SplitScorer(sub, fold_sub, {"2pl": fits_sub}), perms[PRIMARY], PRIMARY, arms=("pass1_A", "2pl_within_A", "2pl"),
                          kinds=("2pl",), controls=False, within=w_sub, log=log).summary(np.random.default_rng([SEED, 8]))
        out["sensitivity_one_system_per_base_model_n50"] = {
            "n_systems": sub.n_sys, "systems": sub.systems, "all_fits_converged": all(f["converged"] for f in fits_sub),
            "within_half_fits": {k: v for k, v in w_sub["2pl"].items() if k not in ("theta", "psd")},
            "pass1_A": summ["pass1_A"], "2pl_within_A": summ["2pl_within_A"], "2pl": summ["2pl"],
            "fits": [{k: v for k, v in f.items() if k != "x"} for f in fits_sub]}
        out["timing_seconds"]["sensitivity"] = round(time.time() - t0, 1)
    out["timing_seconds"]["total"] = round(time.time() - t_all, 1)
    return out, rows, fits


# ----------------------------------------------------------------------------- outputs

def strict(obj):
    """JSON-safe copy: numpy scalars to Python, non-finite floats to None."""
    if isinstance(obj, dict):
        return {str(k): strict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [strict(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return strict(obj.tolist())
    if isinstance(obj, (np.floating, float)):
        return float(obj) if np.isfinite(obj) else None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def lookup(tree: dict, path: list):
    for key in path:
        if not isinstance(tree, (dict, list)):
            return None
        tree = tree[key] if isinstance(tree, list) else tree.get(str(key))
    return tree


def evaluate_forecast(analysis: dict, forecast: dict) -> list[dict]:
    """Each frozen prediction against its outcome: inside its 80% interval or not (failed forecasts reported alike)."""
    out = []
    invalid = not str(analysis.get("status", "")).startswith(("PRIMARY", "SYNTHETIC"))
    for p in forecast.get("predictions", []):
        if invalid:
            out.append({"id": p["id"], "outcome": None, "note": f"unavailable: invalid analysis ({analysis.get('status')})"})
            continue
        value = lookup(analysis, p["path"]) if "path" in p else None
        row = {"id": p["id"], "outcome": value, "point": p.get("point"), "interval80": p.get("interval80"), "probability": p.get("probability")}
        if isinstance(value, bool) and "probability" in p:
            row["note"] = "event occurred" if value else "event did not occur"
        elif isinstance(value, (int, float)) and p.get("interval80"):
            lo, hi = p["interval80"]
            row["inside_interval80"] = bool(lo <= value <= hi)
        out.append(row)
    return out


def fmt(x, nd=3, signed=False) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join(fmt(v, nd, signed) for v in x) + "]"
    return f"{x:+.{nd}f}" if signed else f"{x:.{nd}f}"


def ci(entry: dict, key="mae_difference", nd=4) -> str:
    """x [lo, hi] p-val=Z with the system-bootstrap p-value (null: zero mean difference)."""
    return f"{fmt(entry[key], nd, True)} {fmt(entry['ci95'], nd, True)} p-val={fmt(entry.get('p_value'), 4)}"


SCOPE = ("Intervals resample whole systems (164, or 73 in the sensitivity analysis) with the fitted item parameters, fold "
         "assignments, control fits and task splits held fixed; they are not intervals for a refitted procedure, unseen tasks "
         "or new model families. Split percentiles describe the 2,000 random halves and are not population intervals.")


def render(a: dict) -> str:
    """Markdown tables for results.md from analysis_e14.json."""
    L = ["# Experiment 14 result tables (rendered from `analysis_e14.json`)", "",
         f"Status: **{a['status']}**. Q1 verdict: **{a.get('q1_verdict', 'n/a')}**.", ""]
    if "level_win_beyond_reference_panel" in a:
        L += ["Level-win attribution (frozen interpretation rule): the K-fold 2PL level gain "
              + ("**exceeds** the non-IRT linear-regression forecast from the same reference systems, so it reflects item-level IRT information."
                 if a["level_win_beyond_reference_panel"] else
                 "**is not shown to exceed** the non-IRT linear-regression forecast from the same reference systems (or the level rule did not "
                 "hold), so no item-level IRT information beyond using the reference panel is established."), "", SCOPE, ""]
    v = a["validity"]
    L += ["## Validity", "", "| Check | Value |", "|---|---|"]
    for k, val in v.items():
        L.append(f"| {k} | {json.dumps(val) if not isinstance(val, str) else val} |")
    if "sizes" not in a:
        return "\n".join(L) + "\n"
    P = a["primary_2pl_n50"]
    rk, lv, bt = P["rank"], P["level"], P["rank_bootstrap"]
    s50 = a["sizes"]["50"]["arms"]
    L += ["", f"## Primary (2PL versus pass@1 on half A, n_A = 50, {rk['splits']} splits, {lv['n_systems']} systems)", "",
          f"Rank arm `{P['rank_arm']}` (2PL refitted on half A of every system, no half-B data); level arm `{P['level_arm']}` "
          "(2PL item parameters from the other folds' systems, all tasks).", "",
          f"- Rank rule ({P['rank_rule']}): **{P['rank_status']}** (failed within-half fits: {len(P['rank_failed_splits'])}; "
          f"decision with failed splits at worst/best: {P['rank_bounds_failed_splits_worst_best']}). Median Δ {fmt(rk['delta_median'], 4, True)} "
          f"{fmt(bt['delta_median_ci95'], 4, True)} p-val={fmt(bt['delta_median_p_value'], 4)} (system-cluster bootstrap); split 5th–95th "
          f"{fmt(rk['delta_p05_p95'], 4, True)}; Δ > 0 in {rk['positive_splits']}/{rk['splits']} splits = {fmt(rk['share_delta_positive'], 3)} "
          f"{fmt(bt['share_ci95'], 3)} p-val={fmt(bt['share_p_value_vs_0.60'], 4)} (bootstrap, null share 0.60); median Spearman "
          f"{fmt(rk['spearman_arm_A_vs_pass1_B_median'], 4)} versus {fmt(rk['spearman_pass1_A_vs_pass1_B_median'], 4)} for pass@1 on A.",
          f"- Level rule ({P['level_rule']}): **{P['level_status']}** (numerical gates valid: {P['level_gates']['valid']}). Mean absolute error {fmt(s50['pass1_A']['level']['mae_mean_over_splits'], 4)} "
          f"(pass@1 on A) versus {fmt(s50['2pl']['level']['mae_mean_over_splits'], 4)} (2PL); difference {ci(lv)} ({lv['test']}); "
          f"2PL closer for {lv['systems_arm_better']}/{lv['n_systems']} systems and lower in {lv['splits_arm_mae_lower']}/{lv['splits']} splits.",
          f"- Mean bias (forecast minus held-out pass@1): pass@1 on A {fmt(s50['pass1_A']['level']['mean_bias_forecast_minus_heldout'], 4, True)}, "
          f"2PL {fmt(s50['2pl']['level']['mean_bias_forecast_minus_heldout'], 4, True)}; mean forecast {fmt(s50['2pl']['level']['mean_forecast'], 4)} "
          f"versus mean held-out pass@1 {fmt(s50['2pl']['level']['mean_heldout_pass1'], 4)}.", ""]
    G = a["key_secondary_grm3_n50"]
    L += [f"Key secondary (graded response model on resolved plus partial credit): rank rule **{G['rank_status']}** "
          f"(median Δ {fmt(G['rank']['delta_median'], 4, True)} {fmt(G['rank_bootstrap']['delta_median_ci95'], 4, True)}, share "
          f"{fmt(G['rank']['share_delta_positive'], 3)}); level rule **{G['level_status']}** (difference {ci(G['level'])}).", ""]
    gate_lines = []
    for s, blk in a["sizes"].items():
        for kind, w in blk["within_half_fits"].items():
            gate_lines.append(f"| {s} | within-half {kind} | {w['failed']}/{w['fits']} failed | {fmt(w['check_grid_max_abs_grad_max'], 7)} | "
                              f"{w['endpoint_mass_max']:.1e} | {w['rescore_max_abs_change_max']:.1e} |")
        for kind, em in blk["kfold_endpoint_mass"].items():
            gate_lines.append(f"| {s} | K-fold {kind} | {em['violations']} endpoint violations | — | {em['max']:.1e} | — |")
    for kind, rs in a.get("kfold_rescore_check_n50", {}).items():
        gate_lines.append(f"| 50 | K-fold {kind} rescoring ({rs['splits_checked']} splits) | ok={rs['ok']} | — | — | {rs['max_abs_change']:.1e} |")
    L += ["Numerical gates (tolerances: gradient 1e-4 on both grids, endpoint mass 1e-8, rescoring change 1e-6):", "",
          "| n_A | Fits | Status | Max check-grid gradient | Max endpoint mass | Max rescoring change |", "|---:|---|---|---:|---:|---:|",
          *gate_lines, ""]
    L += ["## Rank: Δ = Spearman(arm forecast, pass@1 on B) − Spearman(pass@1 on A, pass@1 on B)", "",
          "| n_A | Arm | Median Δ | 5th–95th | Splits Δ > 0 | Share | Exact-zero splits | Median Spearman (arm) | Median Spearman (pass@1 on A) |",
          "|---:|---|---:|---|---:|---:|---:|---:|---:|"]
    for size, blk in a["sizes"].items():
        for arm, e in blk["arms"].items():
            if arm == "pass1_A":
                continue
            r = e["rank"]
            L.append(f"| {size} | {arm} | {fmt(r['delta_median'], 4, True)} | {fmt(r['delta_p05_p95'], 4, True)} | {r['positive_splits']}/{r['splits']} | "
                     f"{fmt(r['share_delta_positive'], 3)} | {r['exact_zero_splits']} | {fmt(r['spearman_arm_A_vs_pass1_B_median'], 4)} | "
                     f"{fmt(r['spearman_pass1_A_vs_pass1_B_median'], 4)} |")
    L += ["", "## Level: forecast of each system's pass@1 on half B", "",
          "| n_A | Arm | MAE | RMSE | Mean bias | MAE(pass@1 on A) − MAE(arm) [95% CI] p-val | Systems closer | Splits lower |",
          "|---:|---|---:|---:|---:|---|---:|---:|"]
    for size, blk in a["sizes"].items():
        for arm, e in blk["arms"].items():
            if "level" not in e:
                continue
            lvl = e["level"]
            cmp = lvl.get("vs_pass1_A")
            L.append(f"| {size} | {arm} | {fmt(lvl['mae_mean_over_splits'], 4)} | {fmt(lvl['rmse_mean_over_splits'], 4)} | "
                     f"{fmt(lvl['mean_bias_forecast_minus_heldout'], 4, True)} | {ci(cmp) if cmp else '—'} | "
                     f"{(str(cmp['systems_arm_better']) + '/' + str(cmp['n_systems'])) if cmp else '—'} | {(str(cmp['splits_arm_mae_lower']) + '/' + str(cmp['splits'])) if cmp else '—'} |")
    L += ["", "## Correlations with pass@1 on B at n_A = 50 (medians over splits)", "", "| Arm | Pearson | Spearman | Kendall τ-b |", "|---|---:|---:|---:|"]
    for arm, e in s50.items():
        c = e.get("correlations_median_over_splits")
        if c:
            L.append(f"| {arm} | {fmt(c['pearson'], 4)} | {fmt(c['spearman'], 4)} | {fmt(c['kendall_tau_b'], 4)} |")
    L += ["", "## IRT versus reference-panel controls at n_A = 50 (positive = IRT closer to held-out pass@1)", "",
          "| Control | IRT arm | MAE(control) − MAE(IRT) [95% CI] p-val | Systems where IRT closer |", "|---|---|---|---:|"]
    for ctl, blk in a["irt_vs_reference_panel_controls_n50"].items():
        for arm, e in blk.items():
            L.append(f"| {ctl} | {arm} | {ci(e)} | {e['systems_arm_better']}/{e['n_systems']} |")
    g = a["promotion_gates_n50"]
    L += ["", "## Promotion gates at n_A = 50 (ordered pairs; harmful = candidate below incumbent on half B)", "",
          f"Base rate if every pair were promoted: {fmt(g['base_rate_harmful_if_promoted_at_random'], 4)}. Matched-count failures: "
          f"{g['matched_count_failures']}. {g['degenerate_convention']}.", "",
          "| Gate | Promotions per split (mean) | 5th–95th | Harmful-promotion rate | Correct-promotion rate |", "|---|---:|---|---:|---:|"]
    for name in GATES:
        e = g[name]
        L.append(f"| {name} | {fmt(e['promotions_per_split_mean'], 1)} | {fmt(e['promotions_per_split_p05_p95'], 0)} | "
                 f"{fmt(e['harmful_promotion_rate'], 4)} | {fmt(e['correct_promotion_rate'], 4)} |")
    for key in ("matched_G1m-G2", "matched_G1-G2m"):
        e = g[key]
        L.append(f"\n- {key}: harmful-rate difference (pass@1 gate minus IRT gate, positive = IRT safer) "
                 f"{fmt(e['hpr_difference_pass1_minus_irt'], 4, True)} {fmt(e['ci95'], 4, True)} p-val={fmt(e['p_value'], 4)} ({e['test']}).")
    sv = a["split_variability_n50"]
    L += ["", "## Stability", "", "Per-system standard deviation across the 2,000 halves A at n_A = 50 (lower = steadier estimator):", "",
          "| Arm | Mean SD of forecast | Mean SD of error | Ratio to pass@1 on A [95% CI] |", "|---|---:|---:|---|"]
    for arm in LEVEL_ARMS:
        e = sv[arm]
        L.append(f"| {arm} | {fmt(e['mean_sd_forecast'], 4)} | {fmt(e['mean_sd_error'], 4)} | "
                 f"{(fmt(e['ratio_mean_sd_error_to_pass1_A'], 3) + ' ' + fmt(e['ratio_ci95'], 3)) if 'ratio_ci95' in e else '1 (reference)'} |")
    L += ["", "Fold-seed stability of the primary 2PL comparison (n_A = 50):", "",
          "| Fold seed | K-fold 2PL median Δ | Share Δ > 0 | MAE difference [95% CI] | Fits converged |", "|---:|---:|---:|---|---|"]
    for r in a["fold_seed_stability_2pl_n50"]:
        L.append(f"| {r['fold_seed']} | {fmt(r['kfold_rank_median_delta'], 4, True)} | {fmt(r['kfold_rank_share_delta_positive'], 3)} | "
                 f"{fmt(r['mae_difference'], 4, True)} {fmt(r['mae_difference_ci95'], 4, True)} | {r['all_fits_converged']} |")
    L += ["", "Item-parameter agreement across the 10 fold fits (mean and minimum pairwise correlation):", "",
          "| Model | Parameter | Pearson mean | Pearson min | Spearman mean | Spearman min |", "|---|---|---:|---:|---:|---:|"]
    for kind, blk in a["item_parameter_stability_across_folds"].items():
        for par, e in blk.items():
            if "pearson_mean" in e:
                L.append(f"| {kind} | {par} | {fmt(e['pearson_mean'], 4)} | {fmt(e['pearson_min'], 4)} | {fmt(e['spearman_mean'], 4)} | {fmt(e['spearman_min'], 4)} |")
            else:
                L.append(f"| {kind} | {par} | common slope per fold: {fmt(e['values'], 3)} | | | |")
    sens = a.get("sensitivity_one_system_per_base_model_n50")
    if sens:
        r, lv = sens["2pl_within_A"]["rank"], sens["2pl"]["level"]["vs_pass1_A"]
        L += ["", f"## Sensitivity: one system per base model ({sens['n_systems']} systems, n_A = 50)", "",
              f"- 2PL (within half A) rank: median Δ {fmt(r['delta_median'], 4, True)}, Δ > 0 in {r['positive_splits']}/{r['splits']} = {fmt(r['share_delta_positive'], 3)}.",
              f"- 2PL (K-fold) level: MAE {fmt(sens['pass1_A']['level']['mae_mean_over_splits'], 4)} (pass@1 on A) versus {fmt(sens['2pl']['level']['mae_mean_over_splits'], 4)}; "
              f"difference {ci(lv)}; fits converged: {sens['all_fits_converged']}."]
    b = a["heldout_cell_brier_n50"]
    L += ["", "## Held-out cell Brier score at n_A = 50 (descriptive; lower is better)", "", "| Predictor | Brier |", "|---|---:|"]
    L += [f"| {k} | {fmt(val, 4)} |" for k, val in b.items()]
    if a.get("forecast_evaluation"):
        L += ["", "## Frozen forecast versus outcome", "", "| Prediction | Forecast | Outcome | Inside 80% interval |", "|---|---|---|---|"]
        for r in a["forecast_evaluation"]:
            fc = r["point"] if r.get("point") is not None else f"p={r.get('probability')}"
            fc = f"{fc} {r['interval80']}" if r.get("interval80") else fc
            L.append(f"| {r['id']} | {fc} | {r['outcome']} | {r.get('inside_interval80', r.get('note', '—'))} |")
    L += ["", "Timing (seconds): " + json.dumps(a.get("timing_seconds", {}))]
    return "\n".join(L) + "\n"


def write_outputs(out_dir: Path, analysis: dict, rows: dict, fits: dict, d: Data) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "analysis_e14.json").write_text(json.dumps(strict(analysis), indent=1, allow_nan=False) + "\n")
    with gzip.open(out_dir / "per_split_e14.csv.gz", "wt", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["n_A", "split", "arm", "spearman_vs_pass1_B", "delta_vs_pass1_A", "mae", "rmse", "bias"])
        for size, rs in rows.items():
            for r in rs:
                w.writerow([size, r["split"], r["arm"], *(None if v is None else repr(float(v)) for v in
                            (r["spearman_vs_pass1_B"], r["delta_vs_pass1_A"], r["mae"], r["rmse"], r["bias"]))])
    with gzip.open(out_dir / "fits_e14.json.gz", "wt") as fh:
        json.dump(strict({kind: [f | {"x": f["x"]} for f in fs] for kind, fs in fits.items()} | {"tasks": d.tasks, "systems": d.systems}), fh)
    (out_dir / "results_tables_e14.md").write_text(render(strict(analysis)))


def main() -> None:
    global BOOT, SIGNFLIPS
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=HERE / "results")
    ap.add_argument("--synthetic", type=int, default=None, help="pipeline test on 2PL-generated data (never a result)")
    ap.add_argument("--splits", type=int, default=SPLITS, help="synthetic runs only")
    ap.add_argument("--boot", type=int, default=BOOT, help="synthetic runs only")
    ap.add_argument("--render-only", action="store_true", help="re-render results_tables_e14.md from analysis_e14.json")
    ap.add_argument("--workers", type=int, default=1, help="processes for independent fits (results do not depend on it)")
    args = ap.parse_args()
    if args.render_only:
        analysis = json.loads((args.out_dir / "analysis_e14.json").read_text())
        (args.out_dir / "results_tables_e14.md").write_text(render(analysis))
        return
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    env = {"host": socket.gethostname(), "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
           "platform": platform.platform(), "started": started, "workers": args.workers,
           "thread_env": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}}
    if args.synthetic is None:
        if (args.splits, args.boot) != (SPLITS, BOOT):
            ap.error("the locked run uses 2,000 splits and 2,000 bootstrap draws")
        if not FORECAST.is_file() or not verify_forecast(FORECAST):
            raise SystemExit("STOP: the frozen forecast is missing or its hash does not verify")
        d, e07 = load_real()
        validity = {"systems": d.n_sys, "tasks": d.n_tasks, "cells": int(d.R.size), "inconsistent_cells": d.inconsistent_cells(),
                    "cells_by_graded_category": {str(c): int((d.cat == c).sum()) for c in range(3)},
                    "per_cell_sha256": PINS[PER_CELL.name], "analysis_e07_sha256": PINS[ANALYSIS_E07.name],
                    "forecast_sha256": FORECAST.with_suffix(".sha256").read_text().split()[0]}
        if {k: validity[k] for k in EXPECTED} != EXPECTED:
            raise SystemExit(f"STOP: cohort does not reproduce experiment 07 ({validity})")
        perms = replay_e07_splits(d.n_tasks, d.n_sys)
        repro = reproduce_e07_h2(d, e07["H2_held_out_prediction"], perms)
        validity["e07_h2_reproduction"] = repro
        if not (repro["e07_code_on_replayed_stream_equals_published_h2"] and repro["replayed_permutations_reproduce_published_medians_and_counts"]):
            raise SystemExit(f"STOP: the replayed splits do not reproduce experiment 07's H2 ({repro})")
        names = list(e07["sensitivity_one_system_per_base_model"]["systems"].values())
        sens_rows = np.array(sorted(d.systems.index(n) for n in names))
        forecast = json.loads(FORECAST.read_text())
    else:
        BOOT, SIGNFLIPS = args.boot, max(args.boot, 1000)
        d = synthetic(args.synthetic)
        perms = {s: p[: args.splits] for s, p in replay_e07_splits(d.n_tasks, d.n_sys).items()}
        validity = {"synthetic_seed": args.synthetic, "note": "2PL-generated stand-in data for pipeline tests; never a result",
                    "systems": d.n_sys, "tasks": d.n_tasks}
        sens_rows, forecast = np.arange(0, d.n_sys, 2)[:73], {}
    settings = {"seed_e07": SEED_E07, "splits": len(perms[PRIMARY]), "sizes": list(SIZES), "primary_n_A": PRIMARY, "seed": SEED, "folds": K,
                "fold_seeds": list(FOLD_SEEDS), "bootstrap_draws": BOOT, "signflip_draws": SIGNFLIPS,
                "base_grid": [irt.BASE.lo, irt.BASE.hi, irt.BASE.count], "check_grid": [irt.CHECK.lo, irt.CHECK.hi, irt.CHECK.count],
                "item_priors_sd": irt.PRIOR_SD, "grad_tol": irt.GRAD_TOL, "endpoint_tol": irt.ENDPOINT_TOL, "rescore_tol": irt.RESCORE_TOL,
                "within_fail_share": WITHIN_FAIL_SHARE, "rank_rounding_decimals": ROUND}
    head = {"experiment": EXPERIMENT, "settings": settings, "environment": env, "validity": validity}
    try:
        analysis, rows, fits = run(d, perms, Runner(args.workers), sensitivity_rows=sens_rows)
    except RaschCheckFailed as err:  # a code defect: keep the receipt, give no verdict or forecast outcome, exit non-zero
        receipt = {"status": f"STOP: {err} (code defect)"} | head | {"rasch_common_check": {"n_A": err.size, "nonzero_splits": err.nonzero}}
        receipt["forecast_evaluation"] = evaluate_forecast(receipt, forecast) if forecast else []
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "analysis_e14.json").write_text(json.dumps(strict(receipt), indent=1, allow_nan=False) + "\n")
        (args.out_dir / "results_tables_e14.md").write_text(render(strict(receipt)))
        print(receipt["status"])
        raise SystemExit(2)
    validity["all_primary_fits_converged"] = analysis["all_primary_fits_converged"]
    status = "PRIMARY ANALYSES COMPUTED" if args.synthetic is None else "SYNTHETIC PIPELINE TEST (not a result)"
    analysis = {"status": status} | head | analysis
    analysis["forecast_evaluation"] = evaluate_forecast(strict(analysis), forecast) if forecast else []
    analysis["environment"]["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_outputs(args.out_dir, analysis, rows, fits, d)
    print(json.dumps(strict({k: analysis.get(k) for k in ("status", "q1_verdict", "timing_seconds")}), indent=1))


if __name__ == "__main__":
    main()
