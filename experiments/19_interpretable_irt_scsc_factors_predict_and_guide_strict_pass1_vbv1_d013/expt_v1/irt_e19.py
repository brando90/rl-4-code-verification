"""TLDR: Item response theory (IRT) models for experiment 19, all fitted by marginal maximum a posteriori on fixed ability grids: a binary two-parameter logistic (2PL) model whose item intercepts are random effects around a fitted mean or around a task-feature regression (explanatory IRT), and a two-skill model in which strict success loads on one skill and graded formal specification coverage (FSC) categories load on a second, correlated skill (or the same skill, when tied); extends experiment 15's irt_e15.py."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq, minimize
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


# One-skill grids are experiment 14/15's. The two-skill product grid is coarser for cost; its fit must also pass the
# gradient gate on the finer CHECK2 grid (PROTOCOL.md section 5 has the one refit allowed if it does not).
BASE = Grid(-12.0, 12.0, 1201)
CHECK = Grid(-18.0, 18.0, 4801)
BASE2 = Grid(-9.0, 9.0, 401)
CHECK2 = Grid(-12.0, 12.0, 1201)
FIXED_PRIOR = {"weak_intercept_sd": 5.0, "coef_sd": 2.0, "log_gap_sd": 2.0, "atanh_rho_sd": 1.0, "mean_sd": 2.0}
GRAD_TOL = 1e-4
LOGP_FLOOR = 1e-300


def max_abs(v: np.ndarray) -> float:
    """Largest absolute entry; NaN if any entry is not finite (so a NaN can never pass a tolerance)."""
    return float(np.max(np.abs(v))) if np.all(np.isfinite(v)) else float("nan")


def _check_binary(y: np.ndarray, m: np.ndarray) -> None:
    if y.shape != m.shape or np.any((m != 0) & (m != 1)) or np.any((y != 0) & (y != 1) & (m > 0)):
        raise ValueError("responses must be 0/1 where observed, with a 0/1 mask of the same shape")


def _minimize(fun, x0: np.ndarray, maxiter: int):
    return minimize(fun, x0, jac=True, method="L-BFGS-B",
                    options={"maxiter": maxiter, "maxfun": 2 * maxiter, "ftol": 1e-15, "gtol": 1e-10, "maxcor": 30})


def random_intercept(n_items: int) -> np.ndarray:
    """Design matrix of a random-intercept model: d_j = w0 + e_j."""
    return np.ones((n_items, 1))


# ---------------------------------------------------------------------------------------------------------------
# One-skill binary 2PL.
#   logit P(y_ij = 1) = a_j * theta_i + d_j,  theta_i ~ N(0, 1),  log a_j ~ N(0, slope_sd^2)
#   X given:   d_j = X_j . w + e_j,  w ~ N(0, 2^2),  e_j ~ N(0, sigma_e^2)   (X = 1: random intercepts; X = [1, features]:
#              explanatory IRT with item residuals)
#   X = None:  d_j ~ N(0, 5^2)   (experiment 14/15's weak prior; sensitivity only)
# Parameters x = [log a (J), d (J), w (P)].
# ---------------------------------------------------------------------------------------------------------------


def unpack(x: np.ndarray, n_items: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return np.exp(x[:n_items]), x[n_items:2 * n_items], x[2 * n_items:]


def _log_prior_2pl(x, n_items, X, sigma_e, slope_sd) -> tuple[float, np.ndarray]:
    alpha, d, w = x[:n_items], x[n_items:2 * n_items], x[2 * n_items:]
    lp = -0.5 * np.sum((alpha / slope_sd) ** 2)
    g_alpha = -alpha / slope_sd**2
    if X is None:
        sd = FIXED_PRIOR["weak_intercept_sd"]
        return float(lp - 0.5 * np.sum((d / sd) ** 2)), np.concatenate([g_alpha, -d / sd**2])
    sw = FIXED_PRIOR["coef_sd"]
    e = d - X @ w
    lp += -0.5 * np.sum((e / sigma_e) ** 2) - 0.5 * np.sum((w / sw) ** 2)
    return float(lp), np.concatenate([g_alpha, -e / sigma_e**2, X.T @ (e / sigma_e**2) - w / sw**2])


def binary_node_loglik(a: np.ndarray, d: np.ndarray, y: np.ndarray, m: np.ndarray, nodes: np.ndarray) -> np.ndarray:
    """Per-person log-likelihood of binary responses at every grid node (persons × Q)."""
    z = a[:, None] * nodes[None, :] + d[:, None]  # J × Q
    ym = y * m
    return ym @ log_expit(z) + (m - ym) @ log_expit(-z)


def _binary_item_grad(a, d, y, m, post, nodes):
    """Fisher-identity gradient of the marginal log-likelihood w.r.t. log slopes and intercepts, given node posteriors."""
    z = a[:, None] * nodes[None, :] + d[:, None]
    g_z = (y * m).T @ post - expit(z) * (m.T @ post)  # J × Q
    return a * (g_z @ nodes), g_z.sum(1)


def objective_2pl(x, y, m, X, sigma_e, slope_sd, grid: Grid = BASE) -> tuple[float, np.ndarray]:
    """Negative log posterior per person and its gradient; abilities integrated over the grid; masked cells drop out."""
    n_per, n_items = y.shape
    a, d, _ = unpack(x, n_items)
    lj = binary_node_loglik(a, d, y, m, grid.nodes) + grid.log_w
    log_marg = logsumexp(lj, axis=1)
    post = np.exp(lj - log_marg[:, None])
    g_alpha, g_d = _binary_item_grad(a, d, y, m, post, grid.nodes)
    grad = np.concatenate([g_alpha, g_d, np.zeros(x.size - 2 * n_items)])
    lp, g_lp = _log_prior_2pl(x, n_items, X, sigma_e, slope_sd)
    return -(float(log_marg.sum()) + lp) / n_per, -(grad + g_lp) / n_per


def fit_2pl(y: np.ndarray, m: np.ndarray, *, X: np.ndarray | None = None, sigma_e: float | None = None,
            slope_sd: float = 1.0, maxiter: int = 20000, grid: Grid = BASE, check: Grid | None = CHECK) -> dict:
    """Marginal MAP item parameters by L-BFGS-B, with the gradient gate checked on the fitting and a wider grid."""
    y, m = np.asarray(y, float), np.asarray(m, float)
    _check_binary(y, m)
    if (X is None) != (sigma_e is None):
        raise ValueError("a design matrix and the residual scale sigma_e go together")
    if X is not None and X.shape[0] != y.shape[1]:
        raise ValueError("design-matrix rows must match items")
    tot = np.maximum(m.sum(0), 1.0)
    rate = np.clip(((y * m).sum(0) + 0.5) / (tot + 1.0), 1e-3, 1 - 1e-3)
    d0 = np.log(rate) - np.log1p(-rate)
    w0 = np.zeros(0) if X is None else np.linalg.lstsq(X, d0, rcond=None)[0]
    x0 = np.concatenate([np.zeros(y.shape[1]), d0, w0])
    fun = lambda x: objective_2pl(x, y, m, X, sigma_e, slope_sd, grid)  # noqa: E731
    res = _minimize(fun, x0, maxiter)
    value, grad = fun(res.x)
    max_grad = max_abs(grad)
    check_grad = max_abs(objective_2pl(res.x, y, m, X, sigma_e, slope_sd, check)[1]) if check is not None else None
    ok = bool(np.isfinite(value) and np.all(np.isfinite(res.x)) and max_grad <= GRAD_TOL
              and (check_grad is None or check_grad <= GRAD_TOL))
    return {"x": res.x, "n_items": int(y.shape[1]), "n_persons": int(y.shape[0]), "objective": float(value),
            "max_abs_grad": max_grad, "check_grid_max_abs_grad": check_grad, "converged": ok, "nit": int(res.nit),
            "X": X, "sigma_e": sigma_e, "slope_sd": slope_sd}


def item_params(fitted: dict) -> tuple[np.ndarray, np.ndarray]:
    a, d, _ = unpack(fitted["x"], fitted["n_items"])
    return a, d


def coefficients(fitted: dict) -> np.ndarray:
    return unpack(fitted["x"], fitted["n_items"])[2]


def posterior_1d(a: np.ndarray, d: np.ndarray, y: np.ndarray, m: np.ndarray, grid: Grid = BASE) -> np.ndarray:
    """Posterior node weights (persons × Q) for binary responses under fixed item parameters."""
    lj = binary_node_loglik(a, d, np.asarray(y, float), np.asarray(m, float), grid.nodes) + grid.log_w
    return np.exp(lj - logsumexp(lj, axis=1)[:, None])


def eap(post: np.ndarray, grid: Grid = BASE) -> tuple[np.ndarray, np.ndarray]:
    mean = post @ grid.nodes
    return mean, np.sqrt(np.maximum(post @ grid.nodes**2 - mean**2, 0.0))


def endpoint_mass(post: np.ndarray) -> np.ndarray:
    return post[:, 0] + post[:, -1]


def predictive_1d(a: np.ndarray, d: np.ndarray, post: np.ndarray, grid: Grid = BASE) -> np.ndarray:
    """Posterior-predictive P(success) for every person × item (the ability posterior integrated, not plugged in)."""
    return post @ expit(a[:, None] * grid.nodes[None, :] + d[:, None]).T


def new_item_curves(fitted: dict, X_new: np.ndarray | None, n_new: int, grid: Grid = BASE, chunk: int = 32) -> np.ndarray:
    """Empirical-Bayes item characteristic curves for unseen items (n_new × Q): P(success | theta) averaged over the
    fitted slopes and intercept residuals of the training items, centred at X . w (design matrix) or the mean intercept."""
    a, d, w = unpack(fitted["x"], fitted["n_items"])
    if fitted["X"] is not None:
        resid = d - fitted["X"] @ w
        centre = X_new @ w
    else:
        resid = d - d.mean()
        centre = np.full(n_new, float(d.mean()))
    out = np.empty((n_new, grid.count))
    base = a[:, None] * grid.nodes[None, :] + resid[:, None]  # K × Q
    for s in range(0, n_new, chunk):
        c = centre[s:s + chunk]
        out[s:s + chunk] = expit(base[None, :, :] + c[:, None, None]).mean(1)
    return out


def calibrate_theta(a: np.ndarray, d: np.ndarray, target_rate: float) -> float:
    """Ability at which the mean success probability over the given items equals target_rate."""
    if not 0.0 < target_rate < 1.0:
        raise ValueError("target rate must be strictly between 0 and 1")
    return float(brentq(lambda t: float(np.mean(expit(a * t + d))) - target_rate, -60.0, 60.0, xtol=1e-12))


# ---------------------------------------------------------------------------------------------------------------
# Graded response model (GRM) for ordinal FSC categories 0..C-1 on a skill f:
#   P(cat >= k) = sigmoid(b_j f + g_jk), k = 1..C-1, with g_j1 > g_j2 > ... built from a first value and log gaps.
# ---------------------------------------------------------------------------------------------------------------


def grm_cuts(first: np.ndarray, log_gaps: np.ndarray) -> np.ndarray:
    """Decreasing thresholds (J × K) from the first threshold and K-1 log gaps per item."""
    if log_gaps.shape[1] == 0:
        return first[:, None]
    return np.concatenate([first[:, None], first[:, None] - np.cumsum(np.exp(log_gaps), axis=1)], axis=1)


def grm_cat_probs(b: np.ndarray, cuts: np.ndarray, nodes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Category probabilities (J × Q × C), floored, and the cumulative probabilities (J × Q × K)."""
    cum = expit(b[:, None, None] * nodes[None, :, None] + cuts[:, None, :])
    J, Q, _ = cum.shape
    upper = np.concatenate([np.ones((J, Q, 1)), cum], axis=2)
    lower = np.concatenate([cum, np.zeros((J, Q, 1))], axis=2)
    return np.maximum(upper - lower, LOGP_FLOOR), cum


