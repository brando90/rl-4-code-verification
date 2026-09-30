"""Policy-relative 2x2 environment construction: group signal (mixedness) x admission/cost.

This follows the rules described in the paper's Section 4 and Appendix A as closely as the text
allows: broad Stage A bands, deterministic hash caps (no ranking by extremeness), pooled
success/admission over three independent G=8 probes with averaged mixedness indicators, balanced
mean starting success across cells, and a fresh Stage D confirmation gate. The paper's own
selection code lives in its submission archive; when it is synced into the rl-env-scaling fork,
prefer it and keep this module as the documented approximation.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np

CELLS = ("HH", "HL", "LH", "LL")


@dataclass(frozen=True)
class ProbeStage:
    """One independent probe of one prompt: G rewards and which responses hit the generation cap."""

    rewards: tuple[float, ...]
    capped: tuple[bool, ...]

    @property
    def group_size(self) -> int:
        return len(self.rewards)

    @property
    def mixed(self) -> bool:
        return (max(self.rewards) - min(self.rewards)) > 1e-12

    @property
    def n_noncapped(self) -> int:
        return sum(1 for c in self.capped if not c)


@dataclass(frozen=True)
class BandRule:
    """Stage A bands; defaults are the paper's values for G = 8."""

    high_admission_min_noncapped: int = 3
    low_admission_max_noncapped: int = 4
    cap_per_band: int = 640


def stable_hash(prompt_id: str, salt: str = "") -> int:
    return int(hashlib.sha256(f"{salt}:{prompt_id}".encode()).hexdigest()[:16], 16)


def stage_a_bands(stage_a: Mapping[str, ProbeStage], rule: BandRule = BandRule(), salt: str = "stageA") -> dict[str, list[str]]:
    """Candidate pools per cell from one probe, each hash-capped without ranking by extremeness."""
    pools: dict[str, list[str]] = {c: [] for c in CELLS}
    for pid, st in stage_a.items():
        signal = "H" if st.mixed else "L"
        adm_bands = []
        if st.n_noncapped >= rule.high_admission_min_noncapped:
            adm_bands.append("H")
        if st.n_noncapped <= rule.low_admission_max_noncapped:
            adm_bands.append("L")
        for a in adm_bands:
            pools[signal + a].append(pid)
    for c in CELLS:
        pools[c] = sorted(pools[c], key=lambda p: stable_hash(p, salt))[: rule.cap_per_band]
    return pools


@dataclass(frozen=True)
class PooledStats:
    success: float
    admission: float
    mixedness: float


def pooled_stats(stages: Sequence[ProbeStage]) -> PooledStats:
    """Pool response-level success and admission across stages; average the per-stage mixedness indicators."""
    rewards = [r for st in stages for r in st.rewards]
    capped = [c for st in stages for c in st.capped]
    return PooledStats(
        success=float(np.mean(rewards)),
        admission=float(np.mean([0.0 if c else 1.0 for c in capped])),
        mixedness=float(np.mean([1.0 if st.mixed else 0.0 for st in stages])),
    )


@dataclass
class CellSelection:
    cells: dict[str, list[str]]
    mean_success: dict[str, float]
    mean_admission: dict[str, float]
    mean_mixedness: dict[str, float]
    success_spread: float
    admission_contrast: float
    target_success: float


