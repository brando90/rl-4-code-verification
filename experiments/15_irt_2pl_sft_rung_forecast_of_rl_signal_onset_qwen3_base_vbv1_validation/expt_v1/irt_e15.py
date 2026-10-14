"""TLDR: Binomial-count item response theory (IRT) models for experiment 15 (1PL with one common slope, and 2PL), fitted by marginal maximum a posteriori on a fixed ability grid with successes-out-of-attempts likelihoods and scored by expected a posteriori (EAP) abilities; a generalization of experiment 14's irt_e14.py from 0/1 responses to k-of-n counts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, log_expit, logsumexp


@dataclass(frozen=True)
class Grid:
    """Equally spaced ability nodes with standard-normal population weights (log scale, normalized)."""

    lo: float
    hi: float
    count: int

    @property
    def nodes(self) -> np.ndarray:
        return np.linspace(self.lo, self.hi, self.count)

    @property
    def log_w(self) -> np.ndarray:
        x = self.nodes
        return -0.5 * x**2 - logsumexp(-0.5 * x**2)


# Same grids and priors as experiment 14 (PROTOCOL.md revision 2 there): fit and score on BASE, check on CHECK.
BASE = Grid(-12.0, 12.0, 1201)
CHECK = Grid(-18.0, 18.0, 4801)
PRIOR_SD = {"alpha": 1.0, "d": 5.0}  # log slope ~ N(0, 1), intercept ~ N(0, 5^2)
KINDS = ("1pl", "2pl")
GRAD_TOL = 1e-4  # max |gradient| of the per-person objective, on BASE at the optimum and again on CHECK


def _split(kind: str, x: np.ndarray, n_items: int) -> tuple[np.ndarray, np.ndarray]:
    if kind == "1pl":
        return x[:1], x[1:]
    if kind == "2pl":
        return x[:n_items], x[n_items:]
    raise ValueError(f"unknown IRT model: {kind}")


def unpack(kind: str, x: np.ndarray, n_items: int) -> tuple[np.ndarray, np.ndarray]:
    """Slopes a (J,) and intercepts d (J,) of logit P(success) = a_j * theta + d_j; difficulty is b_j = -d_j / a_j."""
    alpha, d = _split(kind, x, n_items)
    a = np.full(n_items, np.exp(alpha[0])) if kind == "1pl" else np.exp(alpha)
    return a, d


def _log_prior(kind: str, x: np.ndarray, n_items: int) -> tuple[float, np.ndarray]:
    alpha, d = _split(kind, x, n_items)
    sa, sd = PRIOR_SD["alpha"], PRIOR_SD["d"]
    value = -0.5 * (np.sum((alpha / sa) ** 2) + np.sum((d / sd) ** 2))
    return float(value), np.concatenate([-alpha / sa**2, -d / sd**2])


def objective(x: np.ndarray, kind: str, k: np.ndarray, n: np.ndarray, grid: Grid = BASE) -> tuple[float, np.ndarray]:
    """Negative log posterior per person and its gradient for k successes out of n attempts (persons × items).

    Each person's ability is integrated over the grid; the gradient follows Fisher's identity (posterior-weighted
    complete-data scores). A cell with n = 0 (missing) contributes nothing.
    """
    n_per, n_items = k.shape
    theta = grid.nodes
    a, d = unpack(kind, x, n_items)
    z = a[:, None] * theta[None, :] + d[:, None]  # J × Q
    log_joint = k @ log_expit(z) + (n - k) @ log_expit(-z) + grid.log_w  # N × Q
    log_marg = logsumexp(log_joint, axis=1)
    post = np.exp(log_joint - log_marg[:, None])
    g_z = k.T @ post - expit(z) * (n.T @ post)  # d loglik / d z_jq
    g_slope = a * (g_z @ theta)
    grad = np.concatenate([[g_slope.sum()] if kind == "1pl" else g_slope, g_z.sum(1)])
    lp, g_lp = _log_prior(kind, x, n_items)
    return -(float(log_marg.sum()) + lp) / n_per, -(grad + g_lp) / n_per


def initial_params(kind: str, k: np.ndarray, n: np.ndarray) -> np.ndarray:
    """Start at unit slopes and intercepts from clipped pooled success rates."""
    n_items = k.shape[1]
    tot = np.maximum(n.sum(0), 1.0)
    eps = 0.5 / tot.max()
    rate = np.clip(k.sum(0) / tot, eps, 1 - eps)
    d = np.log(rate) - np.log1p(-rate)
    return np.concatenate([np.zeros(1 if kind == "1pl" else n_items), d])


def max_abs(v: np.ndarray) -> float:
    """Largest absolute entry; NaN if any entry is not finite (so a NaN can never pass a tolerance)."""
    return float(np.max(np.abs(v))) if np.all(np.isfinite(v)) else float("nan")


def fit(kind: str, k: np.ndarray, n: np.ndarray, *, maxiter: int = 20000, grid: Grid = BASE, check: Grid | None = CHECK) -> dict:
    """Marginal maximum a posteriori item parameters by L-BFGS-B, with convergence and integration evidence."""
    if kind not in KINDS:
        raise ValueError(f"unknown IRT model: {kind}")
    k, n = np.asarray(k, float), np.asarray(n, float)
    if k.shape != n.shape or np.any(k < 0) or np.any(k > n):
        raise ValueError("successes must satisfy 0 <= k <= n with matching shapes")
    res = minimize(objective, initial_params(kind, k, n), args=(kind, k, n, grid), jac=True, method="L-BFGS-B",
                   options={"maxiter": maxiter, "maxfun": 2 * maxiter, "ftol": 1e-15, "gtol": 1e-10, "maxcor": 30})
    value, grad = objective(res.x, kind, k, n, grid)
    max_grad = max_abs(grad)
    check_grad = max_abs(objective(res.x, kind, k, n, check)[1]) if check is not None else None
    ok = bool(np.isfinite(value) and np.all(np.isfinite(res.x)) and max_grad <= GRAD_TOL
              and (check_grad is None or check_grad <= GRAD_TOL))
    return {"kind": kind, "x": res.x, "n_persons": int(k.shape[0]), "n_items": int(k.shape[1]), "objective": float(value),
            "max_abs_grad": max_grad, "check_grid_max_abs_grad": check_grad, "converged": ok,
            "scipy_success": bool(res.success), "scipy_message": str(res.message), "nit": int(res.nit), "nfev": int(res.nfev)}


def posterior(fitted: dict, k: np.ndarray, n: np.ndarray, grid: Grid = BASE) -> np.ndarray:
    """Posterior weights over the grid (persons × Q) under the fitted item parameters."""
    a, d = unpack(fitted["kind"], fitted["x"], fitted["n_items"])
    z = a[:, None] * grid.nodes[None, :] + d[:, None]
    log_joint = np.asarray(k, float) @ log_expit(z) + (np.asarray(n, float) - k) @ log_expit(-z) + grid.log_w
    return np.exp(log_joint - logsumexp(log_joint, axis=1)[:, None])


def eap(post: np.ndarray, grid: Grid = BASE) -> tuple[np.ndarray, np.ndarray]:
    """Expected a posteriori ability and posterior standard deviation."""
    mean = post @ grid.nodes
    return mean, np.sqrt(np.maximum(post @ grid.nodes**2 - mean**2, 0.0))


def item_probs(fitted: dict, theta: float) -> np.ndarray:
    """P(success) of every item at one ability value."""
    a, d = unpack(fitted["kind"], fitted["x"], fitted["n_items"])
    return expit(a * float(theta) + d)


def endpoint_mass(post: np.ndarray) -> np.ndarray:
    """Posterior mass on the two end nodes, per person (support-truncation diagnostic)."""
    return post[:, 0] + post[:, -1]
