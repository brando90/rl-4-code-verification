# Matched replay versus expansion continuation checkpoint
**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/CKPT_e08_v3.md>
**TLDR:** Prospective protocol locked; no version-3 training or validation has run.
Created: 10-15-2026 20:22 PDT
Last updated: 10-15-2026 20:33 PDT
## Goal
- Complete replay versus expansion SFT continuations and 17,280 validation cells at four sizes; $0 paid calls.
## What ran
- Session `codex-rl4cv-e08v3-run`, owned checkout `/lfs/skampere1/0/brando9/rl4cv_e08/wt_v3/rl-4-code-verification`; full access, approval never.
- Corpus/manifest identity checked; deterministic schedules/configs/manifest generated; prospective forecast frozen.
- Four-tokenizer NeMo rendering: 2,585/2,585 passed at all four sizes; all four start exports hash-verified; full make test 1,183 passed / 17 skipped.
## Results
- Replay half/full steps 334/658: 2,880,477/5,752,936 loss tokens.
- Expansion half/full steps 335/667: 2,878,589/5,757,776 loss tokens; full mix 684 original + 353 cached + 297 MBPP.
## Stuck / blocked
- 14B eight-device route unavailable now: skampere1 must retain an idle device; skampere2/3 occupied; ilc showaccount is empty. Existing association request already filed; no duplicate sent. Other sizes can proceed.
- Hosted judge milestone deferred; this task permits zero paid calls.
## Next steps
- [p 9/10] Publish locked protocol referencing input commit `27ffa740affb6e40cee53525e8ec06f4640aa105`; send start email and run dry_run.sh via run_with_devices.py.
- [p 9/10] Send RUN START; `python3 experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/run_with_devices.py --n 1 --name dry -- bash experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/train_continuation.sh E 1p7b '{gpus}' dry`.
- Then verify dry-run token counts, loss decrease, export/generation, delete disposable weights, run Phase A then Phase B with validation.
## Brando to-do
- None.
## Resource plan
- A100-80GB compute-bound SFT; estimated up to 80GB/device, dry run 5–15 minutes, production 66/107/123/115 minutes per size-condition plus validation. Host memory/storage verified before launch; no paid API calls.
- Phase A 1.7B on one and 4B on two devices, choosing idle unleased devices under both registry locks; leave device 0 free.
- Recovery owner is this live SNAP session; unattended restart is not yet armed. Temporary checkout cleanup owned here after completion.
## Log
- 10-15-2026 20:22 PDT -- Prepared schedules and forecast; static checks running before lock.
- 10-15-2026 20:33 PDT -- Static checks passed (1,183 tests, all corpus/tokenizer/weight checks); locked recommended defaults before dry run.
