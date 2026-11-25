# Existing SFT readiness evidence and Sherlock replication follow-up

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/validation/results.md>

The broader supervised fine-tuning (SFT) effort already has completed validation results and nonzero reinforcement-learning (RL) signal. The two Sherlock replicas are a separate, still-unmeasured replication check; they are not needed to establish that SFT can produce signal.

**Status:** Existing-data audit COMPLETE; Sherlock validation: superseded, completed in expt_v16_sherlock_validation_v4 (QA 11-25-2026). **Last updated:** 10-19-2026 12:17 PDT.

## Recomputed existing validation evidence

All rows below have 1,080/1,080 known cells on the same 135 validation task IDs, eight answers each. These are different trained checkpoints, not new measurements of the Sherlock seeds. The exact source paths, hashes, all gates, histograms and Wilson 95% intervals are in [the reproducible cross-check](results/historical_readiness_crosscheck.json); source CSV tables are already committed at those paths.

| Existing condition | Binary successes | Mixed tasks (1–7/8) | Target band (2–6/8) | Extracted /1080 | Capped /1080 | Frozen gates |
|---|---:|---:|---:|---:|---:|---|
| original_1p7 | 53/1080 | 20/135 | 11/135 | 897 | 184 | FAIL |
| replay_1p7 | 65/1080 | 27/135 | 18/135 | 946 | 134 | FAIL |
| expanded_1p7 | 55/1080 | 19/135 | 14/135 | 959 | 121 | FAIL |
| tiny_control | 99/1080 | 30/135 | 18/135 | 979 | 101 | PASS |
| tiny_mixed | 74/1080 | 28/135 | 16/135 | 976 | 104 | PASS |
| current_corpus | 120/1080 | 24/135 | 16/135 | 971 | 110 | FAIL |

The latest completed current-corpus continuation is [expt_v12](../../expt_v12/results.md): 120/1080 successes, 11.11% [6.94%, 15.83%] by its committed 10,000-draw task bootstrap, seed0, retaining eight attempts per task; p-val=n/a. It has 24/135 mixed tasks (17.78%, Wilson95 [12.25%,25.09%]), and 16/135 in the two-to-six band. It has useful reward variation but misses the inherited extraction gate by one answer (971 versus972), the cap gate by two answers (110 versus108), and the 25% binary-accuracy milestone. These gates are unchanged; a near miss is not a pass.

The [seen/fresh diagnostic](../../expt_v7/results.md) reports 29/50 successes on seen functions (58%, Wilson95 [44.2%,70.6%]) and9/50 on fresh compositions (18%, [9.8%,30.8%]). This may explain a remembered high score, but its relevance to the user's specific score is unconfirmed. It is a different diagnostic, not full VeriBench validation.

## What is finished and what remains

- [expt_v6](../../expt_v6/results.md): both1.7B training/evaluation conditions complete;4B condition remains unfinished in its published record.
- [expt_v12](../../expt_v12/results.md): first current-corpus1.7B training and all1,080 validation cells complete. The25% target remains unmet.
- [expt_v20](../../expt_v20/README.md): newer from-Base training is active in the latest repository receipt read for this audit:460 optimizer updates,920 rows,762,543 loss tokens; no validation summary yet. These are repository observations, not a fresh remote process check.
- [expt_v19](../../expt_v19/results/publication_status.json): published host receipts still show waiting for transfer/full cleanup, with no production or validation result. Newer receipts take precedence over stale prose.
- [expt_v4 training](../results.md): both658-update trajectories complete, but those exact seeds do not yet have a full scored validation cohort. Their evaluation is useful for replication/seed stability, not a prerequisite to acknowledge existing signal or to finish newer SFT evaluation.
- The matched cross-size project still requires a common data/token recipe and validation-passing start across sizes (D-017); one passing1.7B result alone would not settle that claim. Actual RL improvement remains unmeasured by these pre-RL diagnostics.

## Sherlock execution evidence

Existing execution owner is preparing `/scratch/users/brando9/rl4cv_sherlock/v4_validation`; its files were actively updated during inspection. Preserve that owner's jobs; do not launch a second generation copy. Job48502119 was a cancelled40-cell smoke attempt stalled while reading archive weights. Replacement48505048 was queued at inspection; its updated script reads scratch copies and supports bothseeds plusBase. No full validation score was observed.

Full scratch weight hashes for bothseeds pass in job48504619 (exit0:0). Prepared validation prompts pass for135tasks. Pinned Lean scorer control job48483971 matches30/30reference fixtures and40/40positive examples. Scorer hashes match the frozen dependencies. These controls establish infrastructure, not model readiness.

`readiness.py` applies the existing gates to a complete scored CSV and emits an explicit INCOMPLETE verdict for missing cells. Five deterministic tests cover completeness, duplicate/unknown rejection, exact boundaries and high-score/all-pass degeneracy. A high score cannot substitute for the mixed-group count. The2–6band and25%binary milestone are separately reported under D-017; no unmeasured formal-specification judge aggregate is claimed.

The test split was not generated or scored for this follow-up. Existing published historical test summaries do not change the protocol. No new training, teacher calls or duplicate evaluation was launched in this audit.

**Copy-ready message:** I checked the existing SFT results: the latest completed1.7B continuation already has useful reward variation on24/135validation problems, including16in the target2–6/8band. It achieves11.11%binary success and narrowly misses the frozen format gates, so the newer training remains relevant; Sherlock's older replicas are a separate replication check.

**TLDR-end:** [rl4cv: SFT readiness audit] `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test` already has completed SFT evaluations and measured RL signal, but the latest completed1.7B condition does not meet all readiness goals. Its older `expt_v4` Sherlock replicas remain validation-pending and must not be confused with the broader project's progress.
