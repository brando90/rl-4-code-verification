"""Experiment 10: replay AlphaHebe-style promotion policies on experiment 07's SWE-bench Verified factor matrix.

Pairs of public systems stand in for incumbent -> candidate edits. Each random split divides the common cohort
into a validation half (what a promotion policy sees) and a test half (the outcome). Everything here is
deterministic given the frozen seeds in PROTOCOL.md; no model calls are made.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PER_CELL = REPO / "experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/results/per_cell_e07.jsonl.gz"
PER_CELL_SHA256 = "f064c3951860cf4d88879e7c3b81ec42c8b42780923c61198c71f98dc6463a4d"
DRIFT = HERE / "inputs/test_list_drift_e07.json"
POLICIES = ("S0plus", "S1", "S2", "S3", "R0", "R1", "R2", "R3", "R3h")
STRATIFIED = ("R0", "R1", "R2", "R3", "R3h")


@dataclass
class Matrix:
    """Systems x tasks arrays: resolved r, gate g, gated fix gf = g*t_fix, gated keep gk = g*t_keep."""

    systems: list[str]
    tasks: list[str]
    r: np.ndarray
    g: np.ndarray
    gf: np.ndarray
    gk: np.ndarray


def load_matrix(path: Path = PER_CELL, expect_sha: str | None = PER_CELL_SHA256, drop_tasks: frozenset = frozenset()) -> Matrix:
    """Load the included-system, common-cohort cells of experiment 07 (stop rule: exact identity and counts)."""
    raw = path.read_bytes()
    if expect_sha is not None and hashlib.sha256(raw).hexdigest() != expect_sha:
        raise SystemExit(f"STOP: input SHA-256 mismatch for {path}")
    rows = [json.loads(line) for line in gzip.decompress(raw).decode().splitlines() if line.strip()]
    cells = [x for x in rows if x["included"] and x["common_cohort"] and x["instance_id"] not in drop_tasks]
    systems = sorted({x["submission"] for x in cells})
    tasks = sorted({x["instance_id"] for x in cells})
    si = {s: i for i, s in enumerate(systems)}
    ti = {t: j for j, t in enumerate(tasks)}
    shape = (len(systems), len(tasks))
    r, g, gf, gk = (np.full(shape, np.nan) for _ in range(4))
    for x in cells:
        i, j = si[x["submission"]], ti[x["instance_id"]]
        gate = x["gate"]
        if gate is None:
            raise SystemExit(f"STOP: unmeasured cohort cell {x['submission']} {x['instance_id']}")
        r[i, j] = float(bool(x["resolved"]))
        g[i, j] = float(gate)
        gf[i, j] = 0.0 if gate == 0 else float(x["t_fix"])
        gk[i, j] = 0.0 if gate == 0 else float(x["t_keep"])
    if np.isnan(r).any() or np.isnan(gf).any() or np.isnan(gk).any():
        raise SystemExit("STOP: incomplete systems x tasks matrix")
    return Matrix(systems, tasks, r, g, gf, gk)


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

    drop_total: np.ndarray  # sum over (g, gf, gk) of max(0, inc - cand), shape (S, S, T)
    drop_hidden: np.ndarray  # drop_total on jointly unresolved items
    drop_keep_hidden: np.ndarray  # max(0, gk_inc - gk_cand) on jointly unresolved items
    drop_gate_loss: np.ndarray  # drop_total on items where the incumbent's gate is 1 and the candidate's is 0


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


def split_pairs(m: Matrix, pt: PairTensors, val: np.ndarray, near_max_gain: int) -> dict[str, np.ndarray]:
    """All pair statistics for one split, flattened over eligible pairs (incumbent != candidate, net gain > 0)."""
    vi, ti = np.flatnonzero(val), np.flatnonzero(~val)
    nv, nt = len(vi), len(ti)
    rv, rt = m.r[:, vi], m.r[:, ti]
    gains_v = (1 - rv) @ rv.T  # [inc, cand]: tasks the candidate gains
    losses_v = rv @ (1 - rv).T  # [inc, cand]: tasks the candidate loses
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
    sv, st = system_summary(m, vi), system_summary(m, ti)
    inc, cand = np.meshgrid(np.arange(s), np.arange(s), indexing="ij")
    eligible = (inc != cand) & (net_v > 0)
    near = eligible & (net_v <= near_max_gain)
    out = {
        "inc": inc, "cand": cand, "net_v": net_v, "gains_v": gains_v, "losses_v": losses_v,
        "dpass_v": net_v / nv, "dscs_v": sv["scs"][cand] - sv["scs"][inc],
        "trm_v": trm, "hrm_v": hrm, "krm_v": krm, "glm_v": glm,
        "p1_inc_v": sv["pass1"][inc],
        "marg": np.stack([sv[k][inc] for k in ("gate", "fix", "keep")] + [sv[k][cand] for k in ("gate", "fix", "keep")], -1),
        "losses_t": losses_t, "lossfrac_t": losses_t / nt, "dpass_t": (gains_t - losses_t) / nt,
        "eligible": eligible, "near": near,
    }
    return out


def select_prefix(order: np.ndarray, weights: np.ndarray, q: float) -> np.ndarray:
    """Selection mask over pairs: keep a sorted prefix whose cumulative weight is <= q * total (rows = draws)."""
    w_sorted = weights[..., order]
    cum = np.cumsum(w_sorted, axis=-1)
    keep_sorted = cum <= q * w_sorted.sum(-1, keepdims=True) + 1e-9
    keep = np.zeros_like(keep_sorted)
    np.put_along_axis(keep, np.broadcast_to(order, keep_sorted.shape), keep_sorted, axis=-1)
    return keep


def policy_orders(st: dict[str, np.ndarray], idx: np.ndarray, hkey: np.ndarray) -> dict[str, np.ndarray]:
    """Sort orders (positions into idx) for each ranked screening policy; ties broken by the pair hash."""
    net = st["net_v"].ravel()[idx]
    h = hkey.ravel()[idx]
    return {
        "S0plus": np.lexsort((h, -net)),
        "S1": np.lexsort((h, -st["dscs_v"].ravel()[idx])),
        "S2": np.lexsort((h, -net, st["losses_v"].ravel()[idx])),
        "S3": np.lexsort((h, -net, st["trm_v"].ravel()[idx])),
        "R0": np.lexsort((h, net)),
        "R1": np.lexsort((h, -st["dscs_v"].ravel()[idx], net)),
        "R2": np.lexsort((h, st["losses_v"].ravel()[idx], net)),
        "R3": np.lexsort((h, st["trm_v"].ravel()[idx], net)),
        "R3h": np.lexsort((h, st["hrm_v"].ravel()[idx], net)),
    }


def weighted_ranks(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Weighted average ranks (ties share the midpoint of their cumulative weight), vectorized over draws (rows of w)."""
    order = np.argsort(x, kind="stable")
    xs = x[order]
    ws = w[:, order]
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
    """Weighted partial Spearman correlation of y and z given covs, per draw; NaN when undefined."""
    total = w.sum(1, keepdims=True)
    total = np.where(total > 0, total, 1.0)
    ry, rz = weighted_ranks(y, w) / total, weighted_ranks(z, w) / total
    X = np.stack([np.ones_like(ry)] + [weighted_ranks(c, w) / total for c in covs], -1)  # draws x n x p
    XtW = X * w[..., None]
    A = np.einsum("bnp,bnq->bpq", XtW, X)
    out = np.full(w.shape[0], np.nan)
    ok = np.linalg.cond(A) < 1e10
    if not ok.any():
        return out
    Ai = np.linalg.inv(A[ok])
    def resid(v):
        beta = np.einsum("bpq,bq->bp", Ai, np.einsum("bnp,bn->bp", XtW[ok], v[ok]))
        return v[ok] - np.einsum("bnp,bp->bn", X[ok], beta)
    ey, ez = resid(ry), resid(rz)
    ww = w[ok]
    sw = ww.sum(1)
    my, mz = (ww * ey).sum(1) / sw, (ww * ez).sum(1) / sw
    cov = (ww * (ey - my[:, None]) * (ez - mz[:, None])).sum(1)
    vy = (ww * (ey - my[:, None]) ** 2).sum(1)
    vz = (ww * (ez - mz[:, None]) ** 2).sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        out[ok] = np.where((vy > 1e-12) & (vz > 1e-12), cov / np.sqrt(vy * vz), np.nan)
    return out


