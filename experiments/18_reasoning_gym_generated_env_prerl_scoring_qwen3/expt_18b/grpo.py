"""Minimal GRPO on PyTorch + Hugging Face transformers (no TRL/verl/vLLM): on-policy, binary reward, Dr. GRPO advantages.

Pieces are small pure functions (unit-tested on CPU) plus `rollout`, `policy_loss_microbatches` and `MasterAdamW`, which `train.py` drives.
One optimiser step per rollout batch, so the importance ratio is 1 and the clipped objective equals the plain policy gradient.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint


def group_advantages(rewards: torch.Tensor) -> torch.Tensor:
    """rewards [P, G] -> advantages [P, G] = r - group mean (no std normalisation); a constant group gets exactly 0."""
    return rewards - rewards.mean(dim=1, keepdim=True)


def lr_at(step: int, peak: float, warmup: int) -> float:
    """Linear warm-up over `warmup` steps (step 0 -> peak/warmup), then constant. `step` counts from 0."""
    if warmup <= 0:
        return peak
    return peak * min(1.0, (step + 1) / warmup)


def token_logprobs(hidden: torch.Tensor, lm_head: torch.nn.Module, targets: torch.Tensor, chunk: int = 2048) -> torch.Tensor:
    """log p(target | hidden) for [N, H] hidden states, computed in checkpointed chunks so [N, vocab] never exists at once."""

    def _chunk(h: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        logits = lm_head(h).float()
        return -F.cross_entropy(logits, t, reduction="none")

    out = []
    for i in range(0, hidden.shape[0], chunk):
        h, t = hidden[i : i + chunk], targets[i : i + chunk]
        out.append(checkpoint(_chunk, h, t, use_reentrant=False) if torch.is_grad_enabled() and h.requires_grad else _chunk(h, t))
    return torch.cat(out) if out else hidden.new_zeros(0)


def pg_loss(logps: torch.Tensor, adv_per_token: torch.Tensor, total_tokens: int) -> torch.Tensor:
    """Token-level policy-gradient loss, normalised by the whole batch's response-token count (so micro-batches just add up)."""
    return -(adv_per_token * logps).sum() / max(1, total_tokens)


@dataclass
class Rollout:
    prompt_ids: list[int]
    response_ids: list[int]  # up to and including EOS when finished
    finished: bool
    text: str


def _cut_at_eos(ids: list[int], eos_ids: set[int]) -> tuple[list[int], bool]:
    for i, t in enumerate(ids):
        if t in eos_ids:
            return ids[: i + 1], True
    return ids, False


@torch.no_grad()
def rollout(model, tok, prompt_id_lists: list[list[int]], group_size: int, max_new_tokens: int, gen_kw: dict,
            eos_ids: set[int], pad_id: int, device) -> list[list[Rollout]]:
    """Sample `group_size` responses for every prompt with model.generate (left-padded, one batch). Returns [P][G]."""
    model.eval()
    max_len = max(len(p) for p in prompt_id_lists)
    ids = torch.full((len(prompt_id_lists), max_len), pad_id, dtype=torch.long)
    mask = torch.zeros_like(ids)
    for i, p in enumerate(prompt_id_lists):
        ids[i, max_len - len(p) :] = torch.tensor(p)
        mask[i, max_len - len(p) :] = 1
    out = model.generate(input_ids=ids.to(device), attention_mask=mask.to(device), do_sample=True,
                         num_return_sequences=group_size, max_new_tokens=max_new_tokens,
                         eos_token_id=sorted(eos_ids), pad_token_id=pad_id, use_cache=True, **gen_kw)
    out = out[:, max_len:].cpu().tolist()
    groups: list[list[Rollout]] = []
    for pi, p in enumerate(prompt_id_lists):
        g = []
        for k in range(group_size):
            resp, fin = _cut_at_eos(out[pi * group_size + k], eos_ids)
            g.append(Rollout(p, resp, fin, tok.decode(resp, skip_special_tokens=True)))
        groups.append(g)
    return groups


