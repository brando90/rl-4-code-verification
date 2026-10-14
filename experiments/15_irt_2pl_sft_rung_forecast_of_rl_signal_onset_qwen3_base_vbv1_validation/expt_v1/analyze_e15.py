"""TLDR: Experiment 15 analysis: on the 135 validation-split VeriBench V1 tasks (D-013), does a pooled 2PL item response theory (IRT) model with ability linear in log SFT tokens, fitted on the earlier supervised fine-tuning (SFT) rungs of Qwen3 Base 1.7B/4B/8B/14B, forecast the next rung's per-task success probability and mixed-group share better than last-rung-carried-forward and a scalar scaling curve? Zero model calls; --synthetic runs the pipeline on generated data."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
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

import irt_e15 as irt  # noqa: E402
from rl4cv.forecast import verify_forecast  # noqa: E402

EXPERIMENT = "15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation"
E08 = REPO / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results"
PINS = HERE / "input_pins_e15.json"
FORECAST = HERE / "forecasts/e15_forecast.json"

SIZES = ("1.7B", "4B", "8B", "14B")
SIZE_TAG = {"1.7B": "1p7B", "4B": "4B", "8B": "8B", "14B": "14B"}
FRACS = ("0", "0.125", "0.25", "0.5", "0.75", "1.0")  # rung index 0 is the Base model (0 SFT tokens)
TOKENS = {"0": 0, "0.125": 720775, "0.25": 1442549, "0.5": 2884708, "0.75": 4318781, "1.0": 5752936}  # e08 sft_schedule.json
T1 = TOKENS["0.125"]  # the declared offset: one 12.5% rung of SFT tokens
G = 8  # group size for the mixed-group share 1 - p^G - (1 - p)^G
MIN_FIT_RUNGS = 2  # the first forecast rung has index 2 (fit on Base and 12.5%)
N_TASKS, N_SAMPLES = 135, 8
SEED, BOOT = 20261014, 10000
DEGENERATE_SHARE_MAX, MIN_ELIGIBLE_SIZES, MIN_RUNGS_PER_SIZE = 0.10, 2, 3
ARMS = ("irt_2pl", "irt_1pl", "b1_last_rung", "b2_scalar_curve")
PRIMARY_ARM, BASELINES = "irt_2pl", ("b1_last_rung", "b2_scalar_curve")
TREND_FORMS = ("log1p_ratio", "log_tokens")  # primary: log(1 + tokens / T1); sensitivity: log(tokens), Base not in the trend
OUTCOMES = ("kernel_binary", "proof_fraction")  # primary: k successes of n; secondary: round(mean_proof_fraction * n) of n


def covariate(tokens: int, form: str) -> float:
    """Training covariate x of a rung: log(1 + tokens / T1) (Base at 0) or log(tokens) (undefined for Base)."""
    if form == "log1p_ratio":
        return float(np.log1p(tokens / T1))
    if form == "log_tokens":
        return float(np.log(tokens)) if tokens > 0 else float("nan")
    raise ValueError(form)


def file_for(size: str, frac: str) -> str:
    if frac == "0":
        return "ladder/base14b_validation_per_task.csv" if size == "14B" else f"ladder/base_{SIZE_TAG[size]}_e05_validation_per_task.csv"
    return f"ladder/sft_{SIZE_TAG[size]}_f{frac.replace('.', 'p')}_validation_per_task.csv"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SplitViolation(RuntimeError):
    """A per-task file carries a task id outside the validation split (for example a test-split id)."""


def load_real(root: Path = E08, pins: Path | None = PINS) -> dict:
    """Validation-split per-task outcomes for every size and rung, with the split restriction asserted on every file."""
    val_ids = sorted((root / "split/vbv1_validation_task_ids.txt").read_text().split())
    test_ids = set((root / "split/vbv1_test_task_ids.txt").read_text().split())
    if set(val_ids) & test_ids or len(val_ids) != N_TASKS:
        raise SplitViolation("validation and test id lists overlap or the validation list is not 135 tasks")
    expected = json.loads(pins.read_text())["sha256"] if pins is not None else None
    data = {"tasks": val_ids, "sizes": list(SIZES), "rungs": {s: [] for s in SIZES}, "k": {s: {} for s in SIZES},
            "n": {s: {} for s in SIZES}, "mixed": {s: {} for s in SIZES}, "pf": {s: {} for s in SIZES}, "tokens": dict(TOKENS),
            "files": {}, "synthetic": False}
    index = {t: i for i, t in enumerate(val_ids)}
    for size in SIZES:
        for frac in FRACS:
            rel = file_for(size, frac)
            path = root / rel
            if "test" in path.name:
                raise SplitViolation(f"refusing to read a test-split file: {rel}")
            if not path.exists():
                continue
            digest = sha256_file(path)
            if expected is not None and expected.get(rel) != digest:
                raise RuntimeError(f"input hash mismatch for {rel}")
            k, n, mixed, pf = (np.full(N_TASKS, np.nan) for _ in range(4))
            seen = set()
            with path.open(newline="") as fh:
                for row in csv.DictReader(fh):
                    t = row["task_id"]
                    if t in test_ids or t not in index:
                        raise SplitViolation(f"{rel}: task {t} is not a validation-split task")
                    if t in seen:
                        raise RuntimeError(f"{rel}: duplicate task {t}")
                    seen.add(t)
                    i = index[t]
                    n[i] = float(row["samples_known"])
                    k[i] = float(row["k_kernel_binary"])
                    mixed[i] = float(row["mixed"])
                    pf[i] = float(row["mean_proof_fraction"])
            if len(seen) != N_TASKS or np.any(np.isnan(n)):
                raise RuntimeError(f"{rel}: expected {N_TASKS} validation tasks, found {len(seen)}")
            if np.any(k > n) or np.any(k < 0):
                raise RuntimeError(f"{rel}: successes outside 0..n")
            data["rungs"][size].append(frac)
            data["k"][size][frac], data["n"][size][frac], data["mixed"][size][frac], data["pf"][size][frac] = k, n, mixed, pf
            data["files"][rel] = digest
    return data


def synthetic_data(seed: int, degenerate_size: str | None = None) -> dict:
    """A 2PL-generated stand-in with the real shapes: ability linear in the primary covariate per size, hard items."""
    rng = np.random.default_rng(seed)
    tasks = [f"synthetic_task_{i:03d}" for i in range(N_TASKS)]
    a = np.exp(rng.normal(0.2, 0.3, N_TASKS))
    b = rng.normal(2.0, 1.5, N_TASKS)
    base_theta = {"1.7B": -1.5, "4B": -0.8, "8B": -0.2, "14B": 0.2}
    slope = {"1.7B": 0.5, "4B": 0.9, "8B": 1.0, "14B": 1.1}
    data = {"tasks": tasks, "sizes": list(SIZES), "rungs": {s: list(FRACS) for s in SIZES}, "k": {s: {} for s in SIZES},
            "n": {s: {} for s in SIZES}, "mixed": {s: {} for s in SIZES}, "pf": {s: {} for s in SIZES}, "tokens": dict(TOKENS),
            "files": {}, "synthetic": True, "truth": {"a": a.tolist(), "b": b.tolist()}}
    for s in SIZES:
        for f in FRACS:
            theta = base_theta[s] + slope[s] * covariate(TOKENS[f], "log1p_ratio") + rng.normal(0, 0.1)
            p = expit(a * (theta - b))
            n = np.full(N_TASKS, float(N_SAMPLES))
            k = rng.binomial(N_SAMPLES, p).astype(float)
            if s == degenerate_size:
                k[:] = 0.0
            data["k"][s][f], data["n"][s][f] = k, n
            data["mixed"][s][f] = ((k > 0) & (k < n)).astype(float)
            data["pf"][s][f] = np.clip(k / n + rng.normal(0, 0.05, N_TASKS), 0, 1)
    return data


# ----------------------------------------------------------------------------- forecasts

def counts(data: dict, size: str, frac: str, outcome: str) -> tuple[np.ndarray, np.ndarray]:
    n = data["n"][size][frac]
    if outcome == "kernel_binary":
        return data["k"][size][frac], n
    if outcome == "proof_fraction":
        return np.round(data["pf"][size][frac] * n), n
    raise ValueError(outcome)


def in_trend(frac: str, form: str) -> bool:
    return not (form == "log_tokens" and frac == "0")


def fit_linear(xs: np.ndarray, ys: np.ndarray, x_target: float) -> tuple[float, float | None]:
    """Ordinary least squares of y on x, extrapolated to x_target; with one point, carry it forward (slope None)."""
    if len(xs) >= 2 and np.ptp(xs) > 0:
        slope, intercept = np.polyfit(xs, ys, 1)
        return float(intercept + slope * x_target), float(slope)
    return float(ys[-1]), None


def forecast_rung(data: dict, r_idx: int, kind: str, form: str, outcome: str) -> tuple[dict, dict]:
    """Fit pooled item parameters on every size-rung with rung index < r_idx and forecast rung r_idx for each size."""
    persons = [(s, f) for s in data["sizes"] for f in data["rungs"][s] if FRACS.index(f) < r_idx]
    K = np.stack([counts(data, s, f, outcome)[0] for s, f in persons])
    Nn = np.stack([counts(data, s, f, outcome)[1] for s, f in persons])
    fitted = irt.fit(kind, K, Nn)
    post = irt.posterior(fitted, K, Nn)
    theta, sd = irt.eap(post)
    out = {}
    target_frac = FRACS[r_idx]
    for s in data["sizes"]:
        if target_frac not in data["rungs"][s]:
            continue
        rows = [i for i, (s2, f) in enumerate(persons) if s2 == s and in_trend(f, form)]
        if not rows:
            continue
        xs = np.array([covariate(data["tokens"][persons[i][1]], form) for i in rows])
        theta_t, slope = fit_linear(xs, theta[rows], covariate(data["tokens"][target_frac], form))
        out[s] = {"p": irt.item_probs(fitted, theta_t), "theta_forecast": theta_t, "theta_slope": slope,
                  "theta_fit": {persons[i][1]: float(theta[i]) for i in rows}, "theta_sd_fit": {persons[i][1]: float(sd[i]) for i in rows},
                  "converged": fitted["converged"], "endpoint_mass_max": float(irt.endpoint_mass(post).max())}
    info = {"n_persons": len(persons), "converged": fitted["converged"], "max_abs_grad": fitted["max_abs_grad"],
            "check_grid_max_abs_grad": fitted["check_grid_max_abs_grad"], "nit": fitted["nit"]}
    return out, info


def baseline_b1(data: dict, size: str, r_idx: int, outcome: str) -> np.ndarray | None:
    prev = [f for f in data["rungs"][size] if FRACS.index(f) < r_idx]
    if not prev:
        return None
    k, n = counts(data, size, prev[-1], outcome)
    return np.where(n > 0, k / np.maximum(n, 1), np.nan)


def baseline_b2(data: dict, size: str, r_idx: int, form: str, outcome: str) -> np.ndarray | None:
    """One scalar scaling curve per size: logit of the pooled success rate (continuity-corrected) linear in x."""
    prev = [f for f in data["rungs"][size] if FRACS.index(f) < r_idx and in_trend(f, form)]
    if not prev:
        return None
    xs, ys = [], []
    for f in prev:
        k, n = counts(data, size, f, outcome)
        rate = (k.sum() + 0.5) / (n.sum() + 1.0)
        xs.append(covariate(data["tokens"][f], form))
        ys.append(np.log(rate) - np.log1p(-rate))
    logit_t, _ = fit_linear(np.array(xs), np.array(ys), covariate(data["tokens"][FRACS[r_idx]], form))
    return np.full(N_TASKS, float(expit(logit_t)))


def rung_truth(data: dict, size: str, frac: str, outcome: str) -> dict:
    k, n = counts(data, size, frac, outcome)
    valid = n > 0
    truth = np.where(valid, k / np.maximum(n, 1), np.nan)
    return {"truth": truth, "valid": valid, "successes": float(k[valid].sum()), "attempts": float(n[valid].sum()),
            "pooled_rate": float(k[valid].sum() / n[valid].sum()), "realized_mixed_share": float(((k > 0) & (k < n))[valid].mean()),
            "degenerate": bool(k[valid].sum() == 0)}


def per_task_errors(p: np.ndarray, truth: dict) -> dict:
    """Per-task absolute error, Brier (exact mean over the n attempts), expected mixed share and pooled forecast."""
    t, valid = truth["truth"], truth["valid"]
    abs_err = np.where(valid, np.abs(p - t), np.nan)
    brier = np.where(valid, p**2 - 2 * p * t + t, np.nan)  # mean over attempts of (p - y)^2, since y^2 = y
    expected_mixed = 1 - p**G - (1 - p) ** G
    return {"abs_err": abs_err, "brier": brier, "mae": float(np.nanmean(abs_err)), "brier_mean": float(np.nanmean(brier)),
            "expected_mixed_share": float(expected_mixed[valid].mean()),
            "mixed_share_error": float(expected_mixed[valid].mean() - truth["realized_mixed_share"]),
            "pooled_forecast": float(p[valid].mean()), "pooled_error": float(p[valid].mean() - truth["pooled_rate"])}


def all_forecasts(data: dict) -> dict:
    """Every (outcome, trend form, target rung, size, arm) forecast with per-task errors; keys are strings for JSON."""
    res = {}
    for outcome in OUTCOMES:
        for form in TREND_FORMS:
            first = MIN_FIT_RUNGS + (1 if form == "log_tokens" else 0)
            for r_idx in range(first, len(FRACS)):
                frac = FRACS[r_idx]
                irt_out = {kind: forecast_rung(data, r_idx, kind, form, outcome) for kind in ("2pl", "1pl")}
                for s in data["sizes"]:
                    if frac not in data["rungs"][s] or s not in irt_out["2pl"][0]:
                        continue
                    truth = rung_truth(data, s, frac, outcome)
                    arms = {"irt_2pl": irt_out["2pl"][0][s]["p"], "irt_1pl": irt_out["1pl"][0][s]["p"],
                            "b1_last_rung": baseline_b1(data, s, r_idx, outcome), "b2_scalar_curve": baseline_b2(data, s, r_idx, form, outcome)}
                    entry = {"truth": truth, "arms": {}, "irt": {kind: {k2: v for k2, v in irt_out[kind][0][s].items() if k2 != "p"} for kind in irt_out},
                             "fit_info": {kind: irt_out[kind][1] for kind in irt_out}}
                    for arm, p in arms.items():
                        if p is None:
                            continue
                        e = per_task_errors(p, truth)
                        e["p"] = p
                        entry["arms"][arm] = e
                    res[(outcome, form, frac, s)] = entry
    return res


# ----------------------------------------------------------------------------- statistics and decision

def task_bootstrap(diffs: dict, rng: np.random.Generator, draws: int) -> dict:
    """Paired task bootstrap of per-size per-task differences (positive = IRT closer), averaged over sizes.

    Tasks are the resampling unit; one index draw is shared by every size so the pairing across sizes is kept.
    """
    sizes = list(diffs)
    j = len(next(iter(diffs.values())))
    idx = rng.integers(0, j, size=(draws, j))
    per_size = {s: np.nanmean(np.asarray(diffs[s])[idx], axis=1) for s in sizes}
    pooled = np.mean(np.stack([per_size[s] for s in sizes]), axis=0)
    out = {"point": float(np.mean([np.nanmean(diffs[s]) for s in sizes])), "lo": float(np.percentile(pooled, 2.5)),
           "hi": float(np.percentile(pooled, 97.5)), "draws": int(draws), "n_tasks": int(j), "sizes": sizes,
           "test": f"paired task bootstrap, {draws} draws, {j} tasks resampled, 95% percentile interval; p-val=n/a", "per_size": {}}
    for s in sizes:
        out["per_size"][s] = {"point": float(np.nanmean(diffs[s])), "lo": float(np.percentile(per_size[s], 2.5)),
                              "hi": float(np.percentile(per_size[s], 97.5))}
    out["excludes_zero"] = bool(out["lo"] > 0 or out["hi"] < 0)
    return out


def eligibility(data: dict, fc: dict, outcome: str = "kernel_binary", form: str = "log1p_ratio") -> dict:
    """Per-size eligibility for the primary verdict and the degenerate-target-rung accounting."""
    final = FRACS[-1]
    sizes = {}
    for s in data["sizes"]:
        rungs = data["rungs"][s]
        has_final = final in rungs and (outcome, form, final, s) in fc
        final_deg = bool(fc[(outcome, form, final, s)]["truth"]["degenerate"]) if has_final else None
        sizes[s] = {"n_rungs": len(rungs), "has_final_rung": has_final, "final_rung_degenerate": final_deg,
                    "eligible": bool(len(rungs) >= MIN_RUNGS_PER_SIZE and has_final and not final_deg),
                    "degenerate_rungs": [f for f in rungs if bool(data["k"][s][f].sum() == 0)]}
    eligible = [s for s in sizes if sizes[s]["eligible"]]
    targets = [(f, s) for (o, fm, f, s) in fc if o == outcome and fm == form and s in eligible]
    degenerate_targets = [(f, s) for f, s in targets if fc[(outcome, form, f, s)]["truth"]["degenerate"]]
    share = len(degenerate_targets) / len(targets) if targets else float("nan")
    return {"sizes": sizes, "eligible_sizes": eligible, "n_eligible": len(eligible), "n_target_rungs": len(targets), "degenerate_target_rungs": degenerate_targets,
            "degenerate_target_share": share, "min_eligible_sizes": MIN_ELIGIBLE_SIZES, "degenerate_share_max": DEGENERATE_SHARE_MAX}


def decide(primary: dict, elig: dict) -> tuple[str, str]:
    if len(elig["eligible_sizes"]) < MIN_ELIGIBLE_SIZES:
        return "INCONCLUSIVE", f"only {len(elig['eligible_sizes'])} eligible size(s) (need {MIN_ELIGIBLE_SIZES})"
    if elig["degenerate_target_share"] > DEGENERATE_SHARE_MAX:
        return "INCONCLUSIVE", f"degenerate target rungs {elig['degenerate_target_share']:.3f} > {DEGENERATE_SHARE_MAX}"
    wins = {b: (primary[b]["point"] > 0 and primary[b]["lo"] > 0) for b in BASELINES}
    if all(wins.values()):
        return "SUCCESS", "IRT 2PL MAE below both baselines at the final rung with paired task-bootstrap intervals excluding 0"
    return "NO ADVANTAGE", "failed against " + ", ".join(b for b, w in wins.items() if not w)


def summarize(data: dict, fc: dict, rng: np.random.Generator, draws: int) -> dict:
    final = FRACS[-1]
    elig = eligibility(data, fc)
    elig_sizes = elig["eligible_sizes"]
    out = {"eligibility": elig, "primary": {}, "secondary": {}, "per_rung": {}, "monotonicity": {}, "fits": {}}

    def diffs_for(outcome, form, frac, sizes, metric, baseline, arm=PRIMARY_ARM):
        d = {}
        for s in sizes:
            e = fc.get((outcome, form, frac, s))
            if e and baseline in e["arms"] and arm in e["arms"]:
                d[s] = np.asarray(e["arms"][baseline][metric]) - np.asarray(e["arms"][arm][metric])
        return d

    # Primary: MAE of per-task p at the final rung, IRT 2PL against each baseline, averaged over eligible sizes.
    if elig_sizes:
        for b in BASELINES:
            d = diffs_for("kernel_binary", "log1p_ratio", final, elig_sizes, "abs_err", b)
            out["primary"][b] = task_bootstrap(d, np.random.default_rng([SEED, 0, BASELINES.index(b)]), draws) if d else None
    verdict, reason = decide(out["primary"], elig) if all(out["primary"].get(b) for b in BASELINES) else ("INCONCLUSIVE", "primary comparison unavailable")
    out["verdict"], out["verdict_reason"] = verdict, reason
    out["success"], out["inconclusive"] = verdict == "SUCCESS", verdict == "INCONCLUSIVE"

    # Secondary: every outcome, form, rung, metric and arm; pooled intervals over sizes with data at that rung.
    for (outcome, form, frac, s), e in fc.items():
        key = f"{outcome}|{form}|{frac}|{s}"
        out["per_rung"][key] = {"truth": {k: v for k, v in e["truth"].items() if k not in ("truth", "valid")},
                                "arms": {a: {k: v for k, v in m.items() if k not in ("abs_err", "brier", "p")} for a, m in e["arms"].items()},
                                "irt": {kind: {k: v for k, v in v2.items()} for kind, v2 in e["irt"].items()}, "fit_info": e["fit_info"]}
    stream = 0  # deterministic sub-seed counter for the secondary intervals (never Python's randomized hash())
    for outcome in OUTCOMES:
        for form in TREND_FORMS:
            for frac in FRACS:
                sizes_here = [s for s in data["sizes"] if (outcome, form, frac, s) in fc]
                if not sizes_here:
                    continue
                block = {}
                for metric in ("abs_err", "brier"):
                    for arm in ("irt_2pl", "irt_1pl"):
                        for b in BASELINES:
                            stream += 1
                            d = diffs_for(outcome, form, frac, sizes_here, metric, b, arm)
                            if d:
                                block[f"{metric}:{b}-minus-{arm}"] = task_bootstrap(d, np.random.default_rng([SEED, 1, stream]), min(draws, 2000))
                out["secondary"][f"{outcome}|{form}|{frac}"] = {"sizes": sizes_here, "comparisons": block}
    # Monotonicity over training: pooled success rate and realized mixed share per size and rung.
    for s in data["sizes"]:
        rows = []
        for f in data["rungs"][s]:
            t = rung_truth(data, s, f, "kernel_binary")
            rows.append({"frac": f, "tokens": data["tokens"][f], "pooled_rate": t["pooled_rate"], "realized_mixed_share": t["realized_mixed_share"],
                         "successes": t["successes"], "attempts": t["attempts"], "degenerate": t["degenerate"]})
        rates = [r["pooled_rate"] for r in rows]
        out["monotonicity"][s] = {"rungs": rows, "pooled_rate_decreases": int(sum(1 for i in range(1, len(rates)) if rates[i] < rates[i - 1])),
                                  "mixed_share_decreases": int(sum(1 for i in range(1, len(rows)) if rows[i]["realized_mixed_share"] < rows[i - 1]["realized_mixed_share"]))}
    out["seed_variance"] = "unavailable: one SFT run per size and one sampling seed (91) per rung; no repeated runs exist"
    fits = [e["fit_info"][kind] for e in fc.values() for kind in e["fit_info"]]
    out["fits"] = {"n": len(fits), "n_converged": int(sum(1 for f in fits if f["converged"])), "all_converged": bool(all(f["converged"] for f in fits)),
                   "max_abs_grad_max": float(max(f["max_abs_grad"] for f in fits)),
                   "check_grid_max_abs_grad_max": float(max(f["check_grid_max_abs_grad"] for f in fits))}
    return out


# ----------------------------------------------------------------------------- outputs

def write_per_rung_csv(data: dict, fc: dict, path: Path) -> None:
    cols = ["outcome", "trend_form", "size", "frac", "tokens", "x", "attempts", "successes", "pooled_rate", "realized_mixed_share", "degenerate"]
    metrics = ("mae", "brier_mean", "expected_mixed_share", "mixed_share_error", "pooled_forecast", "pooled_error")
    cols += [f"{arm}__{m}" for arm in ARMS for m in metrics] + ["irt_2pl_theta_forecast", "irt_2pl_theta_slope", "irt_2pl_converged"]
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for (outcome, form, frac, s), e in sorted(fc.items(), key=lambda kv: (kv[0][0], kv[0][1], FRACS.index(kv[0][2]), SIZES.index(kv[0][3]))):
            t = e["truth"]
            row = [outcome, form, s, frac, data["tokens"][frac], covariate(data["tokens"][frac], form), t["attempts"], t["successes"],
                   f"{t['pooled_rate']:.6f}", f"{t['realized_mixed_share']:.6f}", int(t["degenerate"])]
            for arm in ARMS:
                m = e["arms"].get(arm)
                row += [f"{m[x]:.6f}" if m else "" for x in metrics]
            row += [f"{e['irt']['2pl']['theta_forecast']:.6f}", "" if e["irt"]["2pl"]["theta_slope"] is None else f"{e['irt']['2pl']['theta_slope']:.6f}", int(e["irt"]["2pl"]["converged"])]
            w.writerow(row)


def write_per_task_csv(data: dict, fc: dict, path: Path) -> None:
    with gzip.open(path, "wt", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["outcome", "trend_form", "size", "frac", "task_id", "attempts", "successes", "truth"] + [f"p_{a}" for a in ARMS])
        for (outcome, form, frac, s), e in fc.items():
            k, n = counts(data, s, frac, outcome)
            for i, t in enumerate(data["tasks"]):
                w.writerow([outcome, form, s, frac, t, int(n[i]), int(k[i]), f"{e['truth']['truth'][i]:.6f}"] + [f"{e['arms'][a]['p'][i]:.6f}" if a in e["arms"] else "" for a in ARMS])


def fmt(b: dict | None) -> str:
    return "unavailable" if not b else f"{b['point']:+.4f} [{b['lo']:+.4f}, {b['hi']:+.4f}] p-val=n/a"


def tables_markdown(summary: dict, data: dict) -> str:
    lines = [f"## Verdict: {summary['verdict']} ({summary['verdict_reason']})", ""]
    lines += ["| Comparison at the final rung (100% SFT tokens, kernel_binary, x = log(1 + tokens/t_12.5%)) | MAE difference (baseline − IRT 2PL), positive = IRT closer |", "|---|---|"]
    for b in BASELINES:
        lines.append(f"| {b} | {fmt(summary['primary'].get(b))} over sizes {summary['primary'][b]['sizes'] if summary['primary'].get(b) else []} |")
    el = summary["eligibility"]
    lines += ["", f"Eligible sizes: {el['eligible_sizes']}; degenerate target rungs: {el['degenerate_target_rungs']} of {el['n_target_rungs']} "
              f"(share {el['degenerate_target_share']:.3f}, maximum {el['degenerate_share_max']})", ""]
    for outcome in OUTCOMES:
        for form in TREND_FORMS:
            lines += [f"### {outcome}, trend form {form}", "", "| Size | Rung | Attempts | Successes | Pooled rate | Realized mixed share | "
                      + " | ".join(f"MAE {a}" for a in ARMS) + " | " + " | ".join(f"Brier {a}" for a in ARMS) + " | Expected mixed share (IRT 2PL / B1 / B2) | θ forecast (slope) |",
                      "|" + "---|" * (6 + 2 * len(ARMS) + 2)]
            for key, e in summary["per_rung"].items():
                o, f, frac, s = key.split("|")
                if o != outcome or f != form:
                    continue
                t = e["truth"]
                mae = " | ".join(f"{e['arms'][a]['mae']:.4f}" if a in e["arms"] else "–" for a in ARMS)
                br = " | ".join(f"{e['arms'][a]['brier_mean']:.4f}" if a in e["arms"] else "–" for a in ARMS)
                ems = " / ".join(f"{e['arms'][a]['expected_mixed_share']:.3f}" if a in e["arms"] else "–" for a in ("irt_2pl", "b1_last_rung", "b2_scalar_curve"))
                sl = e["irt"]["2pl"]["theta_slope"]
                lines.append(f"| {s} | {frac} | {int(t['attempts'])} | {int(t['successes'])} | {t['pooled_rate']:.4f} | {t['realized_mixed_share']:.4f} | {mae} | {br} | {ems} | "
                             f"{e['irt']['2pl']['theta_forecast']:+.3f} ({'–' if sl is None else f'{sl:+.3f}'}) |")
            lines.append("")
    lines += ["### Monotonicity over training (kernel_binary)", "", "| Size | Rung | Tokens | Successes / attempts | Pooled rate | Realized mixed share | Degenerate |", "|---|---|---|---|---|---|---|"]
    for s, m in summary["monotonicity"].items():
        for r in m["rungs"]:
            lines.append(f"| {s} | {r['frac']} | {r['tokens']:,} | {int(r['successes'])} / {int(r['attempts'])} | {r['pooled_rate']:.4f} | {r['realized_mixed_share']:.4f} | {'yes' if r['degenerate'] else 'no'} |")
        lines.append(f"| {s} | decreases | | pooled rate {m['pooled_rate_decreases']} | mixed share {m['mixed_share_decreases']} | | |")
    lines += ["", f"Seed variance: {summary['seed_variance']}.", ""]
    return "\n".join(lines)


def evaluate_forecast(analysis: dict, forecast: dict) -> list[dict]:
    rows = []
    for pred in forecast.get("predictions", []):
        node = analysis
        for key in pred["path"]:
            node = node.get(key) if isinstance(node, dict) else None
            if node is None:
                break
        row = {"id": pred["id"], "outcome": node}
        if "point" in pred and isinstance(node, (int, float)):
            lo, hi = pred["interval80"]
            row["inside_interval80"] = bool(lo <= node <= hi)
            row["error"] = float(node - pred["point"])
        if "probability" in pred and isinstance(node, bool):
            row["brier"] = float((pred["probability"] - float(node)) ** 2)
        rows.append(row)
    return rows


def to_jsonable(o):
    if isinstance(o, dict):
        return {str(k): to_jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return [to_jsonable(v) for v in o.tolist()]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def run(*, synthetic: int | None, out_dir: Path, draws: int, check_forecast: bool = True) -> dict:
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    if synthetic is None:
        if check_forecast and not (FORECAST.exists() and verify_forecast(FORECAST)):
            raise SystemExit("refusing to analyse real outcomes: the frozen forecast is missing or fails verification")
        data = load_real()
    else:
        data = synthetic_data(synthetic)
    fc = all_forecasts(data)
    summary = summarize(data, fc, np.random.default_rng(SEED), draws)
    analysis = {"experiment": EXPERIMENT, "status": "PRIMARY ANALYSES COMPUTED", "synthetic": synthetic, "seed": SEED, "bootstrap_draws": draws,
                "inputs": data["files"], "input_pins_sha256": sha256_file(PINS) if PINS.exists() else None,
                "forecast_sha256": sha256_file(FORECAST) if (synthetic is None and FORECAST.exists()) else None,
                "design": {"sizes": data["sizes"], "rungs": {s: data["rungs"][s] for s in data["sizes"]}, "tokens": data["tokens"], "t1_offset_tokens": T1, "G": G,
                           "min_fit_rungs": MIN_FIT_RUNGS, "arms": ARMS, "primary_arm": PRIMARY_ARM, "baselines": BASELINES, "trend_forms": TREND_FORMS,
                           "outcomes": OUTCOMES, "n_tasks": len(data["tasks"]), "grid": {"base": [irt.BASE.lo, irt.BASE.hi, irt.BASE.count], "check": [irt.CHECK.lo, irt.CHECK.hi, irt.CHECK.count]},
                           "priors": irt.PRIOR_SD},
                "environment": {"host": socket.gethostname(), "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
                **summary, "wall_seconds": None}
    if synthetic is None and FORECAST.exists():
        analysis["forecast_evaluation"] = evaluate_forecast(analysis, json.loads(FORECAST.read_text()))
    analysis["wall_seconds"] = round(time.time() - t0, 2)
    (out_dir / "analysis_e15.json").write_text(json.dumps(to_jsonable(analysis), indent=1) + "\n")
    write_per_rung_csv(data, fc, out_dir / "per_rung_e15.csv")
    write_per_task_csv(data, fc, out_dir / "per_task_forecasts_e15.csv.gz")
    (out_dir / "results_tables_e15.md").write_text(tables_markdown(summary, data))
    return analysis


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--synthetic", type=int, default=None, help="seed of a generated stand-in instead of the real files")
    ap.add_argument("--out-dir", type=Path, default=HERE / "results")
    ap.add_argument("--boot", type=int, default=BOOT)
    args = ap.parse_args()
    a = run(synthetic=args.synthetic, out_dir=args.out_dir, draws=args.boot)
    print(json.dumps({"verdict": a["verdict"], "reason": a["verdict_reason"], "primary": {b: fmt(a["primary"].get(b)) for b in BASELINES},
                      "eligible": a["eligibility"]["eligible_sizes"], "wall_seconds": a["wall_seconds"]}, indent=1))


if __name__ == "__main__":
    main()
