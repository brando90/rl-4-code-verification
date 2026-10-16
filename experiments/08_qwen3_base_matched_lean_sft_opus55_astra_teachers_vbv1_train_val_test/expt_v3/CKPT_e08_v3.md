# Matched replay versus expansion continuation checkpoint
**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/CKPT_e08_v3.md>
**TLDR:** Dry run PASS; priority-size production queue launched; validation outcomes pending.
Created: 10-15-2026 20:22 PDT; last updated: 10-15-2026 20:53 PDT
## Goal
- Complete replay versus expansion supervised fine-tuning and 17,280 validation cells at four sizes; $0 paid calls.
## Execution and evidence
- Owner `codex-rl4cv-e08v3-run`; checkout `/lfs/skampere1/0/brando9/rl4cv_e08/wt_v3/rl-4-code-verification`; full access, approval never.
- Input `27ffa74`, lock `18f5217`, publication `77ab4d2`; START email sent to all four requested inboxes.
- All 2,585 examples matched NeMo at all four tokenizers; four step-658 exports hash-verified; full suite 1,183 passed / 17 skipped before lock.
- Replay half/full steps 334/658: 2,880,477/5,752,936 loss tokens; expansion 335/667: 2,878,589/5,757,776.
- [Dry receipt](results/dry_run_v3.json): 8/8 exact step counts, 75,345 loss tokens; fixed-set loss 0.289257→0.252943; 2/2 generated Lean files; disposable weights removed.
- First inference attempt failed on inherited CUDA 12.4 compiler. Retry used CUDA 12.8 and isolated FlashInfer cache; no repeated training steps or scientific-setting changes.
- Persistent terminal `rl4cv-e08-v3-phase-a-recovery`; ordinary scheduler state `/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/phase_a_state.json`.
## Resource plan and blockers
- 1.7B expansion training on GPU 1; first 9/9 observed step token counts matched; 4B waiting for two idle unleased devices plus one idle reserve. Device 0 remains reserved for Experiment 13.
- 14B eight-device route unavailable: skampere1 must retain an idle device; skampere2/3 occupied; ilc showaccount empty (existing association request, no duplicate sent).
- Phase A: four continuations, eight validation rungs, zero-call namespace diagnostics; Phase B: 8B four devices, 14B eight devices when available.
- Runtime uses local disks; shared DFS low-headroom warning recorded. Hosted judge and test evaluation remain deferred.
## Next steps / exact continuation
- [p 9/10] Inspect phase_a_state.json, phase_a_driver.log, phase_a_logs and ckpt/*/driver_logs under the runtime root; track checkpoint exports, publish completed gate/taxonomy tables.
- Scheduler marks child failures NEEDS_RECOVERY and refuses blind restarts with RUNNING identities; this live owner handles recovery and publication. No unattended agent recovery is claimed.
- [p 9/10] Finish Phase A; then run Phase B without changing 14B tensor-parallel semantics. Send DONE only with the actual terminal status.
- Cleanup disposable checkout after all consumers stop and artifacts are published. Brando to-do: none.
## Log
- 10-15-2026 20:22 PDT -- Prepared schedules and forecast; static checks running before lock.
- 10-15-2026 20:33 PDT -- Static checks passed (1,183 tests, all corpus/tokenizer/weight checks); locked recommended defaults before dry run.
- 10-15-2026 20:36 PDT -- START mail sent; dry session rl4cv-e08-v3-dry admitted GPU 1 under shared leases; training steps observed.
- 10-15-2026 20:48 PDT -- Dry inference recovered with CUDA 12.8; complete dry receipt PASS and disposable weights removed; Phase A queue launched.
- 10-15-2026 20:50 PDT -- First production initialization failed before updates because Ray dashboard UNIX socket path exceeded 107 bytes; shortened temp directory, preserved failure logs, verified previous coordinator exited, reconciled FAILED state and restarted.
- 10-15-2026 20:52 PDT -- Production 1.7B expansion verified through step 9; all nine loss-token counts match the frozen schedule.
- 10-15-2026 20:53 PDT -- Updated full suite passed: 1,184 passed / 17 skipped / zero failures in 339.81 seconds.
