# CKPT Codex: experiment 20 IRT prompt selection for GRPO

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/CKPT_codex-rl4cv-e20-irt-prompt-selection.md>

**TLDR:** Single-writer continuation of `20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013` under the unchanged runbook. Deployment `deploy_50715cf54e614ecf914f0f7da4aae03c`, Codex gpt-6-astra ultra, personal ~/.codex, skampere1.

Created: 10-21-2026 13:44 PDT
Last updated: 10-21-2026 16:33:45 PDT

## Goal
- Complete post-stop pre-registered Phase 0 CPU scoring and item response theory (IRT) gate G0; trainer stays FAILED.
## What ran
- Dispatcher instruction 10-21-2026 reauthorizes only scoring saved 4,312 generations, Phase 0b/G0, and saved-smoke comparison to experiment 13 v4 T1.
- Codex gpt-6-astra/ultra, deployment deploy_50715cf54e614ecf914f0f7da4aae03c, sole repository writer, full access. Independent helpers: saved-smoke audit and numerical analysis driver.
## Results
- Existing calibration 4,312/4,312 generated, 539 tasks, 0 missing; CPU scoring: strict 6/32 jobs, partial 1/32 jobs; 2016/4312 partial cells logged. Saved-smoke T1 comparison FAIL (195 unsupported update2); exact quantiles unavailable, median bounded <0.01. Trainer FAILED: 22,654/864,717 mismatch tokens (2.61982% >1%).
- Existing allocation 7.8258/200 GPU-h; no new GPU jobs, pilot, trainer or gate changes authorized. API $0; test split closed.
## Stuck / blocked
- Trainer admission remains FAILED; CPU Phase 0 completion is independently authorized and underway.
## Next steps
- [p 10/10] Read /tmp/e20_cpu_monitor/latest.json (300-second monitor session78167, only strict48881657/partial48882641/collect48882642). Pushed55118e16; source files verified; full make test PASS1415/17skipped/6subtests/304.93s. Do not add Slurm polls within60s of monitor.
- [p 10/10] After collection download/hashverify phase0_cpu_tables.tgz, commit4312celltable; run venv/bin/python expt_v1/analyze_phase0_e20.py --repo . --scores expt_v1/results/phase0_cells_e20.csv --out expt_v1/results/phase0b --freeze-dir expt_v1/forecasts --workers4 (use full experiment paths). Finish PR20/G0_FINISHED with AUCinterval/results hash.
- Keep >=60 seconds between Slurm checks; remain inside turn. Preserve E20_FINISHED.txt as trainer-stop history.
## Brando to-do
- none; comparison with experiment 13 v4 T1 is decision input, not a gate change.

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
- 10-21-2026 15:24 PDT -- Immutable final results commit 79d02c82ddd578ebeedc556569195c706b30378c; E20_FINISHED.txt records STOPPED at trainer log-probability mismatch gate and this results revision. Publishing marker before final experiment DONE notification.
- 10-21-2026 15:27 PDT -- Results 79d02c82 and marker d2e3c802 pushed and remote hash verified. PR #20 ready for review, open/mergeable/unmerged; final description read back. Final DONE email delivered once (Gmail 1a16091ef0726ab4), all four explicit BCC envelope recipients accepted. Watcher is healthy and awaits the worker idle state after this turn; finish marker exists.
- 10-21-2026 15:32:38 PDT -- Final receipt-publication make test PASS: 1,415 passed, 17 skipped, 6 subtests, 3 warnings, 370.61 s. Removed owned verification worktree without force after exact committed-copy verification; root dependencies preserved. All failed-gate closure deliverables complete; final notification/cleanup receipts ready for push.

- 10-21-2026 15:49:26 PDT -- Dispatcher explicitly reopened CPU-only pre-registered Phase 0 completion on saved 4,312 generations; trainer remains FAILED. Updated current state, preserved prior stop history, began scoring-wrapper verification and independent saved-receipt/IRT work.

- 10-21-2026 15:52:16 PDT -- CPU jobs submitted: materialize48880517, strict48880518, partial48880519 (normal,c1,16G); source hashes verified, shared score_sherlock.sh bridge fixture passed. START email accepted all four BCC recipients. Full deterministic suite running before launch-record push; dispatcher watchdog now targets G0_FINISHED.txt.

