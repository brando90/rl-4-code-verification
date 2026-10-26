"""TLDR: Experiment 20's pluggable GRPO prompt samplers over the 539 D-013 train tasks: Uniform (seeded permutation without replacement, re-permuted when exhausted), StaticFilter (uniform over the tasks the start policy solved 1-7 of 8 in Phase 0), DynamicDAPO (uniform stream plus all-0/all-1 group filtering with refill and a generated-rollout budget) and IRTOnline (12 of 16 groups drawn without replacement in proportion to the 2PL item information a^2 p(1-p) at the current ability estimate, 4 uniform, with a sequential EAP ability update after every update); every sampler is checkpointable through state()/from_state()."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.special import expit, logsumexp

G = 8  # rollouts per group


def active_group(k: int, g: int = G) -> bool:
    """A group carries gradient only when it mixes successes and failures (1..g-1 strict successes)."""
    return 1 <= int(k) <= g - 1


def forecast_active(p: np.ndarray, g: int = G) -> np.ndarray:
    """Probability that a group of g Bernoulli(p) rollouts is active: 1 - p^g - (1 - p)^g."""
    p = np.asarray(p, float)
    return 1.0 - p**g - (1.0 - p) ** g


def eap_update(theta_prev: float, prior_sd: float, k: np.ndarray, n: np.ndarray, a: np.ndarray, d: np.ndarray,
               nodes: np.ndarray) -> tuple[float, float]:
    """CAT-style sequential update (textbook chapter 6): prior N(theta_prev, prior_sd^2) on the grid, binomial
    likelihood of k_j successes in n_j trials with p_j(theta) = sigmoid(a_j theta + d_j); returns the EAP and its SD."""
    k, n, a, d = (np.asarray(x, float) for x in (k, n, a, d))
    z = a[:, None] * nodes[None, :] + d[:, None]  # items x Q
    log_lik = k @ np.log(expit(z)) + (n - k) @ np.log(expit(-z))
    log_post = log_lik - 0.5 * ((nodes - theta_prev) / prior_sd) ** 2
    post = np.exp(log_post - logsumexp(log_post))
    mean = float(post @ nodes)
    sd = float(np.sqrt(max(post @ nodes**2 - mean**2, 0.0)))
    return mean, sd


def weighted_sample_without_replacement(rng: np.random.Generator, weights: np.ndarray, size: int) -> np.ndarray:
    """Efraimidis-Spirakis: keys u^(1/w) (u uniform) rank items; the top `size` keys form a weighted sample without
    replacement in which the first draw has probability proportional to w. Zero-weight items are never chosen."""
    w = np.asarray(weights, float)
    if size > int((w > 0).sum()):
        raise ValueError("not enough positive-weight items for a weighted sample without replacement")
    u = rng.random(w.size)
    keys = np.full(w.size, -np.inf)
    pos = w > 0
    keys[pos] = np.log(u[pos]) / w[pos]
    return np.argsort(-keys)[:size]


class PromptSampler:
    """Base class: next_groups(n) returns task ids for the next generation batch; observe() feeds back strict counts."""

    name = "base"

    def __init__(self, task_ids: list[str], seed: int):
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("task ids must be unique")
        self.task_ids = list(task_ids)
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)
        self.drawn: list[list[str]] = []

    def next_groups(self, n: int) -> list[str]:
        raise NotImplementedError

    def observe(self, update: int, task_ids: list[str], successes: list[int], trials: list[int]) -> None:
        """Default: outcomes are recorded nowhere (uniform and static samplers do not adapt)."""

    def state(self) -> dict:
        return {"name": self.name, "seed": self.seed, "rng": self.rng.bit_generator.state, "drawn": self.drawn}

    def load_state(self, s: dict) -> None:
        if s["name"] != self.name or s["seed"] != self.seed:
            raise ValueError("sampler state belongs to a different sampler")
        self.rng.bit_generator.state = s["rng"]
        self.drawn = [list(x) for x in s["drawn"]]


class Uniform(PromptSampler):
    """Arm A (and the prompt stream shared by arms B and E): a seeded permutation of the pool, consumed in order;
    when it runs out a fresh permutation starts (a task repeats only after every other task was drawn)."""

    name = "uniform"

    def __init__(self, task_ids: list[str], seed: int, pool: list[str] | None = None):
        super().__init__(task_ids, seed)
        self.pool = list(pool) if pool is not None else list(task_ids)
        if not self.pool or set(self.pool) - set(task_ids):
            raise ValueError("the pool must be a non-empty subset of the task ids")
        self._stream: list[str] = []

    def next_groups(self, n: int) -> list[str]:
        out: list[str] = []
        while len(out) < n:
            if not self._stream:
                self._stream = [self.pool[i] for i in self.rng.permutation(len(self.pool))]
            take = min(n - len(out), len(self._stream))
            out.extend(self._stream[:take])
            self._stream = self._stream[take:]
        self.drawn.append(list(out))
        return out

    def state(self) -> dict:
        return {**super().state(), "stream": list(self._stream), "pool": list(self.pool)}

    def load_state(self, s: dict) -> None:
        super().load_state(s)
        self._stream = list(s["stream"])


class StaticFilter(Uniform):
    """Arm S: uniform over the tasks the start policy solved 1..7 of 8 times in Phase 0 (no IRT)."""

    name = "static_filter"

    def __init__(self, task_ids: list[str], seed: int, phase0_successes: dict[str, int], g: int = G):
        eligible = [t for t in task_ids if active_group(phase0_successes[t], g)]
        if len(eligible) < 16:
            raise ValueError(f"only {len(eligible)} tasks are eligible for the static filter; need at least 16")
        super().__init__(task_ids, seed, pool=eligible)


@dataclass
class DAPOBudget:
    """Generated-rollout accounting for arm E: every rollout counts, including dropped groups."""

    rollout_budget: int
    generated: int = 0
    updates: int = 0
    dropped_groups: int = 0
    kept_groups: int = 0

    @property
    def exhausted(self) -> bool:
        return self.generated >= self.rollout_budget


class DynamicDAPO(Uniform):
    """Arm E: DAPO dynamic sampling over A's uniform stream. The trainer draws batches with next_groups(), scores them,
    and calls filter_active() to keep 1..7-of-8 groups, refilling until `groups_per_update` active groups are held or
    the rollout budget is spent; register_generated() charges every rollout against the budget."""

    name = "dynamic_dapo"

    def __init__(self, task_ids: list[str], seed: int, rollout_budget: int = 48 * 16 * G, groups_per_update: int = 16, g: int = G):
        super().__init__(task_ids, seed)
        self.budget = DAPOBudget(rollout_budget)
        self.groups_per_update = groups_per_update
        self.g = g

    def register_generated(self, n_rollouts: int) -> None:
        self.budget.generated += int(n_rollouts)

    def filter_active(self, task_ids: list[str], successes: list[int]) -> list[int]:
        keep = [i for i, k in enumerate(successes) if active_group(k, self.g)]
        self.budget.kept_groups += len(keep)
        self.budget.dropped_groups += len(successes) - len(keep)
        return keep

    def state(self) -> dict:
        return {**super().state(), "budget": self.budget.__dict__}

    def load_state(self, s: dict) -> None:
        super().load_state(s)
        self.budget = DAPOBudget(**s["budget"])


@dataclass
class IRTItems:
    """Frozen 2PL item parameters aligned with a task id list."""

    task_ids: list[str]
    a: np.ndarray
    d: np.ndarray

    def __post_init__(self):
        self.a, self.d = np.asarray(self.a, float), np.asarray(self.d, float)
        if not (len(self.task_ids) == self.a.size == self.d.size) or np.any(self.a <= 0):
            raise ValueError("item parameters must align with the task ids and have positive discriminations")
        self.index = {t: i for i, t in enumerate(self.task_ids)}

    def p(self, theta: float) -> np.ndarray:
        return expit(self.a * theta + self.d)


class IRTOnline(PromptSampler):
    """Arms C and D. Per update: `irt_share` of the groups (12 of 16) are drawn without replacement in proportion to the
    2PL item information a_j^2 p_j (1 - p_j) at the current ability estimate (textbook section 6.2.2), the rest uniformly
    from the remaining tasks; after the update the ability is re-estimated by EAP with prior N(theta_prev, prior_sd^2)
    and the update's strict counts (the smooth reward never enters). Forecasts P(active) at draw time are kept for H2."""

    name = "irt_online"

    def __init__(self, task_ids: list[str], seed: int, items: IRTItems, theta0: float, theta0_sd: float,
                 nodes: np.ndarray, irt_share: float = 0.75, prior_sd: float = 1.0, g: int = G):
        super().__init__(task_ids, seed)
        if list(items.task_ids) != list(task_ids):
            raise ValueError("item parameters must be aligned with the sampler's task ids")
        self.items, self.nodes, self.irt_share, self.prior_sd, self.g = items, np.asarray(nodes, float), irt_share, prior_sd, g
        self.theta, self.theta_sd = float(theta0), float(theta0_sd)
        self.history: list[dict] = [{"update": 0, "theta": self.theta, "theta_sd": self.theta_sd}]
        self.forecasts: list[dict] = []

    def weights(self) -> np.ndarray:
        p = self.items.p(self.theta)
        return self.items.a**2 * p * (1.0 - p)

    def next_groups(self, n: int) -> list[str]:
        n_irt = int(round(self.irt_share * n))
        w = self.weights()
        chosen = list(weighted_sample_without_replacement(self.rng, w, n_irt))
        rest = np.setdiff1d(np.arange(len(self.task_ids)), np.array(chosen, int))
        chosen += list(self.rng.choice(rest, size=n - n_irt, replace=False))
        p = self.items.p(self.theta)
        out = [self.task_ids[i] for i in chosen]
        for pos, i in enumerate(chosen):
            self.forecasts.append({"update": len(self.drawn) + 1, "task_id": self.task_ids[i], "irt_draw": pos < n_irt,
                                   "theta": self.theta, "p": float(p[i]), "p_active": float(forecast_active(p[i], self.g)),
                                   "weight": float(w[i])})
        self.drawn.append(out)
        return out

    def observe(self, update: int, task_ids: list[str], successes: list[int], trials: list[int]) -> None:
        idx = [self.items.index[t] for t in task_ids]
        self.theta, self.theta_sd = eap_update(self.theta, self.prior_sd, np.asarray(successes), np.asarray(trials),
                                               self.items.a[idx], self.items.d[idx], self.nodes)
        self.history.append({"update": int(update), "theta": self.theta, "theta_sd": self.theta_sd,
                             "successes": int(np.sum(successes)), "trials": int(np.sum(trials))})

    def state(self) -> dict:
        return {**super().state(), "theta": self.theta, "theta_sd": self.theta_sd, "history": self.history, "forecasts": self.forecasts}

    def load_state(self, s: dict) -> None:
        super().load_state(s)
        self.theta, self.theta_sd = float(s["theta"]), float(s["theta_sd"])
        self.history, self.forecasts = [dict(x) for x in s["history"]], [dict(x) for x in s["forecasts"]]


def make_sampler(arm: str, task_ids: list[str], seed: int, *, phase0_successes: dict[str, int] | None = None,
                 items: IRTItems | None = None, theta0: float | None = None, theta0_sd: float | None = None,
                 nodes: np.ndarray | None = None, rollout_budget: int = 48 * 16 * G) -> PromptSampler:
    """One trainer, one sampler per arm: A/B uniform (shared stream), S static filter, E DAPO, C/D IRT-online."""
    if arm in ("A", "B"):
        return Uniform(task_ids, seed)
    if arm == "S":
        return StaticFilter(task_ids, seed, phase0_successes)
    if arm == "E":
        return DynamicDAPO(task_ids, seed, rollout_budget=rollout_budget)
    if arm in ("C", "D"):
        return IRTOnline(task_ids, seed, items, theta0, theta0_sd, nodes)
    raise KeyError(arm)
