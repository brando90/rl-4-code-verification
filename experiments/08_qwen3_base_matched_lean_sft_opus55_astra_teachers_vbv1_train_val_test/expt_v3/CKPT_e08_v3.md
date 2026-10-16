# Matched replay versus expansion continuation checkpoint
**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/CKPT_e08_v3.md>
**TLDR:** Training adopted without restart; owner hashes/tokens verified; persistent recovery installed and failure-tested.
Created: 10-15-2026 20:22 PDT
Last updated: 10-15-2026 21:29 PDT
## Goal
- Complete replay/expansion supervised fine-tuning and all 17,280 validation cells at four sizes; $0 paid calls.
## What ran
- Initial writer transfer: `continuation-01`, thread `01a142e9-373b-7ec3-a38f-96ba559bf525`, session `codex-rl4cv-e08v3-owner-continuation`; actual Astra/ultra, never/danger-full-access verified in native transcript.
- Adopted Phase A scheduler PID 195490 and expansion wrapper 195690; runtime `/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3`; no healthy job restarted.
- Host `recovery_watch.py` cron every 5 minutes and reboot; `recovery_state.json`, `recovery_config.json`, [watch runbook](RUNBOOK_recovery_supervision.md); real fake-failure test PASS, 5 focused tests pass; full suite 1,212 passed / 17 skipped in 305.20s.
## Results
- Six initial dispatch hashes match; full expansion 1.7B training verified: 667/667 counts, 5,757,776 loss tokens, 10,383,459 processed real tokens; final export in progress. Resume step 336 was correct.
- Half export remains 335/335 verified, 2,878,589 tokens; validation 0/17,280 known. Dry receipt PASS remains frozen.
## Stuck / blocked
- Local 4B/inference await devices plus idle reserve; experiment 13 keeps device 0. Remote skampere2 has 0 idle and skampere3 4 idle; 14B requires 8 elsewhere.
- Shared NeMo rsync PID 1788378 still active; preserve it. Copied 14B baseline hash check running; never execute partial environments. Shared free bytes 2,289,713,545,216 at last check.
- Personal Codex weekly used 96%; finishing reserve only. Distinct Vals Codex authenticated, recent 37% used (stale observation); fresh continuation runtime still to verify. Dedicated Claude Vals/Stanford grants also authenticated; ordinary profile paths misleadingly report logged out.
## Next steps
- [p 10/10] Finish tests/publication of recovery changes, then transfer to Vals Codex through `python3 <expt_v3>/recovery_watch.py` after exact `owner_handoff.json`; verify fresh actual model, hashes and first useful progress before retiring this owner.
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