def onehot_categories(cat: np.ndarray, mask: np.ndarray, n_cats: int) -> np.ndarray:
    """persons × items × categories indicator of the observed category (all zero where unobserved)."""
    oh = np.zeros(cat.shape + (n_cats,))
    i, j = np.where(mask > 0)
    c = cat[i, j].astype(int)
    if np.any((c < 0) | (c >= n_cats)):
        raise ValueError("category outside 0..C-1")
    oh[i, j, c] = 1.0
    return oh


def _expected_counts(post: np.ndarray, oh: np.ndarray) -> np.ndarray:
    """W[j, q, c] = sum_n post[n, q] * oh[n, j, c], as one matrix product."""
    N, J, C = oh.shape
    return (post.T @ oh.reshape(N, J * C)).reshape(-1, J, C).transpose(1, 0, 2)


def _category_loglik(oh: np.ndarray, log_pc: np.ndarray) -> np.ndarray:
    """lF[n, q] = sum_{j,c} oh[n, j, c] * log_pc[j, q, c], as one matrix product."""
    N, J, C = oh.shape
    return oh.reshape(N, J * C) @ log_pc.transpose(0, 2, 1).reshape(J * C, -1)


def _grm_item_grad(b, cuts, log_gaps, oh, post, nodes):
    """Fisher-identity gradient w.r.t. log b, first thresholds and log gaps, given node posteriors (persons × Q)."""
    pc, cum = grm_cat_probs(b, cuts, nodes)
    K = cum.shape[2]
    W = _expected_counts(post, oh)
    dcum = cum * (1.0 - cum)
    g_eta = W[:, :, 1:] * dcum / pc[:, :, 1:] - W[:, :, :K] * dcum / pc[:, :, :K]  # J × Q × K
    g_logb = b * np.einsum("jqk,q->j", g_eta, nodes)
    g_cut = g_eta.sum(1)  # J × K
    g_first = g_cut.sum(1)
    if K > 1:
        tail = np.cumsum(g_cut[:, :0:-1], axis=1)[:, ::-1]  # sum over k > l, for l = 0..K-2
        g_gaps = -np.exp(log_gaps) * tail
    else:
        g_gaps = np.zeros((cuts.shape[0], 0))
    return g_logb, g_first, g_gaps


