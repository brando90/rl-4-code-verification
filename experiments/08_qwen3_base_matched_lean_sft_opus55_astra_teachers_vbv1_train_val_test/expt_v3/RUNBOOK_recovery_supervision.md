# Persistent recovery for matched replay versus expansion

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/RUNBOOK_recovery_supervision.md>

**TLDR:** The five-minute host watch preserves healthy work, observes failures and can start a bounded authenticated replacement after the previous repository writer exits or explicitly releases ownership. Initial owner acknowledgement and the harmless failure test are verified; a fresh replacement remains unverified until its own receipt and useful action are checked.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

The original [continuation runbook](RUNBOOK_continuation_owner.md), [protocol](PROTOCOL.md), and scientific manifests remain binding. `results/continuation_dispatch_v3.json` records the initial immutable input hashes. Later recovery dispatches snapshot the current checkpoint hashes into the host's `sft_v3/recovery_dispatch.json`; compare against that packet for the new attempt rather than expecting the evolving checkpoint to retain its initial hash.

## Executable and state

Host runtime root: `/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3`. The installed cron entries run `/usr/bin/python3 <this experiment>/recovery_watch.py --root <runtime root>` every five minutes and at reboot. They are tagged `rl4cv-e08-v3-recovery`. Cron and its files survive owner exit; reboot recovery requires the host and mounted filesystems to return. The next periodic tick retries after an early boot mount failure.

`recovery_config.json` contains the exact fixed launch arrays and finite inventory; `recovery_state.json` is the observation and attempt record; `recovery_watch.log` is the cron log. The watch uses `recovery.lock` while checking and reserving a launch. `owner_ack.json` records the actual owner process (boot identifier, process start ticks and process identifier), model, effort, permissions, inputs and training evidence. A recovery process additionally writes `recovery_owner_process.json` before launching its command-line client, preventing a duplicate while a new acknowledgement is pending. Every native recovery output and exit code is retained by attempt.

The watch observes both phase schedulers, child liveness, scheduler heartbeat, work-log/output freshness, analysis errors, failures, free bytes and completion evidence. A stale live process is reported for investigation; it is not killed. Legacy Phase A jobs record only process identifiers, so the watch explicitly reports their weaker identity evidence and never silently restarts them. The replacement owner must reconcile identities and adopt healthy children before restarting any scheduler. Process identifier reuse and zombies are handled in owner fencing.

An owner may intentionally transfer its writer role by writing `owner_handoff.json` with its exact `owner` and `attempt` from the acknowledgement and `released: true`. It must stop repository/runtime mutations at that point. The old owner may then observe and verify the successor without becoming a second writer. No training child is terminated by this protocol.

## Budget and retry limits

Normal polls make zero model calls. At installation the personal Codex native metadata showed 94% of its weekly allowance used and no purchased credits. Preserve its remaining allowance for handoff and verification. The distinct Vals Codex account was signed in; its most recent native usage observation was 37% used at 10-15-2026 18:36 PDT. That older observation is not a current balance guarantee. Its recent runtime used the same Astra model with full access and no approvals; the continuation explicitly requests `ultra`, whose actual value must be checked in the new transcript.

The initial automatic route is Vals Codex, at most two owner invocations. The overall recovery configuration caps automatic invocations at six and gives an absolute 72-hour deadline established at installation. Those bounds do not reset on reboot. Further existing-account candidates are recorded with concrete unverified dependencies; an inventory of profiles is not a claim that each can run. Dedicated Vals and Stanford Claude wrappers report authenticated subscription grants, unlike the logged-out generic profile paths. Stanford Codex's earlier native session was restricted despite full-access defaults, so its effective policy needs a new check. See [the nonsecret inventory](results/recovery_supervision_v3.json).

At each meaningful phase boundary, inspect native usage metadata, preserve a finishing reserve and reconsider at 25% remaining; do not admit another expensive coordination unit below 10%. The local training, inference and Lean workloads consume zero hosted-model dollars. No account switch changes scientific models, data, scheduler steps, sampling, sealed split rules or retry bounds.

## Verification, completion and next work

[The failure-test receipt](results/recovery_selftest_v3.json) records a real disposable tmux replacement launch, useful output, preserved healthy child, no duplicate launch, retained exit code 7 and enforced retry cap. Five focused tests additionally cover a live-owner fence, live recovery-runner fence, dead child/analysis error, process identifier reuse and rejection of a false completion marker. Test jobs made no model calls and were removed after inspection.

The full work remains Phase A's eight validation rungs, Phase B implementation and execution at the frozen device counts, all 17,280 validation cells, namespace diagnostic, paired task bootstrap, forecast assessment and parent results publication. Shared remote staging is still copying the NeMo environment; do not execute it until transfer, relocation, imports, exact pin and model hashes are verified. On 10-15-2026 at 21:25 PDT, skampere2 had no free devices and skampere3 had four free, so neither admitted eight-device 14B training.

The watch accepts completion only when `completion_receipt.json` records `status: COMPLETE`, `published_commit`, `notification_sent`, `training_verified`, `namespace_complete` and `forecast_assessed`, and the validation summary has exactly 16 systems and 17,280 known/declared cells. The owner must substantiate those fields before writing them. On completion the watch becomes inert; remove its two tagged cron lines during owned cleanup. On a recovery deadline or route limit it records the exact boundary; retain the active checkout and useful children and notify the user of a real blocker rather than claiming success.

The START email already exists. Send the single DONE email through `notify_run.py` only with verified terminal status and the required four recipients. Preserve compact numeric tables in Git and bulky raw outputs/checkpoints on the host; publish every completed priority rung promptly.

**TLDR-end:** [rl4cv: matched replay versus expansion continuation] Persistent recovery is installed and harmless-failure tested for 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3; complete training, validation and publication remain the owner's objective.