def policy_loss_microbatches(model, rollouts: list[Rollout], advantages: list[float], micro_bs: int, pad_id: int, device):
    """Backward through the policy-gradient loss in micro-batches; returns (loss value, number of response tokens).

    Right-padded sequences prompt+response, hidden states from the transformer body, response positions only go through lm_head.
    Sequences with advantage 0 contribute no gradient and are skipped (they still count in the token normaliser).
    """
    model.train()
    total_tokens = sum(len(r.response_ids) for r in rollouts)
    idx = [i for i, a in enumerate(advantages) if a != 0.0 and len(rollouts[i].response_ids) > 0]
    # length-sorted micro-batches waste less padding
    idx.sort(key=lambda i: len(rollouts[i].prompt_ids) + len(rollouts[i].response_ids))
    loss_val = 0.0
    for s in range(0, len(idx), micro_bs):
        batch = idx[s : s + micro_bs]
        lens = [len(rollouts[i].prompt_ids) + len(rollouts[i].response_ids) for i in batch]
        L = max(lens)
        ids = torch.full((len(batch), L), pad_id, dtype=torch.long)
        att = torch.zeros_like(ids)
        sel = torch.zeros(len(batch), L, dtype=torch.bool)  # positions whose NEXT token is a response token
        tgt = []
        adv_tok = []
        for b, i in enumerate(batch):
            r = rollouts[i]
            full = r.prompt_ids + r.response_ids
            ids[b, : len(full)] = torch.tensor(full)
            att[b, : len(full)] = 1
            sel[b, len(r.prompt_ids) - 1 : len(full) - 1] = True
            tgt.extend(r.response_ids)
            adv_tok.extend([advantages[i]] * len(r.response_ids))
        hidden = model.model(input_ids=ids.to(device), attention_mask=att.to(device), use_cache=False).last_hidden_state
        h = hidden[sel.to(device)]
        logps = token_logprobs(h, model.lm_head, torch.tensor(tgt, device=device))
        loss = pg_loss(logps, torch.tensor(adv_tok, device=device, dtype=logps.dtype), total_tokens)
        loss.backward()
        loss_val += float(loss.detach())
    return loss_val, total_tokens


class MasterAdamW:
    """AdamW on fp32 master copies of low-precision parameters (bf16 weights cannot hold a 1e-6 update).

    Parameters already in fp32 are optimised in place. After `step()` the low-precision parameters are overwritten from the masters.
    """

    def __init__(self, params, lr: float, betas, eps: float, weight_decay: float):
        self.params = [p for p in params if p.requires_grad]
        self.master = [p.detach().float().clone() if p.dtype != torch.float32 else p for p in self.params]
        self.opt = torch.optim.AdamW(self.master, lr=lr, betas=betas, eps=eps, weight_decay=weight_decay)

    def set_lr(self, lr: float) -> None:
        for g in self.opt.param_groups:
            g["lr"] = lr

    def grad_norm(self) -> float:
        sq = 0.0
        for p in self.params:
            if p.grad is not None:
                sq += float(p.grad.detach().float().pow(2).sum())
        return math.sqrt(sq)

    def step(self, clip: float | None) -> tuple[float, bool]:
        """Clip by global norm, step, copy back. Returns (grad norm, stepped). A non-finite norm skips the step."""
        norm = self.grad_norm()
        if not math.isfinite(norm):
            self.zero_grad()
            return norm, False
        scale = min(1.0, clip / (norm + 1e-6)) if clip else 1.0
        for p, m in zip(self.params, self.master):
            if m is not p:
                m.grad = (p.grad.float() * scale) if p.grad is not None else None
            elif p.grad is not None:
                p.grad.mul_(scale)
        self.opt.step()
        for p, m in zip(self.params, self.master):
            if m is not p:
                p.data.copy_(m.data)
        self.zero_grad()
        return norm, True

    def zero_grad(self) -> None:
        for p, m in zip(self.params, self.master):
            p.grad = None
            if m is not p:
                m.grad = None
