# Experiment 13 v2-S2 anchor generation and scoring

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_ANCHORS_S2.md>

**TLDR:** The base anchor generation is complete: 4,312/4,312 responses on 539 train tasks, eight samples each. No cells are missing or retried. Scoring has not started; the half- and full-schedule panels continue generating.

Recorded: 10-15-2026 01:47 PDT. Condition: **v2-S2**, float16. Generation freeze `d4948f3e57af06fdff660f271a9602e0df3a092c` precedes every response; its bound files still match.

| Base generation accounting | Observed value |
|---|---:|
| Completed / declared responses | 4,312 / 4,312 |
| Missing; second-attempt cells | 0; 0 |
| Generated tokens | 9,324,934 |
| Prompt tokens | 15,515,768 |
| Minimum / maximum output tokens | 2 / 8,192 |
| Responses reaching the fixed token cap | 276 / 4,312 |
| Allocated device-hours, including all segment leases | 6.9587135382493335 |
| Released leases | 17 / 17 |
| Anchor scores; experiment optimizer updates | 0; 0 |

All segment cleanup receipts verify. The [immutable generation receipt](anchors_S2/base_generation.json) binds the frozen manifest, generation lock, private response inventory and closed terminal ledger by SHA-256. Raw responses and task identities remain private. This is complete generation accounting, not a scientific performance verdict; confidence intervals and p-values are not applicable to this fixed-manifest census. Token-cap completion does not establish strict correctness.

At this observation, half-schedule generation retains 3,328/4,312 responses and full-schedule batch 1 retains 2,368/4,312. Independent batch 2 remains unarmed until calibration, item parameters and forecast F2 are frozen and published. The preliminary PLAN runtime estimate is not a measurement: the actual base generation cost above will enter the later T4 resource projection.

Next, publish the base scoring-input lock before invoking the unchanged scorer. No score or actual-data fit has been computed. Required verification before this publication: **857 passed, 3 skipped, zero failures in 458.48 seconds**, direct exit 0, with Lean integration required ([receipt](phase2/evaluation_scoring_monitor_publication_test.json)).
