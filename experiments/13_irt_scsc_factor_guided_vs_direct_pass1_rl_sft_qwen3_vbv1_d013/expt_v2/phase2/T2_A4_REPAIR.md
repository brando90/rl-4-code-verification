# Experiment 13 v2-S2 T2: A4 runtime provenance repair

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2/T2_A4_REPAIR.md>

**TLDR:** Attempt 1 is INCOMPLETE-INFRA: the technical launcher omitted required update provenance, raising `KeyError` after model initialization but before calling the update function. The successor adds identity metadata and a non-probe preflight without changing a scientific setting. Complete attempt 2 follows only after the repair and A4 admission lock are published.

## Retained failure

The [failure](T2_A6_attempt1_result.json) was published at `0266ac5`. Generation completed 256/256 responses (1,262,519 tokens); all 256 scoring receipts closed, with 255 measured and one deterministic timeout. These failed-attempt outputs stay private and never enter a later attempt's statistic. There were zero optimizer calls, trainer recomputation results, refit responses and admission statistics. All four reservations were released with verified cleanup, totaling 0.6015553532706367 device-hours, including the earlier pre-admission collision. Neither the missing cell nor the completed gate data are silently retried.

A4 rule 4 requires the next numbered attempt of the complete technical gate. Thus attempt 2 repeats the fixed complete gate under the identical seeds and probes; it does not resume attempt 1 or import its scoring rows. The per-attempt 8.0-hour and cumulative 10.0-hour caps are unchanged, with at most three total attempts. A computed T2 verdict remains final.

## Infrastructure change and verification

Both technical controllers now attach condition, gate, stage, attempt-root path and fixed run seed as `provenance`. The shared runtime validates that required dictionary before preflight/update model construction. The non-probe engine preflight saves its metadata-check receipt; the existing engine-health and short Ray socket checks still run. Pilot/main materialization already supplies compatible provenance and keeps its existing settings.

The regression reproduces the missing-field `KeyError` at the actual update invocation with a stubbed model session and verifies that no update call occurred. The repaired materialized configuration reaches that invocation with the correct metadata. Both original and A6 controllers, invalid early-preflight metadata, and existing pilot/main metadata are covered: **17 new checks; 34 focused checks passed in 3.58 seconds**. The probability, scoring and gate-evaluation function bodies are unchanged ([receipt](T2_A4_regression.json)). The device-free planned-attempt metadata preflight also passes and reproduces the missing-field rejection; real engine health still precedes numbered admission.

The [successor LP](../locks/LP_A6_S2_T2_A4.json) hashes 4,685 files, preserving 4,678 prior hashes and explicitly listing seven changed/added bindings in the later A4 admission lock. Its hash is `abe0b230034e7d6accf16cd1e1d34be0ac0f727926195a3ce886edc785fdebd5`; the scientific signature remains `dde380f60f21e0ca1dbc6c36ac05c65e383e611fa00f267324451a14fb7a19ae`. The model/tokenizer/scorer, probe sets, seeds, sampler, numerics, token masks/caps, optimizer/loss/scheduler, thresholds and resource allocation remain unchanged. Old locks and failed-attempt evidence remain retained.

Required Lean integration: **1,174 passed, 3 skipped, zero failures in 507.02 seconds**, direct exit 0 ([receipt](T2_A4_full_test.json)). No new probe, optimizer call or device claim was made for this repair.
