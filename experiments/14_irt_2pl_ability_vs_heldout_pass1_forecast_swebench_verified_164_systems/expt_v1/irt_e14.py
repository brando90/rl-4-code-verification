"""TLDR: Unidimensional item response theory (IRT) models for experiment 14 (1PL with one common slope, 2PL, and a three-category graded response model), fitted by marginal maximum a posteriori on a fixed ability grid and scored by expected a posteriori (EAP)."""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, log_expit, logsumexp

# Ability grid and its standard-normal population weights; fitting and scoring share it.
GRID = np.linspace(-6.0, 6.0, 401)
LOG_PRIOR_W = -0.5 * GRID**2 - logsumexp(-0.5 * GRID**2)

# Item priors (frozen in PROTOCOL.md): log slope ~ N(0, 1), intercepts ~ N(0, 5^2),
# log gap between the two graded-response intercepts ~ N(0, 2^2).
PRIOR_SD = {"alpha": 1.0, "d": 5.0, "gamma": 2.0}
KINDS = ("1pl", "2pl", "grm3")
GRAD_TOL = 1e-4  # a fit is accepted when max |gradient| of the per-system objective is at most this


def _split(kind: str, x: np.ndarray, n_items: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Raw parameter blocks (log slopes, intercepts, log gaps) of a parameter vector."""
    if kind == "1pl":
        return x[:1], x[1:], x[:0]
    if kind == "2pl":
        return x[:n_items], x[n_items:], x[:0]
    if kind == "grm3":
        return x[:n_items], x[n_items : 2 * n_items], x[2 * n_items :]
    raise ValueError(f"unknown IRT model: {kind}")


def unpack(kind: str, x: np.ndarray, n_items: int) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """Slopes a (J,), intercepts d of logit P(category >= 1) (J,), and for grm3 the intercepts of logit P(category = 2)."""
    alpha, d, gamma = _split(kind, x, n_items)
    a = np.full(n_items, np.exp(alpha[0])) if kind == "1pl" else np.exp(alpha)
    return a, d, (d - np.exp(gamma) if kind == "grm3" else None)


def node_logprobs(kind: str, a: np.ndarray, d: np.ndarray, d2: np.ndarray | None) -> list[np.ndarray]:
    """Log category probabilities at every grid node, one (J × Q) array per category.

    Binary models have categories (0, 1). The graded response model has categories 0, 1, 2 with
    P(c >= 1) = σ(aθ + d), P(c = 2) = σ(aθ + d2), d2 < d; the middle category uses the stable form
    σ(z1)·σ(-z2)·(1 - exp(-(d - d2))).
    """
    z = a[:, None] * GRID[None, :] + d[:, None]
    if kind != "grm3":
        return [log_expit(-z), log_expit(z)]
    z2 = a[:, None] * GRID[None, :] + d2[:, None]
    gap = np.log(-np.expm1(-(d - d2)))[:, None]
    return [log_expit(-z), log_expit(z) + log_expit(-z2) + gap, log_expit(z2)]


def resolve_probs(kind: str, a: np.ndarray, d: np.ndarray, d2: np.ndarray | None) -> np.ndarray:
    """P(resolved) at every grid node (J × Q): the top category of each model."""
    top = d2 if kind == "grm3" else d
    return expit(a[:, None] * GRID[None, :] + top[:, None])


def _log_prior(kind: str, x: np.ndarray, n_items: int) -> tuple[float, np.ndarray]:
    alpha, d, gamma = _split(kind, x, n_items)
    sa, sd, sg = PRIOR_SD["alpha"], PRIOR_SD["d"], PRIOR_SD["gamma"]
    value = -0.5 * (np.sum((alpha / sa) ** 2) + np.sum((d / sd) ** 2) + np.sum((gamma / sg) ** 2))
    return float(value), np.concatenate([-alpha / sa**2, -d / sd**2, -gamma / sg**2])


def objective(x: np.ndarray, kind: str, cats: list[np.ndarray]) -> tuple[float, np.ndarray]:
    """Negative log posterior per system and its gradient.

    ``cats`` holds one (N × J) 0/1 indicator matrix per category. The marginal likelihood integrates each
    system's ability over the fixed grid; its gradient follows Fisher's identity (posterior-weighted
    complete-data scores).
    """
    n_sys, n_items = cats[0].shape
    a, d, d2 = unpack(kind, x, n_items)
    lps = node_logprobs(kind, a, d, d2)
    log_joint = sum(y @ lp for y, lp in zip(cats, lps)) + LOG_PRIOR_W
    log_marg = logsumexp(log_joint, axis=1)
    post = np.exp(log_joint - log_marg[:, None])
    n_q = post.sum(0)
    if kind != "grm3":
        g_z = cats[1].T @ post - expit(a[:, None] * GRID + d[:, None]) * n_q  # d loglik / d logit, per item and node
        g_slope = a * (g_z @ GRID)
        grad = np.concatenate([[g_slope.sum()] if kind == "1pl" else g_slope, g_z.sum(1)])
    else:
        r0, r1, r2 = (y.T @ post for y in cats)
        p1 = expit(a[:, None] * GRID + d[:, None])
        p2 = expit(a[:, None] * GRID + d2[:, None])
        inv = 1.0 / np.expm1(d - d2)[:, None]
        g1 = -r0 * p1 + r1 * (1.0 - p1 + inv)  # d loglik / d z1
        g2 = r1 * (-p2 - inv) + r2 * (1.0 - p2)  # d loglik / d z2
        g_both = g1 + g2
        grad = np.concatenate([a * (g_both @ GRID), g_both.sum(1), -g2.sum(1) * (d - d2)])
    lp, g_lp = _log_prior(kind, x, n_items)
    return -(float(log_marg.sum()) + lp) / n_sys, -(grad + g_lp) / n_sys


def initial_params(kind: str, cats: list[np.ndarray]) -> np.ndarray:
    """Start at unit slopes and intercepts from clipped category rates."""
    n_sys, n_items = cats[0].shape
    eps = 0.5 / n_sys
    logit = lambda p: np.log(p) - np.log1p(-p)  # noqa: E731
    if kind == "grm3":
        d1 = logit(np.clip((cats[1] + cats[2]).mean(0), eps, 1 - eps))
        d2 = logit(np.clip(cats[2].mean(0), eps, 1 - eps))
        return np.concatenate([np.zeros(n_items), d1, np.log(np.maximum(d1 - d2, 0.1))])
    d = logit(np.clip(cats[1].mean(0), eps, 1 - eps))
    return np.concatenate([np.zeros(1 if kind == "1pl" else n_items), d])


def fit(kind: str, cats: list[np.ndarray], *, maxiter: int = 20000) -> dict:
    """Marginal maximum a posteriori item parameters by L-BFGS-B, with convergence evidence."""
    if kind not in KINDS:
        raise ValueError(f"unknown IRT model: {kind}")
    if len(cats) != (3 if kind == "grm3" else 2):
        raise ValueError("category matrices do not match the model")
    res = minimize(objective, initial_params(kind, cats), args=(kind, cats), jac=True, method="L-BFGS-B",
                   options={"maxiter": maxiter, "maxfun": 2 * maxiter, "ftol": 1e-15, "gtol": 1e-10, "maxcor": 30})
    value, grad = objective(res.x, kind, cats)
    max_grad = float(np.max(np.abs(grad)))
    return {"kind": kind, "x": res.x, "n_systems": int(cats[0].shape[0]), "n_items": int(cats[0].shape[1]),
            "objective": float(value), "max_abs_grad": max_grad, "converged": max_grad <= GRAD_TOL,
            "scipy_success": bool(res.success), "scipy_message": str(res.message), "nit": int(res.nit), "nfev": int(res.nfev)}


class Scorer:
    """Precomputed node probabilities for one fitted model, for EAP scoring of systems not used in the fit."""

    def __init__(self, fitted: dict):
        self.kind, n_items = fitted["kind"], fitted["n_items"]
        self.a, self.d, self.d2 = unpack(self.kind, fitted["x"], n_items)
        self.lps = node_logprobs(self.kind, self.a, self.d, self.d2)
        self.p_resolved = resolve_probs(self.kind, self.a, self.d, self.d2)
        self.p_resolved_total = self.p_resolved.sum(0)

    def posterior(self, cats: list[np.ndarray], items: np.ndarray) -> np.ndarray:
        """Posterior weights over the grid (n × Q) from responses on ``items`` only.

        Binary models use the sufficient statistic T = Σ_j a_j x_j (the count times the common slope for 1PL),
        so systems with equal statistics get bitwise-identical posteriors.
        """
        if self.kind == "grm3":
            log_joint = sum(y[:, items] @ lp[items] for y, lp in zip(cats, self.lps))
        else:
            x = cats[1][:, items]
            stat = x.sum(1) * self.a[0] if self.kind == "1pl" else (x * self.a[items]).sum(1)
            log_joint = np.outer(stat, GRID) + self.lps[0][items].sum(0)
        log_joint = log_joint + LOG_PRIOR_W
        return np.exp(log_joint - logsumexp(log_joint, axis=1)[:, None])

    def forecast(self, post: np.ndarray, items: np.ndarray) -> np.ndarray:
        """Posterior predictive mean pass@1 over ``items`` for each system."""
        return post @ self.p_resolved[items].mean(0)

    def heldout_node_mean(self, observed: np.ndarray) -> np.ndarray:
        """Mean P(resolved) at each node over every item not in ``observed`` (the held-out half B), by complement."""
        return (self.p_resolved_total - self.p_resolved[observed].sum(0)) / (len(self.p_resolved) - len(observed))


def eap(post: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Expected a posteriori ability and posterior standard deviation."""
    mean = post @ GRID
    return mean, np.sqrt(np.maximum(post @ GRID**2 - mean**2, 0.0))