# ---------------------------------------------------------------------------------------------------------------
# Two-skill model. Strict success (binary 2PL) loads on skill s; FSC categories (GRM) load on skill f.
# Untied: (s, f) ~ N(0, [[1, rho], [rho, 1]]), rho = tanh(r), r ~ N(0, 1); integrated on the product grid in log space.
# Tied: s = f = theta ~ N(0, 1) on the one-dimensional grid (the one-skill special case).
# Priors: log a, log b ~ N(0, slope_sd^2); d_j ~ N(mu_d, sigma_e^2); first_j ~ N(mu_g, sigma_e^2); mu_d, mu_g ~ N(0, 2^2);
# log gaps ~ N(0, 2^2).
# x = [log a (J), d (J), log b (J), first (J), log gaps (J*(K-1)), mu_d, mu_g, r (untied only)]
# ---------------------------------------------------------------------------------------------------------------


def _layout(n_items: int, n_cats: int, tied: bool) -> dict:
    K = n_cats - 1
    sizes = [("alpha", n_items), ("d", n_items), ("beta", n_items), ("first", n_items), ("gaps", n_items * (K - 1)),
             ("mu_d", 1), ("mu_g", 1), ("r", 0 if tied else 1)]
    out, start = {}, 0
    for k, s in sizes:
        out[k] = slice(start, start + s)
        start += s
    out["size"], out["K"] = start, K
    return out


