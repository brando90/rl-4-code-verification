# Experiment 13 v2-S2: numerical development and LP-1 confirmation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_LP1_A5.md>

**TLDR:** v2-S2 float16 passes its one final LP-1 confirmation on the original probe: 8/8 responses, 44,844 tokens; unsupported 0, median error 0.0000327481539, 99th percentile 0.0176023889 and truncation 0, all within unchanged thresholds. Phase 1 continues under S2. C1 was selected on the disjoint development probe; C2 was not run. S1's measured FAIL remains final (99th-percentile error 0.124769325 >0.10).

Last updated: 10-14-2026 17:54 PDT

## Final original-probe confirmation: PASS

The selected float16 setting and `LP1_A5_S2.json` were pushed at **`f8ecbfa` before the confirmation launch**. The original eight-task probe, original per-task seeds, sampler, 8,192-token cap and original thresholds were unchanged. This is the only S2 confirmation attempt and its measured verdict is final. [Confirmation evidence](LP1_A5/C1_confirmation_result.json).

| Criterion | Confirmation measured value | Original LP-1 ceiling | Verdict |
|---|---:|---:|---|
| Unsupported generated tokens | 0 / 44,844 | 0 | PASS |
| Median absolute log-probability error | 3.2748153898865e-05 | 0.01 | PASS |
| 99th-percentile absolute log-probability error | 0.0176023888587952 | 0.10 | PASS |
| Importance-ratio truncation at cap 2 | 0 / 44,844 = 0 | 0.01 | PASS |

Coverage is **8/8 responses**, 44,844 supported generated tokens, 28,164 prompt tokens, five terminal-token finishes and three token-cap finishes. Zero optimizer updates and zero retries. The fixed-probe technical statistics have no inferential interval or hypothesis test (p-val=n/a); this is numerical admission, not evidence of learning or reward efficacy.

Fresh process/foreign-lease checks admitted skampere1 GPU 0 under new lease `e13v2-fc3db0de27f5464190c46426461eae0c`. The actual float16 engine passed its one-token non-probe preflight before the numbered attempt. The lease is RELEASED after all four cleanup checks passed without signals. Confirmation used **0.103405812780 device-hours** (372.260926 seconds) under its 0.5-hour cap. **A5 total is 0.207209183243/3.0 device-hours** across development and confirmation; S1's 0.115364423990 hours remain separate. Both A5 plans are retired, no A5 lease remains active, and the final private registry snapshot preserves the closed A5 accounting before any later phase allocation.

The same ignored post-probability trainer destructor exception is retained in the confirmation log; process exit was 0 and cleanup passed. It neither changes this verdict nor permits a retry. No more A5 candidate or confirmation measurement is allowed.

Transition: **continue PLAN §5 under v2-S2**, with a new float16 train anchor panel, then frozen calibration/items/F2, independent batch 2 and G1/H2 using the already published G1 driver/lock before any fit. Later Phase 2 technical gates remain mandatory. The current milestone admits generation; it does not claim that a training update, coverage audit, G1 or H2 has passed.

Final admission publication check (10-14-2026 17:58 PDT): required Lean integration suite exited 0, **558 passed, 23 skipped, zero failures in 233.80 seconds**. [Receipt](LP1_A5/publication_test.json). Final S2 confirmation PASS is ready to publish; anchor implementation/resource preparation continues without any further admission measurement.

## Development result: C1 selected

Candidate list, complete private configuration hashes, implementation and disjoint-probe hashes were pushed at **`6251b77` before any A5 device measurement**. [Frozen declaration](phase1/LP1_A5_candidates.json) · [Method](phase1/LP1_A5.md) · [C1 lock](locks/LP1_A5_C1.json) · [Aggregate evidence](LP1_A5/C1_result.json).

| Criterion | C1 float16 measured value | A5 development ceiling | Verdict |
|---|---:|---:|---|
| Unsupported generated tokens | 0 / 51,472 | 0 | PASS |
| Median absolute log-probability error | 2.25788680836558e-05 | 0.008 | PASS |
| 99th-percentile absolute log-probability error | 0.0163397789001465 | 0.08 | PASS |
| Importance-ratio truncation at cap 2 | 0 / 51,472 = 0 | 0.008 | PASS |

