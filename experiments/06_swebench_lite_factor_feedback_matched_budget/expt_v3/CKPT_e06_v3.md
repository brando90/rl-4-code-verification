# Version 3 factor-feedback validation checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/expt_v3/CKPT_e06_v3.md>

**TLDR:** Version 3 is blocked before admission after all three coordinator launches were spent. No scientific driver remains: 0/16 official controls, 0/8 diagnostic-author calls and 0/56 solver cells completed. Preserve the unfinished source and original limits; this checkpoint does not authorize a fourth coordinator or measured execution.

Updated: 10-08-2026. Last execution/cleanup verification: 20:05 PDT. **State:** BLOCKED BEFORE ADMISSION.

## Authoritative evidence and ownership

- Published state: [blocked receipt](results/supervision_blocked_10-08-2026.json), commit `c53c0e2db8e587989d82b3520618e55ae0f9999f`; [readable results](results.md).
- Host and runtime: `skampere2:/var/tmp/brando9-rl4cv-e06-v3`; canonical symlink `/lfs/skampere2/0/brando9/rl4cv_e06_v3` resolves there.
- Original owner clone: `<runtime>/rl-4-code-verification`, retained at `572e28fa173897877e76b4882c20eefd5d259118` with unfinished changes. Do not reset, clean or replace it.
- Last coordinator: native Claude session `ce1f226b-000e-4413-adc8-5030d07dfee6`, Sonnet 5/high, full permissions; process 2248799 exited at 19:34 PDT. The client recorded `error_max_turns`, 91 reported turns and a configured maximum of 90. No coordinator or scientific child survives.
- Allowance: initial failed Codex launch, first Claude launch and native Claude resume consume all three launches. No fourth launch, hidden retry or clock reset was made.

Earlier remote draft statements about successful smoke validation do not supersede the published blocked receipt. Its endpoints remain null, and the official at-least-6/8-pair gate was not measured.

## Preserved private material

All paths below are relative to the runtime unless stated otherwise.

| Artifact | Path |
|---|---|
| Unfinished source archive, 23 files | `supervision/pending_owner_changes_10-08-2026.tar.gz` |
| Per-file hashes and archive identity | `supervision/pending_owner_changes_manifest.json` |
| Verified test results | `supervision/deterministic_verification_receipt.json`, `repository_verified_tests.txt`, `v3_verified_tests.txt` in the same directory |
| Published-receipt mirror | `blocked_receipt.json` |
| Publication verification | `supervision/blocked_publication_receipt.json` |
| Original enforcement incident and later smoke evidence | `supervision_correction_receipt.json`, `supervision_additional_smoke_receipt.json`, preserved smoke archives under `supervision/` and original event logs |
| Correction and acknowledged mailbox | `supervision_correction_brief.md`, `supervisor_mailbox.md`, `supervisor_mailbox_ack.json` |
| Owner exit and process history | `claude_resume3_exit.json`, `claude_resume3_launch.json`, `owner_ack.json` |
| Observer cleanup | `supervision/observer_cleanup_receipt.json` |

Archive SHA-256: `cc6c35bb5cd888925d9813de56af9b529ca8525a2d4d711e43b91c0a2ac0d4d1`. Raw evaluator material and the incomplete backend remain private. Publication used a separate clone under `supervision/publication`; it did not alter the original owner's dirty checkout.

## Limits, blockers and continuation

The unchanged [protocol](PROTOCOL.md) and [runbook](cc.md) remain the scientific specification, not evidence that admission passed. The provisioned window began 10-08-2026 16:50 PDT and ends 10-09-2026 10:50 PDT. The original 160-processor-hour and storage/container ceilings remain fixed. Complete processor accounting is unknown, so no remaining allocation is asserted.

The preserved code requires deterministic repair and verification before any admission: complete cumulative accounting, bounded image pulls and storage, self-contained dependencies, two failing version-3 tests, fail-closed image identity checks and an executable freeze. The measured Vals-funded Valkyrie route is also unverified. Do not execute the old remote draft's proposed `--execute` continuation merely because a manifest file exists; it is a dry-run manifest with no admitted control state.

No continuation job or model call is scheduled for this version. Deterministic source inspection or repair must preserve these receipts and limits; any proposed new measured execution needs a prospective decision establishing its authorization and valid budget rather than treating this closeout as a fresh allowance.

The independent observer was read-only and never restarted models or enforced scientific budgets. At 20:05 PDT, after the blocked state was published and no scientific job remained, `watch-rl4cv-e06-v3` was stopped and only the cron line tagged `# rl4cv-e06-v3-observer` was removed. Other watchers and cron entries were preserved. Do not report this observer as currently running or claim tested reboot survival.

**TLDR-end:** [rl-4-code-verification: 06_swebench_lite_factor_feedback_matched_budget] Version 3 has a published blocked outcome, preserved unfinished work and no active job; its original limits and unmeasured scientific denominators remain binding.
