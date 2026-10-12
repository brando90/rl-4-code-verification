# Opaque historical audit terminal reconciliation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/RESULTS_opaque_audit_terminal.md>

**TLDR:** All 21,504 declared cells have terminal records, but only 6,739 are measured. The audit exited blocked; fitting and training remain unadmitted.

Created: 10-11-2026 23:30:49 PDT
Last updated: 10-11-2026 23:30:49 PDT
Status: BLOCKED — complete accounting, incomplete measured coverage, failed scientific gate.

The existing audit for `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` terminated at 10-11-2026 23:15:32 PDT with exit 1. Its observer recorded the same blocked state five seconds later and stopped. Launcher, child and observer identities were independently confirmed absent. No measurement or retry was executed for this closeout. [Machine-readable operational receipt](results/opaque_audit_terminal_10-11-2026.json).

| Segment | Accounted | Measured | Unmeasured |
|---|---:|---:|---:|
| Preserved original prefix | 16,645 | 5,981 | 10,664 |
| Retained reboot interruption | 1 | 0 | 1 |
| Originally untouched suffix | 4,858 | 758 | 4,100 |
| Full declared set | 21,504 | 6,739 | 14,765 |

Every manifest identity occurs exactly once, in manifest order, in a newline-terminated ledger. The 16,645-row prefix is byte-identical to its pre-recovery copy. The interrupted record is unchanged and was not retried because its consumed phase budgets could not be recovered. Original parser/compile/kernel limits remain 900/600/900 seconds. These are exhaustive operational counts, not an efficacy estimate; p-val=n/a. All unmeasured cells remain in the denominator, never scored as zero.

Of the unmeasured records, 14,764 carry `source_or_pinned_probe_rejected`; one carries `node_reboot_interrupted_phase_budget_unverifiable`. The generic class already occurred in 10,664 preserved-prefix records, so it did not first appear during reboot recovery. Another 4,100 records in the untouched suffix received that class. The frozen source catches five exception types and discards the phase, exception message, parser output and full compiler/kernel receipts. The resumed child log is empty. Current checks find all 21,504 original sources readable, valid UTF-8 and hash-matched; these checks do not establish which historical exception occurred.

Specific rejection causes therefore remain unresolved. Source-defined branches include unparseable theorem types, source/hash/encoding errors, failed or malformed parser output, invalid or duplicate declaration identities, pinned-module errors and parser/kernel identity disagreement. Listing these branches is a provenance diagnosis, not a claim that any branch explains a particular cell. No Lean probe was rerun on the sealed study to manufacture missing evidence.

Complete accounting does not satisfy the equality gate: that gate requires every required cell to be measured and pass its private comparison. Missing measurements suffice to keep it closed. No per-cell or aggregate sealed score, factor, label, example or private equality comparison is disclosed. Item response theory fitting, factor measurement and reinforcement-learning training remain unadmitted. The append-only [metadata erratum](locks/L1_audit_v2_metadata_erratum.json), complete-diagnostics requirement and all previous failures remain intact.

The smallest next scientific action requires a separately authorized prospective diagnostic/recovery condition. Before another measured attempt, freeze its scope, admissible evidence, complete per-phase receipts, cumulative elapsed accounting and decision criteria; preserve this failed audit as a distinct historical condition. This closeout neither requests replenishment of consumed budgets nor admits a rerun. The experiment stays in its existing active home because this unresolved dependency still blocks the originally requested later phases.

Verification used existing artifacts only: denominator/unique/order/newline checks, prefix byte equality, exact interruption retention, status counts, all source hashes/encoding, source/lock/manifest bindings and process-bound terminal receipts. Scientific source revision remains `ba5b8566976fc2eb0ced2424472efb8d7a153be3`. Publication changes documentation and the sanitized operational receipt only.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] The historical audit has complete accounting but failed scientific acceptance; no fitting or training is admitted.
**Snapshot:** 21,504 accounted; 6,739 measured; 14,765 unmeasured; zero closeout retries.
