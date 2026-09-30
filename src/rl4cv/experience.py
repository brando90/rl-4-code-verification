"""Pre-RL experience-conversion coordinates: usable signal density (rho) and effective coverage (H).

This module implements the measurement side of the ICLR 2027 submission "Which Environments
Should LLMs Learn From? Predicting RL Utility Across Scale" (Section 3.2 and Appendix D).
The definitions are written for any scalar reward, so the same code measures binary
kernel-checked rewards and continuous judge rewards (for example formal specification coverage).

Terminology (paper Section 3):
    group      the G responses sampled from the starting policy for one prompt
    admitted   a response the fixed loss contract keeps; with overlong filtering, a response
               that hit the generation cap stays in the reward baseline but has zero loss weight
    rho        admitted leave-one-out |advantage| mass per million generated tokens (Eq. 5)
    H          normalized effective sample size of admitted mass across prompts (Eq. 6)
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np

TOKENS_PER_MILLION = 1e6


@dataclass(frozen=True)
class Response:
    """One sampled response inside a prompt group."""

    reward: float
    generated_tokens: int
    admitted: bool = True


@dataclass(frozen=True)
class EnvironmentMeasurement:
    """Pre-RL summary of one environment (prompt distribution) under one starting policy."""

    n_groups: int
    n_responses: int
    group_size: float
    mean_reward: float
    q_mixed_empirical: float
    admission_rate: float
    mean_generated_tokens: float
    total_generated_tokens: int
    rho: float
    rho_raw: float
    advantage_survival: float
    H: float
    token_weighted_coverage: float
    top_decile_mass_share: float

    def to_dict(self) -> dict:
        return asdict(self)


def loo_advantages(rewards: Sequence[float]) -> np.ndarray:
    """Unnormalized leave-one-out advantages a_i = r_i - mean_{j != i} r_j (paper Eq. 2)."""
    r = np.asarray(rewards, dtype=float)
    if r.ndim != 1:
        raise ValueError(f"rewards must be one-dimensional, got shape {r.shape}")
    g = r.size
    if g < 2:
        raise ValueError("a group needs at least two responses for a leave-one-out baseline")
    return r - (r.sum() - r) / (g - 1)


def q_mixed(p: float | np.ndarray, group_size: int) -> float | np.ndarray:
    """Probability that a group of independent binary rewards is mixed (paper Eq. 3)."""
    p_arr = np.asarray(p, dtype=float)
    out = 1.0 - p_arr**group_size - (1.0 - p_arr) ** group_size
    return float(out) if np.ndim(out) == 0 else out


def binary_raw_mass(k: int, group_size: int) -> float:
    """Raw |advantage| mass of a binary group with k successes: 2k(G-k)/(G-1) (paper Eq. 8)."""
    if not 0 <= k <= group_size:
        raise ValueError("k must lie in [0, G]")
    return 2.0 * k * (group_size - k) / (group_size - 1)


def group_masses(group: Sequence[Response]) -> tuple[float, float, float]:
    """Return (raw mass, admitted mass, token-weighted admitted mass) for one group (Eq. 4).

    The advantage baseline uses every response, including capped ones, matching overlong
    filtering: capped responses remain in the reward baseline but carry zero loss weight.
    The token-weighted mass multiplies each admitted |advantage| by its generated length and
    is only a diagnostic (the paper's "after token weighting" coverage stage).
    """
    rewards = [resp.reward for resp in group]
    adv = np.abs(loo_advantages(rewards))
    admitted = np.array([1.0 if resp.admitted else 0.0 for resp in group])
    lengths = np.array([float(resp.generated_tokens) for resp in group])
    raw = float(adv.sum())
    adm = float((admitted * adv).sum())
    tok = float((admitted * adv * lengths).sum())
    return raw, adm, tok


def effective_coverage(masses: Sequence[float]) -> float:
    """Normalized effective sample size (sum m)^2 / (n * sum m^2), with 0 when all masses are 0 (Eq. 6)."""
    m = np.asarray(masses, dtype=float)
    if m.size == 0:
        raise ValueError("need at least one group")
    if np.any(m < 0):
        raise ValueError("masses must be non-negative")
    total = m.sum()
    if total <= 0:
        return 0.0
    return float(total**2 / (m.size * np.square(m).sum()))


def top_decile_share(masses: Sequence[float]) -> float:
    """Share of total mass carried by the heaviest 10% of groups (at least one group)."""
    m = np.sort(np.asarray(masses, dtype=float))[::-1]
    total = m.sum()
    if total <= 0:
        return 0.0
    k = max(1, math.ceil(0.1 * m.size))
    return float(m[:k].sum() / total)


def is_mixed(group: Sequence[Response], tol: float = 1e-12) -> bool:
    """A group carries group-relative signal only when its rewards are not all equal."""
    rewards = [resp.reward for resp in group]
    return (max(rewards) - min(rewards)) > tol


def measure_environment(groups: Iterable[Sequence[Response]]) -> EnvironmentMeasurement:
    """Compute rho, H and the paper's diagnostics for one environment's probe groups."""
    groups = [list(g) for g in groups]
    if not groups:
        raise ValueError("need at least one prompt group")
    raw, adm, tok = [], [], []
    n_resp = 0
    n_adm = 0
    total_tokens = 0
    reward_sum = 0.0
    n_mixed = 0
    for group in groups:
        r, a, t = group_masses(group)
        raw.append(r)
        adm.append(a)
        tok.append(t)
        n_resp += len(group)
        n_adm += sum(1 for resp in group if resp.admitted)
        total_tokens += sum(int(resp.generated_tokens) for resp in group)
        reward_sum += sum(float(resp.reward) for resp in group)
        n_mixed += int(is_mixed(group))
    if total_tokens <= 0:
        raise ValueError("total generated tokens must be positive")
    total_raw = float(np.sum(raw))
    total_adm = float(np.sum(adm))
    return EnvironmentMeasurement(
        n_groups=len(groups),
        n_responses=n_resp,
        group_size=n_resp / len(groups),
        mean_reward=reward_sum / n_resp,
        q_mixed_empirical=n_mixed / len(groups),
        admission_rate=n_adm / n_resp,
        mean_generated_tokens=total_tokens / n_resp,
        total_generated_tokens=total_tokens,
        rho=TOKENS_PER_MILLION * total_adm / total_tokens,
        rho_raw=TOKENS_PER_MILLION * total_raw / total_tokens,
        advantage_survival=(total_adm / total_raw) if total_raw > 0 else 0.0,
        H=effective_coverage(adm),
        token_weighted_coverage=effective_coverage(tok),
        top_decile_mass_share=top_decile_share(adm),
    )


def groups_from_records(
    records: Iterable[Mapping],
    *,
    reward_key: str = "reward",
    group_key: str = "task_id",
    tokens_key: str = "generated_tokens",
    admitted_key: str = "admitted",
) -> list[list[Response]]:
    """Group flat per-response records (for example JSONL rows) into prompt groups, in first-seen order."""
    order: list[str] = []
    buckets: dict[str, list[Response]] = {}
    for rec in records:
        gid = str(rec[group_key])
        if gid not in buckets:
            buckets[gid] = []
            order.append(gid)
        buckets[gid].append(
            Response(
                reward=float(rec[reward_key]),
                generated_tokens=int(rec[tokens_key]),
                admitted=bool(rec.get(admitted_key, True)),
            )
        )
    return [buckets[g] for g in order]
