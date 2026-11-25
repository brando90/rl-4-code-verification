# V21 tiny proof repair results

**Doc link:** [Protocol](PROTOCOL.md)

**Status (QA 11-25-2026): DONE_WITH_EXCLUSIONS, 470 accepted, 30 excluded, 125/125 batches.** **TLDR (earlier):** Twenty-five Terra/high worker sessions are repairing the 500 original tiny training examples. Each lane owns 20 cases. Existing V18 and V20 data remain unchanged. Live kernel-pass counts precede final format, commentary, protected-reference and duplicate admission.

## Execution evidence

- All 500 original files parsed successfully with the frozen Lean proof-range parser. Prior V9 inventory found no complete file meeting the strict tactic policy, so no already accepted strict proof was regenerated.
- Twenty-five tmux workers launched at Unix time `1792436969`; actual CLI turn records confirm `gpt-5.6-terra`, high reasoning. Each lane processes five four-case batches, with at most two CLI turns per batch and four distinct checked source hashes per case.
- The 16 shared compiler slots check exact reconstructed source. Implementations, statements, APIs and tests remain fixed; only original proof terms change. Named numeric-test proofs remain required. The existing anonymous concrete `native_decide` exception is preserved.
- Snapshot `1792437318`: 303 kernel-passing sources, 75/125 batches finished, and 7 bounded repair exclusions. V21 configured estimates were $17.358837 conservative and $8.759061 ordinary rate; these are not invoices. No provider or budget hold was present.

## Commentary admission

Kernel success alone does not establish final admission. A source audit of 226 kernel-passing files found all 226 sketch headers, with 207 also containing meaningful English inline proof comments; 19 lacked inline comments. The user authorized deterministic comment-only repairs without extra model calls or redundant compilation.

The final admission adapter preserves the exact raw checked source and receipt, adds truthful descriptions of actual proof steps, and records exact insertion replay, balanced lexical contexts and identical non-comment Lean tokens. An actual preflight passed all 305 then-available checked files; 35 received these comments, with no model or compiler calls and a maximum 447 assistant tokens. Final outputs still require the strict scope, sketch, inline-comment, FILE/Qwen, under-1,000 assistant token, 16,384 conversation token, protected-reference and duplicate checks.

## Canonical artifacts

Remote root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v21`.

- Live state: `progress.json`, `row_progress.csv`, `watch_heartbeat.json`, and `watch.log`.
- Limits/errors: `provider_hold.json`, `budget_hold.json`, and `coordinator_attention.json` when applicable.
- Reproducibility: `dispatch.json`, `launch_source_manifest.json`, `runtime_manifest.json`, and preserved source amendments.
- Final publication after all 125 batches finish: `completion.json`, `final/tiny_training.jsonl`, all 500 outcomes, protected screen, and complete portable proof receipts.

The ordinary supervisor polls every 15 seconds and performs final admission automatically. The shared campaign ceiling remains $900, including earlier charges, with cleanup limited to $780. No automatic spending-limit increase or model fallback is used.
