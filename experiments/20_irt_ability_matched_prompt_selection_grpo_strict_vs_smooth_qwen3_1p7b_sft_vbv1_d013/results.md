# Experiment 20 results: CPU Phase 0 completion; trainer FAILED

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/results.md>

**TLDR:** Experiment 20 is completing pre-registered CPU calibration after the trainer failed its consistency gate (2.61982% of tokens versus 1% allowed); the effect of item response theory (IRT) selection on held-out validation remains unmeasured.

**Status:** IN PROGRESS: post-stop CPU Phase 0 completion; trainer verdict remains FAILED. The downstream IRT treatment effect is unmeasured.

**Last updated:** 10-21-2026 18:19:24 PDT

## Post-stop completion of pre-registered Phase 0 (CPU only, dispatcher instruction 10-21-2026)

**Status (10-21-2026 17:17:03 PDT): IN PROGRESS.** The dispatcher authorized scoring the existing 4,312 train generations, Phase 0b and gate G0, and a saved-receipt comparison with experiment 13 v4 T1. Trainer verdict stays **FAILED**. No new graphics processor (GPU) jobs, pilot, trainer changes or gate changes. Existing failed-gate closure below remains historical evidence.

- CPU scoring: 32/32 strict completion files, 30/32 partial completion files; 4257/4,312 partial cells logged (monitor 20261022T011904Z; states {'COMPLETED': 60, 'PENDING': 1, 'OUT_OF_MEMORY': 8, 'RUNNING': 2}). Collector audits parent completion, source identities and compiler streams; intact nonzero exits retain native failure scores. Retry 2 submitted: materialization `48881654` → strict array `48881657` and partial-credit array `48881660`, each array 32 tasks (`-p normal -c 1 --mem 16G`). `score_sherlock.sh` is invoked unchanged through its interpreter hook, which adds D-109 durable capture. [Retry submission](expt_v1/results/receipts/cpu_retry_receipt.txt). Attempt 1 preparation (`48880517`) exited 1 before materialization (empty log, 9 s); dependent arrays were canceled without executing. Fixed shell-profile initialization under unset-variable checking; no scored cells or model runs were repeated.
- Resource-failure diagnostics: strict jobs `48881657_8` and `_2` recorded out-of-memory events and complete scorer tables. D-109 identifies one killed initial compiler call in each. Identical-cell retry attempts 2 (`48888345`, `48888814`) and 3 (`48890055`, `48890056`) also exhausted memory; final allowed attempt 4 (`48890627`, `48890632`) also exhausted memory and retained the exact source, scorer and `-p normal -c 1 --mem 16G` settings. All original outputs remain immutable. **Interpretation correction:** the frozen scorer explicitly maps every nonzero initial compile exit to failure (run_real_eval.py:215,704–706), and with `--skip-tc` emits `scoring_status=scored` (:811). Protocol §2 prescribes that scorer/resources; its infrastructure-retry clause does not recode completed negative-exit rows as missing. Therefore intact completed resource failures retain their native zero scores, just as native 600-second timeouts do; absent/incomplete evidence remains unresolved. The earlier proposal to mask completed memory failures was not adopted. The 32 GB question was withdrawn; no resources, scorer or gate changed. Collector `48882642` was canceled because its original success dependency cannot resolve; replacement collector `48892191` waits for all owned arrays/retries to terminate, then audits immutable tables, hashes and compiler evidence. [Collector fixture](expt_v1/results/receipts/collector_native_verification.json). [Affected-cell evidence](expt_v1/results/receipts/e20_oom_cells.stdout).

