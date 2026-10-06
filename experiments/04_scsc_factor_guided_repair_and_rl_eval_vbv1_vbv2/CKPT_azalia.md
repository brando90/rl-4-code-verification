# Resume the diagnostic intervention study

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/CKPT_azalia.md>

**TLDR:** Published engineering evidence includes all 24 authored controls and the failed 0/24 external-adapter applicability result. No repair or training is admitted. The version-4 generic-adapter proposal is a draft with zero new model-call budget.

Created: 10-05-2026 11:09 PDT
Last updated: 10-06-2026

## Current continuation state

- The [full reconciliation](expt_v2/endpoint_validation/results_2026-10-06T0734Z_reconciliation.json), SHA-256 `0c420a1e5f6c51e5c350a3fed3d17cad0d3feb104a905a299cf2d9804ca7090d`, has 24/24 measured controls, all matching. It references the original 20 immutable rows and four newly measured missing rows. The failed first resume preflight remains separate and measured no cell.
- [External applicability](expt_v3/results/verina_external24_applicability_2026-10-06T0610Z/results.json), SHA-256 `2bff38d953ccf2b369653ec0dbeb28c01f5e5286c17bcfdaaa46ad8f0a237a63`, is 0/24 against the unchanged 20/24 engineering gate. Every row is `unsupported_adapter`; this does not establish task unsolvability. See [the full findings](expt_v3/results.md) for source compilation and proof-trust limits.
- The external candidate allocation is 141 train / 24 validation / 24 test, not training admission. [Experiment02 readiness](../02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/results/training_readiness_manifest_2026-10-06.json) is `NOT_ADMITTED`, forecast `NOT_FROZEN`, with 0/4 trajectories launched.
- These receipts were published in `b384e06`. The transferred execution root is `/lfs/skampere1/0/brando9/rl4cv_azalia_execute/rl-4-code-verification`; latest remote supervision and completion belong to the [master checkpoint](../CKPT_MASTER_tmuxnone_cxd_01a10d32.md). Do not infer a live job from the historical session below.
- Next proposal: [version-4 generic endpoint adapter](expt_v4/README.md), DRAFT/NOT_ADMITTED, zero new author, solver, judge, reference-generation or training calls. Existing references remain immutable. Verify reference lineage, accepted proof trust, adapter behavior and a separately frozen execution budget before any new external measurement.

## Historical first-audit receipt

The following records the completed 10-05-2026 version-1 audit; its owner, session and next-step wording describe that historical observation, not current execution.

- Canonical experiment: `04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2`.
- Owner: current Codex chat; short lookup agents have finished, no model workers running for this experiment.
- Inputs: four frozen score/manifest/replay files, 6,556,256 bytes; hashes in expt_v1/input_manifest.json. Earlier reports were already read, so retrospective only.
- Runtime: Python standard library on skampere1; no scientific model or reasoning effort applies to deterministic execution. In-process lookup settings were inherited from this chat, not independently verified experimental model settings.
- Permissions: current desktop danger-full-access and approval never; remote ordinary shell worker has no agent sandbox or approval menu.
- Budget: one processor, 300 seconds, no model calls/charges/graphics processors; no scientific retries. Finishing reserve is local verification/publication only.
- Remote directory: `/lfs/skampere1/0/brando9/rl4cv_azalia_audit/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2`.
- Session: `rl4cv-azalia-artifact-audit`; wrapper writes exit code and hashes, survives coordinator disconnect within its bounded command.
- Health: Python and local disk pass; shared DFS free-percent gate fails, irrelevant to this local-scratch-only command; no shared-disk mutation or agent launch.
- Current step: audit executed and hashes verified; 34 repository tests and 5 targeted tests passed. Next scientific work is endpoint validation, not rerunning this completed audit. Publication identity is the Git commit containing this checkpoint; verify origin/main before resuming.
- Exact resume observation: `ssh skampere1 'cat /lfs/skampere1/0/brando9/rl4cv_azalia_audit/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v1/results/execution_receipt.json'`.
- Do not regenerate inputs, relabel historical proof trust, overwrite old outcomes, launch paid calls or tune against VeriBench.
- Later dependency: implement and validate fixed-reference endpoint harness on external tasks; resolve aggregation convention and pin next protocol before intervention measurement.

- Verified result: 5,420 saved rows; 4,444 complete factor rows; V1 saved 5,376/6,272. Independent reference endpoint unavailable; no causal outcome measured.
- Audit terminal receipt: exit 0; start/finish 10-05-2026 11:11 PDT. Existing receipt must not be overwritten. Remote job has completed, so no monitor or recovery process remains necessary.

**TLDR-end:** [rl-4-code-verification: 04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2] Factor-feedback controls and applicability findings are published; a generic adapter and accepted external references still block causal repair and training.
**Snapshot:**
```text
authored_controls=24/24 matching
external_endpoint_applicable=0/24; gate=20/24
candidate_partitions=141/24/24; admission=candidate_only
repair_cells=0/192; judge_member_calls=0/1296
training=NOT_ADMITTED; forecast=NOT_FROZEN
next_version=DRAFT; new_model_calls=0
```
