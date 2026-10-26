# Experiment 20 saved-smoke T1 decision-input analysis

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/RESULTS_saved_smoke_t1.md>

**TLDR:** The saved smoke receipts establish an E20 gate failure: the maximum sampled-token mismatch share is **2.6198166568%** (22,654/864,717) against the frozen E20 limit of **≤1%**. They retain enough aggregate information to establish nonzero unsupported sampled actions (167, then 195), but not exact median or 99th-percentile (p99) absolute log-probability differences nor mismatch slices by task, rollout, token, or position.

## Scope and frozen comparison

This is CPU-only analysis of saved receipts for `experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/`. No new model measurement or gate change was performed. Exact descriptive counts from one run with two updates; p-val=n/a; uncertainty across independent training runs is unmeasured.

`experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/PROTOCOL.md` defines V4-T1's separate frozen eight-response probe: median absolute generator–trainer error ≤0.01, p99 ≤0.10, and zero sampled tokens outside the trainer's recomputed support. The comparison below is decision input only; it does not rename E20 smoke as T1 or change either gate.

## Saved mismatch evidence

| update | tokens | in support | unsupported sampled actions | absolute difference > 0.05 in support | E20 gate numerator / token denominator | E20 share | finite mean absolute difference | finite max absolute difference |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 842,189 | 842,022 | 167 | 21,721 | 21,888/842,189 | 2.5989415677% | 0.0041481149 | 1.3290288448 |
| 2 | 864,717 | 864,522 | 195 | 22,459 | 22,654/864,717 | 2.6198166568% | 0.0042040888 | 1.3342747688 |
| pooled | 1,706,906 | 1,706,544 | 362 | 44,180 | 44,542/1,706,906 | 2.6095168685% | 0.0041764709 | 1.3342747688 |

The frozen E20 gate uses the maximum update share, so update 2's **22,654/864,717 = 2.6198166568%** is the recorded failure. Unsupported actions are specifically sampled tokens outside the trainer's recomputed **truncated** support. The saved full-softmax diagnostic necessarily reports zero outside-support tokens, but still reports absolute difference > 0.05 shares of 2.9479131169% and 3.0318589781%; it is not an unsupported-action breakdown.

## T1 statistic recoverability and defensible bounds

The runtime computed `mismatch_summary` and persisted only token counts, in-support count, count above 0.05, finite mean absolute difference, and finite maximum. It did not persist the delta vector, a histogram, quantiles, token IDs, or per-rollout support flags. Therefore exact median and p99 are **unavailable** from the saved material.

For finite in-support tokens, absolute differences are nonnegative. Since at least half of values are at least the median, `median ≤ 2 × mean`; since more than 1% of finite tokens have absolute difference > 0.05, finite p99 is strictly greater than 0.05; it cannot exceed the saved finite maximum. These are bounds, not reconstructed quantiles.

| update | exact median | finite median bound | exact p99 | finite p99 bound | T1 decision input |
|---:|---|---:|---|---|---|
| 1 | unavailable | [0, 0.0082962299] | unavailable | (0.05, 1.3290288448] | median bound is below 0.01; p99 versus 0.10 remains undecidable; unsupported count is nonzero |
| 2 | unavailable | [0, 0.0084081776] | unavailable | (0.05, 1.3342747688] | median bound is below 0.01; p99 versus 0.10 remains undecidable; unsupported count is nonzero |
| pooled | unavailable | [0, 0.0083529418] | unavailable | (0.05, 1.3342747688] | same |

Thus the saved aggregates imply the finite-median portion of the T1 decision input is bounded above by less than the 0.01 requirement, do **not** decide the p99 ≤0.10 requirement, and decisively fail the analogous zero-unsupported condition (167 and 195 actions). This does not alter the already-failed E20 gate.

## Overall comparison and other T1 requirements

**The analogous smoke would FAIL T1's zero-unsupported requirement.** The 195 unsupported actions comprise 0.02255% of update 2 tokens and 0.86078% of its 22,654 mismatches; the other 22,459 mismatches are finite in-support errors above 0.05 (2.59727% of all update 2 tokens). The unsupported actions are positions, not 195 unique token identities or tasks.

Treating unsupported errors as infinite gives all-token median upper bounds of 0.00829788 and 0.00841007 (finite error sum divided by half the token count minus unsupported count), still below 0.01. Exact median and p99 remain unavailable. T1 also requires identical generator/trainer supports at at least 99% of positions and importance-ratio truncation at cap 2 on at most 1% of tokens, and reports discarded-mass quantiles. Those measurements were not retained and cannot be reconstructed from the saved aggregates. Zero unsupported is already decisively violated; none of these comparisons changes E20's FAILED trainer verdict.

## Recoverable slices

- **By update:** fully recoverable above.
- **By component:** truncated-support mismatch has 167 and 195 unsupported actions. Full-softmax uses all vocabulary as support and has zero unsupported by construction; it is only a comparison diagnostic.
- **By task / rollout / token / token position:** unavailable for mismatch outcomes. The saved rollout ledger has 128 rollouts and 16 task IDs per update, eight rollouts per task, with update token totals of 842,189 and 864,717; but its fields contain no log-probability delta or support membership. Joining it would create unsupported attributions.
- **Saved context:** update 1 has 35/128 length-truncated rollouts and update 2 has 38/128; this is rollout context only, not a mismatch slice.

## Provenance and integrity checks

The canonical receipt, both preserved copies, and the rollouts ledger were compared as listed in the companion JSON. Canonical mismatch JSON/log content matches both saved copies. The analysis reports no new measurement and makes no causal claim about why the unsupported actions occurred. [Reproducible parser](expt_v1/analyze_saved_smoke_e20.py), [machine-readable breakdown](expt_v1/results/smoke_t1_analysis.json).

**TLDR-end:** [rl4cv: saved smoke analysis] E20's frozen trainer gate remains failed at 2.6198166568%; exact median/p99 and token/task/position mismatch slices were not retained, while nonzero unsupported actions are directly established.

**Snapshot:**

- Two updates; 1,706,906 sampled token positions.
- 362 unsupported actions: 167 then 195.
- 44,180 finite in-support errors above 0.05.
- Exact median/p99 and task/token mismatch identities unavailable.
- Analogous T1 comparison FAIL; original E20 trainer verdict FAILED.
