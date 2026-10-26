"""Tiny causal transformers (the scale grid N), next-token pretraining, sampling and GRPO for experiment 16."""

from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ginc_toy import BOS, V, VOCAB

MAX_LEN = 40

# (d_model, layers, heads); parameter counts are printed by run_pilot.py
SCALES = {
    "n1": (16, 1, 2),
    "n2": (32, 2, 2),
    "n3": (64, 2, 4),
    "n4": (128, 3, 4),
}


class TinyLM(nn.Module):
    def __init__(self, d: int, layers: int, heads: int):
        super().__init__()
        self.tok = nn.Embedding(VOCAB, d)
        self.pos = nn.Embedding(MAX_LEN, d)
        layer = nn.TransformerEncoderLayer(d, heads, 4 * d, dropout=0.0, batch_first=True, norm_first=True)
        self.body = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, V)  # BOS is never an output

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        L = tokens.shape[1]
        h = self.tok(tokens) + self.pos(torch.arange(L))
        mask = torch.triu(torch.full((L, L), float("-inf")), diagonal=1)
        h = self.body(h, mask=mask, is_causal=True)
        return self.head(self.norm(h))

    def n_params(self) -> int:
        return sum(p.numel() for p in self.parameters())


def with_bos(x: np.ndarray) -> torch.Tensor:
    t = torch.as_tensor(x, dtype=torch.long)
    return torch.cat([torch.full((t.shape[0], 1), BOS, dtype=torch.long), t], 1)


def pretrain(model: TinyLM, docs: np.ndarray, steps: int, batch: int, lr: float, seed: int) -> list[float]:
    g = torch.Generator().manual_seed(seed)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    data = with_bos(docs)
    losses = []
    for step in range(steps):
        idx = torch.randint(0, data.shape[0], (batch,), generator=g)
        seq = data[idx]
        logits = model(seq[:, :-1])
        loss = F.cross_entropy(logits.reshape(-1, V), seq[:, 1:].reshape(-1))
        cur_lr = lr * 0.5 * (1 + math.cos(math.pi * step / steps))
        for pg in opt.param_groups:
            pg["lr"] = cur_lr
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(float(loss.detach()))
    return losses


@torch.no_grad()
def last_logits(model: TinyLM, x: np.ndarray, chunk: int = 4096) -> torch.Tensor:
    out = []
    for i in range(0, x.shape[0], chunk):
        out.append(model(with_bos(x[i : i + chunk]))[:, -1, :])
    return torch.cat(out)


@torch.no_grad()
def greedy_accuracy(model: TinyLM, x: np.ndarray, y: np.ndarray) -> float:
    return float((last_logits(model, x).argmax(1).numpy() == y).mean())


@torch.no_grad()
def sample_groups(model: TinyLM, x: np.ndarray, G: int, gen: torch.Generator) -> np.ndarray:
    """G sampled next symbols per prompt at temperature 1 (n x G)."""
    probs = F.softmax(last_logits(model, x), dim=-1)
    return torch.multinomial(probs, G, replacement=True, generator=gen).numpy()


def grpo(model: TinyLM, x_pool: np.ndarray, y_pool: np.ndarray, steps: int, batch: int, G: int, lr: float, seed: int, eval_fn, eval_at: list[int], kl_coef: float = 0.0, ref: TinyLM | None = None) -> dict[int, float]:
    """Group-relative policy gradient with leave-one-out advantages (paper Eq. 2), no KL, one update per batch.

    Each response is one generated token, so the generated-token budget after s steps is s * batch * G.
    kl_coef > 0 adds kl_coef * KL(pi || ref) on the full next-symbol distribution (exact, one position).
    Returns eval_fn(model) at each step count in eval_at (0 = start).
    """
    gen = torch.Generator().manual_seed(seed)
    rng = np.random.default_rng(seed)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    out = {}
    if 0 in eval_at:
        out[0] = eval_fn(model)
    for step in range(1, steps + 1):
        idx = rng.integers(0, x_pool.shape[0], size=batch)
        x, y = x_pool[idx], y_pool[idx]
        logits = model(with_bos(x))[:, -1, :]
        logp = F.log_softmax(logits, -1)
        with torch.no_grad():
            a = torch.multinomial(logp.exp(), G, replacement=True, generator=gen)  # batch x G
            r = (a == torch.as_tensor(y)[:, None]).float()
            adv = r - (r.sum(1, keepdim=True) - r) / (G - 1)
        loss = -(adv * logp.gather(1, a)).sum() / (batch * G)
        if kl_coef > 0:
            with torch.no_grad():
                ref_logp = F.log_softmax(ref(with_bos(x))[:, -1, :], -1)
            loss = loss + kl_coef * (logp.exp() * (logp - ref_logp)).sum(1).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step in eval_at:
            out[step] = eval_fn(model)
    return out
