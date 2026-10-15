# Experiment 13 v2-S2 train mutation audit cohort

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2/TRAIN_AUDIT_COHORT_S2.md>

**TLDR:** Freeze 32 train groups and four variants per task before reading anchor scores. This fixes the cohort and mutation operators; the complete source-input and execution lock must precede new audit measurements or learning.

The [cohort lock](../locks/TRAIN_AUDIT_COHORT_S2.json) binds the earlier private draft and its exact frozen copy. The earlier draft SHA-256 is `04b6585c37edd3c02cad63b114f4059a525cc49b3781743219767bbc2754b33b`; the frozen cohort is `02bd5932cc022ee3a3ee8b659f0d198fe8b1eff18adc2aa3ee8f8a40f9b92879`. No anchor score, benchmark mutation measurement or actual-data fit has been read or computed for this choice.

Select 32 of the 400 train groups uniformly without replacement: NumPy `default_rng(1302251).permutation(sorted_group_ids)[:32]`, then the lexicographically first task within each selected group. Reproduction exactly matches the existing draft; all 32 distinct tasks belong to the frozen 539-task train allowlist and have a declared full-batch-1 sample-0 cell. Keep task identities private. The baseline is that sample, and its existing published strict/component measurement will be reused rather than repeated.

Every task declares these four variants, for 128 total:

- Original source, unchanged.
- Padding: append eight fresh digest-named elementary natural-number addition theorems.
- Deletion: remove the last half, rounded up, of named theorem commands by source order.
- Substitution: replace every named theorem command with an elementary addition identity using the same short name.

The published mutation implementation uses complete frozen-frontend byte spans and has no reward or coverage input. Missing source or an unavailable complete frontend leaves affected variants explicitly missing. Preserve zero-theorem unchanged variants, dependency failures and compilation failures; do not choose another task, theorem or operator from outcomes.

Measure strict success, the fixed B reward, C reward under the frozen initial full-policy weights when C is admitted, theorem count, corrected hidden-test coverage and validated compile-gated formal specification coverage (FSC). Independent coverage controls already passed. Actual FSC still requires three declared repeats per member, the median within each member, then the mean of those two medians divided by five. Missing ratings remain unknown. Known compilation failure has compiled FSC zero; unresolved compilation remains missing. Report every reward-increasing mutation with its strict and available coverage change, retaining all 128 declared cells.

Before learning, freeze exact original/source/frontend provenance, generated mutation bytes, hidden suites, judge inputs and all executable bindings. During each B/C pilot run, use this same train cohort at its own start and updates 10, 20 and 30. Freeze monitoring generation randomness and pre-generation C weights in the pilot execution lock. The existing monitor stops that arm when mean reward rises while mean theorem count or available independent coverage drops more than 10% relative to its own start. An unavailable measurement route cannot establish continuation; cell-level missingness stays explicit in the declared cohort. Freeze the executable availability rule with the pilot execution lock before any monitoring measurements. There is no reward retuning, and a known mutation vulnerability alone is not an efficacy result.
