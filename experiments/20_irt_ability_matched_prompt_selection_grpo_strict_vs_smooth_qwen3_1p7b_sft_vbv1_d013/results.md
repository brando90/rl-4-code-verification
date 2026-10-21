# Experiment 20 results: stopped at the trainer log-probability gate

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/results.md>

**TLDR:** Experiment 20 stopped before testing IRT-guided prompt selection: the Qwen3-1.7B trainer smoke exceeded its log-probability mismatch limit (2.61982% of tokens versus 1% allowed), so the effect on held-out validation remains unmeasured.

**Status:** STOPPED at the trainer gate; adopted calibration jobs are finishing naturally. Execution verdict FAILED; this is not evidence of a null IRT effect.

**Last updated:** 10-21-2026 14:19 PDT

## Findings

1. **Trainer gate failed after both smoke updates:** the maximum per-update mismatch is **22,654/864,717 = 2.61982% [n/a, n/a], p-val=n/a** (22,459 tokens with |Δlog p| > 0.05 plus 195 outside recomputed support). Update 1 was 21,888/842,189 = 2.59894%; pooled descriptively, 44,542/1,706,906 = 2.60952%. Threshold: ≤1%, runbook §6.5 and experiment 09 precedent; the pre-existing implementation gates on the maximum. These are exact observed token counts from two updates of arm A, seed 0, with no independent-token inference or repeated-seed uncertainty. The final native receipt says `pass: false`; Slurm exit code is `3:0`. [Final native check](expt_v1/results/receipts/smoke_gate/smoke_logprob_check.json), [gate provenance](expt_v1/results/smoke_gate_observed.json), [plot](expt_v1/results/smoke_gate.png).
2. **Limited training diagnostics:** 256 rollouts on 32 train prompts: update 1 strict 8/128, active 3/16; update 2 strict 9/128, active 3/16; 73/256 token-capped and 0/256 unresolved scoring outcomes. Generation/scoring/training took 247.80/1,134.56/36.03 s in update 1 and 239.81/115.80/35.68 s in update 2. The run completed at 10-21-2026 14:09:11 PDT. These are smoke diagnostics, not validation learning curves or causal evidence. [All 256 rollout records](expt_v1/results/smoke_rollouts.csv), [active-group plot](expt_v1/results/smoke_active_groups.png). In-support mean absolute log-probability differences were 0.004148 and 0.004204; signed bias was not recorded.
3. **Calibration remains unscored:** 2,816/4,312 train generations saved at the latest live receipt. Four adopted generation tasks are finishing under their existing allocations; no scoring/partial-credit arrays, IRT fit or G0 evaluation will launch after this failed gate. No validation evaluation or test-split access occurred.
4. **Implementation deviations are explicit:** the adopted smoke used a custom optimizer loop with TRL's colocated `VLLMGeneration` helper, rather than the runbook's `GRPOTrainer` or prescribed NeMo fallback. The predecessor recorded that choice in the draft protocol; it is not accepted as satisfying the runbook. Smoke also ran before calibration/G0, used seed 0, and had a 45-minute launcher. Its context capacity was raised from 16,384 to 20,480 after an infrastructure failure, preserving the 12,288-new-token sampler. [Captured runtime provenance](expt_v1/results/receipts/runtime_takeover/manifest.json). No backend redesign or gate weakening follows the failure.
5. **Verification passed:** `make test` on the operational fixes: 1,415 passed, 17 skipped, 6 subtests passed; 3 warnings, 291.38 s. Shell syntax and diagnostic-retention retry fixtures passed. Verification used a temporary worktree at the depth required by the repository's legacy relative dependency lookup, with frozen external pins; no other experiment was edited. [Verification receipt](expt_v1/results/receipts/verification_runtime_retention.json).

**Next step:** reconcile the already-running jobs' terminal states and actual GPU-hours, preserve final receipts, finish the review pull request and notifications. No further experimental phase is admitted.

## Live phase table

| Phase | State | GPU-h used / cap |
|---|---|---|
| Setup and protocol draft | Recorded; never pilot-locked | 0 |
| Phase 0a generation, 539 × 8 train cells | Adopted array 48841018_[0-3], 2,816/4,312 saved; finishing naturally | 5.1033 / 10, running allocation |
| Phase 0a strict/smooth scoring | NOT RUN after failed trainer gate | 0 |
| Phase 0b IRT fit and G0 | NOT RUN | CPU only |
| Trainer smoke | FAILED gate after 2/2 updates; 48857034 exit 3:0; earlier infrastructure failures 48845232/48855196 included | 0.5900, included in pilot cap 15 |
| Pilot A/C/S | NOT RUN | 0 additional / 15 |
| Main arms A/S/E/C/B/D | NOT RUN | 0 / 130 |
| Validation evaluation | NOT RUN | 0 / 80 |
| Total | Allocation through latest receipt, not final | 5.6933 / 200 |

Allocation source: [live Slurm receipt](expt_v1/results/receipts/live_gate_state.json), captured 10-21-2026 14:18:15 PDT. GPU-hours use allocated elapsed time × GPU count, including failures and scoring time while the GPU allocation is held. API spend **$0**. Final costs are pending the already-running jobs' natural termination; the runbook forbids cancellation of adopted jobs. Other owners' jobs are untouched.

## Missing outcomes and artifacts

H1 (C−A), H3 (C−S and C−E), H2 (online IRT prediction/active-group comparison), H4 ((D−B)−(C−A)), validation pass@1/pass@8, ability tracking and the smooth-reward audit are **not measured**. Their estimates, confidence intervals and p-values are unavailable, not zero. Required validation learning curves and the H4 2×2 plot cannot be produced from the smoke data; the actual gate plot above is supplied instead. Calibration scores, fitted item parameters and numeric forecasts are also unavailable. No claims use the held-out test split.

## Provenance and continuation

The fenced Claude worker handed off revision `e39d620a`; Codex gpt-6-astra ultra adopted the live jobs and published takeover receipt `eaa6ef96`. Two pre-takeover smoke infrastructure failures consumed 165 allocated GPU-seconds (missing SciPy, then context capacity). Actual launcher/source were captured; their submitter session remains unresolved. [Current resumable checkpoint](CKPT_codex-rl4cv-e20-irt-prompt-selection.md), [experiment checkpoint](CKPT_e20.md), [runbook](expt_v1/cc.md), [Google experiment log](https://docs.google.com/document/d/1KKKabJJArClVmXcaxfTF5jxk8nF1oHmCH08d44jbqUg/edit).

**Copy-ready collaborator message:** I stopped the IRT prompt-selection experiment at the trainer consistency gate: 2.62% of tokens exceeded the allowed mismatch, above the 1% limit. We have not yet tested whether IRT selection improves held-out strict pass@1.

**TLDR-end:** [rl4cv: expt20 IRT prompt selection for GRPO] `20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013` stopped at the trainer log-probability gate. The downstream benefit of IRT prompt selection remains unmeasured; final calibration-job accounting is pending.