Complete coverage: **8/8 responses**, 51,472 generated tokens and 28,903 prompt tokens; all generated tokens supported, six terminal-token finishes and two 8,192-token-cap finishes. Truncated-at-cap responses remain included. Zero optimizer updates. Quantiles pool all declared generated-token probabilities, using linear interpolation and the unchanged evaluator. These are deterministic fixed-probe technical statistics; inferential intervals and hypothesis tests do not apply (p-val=n/a).

The probe contains eight train tasks, zero validation/test tasks, and zero overlap with the original eight-task admission probe. Seed 1302151; task-ID-list SHA-256 `843f5f033b972a596bee6d463ba0e74dc883a481dca0b5a8cd64ea4390b8004b`; manifest SHA-256 `75412ee55bef5d417bce4620a6a276a6fd279c015a1c42a6175c4828b119638c`. The original per-task generation seed rule is retained. No outcome-dependent task or seed replacement occurred.

C1 is the first qualifying candidate in the published order. **C2 is not measured**, as A5 requires stopping selection at the first qualifier. The candidate list is closed; no new setting may be added. The development result does not admit anchors or training before confirmation.

## Resource and execution evidence

The same writer used the experiment-13 registry to claim skampere1 GPU 0 (`GPU-4a898d48-860a-9abc-bda7-59057400018e`). Fresh inventories and canonical foreign-registry checks preceded the claim and a second census followed it. All 33 foreign lease records were released; 17 legacy lease/release files matched their prior hashes, and no additional experiment-12/14 registry was found. The real float16 engine preflight passed on numeric `CUDA_VISIBLE_DEVICES=0` with one authored, non-probe token.

The complete lease consumed **0.103803370463 device-hours** (373.692134 seconds), including preflight, generation, trainer evaluation and cleanup, under the 0.5-hour per-run cap. A5 usage is **0.103803370463/3.0 device-hours**. The earlier S1 usage remains separately recorded at 0.115364423990 hours. Cleanup passed, the lease is RELEASED and the C1 launch plan is retired; the fourteen-line additive cron schedule remains installed. Raw outputs stay private and their hashes are in the aggregate evidence receipt.

The trainer log retains the same ignored `Policy.__del__` teardown exception seen under S1: after explicit Ray shutdown, its destructor attempts automatic Ray initialization with an overlong temporary socket path. All eight probability receipts were already complete, the stage exited 0 and all four marked-process cleanup checks passed without signals. This is retained as a teardown limitation, not reclassified as an unmeasured infrastructure attempt.

## Selected condition and confirmation freeze (historical)

[LP1_A5_S2.json](locks/LP1_A5_S2.json) freezes float16 identically for vLLM 0.10.0 and NeMo RL 0.4.0, with installed versions unchanged. It names the numerical change, all source replacements and each changed runtime binding, and preserves every unchanged S1 scientific binding at its prior hash. Every later generation/training path must use this condition if confirmation passes. Actual Phase 2 cost and training stability remain subject to the frozen later technical gates.

The confirmation uses the exact original manifest SHA-256 `19cc85e9d109695577ee24a5d0b403c349543dabe31c962602b68527175b142d` and unchanged thresholds: unsupported 0, median ≤0.01, 99th percentile ≤0.10, truncation ≤0.01. It runs once after required tests and the S2 lock are pushed. Its measured result is final. A confirmation failure stops v2; a PASS continues Phase 1 under v2-S2. No actual-data calibration or G1 fit has run.

Confirmation-freeze verification (10-14-2026 17:45 PDT): **558 passed, 23 skipped, zero failures in 251.97 seconds**, direct exit 0 with Lean integration required. [Receipt](phase1/LP1_A5_S2_publication_test.json). No confirmation call has run; publish this lock before arming.

## Preserved S1 result and disclosure

[A5](AMENDMENT_A5_numerics_condition_S2_after_LP1_fail_10-14-2026.md) was adopted after S1's measured failure. The new numerical condition is therefore explicitly post-observation; its disjoint development selection and original-probe confirmation are prospective relative to S2 measurements. [S1 report](RESULTS_LP1.md) and its raw evidence remain unchanged. S1 is not retried or retrospectively passed. G0 remains PASS and every later scientific gate threshold is unchanged.
