"""GINC-style toy environment generator and exact verifier for experiment 16 (CPU, numpy only).

A concept is a small hidden Markov model (HMM) over V emission symbols, as in GINC (Xie et al.
2021, "An Explanation of In-context Learning as Implicit Bayesian Inference"). A prompt is a
prefix x_1..x_l sampled from one concept; the task is to emit the next symbol. The verifier is
exact: the reward is 1 when the emitted symbol equals the Bayes-optimal next symbol
argmax_v p(x_{l+1} = v | x_{1:l}, concept), computed with the forward algorithm, and 0 otherwise.

An environment is a prompt distribution set by four knobs:
    S           hidden states per concept
    sharpness   emission sharpness (higher = lower emission entropy)
    n_concepts  how many concepts the environment mixes (the policy must infer which one)
    length      prefix length l (longer = more evidence about the concept)

This is a minimal re-implementation: brando90/beyond-scale-language-data-diversity has the
original GINC generator (src/ginc, hmmlearn + Hugging Face tokenizers), which is heavier than
this CPU pilot needs. Deterministic slot/value emissions are replaced by a sharpness knob so
emission entropy can be varied.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

V = 16  # emission symbols 0..V-1
BOS = V  # beginning-of-sequence token
VOCAB = V + 1
TRANS_SHARPNESS = 3.0


def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


@dataclass(frozen=True)
class Concept:
    S: int
    sharpness: float
    seed: int
    pi: np.ndarray
    T: np.ndarray  # S x S transitions
    B: np.ndarray  # S x V emissions


def make_concept(S: int, sharpness: float, seed: int) -> Concept:
    rng = np.random.default_rng(seed)
    pi = np.full(S, 1.0 / S)
    T = _softmax(rng.standard_normal((S, S)) * TRANS_SHARPNESS)
    B = _softmax(rng.standard_normal((S, V)) * sharpness)
    return Concept(S, sharpness, seed, pi, T, B)


def concept_bank(S: int, sharpness: float, n: int, family_seed: int) -> list[Concept]:
    """n concepts for one (S, sharpness) setting; family_seed separates pretraining and held-out banks."""
    base = 1_000_003 * family_seed + 10_007 * S + int(100 * sharpness)
    return [make_concept(S, sharpness, base + i) for i in range(n)]


def sample_sequences(c: Concept, n: int, length: int, rng: np.random.Generator) -> np.ndarray:
    """n sequences of `length` emissions from concept c (vectorized over n)."""
    h = rng.choice(c.S, size=n, p=c.pi)
    out = np.empty((n, length), dtype=np.int64)
    cT = np.cumsum(c.T, axis=1)
    cB = np.cumsum(c.B, axis=1)
    for t in range(length):
        u = rng.random(n)
        out[:, t] = np.minimum((u[:, None] > cB[h]).sum(1), V - 1)
        u = rng.random(n)
        h = np.minimum((u[:, None] > cT[h]).sum(1), c.S - 1)
    return out


def next_symbol_dist(c: Concept, x: np.ndarray) -> np.ndarray:
    """p(x_{l+1} | x_{1:l}, c) for a batch of prefixes x (n x l), by the scaled forward algorithm."""
    alpha = c.pi[None, :] * c.B[:, x[:, 0]].T
    alpha /= alpha.sum(1, keepdims=True)
    for t in range(1, x.shape[1]):
        alpha = (alpha @ c.T) * c.B[:, x[:, t]].T
        alpha /= alpha.sum(1, keepdims=True)
    return (alpha @ c.T) @ c.B


@dataclass(frozen=True)
class EnvSpec:
    name: str
    S: int
    sharpness: float
    n_concepts: int
    length: int
    family_seed: int = 1  # 1 = the bank the start policies were pretrained on; 2 = held-out concepts

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PromptSet:
    x: np.ndarray  # n x l prefixes
    y: np.ndarray  # n Bayes-optimal next symbols
    bayes_acc: np.ndarray  # n, probability the Bayes answer is the realized next symbol (diagnostic)
    concept_idx: np.ndarray


def make_prompts(spec: EnvSpec, n: int, seed: int) -> PromptSet:
    concepts = concept_bank(spec.S, spec.sharpness, spec.n_concepts, spec.family_seed)
    rng = np.random.default_rng(seed)
    which = rng.integers(0, len(concepts), size=n)
    xs, ys, ba = np.empty((n, spec.length), dtype=np.int64), np.empty(n, dtype=np.int64), np.empty(n)
    for k, c in enumerate(concepts):
        idx = np.where(which == k)[0]
        if idx.size == 0:
            continue
        x = sample_sequences(c, idx.size, spec.length, rng)
        p = next_symbol_dist(c, x)
        xs[idx], ys[idx], ba[idx] = x, p.argmax(1), p.max(1)
    return PromptSet(xs, ys, ba, which)


def pretraining_docs(n: int, length: int, seed: int, settings: list[tuple[int, float]], per_setting: int) -> np.ndarray:
    """Documents from the pretraining bank (family_seed 1): every (S, sharpness) setting, `per_setting` concepts each."""
    rng = np.random.default_rng(seed)
    concepts = [c for S, sh in settings for c in concept_bank(S, sh, per_setting, 1)]
    which = rng.integers(0, len(concepts), size=n)
    docs = np.empty((n, length), dtype=np.int64)
    for k, c in enumerate(concepts):
        idx = np.where(which == k)[0]
        if idx.size:
            docs[idx] = sample_sequences(c, idx.size, length, rng)
    return docs
