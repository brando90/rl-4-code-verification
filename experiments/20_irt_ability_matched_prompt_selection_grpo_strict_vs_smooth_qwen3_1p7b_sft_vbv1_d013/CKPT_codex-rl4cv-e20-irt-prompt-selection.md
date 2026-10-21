# CKPT Codex: experiment 20 IRT prompt selection for GRPO

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/CKPT_codex-rl4cv-e20-irt-prompt-selection.md>

**TLDR:** Single-writer continuation of `20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013` under the unchanged runbook. Deployment `deploy_50715cf54e614ecf914f0f7da4aae03c`, Codex gpt-6-astra ultra, personal ~/.codex, skampere1.

Created: 10-21-2026 13:44 PDT
Last updated: 10-21-2026 15:24 PDT

## Goal
- Close 20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013 at its mandatory failed trainer gate.
## What ran
- Adopted four Phase 0a jobs and smoke 48857034; earlier failed smoke attempts 48845232/48855196 included. All seven allocations are terminal; no new experimental phase.
- Codex gpt-6-astra/ultra, full access, sole repository writer; predecessor fenced; implementation-only worker change.
## Results
- Smoke exit 3:0 after 2 updates; max mismatch 22,654/864,717 = 2.61982% >1%. All 256 rollout records retained; IRT treatment effect unmeasured.
- Calibration 4,312/4,312 generated, 0 missing, 0 scored; full denominator retained. Phase 0 7.2358/10 GPU-h; smoke 0.5900/15; total 7.8258/200; API $0; test split closed.
- Final-code make test PASS: 1,415 passed, 17 skipped, 6 subtests, 3 warnings; 296.87 s. Artifact and allocation reconciliation passed.
## Stuck / blocked
- STOPPED at trainer log-probability mismatch gate. Custom optimizer backend deviates from required GRPOTrainer/NeMo; no redesign or gate weakening in this run.
## Next steps
- [p 10/10] Finish publication of final records and E20_FINISHED.txt; Google log and Phase 0 DONE email are verified; final experiment DONE email and temporary verification-worktree cleanup remain.
- PR https://github.com/brando90/rl-4-code-verification/pull/20 is the sole review PR; do not merge. Exact final evidence: expt_v1/results/receipts/final_accounting.json and phase0_cells_unscored.csv.
- The monitor has observed terminal jobs; do not restart jobs. A new scientific run requires its own prospective protocol.
## Brando to-do
- [p 8/10] Review PR #20 when convenient; no action is needed to close this failed-gate run.

## Log
- 10-21-2026 13:44 PDT -- Codex takeover verified against live Git, processes and Sherlock; adopted calibration; newer smoke differs from handoff and is under investigation. Native helper `/root/locate_experiment_log` (gpt-5.6-terra/medium) is locating the requested Google experiment log; root remains sole repository writer.
- 10-21-2026 13:49 PDT -- Reconciled two failed infrastructure attempts (48845232: missing SciPy, 56 s; 48855196: context limit, 109 s) and adopted 48857034 (A seed 0, 2 smoke updates, output train/runs/A_s0). Runtime source/launcher captured in expt_v1/results/receipts/runtime_takeover; only trainer code difference is context capacity 16384 -> 20480. Google log located: https://docs.google.com/document/d/1KKKabJJArClVmXcaxfTF5jxk8nF1oHmCH08d44jbqUg/edit .
- 10-21-2026 13:53 PDT -- Restored both frozen external dependencies (scorer 59059a2, prompt/judge code c11b99b) for deterministic tests; no other experiment edits. First full check stopped after exposing three environment/path failures (1,226 passed, 40 skipped); corrected-layout full check launched with CPU-only/thread-limited settings. Smoke START email accepted via uutils SMTP; inbox confirmed Phase 0a START already existed.
- 10-21-2026 13:55 PDT -- Calibration reached 1,792/4,312 saved rows; no scored outcome yet. Corrected smoke accounting to include previously unrecorded job 48855196: 0.2117 GPU-h through 13:46 PDT.
- 10-21-2026 13:55 PDT -- Full make test PASS in the verified compatible-layout worktree: 1,391 passed, 41 skipped, 6 subtests. Runtime source/launcher syntax checks and git diff --check passed. Takeover records ready to commit/push.
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
