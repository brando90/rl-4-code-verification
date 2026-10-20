"""TLDR: Match vLLM 0.10.0 native filtering and reject underdetermined top-20 reconstruction."""
import torch

TEMPERATURE = .6
TOP_K = 20
TOP_P = .95


class ReconstructionBlocked(ValueError):
    """The generator receipt cannot determine its exact filtered distribution."""


def support(logits, *, temperature=TEMPERATURE, k=TOP_K, p=TOP_P):
    """Mirror installed apply_top_k_top_p, including strict k cutoff and <= tail removal.

    Sorting is deliberately not made stable: the pinned native sampler uses
    torch.sort(descending=False), including its device-dependent tie order.
    Call on the same backend for ties; T1 measures cross-engine support agreement.
    """
    if logits.ndim < 1 or logits.shape[-1] < 1 or not torch.isfinite(logits).all():
        raise ValueError('finite nonempty full-vocabulary logits required')
    if temperature <= 0 or not 0 < p <= 1 or not 1 <= k <= logits.shape[-1]:
        raise ValueError('invalid filter parameters')
    with torch.no_grad():
        scaled = logits.detach().float() / temperature
        values, indices = scaled.sort(dim=-1, descending=False)
        cutoff = values[..., -k:-k+1] if k > 1 else values[..., -1:]
        values = values.masked_fill(values < cutoff, -float('inf'))
        tail = values.softmax(-1).cumsum(-1)
        # float32 p subtraction matches tensor arithmetic in the installed code.
        removed = tail <= 1 - torch.tensor(p, dtype=torch.float32, device=logits.device)
        removed[..., -1] = False
        kept = torch.isfinite(values) & ~removed
        return torch.zeros_like(kept).scatter(-1, indices, kept)


def filtered_logprobs(logits, old_support, tokens):
    """Differentiate only current logits, with old support fixed and no silent off-support fallback."""
    if old_support.shape != logits.shape or old_support.dtype != torch.bool:
        raise ValueError('old support shape or dtype changed')
    if not old_support.any(-1).all() or not torch.isfinite(logits).all():
        raise ValueError('empty support or nonfinite logits')
    if tokens.shape != logits.shape[:-1] or not old_support.gather(-1, tokens[..., None]).all():
        raise ValueError('sampled token outside old trainer support')
    scaled = logits.float() / TEMPERATURE
    selected = scaled.masked_fill(~old_support.detach(), -float('inf'))
    logp = selected.log_softmax(-1).gather(-1, tokens[..., None]).squeeze(-1)
    discarded = 1 - (scaled.softmax(-1) * old_support).sum(-1)
    return logp, discarded.clamp(0, 1)


def reconstruct(token_ids, raw_logprobs, sampled_token, *, vocab_size,
                complete_topk=False):
    """Reconstruct a certified complete top-k list; ordinary top-20 receipts lack that certificate.

    Raw v1 log-probabilities precede temperature. The omitted common log normalizer
    cancels after dividing by .6. A kth tie or a top-p tie whose ordering matters
    cannot be resolved by sorting a truncated list; refuse it. complete_topk must
    come from generator-side full-logit evidence, never the trainer or a guess.
    """
    ids = torch.as_tensor(token_ids, dtype=torch.long)
    raw = torch.as_tensor(raw_logprobs, dtype=torch.float32)
    if ids.ndim != 1 or raw.shape != ids.shape or len(ids) < min(TOP_K, vocab_size):
        raise ReconstructionBlocked('incomplete top-20 receipt')
    if len(set(ids.tolist())) != len(ids) or not ((ids >= 0) & (ids < vocab_size)).all():
        raise ReconstructionBlocked('duplicate or invalid token IDs')
    if not torch.isfinite(raw).all():
        raise ReconstructionBlocked('nonfinite raw log-probability')
    if vocab_size > len(ids) and not complete_topk:
        raise ReconstructionBlocked('top-20 cannot certify absence of omitted kth-logit ties')
    order = raw.argsort(descending=True)
    values = raw[order]
    if len(values) > TOP_K and values[TOP_K] == values[TOP_K-1]:
        raise ReconstructionBlocked('tie-expanded top-k exceeds frozen top-20 contract')
    if vocab_size > len(ids) and len(torch.unique(values)) != len(values):
        raise ReconstructionBlocked('truncated receipt loses full-vocabulary top-p tie ordering')
    # For a complete tiny vocabulary preserve original vocabulary indexing/order.
    if len(ids) == vocab_size:
        full = torch.empty(vocab_size, dtype=torch.float32)
        full[ids] = raw
        keep = support(full, k=min(TOP_K, vocab_size))
        tokens = keep.nonzero().flatten()
        lp = (full / TEMPERATURE).masked_fill(~keep, -float('inf')).log_softmax(-1)
        if not keep[sampled_token]:
            raise ReconstructionBlocked('sampled token outside reconstructed support')
        return tokens.tolist(), float(lp[sampled_token])
    keep = support(values, k=TOP_K)
    selected = ids[order][keep]
    if sampled_token not in selected.tolist():
        raise ReconstructionBlocked('sampled token outside reconstructed support')
    lp = (values[keep] / TEMPERATURE).log_softmax(-1)
    return selected.tolist(), float(lp[(selected == sampled_token).nonzero()[0, 0]])


def freeze_old(logits, tokens):
    keep = support(logits)
    logp, discarded = filtered_logprobs(logits, keep, tokens)
    return {'support': keep.detach(), 'prev_logprobs': logp.detach(),
            'discarded_mass': discarded.detach()}
