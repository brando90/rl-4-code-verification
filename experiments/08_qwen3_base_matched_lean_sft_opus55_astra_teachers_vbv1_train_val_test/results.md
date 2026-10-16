# Experiment 08 results — matched Lean SFT warm start for Qwen3 Base from Valkyrie teachers on the VeriBench V1 train split

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/results.md>

<!-- E08_V3_FINAL_RESULTS -->
## Matched replay versus expansion continuation: expt_v3

**Last updated:** 10-16-2026 12:17 UTC. **INCOMPLETE: 10,800/17,280 primary validation cells.** [Live results and task-bootstrap intervals](expt_v3/results.md), [execution ledger](expt_v3/results/runtime_progress.md). Healthy native schedulers continue the frozen manifest. Final validation, publication and DONE notification remain required. Zero paid experimental calls; test split unopened.
<!-- /E08_V3_FINAL_RESULTS -->

> **Version 2 — PARTIAL / route blocked (10-13-2026):** The matched step-658 extension stopped at its route-controls gate: Valkyrie authenticates, but managed AWS is unavailable for the existing organization. No new generation batch persisted (0/5,328 cells); all missing identities and unresolved forecasts are published in [expt_v2/results.md](expt_v2/results.md). Reused results reproduce exactly, and version 1 below remains unchanged.

**TLDR:** Matched supervised fine-tuning is complete at all four sizes (658 updates and 5,752,936 real loss tokens each), with all 20 trained validation rungs and 25,920/25,920 validation cells complete. The frozen verdict is **PARTIAL**: 8B step 658 and 14B step 334 passed at different fractions; 1.7B and 4B passed no rung. All **10,656/10,656 test cells have complete factors**, using all **4,302/4,302 validated-judge ratings** over 717 files, including all 60 fixed audit files per system. Final results reproduce exactly; services are stopped and the completed study is closed without a follow-on run.

**Status:** DONE (10-11-2026 21:24 PDT; verdict PARTIAL; test split evaluated once after the committed selection)

**Last updated:** 10-11-2026 22:04 PDT (parent verification and monitor retirement)

## Final result and execution closure (10-11-2026)

`08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` completed the original four-size matched supervised fine-tuning study and its once-only VeriBench V1 test evaluation. The validation rule gives **PARTIAL**, with no common passing token fraction: 8B first passes at 5,752,936 real assistant tokens (step 658), and 14B at 2,884,708 (step 334). The 1.7B and 4B models pass no rung, so this study does not establish a matched warm start for reinforcement learning across all four sizes. No new training or selection used test outcomes.

On all 222 test tasks, eight samples each, the selected 8B diagnostic has a Smooth Conjunctive Score for Code verification (SCS4CV; frozen artifact key `SCSC`) of **0.1116 [0.0823, 0.1435]**, versus Base 8B **0.0000 [0.0000, 0.0000]**. The selected 14B diagnostic has **0.0869 [0.0651, 0.1095]**, versus Base 14B **0.0023 [0.0004, 0.0045]**. These are 0–1 scores, with **1,776/1,776 known cells per system**; the full table below retains all three factors, core/IndustrySet results, and the other Base systems. The paired selected-minus-Base differences are **+0.1116 [0.0823, 0.1435]** for 8B and **+0.0846 [0.0627, 0.1077]** for 14B. Intervals use the frozen 10,000 task-bootstrap resamples, seed 0, carrying each task's eight samples together; p-val=n/a (interval estimation only). They describe this one training run, not variation across training seeds. The selected fractions differ, so the two trained sizes are unmatched diagnostics.

All 12 test-judge runs are terminal, with **4,302/4,302 measured ratings** and no missing, duplicate or extra rating identities. The validated ensemble uses GPT-6 Sol high and Claude Opus 5.5 max, three ratings per member/file, then the mean of member medians divided by five. All 361 cells whose stated tests pass are judged, including the Base-4B cell with zero proved-theorem fraction. The fixed audit adds 356 distinct files after four overlaps, giving 717 unique judged files and **60/60 audit files for each of six systems**. Audit coverage on noncompiling files remains diagnostic; it does not bypass compile gating. All 10,656 declared test cells have known official factors, with **zero pending test cells**.

[Joined factor table](expt_v1/results/test_factor_cells.csv) records every system/task/sample, test and proof factors, judged coverage when available, compile-gated formal specification coverage, strict kernel success, audit membership and per-file combined score. The per-file score is diagnostic; the official aggregate remains the geometric mean of the three factor means on the common known cohort. [Receipt summary](expt_v1/results/test_receipts_summary.json) records the audit identities, complete source hashes and repeat variability. The added deterministic summarizer independently reproduces every published factor mean and aggregate; a full rerun of the original analyzer reproduces `test_eval.json` exactly except its timestamp, including every interval and paired difference.

Repeated-rating variability below is the mean within-file sample standard deviation of each member's three raw ratings, normalized from 0–5 to 0–1. It is a descriptive dispersion statistic, not a confidence interval or repeated measurement of the final six-rating ensemble. Independent repeatability of that final ensemble, human agreement on these student outputs, and training-seed variation were not measured. The existing validated judge's provider-returned model/effort fields remain unavailable; frozen request envelopes and returned no-fallback receipts are verified.

| System | Judged files | Ratings measured / declared | Fixed audit | Sol repeat standard deviation | Opus repeat standard deviation |
|---|---:|---:|---:|---:|---:|
| `base14b` | 65 | 390 / 390 | 60 / 60 | 0.0422 | 0.0213 |
| `base_1p7B_e05` | 60 | 360 / 360 | 60 / 60 | 0.0149 | 0.0058 |
| `base_4B_e05` | 62 | 372 / 372 | 60 / 60 | 0.0380 | 0.0354 |
| `base_8B_e05` | 60 | 360 / 360 | 60 / 60 | 0.0346 | 0.0212 |
| `test_sft_14B_f0p5` | 214 | 1284 / 1284 | 60 / 60 | 0.0148 | 0.0043 |
| `test_sft_8B_f1p0` | 256 | 1536 / 1536 | 60 / 60 | 0.0188 | 0.0036 |

The [charge ledger](expt_v1/results/reported_charge_accounting.json) sums raw reported costs once: main teachers including recovery **$5,111.944132**, preflight **$9.2857082**, test judge **$252.8124947**, and judge controls **$3.1320861**, totaling **$5,377.174421 reported** on the frozen Vals-funded route. The separate recovery files duplicate rows already merged into main receipts and are not added again. There are 446 source rows without reported charges, including four original failed Opus preflight ratings and 16 unserved placeholders; unknown charges are not asserted to be zero. Host computation costs were not measured. The 471 main teacher cells without available responses remain in their original 4,312-cell denominator and are not replayed.

The pipeline published final evaluation in `e755b954` and exited normally at 21:27 PDT; its identity was not restarted. Both finished judge services and tunnels are stopped, all ports 9740–9759 are free, the port claim is archived, and the two completed-pipeline watchdog cron entries are retired. Other jobs and cron entries are preserved. Parent subsequently verified final coordinator closure and retired the two remaining five-minute/reboot coordinator entries at 22:02:50 PDT, preserving all seven unrelated cron lines. The explicit `STOP` marker and all recovery evidence remain. Checkpoints, raw data, failed attempts, retry counts, both protocol locks and the 539/135/222 split remain intact.

The shared native checkpoint limitation is unchanged: 16/16 historical reload samples cover embeddings/query projections only, while actual per-rank query/key normalization-state drift remains unmeasured. This adds no historical-production gate and no selective 14B repair. TP2 remains blocked by gradient semantics; Mercury remains unadmitted with its resumed optimizer update and remote integration unfinished. The disposable probe ledger stays **1783.907/1800 seconds spent, 16.093 remaining**, with no fresh allocation. These unused alternatives do not block the already completed historical production route.

Full `make test`: **277 passed, four optional skips in 158.50 seconds**. The added regression cases cover missing required judging, compile gating with zero proofs, diagnostic audit gating, duplicate identities, mismatched rating transport, and served teacher errors without responses. The original test analyzer, scorer, manifests, training recipe and test outcomes are unchanged. The teacher reporting source now uses the response-availability flag; its historical output remains preserved beside the correction receipt. [Coordination and cleanup receipt](expt_v1/results/coordinator_completion_10-11-2026.json). No scientific model call or resource probe was made in this closure phase.

