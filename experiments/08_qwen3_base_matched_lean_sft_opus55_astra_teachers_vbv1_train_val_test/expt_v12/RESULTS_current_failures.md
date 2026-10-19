# V12: first-run validation failures and partial proof-cleanup comparison

**Doc link:** [live results](results.md)

**TLDR:** The first current-data run finished at 120/1,080 validation successes (11.11%); it did not reach 25%. Most failures are compiler failures, while missing extraction is almost entirely truncated files that began with the correct output envelope. A partial second dataset was frozen with818verified proof replacements and received zero optimizer updates. Its dispatcher is now fenced; the final second condition waits for version18cleanup under version19.

## Complete first-run cohort

| Outcome | Attempts |
|---|---:|
| Binary success / compiled | 120 / 1,080 |
| Extracted Lean, failed compilation | 851 / 1,080 |
| No extracted Lean | 109 / 1,080 |
| Generation hit the 12,288-token cap | 110 / 1,080 |

The 95% percentile bootstrap interval for binary success is **6.94–15.83%**, using 10,000 resamples of the 135 validation tasks while retaining all eight samples per task. The held-out test split was not evaluated. All 109 unextracted answers were capped; 108 began with a FILE marker and Lean opening fence. This generally reflects failure to finish the file, rather than failure to start the requested template. A conservative lexical repetition heuristic flags 32 of those 109 tails; this is a diagnostic, not a correctness judgement.

Core validation accounts for all 120 successes: **120/744 attempts across 93 tasks (16.13%; task-bootstrap 95% 10.35–22.31%)**. Industry validation has **0/336 attempts across 42 tasks**. Resampling an all-zero task vector produces a degenerate interval; it must not be presented as a meaningful upper confidence bound on future success.

## Tactics in the actual generated Lean

Comments and quoted strings were removed before lexical counting. These are overlapping file-presence counts among **971 extracted outputs**, not diagnoses of which tactic caused failure.

| Token | Outputs containing it | In failed outputs | In compiled outputs |
|---|---:|---:|---:|
| `exact?` | 0 | 0 | 0 |
| `apply?`, `simp?`, `simpa?` | 0 each | 0 each | 0 each |
| `simp` | 775 | 756 | 19 |
| `omega` | 359 | 359 | 0 |
| `simpa` | 140 | 140 | 0 |
| `simp_all` | 28 | 28 | 0 |
| `norm_num` | 55 | 55 | 0 |
| `native_decide` | 971 | 851 | 120 |

`native_decide` is also used by the required anonymous concrete tests, including successful files. An error saying it evaluated a proposition as false can indicate an incorrect implementation, test or theorem; its presence alone is not a problem. The observed failures are not random `exact?` calls.

## Descriptive comparison with completed V6 runs

| Previous run | Previous successes | Current minus previous | Paired task-bootstrap 95% interval |
|---|---:|---:|---:|
| 1.7B control | 99 / 1,080 | +1.944 percentage points | −0.093 to +4.167 points |
| 1.7B mixed | 74 / 1,080 | +4.259 percentage points | +2.127 to +6.667 points |

These comparisons use the same 135 validation tasks and all eight attempts; seed 0, 10,000 task resamples, p-value not computed. Additional data, training tokens and continuation differ, so the differences do not identify the causal effect of one dataset or tactic change.

## Historical partial second dataset

All **10,940 original row identities and their batch order** are retained. Exactly **818** Python-to-Lean answers have verified proof-only replacements; **1,767** retain their original answer, including 227 without targeted automation and 1,540 flagged fallbacks. Every replacement has a matching original response hash, immutable prompt, proof-only scope receipt, pinned-kernel check and format/token check. The whole pool passes the same 764-reference overlap screen.

The dataset SHA256 is `deefba0e3dc86c6910a1d5d3b3137cd18510efc1cb943395cff5f372b9356d6c`. It contains **13,420,616 supervised tokens**, compared with 13,168,888 in the first run, and uses the same initial checkpoint, seed, logical row order and 5,470 one-pass updates. This is not an equal-token comparison.

**Status on 10-19-2026:** Data preparation passed, but no production optimizer update occurred. All sufficiently large inspected SNAP GPUs became occupied by foreign jobs, so the partial dispatcher was fenced for migration. The user then required finishing the remaining cleanup. [Version19](../expt_v19/PROTOCOL.md) uses this partial dataset only for a discarded hardware control and trains the final version18cohort, with exclusions and changed row/token counts disclosed. The final second run is not yet measured.

## Diagnostic evidence

The frozen scorer did not retain compiler diagnostics for failed source files. A separate CPU-only pass checked **all 851** original failed extracted files with the same pinned wrapper, 16 parallel processes and a 20-second diagnostic timeout. It did not alter original scores, caches or sources. The following categories use the **first reported error**, are mutually exclusive and sum to 851:

| First reported diagnostic | Failed outputs |
|---|---:|
| `native_decide` evaluated a false proposition | 195 |
| Type mismatch | 151 |
| Unsolved goals | 122 |
| Syntax / invalid notation | 103 |
| Other first diagnostic | 76 |
| Other tactic failure | 72 |
| Instance / type inference | 67 |
| Unknown name or tactic | 46 |
| Diagnostic timeout without an earlier formatted error | 16 |
| Other failure without a formatted error | 3 |

The first diagnostic is a local symptom, not a proven causal root cause. In particular, a false computed proposition may originate in an incorrect implementation, concrete test or theorem; this analysis does not decide which. Across whole logs, overlapping symptoms include type mismatches in 587 outputs, unsolved goals in 577, unknown identifiers/constants in 311 and syntax errors in 254. Thirty-six diagnostic checks reached their 20-second bound; 20 had already emitted a first error. These bounds apply to this analysis pass, not the original evaluation.

[All 1,080 cells](results/current_failure_cells.csv), [first-error categories for 851 outputs](results/current_first_error_cells.csv), [full diagnostic summary](results/current_failure_summary.json) and [first-error summary](results/current_first_error_summary.json) are available locally. Raw source-dependent compiler messages and representative log paths remain in the protected remote analysis directory. Validation source, compiler logs and task-specific repairs are not supplied to teacher workers.
