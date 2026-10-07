"""SCS4C, the smooth conjunctive score for code: a patch-usable gate times the geometric mean of gold-referenced behaviour factors.

Per artifact (one patch for one task):

    SCS4C = G * (T_fix * T_keep [* D_gold]) ** (1 / k)

* ``G`` is 1 when a nonempty patch applied (phase B adds installs/imports); otherwise SCS4C = 0 and
  the factors are recorded as not run (``None``), never as invented test failures.
* ``T_fix`` is the fraction of the gold FAIL_TO_PASS tests that pass and ``T_keep`` the fraction of
  the gold PASS_TO_PASS tests that pass. An empty gold list is vacuously 1.0 (nothing to break).
* ``D_gold`` (phase B) is the fraction of frozen generated inputs on which the patch behaves like
  the gold patch. Phase A ("SCS4C-T") uses only the two test factors.

A system's score is the geometric mean of its gated factor means over a common measured cohort,
as for VeriBench's SCS4CV/SCSC (decision D-009); the mean of per-artifact scores is a separately
labelled diagnostic. Experiment 07 defines and validates the score.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

TEST_FACTORS = ("t_fix", "t_keep")
FULL_FACTORS = ("t_fix", "t_keep", "d_gold")


@dataclass(frozen=True)
class Cell:
    """One system's artifact for one task. ``gate is None`` marks an unmeasured cell (infrastructure gap)."""

    instance_id: str
    gate: int | None
    t_fix: float | None
    t_keep: float | None
    resolved: bool | None
    d_gold: float | None = None
    unmeasured_reason: str | None = None

    @property
    def measured(self) -> bool:
        return self.gate is not None

    def gated(self, factor: str) -> float | None:
        """Factor value with the gate applied: 0.0 when the patch was unusable, ``None`` when unmeasured."""
        if self.gate is None:
            return None
        return 0.0 if self.gate == 0 else getattr(self, factor)


def fraction_passed(passed: Iterable[str], gold: Sequence[str]) -> float:
    """Fraction of the gold test identifiers found among ``passed``; an empty gold list is vacuously 1.0."""
    if not gold:
        return 1.0
    ok = set(passed)
    return sum(test in ok for test in gold) / len(gold)


def _report_tests(status: Mapping, group: str) -> tuple[list[str], list[str]] | None:
    """Distinguish an explicitly empty test list from absent or malformed test evidence."""
    entry = status.get(group)
    if not isinstance(entry, Mapping):
        return None
    ok, bad = entry.get("success"), entry.get("failure")
    if not all(isinstance(v, list) and all(isinstance(t, str) for t in v) for v in (ok, bad)):
        return None
    if len(set(ok + bad)) != len(ok + bad):
        return None
    return ok, bad


def cell_from_report(
    instance_id: str,
    report: Mapping | None,
    f2p_gold: Sequence[str] | None = None,
    p2p_gold: Sequence[str] | None = None,
    *,
    has_patch: bool,
) -> Cell:
    """Build a cell from one official SWE-bench ``report.json`` entry.

    Denominators are the given gold lists, or, when ``None``, the report's own success + failure
    lists (the tests the official harness used to decide ``resolved``). No patch at all is a
    genuine zero; a patch with no report is unmeasured; a patch that did not apply scores 0 with
    its test factors left as not run.
    """
    if not has_patch:
        return Cell(instance_id, 0, None, None, False)
    if report is None:
        return Cell(instance_id, None, None, None, None)
    if not isinstance(report, Mapping):
        return Cell(instance_id, None, None, None, None)
    resolved = report.get("resolved")
    unmeasured = Cell(instance_id, None, None, None, resolved if isinstance(resolved, bool) else None)
    gate_flags = (report.get("patch_exists"), report.get("patch_is_None"), report.get("patch_successfully_applied"))
    if gate_flags[0] is False or gate_flags[1] is True or gate_flags[2] is False:
        return Cell(instance_id, 0, None, None, resolved if isinstance(resolved, bool) else False)
    if gate_flags != (True, False, True) or not all(isinstance(v, bool) for v in gate_flags):
        return unmeasured
    status = report.get("tests_status")
    if not isinstance(status, Mapping) or not isinstance(resolved, bool):
        return unmeasured
    f2p, p2p = _report_tests(status, "FAIL_TO_PASS"), _report_tests(status, "PASS_TO_PASS")
    if f2p is None or p2p is None:
        return unmeasured
    (f2p_ok, f2p_bad), (p2p_ok, p2p_bad) = f2p, p2p
    t_fix = fraction_passed(f2p_ok, f2p_ok + f2p_bad if f2p_gold is None else f2p_gold)
    t_keep = fraction_passed(p2p_ok, p2p_ok + p2p_bad if p2p_gold is None else p2p_gold)
    return Cell(instance_id, 1, t_fix, t_keep, resolved)


