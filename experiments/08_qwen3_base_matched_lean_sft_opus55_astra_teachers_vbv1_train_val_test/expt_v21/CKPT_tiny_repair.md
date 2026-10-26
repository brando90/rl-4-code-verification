# V21 continuation checkpoint

**Doc link:** [Protocol](PROTOCOL.md)

**TLDR:** The 25 requested tiny repair workers are running on SNAP. No further authorization is needed within the existing shared budget. The ordinary supervisor owns recovery and finalization; V20 training continues independently.

## Ownership and frozen inputs

- `/root/cleanup_original_pool`: V21 worker preparation, execution and supervision; no Git staging or pushing.
- Root: V21 protocol/README and publication. Source agent: finalizer, comment-only adapter and admission controls. Training owner: V20.
- Original tiny source: `RUN/curriculum/training.jsonl`, 500 rows, SHA256 `2f50cd04757904b2ac703693c4520df813dd98e0f18881de92c515c7f87bb119`.
- V9 annotated source is retained as optional explanation material; it supplies no already strict whole-file proof.
- Frozen inspector SHA256: `5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287`.

## Running owners

- Worker sessions: `codex-rl4cv-terra-tiny-v21-00` through `24`; each owns 20 source cases and five four-case batches.
- Supervisor session: `rl4cv-v21-tiny-watch`; ordinary 15-second polling, bounded child recovery and idempotent usage accounting.
- Remote root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v21`.
- Budget helper: unchanged `expt_v15/campaign_budget.py`, shared ledger `RUN/adaptive_1p7b_campaign/budget.json`; total $900, cleanup $780. Per call: $10 exposure reservation, $1.20 observed conservative stop, 900 seconds. No other proof generation is authorized by this phase.

## Admission and next step

The strict finalizer and approved comment-only adapter are deployed. The temporary admission-source-update hold has been removed. Final admission uses the exact frozen 3,568-row V20 training file as duplicate baseline. It preserves all raw checked sources and receipts, with explicit comment-only source bindings when needed. No paid call or new Lean compilation is used to add comments.

Wait for all 125 batches to become terminal; the supervisor then runs `finalize_tiny.py --baseline RUN/corpus_training_v20/base/data/training.jsonl`. Inspect root `completion.json` and actual all-500 outcome table before claiming final counts. Raw kernel-pass counts are not final admission counts. Keep provider/budget/error holds visible and investigate a stalled or dead owner; do not silently raise caps.

No file in V18's frozen 800-row pool or V20's live training data is changed by V21.
