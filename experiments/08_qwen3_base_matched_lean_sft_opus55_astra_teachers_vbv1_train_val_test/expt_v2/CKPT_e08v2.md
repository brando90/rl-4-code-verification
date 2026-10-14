# Experiment 08 version 2 checkpoint — matched step-658 test evaluation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/CKPT_e08v2.md>

**TLDR:** This is the resume record for version 2: a one-time test evaluation of 1.7B, 4B and 14B at step 658, so all four sizes are compared after identical SFT (same data, 658 updates, 5,752,936 tokens). The binding protocol is `PROTOCOL_v2.md` and the runbook is `cc.md`.

**Created:** 10-13-2026 17:02 PDT (Claude master). **Last updated:** 10-13-2026 17:22 PDT

## Goal
Compare four Qwen3 sizes at step 658 / 5,752,936 supervised fine-tuning tokens on VeriBench V1 test, preserving version 1.
## What ran
- **Launch receipt, 10-13-2026 17:07 PDT:** host skampere1; tmux `codexv-rl4cv-e08v2-matched-test`; client `codex-vals` (Vals ChatGPT workspace, `CODEX_HOME=~/.codex-vals`); model `gpt-6-astra`, effort `high`; flags `--dangerously-bypass-approvals-and-sandbox` (full access, approval never), observed in `/proc/2972451/cmdline`; PID 2972451; deployment `deploy_e6c90b4a14374fbe81cb42a3fc065263`; clone `$WORK/rl-4-code-verification` at `f2c63f8`. First actions observed: read `cc.md`, refreshed agents-config, read `INDEX_RULES.md`. `[RUN START]` email sent 17:09 PDT to all four of Brando's inboxes.
- **Model choice:** Codex `gpt-6-astra` high, because this is a well-specified but integrity-critical pipeline adaptation, on the Vals workspace that ran version 1. Fallbacks: personal Codex `gpt-6-astra` high (`~/.codex`), then `clauded-vals` `claude-fable-5-1` high, then `clauded`.
- Session `codexv-rl4cv-e08v2-matched-test`; deployment `deploy_e6c90b4a14374fbe81cb42a3fc065263`; gpt-6-astra / high (verified process 2972451, native child 2972470); danger-full-access / never.
- Runbook read fully; rules refreshed; main f2c63f8; version 1 DONE and no live writer; installed scipy/psutil into test environment; baseline: 328 passed / 4 skipped / 4 inherited CODEX_HOME failures; environment-corrected full suite: 338 passed / 4 skipped in 292.21 s (includes six admission tests).
## Results
- 0/5,328 new cells generated; no judge calls. All five input hash checks PASS; route identity and 3/3 freshly downloaded judge files match version 1. START email sent 17:18 PDT. Results ledger: `experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/results.md`.
## Stuck / blocked
- Nothing; test process uses `env -u CODEX_HOME` only; no source repair. Home repository alias missing, actual checkout CLAUDE.md loaded.
## Next steps
- [p 10/10] Publish admission manifest and scripts: `git diff --check`, explicit stage, commit/pull/push; then launch leased driver sessions (cc.md §§ 2–3).
- Runtime root `/lfs/skampere1/0/brando9/rl4cv_e08/v2`; one writer; expected runtime 8–16 h; judge estimate ~$225 plus ~$3 controls, Vals route only; allowance unknown.
## Brando to-do
- None.

## Log

- 10-13-2026 17:02 PDT -- master created the protocol, forecast, runbook and this checkpoint; dispatch next.

- 10-13-2026 17:12 PDT -- worker accepted deployment; version 1 writer check clear; baseline tests and input verification started.

- 10-13-2026 17:21 PDT -- inputs verified; full corrected make test 338 passed / 4 skipped; admission tests and fake-mail watchdog self-test pass; START email delivered.

- 10-13-2026 17:11 PDT -- master dispatched the worker (codex-vals gpt-6-astra high, full access verified, PID 2972451) and sent [RUN START]; runbook § 8 now adds the idle-nudge watchdog and the checkpoint location.

- 10-13-2026 17:22 PDT -- integrated master launch receipt/runbook update; preserving both logs. Master START email at 17:09 was learned after worker START at 17:18; no further START email. Canonical checkpoint here; launch-named local copy lives in $WORK/v2.
