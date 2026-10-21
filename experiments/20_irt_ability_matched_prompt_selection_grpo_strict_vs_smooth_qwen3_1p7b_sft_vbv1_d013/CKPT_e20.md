# CKPT e20: IRT ability-matched prompt selection for GRPO (Azalia's test, IRT version)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/CKPT_e20.md>

**TLDR:** Resume record for experiment 20. Dispatcher: Claude Code session local_268be283 (Mac); worker: tmux `codex-rl4cv-e20-irt-prompt-selection` on skampere1 (Codex gpt-6-astra, ultra, personal profile, full access).

Created: 10-21-2026 11:18 PDT
Last updated: 10-21-2026 15:32:38 PDT

## Goal
- Completed the mandatory failed-gate closure of 20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013.
## What ran
- Adopted four Phase 0a jobs and smoke 48857034; earlier failed smoke attempts 48845232/48855196 included. All seven allocations are terminal; no new experimental phase.
- Codex gpt-6-astra/ultra, full access, sole repository writer; predecessor fenced; implementation-only worker change.
## Results
- Smoke exit 3:0 after 2 updates; max mismatch 22,654/864,717 = 2.61982% >1%. All 256 rollout records retained; IRT treatment effect unmeasured.
- Calibration 4,312/4,312 generated, 0 missing, 0 scored; full denominator retained. Phase 0 7.2358/10 GPU-h; smoke 0.5900/15; total 7.8258/200; API $0; test split closed.
- Final-code make test PASS: 1,415 passed, 17 skipped, 6 subtests, 3 warnings; 370.61 s. Artifact and allocation reconciliation passed.
## Stuck / blocked
- STOPPED at trainer log-probability mismatch gate. Custom optimizer backend deviates from required GRPOTrainer/NeMo; no redesign or gate weakening in this run.
## Next steps
- No experimental continuation. Required closure is complete: results/marker pushed, PR #20 ready/unmerged, Google log and final emails verified; owned verification worktree removed.
- PR https://github.com/brando90/rl-4-code-verification/pull/20 is the sole review PR; do not merge. Exact final evidence: expt_v1/results/receipts/final_accounting.json and phase0_cells_unscored.csv.
- The monitor has observed terminal jobs; do not restart jobs. A new scientific run requires its own prospective protocol.
## Brando to-do
- [p 8/10] Review PR #20 when convenient; no action is needed to close this failed-gate run.

