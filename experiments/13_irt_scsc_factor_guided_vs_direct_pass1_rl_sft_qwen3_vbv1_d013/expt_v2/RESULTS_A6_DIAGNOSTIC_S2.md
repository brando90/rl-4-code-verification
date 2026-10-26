# Experiment 13 v2-S2: final A6 pipeline diagnostic

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_A6_DIAGNOSTIC_S2.md>

**TLDR:** **SOUND**, final attempt 2. The fixed 64-task × 8-sample train diagnostic generated 512/512 responses and was scored once. Attempt 1 remains INCOMPLETE-INFRA with zero responses. Continue to the learning-pilot lock and technical gates.

Published analysis date: 10-15-2026 10:37 PDT. The [aggregate receipt](phase1/A6_S2_result.json) binds the single saved result, full scoring population, timing and input locks. No output enters a comparison statistic.

| Outcome | Successes / declared | Measured / declared | Full-denominator rate bounds | 95% whole-task-group bootstrap outer envelope |
|---|---:|---:|---|---|
| compile | 48/512 | 496/512 | [0.093750000, 0.125000000] | [0.044230769, 0.190476190] |
| strict | 48/512 | 496/512 | [0.093750000, 0.125000000] | [0.044230769, 0.190476190] |

Intervals use the already-published 10,000 draws at seed 1302603 over 61 whole selected train task groups, retaining all eight samples. They condition on this fixed policy/cohort, exclude training-run uncertainty and are descriptive; p-val=n/a (no hypothesis test). A degenerate zero bootstrap is not a population upper bound. The aggregate receipt preserves both endpoint intervals as well as their outer envelope. Missing observations remain unknown, not imputed.

The unchanged A6 criterion is strict successes > 0 and compile rate ≥ one tenth of the historical validation rate. The historical full-schedule policy compiled and strictly succeeded on **100/1,080** responses for each metric: **0.092592593 [0.053700397, 0.132980148], p-val=n/a**, 95% percentile bootstrap over 100 validation task groups. Thus the diagnostic needs at least **5/512 compiling responses** and at least **1/512 strict success**. The frozen full-denominator completion bounds determine the verdict.

Generation retained 2,958,502 tokens, 101/512 cap-limited responses and 0/512 missing generations. Scoring has 0 unresolved cleanups and 0 retries. Missing-status counts: `{"deterministic_resource_limit": 15, "unresolved_measurement": 1}`. Extraction-method counts: `{"file_blocks": 395, "no_lean_block": 101, "unavailable": 16}`.

The repair/attempt-2 lock was pushed at `d9df333` before generation. It accepted the existing bound `pytorch_model.bin` without changing model bytes, prompts, template, float16 numerics or the scorer. The actual engine passed its non-probe health request before diagnostic responses. The diagnostic used the unchanged historical evaluation sampler: temperature 0.6, top-p 0.95, top-k 20 and 12,288 new tokens. The task-ID SHA-256 remains `f6a7c30330782ead62fed3a2c1af1c2b9dbbe3f05d64bcb2584773c9ae61421b`; IDs and raw responses stay private.

Attempt 1 consumed 0.0038115982876883612 device-hours and produced 0/512 responses before engine construction. Its .safetensors-only format guard was corrected with the published regression, preflight and successor lock under A4/A6 clarification. Attempt 2 consumed 1.402495361765 device-hours; cumulative usage is 1.406306960053/2.0, including health and cleanup. Both leases are released with cleanup verified. No third generation attempt is admitted after these responses.

The single scoring/analysis run exited 0, consuming 11393.67 user + 3081.26 system processor-seconds = 4.020813889 processor-hours, with 1753.33 seconds elapsed. Generation processor counters were not recorded and remain unavailable. Exact timing and raw evidence hashes are retained.

Historical G1 remains final INCONCLUSIVE; arm C stays disabled. H2/F2 stay UNAVAILABLE for the null predictor, original F2=0.75 is preserved, and independent batch 2 remains skipped and unarmed. No Phase 2 optimizer update or new held-out response has run. S1 LP-1 FAIL and S2 LP-1 PASS remain unchanged.

Final A6 publication verification: required Lean integration **1,121 passed, 3 skipped, zero failures in 491.85 seconds**, direct exit 0 ([receipt](phase1/A6_final_publication_test.json)). The public result matches the single saved analysis; every provenance hash verifies. No generation or scoring replay occurred.

## Earlier infrastructure and generation chronology

The following is the earlier publication, retained as historical evidence; its pending-status language is superseded by the final result above.

### Experiment 13 v2-S2: A6 diagnostic attempts and pending soundness

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_A6_DIAGNOSTIC_S2.md>

**TLDR:** **Attempt 1 INCOMPLETE-INFRA; soundness unmeasured. Attempt 2 generation is complete; official scoring is pending.** The first A6 launch produced **0/512 responses**, zero generated tokens and zero scores. The launcher rejected the frozen `pytorch_model.bin` export because its preflight mistakenly required a `.safetensors` file. No engine was constructed and no admission statistic exists.