def two_skill_params(x: np.ndarray, n_items: int, n_cats: int, tied: bool) -> dict:
    lay = _layout(n_items, n_cats, tied)
    log_gaps = x[lay["gaps"]].reshape(n_items, lay["K"] - 1)
    return {"a": np.exp(x[lay["alpha"]]), "d": x[lay["d"]], "b": np.exp(x[lay["beta"]]), "first": x[lay["first"]],
            "log_gaps": log_gaps, "cuts": grm_cuts(x[lay["first"]], log_gaps),
            "rho": None if tied else float(np.tanh(x[lay["r"]][0]))}


def _log_phi(nodes: np.ndarray, rho: float) -> tuple[np.ndarray, np.ndarray]:
    """Normalized log weights of the bivariate normal on the product grid (Q × Q) and d log weights / d rho."""
    s, f = nodes[:, None], nodes[None, :]
    one = 1.0 - rho**2
    lw = -0.5 * (s**2 - 2.0 * rho * s * f + f**2) / one
    log_phi = lw - logsumexp(lw)
    h = -0.5 * (-2.0 * s * f * one + 2.0 * rho * (s**2 - 2.0 * rho * s * f + f**2)) / one**2
    return log_phi, h - float(np.sum(np.exp(log_phi) * h))


def two_skill_node_logliks(par: dict, ys, ms, oh, nodes) -> tuple[np.ndarray, np.ndarray]:
    """Per-person strict and FSC log-likelihoods at every node (each persons × Q)."""
    lS = binary_node_loglik(par["a"], par["d"], ys, ms, nodes)
    pc, _ = grm_cat_probs(par["b"], par["cuts"], nodes)
    return lS, _category_loglik(oh, np.log(pc))


