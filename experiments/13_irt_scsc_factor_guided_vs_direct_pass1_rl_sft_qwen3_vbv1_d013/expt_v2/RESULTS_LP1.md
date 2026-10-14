# Experiment 13 version 2: LP-1 attempt 2 measured FAIL under A4

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_LP1.md>

**TLDR:** LP-1 attempt 2 is a final measured FAIL: its 99th-percentile absolute generation/trainer log-probability error is 0.1247693253, above the frozen 0.10 threshold, over all 40,035 tokens from 8/8 probe responses. Other admission criteria pass. A4 forbids an attempt 3 after statistics are computed. Cleanup passed and both leases are released; no anchors, fitted model or Phase 2 run is admitted.

Final preparation/result publication verification: **552 passed, 23 skipped, zero failures in 243.53 seconds**, direct exit 0 with Lean integration required. Seven focused G1 driver checks cover frozen publication/input refusal, phase chronology and retained partial-fit receipts. The final [G1 method lock](locks/G1_A3.json) and [driver](phase1/g1_driver.py) are complete; no actual-data fit ran. [Test receipt](phase1/G1_A3_publication_test.json).

Closeout verified: report and final G1 method published at `77558aa`; the A4 watchdog recorded exactly one stopped notification as **sent** to `brando.science@gmail.com`. Its receipt shows zero live experiment children, both leases released and all twelve cron lines preserved. [Completion receipt](LP1_A4/completion.json).

## Attempt 2 result — 10-14-2026 16:38 PDT

**Verdict: FAIL, final under A4 rule 5.** All 8/8 fixed probe responses and 40,035 generated tokens have trainer probability receipts. The 99th-percentile error exceeds its 0.10 ceiling by 0.0247693253. No threshold, seed, model hash, sampler, cap, scorer or probe identity changed. [Machine-readable result and evidence hashes](LP1_A4/attempt2_result.json).

| Admission statistic | Observed | Frozen threshold | Result |
|---|---:|---:|---|
| Unsupported generated tokens | 0/40,035 | 0 | PASS |
| Median absolute log-probability error | 0.0003027766943 | ≤0.01 | PASS |
| 99th-percentile absolute log-probability error | 0.1247693252563 | ≤0.10 | **FAIL** |
| Importance-ratio truncation at cap 2 | 0/40,035 = 0 | ≤0.01 | PASS |

Thresholds are from PROTOCOL sections 5–6 and PLAN section 5's LP-1 admission, unchanged in the original and A4 locks. Quantiles use the frozen linear method over all generated tokens; every generated terminal token is included. Five responses ended with a registered terminal token and three reached 8,192 new tokens. Prompt tokens total 28,164; prompt positions are excluded from these statistics. These are fixed-probe technical measurements, not estimates of a population effect: no inferential confidence interval or hypothesis test applies (p-val=n/a). This failure does not test whether a partial-credit reward improves reinforcement learning.

### Publication, preflight and device accounting

The fix, regression tests and [successor lock](locks/LP1_A4.json) were pushed as **`957efca7dd84abc6184c6f63aced35c95dc469b8`** before arming or any new device work. Required tests exited 0: **545 passed, 23 skipped, zero failures in 239.73 seconds**. All three CPU routes verified 133 file bindings and eight package versions; the successor configuration checker preserved 130 prior runtime bindings per route and every scientific setting. A4's adoption was explicitly post-observation; attempt 1 remains INCOMPLETE-INFRA and contributes no response to these statistics.

Fresh process, foreign-lease and reservation checks admitted skampere1 device 0, an idle 80 GiB A100. The launcher queried its identifier-to-index mapping and set the numeric index. Before the attempt counted, the real engine constructed successfully on the verified physical device and completed one token for an authored non-probe health prompt. Its process was cleaned; a fresh generation process then used the original probe seeds. [Preflight and arming receipt](phase1/LP1_A4_armed.json).

