# Current corpus 1.7B continuation is training

**Doc link:** [protocol](PROTOCOL.md)

**Status:** RUNNING — production optimizer updates on skampere1 A100 GPU1.

**Last updated:** 10-19-2026 06:11 PDT.

| Phase | Status | Evidence |
|---|---|---|
| Prospective protocol | DONE | Frozen before optimizer updates; exact source hashes verified |
| Corpus admission and tokenization | DONE | 10,940 unique examples; 13,168,888 assistant loss tokens; 5,470 planned updates |
| Protected-reference screen | DONE | 764 references; zero exact or near hits |
| Duplicate and proof exclusions | DONE | 2,773 duplicate Workbook statements and 1,100 failing proof candidates excluded |
| Longest-sequence memory check | DONE | Actual 16,112-token example; finite loss/nonzero gradient; peak38.36GiB; disposable weights discarded |
| First production update | DONE | Loss1.170485; gradient norm14.0225; identical frozen starting weights reloaded |
| Full validation and CPU scoring | QUEUED | Automatic pipeline: all135 tasks × eight samples; GPU released before CPU scoring |
| Cleaned-data comparison | WAITING FOR CLEANUP | Remote watcher freezes accepted replacements and original fallbacks, then starts GPU2 |

## Frozen data and training

| Source | Unique rows |
|---|---:|
| Original Python-to-Lean | 2,585 |
| Annotated tiny Python-to-Lean | 500 |
| Verified Workbook | 7,794 |
| Explicit Workbook repairs | 61 |
| Total | 10,940 |

Training JSONL SHA-256: `6b0cce0608a11b2aa7d31e1343c6db0ba8ade08fdbd62ec68914884064a9df3e`. Starting checkpoint is completed V6 mixed1.7B, verified initial-manifest SHA-256 `0acf7b913175e58d9bc3ead57bd0c0eb0a71669f494918cef404dec77dc9ee7b`. Each row appears once; no sequence truncation. Exact [admission receipt](results/current_prepare_receipt.json), [per-candidate accounting](results/current_row_results.csv), [first update](results/current_first_update.json), [memory control](results/current_smoke_result.json), and [source identity](results/source_lock_verified.json) retain the evidence.

Initial estimate2–4hours training from the prior1.7B throughput; shorter-proof step overhead and shared-node load may change this. Validation generation and Lean scoring follow separately. Loss or compilation of training targets is not evidence that validation success improved. No new validation result is available yet.

**TLDR-end:** [rl-4-code-verification: 1.7B warm start] The10,940-example first continuation is actually training; its full validation/scoring and the subsequent cleaned comparison have remote ordinary-code owners.