def two_skill_posterior(par: dict, lS: np.ndarray, lF: np.ndarray, grid: Grid):
    """Log marginal likelihood per person and posteriors: (logZ, joint or None, post_s, post_f, dlogZ/drho or None)."""
    if par["rho"] is None:
        lj = lS + lF + grid.log_w
        logz = logsumexp(lj, axis=1)
        post = np.exp(lj - logz[:, None])
        return logz, None, post, post, None
    log_phi, dlog_phi = _log_phi(grid.nodes, par["rho"])
    lj = lS[:, :, None] + lF[:, None, :] + log_phi[None, :, :]  # N × Q × Q
    logz = logsumexp(lj.reshape(lj.shape[0], -1), axis=1)
    joint = np.exp(lj - logz[:, None, None])
    return logz, joint, joint.sum(2), joint.sum(1), np.einsum("nqr,qr->n", joint, dlog_phi)


def objective_two_skill(x, ys, ms, oh, n_cats, tied, grid, slope_sd, sigma_e) -> tuple[float, np.ndarray]:
    """Negative log posterior per person and its analytic gradient (Fisher's identity on the grid)."""
    n_per, n_items = ys.shape
    lay = _layout(n_items, n_cats, tied)
    par = two_skill_params(x, n_items, n_cats, tied)
    lS, lF = two_skill_node_logliks(par, ys, ms, oh, grid.nodes)
    logz, _, post_s, post_f, dz_rho = two_skill_posterior(par, lS, lF, grid)
    grad = np.zeros_like(x)
    grad[lay["alpha"]], grad[lay["d"]] = _binary_item_grad(par["a"], par["d"], ys, ms, post_s, grid.nodes)
    g_logb, g_first, g_gaps = _grm_item_grad(par["b"], par["cuts"], par["log_gaps"], oh, post_f, grid.nodes)
    grad[lay["beta"]], grad[lay["first"]], grad[lay["gaps"]] = g_logb, g_first, g_gaps.ravel()
    if not tied:
        grad[lay["r"]] = float(dz_rho.sum()) * (1.0 - par["rho"] ** 2)
    # priors
    lp = 0.0
    for key, s in (("alpha", slope_sd), ("beta", slope_sd), ("gaps", FIXED_PRIOR["log_gap_sd"]),
                   ("mu_d", FIXED_PRIOR["mean_sd"]), ("mu_g", FIXED_PRIOR["mean_sd"])) + \
            (() if tied else (("r", FIXED_PRIOR["atanh_rho_sd"]),)):
        v = x[lay[key]]
        lp += -0.5 * float(np.sum((v / s) ** 2))
        grad[lay[key]] += -v / s**2
    for key, mu_key in (("d", "mu_d"), ("first", "mu_g")):
        e = x[lay[key]] - x[lay[mu_key]][0]
        lp += -0.5 * float(np.sum((e / sigma_e) ** 2))
        grad[lay[key]] += -e / sigma_e**2
        grad[lay[mu_key]] += float(np.sum(e)) / sigma_e**2
    return -(float(logz.sum()) + lp) / n_per, -grad / n_per


