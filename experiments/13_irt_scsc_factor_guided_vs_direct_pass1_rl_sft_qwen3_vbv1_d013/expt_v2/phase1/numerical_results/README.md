# Experiment 13 v2-S2: closed train numerical results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/numerical_results/README.md>

**TLDR:** These four tables copy the saved numerical scoring receipts for all 12,936 anchor slots and all 512 A6 diagnostic slots. No model call, scoring operation, fitting or gate was repeated to produce them. The accompanying manifest hashes both the original receipt and its numerical table.

`task` and `group` are shared anonymous ordinal identifiers across the four tables; `sample` is the original sample index. Task identities, task text and raw responses stay private. All 539 train tasks and 400 task groups are represented across the anchors. Empty cells mean unknown, not zero. `d` is the declaration fraction, `p` the proved-theorem fraction, `e` the nonempty-extracted-source indicator, and `t` the implementation/example score; numerator and denominator are retained separately. `strict` and `compile` retain the frozen scorer's recorded values, with their original measurement status.

The tables preserve the group membership needed for descriptive resampling and every unmeasured slot. See [anchor results](../../RESULTS_ANCHORS_S2.md) and [A6 diagnostic results](../../RESULTS_A6_DIAGNOSTIC_S2.md) for the frozen criteria, intervals, missingness interpretation and scope. A6 is a pipeline diagnostic and never enters the comparison's efficacy statistics.
