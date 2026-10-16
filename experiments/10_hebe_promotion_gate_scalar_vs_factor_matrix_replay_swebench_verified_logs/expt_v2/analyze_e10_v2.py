"""Experiment 10 v2: replay AlphaHebe-style promotion policies on experiment 07's SWE-bench Verified factor matrix,
fixing the 421-task matched_test_lists sensitivity shape check and adding out-of-fold 2PL IRT and 3-category GRM
validation ability / z-score promotion gates from experiment 14 (`fits_e14.json.gz`).

Everything here is deterministic given the frozen seeds in expt_v1/PROTOCOL.md and expt_v1/irt_e14.py; zero model calls.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import multiprocessing as mp
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP_DIR = HERE.parent
V1_DIR = EXP_DIR / "expt_v1"
REPO = EXP_DIR.parents[1]
E14_DIR = REPO / "experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/expt_v1"
for _p in (REPO / "src", E14_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import irt_e14 as irt  # noqa: E402

PER_CELL = REPO / "experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/results/per_cell_e07.jsonl.gz"
PER_CELL_SHA256 = "f064c3951860cf4d88879e7c3b81ec42c8b42780923c61198c71f98dc6463a4d"
FITS_E14 = E14_DIR / "results/fits_e14.json.gz"
FITS_E14_SHA256 = "912f1fb38f147657b933269c0d8278c62441b651153a5443484c4598c4d97c46"
ANALYSIS_E14 = E14_DIR / "results/analysis_e14.json"
DRIFT = V1_DIR / "inputs/test_list_drift_e07.json"

STRATIFIED = ("R0", "R1", "R2", "R3", "R3h", "R_irt2pl", "R_irt2pl_z", "R_grm3", "R_grm3_z")
UNSTRATIFIED = ("S0plus", "S1", "S2", "S3", "S_irt2pl", "S_irt2pl_z", "S_grm3", "S_grm3_z")
POLICIES = UNSTRATIFIED + STRATIFIED
CONTRASTS = (
    ("R0", "R2"),
    ("R2", "R3"),
    ("R0", "R3"),
    ("R0", "R3h"),
    ("R0", "R1"),
    ("R0", "R_irt2pl"),
    ("R0", "R_irt2pl_z"),
    ("R0", "R_grm3"),
    ("R0", "R_grm3_z"),
    ("R_irt2pl", "R2"),
    ("R_irt2pl", "R3"),
    ("R_grm3", "R2"),
    ("R_grm3", "R3"),
    ("S0plus", "R3"),
    ("S0plus", "R2"),
    ("S0plus", "S3"),
    ("S2", "S3"),
    ("S0plus", "S2"),
    ("S0plus", "S1"),
    ("S0plus", "S_irt2pl"),
    ("S0plus", "S_irt2pl_z"),
    ("S0plus", "S_grm3"),
    ("S0plus", "S_grm3_z"),
    ("S_irt2pl", "S2"),
    ("S_irt2pl", "S3"),
    ("S_grm3", "S2"),
    ("S_grm3", "S3"),
)
# Fix v1 bug: 3 of the 4 drift tasks in test_list_drift_e07.json belong to the 424-task common cohort, leaving 421 tasks.
EXPECTED_SHAPE = {"none": (164, 424), "matched_test_lists": (164, 421)}
COND_MAX = 1e10
RESID_TOL = 1e-12
MIN_PRED_PAIRS = 50
MIN_SUPPORT = 0.90


@dataclass
class Matrix:
    """Systems x tasks arrays: resolved r, gate g, gated fix gf = g*t_fix, gated keep gk = g*t_keep, cell score sc."""

    systems: list[str]
    tasks: list[str]
    r: np.ndarray
    g: np.ndarray
    gf: np.ndarray
    gk: np.ndarray
    sc: np.ndarray


def _fraction(x, what: str) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not 0.0 <= x <= 1.0:
        raise SystemExit(f"STOP: {what} must be a finite fraction in [0, 1], got {x!r}")
    return float(x)


def load_matrix(path: Path = PER_CELL, expect_sha: str | None = PER_CELL_SHA256, drop_tasks: frozenset = frozenset()) -> Matrix:
    """Load the included-system, common-cohort cells of experiment 07 with complete-evidence checks (stop rules)."""
    raw = path.read_bytes()
    if expect_sha is not None and hashlib.sha256(raw).hexdigest() != expect_sha:
        raise SystemExit(f"STOP: input SHA-256 mismatch for {path}")
    rows = [json.loads(line) for line in gzip.decompress(raw).decode().splitlines() if line.strip()]
    cells = [x for x in rows if x["included"] and x["common_cohort"] and x["instance_id"] not in drop_tasks]
    keys = [(x["submission"], x["instance_id"]) for x in cells]
    if len(set(keys)) != len(keys):
        raise SystemExit("STOP: duplicate system/task cells")
    systems = sorted({k[0] for k in keys})
    tasks = sorted({k[1] for k in keys})
    si = {s: i for i, s in enumerate(systems)}
    ti = {t: j for j, t in enumerate(tasks)}
    shape = (len(systems), len(tasks))
    r, g, gf, gk, sc = (np.full(shape, np.nan) for _ in range(5))
    for x in cells:
        i, j = si[x["submission"]], ti[x["instance_id"]]
        gate, res = x["gate"], x["resolved"]
        if isinstance(gate, bool) or gate not in (0, 1):
            raise SystemExit(f"STOP: gate must be 0 or 1 for {x['submission']} {x['instance_id']}, got {gate!r}")
        if not isinstance(res, bool):
            raise SystemExit(f"STOP: resolved must be true/false for {x['submission']} {x['instance_id']}, got {res!r}")
        r[i, j] = float(res)
        g[i, j] = float(gate)
        if gate == 0:
            for key in ("t_fix", "t_keep"):
                if x[key] is not None:
                    _fraction(x[key], f"{key} {x['submission']} {x['instance_id']}")
            gf[i, j] = gk[i, j] = 0.0
        else:
            gf[i, j] = _fraction(x["t_fix"], f"t_fix {x['submission']} {x['instance_id']}")
            gk[i, j] = _fraction(x["t_keep"], f"t_keep {x['submission']} {x['instance_id']}")
        sc[i, j] = _fraction(x.get("score", math.sqrt(gf[i, j] * gk[i, j])), f"score {x['submission']} {x['instance_id']}")
    for name, arr in (("resolved", r), ("gate", g), ("gated t_fix", gf), ("gated t_keep", gk), ("score", sc)):
        if not np.isfinite(arr).all():
            raise SystemExit(f"STOP: incomplete systems x tasks matrix ({name})")
    return Matrix(systems, tasks, r, g, gf, gk, sc)


class OutOfFoldIRTScorer:
    """Out-of-fold 2PL and GRM3 validation ability scorer aligned to Matrix.tasks (zero test-half item leakage)."""

    def __init__(self, m: Matrix, fits_path: Path | None = FITS_E14, analysis_e14_path: Path | None = ANALYSIS_E14):
        self.m = m
        cat = np.where(m.r == 1, 2, np.where(m.sc > 0, 1, 0))
        self.cats_bin = [1.0 - m.r, m.r]
        self.cats_grm = [(cat == c).astype(float) for c in range(3)]
        if fits_path is not None and fits_path.is_file() and analysis_e14_path is not None and analysis_e14_path.is_file():
            fits_obj = json.loads(gzip.decompress(fits_path.read_bytes()).decode())
            e14_meta = json.loads(analysis_e14_path.read_text())
            if fits_obj["systems"] != m.systems:
                raise SystemExit("STOP: fits_e14 systems do not match Matrix.systems")
            fold = np.asarray(e14_meta["fold_of_system"], dtype=int)
            fits_tasks = fits_obj["tasks"]
            t_idx = np.array([fits_tasks.index(t) for t in m.tasks], dtype=int)
            self.K = int(fold.max()) + 1
            self.idx = [np.where(fold == k)[0] for k in range(self.K)]
            self.scorers: dict[str, list[irt.Scorer]] = {"2pl": [], "grm3": []}
            for kind in ("2pl", "grm3"):
                for f in fits_obj[kind]:
                    alpha, d, gamma = irt._split(kind, np.asarray(f["x"], dtype=float), len(fits_tasks))
                    x_sub = (
                        np.concatenate([alpha[t_idx], d[t_idx]])
                        if kind == "2pl"
                        else np.concatenate([alpha[t_idx], d[t_idx], gamma[t_idx]])
                    )
                    self.scorers[kind].append(irt.Scorer({"kind": kind, "x": x_sub, "n_items": len(t_idx)}))
        else:
            # Synthetic / standalone fallback: single-fold quick fit on the matrix
            self.K = 1
            self.idx = [np.arange(len(m.systems))]
            self.scorers = {
                "2pl": [irt.Scorer(irt.fit("2pl", self.cats_bin, maxiter=200, check=None))],
                "grm3": [irt.Scorer(irt.fit("grm3", self.cats_grm, maxiter=200, check=None))],
            }

    def score_validation(self, vi: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
        """Return (theta_eap, posterior_sd) on validation items `vi` for '2pl' and 'grm3'."""
        out: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        n_sys = len(self.m.systems)
        for kind, cats in (("2pl", self.cats_bin), ("grm3", self.cats_grm)):
            theta = np.empty(n_sys, dtype=np.float64)
            psd = np.empty(n_sys, dtype=np.float64)
            for k, rows in enumerate(self.idx):
                sc = self.scorers[kind][k]
                post = sc.posterior([c[rows] for c in cats], vi)
                th_k, sd_k = sc.eap(post)
                theta[rows] = th_k
                psd[rows] = sd_k
            out[kind] = (theta, psd)
        return out


def pair_hash(systems: list[str]) -> np.ndarray:
    """Outcome-independent tie-break key per ordered pair (incumbent row, candidate column)."""
    n = len(systems)
    h = np.zeros((n, n), dtype=np.float64)
    for i, a in enumerate(systems):
        for j, b in enumerate(systems):
            h[i, j] = int.from_bytes(hashlib.sha256(f"{a}->{b}".encode()).digest()[:6], "big")
    return h


@dataclass
class PairTensors:
    """Per-pair, per-task quantities precomputed once over all tasks (incumbent axis 0, candidate axis 1)."""

    drop_total: np.ndarray
    drop_hidden: np.ndarray
    drop_keep_hidden: np.ndarray
    drop_gate_loss: np.ndarray


def pair_tensors(m: Matrix) -> PairTensors:
    """Drop tensors used for the factor-regression penalties (float32 to bound memory)."""
    def drop(a: np.ndarray) -> np.ndarray:
        return np.maximum(0.0, a[:, None, :] - a[None, :, :]).astype(np.float32)

    total = drop(m.g) + drop(m.gf) + drop(m.gk)
    joint_unresolved = ((1 - m.r)[:, None, :] * (1 - m.r)[None, :, :]).astype(np.float32)
    gate_loss = (m.g[:, None, :] * (1 - m.g)[None, :, :]).astype(np.float32)
    return PairTensors(total, total * joint_unresolved, drop(m.gk) * joint_unresolved, total * gate_loss)


def make_splits(n_tasks: int, n_splits: int, seed: int) -> np.ndarray:
    """Boolean matrix (splits x tasks): True = validation half (floor(n/2) tasks), False = test half."""
    rng = np.random.default_rng(seed)
    half = n_tasks // 2
    out = np.zeros((n_splits, n_tasks), dtype=bool)
    for s in range(n_splits):
        out[s, rng.permutation(n_tasks)[:half]] = True
    return out


def system_summary(m: Matrix, cols: np.ndarray) -> dict[str, np.ndarray]:
    """Per-system pass@1, gate rate, gated factor means and SCS4C-T (geometric mean of gated factor means, D-009)."""
    p = m.r[:, cols].mean(1)
    gr = m.g[:, cols].mean(1)
    fm = m.gf[:, cols].mean(1)
    km = m.gk[:, cols].mean(1)
    scs = np.where((fm > 0) & (km > 0), np.sqrt(np.where(fm > 0, fm, 1) * np.where(km > 0, km, 1)), 0.0)
    return {"pass1": p, "gate": gr, "fix": fm, "keep": km, "scs": scs}


def _signed_z(dtheta: np.ndarray, se: np.ndarray) -> np.ndarray:
    out = np.zeros_like(dtheta, dtype=np.float64)
    pos = se > 0
    out[pos] = dtheta[pos] / se[pos]
    out[~pos & (dtheta > 0)] = np.inf
    out[~pos & (dtheta < 0)] = -np.inf
    return out


def split_pairs(
    m: Matrix,
    pt: PairTensors,
    irt_scorer: OutOfFoldIRTScorer,
    val: np.ndarray,
    near_max_gain: int,
) -> dict[str, np.ndarray]:
    """All pair statistics for one split as S x S arrays (incumbent rows, candidate columns)."""
    vi, ti = np.flatnonzero(val), np.flatnonzero(~val)
    nv, nt = len(vi), len(ti)
    rv, rt = m.r[:, vi], m.r[:, ti]
    gains_v = (1 - rv) @ rv.T
    losses_v = rv @ (1 - rv).T
    losses_t = rt @ (1 - rt).T
    gains_t = (1 - rt) @ rt.T
    net_v = gains_v - losses_v
    s = m.r.shape[0]
    flat = lambda a: a.reshape(s * s, -1)  # noqa: E731
    vmask = val.astype(np.float32)
    trm = (flat(pt.drop_total) @ vmask).reshape(s, s) / nv
    hrm = (flat(pt.drop_hidden) @ vmask).reshape(s, s) / nv
    krm = (flat(pt.drop_keep_hidden) @ vmask).reshape(s, s) / nv
    glm = (flat(pt.drop_gate_loss) @ vmask).reshape(s, s) / nv
    sv = system_summary(m, vi)
    irt_v = irt_scorer.score_validation(vi)
    th2, sd2 = irt_v["2pl"]
    thg, sdg = irt_v["grm3"]
    inc, cand = np.meshgrid(np.arange(s), np.arange(s), indexing="ij")
    dtheta_2pl = th2[cand] - th2[inc]
    ztheta_2pl = _signed_z(dtheta_2pl, np.sqrt(sd2[cand] ** 2 + sd2[inc] ** 2))
    dtheta_grm3 = thg[cand] - thg[inc]
    ztheta_grm3 = _signed_z(dtheta_grm3, np.sqrt(sdg[cand] ** 2 + sdg[inc] ** 2))
    eligible = (inc != cand) & (net_v > 0)
    near = eligible & (net_v <= near_max_gain)
    return {
        "inc": inc,
        "cand": cand,
        "net_v": net_v,
        "gains_v": gains_v,
        "losses_v": losses_v,
        "dpass_v": net_v / nv,
        "dscs_v": sv["scs"][cand] - sv["scs"][inc],
        "dtheta_2pl_v": dtheta_2pl,
        "ztheta_2pl_v": ztheta_2pl,
        "dtheta_grm3_v": dtheta_grm3,
        "ztheta_grm3_v": ztheta_grm3,
        "trm_v": trm,
        "hrm_v": hrm,
        "krm_v": krm,
        "glm_v": glm,
        "p1_inc_v": sv["pass1"][inc],
        "marg": np.stack([sv[k][inc] for k in ("gate", "fix", "keep")] + [sv[k][cand] for k in ("gate", "fix", "keep")], -1),
        "losses_t": losses_t,
        "lossfrac_t": losses_t / nt,
        "dpass_t": (gains_t - losses_t) / nt,
        "eligible": eligible,
        "near": near,
    }


def selected_weights(order: np.ndarray, weights: np.ndarray, q: float) -> np.ndarray:
    """Selected weight per pair: the sorted prefix keeps exactly floor(q * total weight), the boundary pair partially."""
    w_sorted = weights[..., order].astype(np.float64)
    budget = np.floor(q * w_sorted.sum(-1, keepdims=True) + 1e-9)
    before = np.cumsum(w_sorted, axis=-1) - w_sorted
    kept_sorted = np.clip(budget - before, 0.0, w_sorted)
    kept = np.zeros_like(kept_sorted)
    np.put_along_axis(kept, np.broadcast_to(order, kept_sorted.shape), kept_sorted, axis=-1)
    return kept


def policy_orders(st: dict[str, np.ndarray], idx: np.ndarray, hkey: np.ndarray) -> dict[str, np.ndarray]:
    """Sort orders (positions into idx) for each ranked policy; ties broken by the outcome-independent pair hash."""
    net = st["net_v"].ravel()[idx]
    h = hkey.ravel()[idx]
    return {
        "S0plus": np.lexsort((h, -net)),
        "S1": np.lexsort((h, -st["dscs_v"].ravel()[idx])),
        "S2": np.lexsort((h, st["losses_v"].ravel()[idx])),
        "S3": np.lexsort((h, st["trm_v"].ravel()[idx])),
        "S_irt2pl": np.lexsort((h, -st["dtheta_2pl_v"].ravel()[idx])),
        "S_irt2pl_z": np.lexsort((h, -st["ztheta_2pl_v"].ravel()[idx])),
        "S_grm3": np.lexsort((h, -st["dtheta_grm3_v"].ravel()[idx])),
        "S_grm3_z": np.lexsort((h, -st["ztheta_grm3_v"].ravel()[idx])),
        "R0": np.lexsort((h, net)),
        "R1": np.lexsort((h, -st["dscs_v"].ravel()[idx], net)),
        "R2": np.lexsort((h, st["losses_v"].ravel()[idx], net)),
        "R3": np.lexsort((h, st["trm_v"].ravel()[idx], net)),
        "R3h": np.lexsort((h, st["hrm_v"].ravel()[idx], net)),
        "R_irt2pl": np.lexsort((h, -st["dtheta_2pl_v"].ravel()[idx], net)),
        "R_irt2pl_z": np.lexsort((h, -st["ztheta_2pl_v"].ravel()[idx], net)),
        "R_grm3": np.lexsort((h, -st["dtheta_grm3_v"].ravel()[idx], net)),
        "R_grm3_z": np.lexsort((h, -st["ztheta_grm3_v"].ravel()[idx], net)),
    }


def weighted_ranks(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Weighted average ranks (ties share the midpoint of their cumulative weight), vectorized over draws (rows of w)."""
    if x.size == 0:
        return np.zeros((w.shape[0], 0))
    order = np.argsort(x, kind="stable")
    xs = x[order]
    ws = w[:, order].astype(np.float64)
    cum = np.cumsum(ws, axis=1)
    starts = np.r_[0, np.flatnonzero(np.diff(xs)) + 1]
    ends = np.r_[starts[1:], len(xs)]
    gsum = np.add.reduceat(ws, starts, axis=1)
    before = cum[:, ends - 1] - gsum
    mid = before + gsum / 2.0
    ranks_sorted = np.repeat(mid, ends - starts, axis=1)
    out = np.empty_like(ranks_sorted)
    out[:, order] = ranks_sorted
    return out


