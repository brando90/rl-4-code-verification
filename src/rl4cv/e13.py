"""Validate Experiment 13 control receipts without changing the frozen strict reward."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable, Mapping

from rl4cv.rewards import ScoredResponse, reward_kernel_binary


def _count(name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def _unit(name: str, value: object) -> None:
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{name} must be a finite number in [0, 1]")


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class PartialCredit:
    """Strict evidence and experimental dense diagnostics are distinct channels."""

    extracted: bool
    compiles: bool
    n_examples: int
    theorem_count: int
    proved_count: int
    vacuous_count: int
    declarations_ok: float
    implementation_and_examples_ok: bool
    proved_fraction: float
    truncated: bool = False

    def __post_init__(self) -> None:
        for name in ("extracted", "compiles", "implementation_and_examples_ok", "truncated"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be a boolean")
        for name in ("n_examples", "theorem_count", "proved_count", "vacuous_count"):
            _count(name, getattr(self, name))
        if self.proved_count > self.theorem_count or self.vacuous_count > self.theorem_count:
            raise ValueError("theorem counts inconsistent")
        _unit("declarations_ok", self.declarations_ok)
        _unit("proved_fraction", self.proved_fraction)
        # proved_fraction is a NEW diagnostic on failed files; the official scorer
        # zeroes its proof channel on compile failure. Do not conflate those counts.
        if self.compiles:
            expected = self.proved_count / self.theorem_count if self.theorem_count else 0.0
            if self.proved_fraction != expected:
                raise ValueError("compiled proof fraction disagrees with official counts")

    @property
    def strict(self) -> float:
        """Use the existing scorer semantics, including valid cap completions."""
        return reward_kernel_binary(ScoredResponse(
            extracted=self.extracted, compiles=self.compiles, n_examples=self.n_examples,
            n_theorems_stated=self.theorem_count, n_theorems_proved=self.proved_count,
            vacuous_theorems=self.vacuous_count, truncated=self.truncated,
        ))

    def factored_reward(self) -> float:
        """Fixed prospective B diagnostic; structural guards do not prove coverage."""
        if not self.extracted or self.vacuous_count or self.theorem_count == 0 or self.n_examples == 0:
            return 0.0
        if self.strict:
            return 1.0
        components = (self.declarations_ok, float(self.implementation_and_examples_ok), self.proved_fraction)
        return math.prod(max(0.01, v) for v in components) ** (1.0 / 3.0)


def _index_manifest(manifest: Iterable[Mapping[str, object]]) -> dict[str, dict]:
    indexed = {}
    for entry in manifest:
        entry = dict(entry)
        cid = entry.get("cell_id")
        if not isinstance(cid, str) or not cid or cid in indexed:
            raise ValueError("missing or duplicate manifest cell_id")
        if entry.get("split") not in {"train", "validation"}:
            raise ValueError("test/unknown split is sealed from this control harness")
        for name in ("task_id", "response_sha256"):
            if not isinstance(entry.get(name), str) or not entry[name]:
                raise ValueError(f"manifest lacks {name}")
        digest = entry["response_sha256"]
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("invalid response_sha256")
        _unit("kernel_binary", entry.get("kernel_binary"))
        if entry["kernel_binary"] not in (0, 1):
            raise ValueError("manifest strict value must be binary")
        indexed[cid] = entry
    if not indexed:
        raise ValueError("empty manifest cannot pass reproduction")
    return indexed


def verify_control_rows(rows: Iterable[Mapping[str, object]], manifest: Iterable[Mapping[str, object]]) -> dict[str, object]:
    """Require exact identities, source hashes, split and independent strict labels."""
    expected = _index_manifest(manifest)
    rows = [dict(r) for r in rows]
    seen = set()
    rewards = []
    for row in rows:
        cid = row.get("cell_id")
        if not isinstance(cid, str) or cid not in expected or cid in seen:
            raise ValueError("unexpected or duplicate control cell_id")
        seen.add(cid)
        source = expected[cid]
        for key in ("task_id", "split", "response_sha256"):
            if row.get(key) != source[key]:
                raise ValueError(f"source mismatch for {cid}: {key}")
        if row.get("status") != "measured":
            raise ValueError(f"unmeasured control: {cid}")
        try:
            pc = PartialCredit(**{key: row[key] for key in PartialCredit.__dataclass_fields__})
        except KeyError as exc:
            raise ValueError(f"missing control evidence: {exc}") from exc
        if pc.strict != source["kernel_binary"]:
            raise ValueError(f"strict mismatch for {cid}")
        rewards.append(pc.factored_reward())
    if seen != set(expected):
        raise ValueError(f"missing {len(set(expected) - seen)} control cells")
    return {"cells": len(rows), "manifest_sha256": _digest(sorted(expected.values(), key=lambda x: x["cell_id"])),
            "rows_sha256": _digest(sorted(rows, key=lambda x: x["cell_id"])),
            "dense_min": min(rewards), "dense_max": max(rewards)}


def canonical_control_report(rows: Iterable[Mapping[str, object]], manifest: Iterable[Mapping[str, object]]) -> str:
    """Serialize a verified receipt without treating a receipt as a Lean test."""
    return json.dumps(verify_control_rows(rows, manifest), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"


def placebo_reward(distribution: tuple[float, ...], *, seed: int, update: int, group: int, slot: int) -> float:
    """Independent reproducible P draw; no response or task enters the random stream."""
    if not distribution:
        raise ValueError("empty placebo distribution")
    for v in distribution:
        _unit("placebo value", v)
    for name, v in (("seed", seed), ("update", update), ("group", group), ("slot", slot)):
        _count(name, v)
    # Rejection sampling avoids modulo bias; a distinct domain separates prompt RNG.
    upper = (1 << 256) - ((1 << 256) % len(distribution))
    attempt = 0
    while True:
        n = int(_digest(["e13-placebo-v1", seed, update, group, slot, attempt]), 16)
        if n < upper:
            return float(distribution[n % len(distribution)])
        attempt += 1