def select_balanced_cells(
    pools: Mapping[str, Sequence[str]],
    stats: Mapping[str, PooledStats],
    n_per_cell: int = 256,
    *,
    min_mixedness_high: float = 2 / 3,
    max_mixedness_low: float = 1 / 3,
    success_tol: float = 0.005,
    salt: str = "select",
    max_iter: int = 20000,
) -> CellSelection:
    """Pick disjoint cells of `n_per_cell` prompts with matched mean pooled success.

    Prompts must keep their Stage A signal label after pooling (averaged mixedness at least
    `min_mixedness_high` for high-signal cells, at most `max_mixedness_low` for low-signal cells).
    The common target is the median of the cells' hash-order means, clipped to the range every
    cell can reach. Cells are filled scarcest pool first: start from the first prompts in hash
    order, then swap one member for one spare at a time, each swap landing as close to the
    target as possible, until the cell mean is within `success_tol` or no swap helps.
    """
    eligible: dict[str, list[str]] = {}
    for c in CELLS:
        keep = []
        for p in pools.get(c, []):
            m = stats[p].mixedness
            if (c[0] == "H" and m >= min_mixedness_high) or (c[0] == "L" and m <= max_mixedness_low):
                keep.append(p)
        eligible[c] = sorted(keep, key=lambda p: stable_hash(p, salt))
    short = {c: len(eligible[c]) for c in CELLS if len(eligible[c]) < n_per_cell}
    if short:
        raise ValueError(f"not enough eligible prompts for cells {short}; enlarge the candidate pool")

    def succ(p: str) -> float:
        return stats[p].success

    lows, highs, starts = [], [], []
    for c in CELLS:
        vals = sorted(succ(p) for p in eligible[c])
        lows.append(float(np.mean(vals[:n_per_cell])))
        highs.append(float(np.mean(vals[-n_per_cell:])))
        starts.append(float(np.mean([succ(p) for p in eligible[c][:n_per_cell]])))
    lo, hi = max(lows), min(highs)
    if lo > hi:
        raise ValueError(f"no common mean success is reachable by every cell (needs {lo:.3f} <= {hi:.3f})")
    target = float(min(max(float(np.median(starts)), lo), hi))

    taken: set[str] = set()
    chosen: dict[str, list[str]] = {}
    for c in sorted(CELLS, key=lambda k: (len(eligible[k]), k)):
        avail = [p for p in eligible[c] if p not in taken]
        if len(avail) < n_per_cell:
            raise ValueError(f"cell {c} has {len(avail)} untaken eligible prompts; enlarge the candidate pool")
        members = list(avail[:n_per_cell])
        spare = list(avail[n_per_cell:])
        total = sum(succ(p) for p in members)
        for _ in range(max_iter):
            gap = target * n_per_cell - total
            if abs(gap) <= success_tol * n_per_cell or not spare:
                break
            member = min(members, key=succ) if gap > 0 else max(members, key=succ)
            best = min(spare, key=lambda p: abs(succ(p) - succ(member) - gap))
            delta = succ(best) - succ(member)
            if abs(gap - delta) >= abs(gap):
                break
            members.remove(member)
            members.append(best)
            spare.remove(best)
            spare.append(member)
            total += delta
        chosen[c] = members
        taken.update(members)

    ms = {c: float(np.mean([succ(p) for p in chosen[c]])) for c in CELLS}
    ma = {c: float(np.mean([stats[p].admission for p in chosen[c]])) for c in CELLS}
    mm = {c: float(np.mean([stats[p].mixedness for p in chosen[c]])) for c in CELLS}
    contrast = float(np.mean([ma["HH"], ma["LH"]]) - np.mean([ma["HL"], ma["LL"]]))
    return CellSelection(
        cells={c: sorted(chosen[c]) for c in CELLS},
        mean_success=ms,
        mean_admission=ma,
        mean_mixedness=mm,
        success_spread=max(ms.values()) - min(ms.values()),
        admission_contrast=contrast,
        target_success=target,
    )


def standardized_difference(p1: float, p2: float) -> float:
    """Standardized mean difference for two binary success rates."""
    denom = math.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / 2)
    return 0.0 if denom == 0 else abs(p1 - p2) / denom


@dataclass
class ConfirmationReport:
    success: dict[str, float]
    admission: dict[str, float]
    success_spread: float
    max_standardized_difference: float
    admission_contrast: float
    passed: bool
    reasons: list[str]


def stage_d_confirmation(
    cells: Mapping[str, Sequence[str]],
    fresh: Mapping[str, ProbeStage],
    *,
    max_success_spread: float = 0.03,
    max_std_diff: float = 0.10,
    min_admission_contrast: float = 0.15,
) -> ConfirmationReport:
    """Fresh untouched probe: success spread, pairwise standardized differences and the admission contrast."""
    succ = {c: float(np.mean([r for p in cells[c] for r in fresh[p].rewards])) for c in CELLS}
    adm = {c: float(np.mean([0.0 if cap else 1.0 for p in cells[c] for cap in fresh[p].capped])) for c in CELLS}
    spread = max(succ.values()) - min(succ.values())
    smd = max(standardized_difference(succ[a], succ[b]) for a in CELLS for b in CELLS if a < b)
    contrast = float(np.mean([adm["HH"], adm["LH"]]) - np.mean([adm["HL"], adm["LL"]]))
    reasons = []
    if spread > max_success_spread:
        reasons.append(f"success spread {spread:.4f} > {max_success_spread}")
    if smd > max_std_diff:
        reasons.append(f"max standardized difference {smd:.3f} > {max_std_diff}")
    if contrast < min_admission_contrast:
        reasons.append(f"admission contrast {contrast:.3f} < {min_admission_contrast}")
    return ConfirmationReport(succ, adm, spread, smd, contrast, not reasons, reasons)


def load_stages(records: Iterable[Mapping], *, reward_key: str = "reward", stage_key: str = "stage") -> dict[str, dict[str, ProbeStage]]:
    """Build {stage: {prompt_id: ProbeStage}} from flat probe rows with task_id, stage, reward and truncated fields."""
    tmp: dict[str, dict[str, tuple[list[float], list[bool]]]] = {}
    for rec in records:
        st = tmp.setdefault(str(rec[stage_key]), {})
        r, c = st.setdefault(str(rec["task_id"]), ([], []))
        r.append(float(rec[reward_key]))
        c.append(bool(rec.get("truncated", False)))
    return {s: {p: ProbeStage(tuple(r), tuple(c)) for p, (r, c) in d.items()} for s, d in tmp.items()}