The lease ran **16:30:46–16:36:49 PDT**, **362.776132 seconds = 0.100771148 device-hours**, including preflight and cleanup, below the frozen 0.5-hour cap. The supervisor's internal elapsed time was 349.115145 seconds; total lease time is the budget quantity. Cumulative attempt-1/attempt-2 usage is **0.115364424 of 0.6 device-hours**. All four cleanup checks passed without signals; no marked process remains. Both canonical leases and the active lease file are RELEASED. The launch plan is retired; all twelve cron entries are preserved. Optimizer updates: zero.

The trainer's teardown logged an ignored policy-destructor exception: it attempted Ray auto-initialization after the explicit shutdown and hit a Unix socket path-length limit. All eight probability receipts already existed, the supervisor exited 0, and cleanup was verified. This is retained in the raw log; it does not erase the measured statistics or qualify this attempt for an infrastructure retry. Independent read-only arithmetic on the retained receipts verified alignment, both reported quantiles and the zero truncation count without another model or gate run.

### Transition

A4 says an attempt computing admission statistics is final, PASS or FAIL. Its maximum of three is not permission to retry a measured failure. Attempt 3 is **not admitted**. PLAN section 5's LP-1 prerequisite remains unmet, and PROTOCOL section 8 disallows training beyond admitted diagnostics after a technical failure. G0 remains PASS. Anchor responses are 0/17,248; calibration, G1/H2 and Phase 2 remain unmeasured.

The final G1 execution driver and method lock were prepared during this attempt, before any fit. They retain publication, input-hash, library-version and phase-order checks; the failed LP-1 prerequisite prevents execution. Their tests/publication are retained with the other Phase 1 preparation. The scientific training comparison has not been run. The A4 watchdog completion notification is recorded above.

## Adopted A4 continuation — 10-14-2026 16:23 PDT

The master adopted [A4](AMENDMENT_A4_technical_gate_infrastructure_attempts_10-14-2026.md) at `d79b0fd`, explicitly after observing attempt 1. It classifies that attempt as **INCOMPLETE-INFRA** and admits attempt 2 after a published fix, regression and engine preflight with unchanged scientific settings. The original result receipt, failure evidence and stopped notification remain unchanged; the terminal interpretation below is historical and superseded by A4. [Attempt-2 preparation](phase1/LP1_A4.md).

## Attempt 1 historical report (preserved evidence)

## Chronology and resources

The [lock](locks/LP1.json), implementation and tests were pushed as `d831d0fe9eeff11487b7449530abf3f672b7d474` before arming automatic dispatch. Lock SHA-256: `298c6165e2697b56c97334ad32e83bc5f63c08b7dd433aff97dd94a4778c89d0`. The required suite passed 512 tests with 23 skips, zero failures, in 240.62 seconds. CPU-only preflight verified 132 file bindings and eight package versions on each skampere route. These checks did not establish device execution or probability agreement.

The 15:19 PDT first dispatch returned WAIT. The next scheduled poll, on 10-14-2026 at 15:30 PDT, found skampere1 devices 2 and 7 idle. The dispatcher checked compute processes twice, canonical foreign leases and the master reservation hash, then claimed device 2, an A100 with 80 GiB memory. Its recorded inventory had no compute process, zero used device memory and zero utilization on that device. Other users' occupied devices were excluded.

The experiment-13 lease ran from **15:30:06 to 15:30:58 PDT**, **52.535794 seconds = 0.014593276 device-hours**, within its 1,800-second bound. The supervisor recorded one attempt and eight started response slots. Generation failed during engine construction. It returned no response, and the trainer stage did not start. Both cleanup checks passed with no signals needed; no marked process remains. Both the active lease file and canonical registry record are RELEASED. The launch plan was retired; all ten cron entries remain unchanged.

## Failure evidence