## Log
- 10-21-2026 11:18 PDT -- folder claimed on main; runbook written; dispatching the worker.
- 10-21-2026 11:38 PDT -- dispatch receipt logged (deploy_ed87a5b1900b45d2af6e22c1707cc31e, cc profile, watch-e20); worker checkpoint CKPT_cc-rl4cv-e20-irt-prompt-selection.md created; README dispatch line corrected.
- 10-21-2026 12:40 PDT -- worker change: Claude Fable 5.1 (personal account) -> Codex gpt-6-astra ultra (personal ~/.codex), reason: Claude personal weekly allowance reserved; implementation-only role, no measured model or protocol change. Handoff state: branch e20-irt-prompt-selection pushed; Sherlock jobs 48841018 (Phase 0a, running/pending), 48845232 (trainer smoke, pending) left running; worker checkpoint holds the exact next commands.
- 10-21-2026 13:44 PDT -- Codex start: deploy_50715cf54e614ecf914f0f7da4aae03c, gpt-6-astra ultra, personal ~/.codex; full access verified in process arguments, predecessor fenced. Implementation-only role; no measured model, judge, dataset or protocol change. Live-state discrepancy (newer smoke) recorded in the Codex checkpoint.
- 10-21-2026 13:55 PDT -- Codex takeover verification passed (make test: 1,391 passed, 41 skipped, 6 subtests); calibration 1,792/4,312 rows, trainer smoke 48857034 scoring. Current command and receipts are in the Codex checkpoint.
- 10-21-2026 14:05 PDT -- Adopted smoke update 1 violates the frozen log-probability gate: (21,721 out-of-tolerance + 167 outside-support) / 842,189 tokens = 2.59894%, above 1%. The implementation takes the maximum over smoke updates, so the gate cannot recover on update 2. No pilot/main/evaluation admission. Calibration is 2,304/4,312 generated rows; existing jobs are being reconciled at the stop boundary.
- 10-21-2026 14:09 PDT -- Gate evidence and 128 smoke rollout records preserved; full verification PASS (1,415 passed, 17 skipped, 6 subtests). Google experiment log readback verified. Adopted jobs drain naturally; local 300-second monitor active.
- 10-21-2026 14:13 PDT -- Gate evidence and operational fixes pushed in b0ef925e; draft PR https://github.com/brando90/rl-4-code-verification/pull/20 opened and mergeable. Artifact-only closure collector passed denominator/missing-cell/duplicate fixtures; no scoring or new jobs.
- 10-21-2026 14:14 PDT -- Smoke 48857034 finished both updates and failed the gate (exit 3:0, max 2.61982% versus 1%); final smoke allocation including two infrastructure failures is 0.5900 GPU-h. 256 rollout records and native final check downloaded with SHA-256 verification. Calibration 2,688/4,312 saved; only calibration remains running.
- 10-21-2026 14:19 PDT -- Calibration progress: 2,816/4,312 generations, 0/4 chunks complete, 4 adopted jobs active; Phase 0 allocated 5.1033/10 GPU-h as of 10-21-2026 14:18:15 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 14:19 PDT -- Closure collector and final smoke artifacts verified: make test PASS (1,415 passed, 17 skipped, 6 subtests, 295.48 s). Smoke DONE email delivered (Gmail 1a16051be5758f1a); Google final smoke bullet readback verified.
- 10-21-2026 14:24 PDT -- Calibration progress: 2,944/4,312 generations, 0/4 chunks complete, 4 adopted jobs active; Phase 0 allocated 5.4367/10 GPU-h as of 10-21-2026 14:23:16 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 14:29 PDT -- Calibration progress: 3,168/4,312 generations, 2/4 chunks complete, 2 adopted jobs active; Phase 0 allocated 5.7067/10 GPU-h as of 10-21-2026 14:28:15 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 14:30 PDT -- Chunks 2/3 completed (904/856 cells). Verified actual chunk task counts 179/140/113/107 (1,432/1,120/904/856 cells); split -n l/4 balances bytes, so the old equal-sized comment and earlier chat estimate were wrong. Corrected comment only; inputs unchanged. Chunks 0/1 still active.
- 10-21-2026 14:34 PDT -- Calibration progress: 3,424/4,312 generations, 2/4 chunks complete, 2 adopted jobs active; Phase 0 allocated 5.8739/10 GPU-h as of 10-21-2026 14:33:17 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 14:40 PDT -- Calibration progress: 3,424/4,312 generations, 2/4 chunks complete, 2 adopted jobs active; Phase 0 allocated 6.0400/10 GPU-h as of 10-21-2026 14:38:13 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 14:43 PDT -- Completed-chunk publication verified: make test PASS (1,415 passed, 17 skipped, 6 subtests; 347.52 s). Hourly agents-config refresh unchanged at 217b6ee6; concurrent local changes preserved. Current pushed branch e71576b0, PR #20 remains draft pending final accounting.
- 10-21-2026 14:44 PDT -- Calibration progress: 3,552/4,312 generations, 2/4 chunks complete, 2 adopted jobs active; Phase 0 allocated 6.2067/10 GPU-h as of 10-21-2026 14:43:16 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 14:48 PDT -- Calibration progress: 3,552/4,312 generations, 2/4 chunks complete, 2 adopted jobs active; Phase 0 allocated 6.3733/10 GPU-h as of 10-21-2026 14:48:13 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 14:50 PDT -- Current committed scoring scripts passed isolated retention fixtures: failed compiler evidence retained, real-newline completion receipts, second invocation skips, exactly one archived attempt. Evidence: expt_v1/results/receipts/diagnostic_retention_fixture.json. No GPU or model calls.
- 10-21-2026 14:53 PDT -- Calibration progress: 3,680/4,312 generations, 2/4 chunks complete, 2 adopted jobs active; Phase 0 allocated 6.5400/10 GPU-h as of 10-21-2026 14:53:14 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 14:59 PDT -- Calibration progress: 3,808/4,312 generations, 2/4 chunks complete, 2 adopted jobs active; Phase 0 allocated 6.7067/10 GPU-h as of 10-21-2026 14:58:18 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 14:59 PDT -- Final-code make test PASS: 1,415 passed, 17 skipped, 6 subtests; 3 warnings, 310.61 s. Verified implementation hashes match the tested worktree; final data/publication still awaits terminal calibration receipts.
- 10-21-2026 15:04 PDT -- Calibration progress: 3,936/4,312 generations, 2/4 chunks complete, 2 adopted jobs active; Phase 0 allocated 6.8739/10 GPU-h as of 10-21-2026 15:03:19 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 15:08 PDT -- Calibration progress: 4,064/4,312 generations, 2/4 chunks complete, 2 adopted jobs active; Phase 0 allocated 7.0406/10 GPU-h as of 10-21-2026 15:08:17 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 15:13 PDT -- Calibration progress: 4,160/4,312 generations, 3/4 chunks complete, 1 adopted jobs active; Phase 0 allocated 7.1600/10 GPU-h as of 10-21-2026 15:13:15 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 15:18 PDT -- Calibration progress: 4,312/4,312 generations, 4/4 chunks complete, 0 adopted jobs active; Phase 0 allocated 7.2358/10 GPU-h as of 10-21-2026 15:18:18 PDT; smoke final 0.5900/15. No new phase launched.
- 10-21-2026 15:20 PDT -- All adopted jobs terminal; final artifacts reconciled: 4,312/4,312 generated, 0 missing, all scores unmeasured. Final allocation Phase 0 7.2358/10 GPU-h, smoke 0.5900/15, total 7.8258/200, API $0. No new experimental phase.
- 10-21-2026 15:22 PDT -- Final transfer SHA-256 verified; 4,312 cells/539 tasks/eight samples, no duplicates/missing, 25,821,971 tokens, 940 capped. Full task ID hash matches declared train IDs. Manifest preserves 2,027 remote raw/diagnostic files. Google final bullet readback verified; Phase 0 DONE email delivered (Gmail 1a1608dba9bbe9eb), explicit four-address BCC envelope accepted.
- 10-21-2026 15:24 PDT -- Terminal-publication make test PASS: 1,415 passed, 17 skipped, 6 subtests, 3 warnings, 296.87 s; exact implementation hashes unchanged. Final staged CSV bytes match validated artifacts; secret-pattern/diff checks passed. Preparing final results commit and finish marker.
- 10-21-2026 15:24 PDT -- Immutable final results commit 79d02c82ddd578ebeedc556569195c706b30378c; E20_FINISHED.txt records STOPPED at trainer log-probability mismatch gate and this results revision. Publishing marker before final experiment DONE notification.
- 10-21-2026 15:27 PDT -- Results 79d02c82 and marker d2e3c802 pushed and remote hash verified. PR #20 ready for review, open/mergeable/unmerged; final description read back. Final DONE email delivered once (Gmail 1a16091ef0726ab4), all four explicit BCC envelope recipients accepted. Watcher is healthy and awaits the worker idle state after this turn; finish marker exists.
- 10-21-2026 15:32:38 PDT -- Final receipt-publication make test PASS: 1,415 passed, 17 skipped, 6 subtests, 3 warnings, 370.61 s. Removed owned verification worktree without force after exact committed-copy verification; root dependencies preserved. All failed-gate closure deliverables complete; final notification/cleanup receipts ready for push.