def fit_two_skill(ys: np.ndarray, ms: np.ndarray, cat: np.ndarray, mc: np.ndarray, n_cats: int, *, tied: bool,
                  slope_sd: float, sigma_e: float, grid: Grid | None = None, check: Grid | None = None,
                  maxiter: int = 20000) -> dict:
    """Marginal MAP for the two-skill model (or its tied one-skill special case) with the gradient gate."""
    ys, ms, mc = np.asarray(ys, float), np.asarray(ms, float), np.asarray(mc, float)
    _check_binary(ys, ms)
    grid = grid or (BASE if tied else BASE2)
    check = check if check is not None else (CHECK if tied else CHECK2)
    n_items = ys.shape[1]
    lay = _layout(n_items, n_cats, tied)
    oh = onehot_categories(np.asarray(cat), mc, n_cats)
    rate = np.clip(((ys * ms).sum(0) + 0.5) / (ms.sum(0) + 1.0), 1e-3, 1 - 1e-3)
    x0 = np.zeros(lay["size"])
    x0[lay["d"]] = np.log(rate) - np.log1p(-rate)
    x0[lay["mu_d"]] = float(np.mean(x0[lay["d"]]))
    # thresholds start at the pooled cumulative category logits of each item (0.5-smoothed)
    counts = oh.sum(0) + 0.5  # J × C
    tail = np.cumsum(counts[:, ::-1], axis=1)[:, ::-1][:, 1:] / counts.sum(1, keepdims=True)  # P(cat >= k), k = 1..K
    g0 = np.log(tail) - np.log1p(-tail)
    g0 = np.minimum.accumulate(g0, axis=1) - 1e-3 * np.arange(lay["K"])[None, :]
    x0[lay["first"]] = g0[:, 0]
    x0[lay["mu_g"]] = float(np.mean(g0[:, 0]))
    if lay["K"] > 1:
        x0[lay["gaps"]] = np.log(np.maximum(-np.diff(g0, axis=1), 1e-3)).ravel()
    fun = lambda x: objective_two_skill(x, ys, ms, oh, n_cats, tied, grid, slope_sd, sigma_e)  # noqa: E731
    res = _minimize(fun, x0, maxiter)
    value, grad = fun(res.x)
    max_grad = max_abs(grad)
    check_grad = max_abs(objective_two_skill(res.x, ys, ms, oh, n_cats, tied, check, slope_sd, sigma_e)[1]) if check else None
    ok = bool(np.isfinite(value) and max_grad <= GRAD_TOL and (check_grad is None or check_grad <= GRAD_TOL))
    par = two_skill_params(res.x, n_items, n_cats, tied)
    return {"x": res.x, "n_items": n_items, "n_cats": n_cats, "tied": tied, "rho": par["rho"], "objective": float(value),
            "max_abs_grad": max_grad, "check_grid_max_abs_grad": check_grad, "converged": ok, "nit": int(res.nit),
            "grid": (grid.lo, grid.hi, grid.count), "slope_sd": slope_sd, "sigma_e": sigma_e}


def two_skill_predict(fitted: dict, ys_obs, ms_obs, cat_obs, mc_obs, target: np.ndarray) -> dict:
    """Posterior-predictive P(strict), P(top FSC category), P(strict and top FSC category) and every FSC category's
    probability on target items, for persons observed on (ys_obs, cat_obs); arrays index the fitted item set."""
    grid = Grid(*fitted["grid"])
    par = two_skill_params(fitted["x"], fitted["n_items"], fitted["n_cats"], fitted["tied"])
    oh = onehot_categories(np.asarray(cat_obs), np.asarray(mc_obs, float), fitted["n_cats"])
    lS, lF = two_skill_node_logliks(par, np.asarray(ys_obs, float), np.asarray(ms_obs, float), oh, grid.nodes)
    _, joint, post_s, post_f, _ = two_skill_posterior(par, lS, lF, grid)
    A = expit(par["a"][target, None] * grid.nodes[None, :] + par["d"][target, None])  # T × Q
    pc, _ = grm_cat_probs(par["b"][target], par["cuts"][target], grid.nodes)
    B = pc[:, :, -1]  # T × Q: P(top category | f)
    if joint is None:
        p_both = post_s @ (A * B).T
    else:
        p_both = np.einsum("nqr,tq,tr->nt", joint, A, B, optimize=True)
    return {"strict": post_s @ A.T, "top": post_f @ B.T, "both": p_both, "cat_probs": np.einsum("nq,tqc->ntc", post_f, pc),
            "endpoint_mass": float(np.max(post_s[:, [0, -1]].sum(1)))}
