# Experiment 08 version 2 checkpoint — matched step-658 test evaluation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/CKPT_e08v2.md>

**TLDR:** This is the resume record for version 2: a one-time test evaluation of 1.7B, 4B and 14B at step 658, so all four sizes are compared after identical SFT (same data, 658 updates, 5,752,936 tokens). The binding protocol is `PROTOCOL_v2.md` and the runbook is `cc.md`.

**Created:** 10-13-2026 17:02 PDT (Claude master). **Last updated:** 10-13-2026 17:11 PDT (Claude master, worker dispatched and verified).

## Goal

Compare the test SCSC (the smooth conjunctive score for code verification) of Qwen3 Base 1.7B, 4B, 8B and 14B after the same SFT (step 658, 5,752,936 loss tokens) on VeriBench V1's 222 test tasks × 8 samples, against each matched Base model.

## What ran

- 10-13-2026: the master locked `PROTOCOL_v2.md` and froze the forecast `forecasts/e08v2_matched_step658_test.json` (SHA-256 `cb6661dd…`) before any version 2 test generation.
- **Launch receipt, 10-13-2026 17:07 PDT:** host skampere1; tmux `codexv-rl4cv-e08v2-matched-test`; client `codex-vals` (Vals ChatGPT workspace, `CODEX_HOME=~/.codex-vals`); model `gpt-6-astra`, effort `high`; flags `--dangerously-bypass-approvals-and-sandbox` (full access, approval never), observed in `/proc/2972451/cmdline`; PID 2972451; deployment `deploy_e6c90b4a14374fbe81cb42a3fc065263`; clone `$WORK/rl-4-code-verification` at `f2c63f8`. First actions observed: read `cc.md`, refreshed agents-config, read `INDEX_RULES.md`. `[RUN START]` email sent 17:09 PDT to all four of Brando's inboxes.
- **Model choice:** Codex `gpt-6-astra` high, because this is a well-specified but integrity-critical pipeline adaptation, on the Vals workspace that ran version 1. Fallbacks: personal Codex `gpt-6-astra` high (`~/.codex`), then `clauded-vals` `claude-fable-5-1` high, then `clauded`.
- Preflight: skampere1 is reachable; the `snap_health` audit's only FAIL is `disk.dfs` (off this job's LFS path). All four step-658 exports exist (1.7B 7.6G, 4B 17G, 8B 31G, 14B 56G). Six of eight A100s were idle at 16:54 PDT.

## Results

None yet. 0 of 5,328 new cells generated; 0 judge ratings.

## Stuck / blocked

Nothing.

## Next steps

1. Worker (running): runbook §§ 0–9, from the inputs check through the `[RUN DONE]` email.
2. Master: watch the worker for done, dead, blocked or idle (Rule 69); verify the final publication.

## Brando to-do

None.

## Log

- 10-13-2026 17:02 PDT -- master created the protocol, forecast, runbook and this checkpoint; dispatch next.
- 10-13-2026 17:11 PDT -- master dispatched the worker (codex-vals gpt-6-astra high, full access verified, PID 2972451) and sent [RUN START]; runbook § 8 now adds the idle-nudge watchdog and the checkpoint location.
