# Matched replay versus expansion continuation checkpoint
**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/CKPT_e08_v3.md>
**TLDR:** Recovery-01 accepted; completed 1.7B training reconciled; Phase A resumed with isolated children.
Created: 10-15-2026 20:22 PDT
Last updated: 10-15-2026 22:04 PDT
## Goal
- Complete replay/expansion supervised fine-tuning and all 17,280 validation cells at four sizes; $0 paid calls.
## What ran
- Initial writer transfer: `continuation-01`, thread `01a142e9-373b-7ec3-a38f-96ba559bf525`, session `codex-rl4cv-e08v3-owner-continuation`; actual Astra/ultra, never/danger-full-access verified in native transcript.
- Adopted Phase A scheduler PID 195490 and expansion wrapper 195690; runtime `/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3`; no healthy job restarted.
- Host `recovery_watch.py` cron every 5 minutes and reboot; `recovery_state.json`, `recovery_config.json`, [watch runbook](RUNBOOK_recovery_supervision.md); real fake-failure test PASS, 5 focused tests pass; full suite 1,212 passed / 17 skipped in 305.20s.
## Results
- Six initial dispatch hashes match; full expansion 1.7B training verified: 667/667 counts, 5,757,776 loss tokens, 10,383,459 processed real tokens; final export hash check PASS. Resume step 336 was correct.
- Half export remains 335/335 verified, 2,878,589 tokens; validation 0/17,280 known. Dry receipt PASS remains frozen.
## Stuck / blocked
- Expansion wrapper exit 2 reconciled after both checksum checks and 667 counts. Old scheduler termination also ended its tmux generation children; zero durable rows, exact infrastructure retries queued; interruption receipt retained. New jobs use separate sessions and exact exit receipts.
- Both local remote environments verified via complete compressed archive, exact NeMo pin and CPU imports. Baseline 14B checks pass. Superseded owned small-file rsync stopped with partial copy retained; queued priority replay may use remote free devices at frozen 1/2 layouts. Remote eight-device availability remains unresolved.
- Personal Codex weekly used 96%; finishing reserve only. Current Vals owner is verified Astra/ultra full access; latest weekly used 39%. Dedicated Claude Vals/Stanford grants also authenticated; ordinary profile paths misleadingly report logged out.
## Next steps
- [p 10/10] Current owner recovery-01, thread01a142fc-0eff-7551-a40c-322e33c6c9cb, PID2580398/start36376767; native Astra/ultra never/full-access, 37% weekly usage. Fresh owner_ack.json verifies all six recovery_dispatch hashes; original transfer is historical. Phase A scheduler running; E4B step335/335 and export verified, 2,878,589 tokens. Phase B running WAITING_PHASE_A.
- [p 9/10] Complete Phase A; publish each rung; implement Phase B using verified wrappers, relocate/verify staged environment, admit 14B only at frozen 8-device layout. Analysis errors are blockers, not success.
- Original manifest hashes stay historical; later handoffs compare current `recovery_dispatch.json`. Required end state: 17,280 exact cells, paired bootstrap, namespace diagnostic, forecast, published parent/results and deduplicated DONE email.
## Brando to-do
- None. START already sent; hosted judging/test split deferred. Checkout retained for live consumers.
## Log
- 10-15-2026 20:22 PDT -- Prepared schedules and forecast; static checks running before lock.
- 10-15-2026 20:33 PDT -- Static checks passed (1,183 tests, all corpus/tokenizer/weight checks); locked recommended defaults before dry run.
- 10-15-2026 20:36 PDT -- START mail sent; dry session rl4cv-e08-v3-dry admitted GPU 1 under shared leases; training steps observed.
- 10-15-2026 20:48 PDT -- Dry inference recovered with CUDA 12.8; complete dry receipt PASS and disposable weights removed; Phase A queue launched.
- 10-15-2026 20:50 PDT -- First production initialization failed before updates because Ray dashboard UNIX socket path exceeded 107 bytes; shortened temp directory, preserved failure logs, verified previous coordinator exited, reconciled FAILED state and restarted.
- 10-15-2026 20:52 PDT -- Production 1.7B expansion verified through step 9; all nine loss-token counts match the frozen schedule.
- 10-15-2026 20:53 PDT -- Updated full suite passed: 1,184 passed / 17 skipped / zero failures in 339.81 seconds.
- 10-15-2026 21:11 PDT -- Expansion 1.7B reached/exported step 335; all 335 counts match 2,878,589 tokens. Prepared shared-storage route and persistent ownership continuation.
- 10-15-2026 21:25 -- Accepted ownership with 6/6 hashes and 433/433 token counts; installed five-minute/reboot recovery, passed real harmless-failure test and 5 focused tests; discovered personal quota risk and authenticated alternate subscription routes.
- 10-15-2026 21:29 PDT -- Expansion 1.7B completed all 667 updates; 667/667 token counts match 5,757,776 loss tokens. Final export underway. Full deterministic suite passed: 1,212 passed / 17 skipped in 305.20 seconds.
- 10-15-2026 21:32 PDT -- Full expansion export checksum check passed; retained wrapper exit 2 after export (post-loop syntax error; current script syntax passes). Both validation generations are live. Published recovery implementation and full training log, preparing verified Vals owner transfer for personal quota reserve.
- 10-15-2026 21:45 PDT -- Recovery-01 verified 6/6 hashes, 667/667 counts and both exports; reconciled exit2 without retraining; retained two interrupted generation batches and isolated new children; Phase A resumed. Phase B/forecast implementation and clean-environment full tests underway.
- 10-15-2026 22:04 PDT -- E4B half checkpoint verified (335 steps, 2,878,589 tokens and export checksums); both remote copied environments verified; latest full suite 1,224 passed/17 skipped. Phase B waits on Phase A; preparing queued replay on spare remote devices with unchanged layouts.

- 10-15-2026 22:30 PDT: recovery-01 continues as sole writer. Phase A scheduler now PID 595641 (`rl4cv-e08-v3-phase-a-recovery01-gen`); exact existing children preserved. Expansion 4B 667/667 token counts verified; replay 1.7B remote GPU2 399 checked counts pass. Generator environment copied/verified on both remote hosts; validation-only inputs staged; remote two-rung route active. See host `scheduler_adoption_generation_routes.json`, `recovery01_token_progress.json`, and public remote preparation receipt. Full test suite running; 0/17,280 scored cells.
