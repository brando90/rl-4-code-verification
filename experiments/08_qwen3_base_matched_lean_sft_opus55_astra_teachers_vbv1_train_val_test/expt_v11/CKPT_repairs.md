# Sol proof repair continuation

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v11/CKPT_repairs.md

**TLDR:** Generate and verify explicit repaired proofs for the68remaining unresolved cases.

Created: 10-19-2026 05:38 PDT. Last updated: 10-19-2026 05:43 PDT.
## Goal
- Actual Sol/high proof repair with unchanged target statements and explicit tactics.
## What ran
-16Sol/high workers `codex-rl4cv-sol-repair-v11-00`…`15`, full-access Codex CLI0.114.0 on skampere1;4native compiler slots.
-Remote owner `rl4cv-sol-repair-watch-v11` observes death, preserves2CLI/8candidate bounds, and owns final format/screens/worker cleanup.
## Results
-Actual repaired proofs are passing; live counts are inresults/progress.json. Positive, unfinished-proof and exact?-policy controls passed.
-One actual repair passed FILE/template/token checks and764protected screens; all repaired outputs receive the same finalization.
## Stuck / blocked
-Nothing known. Other corpus verification andGX10work continue independently; no new training.
## Next steps
-Read `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v11/progress.json`, `watch.log` and `completion.json`.
-Local publisher: `python3 sync_repairs.py --watch --publish`, native terminal `rl4cv-sol-repair-progress-v11`; only ordinary orchestration runs locally.
-Canonical project `/Users/lethan3/Documents/veribench-projects/rl-4-code-verification/`; temporary owner `/Users/lethan3/Documents/veribench-projects/.worktrees/rl4cv-sol-repair-10-19-2026/`.
-Root coordinator retains that checkout for live publication; preserve/mirror/publish final receipts and remove it after both watcher/publisher exit. Raw worker records stay on the cluster.
## Brando to-do
-None.
## Log
- 10-19-2026 05:38 PDT -- Prepared actual proof-repair protocol and new bounded Sol/high driver. Existing version10bulk andGX10work remain active.
- 10-19-2026 05:41 PDT -- RUNNING, 10-19-2026 05:41 PDT. Sol/high: 18/68 cases complete, 18 exact-source kernel-verified explicit repairs; 16 running and 34 pending.
- 10-19-2026 05:43 PDT -- RUNNING, 10-19-2026 05:43 PDT. Sol/high: 35/68 cases complete, 35 exact-source kernel-verified explicit repairs; 16 running and 17 pending.
- 10-19-2026 05:45 PDT -- Verified actual Sol repairs and warm-start-format preflight; full16-worker queue plus remote recovery/finalization owner are running.