Parent final verification independently matched all 42 newly published files to runtime and rebuilt all 10,656 factor rows and 4,302 rating identities. A separate task-sum bootstrap reproduced all 18 system/scope means, 72 factor/aggregate intervals and six paired comparisons. Final owner closure verifies 24/24 output hashes, 14/14 published files and absence of all 158 recorded identities; its exit zero preceded the unchanged incident deadline. Teacher response counts and the 28-file reported-charge ledger also independently reproduce. [Parent completion verification](expt_v1/results/parent_final_verification_10-11-2026.json). All four experiment08 host watch entries are retired; the parent will remove its desktop heartbeat after publishing this verification.

Earlier dated entries below retain the state observed at their own timestamps.

## Test kernel completion and judge admission recovery (10-11-2026 20:01 PDT)

`08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` has complete kernel-factor coverage for all six declared test systems: 222 tasks × eight samples × six systems = **10,656/10,656 known cells**. All 5,328 new generations and all 24 new score shards are complete. The frozen split, both protocol locks, 20/20 trained validation rungs, selection and test-manifest hashes match; the published PARTIAL selection is unchanged. These counts measure execution completeness, not model quality.

The original pipeline (process 28223/start 24891, boot `839e7dd6-64e1-4a80-9498-31d30b3cc2df`) survived this coordination phase unchanged. Its reboot environment had only system executable paths: `valk` could not start, leaving an `admitting` receipt without a run identifier, while publication failed seven Lean-backed tests because `lake` was unavailable. Two read-only tracker listings returned zero control runs; the old command lookup reproduced `FileNotFoundError` before any client existed. The recovery retained that original admission and evidence and made one identical bounded admission attempt. No served or possibly served request was repeated.

New judge subprocesses now include their own interpreter directory in the executable path and record client-launch failures/timeouts without automatic replay. The experiment-only virtual environment contains a link to the existing compatible Valkyrie wrapper plus `lean`/`lake` launchers pointing to the existing local toolchain. All three downloaded `vb103_judge` files match the frozen bundle, including the Vals-managed credential mapping. The two verified runs are GPT-6 Sol high `7e85dd9e-58d8-4a6c-a4e1-d5b253b37fe7` and Claude Opus 5.5 max `e30e4c47-e2da-4bc1-b0a9-9c9b8fcb8208`, **25 control ratings each**. At 19:59 PDT, the tracker reported both in progress, with eight Sol tasks executing and the remaining tasks pending; no control rating was yet terminal. Test-judge admission required the unchanged control acceptance checks. The pipeline subsequently harvested all 50 ratings and recorded **PASS at 20:03 PDT**: all five oracle, vacuous, shuffled and blank controls passed per member, and four of five half-deletion controls passed per member, meeting the frozen 0.90/0.80 thresholds. These are route checks, not judge–human agreement estimates; p-val=n/a. Reported Vals-funded charges were $0.5931 for Sol and $2.5389 for Opus, $3.1320 total. Provider-returned model/effort fields remain unavailable in the validated bundle; acceptance verifies its frozen request envelope and returned no-fallback receipt. The pipeline then froze and published the 717-file, 4,302-rating test-judge manifest (three repeats per member), with no missing files, and admitted all 12 runs. The selected-8B admissions initially failed before producing run IDs because the 77,804-byte task-ID verification URL exceeded the transport limit (local HTTP 400; tunnel HTTP 414). Read-only tracker inventory showed zero selected-8B runs. The existing slice `1383:2151` returned exactly the same ordered 768 IDs locally and through the tunnel (SHA-256 `c0f139b8c23b3eb9ffa4aadf59448005e84997777547288db2611655c3db672a`). One recorded admission recovery per member then succeeded; all 12 runs cover exactly 4,302 declared ratings. Original commands and failures remain in `prior_launches`; no generation or scientific retry count was reset.

Full `make test` in the **actual pipeline publication environment** passes: **271 passed, four optional skips in 158.26 seconds**, including the launch-failure and no-replay regression checks. The original seven failures remain recorded in the pipeline log. Source changes affect transport execution and failure accounting only. The five-minute coordinator monitor and 15-minute watchdog retain their reboot entries. Formal specification coverage, its fixed audit, official aggregate and final intervals remain pending; kernel factors do not replace the validated judge.

Incident `6ca5cdbf-0415-4a2e-83c9-c0c95c937d20`, attempt 2, verifies native Astra/ultra/full-access/approval-never and parent findings SHA-256 `26ec0a7eb5704790ac730fa5385c3b2e628bd57e9da5a1619622f3f7eac5d8ba`. The 16/16 restored samples cover embeddings/query projections only; native normalization-state deduplication remains a shared pinned-baseline limitation with numerical drift unmeasured. No new historical gate or selective 14B repair was introduced. Mercury remains unadmitted, with **1783.907/1800 seconds spent and 16.093 remaining**; no resource probe ran. All scientific and infrastructure retries remain recorded. [Detailed coordination receipt](expt_v1/results/coordinator_judge_recovery_10-11-2026.json).

## Reboot recovery; all test generations preserved (10-11-2026)

`08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` recovered through its existing reboot watchdog at 16:34:18 PDT. The prior pipeline process 4005026 ended with boot `83765e57…`; the recovered process is 28223/start 24891 on boot `839e7dd6-64e1-4a80-9498-31d30b3cc2df`. The pipeline resumed both unfinished scorers at 16:34:21 PDT. Their retry counters advanced from zero to one under the existing bound; no counter was cleared and no manual competing process was launched.

All three new test generation files contain exactly **1,776/1,776 distinct declared cells**, totaling **5,328/5,328**, with no missing, duplicate or extra generation cells. Base 14B has all eight score shards and 1,776 merged scored cells. The selected 8B checkpoint has five completed shards (1,110 cells), with shards 5–7 active; selected 14B has no finalized shard yet, with shards 0–3 active. Thus **2,886/5,328 new cells have finalized kernel-score artifacts and 2,442 await finalized shards**. The strict system-level completion remains **1/3**. In-progress shard work is not counted as complete. Completed shards were skipped, interrupted directories retained, and all three generation digests were recorded. These counts describe execution completeness, not model quality.

The frozen six-system denominator remains **10,656 test cells**, including 5,328 reused Base cells. Both protocol locks, all 20 completed validation rungs, 25,920/25,920 validation cells, selection and test-manifest hashes are unchanged. Published PARTIAL selection still admits only the 8B step-658 and 14B step-334 diagnostics plus the declared Base systems; no test outcome changes selection. The downstream commands run in the recovered pipeline's environment, its Git access succeeds, all 25 train-control instruction hashes match, and live Lean compiler children confirm actual scoring. Judge route controls, validated formal specification coverage and final analysis remain pending. Kernel factors do not substitute for the validated judge.

Incident `294a3a1b-b6a7-4eb5-be83-4c34b32cada2`, attempt 2, verified native `gpt-6-astra` / `ultra`, `danger-full-access`, approval `never`, stable input hashes and parent finding `26ec0a7e…`. The shared native normalization-state checkpoint limitation remains: 16/16 reload samples cover embeddings/query projections only, with actual normalization-state numerical drift unmeasured. There is no new historical gate or selective 14B repair. Mercury remains unadmitted, and its cumulative probe accounting stays **1783.907/1800 seconds spent**, with **16.093 seconds remaining**; no resource probe ran.

Full `make test`: **268 passed, four optional skips in 153.41 seconds**. No production source or scientific setting changed. The 15-minute watchdog and five-minute coordinator monitor retain their reboot entries; the model phase ends with healthy scoring under ordinary-code supervision. Parent publications through `4e9c51a` were fast-forwarded from a clean tree under the pipeline lock, and the parent's master checkpoint was preserved. [Detailed verified receipt](expt_v1/results/coordinator_reboot_recovery_10-11-2026.json).

## Full validation and published PARTIAL selection; test running (10-11-2026)

`08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` has all 20 trained validation rungs complete. Independent cell joins verify all 24 validation systems (20 trained plus four Base), each with 135 tasks × eight samples = 1,080 distinct known cells: **25,920/25,920**, with no missing or extra cells. Recomputed extraction, token-cap and mixed-task counts match every published gate. The rule in PROTOCOL § 9 gives PARTIAL, with no common passing fraction; test outcomes cannot revise this selection.

