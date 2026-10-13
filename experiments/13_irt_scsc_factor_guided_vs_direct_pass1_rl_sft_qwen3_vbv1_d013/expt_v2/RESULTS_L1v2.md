# Experiment 13 version 2 measurement and forecast lock

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_L1v2.md>

**TLDR:** L1v2 freezes the accepted measurement pipeline, complete historical manifests, prediction implementation and carried forecasts before any version-2 validation or test factor. R2 is admitted only after this publication.

Frozen: 10-13-2026 13:49 PDT. Implementation commit: `3e5f159079f07fa1e741b503e93ea3e8234693c3`.
Lock SHA-256: `1578f86fa5f01af3d56a02d30cdbc27bb199b29f677f48dbddcbae34304fe875`. All 51 file bindings were verified before publication.

| Binding | Frozen value |
|---|---|
| R0 acceptance | Attempt 2 PASS, 30/30 authored fixtures; attempt 1 unchanged |
| R1 acceptance | Attempt 1 PASS, 400/400 train cells; 300 rejected plus 100 measured |
| Full cohort | 38,784 unique sources: base 21,504 + ladder 20,520 - overlap 3,240 |
| Family-specific oracle comparisons | 42,024; shared sources measured once, with both historical readbacks retained |
| Ordinary route | 33,456 cells: 12,936 train + 20,520 validation |
| Opaque test route | 5,328 cells; completeness, hashes and equality only |
| Unavailable parent ladder | 5,400 separately declared cells |
| F0v2 | Dense-only 4B validation task share 0.50, carried from PROTOCOL section 8 |
| F1v2 | Selected conjunctive-model full-schedule policy Pearson correlation 0.85, carried from PROTOCOL section 8 |
| Required implementation suite | 300 passed, 23 unrelated skips, 165.29 seconds; required Lean integration enabled |

The numeric forecasts retain version 1's history. Its original forecast wrappers and their hash ledger are embedded/bound in [F0v2](locks/F0v2.json) and [F1v2](locks/F1v2.json). Their old timestamps are not prospective registration of this changed procedure. Version-1 ledger digests use canonical JSON; the version-2 history records raw-file SHA-256 digests, so those two digest forms differ without changed content. Version 1 privately computed 6,739 base equality results without publishing per-cell values or factors; the master has not read those outcomes. Published experiment-08 validation aggregates informed the original design. Version 2 has observed only authored fixtures and the 400-cell train diagnostic. It has computed zero validation/test factors at this lock.

The prediction lock records numerical libraries, identified models, five starts, priors, inner/outer grouping, random-effect integration, feature encoding, calibration and synthetic-recovery controls. The two owner-defined calibration/recovery operational thresholds are explicitly prospective; no historical validation fit has been performed. Test rows cannot enter that model harness. [Prediction specification](prediction/README.md).

The [execution lock](locks/R2_execution.json) admits 48 global workers, a 64 GiB per-worker address-space limit and an aggregate cap of 1,044,624,427,008 bytes. Admission falls with available host memory; no device allocation or model call is involved. R1 measured a complete-cell 99th-percentile tree peak of 6.452 GiB. Its combined old/new path took 18.298 seconds per cell on average, giving a conservative R2 estimate of 4.11 hours at 48 workers, or 5.13 hours with the recorded reserve. Actual throughput will be reported.

R2 must account for every cell and reproduce each measured oracle value/status, except reported typed deterministic limits; an untyped inconsistency or opaque discrepancy blocks admission. Missing measurements are INCOMPLETE and never advance. No gate retries are allowed after L1v2; the persistent per-cell ledger permits only one identical infrastructure retry. G0 remains at least 21/135 dense-only tasks and area under the receiver-operating curve at least 0.65 on its specified earlier-zero-success subset. Undefined one-class discrimination fails.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2's measurement and prediction procedure is frozen before held-out factors; full opaque-routed reproduction is next.
**Snapshot:** L1v2 frozen; F0v2 0.50; F1v2 0.85; R2 0/38,784; test outcomes undisclosed.
