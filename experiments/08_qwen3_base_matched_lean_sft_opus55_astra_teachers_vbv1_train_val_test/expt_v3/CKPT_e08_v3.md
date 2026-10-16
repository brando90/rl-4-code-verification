# Matched replay versus expansion continuation checkpoint
**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/CKPT_e08_v3.md>
**TLDR:** Dry run PASS; 1.7B expansion half-budget exported and token-verified; production continues.
Created: 10-15-2026 20:22 PDT
Last updated: 10-15-2026 21:11 PDT
## Goal
- Complete matched replay/expansion supervised fine-tuning and all 17,280 validation cells at four sizes; $0 paid calls.
## What ran
- Input `27ffa74`, lock `18f5217`, dry/execution `90ad157`, publication `f8d7343`; START email delivered; full tests 1,184 passed / 17 skipped; merge regressions 27 passed.
- Persistent Phase A scheduler PID 195490, session `rl4cv-e08-v3-phase-a-recovery`; state `/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/phase_a_state.json`.
- 1.7B expansion child wrapper PID 195690 owns GPU 1; adopt it and the scheduler, never duplicate. Last native checkpoint step 335; next is 667.
- Private shared staging `/dfs/scratch0/brando9/rl4cv_e08_v3_remote`: NeMo environment and 14B baseline rsyncs underway; no remote GPU work started.
## Results
- Dry: 8/8 matched steps, 75,345 loss tokens, fixed-set loss 0.289257→0.252943, 2/2 Lean extractions; disposable weights deleted.
- Production expansion half: 335/335 matched steps, 2,878,589 loss tokens; export saved. Validation 0/17,280 known; gates unresolved.
- Replay half/full planned 334/658, expansion 335/667; frozen corpus, manifest, forecast and all four baseline exports verified.
## Stuck / blocked
- 4B awaits 2 free devices plus idle reserve. Experiment 13 actively holds GPU 0; preserve an additional idle GPU and all other users' jobs.
- 14B needs 8 idle devices elsewhere; open remote local disks hold only 230/311 GiB free, so shared staging route prepared (2.2 TiB measured free, ≤1,100 GiB estimated full 14B working set; recheck at launch).
- Two infrastructure failures repaired before production: CUDA 12.4 compiler selection and Ray socket pathname length; original logs retained.
## Next steps
- [p 9/10] Read [RUNBOOK_continuation_owner.md](RUNBOOK_continuation_owner.md), inspect phase_a_state.json and verify current child progress; publish each completed rung, then execute Phase B and comparison.
- Verify remote copy completion, relocate copied editable-package paths, hash-check weights and CPU imports before any remote lease; respect priority order and unchanged tensor parallelism.
- Establish/test non-model death/completion watch and verified ownership continuation; current parent remains supervisor until acknowledgement.
## Brando to-do
- None. Hosted judging and test split remain deferred. DONE mail only with actual terminal status; active checkout retained until all consumers finish.
## Log
- 10-15-2026 20:22 PDT -- Prepared schedules and forecast; static checks running before lock.
- 10-15-2026 20:33 PDT -- Static checks passed (1,183 tests, all corpus/tokenizer/weight checks); locked recommended defaults before dry run.
- 10-15-2026 20:36 PDT -- START mail sent; dry session rl4cv-e08-v3-dry admitted GPU 1 under shared leases; training steps observed.
- 10-15-2026 20:48 PDT -- Dry inference recovered with CUDA 12.8; complete dry receipt PASS and disposable weights removed; Phase A queue launched.
- 10-15-2026 20:50 PDT -- First production initialization failed before updates because Ray dashboard UNIX socket path exceeded 107 bytes; shortened temp directory, preserved failure logs, verified previous coordinator exited, reconciled FAILED state and restarted.
- 10-15-2026 20:52 PDT -- Production 1.7B expansion verified through step 9; all nine loss-token counts match the frozen schedule.
- 10-15-2026 20:53 PDT -- Updated full suite passed: 1,184 passed / 17 skipped / zero failures in 339.81 seconds.
- 10-15-2026 21:11 PDT -- Expansion 1.7B reached/exported step 335; all 335 counts match 2,878,589 tokens. Prepared shared-storage route and persistent ownership continuation.