| Selected diagnostic checkpoint | Real assistant tokens | Extracted / 1,080 | Capped / 1,080 | Tasks with both passing and failing samples / 135 (share; Wilson 95%) |
|---|---:|---:|---:|---|
| 8B, step 658, fraction 1.0 | 5,752,936 | 974 | 106 | 32 / 135 (0.2370; [0.1732, 0.3154]) |
| 14B, step 334, fraction 0.5 | 2,884,708 | 975 | 105 | 30 / 135 (0.2222; [0.1603, 0.2995]) |

The prespecified gates require at least 972 extracted cells, at most 108 capped cells and at least seven mixed tasks, with every cell known; p-val=n/a (point-estimate gates, no hypothesis test). Neither 1.7B nor 4B passes all gates at any rung; even their final checkpoints miss both formatting gates (1.7B: 897 extracted / 184 capped; 4B: 946 / 134, each of 1,080). Full rung-level counts remain in the validation table below. The selected fractions differ, so they do not establish cross-size reinforcement-learning readiness.

Selection commit `089a323` was pushed at 09:45:34 PDT, test-manifest commit `bee4580` at 09:49:10 PDT, and the first test launcher started at 09:49:11 PDT. A fresh remote query confirms publication; all selection, ladder, task-list and selected export-manifest digests agree. The actual admission guard accepts the three declared new-generation systems and rejects an unselected 4B checkpoint. The frozen test denominator is **10,656 cells**: six systems × 222 tasks × eight samples, comprising 5,328 new cells and 5,328 reused Base cells. No test outcome was used for selection.

The original pipeline process 4005026/start 8095062 is unchanged. Trained 8B test generation holds device 2; trained 14B and Base14B wait for idle devices, with other users occupying the remaining devices at 09:56 PDT. At this observation, **0/3 new systems are fully scored**. The downstream command entry points and pinned Lean 4.22.0 execute, and all 25 stored train-control instruction hashes match. Judge route controls, validated formal specification coverage and final test analysis remain pending; kernel factors alone do not supply that coverage. The five-minute coordinator monitor and 15-minute watchdog retain their reboot entries and ordinary-code supervision.

Incident `9618422d-1484-4d67-86ce-d876278664e5`, attempt 2, verified native `gpt-6-astra` / `ultra`, full access and approval never; stable handoff hashes and the parent's `26ec0a7e…` finding were acknowledged. Its 16/16 restored samples cover embeddings/query projections only. Native query/key-normalization checkpoint deduplication remains a shared pinned-baseline limitation with numerical drift unmeasured, without a new historical gate or selective 14B repair. Mercury remains unadmitted; 1783.907/1800 probe seconds are spent and 16.093 remain. All retries and failed probes are preserved. No production source or scientific setting changed. Full `make test`: **268 passed, 4 optional skips in 207.61 seconds** after applying the existing host test environment; initial environment-only failures are retained in the receipt. [Detailed coordination check](expt_v1/results/coordinator_test_start_10-11-2026.json).

## Five 14B exports verified; validation running (10-11-2026)

`08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` completed the production launcher at 02:14:55 PDT. All five 14B checkpoints (steps 82, 164, 334, 497 and 658) have complete Hugging Face exports: **50/50 listed file digests match**, including five distinct weight digests. Every referenced native weight/optimizer extent is also present and in bounds across eight shards at each rung. All four 658-step training logs agree exactly on per-step tokens, cumulative tokens and logged learning rates. The final 1,316 consumed slots comprise 1,315 real examples plus one fully loss-masked padding slot. These execution checks do not establish validation improvement or lossless per-rank normalization-state restoration.

The original pipeline PID 4005026/start 8095062 released its training lease and launched validation fractions 0.125 and 0.25 on devices 0 and 1 at 02:15:34 and 02:17:44 PDT. Both exports loaded in vLLM and generation is progressing. Fractions 0.5, 0.75 and 1.0 await the existing two-generator concurrency limit; no resource recipe changed. The 15 completed trained rungs and reused baselines still account for 20,520 known validation cells. All five trained-14B cohorts remain unscored, so **5,400 cells stay unknown** and no checkpoint has been selected.

Incident `adac6942-e4d9-493e-b141-9acc43540db6` acknowledged the stable handoff and parent findings (`26ec0a7e…`) with verified native Astra/ultra/full-access/never settings. The shared normalization-state checkpoint limitation remains documented, with numerical drift unmeasured. Mercury is still unadmitted; its ledger remains 1783.907/1800 seconds spent, without a new allocation. The parent’s newly published records were integrated while preserving the pipeline’s uncommitted artifacts byte for byte and leaving the parent master checkpoint untouched by owned edits.

The downstream commands, pinned Lean toolchain, live pipeline Git access and monitor executable hashes check out. An actual prospective test-admission check rejects `No committed, admitted selection`. Formal specification coverage still requires the validated judge and its pending route controls. Full `make test`: **268 passed, four optional skips in 204.22 seconds**. No production source or scientific setting changed. [Complete export/training and coordination receipt](expt_v1/results/coordinator_validation_start_10-11-2026.json); [full 14B training log](expt_v1/results/train_logs/sft_14B_steps.csv).

## Full 14B training complete; checkpoint exports running (10-11-2026)

All five segments exited zero. Independent read-only verification found exactly 658 completed update records and 658 finite TensorBoard loss, learning-rate and token records. Cumulative token counts and logged float32 learning rates match the frozen recipe at every update; per-step token counts and rates also match each of the completed 1.7B, 4B and 8B runs. The final metadata records 658 total updates, 1,316 samples and 5,752,936 valid tokens. Its `step: 0` field is the native within-epoch cursor, separate from the total update count.

The final native checkpoint has all referenced weight/optimizer storage extents present and in bounds across eight shards each. Full payload hashes and numerical restoration fidelity were not measured; the shared query/key normalization-state limitation below remains unchanged. At 01:43 PDT, the first of five exports was actively writing, with its weight file growing from about 26 GB to 38 GB between observations. Exports are not yet complete, and trained-14B validation remains 0/5 rungs. The existing pipeline will continue exports, full validation and frozen selection before admitting held-out evaluation. [Verified training and export observation](expt_v1/results/parent_training_complete_10-11-2026.json).

The prior Vals coordinator phase exited zero at 00:37:26 PDT. Parent verified all 15 output hashes and five published file hashes; the recovery monitor returned ARMED with no active model owner. This phase completion is separate from completion of the scientific study.

## Verified coordinator continuation and second 14B rung (10-11-2026)

The recovered Vals coordinator (`gpt-6-astra`, `ultra`, full access, approval `never`) acknowledged incident `53cd99c4-2406-4b25-8933-d6cd76c0a6d1` and produced an immutable first-action check. All stable handoff hashes match. The original pipeline PID 4005026/start 8095062 and scientific driver PID 456540/start 20305429 remain adopted without restart. The monitor’s five-minute cron, reboot entry, attempt history and original 01:10:02 PDT coordination deadline are preserved.

Segment 164 exited successfully at 00:27:28 PDT. Both saved native checkpoints (82 and 164) have all referenced weight/optimizer extents present and in bounds. The log contains 164 consecutive updates and zero token-schedule or learning-rate mismatches against the completed 1.7B, 4B and 8B runs. Full payload hashes were not recomputed. The next segment target, 334, is not a completed-update count. Exports occur after all five segments, followed by validation. [Detailed receipt](expt_v1/results/coordinator_training_progress_10-11-2026.json); [partial per-step log](expt_v1/results/train_logs/sft_14B_partial_step164_10-11-2026.csv).

The latest parent finding (`26ec0a7e…`, full digest in the receipt) is verified and acknowledged: the 16/16 Mercury reload samples cover embeddings/query projections only. Native deduplication of query/key normalization weights and optimizer states is a shared pinned-baseline limitation; actual per-rank numerical drift was not measured. It adds no new historical-production gate and authorizes no selective 14B repair. Mercury still lacks its completed resumed optimizer update and remote-production integration. The probe ledger remains 1783.907/1800 seconds spent (16.093 seconds left); no fresh allocation or new probe was made.

All 15 completed trained validation rungs plus Base 14B pass the existing artifact checks; reused baselines bring the total to 20,520 known cells. Each trained-14B rung has **0/1,080 known cells**. The table’s missing outcomes are shown as unknown; any zero placeholders in historical incomplete analyzer records do not represent measured failure rates. Selection still requires all 20 trained rungs, and the actual test-admission check rejects `No committed, admitted selection`. Formal specification coverage still requires the validated judge. No scientific generation, judging or held-out evaluation was launched by this coordination phase.

