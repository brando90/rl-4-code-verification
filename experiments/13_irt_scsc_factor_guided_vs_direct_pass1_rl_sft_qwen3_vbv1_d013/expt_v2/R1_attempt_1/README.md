# R1 attempt 1: train-only diagnostic procedure

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/R1_attempt_1/README.md>

**TLDR:** After R0 attempt 2 passes and is published, freeze a seeded 300-rejected plus 100-measured train-cell sample, instrument the complete unchanged version 1 path, and measure the version 2 oracle and components on exactly those cells.

The selector runs separately over the sealed metadata, checks the pinned base-manifest and terminal-ledger hashes, filters by D-013 train identifiers before selecting or opening sources, and emits only the train allowlist/sample. Selection uses cell identifiers and recorded measured/rejected status, seed 1302001; no outcome enters selection. The 12,936 allowed cells are the 539 train tasks × three base policies × eight samples. No validation/test source is opened.

Version 1 is invoked through its original `opaque_base_audit.reproduce`, on a one-cell train manifest, without replacing any vacuity, adapter or PartialCredit behavior. A Python trace records exceptions and their phase; subprocess capture retains complete raw streams. Version 2 separately invokes the preserved historical oracle and accepted attempt-2 frontend. Source bytes are checked against their original hash.

The cause table denominator is exactly the selected rejected train cohort (target 300), with Wilson 95% intervals as required by PLAN §4. Those descriptive binomial intervals do not adjust within-task correlation. Branch-to-fixture mappings are written in `summarize_r1.py` before execution; a branch over 1% without coverage fails admission. No untyped inconsistency or unmeasured cell passes. Typed resource/infrastructure classes remain declared. Historical oracle equality requires both value and status.

Memory is sampled every 0.1 second over the worker and all descendants, with child maximum resident size retained. Run the first cell serially; use its measured peak to initialize PLAN §7 concurrency, then lower admission dynamically using observed 99th-percentile peaks and current headroom, capped at 48. Freeze a 64-GiB virtual-address limit per cell, an aggregate systemd scope at half of launch-time available memory, and a 25%-available admission floor. The scope was supported by the owned `e13v2-a1-memory-preflight` test. Each cell has an owned process group and persistent run/start/boot identity. Final reporting uses all complete-cell peaks and costs, including version 1's path.

This is development attempt 1 of at most five under A1. Each attempt has independent locks/results and retains failures. Acceptance permits freezing L1v2; the no-retry scientific gates thereafter are unchanged.
