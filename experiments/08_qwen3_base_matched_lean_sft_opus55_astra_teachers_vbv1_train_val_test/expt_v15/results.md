# 1.7B campaign: current-data training running, Terra cleanup launched

**Doc link:** [experiment home](README.md)

**TLDR:** The first1.7B continuation is training on A100 GPU1 with10,940 unique examples. The first four Terra/high cleanup workers are executing. The second training run waits for verified replacements; a remote outcome-triggered coordinator is armed for later validation-driven improvements. Additional API budget is$300 initially, plus$300 if needed, maximum$600.

**Last updated:** 10-19-2026 06:11 PDT.

| Phase | State | Verified evidence |
|---|---|---|
| Current training dataset | DONE | 10,940 rows;13,168,888 assistant loss tokens; zero protected overlap hits |
| First1.7B continuation | RUNNING | Real production update passed on A100 GPU1; automatic full validation/scoring |
| Original2,585 proof cleanup | RUNNING | First four Terra/high CLI workers; all2,585 source files parsed into100,234 proof terms |
| Cleaned1.7B comparison | WAITING | Remote watcher will use verified replacements and flagged original fallbacks, then claim GPU2 |
| GX10 environment | PROVISIONED | Actual tensor and tiny Qwen3 backward/optimizer controls passed; dynamic dispatch remains Mac-dependent |
| Additional Mathlib/DeepSeek data | CANDIDATES ONLY | 217 Mathlib plus512 DeepSeek candidates; future training admission requires all gates |
| Validation-driven adaptation | ARMED | Remote ordinary-code heartbeat verified; no adaptive model call before a completed outcome or actual failed job |

The first cleanup batch calibrates quality, cost and throughput before broader concurrency. The shared ledger reserves worst in-flight exposure and records conservative token charges; the second authorized$300 tranche is activated only if needed. No other paid model substitution is authorized.

Each regime, source mix, failure and result will be versioned. Prior V6 matched continuation gave99/1080 successes for replay and74/1080 for the tiny-augmented run; this was a negative result, with details in [the source and failure analysis](../expt_v14/results.md). The new campaign has no validation result yet. Its25% target is adaptive validation binary success over a complete135-task/eight-sample manifest; the test split stays sealed.

[First training run](../expt_v12/results.md) · [Proof cleanup](../expt_v13/results.md) · [GX10 and source preparation](../expt_v14/results.md).

## Latest automatic snapshot

10-19-2026 08:22 PDT.

- Current training: 5,470/5,470 updates; 13,168,888 assistant loss tokens.
- Cleaned training: 0 updates; waits for verified cleanup when zero.
- Cleanup: {'PENDING': 1815, 'DONE': 504, 'UNCHANGED': 227, 'RUNNING': 24, 'FALLBACK': 15}; declared 2,585.
- Additional public sources: 729/729 checked; {'FORMAL_CHECK_FAILED': 1, 'FORMAL_PASS': 688, 'LIBRARY_IDENTIFIER': 1, 'SYNTAX_COMPATIBILITY': 39}.
- Paid work: $118.22 base-rate usage estimate; $234.99 conservatively charged; $240.00 reserved for in-flight work. Estimates are not invoices.
- Second authorized $300 tranche activated: True. Goal receipt: False.