The published execution freeze `f5af95c` preceded the launch. Device 0 on skampere1 was claimed only after two complete idle observations, fresh foreign-lease/reservation checks and numeric UUID-to-index mapping. The worker exited with code 1 in `a6_runtime.verify`, before `build_engine` or a diagnostic prompt could run. Cleanup verified with no signals, and the lease was released. Consumed device time was **0.0038115982876883612 hours**; **1.9961884017123116 of 2.0 hours** remains, without any reset. At the close of attempt 1, no owned device lease remained active. The [attempt receipt](phase1/A6_diagnostic_attempt1.json) binds raw logs, process identity, runtime, cleanup and release evidence.

This is neither SOUND nor UNSOUND: strict successes and compile rate are unavailable, not zero. No bootstrap interval or p-value can be computed without observations. The historical reference (100/1,080 for both outcomes), 64-task cohort, prompt tokens, model bytes, numerics, sampler, token cap and scorer remain frozen. The failure says nothing about model capability or the rollout sampler.

The [one-line repair patch](phase2/A6_checkpoint_format_fix.patch) accepts either already-bound checkpoint format. It is **applied under the A6 clarification at `80fdd2a`**, without changing any scientific setting. Regression tests reproduce the original `.bin` rejection, pass the proposed check for `.bin` and `.safetensors`, and retain rejection of missing or changed weights. The [repair record](locks/A6_CHECKPOINT_FIX_PROPOSED.json) retains the proposal chronology, and the [successor execution lock](locks/A6_DIAGNOSTIC_ATTEMPT2.json) lists the changed runtime and clarification bindings, plus all 286 unchanged original hashes. No export conversion, checkpoint change or outcome-based selection is proposed. A pre-clarification [device-free check against the exact real inputs](phase1/A6_repair_preflight.json) reproduced the original rejection and verified that the candidate accepts all 288 bound files and installed versions, then stops at the released-lease guard. It constructed no engine, claimed no device and computed no gate statistic.

The master’s 10-15-2026 08:15 PDT [clarification](AMENDMENT_A6_zero_strict_signal_rollout_sampler_10-15-2026.md#clarification-10-15-2026-0815-pdt-master-infrastructure-attempts-of-the-diagnostic) explicitly applies A4 to this diagnostic. The earlier interpretation that a new amendment was required is superseded. Attempt 1 is an infrastructure attempt, **not a scientific stop**. At most three attempts are allowed; the cumulative 2.0 device-hour allocation is unchanged, and any completed scored cohort is final. Attempt 2 uses a separate output directory and a bound admission guard that rejects changed predecessor evidence, a generated diagnostic response, prior scoring, exceeded attempt limits or a changed budget. The original attempt’s evidence remains immutable. The unchanged engine performs its non-probe health request before any diagnostic response. Publish the fix, regression tests, preflight evidence and successor lock before launch.

Historical G1 completed once and is [final INCONCLUSIVE](RESULTS_G1_S2.md); arm C remains disabled. H2 and F2 remain UNAVAILABLE, independent batch 2 is skipped, and no Phase 2 optimizer update or new held-out response has run.

Applied-repair preflight: [PASS](phase1/A6_attempt2_preflight.json), 295 unique successor input/source bindings verified in the exact frozen runtime, predecessor evidence checked, then the released-lease guard correctly refused a model call. No device was claimed. During preparation, a duplicated amendment binding and use of the coordinator rather than frozen runtime were caught before launch and corrected; neither created an experiment attempt. The original runtime and environment settings remain unchanged except for the recorded checkpoint-format acceptance fix.

Publication verification: required Lean integration **1,042 passed, 3 skipped, zero failures; direct exit 0**, 505.09 seconds ([receipt](phase2/A6_attempt2_publication_test.json)).

Attempt 2 launched after `d9df333`, with the actual engine health preflight PASS ([launch receipt](phase1/A6_attempt2_launch.json)). Soundness remains unmeasured until the complete frozen cohort is scored.

Progress at 10-15-2026 09:42 PDT: attempt 2 has 416/512 durable responses on its original leased device 0; no scoring or admission statistic has run. The cumulative allowance remains 2.0 device-hours.

A6 generation closure and scoring freeze (10-15-2026 10:07 PDT): attempt 2 saved **512/512 responses**, 2,958,502 generated tokens, 0 missing responses and 101 cap-limited responses. Cleanup and lease release verified; device time 1.402495362 hours for attempt 2, 1.406306960/2.0 cumulative including attempt 1. No generation replay is admitted. The [generation receipt](phase1/A6_attempt2_generation.json) and [complete scoring-input lock](locks/A6_DIAGNOSTIC_SCORE.json) retain every declared slot. Soundness remains unmeasured; one official scoring/analysis run follows publication. Required Lean integration **1,121 passed, 3 skipped, zero failures in 488.93 seconds**, direct exit 0 ([receipt](phase1/A6_scoring_input_publication_test.json)).

The original sampler, prompts, model, numerical setting and scorer remain unchanged. The scoring lock binds all 512 generation statuses, each retained response, the train grouping, original reference, analysis implementation and timed launcher. Bootstrap settings remain the published 10,000 whole-train-group draws at seed 1302603. No scoring or diagnostic threshold statistic has been computed.
