# expt_v21 — Tiny repair admission handoff

## State (10-19-2026)

- Owner: `unattended_and_gap_sources`; worker/deployment owner: `cleanup_original_pool`.
- Deliverable: accepted-only training supplement from all 500 fixed tiny source tasks, with a complete outcome ledger and portable source/proof receipts.
- Source ready: `finalize_tiny.py` SHA-256 `53b2260793a443c82e494672513c1ea57dd856335b0040ed976f7bb45bebc00e`.
- Pure comment adapter ready: `add_missing_inline.py` SHA-256 `ad8bea2bd9e5d7c06294a4a297ead1b236bcef733fabce2de23961e6bef32253`.
- Root approved deterministic comment-only annotation with exact raw checked-source receipt, balanced lexical contexts, identical non-comment tokens and explicit two-source provenance. No additional model call or Lean compilation.
- Actual preflight: 305/305 then-accepted sources passed; 35 required the adapter; maximum assistant loss span 447 tokens. This is a preflight subset, not the final declared-cohort result.
- Finalizer and adapter deterministic controls pass; evidence is in `results/finalization_controls.json`, `results/inline_comment_helper_controls.json` and `results/finalization_comment_preflight.json`.
- Finalization waits for all 125 batches to be `DONE`, then accounts for all 500 rows. Every final training row requires strict proof scope, sketch and inline comments, actual FILE/Qwen format, fewer than 1,000 assistant loss tokens, protected-data screen and global dedup.
- Dedup baseline is the immutable running experiment 20 cohort: `corpus_training_v20/base/data/training.jsonl`, SHA-256 `0882a88925e862b44fd79b7592d8d525829aec1f2ac1bd12afa1fd43fc6a5de7`.
- Deployment owner holds `lean_corpus_v21/finalizer_hold.json` while updating these source files. Remove that hold only after their exact hashes are deployed and verified; worker lanes continue independently.
- Command after all batches finish: existing training virtual-environment Python, `finalize_tiny.py --baseline /lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v20/base/data/training.jsonl`.
- `lean_corpus_v21/final/` publishes atomically; root completion follows. Existing final directories are immutable. Failed build directories are evidence and never training inputs.
- No training launch by this admission phase; live experiment 20 data and optimizer remain unchanged.

## Event log

- 10-19-2026: Completed source-bound receipt/schema preflight, observed missing inline comments, implemented the explicitly approved pure comment-insertion adapter, and handed stable hashes plus actual 305-row preflight evidence to the deployment owner.
