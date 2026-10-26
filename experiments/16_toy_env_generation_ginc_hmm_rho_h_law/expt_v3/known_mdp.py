"""Known-MDP sanity family for experiment 16: a chain MDP whose value is computable exactly.

The chain has N states 0..N-1 and a goal N. In state s the policy picks one of A actions; the
correct action c(s) moves to s+1, every other action stays at s. An episode ("response") starts
at s0, runs until the goal or until the horizon T, and every action is one generated token. The
verifier reward is 1 on reaching the goal plus Gaussian noise of SD sigma. An episode that hits
the horizon is capped: like an overlong response it stays in the group baseline but is not
admitted (zero loss weight), so lengths and admission vary and rho and H can separate.

The chain is split into regions; each region r has its own hidden linear map M_r from state
features to the correct action, so training on one region transfers only partly to the others.
The policy sees phi(s) = [one-hot region, d Gaussian features].

Exact quantities (no sampling): the probability of reaching the goal within t steps from s,
V_t(s) = p(s) V_{t-1}(s+1) + (1 - p(s)) V_{t-1}(s), with p(s) = pi(c(s) | s). It is
differentiable in the policy, which gives the exact target utility and the exact-gradient oracle.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import torch

N_STATES = 16
N_REGIONS = 4
A = 4
D_FEAT = 8
MDP_SEED = 16


@dataclass(frozen=True)
class Chain:
    phi: np.ndarray  # N x (regions + d) policy inputs
    correct: np.ndarray  # N correct actions
    region: np.ndarray  # N region index


def make_chain(seed: int = MDP_SEED) -> Chain:
    rng = np.random.default_rng(seed)
    region = np.arange(N_STATES) * N_REGIONS // N_STATES
    feats = rng.standard_normal((N_STATES, D_FEAT))
    maps = rng.standard_normal((N_REGIONS, A, D_FEAT))
    correct = np.array([int(np.argmax(maps[region[s]] @ feats[s])) for s in range(N_STATES)])
    phi = np.concatenate([np.eye(N_REGIONS)[region], feats], 1).astype(np.float32)
    return Chain(phi, correct, region)


@dataclass(frozen=True)
class EnvSpec:
    """A training distribution: start states drawn uniformly from `starts`, horizon slack, reward noise."""

    name: str
    starts: tuple[int, ...]
    slack: int  # horizon T(s0) = (N - s0) + slack
    sigma: float

    def to_dict(self) -> dict:
        return asdict(self)

    def horizon(self, s0: int) -> int:
        return (N_STATES - s0) + self.slack


TARGET = EnvSpec("target_all_starts_slack4", tuple(range(N_STATES)), 4, 0.0)


def region_states(regions) -> tuple[int, ...]:
    return tuple(s for s in range(N_STATES) if s * N_REGIONS // N_STATES in set(regions))


def exact_success(p_correct: torch.Tensor, spec: EnvSpec) -> torch.Tensor:
    """Exact P(goal within T(s0)) for every s0 in spec.starts, differentiable in p_correct (length N)."""
    tmax = max(spec.horizon(s) for s in spec.starts)
    V = torch.zeros(N_STATES + 1)
    V = torch.cat([V[:-1], torch.ones(1)])  # V_0: only the goal has value 1
    by_t = [V]
    for _ in range(tmax):
        nxt = torch.cat([p_correct * V[1:] + (1 - p_correct) * V[:-1], torch.ones(1)])
        V = nxt
        by_t.append(V)
    return torch.stack([by_t[spec.horizon(s)][s] for s in spec.starts])


def exact_value(p_correct: torch.Tensor, spec: EnvSpec) -> torch.Tensor:
    return exact_success(p_correct, spec).mean()


def rollout_groups(probs: np.ndarray, chain: Chain, spec: EnvSpec, n_groups: int, G: int, rng: np.random.Generator):
    """Sample n_groups start states and G episodes each. Returns per-episode arrays and visit counts.

    probs: N x A action probabilities. Output dict: s0 (n), reward (n x G), success, tokens, capped,
    and counts (n x G x N x A) is avoided: instead `sa` lists, per episode, the (state, action) pairs.
    """
    s0 = rng.choice(np.array(spec.starts), size=n_groups)
    cum = np.cumsum(probs, 1)
    n = n_groups * G
    state = np.repeat(s0, G)
    T = np.array([spec.horizon(int(s)) for s in state])
    done = np.zeros(n, bool)
    success = np.zeros(n, bool)
    tokens = np.zeros(n, np.int64)
    sa_counts = np.zeros((n, N_STATES, A), np.float32)
    for t in range(int(T.max())):
        act = (rng.random(n)[:, None] > cum[np.minimum(state, N_STATES - 1)]).sum(1).clip(0, A - 1)
        live = ~done & (t < T)
        idx = np.where(live)[0]
        sa_counts[idx, state[idx], act[idx]] += 1
        tokens[idx] += 1
        move = live & (act == chain.correct[np.minimum(state, N_STATES - 1)])
        state = state + move
        reached = live & (state >= N_STATES)
        success |= reached
        done |= reached | (live & (t + 1 >= T))
    reward = success.astype(float) + spec.sigma * rng.standard_normal(n)
    return {
        "s0": s0,
        "reward": reward.reshape(n_groups, G),
        "success": success.reshape(n_groups, G),
        "tokens": tokens.reshape(n_groups, G),
        "capped": (~success).reshape(n_groups, G),
        "sa_counts": sa_counts.reshape(n_groups, G, N_STATES, A),
    }
