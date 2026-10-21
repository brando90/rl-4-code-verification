# Experiment 20 results: stopped at the trainer log-probability gate

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/results.md>

**TLDR:** Experiment 20 stopped before testing IRT-guided prompt selection: the Qwen3-1.7B trainer smoke exceeded its log-probability mismatch limit (2.59894% of tokens versus 1% allowed), so the effect on held-out validation remains unmeasured.

**Status:** STOPPED at the trainer gate; already-running adopted jobs are finishing naturally. Execution verdict FAILED; this is not evidence of a null IRT effect.

**Last updated:** 10-21-2026 14:09 PDT

## Findings

1. **Trainer gate failed:** 21,721 tokens with |Δlog p| > 0.05 plus 167 outside the recomputed sampling support, out of 842,189 = **2.59894% [n/a, n/a], p-val=n/a**. Threshold: ≤1%, runbook §6.5 and experiment 09 precedent. This is the exact observed token census of smoke update 1, arm A, seed 0; no independent-token inference or repeated-seed estimate is available. The pre-existing implementation takes the maximum across smoke updates, so update 2 cannot reverse the failure. [Gate receipt](expt_v1/results/smoke_gate_observed.json), [observed log](expt_v1/results/receipts/smoke_gate/log.jsonl), [plot](expt_v1/results/smoke_gate.png).
2. **Limited training diagnostics:** update 1 generated 128 rollouts on 16 train prompts, with 8/128 strict successes, 3/16 active groups and 35/128 token-capped outputs; 0/128 scoring outcomes unresolved. Generation took 247.80 s, scoring 1,134.56 s and training 36.03 s (update total 1,418.83 s). These are smoke diagnostics, not validation learning curves or causal evidence. [All 128 per-rollout records](expt_v1/results/smoke_rollouts.csv). In-support mean absolute log-probability difference was 0.004148; signed bias was not recorded.
3. **Calibration remains unscored:** 2,432/4,312 train generations saved at the latest live receipt. Four adopted generation tasks are finishing under their existing allocations; no scoring/partial-credit arrays, IRT fit or G0 evaluation will launch after this failed gate. No validation evaluation or test-split access occurred.
4. **Implementation deviations are explicit:** the adopted smoke used a custom optimizer loop with TRL's colocated `VLLMGeneration` helper, rather than the runbook's `GRPOTrainer` or prescribed NeMo fallback. The predecessor recorded that choice in the draft protocol; it is not accepted as satisfying the runbook. Smoke also ran before calibration/G0, used seed 0, and had a 45-minute launcher. Its context capacity was raised from 16,384 to 20,480 after an infrastructure failure, preserving the 12,288-new-token sampler. [Captured runtime provenance](expt_v1/results/receipts/runtime_takeover/manifest.json). No backend redesign or gate weakening follows the failure.
5. **Verification passed:** `make test` on the operational fixes: 1,415 passed, 17 skipped, 6 subtests passed; 3 warnings, 291.38 s. Shell syntax and diagnostic-retention retry fixtures passed. Verification used a temporary worktree at the depth required by the repository's legacy relative dependency lookup, with frozen external pins; no other experiment was edited. [Verification receipt](expt_v1/results/receipts/verification_runtime_retention.json).

**Next step:** reconcile the already-running jobs' terminal states and actual GPU-hours, preserve final receipts, finish the review pull request and notifications. No further experimental phase is admitted.

## Live phase table

| Phase | State | GPU-h used / cap |
|---|---|---|
| Setup and protocol draft | Recorded; never pilot-locked | 0 |
| Phase 0a generation, 539 × 8 train cells | Adopted array 48841018_[0-3], 2,432/4,312 saved; finishing naturally | 4.4356 / 10, running allocation |
| Phase 0a strict/smooth scoring | NOT RUN after failed trainer gate | 0 |
| Phase 0b IRT fit and G0 | NOT RUN | CPU only |
| Trainer smoke | Gate failed on update 1; job 48857034 still running; earlier infrastructure failures 48845232/48855196 included | 0.5736, included in pilot cap 15 |
| Pilot A/C/S | NOT RUN | 0 additional / 15 |
| Main arms A/S/E/C/B/D | NOT RUN | 0 / 130 |
| Validation evaluation | NOT RUN | 0 / 80 |
| Total | Allocation through latest receipt, not final | 5.0092 / 200 |

Allocation source: [live Slurm receipt](expt_v1/results/receipts/live_gate_state.json), captured 2026-10-21T21:08:14.476758+00:00. GPU-hours use allocated elapsed time × GPU count, including failures and scoring time while the GPU allocation is held. API spend **$0**. Final costs are pending the already-running jobs' natural termination; the runbook forbids cancellation of adopted jobs. Other owners' jobs are untouched.

## Missing outcomes and artifacts

H1 (C−A), H3 (C−S and C−E), H2 (online IRT prediction/active-group comparison), H4 ((D−B)−(C−A)), validation pass@1/pass@8, ability tracking and the smooth-reward audit are **not measured**. Their estimates, confidence intervals and p-values are unavailable, not zero. Required validation learning curves and the H4 2×2 plot cannot be produced from the smoke data; the actual gate plot above is supplied instead. Calibration scores, fitted item parameters and numeric forecasts are also unavailable. No claims use the held-out test split.

## Provenance and continuation

The fenced Claude worker handed off revision `e39d620a`; Codex gpt-6-astra ultra adopted the live jobs and published takeover receipt `eaa6ef96`. Two pre-takeover smoke infrastructure failures consumed 165 allocated GPU-seconds (missing SciPy, then context capacity). Actual launcher/source were captured; their submitter session remains unresolved. [Current resumable checkpoint](CKPT_codex-rl4cv-e20-irt-prompt-selection.md), [experiment checkpoint](CKPT_e20.md), [runbook](expt_v1/cc.md), [Google experiment log](https://docs.google.com/document/d/1KKKabJJArClVmXcaxfTF5jxk8nF1oHmCH08d44jbqUg/edit).

**Copy-ready collaborator message:** I stopped the IRT prompt-selection experiment at the trainer consistency gate: 2.60% of tokens exceeded the allowed mismatch, above the 1% limit. We have not yet tested whether IRT selection improves held-out strict pass@1.

**TLDR-end:** [rl4cv: expt20 IRT prompt selection for GRPO] `20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013` stopped at the trainer log-probability gate. The downstream benefit of IRT prompt selection remains unmeasured; final adopted-job accounting is pending.