def weighted_partial_corr(y: np.ndarray, z: np.ndarray, covs: list[np.ndarray], w: np.ndarray) -> np.ndarray:
    """Weighted partial Spearman correlation of y and z given covs, per draw (float64 weighted least squares)."""
    w = w.astype(np.float64)
    out = np.full(w.shape[0], np.nan)
    if y.size < len(covs) + 3:
        return out
    total = w.sum(1, keepdims=True)
    total = np.where(total > 0, total, 1.0)
    ry, rz = weighted_ranks(y, w) / total, weighted_ranks(z, w) / total
    X = np.stack([np.ones_like(ry)] + [weighted_ranks(c, w) / total for c in covs], -1)
    sw = np.sqrt(w)
    U, s, _ = np.linalg.svd(X * sw[..., None], full_matrices=False)
    with np.errstate(divide="ignore", invalid="ignore"):
        cond = np.where(s[:, -1] > 0, s[:, 0] / s[:, -1], np.inf)
    ok = cond < COND_MAX

    def resid(v):
        vw = v * sw
        return vw - np.einsum("bnp,bp->bn", U, np.einsum("bnp,bn->bp", U, vw)), (vw ** 2).sum(1)

    ey, ny = resid(ry)
    ez, nz = resid(rz)
    vy, vz = (ey ** 2).sum(1), (ez ** 2).sum(1)
    ok &= (vy > RESID_TOL * np.maximum(ny, 1e-300)) & (vz > RESID_TOL * np.maximum(nz, 1e-300))
    with np.errstate(invalid="ignore", divide="ignore"):
        out[ok] = ((ey * ez).sum(1) / np.sqrt(vy * vz))[ok]
    return out