def geometric_mean(values: Sequence[float]) -> float:
    """Geometric mean of values in [0, 1]; any exact zero gives 0 (no clamping before a logarithm)."""
    if not len(values) or any(not math.isfinite(v) or not 0 <= v <= 1 for v in values):
        raise ValueError("geometric_mean requires nonempty finite factors in [0, 1]")
    if any(v == 0 for v in values):
        return 0.0
    return math.exp(sum(math.log(v) for v in values) / len(values))


def cell_score(cell: Cell, factors: Sequence[str] = TEST_FACTORS) -> float | None:
    """Per-artifact SCS4C: 0 when the gate fails, ``None`` when unmeasured or a required factor is missing."""
    if cell.gate is None:
        return None
    if cell.gate == 0:
        return 0.0
    values = [getattr(cell, f) for f in factors]
    if any(v is None or not math.isfinite(v) for v in values):
        return None
    return geometric_mean(values)


def system_summary(cells: Sequence[Cell], factors: Sequence[str] = TEST_FACTORS) -> dict:
    """System-level SCS4C (geometric mean of gated factor means) and pass@1 over the measured cohort.

    Returns ``None`` scores for an empty cohort. ``pass1_declared`` uses known official resolutions
    over the declared denominator; unknown resolutions count unresolved only for that diagnostic.
    """
    cohort = [c for c in cells if c.measured and c.resolved is not None and cell_score(c, factors) is not None]
    declared_pass1 = sum(c.resolved is True for c in cells) / len(cells) if cells else None
    out = {"declared": len(cells), "measured": len(cohort), "unmeasured": len(cells) - len(cohort),
           "pass1_declared": declared_pass1}
    if not cohort:
        return out | {"scs4c": None, "per_task_mean": None, "pass1": None, "factor_means": {}}
    means = {f: float(np.mean([c.gated(f) for c in cohort])) for f in factors}
    return out | {
        "scs4c": geometric_mean(list(means.values())),
        "per_task_mean": float(np.mean([cell_score(c, factors) for c in cohort])),
        "pass1": float(np.mean([bool(c.resolved) for c in cohort])),
        "factor_means": means,
    }


def _ranks(x: np.ndarray) -> np.ndarray:
    """Ranks with ties given their average rank (1-based)."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    sorted_x = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sorted_x[j + 1] == sorted_x[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def _finite_pairs(x: Sequence[float], y: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    """Keep the same finite pairs for every correlation; reject mismatched vector shapes."""
    a, b = np.asarray(x, float), np.asarray(y, float)
    if a.ndim != 1 or b.ndim != 1 or a.shape != b.shape:
        raise ValueError("correlations require equal-length one-dimensional inputs")
    keep = np.isfinite(a) & np.isfinite(b)
    return a[keep], b[keep]


def pearson(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Pearson correlation; ``None`` when either input is constant or shorter than 3."""
    a, b = _finite_pairs(x, y)
    if len(a) < 3 or np.all(a == a[0]) or np.all(b == b[0]) or a.std() == 0 or b.std() == 0:
        return None
    value = float(np.corrcoef(a, b)[0, 1])
    return value if math.isfinite(value) else None


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Spearman rank correlation (Pearson on average-tie ranks)."""
    a, b = _finite_pairs(x, y)
    return pearson(_ranks(a), _ranks(b))


def kendall_tau_b(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Kendall tau-b, which corrects for ties in either variable."""
    a, b = _finite_pairs(x, y)
    if len(a) < 3:
        return None
    da = np.sign(a[:, None] - a[None, :])
    db = np.sign(b[:, None] - b[None, :])
    iu = np.triu_indices(len(a), 1)
    sa, sb = da[iu], db[iu]
    n0 = len(sa)
    ties_a, ties_b = np.sum(sa == 0), np.sum(sb == 0)
    denom = math.sqrt((n0 - ties_a) * (n0 - ties_b))
    return None if denom == 0 else float(np.sum(sa * sb) / denom)