Full `make test` passed: **268 tests, four optional skips in 207.88 seconds**. The initial environment failures and the corrected command are retained in the receipt; no source, recipe or acceptance criterion changed. Git publication uses the existing approved credential through a readable, command-scoped path.

## First scientific 14B rung (10-11-2026)

The existing pipeline acquired all eight A100 devices and started the historical eight-way tensor-parallel recipe on 10-10-2026 at 23:58:19 PDT. The first segment exited successfully at 10-11-2026 00:11:42 PDT. Native `training_info.json` records step 82, 164 consumed samples and 720,775 valid tokens, matching the frozen first rung. Parent and an independent read-only worker checked the logs and checkpoint metadata. All referenced weight and optimizer storage extents exist inside the eight shards of each type; full payload hashes were not recomputed. This is structural evidence, not proof of lossless per-rank normalization-state restoration; the shared baseline limitation below remains documented.

The next segment is initializing from the native checkpoint. Hugging Face exports follow all five training segments, so no trained-14B validation has started. The five missing validation cohorts remain 0/1,080 each; unmeasured outcomes are unknown rather than zero. The aligned item-by-factor outputs will retain those cells until measured. No selection or test calls were admitted.

The training-start event exposed a separate coordinator-monitor failure: the eligible Vals candidate could not prepare its handoff because the cron process could not read its home-directory policy clone. The scientific pipeline remains healthy. Parent is repairing the policy path and same-attempt pre-launch continuation within incident `53cd99c4-2406-4b25-8933-d6cd76c0a6d1`, whose original deadline is 10-11-2026 01:10:02 PDT. Existing attempts, scientific retries and probe budgets are preserved. Evidence: [training snapshot](expt_v1/results/training_progress_10-11-2026.json) and the parent master checkpoint.

## Smaller-device layout investigation (10-09-2026)

The historical eight-device configuration is one admitted route, not a scientific prerequisite. Two A100s with CPU state offload fit and executed optimizer updates, but changing tensor parallelism changes the pinned query/key-normalization gradient semantics. Mercury2's eight 16-GiB A4000s preserve the eight tensor partitions; whole-decoder checkpointing completed two full-length updates, with 124.020/121.506-second training times and peak reserved memory14.471GiB/device. Its checkpoint restored16/16 sampled parameter hashes, but the cumulative probe boundary stopped the resumed update after one backward per rank. **At the close of that 10-09-2026 phase, no alternative was admitted and 14B production was 0/658.**

The phase used1783.907/1800 accelerator-window seconds, preserving every failed attempt and all scientific retries. All probe leases/children are released. The pipeline now reads hash-verified layout admissions; it was safely reloaded while idle and can launch the historical route when available. The final survey has only skampere1 devices1,2 idle. Completed study evidence and all validation/selection/test settings remain unchanged. [Full decision, measured costs, numerical limits and exact receipts](expt_v1/results/layout_10-09-2026/README.md).

## Coordinator event repair (10-09-2026 14:47 PDT)

The first cron check after the resource owner finished reopened an already-serviced event: its long-running parent used the earlier event schema, while the owner computed the new schema containing the admission-registry hash. The monitor now honors the verified completion key and lets the next tick detect genuinely new events. Regression tests reproduce the failure and verify completion deduplication, new-event dispatch and preservation of archived attempts. Published fix: `6025ecc`, merged `aa3e7b2`; parent full suite **208 passed, five skipped**. The execution host passed all **24 monitor tests**, and an actual post-repair tick returned **ARMED** without starting a model owner.

At 14:47:34 PDT the parent verified the completed phase and all 14 immutable output hashes, then reconciled the duplicate incident under monitor, owner and pipeline locks. Both failed account-read attempts remain archived as `SUPERSEDED_BY_VERIFIED_COMPLETION`; no replacement model owner or scientific call was launched. The original pipeline identity is unchanged, and the monitor returned to ARMED. A separate native diagnostic at 14:45 confirmed the personal account eligible with 62% weekly allowance remaining; this does not erase the earlier transient read failure. Private receipts: `$WORK/owner_recovery/monitor_diagnostic_10-09-2026/`.

The continuation brief now requires the next owner to read and acknowledge the parent's updated checkpoint findings. Sampled embedding/query-projection agreement is not proof of lossless per-rank normalization-state restoration. The native deduplication limitation also belongs to the historical implementation, so it is documented without selectively changing 14B or imposing a new retrospective gate. At that 10-09-2026 repair, scientific counts were **0/658 14B updates**, **15/20 trained rungs**, **20,520/25,920 validation cells**, with **5,400 missing**.

## Earlier coordinator recovery (10-09-2026 13:21 PDT)

Personal Codex `gpt-6-astra` / `ultra` adopted the original healthy pipeline after the Claude coordinator exhausted its allowance. The Stanford candidate could not provide required permissions and is excluded; personal and Vals remain independent evidenced routes. Full access and approval `never` are effective. Artifact checks confirm 15 / 20 trained checkpoints and 20,520 / 25,920 full validation cells (17,280 new + 3,240 reused); all 5,400 missing cells belong to trained 14B. No current lease or compute child exists. The eight-device wait is preserved. Selection, new test generation and judging remain pending. Host receipts: `$WORK/owner_recovery/{ack,artifact_check}.json`. An ordinary-code coordinator recovery monitor is installed on this host at five-minute cadence and reboot, using fixed personal/Vals candidates with fresh native account reads, one-writer locks, finite attempts, process identities and verified handoff/output hashes. The first cron invocation observed the current owner; provider failover is prepared, while failure handling was tested with harmless local fixtures. Existing pipeline/watchdog entries and retries are preserved.