Installed `vllm/platforms/interface.py`, method `device_id_to_physical_device_id`, reads `CUDA_VISIBLE_DEVICES` and executes `int(physical_device_id)`. The launcher's value was the leased device's UUID, `GPU-e98e645a-d860-3666-a80b-2cea81363c51`. Architecture inspection therefore raised:

```text
ValueError: invalid literal for int() with base 10: 'GPU-e98e645a-d860-3666-a80b-2cea81363c51'
```

The outer model-configuration validation then failed before any generated response. vLLM's internal architecture inspection tried its configured architecture and fallback; this was one supervisor invocation, not a regenerated probe. The CPU preflight had checked source hashes, package versions, trainer imports and sampler construction, but omitted this device-index compatibility check. This was a launcher defect; it is not evidence of probability disagreement or a scientific failure of partial credit.

Full private startup logs, attempt records, all eight started-slot records, the generation terminal receipt, cleanup and lease records are hash-bound in the [public result receipt](LP1/result.json). No task identifiers or prompts are published here.

| Quantity | Result | Admission threshold/source |
|---|---:|---|
| Probe responses generated / declared | 0/8 | Complete frozen probe; LP-1 lock |
| Generated tokens | 0 | Maximum 65,536 for this probe |
| Trainer probability evaluations | 0 | Same-policy comparison required |
| Unsupported token count | Unmeasured | 0; PROTOCOL sections 5–6 |
| Median absolute log-probability error | Unmeasured | ≤0.01 |
| 99th-percentile absolute log-probability error | Unmeasured | ≤0.10 |
| Importance-ratio truncation fraction | Unmeasured | ≤0.01 at ratio cap 2 |
| Optimizer updates / retries | 0 / 0 | Generation only; no retry |

These are technical execution counts and missing measurements, not statistical estimates. Confidence intervals and hypothesis tests are not applicable (p-val=n/a); unavailable probability statistics are not reported as zero.

## Transition and retained preparation

**LP-1 is INCOMPLETE and does not admit anchor generation.** PLAN section 5 requires LP-1 before the anchor panel; PLAN section 4 and the master's explicit no-retry instruction preserve the one-attempt rule from L1v2 onward. The adopted A3 admission record also states that a nonpassing/inconclusive gate does not advance. This is an unmet prerequisite, not a claimed G1/H2 or Phase 2 T1 failure. The protocol has no exception granting an automatic changed-launcher LP-1 retry. G0 PASS remains unchanged.

No anchor responses were generated (0/17,248 across the four declared batches), no calibration or item parameters were fitted, G1/H2 remain unmeasured, and Phase 2 was not run. The validated Valkyrie formal specification coverage limitation remains documented but did not cause this stop.

Completed CPU preparation is retained: anchor generation and scoring, sampler and token caps, conditional and two-parameter logistic fitting controls, source-bound A3 missingness loader, completion bounds, and train/validation source features. The final G1 execution driver and executable lock were still pending; `G1_A3_DRAFT.json` remains explicitly non-executable. The latest required suite passed **528 tests, 23 skipped, zero failures in 247.80 seconds**, including the real capped-source Lean control. The independent frozen prediction and historical scorer files remain unchanged.

A future authorized protocol amendment could prospectively freeze a corrected numeric device mapping with UUID-to-index verification and an additional preflight. No such rerun was performed or implicitly approved by this report. The current attempt, lock, failure and budget accounting remain immutable.

Publication verified on remote main at `50cf118`. The watchdog sent exactly one stopped notice at 15:38 PDT on 10-14-2026; no live experiment child or active lease remains. [Completion receipt](LP1/completion.json).

**TLDR-end:** [rl4cv: Experiment 13 v2] LP-1 attempt 2 fails its frozen probability-tail criterion; A4 makes this measured result final and no downstream run is admitted.
**Snapshot:** Responses 8/8; generated tokens 40,035; median error 0.000302777; p99 error 0.124769325 > 0.10; unsupported/truncated tokens 0/40,035; cumulative device-hours 0.115364424; leases RELEASED.
