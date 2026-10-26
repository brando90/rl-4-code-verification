# V16: Independent ordinary-code receipt recovery for V12 current

**Status:** Prospective CPU-only recovery phase, frozen before execution on October 19, 2026.

## Hypothesis

The V12-current result is a complete 1080-cell measurement, but its required independent ordinary-code receipt was absent solely because the V15 supervisor invoked the frozen V6 analysis without `TINY_RUN_ROOT`. Re-running the identical frozen V6 `analyze.evaluate` path with that environment variable supplied should reproduce the recorded `declared_cells`, `scored_cells`, `successes`, and `success_rate` exactly. This phase does not train, generate, alter prompts, or inspect the test split.

## Frozen inputs

- Recorded V12 summary: `corpus_training_v12/analysis/v12_current_summary.json`.
- Raw cells: `corpus_training_v12/validation/v12_current/raw.jsonl`.
- Scored cells: `corpus_training_v12/validation/v12_current/scored.jsonl`.
- Validation IDs and evaluator source bytes are the frozen V6/V15 paths recorded in `sources/SHA256SUMS`; the local source copies are provenance snapshots only.
- The validation manifest remains the inherited 135 task IDs × 8 fixed samples (1080 declared cells). The 222-task test split is not opened.

## Method and selection criterion

`run_receipt.py` sets `TINY_RUN_ROOT` only for its own subprocess, imports the unchanged V6 evaluator from the frozen project path, and calls `analyze.evaluate("v12_current", raw, scored, ids)`. It writes an immutable input digest, complete returned per-cell vector, recomputed aggregate, and a separate terminal receipt.

The recovery passes only when the recomputed values exactly equal the V12 recorded values for `declared_cells`, `scored_cells`, `successes`, and `success_rate`; otherwise it is recorded as failed. No optimizer update, checkpoint selection, data admission, paid model call, or GPU allocation is permitted.

## Resources and ownership

The phase runs in `rl4cv-adaptive-v16-independent-v12` with `CUDA_VISIBLE_DEVICES` empty. It uses an isolated trial directory and does not modify V12, V13, V14, or V15 source/runtime artifacts. Its manifest is intentionally a receipt-phase manifest: `summary_path` is null because it is not a new model evaluation; `receipt.json` is the result artifact.
