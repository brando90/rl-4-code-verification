"""TLDR: Feed fixed-support temperature-scaled logits through the installed NeMo clipped loss."""
import torch
from nemo_rl.algorithms.loss_functions import ClippedPGLossFn
from worker_hooks import install_on_policy

LOSS = {'reference_policy_kl_penalty': 0., 'ratio_clip_min': .2, 'ratio_clip_max': .28,
        'ratio_clip_c': None, 'use_on_policy_kl_approximation': False,
        'use_importance_sampling_correction': True, 'truncated_importance_sampling_ratio': 2.,
        'token_level_loss': True, 'sequence_level_importance_ratios': False}


class FilteredClippedPGLossFn(ClippedPGLossFn):
    """A serialized v4-owned NeMo LossFunction; no site-packages monkeypatch is installed."""
    def __init__(self, cfg=None):
        cfg = LOSS if cfg is None else cfg
        if cfg != LOSS:
            raise ValueError('v4 loss settings differ from frozen recipe')
        super().__init__(cfg)

    def __call__(self, next_token_logits, data, global_valid_seqs, global_valid_toks,
                 vocab_parallel_rank=None, vocab_parallel_group=None, context_parallel_group=None):
        if vocab_parallel_group is not None or context_parallel_group is not None:
            raise ValueError('v4 admits only single-device unpartitioned logits')
        logits = next_token_logits
        if hasattr(logits, 'to_local'):
            if logits.device_mesh.size() != 1:
                raise ValueError('v4 requires one-rank DTensor')
            logits = logits.to_local()
        # Supports are sparse, position-aligned with target tokens (first position dummy).
        ids = data['v4_support_ids'][:, 1:].to(logits.device)
        valid = data['v4_support_mask'][:, 1:].to(logits.device).bool()
        targets = data['input_ids'][:, 1:].to(logits.device)
        active = (data['token_mask'][:, 1:] * data['sample_mask'][:, None]).to(logits.device).bool()
        if ids.shape[:2] != targets.shape or valid.shape != ids.shape:
            raise ValueError('misaligned old supports')
        if (ids < 0).any() or (ids >= logits.shape[-1]).any() or not valid.any(-1).all():
            raise ValueError('invalid or empty old supports')
        sorted_ids = ids.masked_fill(~valid, logits.shape[-1]).sort(-1).values
        if ((sorted_ids[..., 1:] == sorted_ids[..., :-1]) &
                (sorted_ids[..., 1:] < logits.shape[-1])).any():
            raise ValueError('duplicated support token')
        matched = (ids == targets[..., None]) & valid
        if not matched.any(-1)[active].all():
            raise ValueError('sampled token outside old trainer support')
        for key in ('prev_logprobs', 'generation_logprobs'):
            if data[key].requires_grad or not torch.isfinite(data[key][:, 1:][active.cpu() if data[key].device.type == 'cpu' else active]).all():
                raise ValueError('old and behaviour log-probabilities must be detached and finite')
        # DTensorPolicyWorker scales logits BEFORE invoking its loss callable.
        # worker_hooks installs float32 division there; never divide a second time.
        gathered = logits[:, :-1].float().gather(-1, ids)
        filtered = gathered.masked_fill(~valid, -float('inf'))
        # Parent sees an equivalent compact vocabulary with a per-position target index.
        # Its clipping, importance correction and global token normalization stay unchanged.
        compact = torch.cat([filtered, torch.zeros_like(filtered[:, :1])], dim=1)
        remapped = dict(data)
        remapped['input_ids'] = torch.cat([torch.zeros_like(targets[:, :1]), matched.long().argmax(-1)], 1)
        return super().__call__(compact, remapped, global_valid_seqs, global_valid_toks)


def train_filtered(policy, data, *, lease_check):
    """Launch-only entry: the actual Policy.train receives the v4 serialized loss callable."""
    lease_check()
    if 'v4_support_ids' not in data or 'v4_support_mask' not in data:
        raise ValueError('old-weight support must be frozen before Policy.train')
    install_on_policy(policy)
    return policy.train(data, FilteredClippedPGLossFn())
