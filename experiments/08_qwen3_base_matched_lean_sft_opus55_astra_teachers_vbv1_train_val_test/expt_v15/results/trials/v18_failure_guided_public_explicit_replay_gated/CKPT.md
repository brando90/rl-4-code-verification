# V18 Checkpoint

Created: 2026-10-19 PDT
Last updated: 2026-10-19 PDT

## State

- V12-current completed with 120/1,080 successes (11.11%); its dominant residual is extracted Lean that does not compile, not absent file markers.
- V14 admission is complete: 678 public explicit-proof rows, protected exact/near screens zero, current kernel/formal receipts and comment-only byte roundtrips passed.
- V17 used this curriculum but terminated from a foreign GPU-1 allocation race after optimizer updates; no V17 checkpoint or validation result is adopted.
- V18 uses the exact copied, checked input files and begins freshly from V12-current with a fresh optimizer. The copied training, token, and schedule SHA256 values are recorded in `input_manifest.json`.
- Named tmux launcher: `rl4cv-v18-public-explicit-gated`; it is waiting without a CUDA context for an empty GPU 0, 3, 4, 5, or 7. GPU1 is explicitly excluded for V12-cleaned; GPU2 and GPU6 are excluded for protected foreign/4B work.
- The brief first waiting launcher was stopped before GPU admission solely to exclude GPU1. Its `KeyboardInterrupt` receipt is preserved as `terminal_prelaunch_candidate_correction.json`; canonical `terminal.json` remains absent until V18 completes or truly fails.

## Next Measurement

After double-observed allocator admission, record smoke and full training receipts, then exactly 1,080 frozen validation cells. The next decision quantity is `analysis/v18_adapt_summary.json`: declared/scored cells, binary successes/rate, compilation/cap counts, and raw/scored-cell paths from `manifest.json`.
