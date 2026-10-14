# Experiment 08 version 2 checkpoint — matched step-658 test evaluation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/CKPT_e08v2.md>

**TLDR:** This is the resume record for version 2: a one-time test evaluation of 1.7B, 4B and 14B at step 658, so all four sizes are compared after identical SFT (same data, 658 updates, 5,752,936 tokens). The binding protocol is `PROTOCOL_v2.md` and the runbook is `cc.md`.

**Created:** 10-13-2026 17:02 PDT (Claude master). **Last updated:** 10-13-2026 17:02 PDT (Claude master, before dispatch).

## Goal

Compare the test SCSC (the smooth conjunctive score for code verification) of Qwen3 Base 1.7B, 4B, 8B and 14B after the same SFT (step 658, 5,752,936 loss tokens) on VeriBench V1's 222 test tasks × 8 samples, against each matched Base model.

## What ran

- 10-13-2026: the master locked `PROTOCOL_v2.md` and froze the forecast `forecasts/e08v2_matched_step658_test.json` (SHA-256 `cb6661dd…`) before any version 2 test generation.
- Preflight: skampere1 is reachable; the `snap_health` audit's only FAIL is `disk.dfs` (off this job's LFS path). All four step-658 exports exist (1.7B 7.6G, 4B 17G, 8B 31G, 14B 56G). Six of eight A100s were idle at 16:54 PDT.

## Results

None yet. 0 of 5,328 new cells generated; 0 judge ratings.

## Stuck / blocked

Nothing.

## Next steps

1. Dispatch the worker: `deploy_cc.sh --name codexv-rl4cv-e08v2-matched-test --profile codex-vals --model gpt-6-astra --effort high --prompt-file expt_v2/cc.md`, on skampere1, in `$WORK/rl-4-code-verification`.
2. Worker: runbook §§ 0–9 (inputs check, frozen manifest and admission, generation and scoring, judge, analysis, publish, `[RUN DONE]` email).

## Brando to-do

None.

## Log

- 10-13-2026 17:02 PDT -- master created the protocol, forecast, runbook and this checkpoint; dispatch next.