- 10-21-2026 15:53:51 PDT -- Saved smoke comparison finished from receipts only: update2 =22459 finite>0.05+195 unsupported/864717; analogous T1 fails zero unsupported. Median upper bound0.00841008, exactmedian/p99 unretained, p99 criterion undecidable; results/report/parser saved. No gate or trainer change.

- 10-21-2026 15:59:18 PDT -- Attempt1 materialization failed in shell-profile initialization (9s,exit1,no jobs materialized); dependent arrays canceled without executing. Retry2 submitted48881654→48881657/48881660 after environment fix. Full make test1415passed/17skipped/6subtests/300.55s; wrapper,4312cell-join,and diagnostic-hash fixtures PASS. Publishing live CPU launch and saved-smoke results; GDoc and STARTemailreadbacks verified.

- 10-21-2026 16:05:11 PDT -- Preparation complete4312cells/61s; all32strict tasks running. Identified/fixed partialD109 bypasses (local import and nice-prefixed parser); canceled onlyownedpartial48881660 (index0started) andcollector48882176, outputsretained. Helper verifiesfakecapture beforeisolatedretry. Driver analyze_phase0_e20.py integrated, synthetic numerical paths PASS; no realfitsyet. Lastpushc4727d44.

- 10-21-2026 16:08:32 PDT -- Partial D109 fixes passed all compiler/kernel/parser/timeout/hash fixtures; isolated deployment complete. Replacementpartial48882641 andcollector48882642 submitted; previouspartialindex0 canceledafter98s, originaloutputsretained. Active monitor/tmp/e20_cpu_monitor.py session78167 checks300s; root staysinside turn. New fullmake session21533; realIRT waits for scoretable.

- 10-21-2026 16:10:51 PDT -- LivepartialD109 parser/compiler/kernel examples verified with rawstdout/stderr and source hashes, fixedwrapper c03ec54f; firstmonitorobserved55runningtasks,78partialcells. PR20 title/bodyupdated forCPUcontinuation/trainerFAILED. Strictjobskeeporiginaldeployedcapturebytes.

- 10-21-2026 16:12:29 PDT -- FullmakePASS1415passed,17skipped,6subtests,3warnings,307.99s afterD109fix/driverintegration. Publishing numericaldriver/syntheticproofs and realcaptureexamples; allCPUjobs continue under300smonitor, no newGPUjobs/modelcalls.

- 10-21-2026 16:16:27 PDT -- Published CPU diagnostic fixes and registered analysis driver in 55118e1665c892fc3b2da461e5426dc465793805; remote hash verified. Monitor 20261021T231308Z: {'RUNNING': 64, 'PENDING': 1}, strict compiler calls 1253, partial calls 955, partial cells 429/4312. Trainer remains FAILED.

- 10-21-2026 16:24:19 PDT -- Prepared score-summary and result-report renderers; synthetic constant-group bootstrap, missing-cell rejection and read-only report fixtures PASS. Monitor16:23 transport returned HTTP404/exit75 without Slurm data; preserve last known64running/859partialcells and retry at scheduled5min cadence, no submissions. Fullmake session85599 running.

- 10-21-2026 16:28:37 PDT -- CPU monitor 20261021T232751Z: states {'RUNNING': 63, 'COMPLETED': 1, 'PENDING': 1}; strict jobs 0/32, partial jobs 1/32, partial cells logged 1751/4312. Strict/partial diagnostic calls 2435/3305. Collection ready=False; trainer FAILED unchanged.

- 10-21-2026 16:29:11 PDT -- Fullmake PASS1415/17skipped/6subtests/3warnings in304.93s; synthetic summary and report fixtures PASS; staged exact bytes and secret/diff checks PASS. Publishing 1751/4312 partial-cell progress with report tooling; HTTP404 recovered on next scheduled observation, no job resubmission.

- 10-21-2026 16:33:45 PDT -- CPU monitor 20261021T233247Z: states {'RUNNING': 57, 'COMPLETED': 7, 'PENDING': 1}; strict jobs 6/32, partial jobs 1/32, partial cells logged 2016/4312. Strict/partial diagnostic calls 2738/3772. Collection ready=False; trainer FAILED unchanged.
