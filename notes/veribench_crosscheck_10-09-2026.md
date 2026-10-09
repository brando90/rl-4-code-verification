# VeriBench crosscheck — exposure and record issues (10-09-2026)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/notes/veribench_crosscheck_10-09-2026.md>
**TLDR:** Independently re-counted receipts (VeriBench `experiments/ideas/rl4cv_factored_scsc_results_implications_for_vb/AUDIT.md`, commit `891cc9a1cd`) confirm two of VeriBench's human-rated task pools overlap rl4cv's kept fine-tuning set, and surface four stale/wrong rl4cv records, now fixed or flagged below.
Created: 10-09-2026

## VeriBench exposure crosswalk

Both counts are against rl4cv's kept fine-tuning set (experiment `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test`, 476 distinct VeriBench V1 (VBV1) tasks across train/validation/test by decision D-013: 539/135/222).

| VeriBench pool | Tasks | Overlap with rl4cv's kept SFT set | By rl4cv's D-013 split |
|---|---:|---:|---|
| Experiment 100's 75-item human-rated pool | 25 | 13/25 (6/10 of the human test-split tasks) | 17/25 all-D-013 train, 2 validation, 6 test (see `human_overlap` in AUDIT.md) |
| Experiment 102's set N | 25 | 9/25 | 15 train, 2 validation, 8 test (see `setN_overlap` in AUDIT.md) |

**Rule stated in both VeriBench READMEs (added 10-09-2026, VeriBench commit pending):** rl4cv-trained models are evaluated on rl4cv's own 222-task D-013 test split and labelled with their exposure. These old human-rated tasks are not fresh holdouts for rl4cv models — a rl4cv model's score on them cannot be read as held-out performance.

No FSC or SCSC value from VeriBench experiments 102, 103 or 106–110 appears in this note or in the VeriBench edits (agents-config rater-blinding limit: Brando is a blinded rater in experiment 102's round).

## rl4cv record issues

1. **Experiment 05 — mislabeled 1.7B-Base IC_tests count.** Fixed with a dated note in [`../experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/results.md`](../experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/results.md): the execution-diagnostics table's "Compiling (`IC_tests=1`)" column said 34 of 7,168 for Qwen3-1.7B-Base; the receipts (`IC_tests` mean 0.00028 × 7,168 ≈ 2) show only 2 satisfy `IC_tests = 1`.
2. **Experiment 05 — understated 4B binary-pass count.** Fixed with the same dated note: the "Representative completions" prose said "the one genuine `kernel_binary = 1` pass across all 21,504 cells," but the headline table's own 4B pass@8 share (0.006 ≈ 5/896 tasks, each contributing exactly one passing sample per the Core/IndustrySet histograms) and the independent audit (`e05_qwen3-4b-base.binary_pass_samples = 5`) show 5 passes for 4B alone, not 1 across the whole run.
3. **Root README — stale "small models are unmeasured" status.** Fixed: [`../README.md`](../README.md) said no model at or below 14B had ever been evaluated on VeriBench; experiment 05 (done 10-05/06-2026) measured Qwen3-1.7B/4B/8B-Base at G=8 on all 896 VBV1 tasks. Status line now points to experiment 05 and states the "SFT warm start needed" verdict instead.
4. **Experiment 02C README/code mismatch — flagged, not resolved.** [`../experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_c_reward_channel_for_fsc_kernel_vs_judge/README.md`](../experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_c_reward_channel_for_fsc_kernel_vs_judge/README.md) says "the judge runs asynchronously, only on responses with `IC_tests · IC_proofs > 0`" (both mechanical factors positive — that is actually the `scsc` channel's gate). The code it names, `src/rl4cv/rewards.py` `fsc_compiled`/`needs_judge` (lines 77–96), gates the phase's own `fsc_compiled` channel on `ic_tests == 1.0 and vacuous_theorems == 0` only — it does not require `IC_proofs > 0`. Experiment 02C has no `PROTOCOL.md` (only phase A and phase B do) and its status is still "TODO, after experiment 02A," so no locked protocol settles which gate is intended. A dated flag is added to the 02C README asking whoever locks its protocol to pick one side and update the other; not resolved here per the runbook's instruction to flag rather than choose absent a settling protocol.

## Sources

- VeriBench `experiments/ideas/rl4cv_factored_scsc_results_implications_for_vb/AUDIT.md` and `REPRODUCE.md`, commit `891cc9a1cd` (deterministic recount, exact census, no sampling interval).
- rl4cv `experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/results.md` (pre-fix) and its `expt_v1/results/analysis_e05.json` / `analysis_e05_table.md`.
- rl4cv `experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/sft_set_manifest.csv` (1,315 kept rows, 476 distinct tasks).
- rl4cv `src/rl4cv/rewards.py`.