The recovery fixes run in newly launched downstream processes: the test launcher requires the exact published selection and test manifest plus complete validation; ambiguous judge admissions cannot be replayed; route controls require returned request-envelope evidence and every declared rating; a missing rating leaves formal specification coverage unknown. The validated bundle does not expose provider-returned model/effort fields, so that identity evidence remains unavailable. No new teacher, test or judge call was made during this phase. Full checks: **192 passed, 4 skipped**, plus actual pre-selection rejection without test output. Published implementation: [4fa224e](https://github.com/brando90/rl-4-code-verification/commit/4fa224e92c038b94f917b531fb8fd2506471c2ab), merged to main as 03520a5 with the same full test result. The monitor has observed this owner in three scheduled checks and will return to waiting after the coordinator exits. Details and receipt pointers: [recovery record](expt_v1/results/coordinator_recovery_10-09-2026.json) and [continuation brief](expt_v1/coordinator_recovery.md).

## Phases

| Phase | Status | Evidence |
|---|---|---|
| D-013 split | DONE (10-07-2026) | `expt_v1/results/split/` (manifest SHA-256 `157ce781…`), `tests/test_splits.py` |
| Base models on the splits (experiment 05 receipts) | DONE (10-07-2026) | `expt_v1/results/base_qwen3_e05_on_d013_splits.json` |
| Token-budget inputs | DONE (10-07-2026) | `expt_v1/results/token_budget_gold_lengths.json`, `token_budget_e103_teacher_yields.json` |
| Lock 1 preflight and lock | DONE: lock 1 LOCKED 2026-10-08T00:16 UTC at `6e6890f` (lock commit `cc86ec0`); amendment A1 (opus55 effort xhigh) at `bc27e1c`; live preflight passed (8 locked cells + 4 diagnostic cells, 10-07/10-08-2026) | `expt_v1/results/pack_check.json`, `scorer_adapter_check.json`, `template_check.json`, `deployment_e08.json`, `route_identity_e08.json` |
| Teacher runs (4,312 cells) | DONE (10-08-2026): 4,312 / 4,312 terminal; response available 3,841; unavailable 471; kept 2,004; charges 5,111.94 USD | `expt_v1/results/runs_state.json`, `results/receipts/preflight/` |
| Scoring, screen, SFT set S | DONE (10-08-2026): 1,315 examples over 476 tasks, 5.75M assistant tokens | `expt_v1/results/scored_cells.jsonl`, `generated_lean_screen.json`, `sft_set_manifest.csv`, `sft_set_stats.json`, `teacher_analysis.json` |
| Lock 2 preflight and lock | DONE (10-08-2026): lock 2 at `d1c101a` (lock commit `9995821`); dry run PASS (val loss on the fixed 16 examples 0.6283 → 0.5886, loss tokens = rendered spans, export loads in vLLM); framework NeMo RL | `expt_v1/results/sft_schedule.json`, `sft_config_diff.md`, `dry_run_e08.json` |
| Matched SFT, 4 sizes × 5 checkpoints | DONE: 658 steps and 5,752,936 real loss tokens per size; all 20 exports complete; all 50 listed 14B export file digests verified | `expt_v1/results/train_logs/`, `expt_v1/results/coordinator_validation_start_10-11-2026.json` |
| Validation ladder and selection | DONE: 20/20 trained rungs, four Base systems and 25,920/25,920 known cells. Published PARTIAL selection: 8B step 658; 14B step 334; no common passing fraction | `expt_v1/results/validation_ladder.json`, `selection.json`, `coordinator_test_start_10-11-2026.json` |
| Test evaluation | DONE: 10,656/10,656 known factor cells; 4,302/4,302 test ratings over 717 files; 60/60 audit files per system; final analysis reproduced | `expt_v1/results/test_eval.json`, `test_factor_cells.csv`, `test_receipts_summary.json` |

## D-013 split

| Split | All | Core | IndustrySet |
|---|---:|---:|---:|
| train | 539 | 369 | 170 |
| validation | 135 | 93 | 42 |
| test | 222 | 152 | 70 |
| total | 896 | 614 | 282 |

- **Groups:** 664 groups (434 single tasks, 229 pairs, 1 group of 4). They were linked by 230 security safe/vulnerable pairs, 2 exact Python copies, 4 exact gold-Lean copies, 1 near Python copy and 1 near gold-Lean copy.
- **Gold mapping:** all 896 Python tasks map to exactly one gold Lean file. The task ids are identical to experiment 05's 896.
- **Leakage check:** the largest Jaccard between tasks in different splits is 0.640 for Python (`realcode_set__1_insort_right` train vs `realcode_set__3_insort_left` validation) and 0.610 for gold Lean, both below the 0.70 grouping threshold.

## Baseline: Qwen3 Base on the D-013 splits (experiment 05 receipts, G = 8, zero new calls)

`kernel_binary` per task over 8 samples; mixed = between 1 and 7 passes. The 95% interval is Wilson's, with the task as the unit.

| Model | Split | Tasks | Mixed share [95%] | pass@8 share | IC_tests mean pass rate |
|---|---|---:|---:|---:|---:|
| Qwen3-1.7B-Base | validation | 135 | 0.000 [0.000, 0.028] | 0.000 | 0.0009 |
| Qwen3-4B-Base | validation | 135 | 0.022 [0.008, 0.063] | 0.022 | 0.0046 |
| Qwen3-8B-Base | validation | 135 | 0.000 [0.000, 0.028] | 0.000 | 0.0000 |
| Qwen3-1.7B-Base | test | 222 | 0.000 [0.000, 0.017] | 0.000 | 0.0000 |
| Qwen3-4B-Base | test | 222 | 0.005 [0.001, 0.025] | 0.005 | 0.0011 |
| Qwen3-8B-Base | test | 222 | 0.000 [0.000, 0.017] | 0.000 | 0.0000 |

Every mixed-share point estimate is below experiment 08's 0.05 readiness gate (experiment 01 G1's failure boundary, not its 0.20 strong-pass boundary); the 4B validation interval crosses 0.05, so this is not an uncertainty-adjusted rejection. p-val=n/a (no hypothesis test). Qwen3-14B-Base is not measured yet; PROTOCOL § 9 generates it.

## Token-budget inputs (zero calls, Qwen3 tokenizer)

| Quantity | Train | Validation | Test |
|---|---:|---:|---:|
| Gold Lean tokens, mean (median) | 2,312 (1,657) | 1,918 (1,718) | 1,995 (1,648) |
| Experiment 103 Opus 5 max single call, tasks passing the kernel proxy | 251 / 539 | 62 / 135 | 99 / 222 |
| … mean tokens of its passing files | 5,104 | 4,998 | 5,042 |
| Experiment 103 Astra high single call, tasks passing | 261 / 539 | 68 / 135 | 118 / 222 |
| … mean tokens of its passing files | 2,731 | 2,602 | 2,809 |

These historical validation/test summaries were inspected before the prospective protocol locks; the holdout claim concerns newly selected trained checkpoints, not unseen historical outcomes. Token `median` fields use the upper middle observation for even counts.

