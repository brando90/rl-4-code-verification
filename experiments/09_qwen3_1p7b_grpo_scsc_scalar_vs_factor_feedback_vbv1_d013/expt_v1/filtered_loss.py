"""TLDR: Single-fresh-batch GRPO loss for the frozen experiment09 truncated policy."""
from __future__ import annotations

import torch
from nemo_rl.algorithms.interfaces import LossType
from filtered_policy import selected_logprobs, SupportMismatch

# Prospective numerical tolerances, fixed before the first real optimizer control.
GENERATION_LOGPROB_ATOL = 0.05
CURRENT_LOGPROB_ATOL = 0.005


class FilteredGRPOLoss:
    """Clipped token-level GRPO, beta=0, exactly one step per fresh full batch.

    Both assistant spans receive the terminal trajectory advantage. A policy
    support mismatch or an inconsistent probability calculation blocks the batch.
    No epsilon floors, replacement samples or masked nonfinite arithmetic.
    """
    loss_type = LossType.TOKEN_LEVEL

    def __init__(self, cfg):
        assert cfg["reference_policy_kl_penalty"] == 0
        assert cfg["token_level_loss"]
        assert not cfg["use_importance_sampling_correction"]
        assert not cfg.get("disable_ppo_ratio", False)
        assert not cfg.get("sequence_level_importance_ratios", False)
        assert cfg["ratio_clip_c"] is None
        self.clip_min = cfg["ratio_clip_min"]
        self.clip_max = cfg["ratio_clip_max"]

    def __call__(self, next_token_logits, data, global_valid_seqs,
                 global_valid_toks, vocab_parallel_rank=None,
                 vocab_parallel_group=None, context_parallel_group=None):
        assert vocab_parallel_group is None and context_parallel_group is None
        assert data.get("seq_index") is None
        assert torch.all(data["sample_mask"] == 1), "No outcome-based sample removal"
        mask = data["token_mask"][:, 1:].bool()
        current = selected_logprobs(next_token_logits[:, :-1],
                                   data["input_ids"][:, 1:], mask)[mask]
        old = data["prev_logprobs"][:, 1:][mask].float().detach()
        generation = data["generation_logprobs"][:, 1:][mask].float().detach()
        advantage = data["advantages"][:, 1:][mask].float().detach()
        if not current.numel():
            raise ValueError("No assistant actions in microbatch")
        if not all(torch.isfinite(x).all() for x in (current, old, generation, advantage)):
            raise SupportMismatch("Nonfinite active probability or advantage")
        generation_error = (generation - old).abs().max()
        current_error = (current.detach() - old).abs().max()
        if generation_error > GENERATION_LOGPROB_ATOL:
            raise SupportMismatch(f"Generation/old log q disagreement {generation_error.item()}")
        if current_error > CURRENT_LOGPROB_ATOL:
            raise SupportMismatch(f"Current/old log q disagreement {current_error.item()}")
        ratio = (current - old).exp()
        clipped = ratio.clamp(1 - self.clip_min, 1 + self.clip_max)
        denominator = torch.as_tensor(global_valid_toks, device=current.device)
        if denominator <= 0:
            raise ValueError("Nonpositive global assistant-token denominator")
        loss = torch.maximum(-advantage * ratio, -advantage * clipped).sum() / denominator
        return loss, {
            "num_valid_samples": data["sample_mask"].sum().item(),
            "e09_generation_logprob_max_error": generation_error.item(),
            "e09_current_logprob_max_error": current_error.item(),
            "e09_reference_kl_coefficient": 0.0,
        }
