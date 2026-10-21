# V4-A1: unresolved importance correction at uncertified positions

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/BLOCKER_V4_A1_importance_correction.md>

**TLDR:** The top-64 certificate solves the previous support-receipt gate blocker, but A1 allows uncertified positions with no generator log probability. The unchanged installed loss requires that probability for a separate importance correction. The master must specify its treatment before measured launch; this document changes neither frozen document.

## Source evidence

For `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4`, the frozen recipe keeps importance-weight cap 2, token-normalized loss and the installed NeMo 0.4.0 loss path. The v4 wrapper's `LOSS` enables `use_importance_sampling_correction` and sets `truncated_importance_sampling_ratio=2`.

Installed source `/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/nemo_rl/algorithms/loss_functions.py` has two distinct operations:

1. Around line 288: policy ratio `exp(curr_logprobs - prev_logprobs)`. Both terms are trainer-computed, as the protocol requires.
2. Around lines 332–360: actor correction `exp(prev_logprobs - generation_logprobs)`, clamped at 2 and multiplied into the clipped loss. This still needs the generator probability.

A1 §7 stores generator log π only **where certified**. A1 §5 permits up to 1% uncertified T1 positions; updates have no zero-uncertified requirement. At these positions the installed correction has no specified input. The raw sampled-token probability cannot replace the filtered probability, and the trainer's tie-inclusive normalizer can differ from the generator's normalizer.

The new tests in `tests/test_amendment_a1.py` exercise the actual installed loss on tiny CPU logits. With trainer probabilities and advantages fixed, subtracting log(1.5) from the generator log probability multiplies the loss by 1.5; a nonfinite missing probability is rejected. Neither test constructs an engine or runs an optimizer. This is a deterministic implementation fact, not a statistical experiment; confidence intervals and p-values do not apply.

## Smallest fixes for the master to choose

- Preserve the current importance correction by recording the **actual filtered sampled-token log probability at every position**, independently of the top-64 support certificate. A v4-owned sampler hook could capture it without editing the shared runtime. That adds a receipt field and needs a numbered amendment plus installed-source and real T1 equivalence checks.
- Explicitly change the loss contract to unit actor correction (or another specified treatment) at uncertified positions. This changes the objective and must be stated prospectively; the implementation cannot silently choose it.

A stronger “zero uncertified positions everywhere, otherwise stop” rule would also avoid missing probabilities, but it is an additional stop criterion absent from A1, not an implementation-only fix. No such rule is adopted here. A1's reduced `support_size` is likewise represented as null when support cannot be determined; it cannot truthfully be an exact integer in an uncertified case without more engine evidence.

## Implementation status

The A1 certificate, trainer tie rule, receipt extraction, guarded top-64 generator constructor and ordered CPU stage controller are implemented. The full dry run uses stub engines and explicitly labels every stage synthetic. The real scorer/trainer/checkpoint/export/replay adapter, device-leased stage subprocess orchestration and fixed-cohort audit integration are **not complete**. The admission records that implementation gap separately from the scientific blocker; neither is hidden behind a device lease or a request for a launch go.

The earlier frozen top-20 impossibility is no longer the blocker. `launch-check` still rejects for the two reasons above. No GPU, model generation, optimizer step, provider call, cron installation or tmux session is needed to reproduce the blocker.