The kernel proxy is IC_tests = IC_proofs = 1 with at least one theorem and one `example`, without the vacuity check. Either teacher passes 362 of 539 train tasks; both pass 150. The estimate in [README.md](README.md#how-many-sft-tokens-estimate-before-any-call) is about 1,100–1,300 SFT examples, or about 4–5M assistant tokens per model.

## Light QA before dispatch (requested by Brando, one round)

- **Reviewer:** Codex CLI 0.161.0, model `gpt-6-astra`, reasoning effort `ultra`. This was a cross-company review of a Claude-built change, with role `acceptance` for the design.
- **Scope:** `ab650c3..4b66ca1` (commits `a17b899` and `4b66ca1`), meaning the split code, tests and artifacts, the D-013 / D-015 rule edits, and this experiment's design, protocol and runbook. Zero model calls, no Valkyrie runs, no GPUs.
- **Verdict block:**

  ```
  VERDICT: FIXED
  CRITICAL_ISSUES: 0
  MAJOR_ISSUES: 10
  FIXES_APPLIED: 14
  STRUCTURAL: IMPROVED
  SUMMARY: Corrected experiment 08's protocol, runbook and artifact validation while preserving the split and earlier experiment protections. Deterministic checks pass.
  ```

- **Major findings fixed (by the reviewer):**
  1. FSC judging covers every IC_tests = 1 cell on one common cohort (D-009), with D-102's 60-file audit and route controls.
  2. Screens cover full assistant text.
  3. The SFT-set priority and filter order are deterministic.
  4. An actual non-vacuity check is required (the stock adapter defaults it to zero).
  5. Locks precede live preflight and the dry run.
  6. Seed, scheduler, odd final batch and loss normalization are explicit.
  7. Incomplete gate inputs block selection.
  8. Worker paths are isolated under the experiment's work root.
  9. The input readers reject duplicate or incomplete rows.
  10. The split reproduction test fails, instead of skipping, on a dataset mismatch, and checks all seven artifacts.
- **Split unchanged:** all seven split artifacts reproduce byte for byte, and the manifest SHA-256 is still `157ce781…`.
- **Builder follow-ups after review (master, 10-07-2026 16:42 PDT):**
  - Reverted an out-of-scope title header the reviewer added above `CLAUDE.md`'s agents-config bootstrap lines.
  - Aligned PROTOCOL § 8 with Varun's committed config: his `LinearLR`-then-cosine schedule form, seed 20260830, SFT-time validation and Weights & Biases off.
  - Committed Varun's config files with provenance (`expt_v1/configs/`), so the worker needs no access to `skampere3`.
  - Added an upper scenario to the token estimate: about 1,200–1,600 examples and 4.5–6.5M assistant tokens.

## Worker setup and lock-1 zero-call checks (SNAP worker, 10-07-2026)

Host `skampere1`, work root `/lfs/skampere1/0/brando9/rl4cv_e08`, own clone on `main`. Zero model calls in this section.

| Check (PROTOCOL § 12, before lock 1) | Result | Evidence |
|---|---|---|
| `make test` with the pinned VeriBench root | 112 passed, 1 skipped (the skip is experiment 07's `scipy` test); all 13 split tests ran, including the reproduction test | `.venv`, `external/` at the three pins |
| Served pack (539 train tasks) | PASS: 539 / 539 instruction hashes equal experiment 05's receipts; no `.lean`, `solution/`, gold or theorem text outside `instruction.md`; system prompt `dc051963…`, addendum `a7a0fc1b…` | `expt_v1/results/pack_check.json` |
| Held-out screen of system prompt, addendum and 539 instructions vs validation + test Python and gold Lean (714 files) | 0 exact, 0 near hits; max word-5-gram Jaccard 0.177 (an instruction vs a validation Python program) | same file |
| Tokenizer template (control task, 4 sizes) | PASS: evaluation prompt is a byte and token-id prefix of the full render; loss span = `<think>\n\n</think>\n\n` + response verbatim + `<|im_end|>\n`; 1.7B / 4B / 8B / 14B tokenizer files and chat template byte-identical; 3,630 prompt tokens, 87 assistant tokens on the control | `expt_v1/results/template_check.json` |
| Scorer adapter (frozen scorer `59059a20`, private grading project, Lean v4.22.0 + Mathlib `79e94a09`) | PASS on 14 files: 3 train gold kept (IC_tests = IC_proofs = 1, `kernel_binary` 1); empty → `no_lean`, non-compiling → `no_typecheck`, `sorry` → `unproved_theorem`; the compiling `True` control → `vacuous_theorem` despite perfect kernel factors; 5 experiment-103 Astra train files reproduce experiment 103's IC_tests / IC_proofs / theorem and axiom counts exactly | `expt_v1/results/scorer_adapter_check.json` |
| Service | `rl4cv-e08-vbv1-train` on `127.0.0.1:9740` (claimed block 9740–9759) behind a bearer-protected cloudflared tunnel; health 200 with the bearer and 401 without, locally and through the tunnel; per-task limit read back 6,600 s = 2 × 3,000 + 600 | `expt_v1/results/deployment_e08.json` (URL and bearer only under `$WORK/private/`) |
| Route identity (D-108) | PASS: Valkyrie environment `bench`, log group `fellows/brando-miranda`, bucket `fellow-brando-miranda` (organization BrandoMiranda-fellow); the gateway key never reached the host (secret mapping `fellows/brandoModelGatewayApiKey` by name); installed `vb103_single_call` bundle = experiment 103's frozen hashes (`single_call.py` `6e1a9b0d…`); retry bound verified: at most 2 requests per cell, re-send only after HTTP 429/5xx, timeouts never replayed; payer Vals; 0 prior runs on this benchmark | `expt_v1/results/route_identity_e08.json` |
| Registry dump (10-07-2026, 454 models, SHA-256 `572c742f…`) | `anthropic/claude-opus-5-5-no-fallback`: fallback list empty (the only Opus 5.5 selector without fallbacks), default compute effort `max`, max_tokens 128,000; `openai/gpt-6-astra-max`: the highest served effort (max > xhigh > high > medium > low) | same file |

**Finding (gold references and the keep rule):** 403 of the 896 pinned gold references use `native_decide`, mostly in `example`s but sometimes inside named theorems, where the frozen scorer counts the theorem as not kernel-proved (IC_proofs 0.5 on the two aerospace diagnostics). The adapter check therefore picks its 3 gold files among references that never use `native_decide` and scores the first 2 that do as diagnostics (`forbidden_axiom`, `kernel_binary` 0). The keep rule for teacher files is unchanged.

## Live preflight (PROTOCOL § 12.7; 8 locked cells + 4 diagnostic cells)

| Teacher | Cells | Served | Finish | Lean collected | Scored | Independent samples | Charge (USD) |
|---|---:|---:|---|---:|---|---|---:|
| Astra (`openai/gpt-6-astra-max`, reasoning max) | 4 | 4 | `stop` ×4 (2.3–3.8k output, 17–33k reasoning tokens, 8–16 min) | 4 | 4 × `no_typecheck` (IC_tests 0; 6–9 theorems stated); prompt hashes = pack; extraction consistent 4 / 4 | yes (response hashes differ on both tasks) | 5.78 |
| Opus 5.5 (`anthropic/claude-opus-5-5-no-fallback`, compute max) | 4 | 4 | `model_error` / `MaxOutputTokensExceededError` ×4 after ~18 min | 0 | 4 × `no_lean` | not testable (no responses) | 0.00 recorded |
| Opus 5.5, compute **xhigh** (diagnostic, amendment A1) | 4 | 4 | `stop` ×4 (5.1–9.0k output, 22.8–43.3k reasoning tokens, 4–7 min) | 4 | 4 × **kept** (IC_tests = IC_proofs = 1, 10–20 theorems stated, none vacuous); extraction consistent 4 / 4 | yes (both tasks) | 3.51 |

- **Finding (10-07-2026, worker):** the gateway caps this model's output at 128,000 tokens (registry `properties.max_tokens`). Experiment 103's Opus 5 max run spent a median 76,840 reasoning tokens per cell and 117 / 895 cells hit the same error; experiment 02A v3's Fable 5.1 max preflight failed the same way. Opus 5.5 at max effort therefore cannot deliver files on most tasks under the locked settings, and the 2,156 main calls would be wasted.
- **Decision (agents-config Rule 57, flagged for Brando):** Opus main runs were not admitted at `max`. The tagged diagnostic preflight at `compute_effort xhigh` completed and passed end to end, so PROTOCOL § 3 was amended for `opus55` to `xhigh` (lock-1 amendment A1, version 1.1, `LOCKED 2026-10-08T00:55:51Z at bc27e1c`) before any Opus main call; the Opus main runs were then admitted. Astra's settings are unchanged; its 4 main runs (2,156 cells) were admitted at 17:44 PDT under the lock.
- **Harvest note:** `valk run results` answers "tracker returned a malformed response" on this tracker (as in 02A v3 and experiment 01); the run-output benchmark JSON carries the same per-task rows with the service-collected bytes, and the per-task `agent_output.tar.gz` carries `receipt.json` + `response.txt`.
- **NeMo RL infrastructure smoke (not scientific):** NeMo RL 0.4.0 at `c751f811` built with `uv` (worker venvs built at first launch); Qwen3-1.7B-Base, 4 synthetic examples, 2 steps on GPU 0 (21.7 GB): loss 2.73 → 2.15, `step_2` checkpoint saved with optimizer, scheduler and dataloader state, exported to Hugging Face format (`qwen3`). All four Base snapshots hash-verified against the hub (`expt_v1/results/model_weights_e08.json`).

## Base 14B on the validation split (generated here, PROTOCOL § 9; zero model calls)

Qwen3-14B-Base `0b0bd373…`, experiment 05's exact sampling, 135 tasks × 8 = 1,080 cells (frozen manifest `expt_v1/results/ladder_manifest_base14b.json`), all 1,080 known.

| Gate | Value | Threshold | Pass |
|---|---:|---|---|
| (a) extraction | 1,010 / 1,080 = 0.935 | ≥ 0.90 | yes |
| (b) capped at 12,288 tokens | 77 / 1,080 = 0.071 | ≤ 0.10 | yes |
| (c) `kernel_binary` mixed-group share | 7 / 135 = 0.052, Wilson 95% [0.025, 0.103] | ≥ 0.05 | yes (at the boundary) |

Diagnostics: pass@8 share 0.052, all-pass share 0, mean pass rate 9 / 1,080 = 0.0083, IC_tests rate 0.0083, mean generated tokens 2,001, within-task diversity (mean pairwise word-5-gram Jaccard) 0.144; 5 cells had a vacuous theorem and are not counted as passes. p-val=n/a (prespecified point-estimate gate). Note: Base 14B meets the readiness gate without any SFT, unlike Base 1.7B / 4B / 8B on experiment 05's receipts (0.000 / 0.022 / 0.000); the selection rule in PROTOCOL § 9 applies to the trained checkpoints and is unchanged. Evidence: `expt_v1/results/validation_ladder_base14b.json`, `expt_v1/results/ladder/base14b_validation_{per_task,cells}.csv`.

## Teacher runs, scoring, screen and the SFT set S (PROTOCOL §§ 3–7; 10-08-2026)

All 4,312 declared cells are terminal (8 Valkyrie runs of 539 cells, concurrency 24; one identical recovery re-send for 16 positively unserved cells, all measured). Every collected file was kernel-scored by the frozen scorer in the private grading project; `kernel_binary` includes the non-vacuity screen. Charges are the gateway's per-receipt reports (Vals-funded, D-108). Unmeasured = no model response (output cap, content filter, infrastructure); such cells stay in the denominator.

**Reporting correction, 10-11-2026:** [receipt reconciliation](expt_v1/results/teacher_receipt_reconciliation_10-11-2026.json) distinguishes served requests from available responses. The historical analyzer used `served=True` as its measured condition, yielding the incorrect 539/539 measured rows; an earlier phase summary also stated 3,827. Original receipts contain **3,841 available responses and 471 unavailable**, with terminal statuses **3,837 measured, 49 incomplete, 347 model_error and 79 unmeasured_infra**. Four incomplete-status cells nevertheless have captured responses and consistent extraction; three pass the existing keep rule. The corrected table uses the original response-availability Boolean and retains every declared cell. Its Wilson intervals use tasks within each run; p-val=n/a. Original `teacher_analysis.json`, receipt statuses, kept-file hashes and the frozen SFT set are preserved. The reporting source is corrected prospectively to use `measured` rather than `served`.

| Teacher / sample | Declared | Response available | Response unavailable | Kept | Kept / available [Wilson 95%] | Truncated | Reported charge (USD) |
|---|---:|---:|---:|---:|---:|---:|---:|
| opus55/s1 | 539 | 432 | 107 | 303 | 0.7014 [0.6566, 0.7426] | 97 | 447.75 |
| opus55/s2 | 539 | 426 | 113 | 287 | 0.6737 [0.6278, 0.7165] | 102 | 461.02 |
| opus55/s3 | 539 | 432 | 107 | 304 | 0.7037 [0.6590, 0.7448] | 96 | 467.13 |
| opus55/s4 | 539 | 429 | 110 | 306 | 0.7133 [0.6687, 0.7540] | 101 | 460.19 |
| astra/s1 | 539 | 533 | 6 | 206 | 0.3865 [0.3461, 0.4285] | 0 | 840.9 |
| astra/s2 | 539 | 530 | 9 | 207 | 0.3906 [0.3500, 0.4327] | 0 | 812.77 |
| astra/s3 | 539 | 526 | 13 | 193 | 0.3669 [0.3268, 0.4089] | 0 | 807.72 |
| astra/s4 | 539 | 533 | 6 | 198 | 0.3715 [0.3315, 0.4133] | 0 | 814.46 |

Union coverage: 479 / 539 train tasks have at least one kept file (share 0.8887, Wilson 95% [0.8593, 0.9125]); both teachers 277, opus55 only 159, astra only 43, neither 60. Total reported charge 5111.94 USD.

Failure taxonomy (cells): Opus 5.5 {"kept": 1200, "no_lean": 437, "no_typecheck": 515, "unproved_theorem": 2, "vacuous_theorem": 2}; Astra {"kept": 804, "no_lean": 34, "no_typecheck": 1316, "unparseable_theorem_type": 2}. `no_lean` cells are those without available responses (Opus: 78 per run exceeded the 128,000-token output cap even at xhigh, 9–11 were content-filtered); `no_typecheck` is the dominant measured failure. Kept-file lengths (Qwen3 tokens): Opus mean 4908, median 4811, p90 6615 (n 1200); Astra mean 3055, median 2653, p90 4693 (n 804). Per-family union coverage: aerospace_set_real 2/2, aerospace_set_synthetic 10/10, compilers_set_real 3/3, compilers_set_synthetic 9/9, concurrent_set_real 3/3, concurrent_set_synthetic 9/9, critical_infra_set_real 4/4, critical_infra_set_synthetic 8/8, crypto_set_real 10/10, crypto_set_synthetic 2/2, cs_set 1/15, easy_set 20/25, finance_set_real 5/5, finance_set_synthetic 7/7, gov_cert_set_real 2/2, gov_cert_set_synthetic 10/10, hardware_set_real 3/3, hardware_set_synthetic 10/10, humaneval_set 30/34, hypervisor_set_real 3/3, hypervisor_set_synthetic 10/10, medical_oss_set_real 6/6, medical_oss_set_synthetic 6/6, memory_bugs_set_real 3/3, memory_bugs_set_synthetic 9/9, os_embedded_set_real 4/4, os_embedded_set_synthetic 8/8, realcode_set 3/19, regulated_set_real 3/3, regulated_set_synthetic 9/9, rfc_set_real 11/11, rfc_set_synthetic 1/1, security_set 255/276.

**Generated-Lean screen (§ 6):** 2004 kept, extraction-consistent cells → 6012 texts (file, full response, each fenced block) against the 714 validation + test Python programs and gold Lean references: 0 exact, 0 near hits (max word-5-gram Jaccard 0.0277); mean Jaccard to the task's own gold 0.0284 (max 0.1402), diagnostic only.

**S (§ 7):** |S| = 1315 examples over 476 distinct train tasks (Opus 798, Astra 517); exclusions {"over_length_cap": 4, "per_teacher_cap": 685} (the per-teacher cap of 2 distinct files is the rule, not a loss); per-task example counts {"0": 63, "1": 29, "2": 185, "3": 132, "4": 130}. Assistant tokens (template-inserted prefix + response + `<|im_end|>\n`): total 5,751,621, mean 4373.9, median 4296, p10 2213, p90 6623, max 12070; prompt tokens total 4,617,702 (mean 3511.6). Against the README estimate (1,100–1,600 examples, 4–6.5M assistant tokens): realized 1,315 examples and 5.75M assistant tokens, inside the upper scenario. Manifest (ids, hashes, token counts, no contents): `expt_v1/results/sft_set_manifest.csv`; stats `sft_set_stats.json`; the JSONL stays on the host.

**Lock-2 static checks (§ 12):** rendering prefix and mask on every example under all four tokenizers: 1315 / 1315 PASS (`template_check_examples.json`); NeMo RL's own formatter reproduces the evaluation prompt and the loss span (`<think>\n\n</think>\n\n` + response + `<|im_end|>\n` + `<|endoftext|>`) on every example with identical ids across sizes (`sft_schedule.json`, verdict PASS). Schedule: 658 steps of global batch 2 (|S| odd → one fully loss-masked padding slot in the last step), warmup W = 20 then cosine over 638; loss-token total 5,752,936; checkpoints at steps [82, 164, 334, 497, 658] (12.5 / 25 / 50 / 75 / 100 %, overshoot 1,658 / 4,315 / 8,240 / 4,079 / 0 tokens). Configs `expt_v1/configs/e08_sft_<size>.yaml` derive from Varun's with every difference listed in `sft_config_diff.md` (declared: `add_generation_prompt true` so the loss span excludes the generation prompt; openai_format adapter for the system message; SFT-time validation and Weights & Biases off; segment-and-resume checkpoints; GPU layout per size).

## Validation ladder (live; PROTOCOL § 9: 135 tasks × 8 samples per system; gates (a) extraction ≥ 972/1080, (b) capped ≤ 108/1080, (c) mixed `kernel_binary` tasks ≥ 7/135; p-val=n/a)

Written 2026-10-11T16:42:04+00:00 by the pipeline from `expt_v1/results/validation_ladder.json` (per-task and per-cell CSVs under `expt_v1/results/ladder/`).

| System | Status | Extraction | Capped | Mixed tasks (share; Wilson 95%) | Gates | pass@8 | mean pass | mean tokens |
|---|---|---:|---:|---|---|---:|---:|---:|
| `base14b` | COMPLETE | 1010 / 1080 | 77 / 1080 | 7 / 135 (0.0519; [0.0253, 0.1032]) | PASS | 0.0519 | 0.00833 | 2000.6 |
| `base_1p7B_e05` | COMPLETE | 601 / 1080 | 658 / 1080 | 0 / 135 (0.0; [0.0, 0.0277]) | fail | 0.0 | 0.0 | 7945.7 |
| `base_4B_e05` | COMPLETE | 913 / 1080 | 108 / 1080 | 3 / 135 (0.0222; [0.0076, 0.0633]) | fail | 0.0222 | 0.00278 | 2242.3 |
| `base_8B_e05` | COMPLETE | 930 / 1080 | 142 / 1080 | 0 / 135 (0.0; [0.0, 0.0277]) | fail | 0.0 | 0.0 | 2533.3 |
| `sft_14B_f0p125` | COMPLETE | 848 / 1080 | 169 / 1080 | 20 / 135 (0.1481; [0.098, 0.2178]) | fail | 0.1481 | 0.03704 | 5682.8 |
| `sft_14B_f0p25` | COMPLETE | 952 / 1080 | 128 / 1080 | 25 / 135 (0.1852; [0.1287, 0.2591]) | fail | 0.1852 | 0.06667 | 5137.2 |
| `sft_14B_f0p5` | COMPLETE | 975 / 1080 | 105 / 1080 | 30 / 135 (0.2222; [0.1603, 0.2995]) | PASS | 0.2296 | 0.10278 | 4603.3 |
| `sft_14B_f0p75` | COMPLETE | 953 / 1080 | 127 / 1080 | 35 / 135 (0.2593; [0.1927, 0.3391]) | fail | 0.2667 | 0.09352 | 5361.5 |
| `sft_14B_f1p0` | COMPLETE | 995 / 1080 | 84 / 1080 | 39 / 135 (0.2889; [0.2191, 0.3703]) | PASS | 0.2889 | 0.12037 | 4606.1 |
| `sft_1p7B_f0p125` | COMPLETE | 66 / 1080 | 608 / 1080 | 3 / 135 (0.0222; [0.0076, 0.0633]) | fail | 0.0222 | 0.0037 | 8394.6 |
| `sft_1p7B_f0p25` | COMPLETE | 79 / 1080 | 387 / 1080 | 1 / 135 (0.0074; [0.0013, 0.0408]) | fail | 0.0074 | 0.00093 | 7205.3 |
| `sft_1p7B_f0p5` | COMPLETE | 834 / 1080 | 245 / 1080 | 11 / 135 (0.0815; [0.0461, 0.14]) | fail | 0.0815 | 0.01759 | 5984.3 |
| `sft_1p7B_f0p75` | COMPLETE | 875 / 1080 | 205 / 1080 | 16 / 135 (0.1185; [0.0743, 0.1839]) | fail | 0.1185 | 0.04074 | 5896.9 |
| `sft_1p7B_f1p0` | COMPLETE | 897 / 1080 | 184 / 1080 | 20 / 135 (0.1481; [0.098, 0.2178]) | fail | 0.1481 | 0.04907 | 5369.9 |
| `sft_4B_f0p125` | COMPLETE | 43 / 1080 | 390 / 1080 | 4 / 135 (0.0296; [0.0116, 0.0737]) | fail | 0.0296 | 0.00556 | 7093.7 |
| `sft_4B_f0p25` | COMPLETE | 724 / 1080 | 245 / 1080 | 21 / 135 (0.1556; [0.1041, 0.2261]) | fail | 0.1556 | 0.04167 | 5671.6 |
| `sft_4B_f0p5` | COMPLETE | 845 / 1080 | 230 / 1080 | 22 / 135 (0.163; [0.1102, 0.2344]) | fail | 0.163 | 0.03889 | 5870.6 |
| `sft_4B_f0p75` | COMPLETE | 916 / 1080 | 164 / 1080 | 21 / 135 (0.1556; [0.1041, 0.2261]) | fail | 0.1556 | 0.03704 | 5658.0 |
| `sft_4B_f1p0` | COMPLETE | 946 / 1080 | 134 / 1080 | 32 / 135 (0.237; [0.1732, 0.3154]) | fail | 0.2444 | 0.09259 | 5022.7 |
| `sft_8B_f0p125` | COMPLETE | 504 / 1080 | 247 / 1080 | 10 / 135 (0.0741; [0.0407, 0.131]) | fail | 0.0741 | 0.01296 | 5586.3 |
| `sft_8B_f0p25` | COMPLETE | 929 / 1080 | 150 / 1080 | 23 / 135 (0.1704; [0.1163, 0.2427]) | fail | 0.1704 | 0.06944 | 5253.6 |
| `sft_8B_f0p5` | COMPLETE | 934 / 1080 | 146 / 1080 | 29 / 135 (0.2148; [0.1539, 0.2915]) | fail | 0.2148 | 0.0713 | 5200.8 |
| `sft_8B_f0p75` | COMPLETE | 964 / 1080 | 118 / 1080 | 33 / 135 (0.2444; [0.1797, 0.3233]) | fail | 0.2444 | 0.08241 | 5141.6 |
| `sft_8B_f1p0` | COMPLETE | 974 / 1080 | 106 / 1080 | 32 / 135 (0.237; [0.1732, 0.3154]) | PASS | 0.237 | 0.0963 | 4913.8 |

**Selection (PROTOCOL § 9, frozen rule):** verdict **PARTIAL**, f* = None; earliest passing fraction per size {"1.7B": null, "14B": "0.5", "4B": null, "8B": "1.0"}; tokens needed {"14B": 2884708, "8B": 5752936}; incomplete systems []. `expt_v1/results/selection.json` is committed before any test generation (D-004).

## Test evaluation (once; PROTOCOL § 10 and D-009: geometric mean of factor means on the common known cohort; 10,000 task-bootstrap resamples, seed 0; p-val=n/a)

Verdict PARTIAL; no common passing fraction. `IC_tests` is the stated-test correctness factor; `IC_proofs` is the proved-theorem fraction; `fsc_compiled` is validated formal specification coverage after the compile gate. All factors and the official combined score are on 0–1 scales. Written 2026-10-12T04:24:52+00:00 from `expt_v1/results/test_eval.json`; unknown cells stay in the declared denominator and are listed there.

| System | Scope | Known / declared cells | IC_tests | IC_proofs | fsc_compiled | SCSC [task-bootstrap 95%] | kernel_binary mean |
|---|---|---:|---:|---:|---:|---|---:|
| `base14b` | all | 1776 / 1776 | 0.0028 | 0.0028 | 0.0015 | 0.0023 [0.0004, 0.0045] | 0.002815315315315315 |
| `base14b` | core | 1216 / 1216 | 0.0000 | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0 |
| `base14b` | industryset | 560 / 560 | 0.0089 | 0.0089 | 0.0048 | 0.0073 [0.0017, 0.0144] | 0.008928571428571428 |
| `base_1p7B_e05` | all | 1776 / 1776 | 0.0000 | 0.0001 | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0 |
| `base_1p7B_e05` | core | 1216 / 1216 | 0.0000 | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0 |
| `base_1p7B_e05` | industryset | 560 / 560 | 0.0000 | 0.0003 | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0 |
| `base_4B_e05` | all | 1776 / 1776 | 0.0011 | 0.0006 | 0.0006 | 0.0007 [0.0000, 0.0019] | 0.0005630630630630631 |
| `base_4B_e05` | core | 1216 / 1216 | 0.0000 | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0 |
| `base_4B_e05` | industryset | 560 / 560 | 0.0036 | 0.0018 | 0.0020 | 0.0023 [0.0000, 0.0061] | 0.0017857142857142857 |
| `base_8B_e05` | all | 1776 / 1776 | 0.0000 | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0 |
| `base_8B_e05` | core | 1216 / 1216 | 0.0000 | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0 |
| `base_8B_e05` | industryset | 560 / 560 | 0.0000 | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0 |
| `test_sft_14B_f0p5` | all | 1776 / 1776 | 0.0873 | 0.0873 | 0.0861 | 0.0869 [0.0651, 0.1095] | 0.08727477477477477 |
| `test_sft_14B_f0p5` | core | 1216 / 1216 | 0.1258 | 0.1258 | 0.1242 | 0.1253 [0.0952, 0.1568] | 0.12582236842105263 |
| `test_sft_14B_f0p5` | industryset | 560 / 560 | 0.0036 | 0.0036 | 0.0036 | 0.0036 [0.0000, 0.0089] | 0.0035714285714285713 |
| `test_sft_8B_f1p0` | all | 1776 / 1776 | 0.1120 | 0.1120 | 0.1106 | 0.1116 [0.0823, 0.1435] | 0.11204954954954954 |
| `test_sft_8B_f1p0` | core | 1216 / 1216 | 0.1637 | 0.1637 | 0.1615 | 0.1629 [0.1219, 0.2062] | 0.16365131578947367 |
| `test_sft_8B_f1p0` | industryset | 560 / 560 | 0.0000 | 0.0000 | 0.0000 | 0.0000 [0.0000, 0.0000] | 0.0 |

Paired differences on all 222 tasks (shared known cohort, shared resampled task indices):

| Size | Selected − Base | kernel_binary mean pass-rate diff [95%] | SCSC diff [95%] | shared known cells |
|---|---|---|---|---:|
| 14B | `test_sft_14B_f0p5` − `base14b` | +0.0845 [+0.0625, +0.1075] | +0.0846 [+0.0627, +0.1077] | 1,776 / 1,776; missing 0 |
| 8B | `test_sft_8B_f1p0` − `base_8B_e05` | +0.1120 [+0.0828, +0.1441] | +0.1116 [+0.0823, +0.1435] | 1,776 / 1,776; missing 0 |

## Open questions for Brando

- None for the completed version 1. Follow-on training or evaluation requires its own authorization and prospective protocol.

**TLDR-end:** [rl4cv: 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test] Matched supervised fine-tuning and the once-only test evaluation are complete. Verdict PARTIAL: no common passing fraction; all 10,656 test factor cells and 4,302 judge ratings are known, with finished services retired and further launches stopped.
