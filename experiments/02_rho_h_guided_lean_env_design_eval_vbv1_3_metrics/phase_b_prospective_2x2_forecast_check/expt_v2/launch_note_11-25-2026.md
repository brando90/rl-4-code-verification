# 11-25-2026 — Experiment 02B GPU launch readiness

**Date:** 11-25-2026.
**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/launch_note_11-25-2026.md>

**TLDR:** Not launched: H200 capacity is available on skampere2, but the locked external-only experiment still lacks a verified executable training configuration, accepted-reference admission, measured pre-training probes and a frozen forecast. Brando's GPU approval is already given. The dated launcher exits with a specific blocker; it cannot substitute an unrelated trainer or make a scientific forecast up.

Harness: Codex CLI, GPT-6 Astra ultra (Vals account). This is a code/artifact and host-status check, no new model generation or RL result. No DT. The engineering adapter support result is reported separately in phase A; support for a reference's syntax does not establish that its proof is accepted or non-vacuous.

The coordination claim was pushed to `agent-sync` main before any possible launch: [eeed3cd](https://github.com/brando90/agent-sync/commit/eeed3cd). It records AT-3598 as owner and NOT LAUNCHED. No job from this task has a GPU job ID.

## Placement and compute estimate

The repository launch rule is B200 (`skampere3`) before H200 (`skampere2`) before A100-80GB (`skampere1`), among eligible idle devices. It excludes any device occupied by another user or above 10% utilization. The 19:46 PST [live inventory](../../../../docs/qa_11-25-2026/snap_inventory_at3598_11-25-2026.json) found all eight local A100s occupied by another user's processes, 35–99% utilization and 9,767–48,837 MiB free. Free memory alone does not admit a GPU. The inherited `CUDA_VISIBLE_DEVICES=2` is an old pin, not a placement decision. No device was selected, no GPU waiter was started, and no process was stopped.

Remote access was attempted through a workspace-local copy of the `agent-sync` SNAP recipe, preserving host-key checks and backoff. The first attempt failed because its control-socket path exceeded the Unix path limit; the path was shortened inside this task's workspace while retaining the mandated backoff. The permitted retry succeeded; all four remote hosts were inventoried through the reused whale master. **Skampere2 H200 GPUs 4–7 are physically idle and compatible** (143,157 MiB free each). Their previous experiment 18c worker jobs all have exit 0 and `WORKER END` logs. Skampere3 B200s are occupied; mercury A4000s have only 16 GB and are excluded by this runbook for RL. Thus skampere2 is the preferred candidate host, but no GPU is allocated because the scientific gates remain incomplete. These results are recorded in the inventory receipt and [SNAP status note](../../../../docs/qa_11-25-2026/snap_status_at3598_11-25-2026.md). No existing SSH directory or configuration was modified.

The locked v2 design is four trajectories of 64 optimizer steps. Its runbook explicitly says that runtime and GPU-hours are unmeasured until Lean response lengths and scorer throughput are measured. **A defensible numeric GPU-hour or A100 wall-clock estimate is therefore unavailable.** Required estimate after the baseline: 256 measured optimizer-step durations, plus the declared probes and endpoint evaluation, with GPU-resident and CPU-only time separated. The parent's 500–700 B200 GPU-hour estimate refers to the distinct larger scale study; it is not an estimate for this four-trajectory pilot.

## Exact prepared invocation and remaining gates

From the repository root:

```bash
env -u BASH_ENV bash --noprofile --norc experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/launch_11-25-2026.sh
```

This executes the dated admission receipt and exits **2, NOT LAUNCHED**. It is a runnable admission/launch wrapper, **not an implemented Lean training configuration**. The receipt deliberately has `training_entrypoint: null`. A training command cannot be stated truthfully until the real Lean reward/scorer integration and configuration are implemented and verified; a generic math GRPO invocation would be the wrong experiment.

The wrapper's admitted path requires hash-pinned protocol, trainer, configuration, forecast, reference/screen/adapter/precision receipts and a published claim, an explicit GPU UUID from the admitted host inventory, included self-hosted computation, a fresh output log, and a bounded tmux command. It rechecks GPU ownership/memory immediately before dispatch and exits 75 if occupied; it never polls. The future dated admission must record its exact tmux session, log path and bounded runtime before dispatch, followed by first-real-rollout verification. It does not launch an agent loop or send email.

These scientific prerequisites remain separate from GPU availability:

- The two environments need accepted, screened Lean 4.22.0 references with allowed axioms and non-vacuity checks. Candidate counts and adapter-support counts are different from reference acceptance.
- A real external-only Lean rollout adapter and verified trainer/configuration must replace the math-specific placeholder recorded in the historical readiness manifest.
- The initial checkpoint needs a recorded immutable revision and an actual dtype/mismatch/throughput baseline. Experiment 08's VeriBench-trained SFT checkpoints violate this older experiment's all-VeriBench exclusion if silently reused.
- Measured pre-RL probes and a prospective numeric forecast must exist before training. **Correction beside the historical manifest:** `src/rl4cv/utility_model.py` now contains the equation and numeric `paper_frozen_14b_model()` coefficients; their presence does not supply missing Lean measurements, standardizers or the frozen forecast. The historical `NOT_FROZEN` artifact stays unchanged.

No `PROTOCOL.md`, frozen forecast, scored table or CSV was edited. No paid API was used. Tests and final issue status are recorded in the experiments-level AT-3598 report.

## Verification on 11-25-2026

`bash -n launch_11-25-2026.sh`: exit 0. Actual wrapper invocation: exit 2 (expected NOT LAUNCHED). `python3 -m pytest -q` on this version folder: **3 passed, exit 0**. These are admission-safety tests, not GPU-training or adapter-support measurements.
