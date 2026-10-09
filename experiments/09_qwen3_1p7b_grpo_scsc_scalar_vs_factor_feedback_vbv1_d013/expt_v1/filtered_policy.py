"""TLDR: Exact native vLLM 0.10 top-k/top-p support and differentiable action probabilities for experiment09."""
from __future__ import annotations

import torch

TEMPERATURE = 0.6
TOP_K = 20
TOP_P = 0.95


class SupportMismatch(RuntimeError):
    """A generated action is outside the recomputed policy support; block the batch."""


def kept_mask(scaled_logits: torch.Tensor, top_k: int = TOP_K,
              top_p: float = TOP_P) -> torch.Tensor:
    """Match the pinned native filter, including ties and its <= nucleus cutoff.

    Input is already temperature-scaled float32. Support is discrete and detached;
    gradients below follow the resulting piecewise-differentiable distribution.
    """
    if scaled_logits.ndim != 2 or scaled_logits.dtype != torch.float32:
        raise ValueError("expected two-dimensional, temperature-scaled float32 logits")
    if not 1 <= top_k <= scaled_logits.shape[-1] or not 0 < top_p <= 1:
        raise ValueError("invalid top-k/top-p")
    with torch.no_grad():
        if not torch.isfinite(scaled_logits).all():
            raise ValueError("nonfinite model logits")
        ordered, indices = scaled_logits.detach().sort(dim=-1, descending=False)
        # Tensor p uses the same float32 subtraction as vLLM SamplingMetadata.
        p = torch.full((ordered.shape[0], 1), top_p, device=ordered.device,
                       dtype=torch.float32)
        cutoff = ordered[:, -top_k].unsqueeze(1)
        ordered.masked_fill_(ordered < cutoff, -float("inf"))
        cumulative = ordered.softmax(dim=-1).cumsum(dim=-1)
        removed = cumulative <= 1 - p
        removed[:, -1] = False
        ordered.masked_fill_(removed, -float("inf"))
        kept = torch.zeros_like(ordered, dtype=torch.bool)
        kept.scatter_(1, indices, torch.isfinite(ordered))
        return kept


def filtered_logprobs(logits: torch.Tensor, *, already_scaled: bool = False,
                      top_k: int = TOP_K, top_p: float = TOP_P) -> torch.Tensor:
    """Return complete log q; never mutate logits or draw from a random generator."""
    scaled = logits.float() if already_scaled else logits.float() / TEMPERATURE
    mask = kept_mask(scaled, top_k, top_p)
    return scaled.masked_fill(~mask, -float("inf")).log_softmax(dim=-1)


def selected_logprobs(scaled_logits: torch.Tensor, targets: torch.Tensor,
                      action_mask: torch.Tensor, chunk_size: int = 16,
                      require_support: bool = True) -> torch.Tensor:
    """Gather log q only on action positions; neutral finite values elsewhere.

    NeMo workers have already applied temperature exactly once. Finite checks and
    support checks apply before any ratio arithmetic; zero times infinity is unsafe.
    """
    if scaled_logits.shape[:-1] != targets.shape or targets.shape != action_mask.shape:
        raise ValueError("logits/target/action-mask shapes disagree")
    if chunk_size < 1:
        raise ValueError("chunk size must be positive")
    flat_logits = scaled_logits.reshape(-1, scaled_logits.shape[-1])
    flat_targets = targets.reshape(-1).to(scaled_logits.device)
    positions = action_mask.reshape(-1).to(scaled_logits.device).bool().nonzero().flatten()
    result = scaled_logits.new_zeros(flat_targets.shape, dtype=torch.float32)
    chunks = []
    for offset in range(0, positions.numel(), chunk_size):
        index = positions[offset:offset + chunk_size]
        # Determine discrete support without retaining a full-vocabulary backward
        # graph per chunk. Gather just the retained logits for logsumexp.
        with torch.no_grad():
            mask = kept_mask(flat_logits[index].detach())
            supported = mask.gather(1, flat_targets[index, None]).squeeze(1)
            coordinates = mask.nonzero()
            counts = mask.sum(-1)
            starts = counts.cumsum(0) - counts
            columns = torch.arange(len(coordinates), device=mask.device) - starts[coordinates[:, 0]]
            width = int(counts.max())
        if require_support and not supported.all():
            n = int((~supported).sum())
            raise SupportMismatch(f"{n} sampled action(s) outside recomputed support")
        retained = flat_logits[index[coordinates[:, 0]], coordinates[:, 1]]
        padded = retained.new_full((len(index), width), -float("inf"))
        padded = padded.index_put((coordinates[:, 0], columns), retained)
        values = flat_logits[index, flat_targets[index]] - padded.logsumexp(-1)
        values = values.masked_fill(~supported, -float("inf"))
        chunks.append(values)
    if chunks:
        result = result.index_copy(0, positions, torch.cat(chunks))
    return result.reshape(targets.shape)
