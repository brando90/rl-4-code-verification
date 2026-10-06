# Execute factor feedback repair and prospective environment preparation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/CKPT_MASTER_tmuxnone_cxd_01a10d32.md>

**TLDR:** This coordinator executes `04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2` and the prerequisite preparation in `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics`. The separate Qwen3 Base run remains owned by its existing worker. Resume from current receipts, not old status prose.

Created: 10-05-2026 22:33 PDT
Last updated: 10-05-2026 22:33 PDT

## Identity and recovery

- Master: Codex desktop thread `01a10d32-a3b2-7d70-a8e9-764e40592ed5`, `/Users/brandomiranda/rl-4-code-verification`, no local tmux. Full access, approval never. Resume: `codex resume 01a10d32-a3b2-7d70-a8e9-764e40592ed5`.
- Remote owner: one Codex execution worker, selected `gpt-5.6-terra` / high, in `/lfs/skampere1/0/brando9/rl4cv_azalia_execute/rl-4-code-verification`; session `rl4cv-azalia-external-v3`. Launch not yet verified in this checkpoint revision.
- Read [runbook](04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v3/cc.md), [dispatch manifest](04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v3/dispatch_manifest.json), and [live ledger](04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v3/results.md).

## Hazards and owned work

- The older Qwen3 Base run in `/lfs/skampere1/0/brando9/rl4cv_e05` is a read-only dependency; never duplicate or change it. Branch `e05-qwen3-base-vbv1-g8-sft-derisk` has newer work absent from local main.
- Shared distributed storage is almost full; all sizeable new outputs use local scratch. Health checks pass for the selected local-scratch toolchain. Small existing global client/auth state remains on the shared installation.
- Parent prepares local files, then hands versions2/3 of experiment04 and versions2 of experiment02 phases A/B to the sole remote writer. After acknowledgement, avoid local edits there until remote changes are synchronized.
- Synthetic controls are engineering validation only. Real external references and applicability remain necessary before the repair experiment. No VeriBench training, tuning, warm starts or checkpoint selection.
- No new benchmark-reference labels or edits. Any reference problem is recorded as unavailable instead of silently corrected.

## Watches

The version3 `supervise.py` writes process/boot identities every 120 seconds and permits one coordinator restart only after owned processes have stopped; child jobs survive coordinator exit. It does not claim scientific success from exit status. Reboot auto-restart is not installed. A same-thread heartbeat will verify outcomes and recover dependencies; record its actual identifier after creation. No collaborator messages or email notifications are authorized by this runbook.

## Decisions and next commands

- [p 10/10] Compile the complete endpoint controls, because invalid acceptance would invalidate all downstream comparisons.
- [p 9/10] Finish real external source screening and 24-task applicability before repair inference; do not replace inaccessible tasks with easy successes.
- [p 8/10] After real probes, freeze numeric environment forecasts before training outcomes; exact submitted-paper code/config/warm starts remain unconfirmed until retrieved.

Runbook makes bounded implementation decisions without further permission questions. Large training manifests and capacity must become concrete before admission; current measured pilot ceiling is one graphics processor, six graphics-processor hours and 24 processor hours. Read current remote `runtime/supervisor.json`, `ack.json`, `progress.json`, `worker_completion.json` and task result ledgers to continue. Verify all final counts, output hashes, tests and main publication before closing the watch.
