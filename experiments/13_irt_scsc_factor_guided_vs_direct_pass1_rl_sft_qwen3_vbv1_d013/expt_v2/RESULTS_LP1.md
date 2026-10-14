# Experiment 13 version 2: LP-1 incomplete at generation startup

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_LP1.md>

**TLDR:** `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` stopped at LP-1, the generation-only resource and probability admission. One attempt produced 0/8 responses because the launcher supplied a graphics processor UUID where installed vLLM 0.10.0 expected a numeric device index. Probability agreement is unmeasured. Cleanup passed and the lease was released; no retry, anchors, actual-data fit or Phase 2 ran.

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

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2 ends at incomplete LP-1 startup under the no-retry rule; G0 still passes, while Phase 1 scientific measurements and Phase 2 remain unmeasured.
**Snapshot:** LP-1 attempts 1; responses 0/8; tokens 0; optimizer updates 0; retries 0; device-hours 0.014593276; cleanup PASS; lease RELEASED.
