"""TLDR: Experiment 20's GRPO objective as pure torch functions (unit-testable on CPU): group-normalized advantages, the clipped surrogate with asymmetric clipping (0.2 below, 0.28 above), the vLLM-to-trainer token-level importance weight truncated at 2.0, token-normalized (DAPO) loss over all completion tokens of an update, and the truncated-support recomputation (temperature, top-k, top-p) used by the smoke test's log-probability mismatch check."""
from __future__ import annotations

import torch

EPS_LOW, EPS_HIGH, IS_CAP = 0.2, 0.28, 2.0


def group_advantages(rewards: torch.Tensor, eps: float = 1e-4) -> torch.Tensor:
    """(groups x G) rewards -> (r - mean_group) / (std_group + eps); a constant group gets zero advantage."""
    mean = rewards.mean(dim=1, keepdim=True)
    std = rewards.std(dim=1, keepdim=True, unbiased=False)
    return (rewards - mean) / (std + eps)


def importance_weights(logp_trainer: torch.Tensor, logp_sampler: torch.Tensor, cap: float = IS_CAP) -> torch.Tensor:
    """Token-level vLLM -> trainer correction exp(logp_trainer - logp_sampler), truncated above at `cap` (no lower clip),
    detached (TRL `vllm_importance_sampling_mode="token_truncate"`)."""
    return torch.exp(logp_trainer.detach() - logp_sampler).clamp(max=cap)


def clipped_surrogate(logp: torch.Tensor, logp_old: torch.Tensor, advantage: torch.Tensor,
                      eps_low: float = EPS_LOW, eps_high: float = EPS_HIGH) -> torch.Tensor:
    """Per-token PPO/GRPO surrogate min(r A, clip(r, 1 - eps_low, 1 + eps_high) A) with r = exp(logp - logp_old)."""
    ratio = torch.exp(logp - logp_old)
    return torch.minimum(ratio * advantage, ratio.clamp(1.0 - eps_low, 1.0 + eps_high) * advantage)


def token_normalized_loss(surrogate: torch.Tensor, weights: torch.Tensor, mask: torch.Tensor, total_tokens: float) -> torch.Tensor:
    """Negative sum of weighted surrogates over this micro-batch's completion tokens divided by the update's total number
    of completion tokens (DAPO token-level normalization, so micro-batch losses add up to the update loss)."""
    return -(surrogate * weights * mask).sum() / total_tokens


def truncated_logprobs(logits: torch.Tensor, token_ids: torch.Tensor, temperature: float, top_k: int, top_p: float) -> dict:
    """Recompute the sampling distribution vLLM used (logits / T, keep the top-k, then the smallest top-p nucleus that
    reaches mass p, renormalize) and return the full-softmax and truncated log-probabilities of the sampled tokens plus
    whether each sampled token lies inside the recomputed support. logits: (N, V); token_ids: (N,)."""
    z = logits.float() / temperature
    full = torch.log_softmax(z, dim=-1)
    logp_full = full.gather(1, token_ids[:, None])[:, 0]
    k = min(top_k, z.shape[1]) if top_k and top_k > 0 else z.shape[1]
    topv, topi = torch.topk(z, k, dim=-1)
    probs = torch.softmax(topv, dim=-1)  # within the top-k
    cum = probs.cumsum(dim=-1)
    # vLLM keeps tokens while the cumulative probability before them is below p (always keeps the first).
    keep = (cum - probs) < top_p
    kept_mass = (probs * keep).sum(dim=-1)
    in_support = (topi == token_ids[:, None]) & keep
    inside = in_support.any(dim=-1)
    p_tok = (probs * in_support).sum(dim=-1)
    logp_trunc = torch.where(inside, torch.log(p_tok.clamp_min(1e-300)) - torch.log(kept_mass), torch.full_like(p_tok, float("-inf")))
    return {"logp_full": logp_full, "logp_truncated": logp_trunc, "in_support": inside}


def mismatch_summary(logp_recomputed: torch.Tensor, logp_sampler: torch.Tensor, in_support: torch.Tensor, tol: float = 0.05) -> dict:
    """Share of tokens with |delta| > tol among in-support tokens, plus the out-of-support count (experiment 09's gate)."""
    delta = (logp_recomputed - logp_sampler).abs()
    ok = in_support & torch.isfinite(delta)
    n = int(ok.sum())
    bad = int((delta[ok] > tol).sum())
    return {"tokens": int(delta.numel()), "in_support": n, "outside_support": int((~in_support).sum()),
            "abs_delta_gt_tol": bad, "share_gt_tol": (bad + int((~in_support).sum())) / max(delta.numel(), 1),
            "mean_abs_delta": float(delta[ok].mean()) if n else float("nan"), "max_abs_delta": float(delta[ok].max()) if n else float("nan")}
