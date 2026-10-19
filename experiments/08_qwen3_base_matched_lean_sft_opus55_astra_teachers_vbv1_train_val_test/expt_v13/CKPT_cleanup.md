# V13 checkpoint: Original Python-to-Lean proof cleanup

**Doc link:** [Results](results.md)

**TLDR:** DONE_PARTIAL: 818 replacements pass kernel, format, token-cap and protected-overlap checks. All 2,585 rows are accounted for; V12 independently accepted the completion contract and automatically started the second training preparation.

Created: 10-19-2026 06:10 PDT
Last updated: 10-19-2026 10:28 PDT

## State

- Owner: `/root/cleanup_original_pool`; local edits only in this V13 directory, no Git publication by worker.
- Remote: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v13`.
- Source: original 2,585 JSONL rows; SHA `7fa0255741a2b6046ceda0dfda43664334ca603a0aeca9fc2424af43c849726b`.
- Actual parser: 2,585 successful, 100,234 proof terms; 2,358 targets, 227 UNCHANGED; zero exact-context saved alternatives.
- Model: `gpt-5.6-terra`, high; Codex 0.114.0, actual turn-context metadata verified; local context report 121,600 tokens.
- Initial cleanup cap $240; preapproved second tranche cleanup cap $480; total campaign max $600. Shared ledger at `adaptive_1p7b_campaign/budget.json`.
- Per-attempt reserve $10, observed conservative estimate stop $1.20; 2 attempts/case, 4 candidate hashes, 900 seconds/CLI, 120 seconds/compiler.
- Controls: real pinned kernel positive/unsolved-negative, policy-negative, unchanged implementation/native tests, actual harmless-child cost termination and dead-driver recovery PASS.
- Complete: ordinary supervisor/finalizer finished; zero paid cleanup CLI or in-flight budget reservation remains.
- Final: 818 accepted replacements + 227 unchanged originals + 1,540 flagged original fallbacks = 2,585; protected exact/near hits 0/0 over 764 references.
- Completion SHA: `9fd305accd57d7ef2c2c75082918b8f742be12920656cb93ca679f0e79379f93`; replacement SHA: `ad84f18d0273a243190f5e213702224a8a979299d61b43aa40b4196c716e1982`.
- Full training SHA: `0ada06ed829d2012c77374af3ad3e1eec02555d2a8ca901d8d218a6a084bd974`; row/order/prompt/fallback-byte contract PASS in final/contract_receipt.json.
- Settled estimates: ordinary $237.391247; conservative $469.991219; cleanup reservation $0. No rate/ceiling changes.
- Handoff: V12 training owner independently verified completion and automatic watcher started PREPARE_RUNNING (assembler PID3691394), prefers free GPU1. Root owns final Git publication; this worker performs no Git mutations.
- V12 consumer waits for root `completion.json` and `final/replacements.jsonl` with `replacements_sha256`; every one of 2,585 rows must be accounted.
- No blocker; compilation uses existing cluster CPUs. Credentials remain private LFS, never copied into the experiment.

## Event log

- 10-19-2026 06:10 PDT: Preparation and actual controls complete; no paid calls before protocol freeze.
- 10-19-2026 06:14 PDT: First four real cases passed all kernel/format/screen gates; full23-worker pool and remote death/budget/finalization supervisor active. Local sources compile; runtime hashes and compact receipts collected. Ready for root publication.
- 10-19-2026 10:27 PDT: Root requested immediate comparison freeze after budget-reservation headroom collapsed to one worker and delayed training. Prospective amendment/queue admission flag written at 10:25:25; 1,445 unattempted rows became explicit original fallbacks. Adopted the last healthy CLI within its original time/cost limits, prevented a second paid attempt, and settled its existing reservation once; it passed, yielding 818 kernel-verified replacements. Full finalization now runs; training owner notified.
- 10-19-2026 10:28 PDT: Full finalization admitted all 818 kernel-passing replacements, zero format/token/overlap exclusions; all 2,585 rows and original fallback bytes verified. Completion/replacement/training hashes bound in contract receipt. V12 watcher fired automatically within five seconds and training owner confirmed PREPARE_RUNNING. Final source/amendment/tables collected locally for root publication.
