# Version 3 factor-feedback validation: blocked before admission

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v3/results.md>

**TLDR:** The three-launch coordinator allowance is exhausted, with 0/16 official controls, 0/8 diagnostic-author calls and 0/56 solver cells completed. The five observed smoke executions were not admitted controls. This infrastructure blockage establishes no repair effect and no official validity-gate outcome.

Updated: 10-08-2026. Evidence verified through 20:05 PDT. **Status:** BLOCKED BEFORE ADMISSION.

## Verified outcome

The [blocked receipt](results/supervision_blocked_10-08-2026.json), published in commit `c53c0e2db8e587989d82b3520618e55ae0f9999f`, records all 16 official cells with null endpoints and `NOT_ADMITTED` status. The `skampere2` coordinator exited at 19:34 PDT with `error_max_turns`: the command-line interface reported 91 turns against a configured maximum of 90. This was not an authentication or account-quota failure. No fourth coordinator was launched.

| Declared stage | Completed | Interpretation |
|---|---:|---|
| Official gold/empty controls | 0/16 | Not admitted; no valid-pair count measured against the at-least-6/8 gate |
| Conditional diagnostic-author calls | 0/8 | Not admitted; Vals-funded Valkyrie route unverified |
| Conditional solver cells | 0/56 | Not admitted; all remain unmeasured |

Four earlier smoke executions had observed Docker limits of zero for both processors and memory, with no ownership labels. A later `smoke3-empty` execution verified four processors, eight gibibytes and ownership labels; its test command ran for 5.383 seconds, but the storage observer failed because the Docker inspection method did not support `size=True`. No `smoke3-gold` result was observed. These five executions remain private infrastructure evidence and contribute no official endpoint.

## Checks and unresolved admission

Fresh deterministic verification of the preserved remote revision `572e28f` under Python 3.12 found **113 repository tests passed, 11 skipped**, and **146 version-3 tests passed, two failed**. The two failures concern rejection-reason classification for deeply nested structured data; they remain required-check failures. With `PYTHONPATH` unset, the backend cannot import `requests`, and its environment also lacks `pygments` for the test runner. The earlier [review](results/implementation_review.json) applies only to its recorded snapshot.

The pending backend contains changes for direct resource-limited container creation, actual limit inspection, Git tree identities, empty-patch handling and image/source provenance. Those unfinished files are preserved, not published as a validated implementation. Remaining prerequisites include a complete version-budget ledger, bounded daemon-side image pulls, complete owned-storage accounting, a self-contained environment with passing checks, verified immutable execution inputs and a fresh admitted manifest. The response route and subsequent scientific gates also remain unverified.

The original deadline is **10-09-2026 10:50 PDT**. The ceilings remain 160 processor-hours and 18 elapsed hours, two containers with four processors/eight gibibytes each, and 120 gibibytes each of owned Docker and scratch data. Total processor use and remaining allowance are unknown; no budget reset occurred.

## Preservation and cleanup

Twenty-three pending files were archived privately at `skampere2:/var/tmp/brando9-rl4cv-e06-v3/supervision/pending_owner_changes_10-08-2026.tar.gz`, with SHA-256 `cc6c35bb5cd888925d9813de56af9b529ca8525a2d4d711e43b91c0a2ac0d4d1`. The original dirty owner clone, smoke evidence, source hashes and correction mailbox remain intact; [the checkpoint](CKPT_e06_v3.md) identifies their paths.

The owner acknowledged the correction mailbox and adopted the independent observer. Its ten harmless tests passed. After publication and verification that no scientific process or owned container remained, only `watch-rl4cv-e06-v3` and its one tagged cron entry were removed at 20:05 PDT. The private `supervision/observer_cleanup_receipt.json` records that later cleanup; the published blocked receipt is the preceding 20:02 PDT snapshot. No other experiment's watcher was changed, and no email was sent.

Historical [version-2 control](../expt_v2/results/official_evaluator_controls.md) and [diagnostic](../expt_v2/results/diagnostic_rejection_audit.md) results are unchanged. Neither the incomplete implementation nor these smoke executions support a claim that factor feedback improves or harms repair.

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] Version 3 is blocked before official admission; source and evidence are preserved, all declared scientific outcomes remain unmeasured, and its observer has been cleaned up.
