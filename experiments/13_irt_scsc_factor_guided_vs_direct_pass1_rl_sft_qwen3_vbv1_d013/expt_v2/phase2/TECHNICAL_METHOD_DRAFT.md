# Experiment 13 v2-S2 technical-gate implementation preparation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2/TECHNICAL_METHOD_DRAFT.md>

**TLDR:** The raw training, saved-state replay and gate-evaluation primitives are prepared and tested without experiment model calls. This document is not an LP lock or permission to execute a gate. Complete Phase 1 and publish the full execution, input and resource lock first.

## Runtime and finality

`trainer_core.update` retains the raw before/after parameter digests. Its normal path no longer compares them into T2's admission statistic before refit has finished. The complete T2 refit probability receipts must exist before `technical_measurements.t2` evaluates weight change and refit error. The optional combined replay helper is for authored regression coverage; the intended gate driver uses the separate `replay_saved` path after publishing T2.

`replay_saved` verifies T2's source result, before/after checkpoint receipts and exact saved loss-input batch, restores the pre-update weights/optimizer/scheduler/random state, then executes one diagnostic replay. It records raw loss and resulting state digests without computing T3's admission statistic. It neither regenerates a response nor executes a fresh original T2 update. The evaluator then binds the source result hash and saved batch hash, requires verified restoration and compares the two loss arrays.

A fresh trainer validates its initial fixed seed before constructing a model. New policy workers initialize that seed once; resumed workers restore their saved random state. The original common tokenizer, float16 condition and installed numerical paths remain unchanged. Empty initial optimizer state is preserved around native checkpointing as described in the implementation README.

A4 permits at most three attempts of LP and T1–T4 only for a reproducible infrastructure failure before admission statistics, with a tested published fix, unchanged scientific settings/caps and retained prior attempts. No primitive grants an automatic retry. Statistics make a technical result final. T5, L2, pilot/main and test evaluation keep their no-retry rules. The future supervisor must preserve this boundary and publish every result.

## Isolated execution stages

`technical_runtime.py` provides separately launched non-probe preflight, generation, probability recomputation, update, replay and native export stages. It verifies authored source and dynamic-input hashes, installed versions, fixed model/tokenizer files, train-only manifests, terminal masks and the current numeric leased device. A complete generation ledger and unchanged cell identities are required before probability recomputation. Nonfinite trainer values remain explicit missing values for the final evaluator; the worker never converts them to successful agreement or runs a gate comparison. An existing attempt directory refuses repetition. The driver, publication/prerequisite checks, bounded allocation and cleanup supervisor remain required before actual device use.

## Evaluators

- **T1:** Import the unchanged `phase1/probability.py` assessment. Require every declared train cell with unchanged token IDs and assistant/end-of-sequence masks. Zero unsupported tokens; median absolute error at most 0.01, 99th percentile at most 0.10, importance truncation at most 1%.
- **T2:** One real declared 256-slot update, unchanged model-state dimensions, actual parameter hash change, and a complete finite refit probe with exact masks and median absolute error at most 0.01. Report the refit tail and truncation statistics descriptively; do not add T1's tail/truncation thresholds to T2's stated criterion.
- **T3:** Verified exact pre-update restoration and identical saved batch/source provenance; maximum replay loss difference at most 0.001. Report the ending parameter-digest comparison descriptively. Exact ending weights are not an extra gate threshold beyond the stated replay-loss tolerance.
- **T5, prospective operational definition:** Use both fixed A seeds 1301/1302 equally and every 256-slot scheduled opportunity. Pool the two equal-size ten-update windows, 5,120 declared slots each. Compare updates 1–10 to 21–30; if the lower improvement bound is below two percentage points, use the one predeclared extension and compare 1–10 to 51–60. Missing strict outcomes retain full-denominator worst-case bounds, not zero labels. At 60, PASS requires the lower bound at least 0.02; FAIL requires the upper bound below 0.02; overlap is INCONCLUSIVE and cannot admit main. Every scheduled opportunity must be accounted, including middle updates outside the two windows. This is feasibility selection, not evidence for the main efficacy hypothesis; no inferential p-value is claimed.

The T5 pooling and missing-outcome operational definition must be included in the eventual LP lock before pilot outcomes. The extension never chooses seeds or adds a second extension. Any compared pilot learning curves use their common horizon, as PROTOCOL requires.

T4's complete cost ledger, resource admission, actual-device supervisor, train mutation/independent coverage controls, learning loop, main token-boundary controller and final analysis remain to be completed. No technical or learning verdict is established by these synthetic regressions.
