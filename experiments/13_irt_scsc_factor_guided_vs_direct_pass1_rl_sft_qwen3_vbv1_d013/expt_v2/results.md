# Experiment 13 version 2 results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/results.md>

**TLDR:** `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` version 2 passed R0 attempt 2 under Amendment A1: 30/30 fixtures matched, with complete components and historical oracle value/status. R1 attempt 1 also passed 400/400 train cells with matching historical oracle values and statuses.

Last updated: 10-13-2026 16:28 PDT
Status: **RUNNING UNDER A2 — original ordinary cohort continues; amended reconciliation and admission pending.**

| Stage | Status | Measured / declared |
|---|---|---|
| R0 attempt 1 | FAIL, retained | 26/29 matches; 28/29 complete components |
| R0 attempt 2 | PASS | 30/30 matches, oracle values/statuses, and complete components |
| Required suite for attempt 2 | PASS | 283 passed, 23 skipped; all seven required Lean cases ran |
| R1 attempt 1 | PASS | 400/400 measured and oracle-equal; zero untyped inconsistencies |
| L1v2 | FROZEN | 51 verified bindings; F0v2 0.50, F1v2 0.85; zero validation/test factors at freeze |
| R2 | Original opaque INCOMPLETE; A2 reconciliation pending | 23,351/38,784 receipts; ordinary 18,023/33,456 at 10-13-2026 16:27 PDT; opaque 5,319 measured + 7 typed limits + 2 untyped / 5,328 |
| G0 | NOT ADMITTED | 0/135 validation tasks |
| Phases 1 and 2 | NOT ADMITTED | No fitting or reinforcement learning |

[L1v2 lock report](RESULTS_L1v2.md) · [R1 report](RESULTS_R1_attempt_1.md) · [Attempt-2 report](RESULTS_R0_attempt_2.md) · [Unchanged attempt-1 report](RESULTS_R0_terminal.md) · [Owner checkpoint](CKPT_e13_v2_owner.md). The full historical denominator stays 38,784 = 21,504 base + 20,520 ladder − 3,240 overlap. The 5,400 unavailable ladder cells remain separately declared. Splits: train 539, validation 135, test 222.

Attempt 2 retained two 5,001-character messages and their intervening theorem error, checked information-message and raw-stream channels separately, and measured the unresolved theorem as 0/1 proved. All 42 original version-1 files and 47 preserved attempt-1 evidence/configuration files remain byte-identical. The 50-file snapshot also includes PLAN and the runbook, explicitly superseded by master Amendment A2, and the separately owned live master checkpoint. Frozen fixture measurements and measurement code remain unchanged. These are deterministic counts; intervals and p-values are not applicable (p-val=n/a).

The [opaque public receipt](R2/opaque_public_receipt.json) exposes completeness and hashes only. No test discrepancy, factor, label or source has been inspected. [Amendment A2](AMENDMENT_A2_R2_untyped_cells_and_admission_10-13-2026.md), written after that public observation, supersedes the original incomplete-stop rule. The original ordinary run finishes untouched; separate route processes then retry each untyped cell exactly once with unchanged measurement code, inputs and limits. Admission requires measured equality, no integrity defects and at most 5/5,328 unresolved opaque cells and 33/33,456 unresolved ordinary cells. [Reconciliation implementation](reproduction/README_A2.md) and [A2 lock](locks/A2_reconciliation.json) are prepared before retries; required suite: 313 passed, 23 unrelated skips. No A2 retry has run yet. This is technical measurement admission, not evidence against the reward hypothesis.

A1 permits at most five attempts each for R0 and R1; every attempt remains recorded. Later gates retain the no-retry rule; A2 authorizes only the specified untyped-cell retries in R2.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2's fixture acceptance passed 30/30 on attempt 2; the train-only diagnostic passed 400/400; L1v2 is published and full reproduction continues under A2, with amended reconciliation and admission pending.
**Snapshot:** R0_attempt_2 PASS; 30/30 fixtures; 283 tests passed; R1 400/400 PASS; R2 opaque INCOMPLETE: 5,319 measured, 7 typed limits, 2 unresolved / 5,328; ordinary cohort running.