- IRT/G0: strict scoring is independent of descriptive smooth missingness. Among the first 1,063 terminal partial records, 267 malformed-source outcomes have the registered zero credit, and 28 duplicate declaration identities remain unmeasured; they are never imputed as zero. The analysis records missing smooth cells and masks only their likelihood contributions. Numerical driver is ready; synthetic gradient, grouped-fold, bootstrap, joint-likelihood, convergence-rejection and freeze checks passed. Real-data fitting awaits score tables; frozen protocol §3 applies. [Driver](expt_v1/analyze_phase0_e20.py).
- Saved smoke: COMPLETE. Update 2 mismatch = 22,459 finite errors above 0.05 + 195 unsupported actions, out of 864,717 tokens (2.61982%). Analogous experiment 13 v4 T1 comparison **FAIL** due to nonzero unsupported actions. Exact median/p99 and task/token slices unavailable; all-token median bound ≤0.00841008 <0.01, p99 ≤0.10 undecidable. [Full saved-receipt comparison](RESULTS_saved_smoke_t1.md).
- D-109 recovery: materialization completed (61 s), all 32 strict tasks running. Found partial wrapper bypasses for a function-local subprocess import and the parser’s `nice -n 10 lake env lean` invocation. Held pending partial tasks, then canceled owned partial array `48881660` (only index 0 had started) and dependent collector `48882176`; preserved all outputs. Corrected wrapper passed compiler/kernel/parser/timeout fixtures and was deployed to isolated `code/cpu_partial_d109_v2`; replacement partial array `48882641` and collector `48882642` submitted. The interrupted index ran 98 seconds; original diagnostics are preserved. Strict jobs continue with unchanged deployed bytes. [Capture verification](expt_v1/results/receipts/partial_d109_fixture.json), [actual parser/compiler/kernel receipts](expt_v1/results/receipts/live_d109_examples.json). All sampled raw stream/source hashes verified against metadata; Lean4.22.0 identity retained.
- Publication: same unmerged [PR #20](https://github.com/brando90/rl-4-code-verification/pull/20); G0_FINISHED.txt will record the G0 verdict, AUC interval and results revision.

## Trainer-stop findings (historical closure at 10-21-2026 15:24 PDT)

1. **Trainer gate failed after both smoke updates:** the maximum per-update mismatch is **22,654/864,717 = 2.61982% [n/a, n/a], p-val=n/a** (22,459 tokens with |Δlog p| > 0.05 plus 195 outside recomputed support). Update 1 was 21,888/842,189 = 2.59894%; pooled descriptively, 44,542/1,706,906 = 2.60952%. Threshold: ≤1%, runbook §6.5 and experiment 09 precedent; the pre-existing implementation gates on the maximum. These are exact observed token counts from two updates of arm A, seed 0, with no independent-token inference or repeated-seed uncertainty. The final native receipt says `pass: false`; Slurm exit code is `3:0`. [Final native check](expt_v1/results/receipts/smoke_gate/smoke_logprob_check.json), [gate provenance](expt_v1/results/smoke_gate_observed.json), [plot](expt_v1/results/smoke_gate.png).
2. **Limited training diagnostics:** 256 rollouts on 32 train prompts: update 1 strict 8/128, active 3/16; update 2 strict 9/128, active 3/16; 73/256 token-capped and 0/256 unresolved scoring outcomes. Generation/scoring/training took 247.80/1,134.56/36.03 s in update 1 and 239.81/115.80/35.68 s in update 2. The run completed at 10-21-2026 14:09:11 PDT. These are smoke diagnostics, not validation learning curves or causal evidence. [All 256 rollout records](expt_v1/results/smoke_rollouts.csv), [active-group plot](expt_v1/results/smoke_active_groups.png). In-support mean absolute log-probability differences were 0.004148 and 0.004204; signed bias was not recorded.
3. **Calibration retained and unscored:** 4,312/4,312 planned train generations from 539 tasks are saved; 0 missing generations remain explicit in the full table. The four adopted generation jobs are terminal. Actual chunk sizes are 1,432/1,120/904/856 cells (the line-preserving splitter balances bytes, not task counts). Observed generation tokens: 25,821,971; token-capped generations: 940/4,312. All 4,312 strict, factored-reward and component score entries are blank/unmeasured; no calibration scoring, IRT fit, G0, pilot, main training or validation evaluation followed the failed gate. The test split stayed closed. [Full cell table](expt_v1/results/phase0_cells_unscored.csv), [collection summary](expt_v1/results/closure_collection.json), [remote raw/diagnostic paths and hashes](expt_v1/results/remote_artifact_manifest.csv).
4. **Implementation deviations are explicit:** the adopted smoke used a custom optimizer loop with TRL's colocated `VLLMGeneration` helper, rather than the runbook's `GRPOTrainer` or prescribed NeMo fallback. The predecessor recorded that choice in the draft protocol; it is not accepted as satisfying the runbook. Smoke also ran before calibration/G0, used seed 0, and had a 45-minute launcher. Its context capacity was raised from 16,384 to 20,480 after an infrastructure failure, preserving the 12,288-new-token sampler. [Captured runtime provenance](expt_v1/results/receipts/runtime_takeover/manifest.json). No backend redesign or gate weakening follows the failure.
5. **Verification passed:** `make test` on the operational fixes: 1,415 passed, 17 skipped, 6 subtests passed; 3 warnings, 296.87 s. Shell syntax and diagnostic-retention retry fixtures passed. Verification used a temporary worktree at the depth required by the repository's legacy relative dependency lookup, with frozen external pins; no other experiment was edited. [Verification receipt](expt_v1/results/receipts/verification_terminal_publication.json).

**Next step:** finish the authorized CPU Phase 0 analyses and publish to [pull request #20](https://github.com/brando90/rl-4-code-verification/pull/20). The trainer stop remains in force.

## Live phase table

| Phase | State | GPU-h used / cap |
|---|---|---|
| Setup and protocol draft | Recorded; never pilot-locked | 0 |
| Phase 0a generation, 539 × 8 train cells | Adopted array 48841018_[0-3] terminal; 4,312/4,312 generated, 0 missing; separate CPU scoring in progress | 7.2358 / 10, final |
| Phase 0a strict/smooth scoring | IN PROGRESS: strict48881657 + corrected partial48882641; collector48892191 waiting for terminal jobs; preparation48881654 complete | 0 |
| Phase 0b IRT fit and G0 | PENDING scoring; authorized post-stop completion | CPU only |
| Trainer smoke | FAILED gate after 2/2 updates; 48857034 exit 3:0; earlier infrastructure failures 48845232/48855196 included | 0.5900, included in pilot cap 15 |
| Pilot A/C/S | NOT RUN | 0 additional / 15 |
| Main arms A/S/E/C/B/D | NOT RUN | 0 / 130 |
| Validation evaluation | NOT RUN | 0 / 80 |
| Total | Final allocation, including all failures | 7.8258 / 200 |

Allocation source: [all seven allocation rows](expt_v1/results/gpu_accounting.csv), [terminal Slurm receipt](expt_v1/results/receipts/live_gate_state.json), and [final accounting](expt_v1/results/receipts/final_accounting.json). GPU-hours use allocated elapsed seconds × GPU count, including failures and scoring time while a GPU allocation was held. Phase 0 used 7.2358/10 GPU-h; trainer smoke used 0.5900/15; main and evaluation used 0/130 and 0/80. Total 7.8258/200 GPU-h, API spend **$0**. All adopted GPU jobs ended naturally. The subsequent CPU Phase 0 completion is authorized by the dispatcher instruction above. Other owners' jobs were untouched.

## Missing outcomes and artifacts

H1 (C−A), H3 (C−S and C−E), H2 (online IRT prediction/active-group comparison), H4 ((D−B)−(C−A)), validation pass@1/pass@8, ability tracking and the smooth-reward audit are **not measured**. Their estimates, confidence intervals and p-values are unavailable, not zero. Required validation learning curves and the H4 2×2 plot cannot be produced from the smoke data; the actual gate plot above is supplied instead. Calibration scores, fitted item parameters and numeric forecasts are pending the authorized CPU completion. No claims use the held-out test split.

## Provenance and continuation

The fenced Claude worker handed off revision `e39d620a`; Codex gpt-6-astra ultra adopted the live jobs and published takeover receipt `eaa6ef96`. Two pre-takeover smoke infrastructure failures consumed 165 allocated GPU-seconds (missing SciPy, then context capacity). Actual launcher/source were captured; their submitter session remains unresolved. [Current resumable checkpoint](CKPT_codex-rl4cv-e20-irt-prompt-selection.md), [experiment checkpoint](CKPT_e20.md), [runbook](expt_v1/cc.md), [Google experiment log](https://docs.google.com/document/d/1KKKabJJArClVmXcaxfTF5jxk8nF1oHmCH08d44jbqUg/edit).

**Copy-ready collaborator message:** I stopped the IRT prompt-selection experiment at the trainer consistency gate: 2.62% of tokens exceeded the allowed mismatch, above the 1% limit. We have not yet tested whether IRT selection improves held-out strict pass@1.

**TLDR-end:** [rl4cv: expt20 IRT prompt selection for GRPO] `20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013` stopped at the trainer log-probability gate. The downstream benefit remains unmeasured; GPU work is terminal at 7.8258 GPU-hours and $0 API spend, while authorized CPU scoring continues.

**Snapshot:**

- Trainer mismatch: 22,654/864,717 = 2.61982%; allowed ≤1%.
- Smoke records: 256 rollouts, 32 prompts, 2 updates.
- Calibration: 4,312 saved generations; scored-cell collection pending both CPU arrays.
- Allocation ledger: 7 terminal jobs, 7.8258 GPU-hours.
- Deterministic verification: 1,415 passed, 17 skipped, 6 subtests passed.
- Review: pull request #20; not merged.
