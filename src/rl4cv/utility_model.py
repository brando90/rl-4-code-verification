"""Compact environment-utility model (paper Eq. 7) with leave-one-scale-out evaluation and decision metrics.

Model (ICLR 2027 submission, Section 3.3):

    U_hat = b0 + bN * x_N + bC * s(C) + b_rho * s(C) * z(log rho) + b_H * s(C) * z(H)

with s(C) = C / (C + C0), x_N = log(N / N_a) / log(N_b / N_a) (the paper uses N_a = 1.7B,
N_b = 4B), and z() a population-standard-deviation standardization computed on the training
fold's distinct (scale, environment) cells. Utility is the held-out change from each scale's
warm start, as a fraction (0.01 = one percentage point). Cell labels are never features.

Evaluation follows the paper's Appendix D: RMSE over held-out scale-cell-budget points,
pairwise rank accuracy with half credit for exact ties, and mean allocation regret, where
ties for the highest predicted utility average their observed utilities.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class Observation:
    """One held-out utility observation (normally a two-seed mean) for a scale, environment and budget."""

    scale: float
    env: str
    budget: float
    utility: float
    rho: float
    H: float


@dataclass(frozen=True)
class FeatureSet:
    """Which environment coordinates enter the model; both False gives the budget/scale-only baseline."""

    rho: bool = True
    H: bool = True

    @property
    def name(self) -> str:
        if self.rho and self.H:
            return "rho-H"
        if self.rho:
            return "rho-only"
        if self.H:
            return "H-only"
        return "budget-scale-only"


RHO_H = FeatureSet(True, True)
RHO_ONLY = FeatureSet(True, False)
H_ONLY = FeatureSet(False, True)
BUDGET_SCALE_ONLY = FeatureSet(False, False)


@dataclass
class UtilityModel:
    """A fitted (or frozen) instance of Eq. 7."""

    beta: np.ndarray
    C0: float
    logrho_mean: float
    logrho_sd: float
    H_mean: float
    H_sd: float
    features: FeatureSet = RHO_H
    ref_scales: tuple[float, float] = (1.7, 4.0)
    meta: dict = field(default_factory=dict)

    def x_N(self, scale: float) -> float:
        a, b = self.ref_scales
        return math.log(scale / a) / math.log(b / a)

    def s(self, budget: float) -> float:
        return budget / (budget + self.C0)

    def z_logrho(self, rho: float) -> float:
        if rho <= 0:
            raise ValueError("rho must be positive to take log rho; an environment with no admitted signal is outside the model")
        return (math.log(rho) - self.logrho_mean) / self.logrho_sd

    def z_H(self, H: float) -> float:
        return (H - self.H_mean) / self.H_sd

    def design_row(self, scale: float, budget: float, rho: float, H: float) -> np.ndarray:
        s = self.s(budget)
        row = [1.0, self.x_N(scale), s]
        if self.features.rho:
            row.append(s * self.z_logrho(rho))
        if self.features.H:
            row.append(s * self.z_H(H))
        return np.array(row)

    def predict(self, scale: float, budget: float, rho: float, H: float) -> float:
        return float(self.design_row(scale, budget, rho, H) @ self.beta)

    def predict_obs(self, obs: Observation) -> float:
        return self.predict(obs.scale, obs.budget, obs.rho, obs.H)

    def env_term(self, rho: float, H: float) -> float:
        """Environment contrast per unit s(C); it fixes the environment ordering within a scale."""
        k = 3
        out = 0.0
        if self.features.rho:
            out += self.beta[k] * self.z_logrho(rho)
            k += 1
        if self.features.H:
            out += self.beta[k] * self.z_H(H)
        return float(out)

    def coefficients(self) -> dict:
        names = ["b0", "bN", "bC"] + (["b_rho"] if self.features.rho else []) + (["b_H"] if self.features.H else [])
        return dict(zip(names, (float(b) for b in self.beta)))


def paper_frozen_14b_model() -> UtilityModel:
    """The prospective 14B forecast model exactly as reported in the paper's Appendix D.

    Budgets are in millions of generated action tokens (C0 = 14.36651M) and utilities are
    pass@1 fractions; fit on 1.7B, 4B and 8B OpenR1-Math outcomes, frozen before 14B outcomes.
    """
    return UtilityModel(
        beta=np.array([-0.006221, -0.008124, 0.023489, -0.076673, 0.093314]),
        C0=14.36651,
        logrho_mean=2.280467,
        logrho_sd=0.975934,
        H_mean=0.429913,
        H_sd=0.290342,
        features=RHO_H,
        ref_scales=(1.7, 4.0),
        meta={"source": "ICLR 2027 submission, Appendix D", "domain": "OpenR1-Math", "budget_unit": "million tokens"},
    )


def _cell_standardizers(obs: Sequence[Observation]) -> tuple[float, float, float, float]:
    cells: dict[tuple[float, str], tuple[float, float]] = {}
    for o in obs:
        cells[(o.scale, o.env)] = (o.rho, o.H)
    lr = np.log(np.array([v[0] for v in cells.values()], dtype=float))
    hh = np.array([v[1] for v in cells.values()], dtype=float)
    lr_sd = float(lr.std(ddof=0)) or 1.0
    h_sd = float(hh.std(ddof=0)) or 1.0
    return float(lr.mean()), lr_sd, float(hh.mean()), h_sd


def fit_utility_model(
    obs: Sequence[Observation],
    features: FeatureSet = RHO_H,
    *,
    C0: float | None = None,
    ref_scales: tuple[float, float] = (1.7, 4.0),
) -> UtilityModel:
    """Ordinary-least-squares fit of Eq. 7 over positive budgets; C0 defaults to the training median budget."""
    train = [o for o in obs if o.budget > 0]
    if not train:
        raise ValueError("no positive-budget observations to fit")
    if C0 is None:
        C0 = float(np.median([o.budget for o in train]))
    lr_m, lr_s, h_m, h_s = _cell_standardizers(train)
    model = UtilityModel(
        beta=np.zeros(3 + int(features.rho) + int(features.H)),
        C0=C0,
        logrho_mean=lr_m,
        logrho_sd=lr_s,
        H_mean=h_m,
        H_sd=h_s,
        features=features,
        ref_scales=ref_scales,
    )
    X = np.vstack([model.design_row(o.scale, o.budget, o.rho, o.H) for o in train])
    y = np.array([o.utility for o in train])
    if len(set(o.scale for o in train)) < 2:
        # With one scale x_N is collinear with the intercept; drop it rather than return an arbitrary split.
        X = X.copy()
        X[:, 1] = 0.0
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    model.beta = beta
    model.meta = {"n_train": len(train), "train_scales": sorted(set(o.scale for o in train))}
    return model


# ---------------------------------------------------------------------------------------------
# Decision and curve metrics
# ---------------------------------------------------------------------------------------------


def _by_decision(obs: Sequence[Observation]) -> dict[tuple[float, float], list[Observation]]:
    out: dict[tuple[float, float], list[Observation]] = {}
    for o in obs:
        out.setdefault((o.scale, o.budget), []).append(o)
    return out


def pairwise_rank_accuracy(obs: Sequence[Observation], preds: Sequence[float]) -> float:
    """Fraction of environment pairs, within each (scale, budget), ordered correctly; exact ties get half credit."""
    pred_of = {id(o): p for o, p in zip(obs, preds)}
    credit = 0.0
    n = 0
    for group in _by_decision(obs).values():
        for a, b in itertools.combinations(group, 2):
            dp = pred_of[id(a)] - pred_of[id(b)]
            do = a.utility - b.utility
            if dp == 0 or do == 0:
                credit += 0.5
            elif (dp > 0) == (do > 0):
                credit += 1.0
            n += 1
    return credit / n if n else float("nan")


def allocation_regret(obs: Sequence[Observation], choose: Callable[[list[Observation]], Sequence[str]]) -> float:
    """Mean over (scale, budget) decisions of max observed utility minus the observed utility of the choice.

    `choose` returns the chosen environment label(s); several labels mean a tie, whose observed
    utilities are averaged (paper Appendix D).
    """
    regrets = []
    for group in _by_decision(obs).values():
        chosen = set(choose(group))
        best = max(o.utility for o in group)
        picked = [o.utility for o in group if o.env in chosen]
        if not picked:
            raise ValueError(f"decision rule chose {chosen}, which is not among {[o.env for o in group]}")
        regrets.append(best - float(np.mean(picked)))
    return float(np.mean(regrets))


def argmax_labels(values: Mapping[str, float]) -> list[str]:
    top = max(values.values())
    return [k for k, v in values.items() if v == top]


def model_rule(model: UtilityModel) -> Callable[[list[Observation]], list[str]]:
    return lambda group: argmax_labels({o.env: model.predict_obs(o) for o in group})


def feature_rule(feature: Callable[[Observation], float]) -> Callable[[list[Observation]], list[str]]:
    """Choose the environment with the highest pre-RL feature (for example raw mixedness or starting success)."""
    return lambda group: argmax_labels({o.env: feature(o) for o in group})


def fixed_label_rule(label: str) -> Callable[[list[Observation]], list[str]]:
    return lambda group: [label]


def uniform_portfolio_regret(obs: Sequence[Observation]) -> float:
    """Expected regret of choosing uniformly at random among the environments at each decision."""
    return float(np.mean([max(o.utility for o in g) - np.mean([o.utility for o in g]) for g in _by_decision(obs).values()]))


def best_training_label(train: Sequence[Observation]) -> str:
    """The fixed label with the highest mean observed utility in the training fold."""
    means: dict[str, list[float]] = {}
    for o in train:
        if o.budget > 0:
            means.setdefault(o.env, []).append(o.utility)
    return max(means, key=lambda k: float(np.mean(means[k])))


@dataclass
class LosoResult:
    features: str
    rmse: float
    rank_accuracy: float
    mean_regret: float
    fixed_label_regret: float
    uniform_regret: float
    per_scale: dict
    residuals: list


def leave_one_scale_out(obs: Sequence[Observation], features: FeatureSet = RHO_H) -> LosoResult:
    """Fit on all but one scale (C0 = that fold's median budget), predict the held-out scale, and pool the metrics."""
    obs = [o for o in obs if o.budget > 0]
    scales = sorted(set(o.scale for o in obs))
    if len(scales) < 3:
        raise ValueError("leave-one-scale-out needs at least three scales so every fold trains on two")
    all_test, all_pred, residuals = [], [], []
    regrets, fixed_regrets = [], []
    per_scale = {}
    for held in scales:
        train = [o for o in obs if o.scale != held]
        test = [o for o in obs if o.scale == held]
        model = fit_utility_model(train, features)
        preds = [model.predict_obs(o) for o in test]
        err = np.array(preds) - np.array([o.utility for o in test])
        label = best_training_label(train)
        r_model = allocation_regret(test, model_rule(model))
        r_fixed = allocation_regret(test, fixed_label_rule(label)) if any(o.env == label for o in test) else float("nan")
        per_scale[held] = {
            "rmse": float(np.sqrt(np.mean(err**2))),
            "rank_accuracy": pairwise_rank_accuracy(test, preds),
            "regret": r_model,
            "fixed_label": label,
            "fixed_label_regret": r_fixed,
            "coefficients": model.coefficients(),
        }
        n_dec = len(_by_decision(test))
        regrets += [r_model] * n_dec
        fixed_regrets += [r_fixed] * n_dec
        all_test += test
        all_pred += preds
        residuals += [(o.scale, o.env, o.budget, float(p - o.utility)) for o, p in zip(test, preds)]
    err = np.array(all_pred) - np.array([o.utility for o in all_test])
    return LosoResult(
        features=features.name,
        rmse=float(np.sqrt(np.mean(err**2))),
        rank_accuracy=pairwise_rank_accuracy(all_test, all_pred),
        mean_regret=float(np.mean(regrets)),
        fixed_label_regret=float(np.nanmean(fixed_regrets)),
        uniform_regret=uniform_portfolio_regret(all_test),
        per_scale=per_scale,
        residuals=residuals,
    )


def curve_envelope(residuals: Iterable[tuple[float, str, float, float]], quantile: float = 0.9) -> float:
    """Empirical curve-level envelope: the quantile of each held-out cell's maximum absolute residual across budgets."""
    worst: dict[tuple[float, str], float] = {}
    for scale, env, _budget, r in residuals:
        key = (scale, env)
        worst[key] = max(worst.get(key, 0.0), abs(r))
    if not worst:
        raise ValueError("no residuals")
    return float(np.quantile(np.array(list(worst.values())), quantile))