def split_statistics(st: dict[str, np.ndarray], pop: str, hkey: np.ndarray, wpair: np.ndarray, qs: tuple[float, ...]) -> dict:
    """All per-split estimands for one population under pair weights wpair (draws x S x S); row 0 may be all ones."""
    idx = np.flatnonzero(st[pop].ravel())
    n = len(idx)
    w = wpair.reshape(wpair.shape[0], -1)[:, idx]
    harm = (st["dpass_t"].ravel()[idx] < 0).astype(float)
    anyloss = (st["losses_t"].ravel()[idx] >= 1).astype(float)
    lossf = st["lossfrac_t"].ravel()[idx]
    dpt = st["dpass_t"].ravel()[idx]
    good = (dpt > 0).astype(float)
    sw = w.sum(1)
    res = {"n_pairs": n, "weight_total": sw}
    with np.errstate(invalid="ignore", divide="ignore"):
        res["H1"] = {
            "hpr": (w * harm).sum(1) / sw, "share_any_loss": (w * anyloss).sum(1) / sw,
            "mean_lossfrac": (w * lossf).sum(1) / sw, "mean_dpass_t": (w * dpt).sum(1) / sw,
        }
        cov3 = [st["losses_v"].ravel()[idx], st["gains_v"].ravel()[idx], st["p1_inc_v"].ravel()[idx]]
        marg = [st["marg"].reshape(-1, 6)[idx, k] for k in range(6)]
        specs = {
            "hrm": (st["hrm_v"].ravel()[idx], cov3),
            "krm": (st["krm_v"].ravel()[idx], cov3),
            "hrm_with_marginals": (st["hrm_v"].ravel()[idx], cov3 + marg),
            "trm_given_gain_p1": (st["trm_v"].ravel()[idx], cov3[1:]),
        }
        chunk = max(1, int(4e7 // max(1, n * 11)))
        res["H2"] = {k: np.concatenate([weighted_partial_corr(x, lossf, cv, w[b:b + chunk]) for b in range(0, w.shape[0], chunk)])
                     for k, (x, cv) in specs.items()}
        orders = policy_orders(st, idx, hkey)
        res["H3"] = {}
        for q in qs:
            per = {}
            net_idx = st["net_v"].ravel()[idx]
            for name, order in orders.items():
                if name in STRATIFIED:
                    sel = np.zeros_like(w, dtype=bool)
                    for k in np.unique(net_idx):
                        sub = order[net_idx[order] == k]  # this stratum, in policy order
                        local = select_prefix(np.arange(len(sub)), w[:, sub], q)
                        sel[:, sub] = local
                else:
                    sel = select_prefix(order, w, q)
                ws = w * sel
                sws = ws.sum(1)
                per[name] = {
                    "hpr": (ws * harm).sum(1) / sws, "mean_lossfrac": (ws * lossf).sum(1) / sws,
                    "mean_dpass_t": (ws * dpt).sum(1) / sws,
                    "recall": (ws * good).sum(1) / np.maximum((w * good).sum(1), 1e-12),
                    "rate": sws / sw,
                }
            res["H3"][q] = per
        # Deployable rule (descriptive): strict scalar gain and zero observed binary losses on validation.
        d2 = (st["losses_v"].ravel()[idx] == 0).astype(float)
        wd = w * d2
        res["deploy_zero_loss"] = {"acceptance": wd.sum(1) / sw, "hpr": (wd * harm).sum(1) / np.maximum(wd.sum(1), 1e-12),
                                   "n_accepted_unweighted": int(d2.sum())}
    return res


def predictive_comparison(st: dict[str, np.ndarray], pop: str, rng: np.random.Generator) -> dict[str, float]:
    """Endpoint-disjoint out-of-sample R^2 of binary-only, +marginals, +matrix models for held-out loss fraction."""
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
    out = {"n_fit": int(fit.sum()), "n_eval": int(ev.sum())}
    if fit.sum() < 50 or ev.sum() < 50:
        return {**out, "M0": math.nan, "M1": math.nan, "M2": math.nan}
    for name, feats in (("M0", base), ("M1", base + marg), ("M2", base + marg + matrix)):
        Xf = np.column_stack([np.ones(fit.sum())] + [f[fit] for f in feats])
        Xe = np.column_stack([np.ones(ev.sum())] + [f[ev] for f in feats])
        beta, *_ = np.linalg.lstsq(Xf, y[fit], rcond=None)
        pred = Xe @ beta
        ss_res = ((y[ev] - pred) ** 2).sum()
        ss_tot = ((y[ev] - y[ev].mean()) ** 2).sum()
        out[name] = float(1 - ss_res / ss_tot) if ss_tot > 0 else math.nan
    return out


def bootstrap_weights(n_systems: int, n_draws: int, seed: int) -> np.ndarray:
    """Dyadic system-bootstrap pair weights m_i * m_j (self pairs excluded later by eligibility), draw 0 = identity."""
    rng = np.random.default_rng(seed)
    m = np.ones((n_draws + 1, n_systems))
    m[1:] = rng.multinomial(n_systems, np.full(n_systems, 1 / n_systems), size=n_draws)
    return m[:, :, None] * m[:, None, :]


def summarize(values: np.ndarray) -> dict:
    """Point estimate (draw 0) with a percentile interval over bootstrap draws 1..B (NaN-aware)."""
    point = float(values[0])
    boot = values[1:]
    boot = boot[np.isfinite(boot)]
    lo, hi = (np.percentile(boot, [2.5, 97.5]).tolist() if len(boot) >= 20 else [math.nan, math.nan])
    return {"estimate": point, "lo": lo, "hi": hi, "draws_defined": int(len(boot))}


def run(args: argparse.Namespace) -> dict:
    """Full replay: splits x draws, then split-averaged estimands with dyadic-bootstrap intervals."""
    t0 = time.time()
    drop = frozenset(json.loads(DRIFT.read_text())["tasks"]) if args.sensitivity == "matched_test_lists" else frozenset()
    m = load_matrix(Path(args.per_cell), args.expect_sha, drop)
    if args.sensitivity == "none" and (len(m.systems), len(m.tasks)) != (164, 424):
        raise SystemExit(f"STOP: expected 164 x 424, got {len(m.systems)} x {len(m.tasks)}")
    pt = pair_tensors(m)
    hkey = pair_hash(m.systems)
    splits = make_splits(len(m.tasks), args.splits, args.split_seed)
    near_max = int(math.floor(args.near_band * (len(m.tasks) // 2)))
    wpair = bootstrap_weights(len(m.systems), args.draws, args.boot_seed).astype(np.float32)
    qs = tuple(args.q)
    pops = ("near", "eligible")
    acc = {p: [] for p in pops}
    pred = {p: [] for p in pops}
    degenerate = {p: 0 for p in pops}
    rng_pred = np.random.default_rng(args.split_seed + 1)
    for si in range(args.splits):
        st = split_pairs(m, pt, splits[si], near_max)
        for p in pops:
            res = split_statistics(st, p, hkey, wpair if p == "near" else wpair[:1], qs)
            if res["n_pairs"] < args.min_pairs:
                degenerate[p] += 1
                continue
            acc[p].append(res)
            pred[p].append(predictive_comparison(st, p, rng_pred))
        if args.progress and (si + 1) % max(1, args.splits // 20) == 0:
            print(f"split {si + 1}/{args.splits} {time.time() - t0:.0f}s", file=sys.stderr, flush=True)
    out = {"settings": vars(args), "systems": len(m.systems), "tasks": len(m.tasks), "near_max_net_gain": near_max,
           "splits_degenerate": degenerate, "populations": {}}
    for p in pops:
        rs = acc[p]
        if not rs:
            out["populations"][p] = {"status": "inconclusive: no non-degenerate split"}
            continue
        mean_over_splits = lambda f: np.nanmean(np.stack([f(r) for r in rs]), axis=0)  # noqa: E731
        split_pct = lambda f: np.nanpercentile(np.stack([f(r)[0] for r in rs]), [5, 95]).tolist()  # noqa: E731
        pop = {"splits_used": len(rs), "pairs_per_split_median": float(np.median([r["n_pairs"] for r in rs]))}
        pop["H1"] = {k: {**summarize(mean_over_splits(lambda r, k=k: r["H1"][k])), "split_5_95": split_pct(lambda r, k=k: r["H1"][k])}
                     for k in rs[0]["H1"]}
        pop["H2"] = {k: {**summarize(mean_over_splits(lambda r, k=k: r["H2"][k])), "split_5_95": split_pct(lambda r, k=k: r["H2"][k])}
                     for k in rs[0]["H2"]}
        pop["H3"] = {}
        for q in qs:
            per = {}
            for name in POLICIES:
                per[name] = {k: summarize(mean_over_splits(lambda r, k=k, n=name, q=q: r["H3"][q][n][k])) for k in rs[0]["H3"][q][name]}
            contrasts = {}
            for a, b in (("R0", "R2"), ("R2", "R3"), ("R0", "R3"), ("R0", "R3h"), ("R0", "R1"),
                         ("S0plus", "R3"), ("S0plus", "R2"), ("S0plus", "S3"), ("S2", "S3"), ("S0plus", "S2"), ("S0plus", "S1")):
                d = mean_over_splits(lambda r, a=a, b=b, q=q: r["H3"][q][a]["hpr"] - r["H3"][q][b]["hpr"])
                ha = mean_over_splits(lambda r, a=a, q=q: r["H3"][q][a]["hpr"])
                with np.errstate(invalid="ignore", divide="ignore"):
                    rel = np.where(ha > 0, d / ha, np.nan)
                gain = mean_over_splits(lambda r, a=a, b=b, q=q: r["H3"][q][b]["mean_dpass_t"] - r["H3"][q][a]["mean_dpass_t"])
                contrasts[f"{a}_minus_{b}"] = {"hpr_abs_reduction": summarize(d), "hpr_rel_reduction": summarize(rel),
                                               "mean_dpass_t_gain_of_second": summarize(gain)}
            per["contrasts"] = contrasts
            pop["H3"][str(q)] = per
        pop["deploy_zero_loss"] = {k: summarize(mean_over_splits(lambda r, k=k: r["deploy_zero_loss"][k]))
                                   for k in ("acceptance", "hpr")}
        pop["deploy_zero_loss"]["n_accepted_per_split_median"] = float(np.median([r["deploy_zero_loss"]["n_accepted_unweighted"] for r in rs]))
        pr = pred[p]
        pop["H2_predictive"] = {
            k: {"median": float(np.nanmedian([x[k] for x in pr])), "split_5_95": np.nanpercentile([x[k] for x in pr], [5, 95]).tolist()}
            for k in ("M0", "M1", "M2")
        }
        d21 = np.array([x["M2"] - x["M1"] for x in pr])
        pop["H2_predictive"]["M2_minus_M1"] = {"median": float(np.nanmedian(d21)), "share_positive": float(np.nanmean(d21 > 0)),
                                               "split_5_95": np.nanpercentile(d21, [5, 95]).tolist()}
        out["populations"][p] = pop
    out["runtime_s"] = round(time.time() - t0, 1)
    return out


def main(argv=None) -> None:
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
    ap.add_argument("--out", required=True)
    ap.add_argument("--progress", action="store_true")
    args = ap.parse_args(argv)
    if args.expect_sha in ("", "none"):
        args.expect_sha = None
    res = run(args)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(json.dumps({"out": args.out, "runtime_s": res["runtime_s"], "degenerate": res["splits_degenerate"]}))


if __name__ == "__main__":
    main()
