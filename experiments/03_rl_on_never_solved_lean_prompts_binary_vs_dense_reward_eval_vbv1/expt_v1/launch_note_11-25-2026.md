# 11-25-2026 — Experiment 03 GPU launch readiness

**Date:** 11-25-2026.
**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/03_rl_on_never_solved_lean_prompts_binary_vs_dense_reward_eval_vbv1/expt_v1/launch_note_11-25-2026.md>

**TLDR:** Not launched: this experiment has no `PROTOCOL.md`, no admitted zero-signal probes/forecast and no executable training configuration. Its `cc.md` explicitly requires stopping when the protocol is absent. All local A100s fail the idle-device rule, but skampere2 H200 GPUs 4–7 are physically idle and compatible. GPU approval is already granted; experiment-readiness is the remaining blocker.

Harness: Codex CLI, GPT-6 Astra ultra (Vals account). Artifact/host-status inspection only; no model generation or RL run, no DT. Claim: [agent-sync eeed3cd](https://github.com/brando90/agent-sync/commit/eeed3cd), AT-3598, NOT LAUNCHED. GPU job ID: none.

## Prepared command and evidence

From the repository root:

```bash
env -u BASH_ENV bash --noprofile --norc experiments/03_rl_on_never_solved_lean_prompts_binary_vs_dense_reward_eval_vbv1/expt_v1/launch_11-25-2026.sh
```

The exact wrapper returns **2, NOT LAUNCHED**, with every scientific blocker. It delegates to experiment 02B's bounded logged tmux launcher only after a complete hash-pinned admission receipt exists. `training_entrypoint` is deliberately null; no executable Lean configuration exists to substitute. No tmux GPU job or waiter was started.

The 19:46 PST [inventory](../../../docs/qa_11-25-2026/snap_inventory_at3598_11-25-2026.json) finds eight occupied A100-80GB GPUs, all above 10% utilization with another user's process. The rule prefers reachable idle B200, then H200, then A100-80GB devices. Remote access and the existing live jobs are described in the [SNAP status note](../../../docs/qa_11-25-2026/snap_status_at3598_11-25-2026.md); the recipe succeeded to all four remote hosts. Skampere2 GPUs 4–7 have 143,157 MiB free each, zero GPU processes and zero sampled utilization; the earlier experiment 18c workers each have exit 0. Skampere2 is the preferred candidate host, but scientific admission prevents allocation/launch.

The README's original **18 trajectories × approximately 5 hours = approximately 90 B200 GPU-hours** is a historical planning estimate, not a measured A100 estimate. With one trainer per host, the corresponding old serial wall-clock estimate is approximately 90 hours before any uncounted evaluation overhead. Actual A100/H200 runtime remains unmeasured until the exact checkpoint, dtype, rollout and Lean-scoring baseline exists. Any eventual tmux segment needs a finite limit and a new log path recorded in its admission receipt; the supplied wrapper allows at most 24 hours per segment and does not restart jobs automatically.

## Work still required

- A protocol must exist and be locked before training. This task created or edited no `PROTOCOL.md`, as instructed.
- Experiment 02A must supply the external-only warm starts, four G=8 probe records, source-screened zero-signal `Z` pool and frozen within-source panel. The separate experiment 02A v3 teacher/data job's DONE marker is not evidence of those prerequisites.
- Freeze the pre-RL per-reward measurements and outcome forecast before any trajectory starts.
- Implement and verify `proof_fraction_feedback1` and the trainer's one-feedback-turn behavior; inspection found no implementation in `src/rl4cv` or tests. The verifier must retain the allowed-axiom and non-vacuity checks.
- Supply experiment 02B's verified training configuration, precision/mismatch baseline and exact external-only model provenance. An experiment 08 checkpoint trained on VeriBench cannot silently replace it under the older all-VeriBench-held-out rule.

No scored table, CSV or historical receipt was changed. No paid API or new model call was used. Issue #3 must remain open because the requested 02B–02D/03 SNAP runs have not started.

## Verification on 11-25-2026

`bash -n launch_11-25-2026.sh`: exit 0. Actual wrapper invocation: exit 2 (expected NOT LAUNCHED). `python3 -m pytest -q` on this version folder: **no tests collected, exit 5**; this is not reported as a passing test suite. The shared launcher has three passing admission-safety tests in experiment 02B.
