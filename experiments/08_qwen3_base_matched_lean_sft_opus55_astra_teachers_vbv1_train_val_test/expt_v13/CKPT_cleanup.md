# V13 checkpoint: Original Python-to-Lean proof cleanup

**Doc link:** [Results](results.md)

**TLDR:** The first four real Terra/high replacements passed kernel and all format/screen checks. The full worker pool is running under an ordinary remote supervisor; all 2,585 cases will be finalized with verified replacements or explicit original fallbacks for the matched second training run.

Created: 10-19-2026 06:10 PDT
Last updated: 10-19-2026 06:14 PDT

## State

- Owner: `/root/cleanup_original_pool`; local edits only in this V13 directory, no Git publication by worker.
- Remote: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v13`.
- Source: original 2,585 JSONL rows; SHA `7fa0255741a2b6046ceda0dfda43664334ca603a0aeca9fc2424af43c849726b`.
- Actual parser: 2,585 successful, 100,234 proof terms; 2,358 targets, 227 UNCHANGED; zero exact-context saved alternatives.
- Model: `gpt-5.6-terra`, high; Codex 0.114.0, actual turn-context metadata verified; local context report 121,600 tokens.
- Initial cleanup cap $240; preapproved second tranche cleanup cap $480; total campaign max $600. Shared ledger at `adaptive_1p7b_campaign/budget.json`.
- Per-attempt reserve $10, observed conservative estimate stop $1.20; 2 attempts/case, 4 candidate hashes, 900 seconds/CLI, 120 seconds/compiler.
- Controls: real pinned kernel positive/unsolved-negative, policy-negative, unchanged implementation/native tests, actual harmless-child cost termination and dead-driver recovery PASS.
- Active: `rl4cv-terra-clean-watch-v13`; paid sessions `codex-rl4cv-terra-clean-v13-00` onward, 23 at snapshot; 16 compiler slots.
- Latest: 12 kernel passes, 23 RUNNING, 2,323 PENDING, 227 UNCHANGED; settled ordinary estimate $1.5042, conservative charge $3.1058, $230 reserved (estimates, not invoices).
- Next: ordinary supervisor continues; inspect `progress.json`, `row_progress.csv`, `watch_heartbeat.json`, then final `completion.json`. Local collector: `python3 sync_cleanup.py`.
- V12 consumer waits for root `completion.json` and `final/replacements.jsonl` with `replacements_sha256`; every one of 2,585 rows must be accounted.
- No blocker; compilation uses existing cluster CPUs. Credentials remain private LFS, never copied into the experiment.

## Event log

- 10-19-2026 06:10 PDT: Preparation and actual controls complete; no paid calls before protocol freeze.
- 10-19-2026 06:14 PDT: First four real cases passed all kernel/format/screen gates; full23-worker pool and remote death/budget/finalization supervisor active. Local sources compile; runtime hashes and compact receipts collected. Ready for root publication.