def _ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    """num / den with NaN where the denominator is zero (an undefined conditional rate, never a fake zero)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)


def split_statistics(st: dict[str, np.ndarray], pop: str, hkey: np.ndarray, wpair: np.ndarray, qs: tuple[float, ...]) -> dict:
    """Per-split estimands for one population under pair weights wpair (draws x S x S; row 0 is the identity)."""
    idx = np.flatnonzero(st[pop].ravel())
    n = len(idx)
    w = wpair.reshape(wpair.shape[0], -1)[:, idx].astype(np.float64)
    harm = (st["dpass_t"].ravel()[idx] < 0).astype(float)
    anyloss = (st["losses_t"].ravel()[idx] >= 1).astype(float)
    lossf = st["lossfrac_t"].ravel()[idx]
    dpt = st["dpass_t"].ravel()[idx]
    good = (dpt > 0).astype(float)
    sw = w.sum(1)
    res = {"n_pairs": n}
    res["H1"] = {
        "hpr": _ratio((w * harm).sum(1), sw),
        "share_any_loss": _ratio((w * anyloss).sum(1), sw),
        "mean_lossfrac": _ratio((w * lossf).sum(1), sw),
        "mean_dpass_t": _ratio((w * dpt).sum(1), sw),
    }
    cov3 = [st["losses_v"].ravel()[idx], st["gains_v"].ravel()[idx], st["p1_inc_v"].ravel()[idx]]
    marg = [st["marg"].reshape(-1, 6)[idx, k] for k in range(6)]
    specs = {
        "hrm": (st["hrm_v"].ravel()[idx], cov3),
        "krm": (st["krm_v"].ravel()[idx], cov3),
        "hrm_with_marginals": (st["hrm_v"].ravel()[idx], cov3 + marg),
        "trm_given_gain_p1": (st["trm_v"].ravel()[idx], cov3[1:]),
    }
    chunk = max(1, int(2e7 // max(1, n * 11)))
    res["H2"] = {
        k: np.concatenate([weighted_partial_corr(x, lossf, cv, w[b : b + chunk]) for b in range(0, w.shape[0], chunk)])
        for k, (x, cv) in specs.items()
    }
    orders = policy_orders(st, idx, hkey)
    net_idx = st["net_v"].ravel()[idx]
    total_good = (w * good).sum(1)
    res["H3"] = {}
    for q in qs:
        per = {}
        for name, order in orders.items():
            if name in STRATIFIED:
                kept = np.zeros_like(w)
                for k in np.unique(net_idx):
                    sub = order[net_idx[order] == k]
                    kept[:, sub] = selected_weights(np.arange(len(sub)), w[:, sub], q)
            else:
                kept = selected_weights(order, w, q)
            sk = kept.sum(1)
            per[name] = {
                "hpr": _ratio((kept * harm).sum(1), sk),
                "mean_lossfrac": _ratio((kept * lossf).sum(1), sk),
                "mean_dpass_t": _ratio((kept * dpt).sum(1), sk),
                "recall": _ratio((kept * good).sum(1), total_good),
                "rate": _ratio(sk, sw),
            }
        res["H3"][q] = per
    zero_loss = (st["losses_v"].ravel()[idx] == 0).astype(float)
    wd = w * zero_loss
    res["deploy_zero_loss"] = {
        "acceptance": _ratio(wd.sum(1), sw),
        "hpr": _ratio((wd * harm).sum(1), wd.sum(1)),
        "n_accepted_unweighted": int(zero_loss.sum()),
    }
    return res


def predictive_comparison(st: dict[str, np.ndarray], pop: str, rng: np.random.Generator) -> dict:
    """Endpoint-disjoint out-of-sample R^2 of binary-only, +marginals, +matrix, +IRT models for held-out loss fraction."""
    s = st["inc"].shape[0]
    half = rng.permutation(s)[: s // 2]
    in_a = np.zeros(s, bool)
    in_a[half] = True
    popm = st[pop]
    fit = popm & in_a[st["inc"]] & in_a[st["cand"]]
    ev = popm & ~in_a[st["inc"]] & ~in_a[st["cand"]]
    y = st["lossfrac_t"]
    base = [st["losses_v"], st["gains_v"], st["p1_inc_v"]]
    marg = [st["marg"][..., k] for k in range(6)]
    matrix = [st["hrm_v"], st["krm_v"], st["trm_v"], st["glm_v"]]
    irt_feats = [st["dtheta_2pl_v"], st["ztheta_2pl_v"], st["dtheta_grm3_v"], st["ztheta_grm3_v"]]
    out = {"n_fit": int(fit.sum()), "n_eval": int(ev.sum())}
    if fit.sum() < MIN_PRED_PAIRS or ev.sum() < MIN_PRED_PAIRS:
        return {**out, "M0": math.nan, "M1": math.nan, "M2": math.nan, "M3_irt": math.nan}
    for name, feats in (
        ("M0", base),
        ("M1", base + marg),
        ("M2", base + marg + matrix),
        ("M3_irt", base + marg + matrix + irt_feats),
    ):
        Xf = np.column_stack([np.ones(fit.sum())] + [f[fit] for f in feats])
        Xe = np.column_stack([np.ones(ev.sum())] + [f[ev] for f in feats])
        beta, *_ = np.linalg.lstsq(Xf, y[fit], rcond=None)
        ss_res = ((y[ev] - Xe @ beta) ** 2).sum()
        ss_tot = ((y[ev] - y[ev].mean()) ** 2).sum()
        out[name] = float(1 - ss_res / ss_tot) if ss_tot > 0 else math.nan
    return out


def bootstrap_weights(n_systems: int, n_draws: int, seed: int) -> np.ndarray:
    """Dyadic system-bootstrap pair weights m_i * m_j, draw 0 = identity."""
    rng = np.random.default_rng(seed)
    m = np.ones((n_draws + 1, n_systems))
    m[1:] = rng.multinomial(n_systems, np.full(n_systems, 1 / n_systems), size=n_draws)
    return m[:, :, None] * m[:, None, :]


def aggregate_family(values: dict[str, list[np.ndarray]], n_splits_considered: int) -> dict:
    """Split-average estimands on one common split support with draw invalidation (PROTOCOL statistics)."""
    names = list(values)
    stacks = {k: np.stack(values[k]) for k in names}
    admitted = np.all([np.isfinite(stacks[k][:, 0]) for k in names], axis=0)
    n_adm = int(admitted.sum())
    out = {"splits_considered": n_splits_considered, "splits_admitted": n_adm}
    if n_adm == 0:
        return {**out, "status": "undefined: no admitted split", "members": {}}
    adm = {k: v[admitted] for k, v in stacks.items()}
    n_draws = adm[names[0]].shape[1] - 1
    valid = np.all([np.isfinite(adm[k][:, 1:]).all(0) for k in names], axis=0) if n_draws else np.zeros(0, bool)
    out["draws_valid"] = int(valid.sum())
    out["draws_total"] = n_draws
    coverage_ok = n_adm >= MIN_SUPPORT * n_splits_considered and (n_draws == 0 or valid.sum() >= MIN_SUPPORT * n_draws)
    out["status"] = "ok" if coverage_ok else "inconclusive: insufficient split or draw support"
    members = {}
    for k in names:
        entry = {"estimate": float(adm[k][:, 0].mean()), "split_5_95": np.percentile(adm[k][:, 0], [5, 95]).tolist()}
        if n_draws > 0:
            boot = adm[k][:, 1:][:, valid].mean(0)
            entry["lo"], entry["hi"] = (np.percentile(boot, [2.5, 97.5]).tolist() if len(boot) >= 20 else [math.nan, math.nan])
        members[k] = entry
    out["members"] = members
    return out


_STATE: dict = {}


def _worker_init(args_dict: dict) -> None:
    """Per-process state: matrix, tensors, IRT scorer, hash keys, splits and bootstrap weights."""
    a = argparse.Namespace(**args_dict)
    drop = frozenset(json.loads(DRIFT.read_text())["tasks"]) if a.sensitivity == "matched_test_lists" else frozenset()
    m = load_matrix(Path(a.per_cell), a.expect_sha, drop)
    fits_p = FITS_E14 if a.expect_sha is not None else None
    ana_p = ANALYSIS_E14 if a.expect_sha is not None else None
    _STATE.update(
        a=a,
        m=m,
        pt=pair_tensors(m),
        irt_scorer=OutOfFoldIRTScorer(m, fits_p, ana_p),
        hkey=pair_hash(m.systems),
        splits=make_splits(len(m.tasks), a.splits, a.split_seed),
        near_max=int(math.floor(a.near_band * (len(m.tasks) // 2))),
        wpair=bootstrap_weights(len(m.systems), a.draws, a.boot_seed).astype(np.float32),
    )


def _run_split(si: int) -> dict:
    """Statistics for one split for both populations; degenerate splits are recorded before any computation."""
    a, m = _STATE["a"], _STATE["m"]
    st = split_pairs(m, _STATE["pt"], _STATE["irt_scorer"], _STATE["splits"][si], _STATE["near_max"])
    out = {"split": si}
    for pop, min_pairs, weights in (("near", a.min_pairs, _STATE["wpair"]), ("eligible", 1, _STATE["wpair"][:1])):
        n = int(st[pop].sum())
        if n < min_pairs:
            out[pop] = {"degenerate": True, "n_pairs": n}
            continue
        res = split_statistics(st, pop, _STATE["hkey"], weights, tuple(a.q))
        res["pred"] = predictive_comparison(st, pop, np.random.default_rng([a.split_seed, si, 1 if pop == "near" else 2]))
        res["degenerate"] = False
        out[pop] = res
    return out


def run(args: argparse.Namespace) -> dict:
    """Full replay over all splits (optionally in parallel), then family-wise aggregation."""
    t0 = time.time()
    _worker_init(vars(args))
    m = _STATE["m"]
    expected = EXPECTED_SHAPE.get(args.sensitivity)
    if args.expect_sha is not None and expected and (len(m.systems), len(m.tasks)) != expected:
        raise SystemExit(f"STOP: expected {expected}, got {(len(m.systems), len(m.tasks))}")
    if args.sensitivity == "matched_test_lists" and len(json.loads(DRIFT.read_text())["tasks"]) != 4:
        raise SystemExit("STOP: the drift sensitivity must drop exactly the 4 declared tasks")
    if args.workers > 1:
        with mp.get_context("fork").Pool(args.workers, initializer=_worker_init, initargs=(vars(args),)) as pool:
            per_split = pool.map(_run_split, range(args.splits), chunksize=max(1, args.splits // (args.workers * 8)))
    else:
        per_split = [_run_split(si) for si in range(args.splits)]
    out = {
        "settings": vars(args),
        "systems": len(m.systems),
        "tasks": len(m.tasks),
        "near_max_net_gain": _STATE["near_max"],
        "populations": {},
    }
    for pop in ("near", "eligible"):
        rs = [r[pop] for r in per_split if not r[pop]["degenerate"]]
        degenerate = args.splits - len(rs)
        pop_out = {"splits_degenerate": degenerate, "splits_used": len(rs), "status": "ok"}
        if pop == "near" and degenerate > 0.10 * args.splits:
            pop_out["status"] = "inconclusive: more than 10% of splits degenerate"
        if not rs:
            pop_out["status"] = "inconclusive: no non-degenerate split"
            out["populations"][pop] = pop_out
            continue
        n = len(rs)
        pop_out["pairs_per_split_median"] = float(np.median([r["n_pairs"] for r in rs]))
        pop_out["H1"] = aggregate_family({k: [r["H1"][k] for r in rs] for k in rs[0]["H1"]}, n)
        pop_out["H2"] = {k: aggregate_family({k: [r["H2"][k] for r in rs]}, n) for k in rs[0]["H2"]}
        pop_out["H3"] = {}
        for q in args.q:
            fam = {}
            for name in POLICIES:
                for k in ("hpr", "mean_dpass_t"):
                    fam[f"{name}.{k}"] = [r["H3"][q][name][k] for r in rs]
            for a_, b_ in CONTRASTS:
                fam[f"{a_}-{b_}.hpr_abs_reduction"] = [r["H3"][q][a_]["hpr"] - r["H3"][q][b_]["hpr"] for r in rs]
                fam[f"{a_}-{b_}.dpass_gain_of_second"] = [
                    r["H3"][q][b_]["mean_dpass_t"] - r["H3"][q][a_]["mean_dpass_t"] for r in rs
                ]
            aux = {f"{name}.{k}": [r["H3"][q][name][k] for r in rs] for name in POLICIES for k in ("mean_lossfrac", "rate")}
            recall = {f"{name}.recall": [r["H3"][q][name]["recall"] for r in rs] for name in POLICIES}
            pop_out["H3"][str(q)] = {
                "main": aggregate_family(fam, n),
                "aux": aggregate_family(aux, n),
                "recall": aggregate_family(recall, n),
            }
        pop_out["deploy_zero_loss"] = {
            "acceptance": aggregate_family({"acceptance": [r["deploy_zero_loss"]["acceptance"] for r in rs]}, n),
            "hpr_given_accepted": aggregate_family({"hpr": [r["deploy_zero_loss"]["hpr"] for r in rs]}, n),
            "n_accepted_per_split_median": float(np.median([r["deploy_zero_loss"]["n_accepted_unweighted"] for r in rs])),
        }
        pr = [r["pred"] for r in rs]
        pred = {
            "attempted_splits": len(pr),
            "n_fit_median": float(np.median([x["n_fit"] for x in pr])),
            "n_eval_median": float(np.median([x["n_eval"] for x in pr])),
        }
        for k in ("M0", "M1", "M2", "M3_irt"):
            v = np.array([x[k] for x in pr], float)
            v = v[np.isfinite(v)]
            pred[k] = {
                "defined_splits": int(len(v)),
                "median": float(np.median(v)) if len(v) else None,
                "split_5_95": np.percentile(v, [5, 95]).tolist() if len(v) else None,
            }
        for label, ka, kb in (("M2_minus_M1", "M2", "M1"), ("M3_irt_minus_M2", "M3_irt", "M2")):
            d = np.array([x[ka] - x[kb] for x in pr], float)
            d = d[np.isfinite(d)]
            pred[label] = {
                "defined_splits": int(len(d)),
                "median": float(np.median(d)) if len(d) else None,
                "share_positive": float((d > 0).mean()) if len(d) else None,
                "split_5_95": np.percentile(d, [5, 95]).tolist() if len(d) else None,
            }
        pop_out["H2_predictive"] = pred
        out["populations"][pop] = pop_out
    out["runtime_s"] = round(time.time() - t0, 1)
    return out


def relative_reductions(result: dict) -> None:
    """Add relative HPR reductions (absolute reduction / comparator HPR, point estimates) on the same support."""
    for pop in result["populations"].values():
        for qd in pop.get("H3", {}).values():
            mem = qd["main"].get("members", {})
            for a_, b_ in CONTRASTS:
                ha, d = mem.get(f"{a_}.hpr"), mem.get(f"{a_}-{b_}.hpr_abs_reduction")
                key = f"{a_}-{b_}.hpr_rel_reduction"
                if ha and d and ha["estimate"] > 0:
                    mem[key] = {"estimate": d["estimate"] / ha["estimate"], "note": "point estimate (ratio of split averages)"}
                else:
                    mem[key] = {"estimate": None, "note": "undefined: comparator harmful promotion rate is zero or missing"}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--per-cell", default=str(PER_CELL))
    ap.add_argument("--expect-sha", default=PER_CELL_SHA256)
    ap.add_argument("--sensitivity", choices=("none", "matched_test_lists"), default="none")
    ap.add_argument("--splits", type=int, default=1000)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--split-seed", type=int, default=20261009)
    ap.add_argument("--boot-seed", type=int, default=20261010)
    ap.add_argument("--near-band", type=float, default=0.05)
    ap.add_argument("--q", type=float, nargs="+", default=[0.5, 0.25, 0.75])
    ap.add_argument("--min-pairs", type=int, default=200)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.expect_sha in ("", "none"):
        args.expect_sha = None
    res = run(args)
    relative_reductions(res)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(json.dumps({"out": args.out, "runtime_s": res["runtime_s"],
                      "degenerate": {p: v.get("splits_degenerate") for p, v in res["populations"].items()}}))


if __name__ == "__main__":
    main()
