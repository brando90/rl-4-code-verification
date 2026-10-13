# Experiment 13 v2 owner runbook (SNAP, skampere1)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/cc.md>

**TLDR:** You are the single writer for experiment 13 version 2 on skampere1. Your job, in order:

1. Build a declaration scorer that records an outcome for every output instead of rejecting malformed files, with full diagnostics.
2. Prove it on fixtures and a 400-cell diagnostic sample.
3. Reproduce the historical strict score on all 38,784 cells.
4. Run gate G0, then Phase 1's item response models and gate G1, then Phase 2's matched four-arm RL comparison, through test evaluation.

Success is a published report for each phase in `expt_v2/`, ending with Phase 2's test analysis, or an honest stop at the first failed gate with its evidence. Version 1's files and failed audit stay byte-identical; nothing is retried until it passes.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Start

1. Read `~/agents-config/INDEX_RULES.md`, this repository's `CLAUDE.md`, then:
   - `expt_v2/PLAN.md` (binding);
   - `../PROTOCOL.md`;
   - `../expt_v1/REVIEW.md`;
   - `../expt_v1/PHASE1_IRT_PLAN.md`;
   - `../expt_v1/PHASE2_MATCHED_RL_PLAN.md`;
   - `../expt_v1/RESULTS_opaque_audit_terminal.md`.
2. Set up a work root and source the environment:
   - `export WR=/lfs/skampere1/0/brando9/rl4cv_e13v2`, with your own clone of `main`.
   - Reuse experiment 08's pinned environment read-only: `/lfs/skampere1/0/brando9/rl4cv_e08/env_e08.sh`, the private Lean v4.22.0 plus Mathlib copy, and the frozen scorer from `external/deps.lock.json`.
   - Never write inside another experiment's work root.
3. Create `expt_v2/CKPT_e13_v2_owner.md` and `expt_v2/results.md` (header, status, declared denominators). Commit and push both before the first measurement.
4. Install `expt_v2/watchdog_e13v2.sh` (PLAN § 4) in your crontab every 15 minutes plus `@reboot`. Run it once with a fake mailer to show it detects a dead pane. Record the cron line and the test in the checkpoint.

## 1. Phase 0v2: scorer, fixtures, diagnostic sample, reproduction, G0

Follow PLAN § 3 exactly; R0 → R1 → R2 → G0, each published before the next.

- **Scorer contract.** Implement PLAN § 2's contract in `expt_v2/declaration_adapter_v2.py`, using a new probe file if needed.
  - Parse errors, truncation, non-compilation, unparseable theorem statements and missing theorems are measured failures.
  - Only infrastructure faults are unmeasured; each gets one identical retry and typed receipts.
- **Diagnostic sample.** Read only cell identities and status classes from version 1's private ledger; never stored strict or factor values. Run the version 1 adapter in a diagnostics wrapper and the version 2 adapter on the same seeded 400 cells.
- **Forecast.** Append F0v2 to `../expt_v1/locks/forecast_ledger.jsonl`'s successor in `expt_v2/locks/` before measuring G0.
- **Throughput.** Run 48 processes, but first check `uptime`, `free -g` and other users' processes. Lower the count if the node is busy. Record the actual rate after 500 cells.

## 2. Phase 1: models and G1

Follow `../expt_v1/PHASE1_IRT_PLAN.md` and `../PROTOCOL.md` § 4.

- **Rollout batches.** Generate the two train-split batches (539 × 8 each) from experiment 08's `sft_4B_f1p0` export with self-hosted vLLM on **one** idle device.
  - Before launching, check `nvidia-smi` and pick a device with no other user's process and under 10% utilization.
  - Export `CUDA_VISIBLE_DEVICES`.
  - Record the device plan in the checkpoint (Trigger Rule 9 pre-approval).
- **Fits and gate.** Fit, validate, publish G1, then H2.
- **Phase 1b.** Fit the conjunctive model to experiment 07's components and score the IRT promotion gate on experiment 10's pairs, as a secondary analysis that leaves experiment 10's locked protocol untouched.

## 3. Phase 2: matched RL and test evaluation

Follow `../expt_v1/PHASE2_MATCHED_RL_PLAN.md` and `../PROTOCOL.md` §§ 5–8.

- **Sequence:** LP → T1 → T2/T3 → T4 → T5 → L2, then main runs (4 arms × 3 paired seeds), validation selection and a single test evaluation.
- **Devices.** Use only idle devices that no other user holds, or devices granted through experiment 08's lease interface. Record each plan and the measured T4 cost in the checkpoint before L2.
- **FSC on test outputs.** Use the validated Valkyrie judge with route controls (D-102, D-108). Never call a provider API directly.

## 4. Throughout

- **Publishing.** Push each finished, test-passing step to `main` (`make test` first; stage explicit paths only). Update `results.md` and the checkpoint at every phase boundary and at least every 4 hours while running.
- **Failure.** A failed gate is a result: publish it with evidence and the README decision rule it triggers, then stop that branch.
- **Interruptions.** On account, context or turn exhaustion, write the checkpoint and continue through an eligible account under Rule 48. Keep one writer.
- **Notifications.** Email `brando.science@gmail.com` (no CC) only at completion or on an event that needs Brando, deduplicated, through the watchdog's mailer.
- **Master contact.** The master session checks in hourly. Answer its messages through the checkpoint and `results.md`.

**TL;DR:** fix the scorer to measure every output → fixtures and a 400-cell diagnostic sample → full 38,784-cell reproduction → G0 → IRT fits and G1 → four-arm matched RL through one test evaluation, publishing each phase and stopping honestly at any failed gate.
