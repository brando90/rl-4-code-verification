"""Reward channels for Lean code-verification rollouts, computed from VeriBench-style per-response scores.

A reward channel maps one scored response to a scalar. The same prompts measured under
different channels give different rho and H, which is how this project tests whether the
environment-utility law carries over from binary math rewards to kernel-checked and
judge-scored rewards. Channels never loosen VeriBench's scorer: a theorem counts as proved
only when its kernel axioms stay within {propext, Classical.choice, Quot.sound}.

Factor names follow VeriBench:
    IC_tests   1 when the file typechecks and states at least one `example`, else 0
    IC_proofs  fraction of stated theorems the kernel accepted with only the allowed axioms
    FSC        formal specification coverage: judged directional coverage of the reference
               theorem statements by the response's theorem statements, normalized to [0, 1]
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Mapping


@dataclass(frozen=True)
class ScoredResponse:
    """Per-response scores produced by the VeriBench scorer (and, for FSC, the judge)."""

    extracted: bool
    compiles: bool
    n_examples: int
    n_theorems_stated: int
    n_theorems_proved: int
    fsc: float | None = None
    vacuous_theorems: int = 0
    truncated: bool = False

    @property
    def ic_tests(self) -> float:
        return 1.0 if (self.extracted and self.compiles and self.n_examples >= 1) else 0.0

    @property
    def ic_proofs(self) -> float:
        if not self.extracted or self.n_theorems_stated == 0:
            return 0.0
        return self.n_theorems_proved / self.n_theorems_stated


def reward_kernel_binary(s: ScoredResponse) -> float:
    """1 only for a fully verified file: typechecks, has an example, every stated theorem proved, none vacuous."""
    ok = (
        s.ic_tests == 1.0
        and s.n_theorems_stated >= 1
        and s.n_theorems_proved == s.n_theorems_stated
        and s.vacuous_theorems == 0
    )
    return 1.0 if ok else 0.0


def reward_proof_fraction(s: ScoredResponse) -> float:
    """IC_tests x IC_proofs, zeroed when any theorem is vacuous (denser than the binary channel)."""
    if s.vacuous_theorems > 0:
        return 0.0
    return s.ic_tests * s.ic_proofs


def reward_fsc(s: ScoredResponse) -> float:
    """Judge-scored formal specification coverage alone; requires a reference specification.

    Diagnostic only: VeriBench's judge scores any non-empty file, compiling or not, and is
    lenient on partial coverage, so an ungated FSC reward pays for Lean-looking text that does
    not typecheck. Use `reward_fsc_compiled` or `reward_scsc` for training.
    """
    if s.fsc is None:
        raise ValueError("FSC reward needs a judged coverage score (the task must have reference specifications)")
    return float(s.fsc) if s.extracted else 0.0


def reward_fsc_compiled(s: ScoredResponse) -> float:
    """FSC paid only when the file typechecks with at least one example (IC_tests = 1) and nothing is vacuous."""
    if s.ic_tests == 0.0 or s.vacuous_theorems > 0:
        return 0.0
    if s.fsc is None:
        raise ValueError("compile-gated FSC reward needs a judged coverage score for every compiling response")
    return float(s.fsc)


def needs_judge(s: ScoredResponse, channel: str) -> bool:
    """Whether a response needs a judge call under a channel; SCSC and gated FSC are 0 without one when IC fails."""
    if channel in ("kernel_binary", "proof_fraction"):
        return False
    if channel == "fsc":
        return s.extracted
    if channel == "fsc_compiled":
        return s.ic_tests == 1.0 and s.vacuous_theorems == 0
    if channel == "scsc":
        return s.ic_tests * s.ic_proofs > 0 and s.vacuous_theorems == 0
    raise KeyError(channel)


def reward_scsc(s: ScoredResponse) -> float:
    """Per-response analogue of VeriBench's aggregate: (IC_tests * IC_proofs * FSC)^(1/3), zeroed if vacuous.

    It is exactly 0 whenever IC_tests * IC_proofs = 0, so the judge is only needed for responses
    that typecheck and prove at least one stated theorem (see `needs_judge`).
    """
    if s.vacuous_theorems > 0:
        return 0.0
    ic = s.ic_tests * s.ic_proofs
    if ic == 0:
        return 0.0
    if s.fsc is None:
        raise ValueError("SCSC-style reward needs a judged coverage score when IC_tests * IC_proofs > 0")
    prod = ic * float(s.fsc)
    return prod ** (1.0 / 3.0) if prod > 0 else 0.0


REWARD_CHANNELS: Mapping[str, Callable[[ScoredResponse], float]] = {
    "kernel_binary": reward_kernel_binary,
    "proof_fraction": reward_proof_fraction,
    "fsc": reward_fsc,
    "fsc_compiled": reward_fsc_compiled,
    "scsc": reward_scsc,
}


# Heuristic screen for vacuous theorem statements. It is deliberately conservative (it only flags
# statements whose conclusion is literally True or a syntactic self-equality); the authoritative
# check should reuse VeriBench's tests/test_reference_specs_nonvacuous.py logic from the pinned checkout.
_SELF_EQ = re.compile(r"^\(?\s*(?P<lhs>[^=]+?)\s*=\s*(?P<rhs>[^=]+?)\s*\)?$")


def conclusion_of(statement: str) -> str:
    """Rough conclusion of a Lean theorem type: the text after the last top-level arrow, binder or comma."""
    body = statement.strip()
    for sep in ("→", "->"):
        if sep in body:
            body = body.rsplit(sep, 1)[1]
    if "," in body and ("∀" in statement or "∃" in statement):
        body = body.rsplit(",", 1)[1]
    return body.strip()


def is_vacuous_statement(statement: str) -> bool:
    concl = conclusion_of(statement)
    if concl in {"True", "(True)"}:
        return True
    m = _SELF_EQ.match(concl)
    return bool(m and m.group("lhs").strip() == m.group("rhs").strip())
