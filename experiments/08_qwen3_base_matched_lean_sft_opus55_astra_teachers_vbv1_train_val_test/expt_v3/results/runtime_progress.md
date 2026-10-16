# Recovery and execution events for the matched continuation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/results/runtime_progress.md>

**Last updated:** 10-15-2026 21:45 PDT. **Status:** RUNNING.

- Recovery-01 verified native `gpt-6-astra` / `ultra`, `never` / `danger-full-access`, six current dispatch hashes and all 667 expansion 1.7B training counts. The Vals subscription reported 37% weekly usage at acceptance. [Ownership receipt](owner_recovery01_v3.json).
- Expansion 1.7B completed 5,757,776 loss tokens and 10,383,459 processed real tokens; both step-335 and step-667 export checksum checks passed. Native wrapper exit 2 is preserved and scheduler bookkeeping reconciled without retraining. [Reconciliation](train_logs/v3_E_1p7b_export_reconciliation.json).
- Replacing the original scheduler closed its tmux process group and interrupted both live generations. Both raw output files had zero durable rows; native progress logs reported 300/1024 and 54/1024 completed prompts within their first batches. Exact same-cell infrastructure retries retain the frozen models, seed, 12,288-token cap and 1,080-cell rung denominator. No alternative samples were selected. [Interruption receipt](generation_interruption_recovery-01.json).
- New jobs have separate sessions, boot/start identities and durable native exit receipts. A real harmless session-hangup test confirms child completion survives scheduler loss; 15 focused recovery/forecast/remote-admission tests pass. Existing failure evidence stays in the host logs.
- Phase A is running in `rl4cv-e08-v3-phase-a-recovery-01`; expansion 4B has passed step 60/335. Replay 1.7B and the identical generation retries await devices under both lease registries, retaining GPU 0 and an idle device.
- Phase B scheduler and remote TP8 admission implementation are prepared. Remote staging remains incomplete; no copied environment has been executed. skampere2 had 0/8 free devices and skampere3 had 4/8 at the last inventory; Slurm still lists no association. Eight-device training is not replaced by a smaller layout.
- Full tests initially reported 1,212 passed / 17 skipped / 4 failed because the Vals profile's inherited `CODEX_HOME` conflicts with v1 monitor fixtures. The clean-environment `make test` passed: 1,216 passed / 17 skipped / zero failures in 366.32 seconds. All 15 focused tests including subsequently added forecast and remote-admission checks also pass; no production profile was changed.
- Host cron remains every five minutes and at reboot. Original finite route/deadline inventory is retained, with the actual Vals runtime and allowance updated. No repeated START mail; DONE waits for checked publication of all 17,280 cells and actual delivery.

**TLDR-end:** [rl4cv: 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3] Recovery has reconciled completed training and resumed Phase A; validation coverage is still 0/17,280. Zero paid experiment calls; test split unopened.

- 10-15-2026 21:49 PDT: Compressed 11 GB environment archive built; preparing local extraction on candidate remote nodes while keeping large checkpoints on shared storage. Live 4B shell retains its original inode and bytes while future launches gain the environment-path override.
