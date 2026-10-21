"""TLDR: Certify V4-A1 top-64 receipts and freeze tie-inclusive trainer supports."""
import torch

TEMPERATURE = .6
TOP_K = 20
TOP_P = .95


class ReconstructionBlocked(ValueError):
    """The generator receipt cannot determine its exact filtered distribution."""


def native_support(logits, *, temperature=TEMPERATURE, k=TOP_K, p=TOP_P):
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


def support(logits, *, temperature=TEMPERATURE, k=TOP_K, p=TOP_P):
    """Trainer support includes the entire equal-logit group crossing the nucleus boundary."""
    native = native_support(logits, temperature=temperature, k=k, p=p)
    with torch.no_grad():
        scaled = logits.detach().float() / temperature
        boundary = scaled.masked_fill(~native, float('inf')).amin(-1, keepdim=True)
        return scaled >= boundary


def certificate(token_ids, raw_logprobs, sampled_token, *, vocab_size):
    """Certify an actual top-64 list, excluding any extra sampled-token entry.

    Complete tiny vocabularies use k=min(20,V). Both cumulative sums adjacent
    to the removal boundary must be farther than 1e-5 from .05: otherwise a
    float32 rounding change can move that boundary. Ties away from it are safe.
    """
    ids = torch.as_tensor(token_ids, dtype=torch.long)
    raw = torch.as_tensor(raw_logprobs, dtype=torch.float32)
    if (type(vocab_size) is not int or vocab_size < 1 or not 0 <= sampled_token < vocab_size or ids.ndim != 1 or raw.shape != ids.shape
            or len(ids) != min(64, vocab_size) or len(set(ids.tolist())) != len(ids)
            or not ((ids >= 0) & (ids < vocab_size)).all() or not torch.isfinite(raw).all()):
        raise ReconstructionBlocked('invalid or incomplete top-64 receipt')
    order = raw.argsort(descending=True); raw = raw[order]; ids = ids[order]
    k = min(TOP_K, vocab_size)
    complete = vocab_size <= 64 or bool(raw[63] < raw[k-1])
    result = {'top_k_certified': complete, 'nucleus_certified': False,
              'certified': False, 'support_size': None, 'generator_support': None,
              'generator_logp': None, 'reason': 'v64_not_strictly_below_v20'}
    if not complete:
        return result
    chosen = raw >= raw[k-1]
    values, order = raw[chosen].sort(descending=False)
    selected = ids[chosen][order]
    scaled = values / TEMPERATURE
    tail = scaled.softmax(-1).cumsum(-1)
    threshold = 1 - torch.tensor(TOP_P, dtype=torch.float32)
    removed = tail <= threshold; removed[-1] = False
    nremoved = int(removed.sum())
    split_tie = (0 < nremoved < len(values) and bool(values[nremoved-1] == values[nremoved]))
    adjacent = tail[max(0, nremoved-1):min(len(tail), nremoved+1)]
    near = bool(((adjacent - .05).abs() <= 1e-5).any())
    result['reason'] = 'split_boundary_tie' if split_tie else 'boundary_margin' if near else None
    if split_tie or near:
        return result
    kept = selected[~removed]
    if sampled_token not in kept.tolist():
        raise ReconstructionBlocked('sampled token outside certified generator support')
    lp = scaled[~removed].log_softmax(-1)
    result.update(nucleus_certified=True, certified=True, support_size=len(kept),
                  generator_support=kept.tolist(),
                  generator_logp=float(lp[(kept == sampled_token).nonzero()[0, 0]]))
    return result


def reconstruct(token_ids, raw_logprobs, sampled_token, *, vocab_size, complete_topk=False):
    """Only a V4-A1 certificate admits reconstruction; caller assertions are not evidence."""
    result = certificate(token_ids, raw_logprobs, sampled_token, vocab_size=vocab_size)
    if not result['certified']:
        raise ReconstructionBlocked(result['reason'])
    return result['generator_support'], result['generator_logp']


def freeze_old(logits, tokens):
    keep = support(logits)
    logp, discarded = filtered_logprobs(logits, keep, tokens)
    return {'support': keep.detach(), 'prev_logprobs': logp.detach(),
            'discarded_mass': discarded.detach()}
