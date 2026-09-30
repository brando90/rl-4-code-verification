"""Contamination screens between a training pool and protected corpora (VeriBench, held-out panels).

Two screens, both from the paper's Appendix A:
    exact    normalized-text SHA-256 overlap (remove every hit)
    near     maximum word-5-gram Jaccard similarity against the protected corpus (flag >= 0.7,
             report held-out results with and without flagged items)

Normalization lowercases, drops comments and collapses whitespace, so formatting-only copies still collide.
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping

_PY_COMMENT = re.compile(r"#[^\n]*")
_LEAN_LINE_COMMENT = re.compile(r"--[^\n]*")
_LEAN_BLOCK_COMMENT = re.compile(r"/-.*?-/", re.S)
_WORD = re.compile(r"[A-Za-z0-9_]+")


def normalize(text: str) -> str:
    t = _LEAN_BLOCK_COMMENT.sub(" ", text)
    t = _LEAN_LINE_COMMENT.sub(" ", t)
    t = _PY_COMMENT.sub(" ", t)
    return " ".join(t.lower().split())


def norm_hash(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def shingles(text: str, n: int = 5) -> frozenset[tuple[str, ...]]:
    words = _WORD.findall(normalize(text))
    if len(words) < n:
        return frozenset([tuple(words)]) if words else frozenset()
    return frozenset(tuple(words[i : i + n]) for i in range(len(words) - n + 1))


def jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(frozen=True)
class ScreenHit:
    item_id: str
    exact_match: str | None
    max_jaccard: float
    nearest: str | None


def screen(pool: Mapping[str, str], protected: Mapping[str, str], *, n: int = 5, threshold: float = 0.7) -> dict:
    """Screen every pool item against every protected item; returns hits and summary counts.

    An inverted index over shingles keeps this near-linear: only protected items sharing at least
    one shingle with a pool item are compared.
    """
    prot_hash: dict[str, str] = {}
    for pid, text in protected.items():
        prot_hash.setdefault(norm_hash(text), pid)
    prot_sh = {pid: shingles(text, n) for pid, text in protected.items()}
    index: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for pid, sh in prot_sh.items():
        for s in sh:
            index[s].append(pid)
    hits = []
    for iid, text in pool.items():
        sh = shingles(text, n)
        cands = {pid for s in sh for pid in index.get(s, ())}
        best, best_id = 0.0, None
        for pid in cands:
            j = jaccard(sh, prot_sh[pid])
            if j > best:
                best, best_id = j, pid
        hits.append(ScreenHit(iid, prot_hash.get(norm_hash(text)), best, best_id))
    exact = [h for h in hits if h.exact_match is not None]
    near = [h for h in hits if h.exact_match is None and h.max_jaccard >= threshold]
    return {
        "n_pool": len(pool),
        "n_protected": len(protected),
        "n_exact": len(exact),
        "n_near": len(near),
        "threshold": threshold,
        "shingle_n": n,
        "exact": [h.__dict__ for h in exact],
        "near": [h.__dict__ for h in near],
        "clean_ids": sorted(h.item_id for h in hits if h.exact_match is None and h.max_jaccard < threshold),
    }


def load_texts(paths: Iterable[str]) -> dict[str, str]:
    from pathlib import Path

    return {str(p): Path(p).read_text(encoding="utf-8", errors="replace") for p in paths}
