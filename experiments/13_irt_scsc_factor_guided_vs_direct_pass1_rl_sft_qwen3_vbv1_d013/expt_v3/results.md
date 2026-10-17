# Experiment 13 v3: factored reward technical gate and paired learning pilot

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/results.md>

**TLDR:** The retained 256-rollout factored batch is verified and its one-step optimizer update is running. No learning or validation outcome is measured yet.

**Status:** TECHNICAL_GATES_RUNNING
**Last updated:** 10-16-2026 19:15 PDT

The exact retained 256-rollout train cohort has been assembled in v3. Its 255 measured scores reproduce 21 positive factored rewards, 14/31 active complete groups and 112/248 nonzero-advantage slots. The incomplete eight-response group remains masked. These are fixed-cohort diagnostics, not evidence of learning or held-out performance (p-val=n/a).

| Stage | Status | Evidence |
|---|---|---|
| Retained cohort | DONE | [Every group and original generation hash](results/retained_cohort.json) |
| T2: one update and eight-response refit | IN PROGRESS | Strict baseline: gradient norm 0; 0/399 changed tensors. Actual NeMo batch confirms 112 nonzero-advantage slots; optimizer/refit unmeasured. |
| T3: saved-batch replay | PENDING | Requires T2 PASS; maximum loss difference ≤0.001. |
| T4: eight-cell train evaluation cost | PENDING | Requires T3 PASS. |
| T5 and paired B/A/P pilot | PENDING | Seeds 1301 and 1302; continuous B reward gate. |
| Validation pass@1 and SCSC | PENDING | No new held-out outputs or scores. |

All execution is local and offline; API spend is $0. The v2 directory is read-only input. New artifacts live under `/lfs/skampere1/0/brando9/rl4cv_e13v3/`; no v2 receipt is rewritten. The owned repository is its `rl-4-code-verification/` subdirectory, initial revision `de73908cffa501a46f5e628a0701d34dbfd0ac20`.

The implementation reuses the original NeMo distributed-tensor worker, native checkpoint save/restore, float16 precision, loss, sampler and probability comparison as read-only modules. A v3 resource guard replaces only the v2 resource-owner check. Legacy primitive receipts retain their internal `v2-S2` serialization label; v3 provenance and gate receipts identify the new condition. The update restores the original saved pre-update state, including optimizer, scheduler and random state. It changes only rewards on the retained generation cohort.

GPU plan: device 0 for sequential technical stages, roughly 30–65 GiB video memory depending on stage, an estimated 1–2 hours for update/refit, with uncertain duration; devices 5 and 7 are eligible for later matched trajectories after fresh idle checks. Devices 1, 2, 3, 4 and 6 are excluded. Every stage rechecks physical device identity and foreign occupancy. The initial T2 controller has a ten-hour allocation expiration; its subprocesses are bounded to four hours. The follow-through permits at most four hours for replay and one hour for the evaluation generation lease. No provider calls are implemented.

VeriBench SCSC is the smooth conjunctive score, `(IC_tests × IC_proofs × FSC)^(1/3)`, where the three factors measure test correctness, proof correctness and formal-specification coverage. The locally computed guarded `factored_reward` is a training proxy, not an interchangeable official SCSC measurement. Local validation will retain the exact mechanical factors from the frozen strict scorer. Known compilation failures have zero composite score under the inherited compile-gated coverage rule; a known zero mechanical factor also determines a zero product. Other missing coverage stays unknown, with full-denominator composite bounds. No local training proxy is substituted for official SCSC.

For the paired pilot, both seeds 1301 and 1302 receive the declared arm comparisons. T5 retains the inherited executable A6 gating seed, B/1301; B/1302 is a separately reported replication, never used to rescue a failing feasibility result. This interpretation is recorded before any pilot response. Continuous-reward missingness bounds and the one permitted 60-update extension are implemented and tested.

Validation: 42 new deterministic tests pass. The first full suite had 1,381 passes and one missing-path failure in an existing experiment-08 test; a temporary `ultimate-utils` test-environment alias fixed the path. The full rerun passes **1,382 tests, 3 skipped, 6 subtests**, exit 0 in 557.05 seconds ([receipt](results/publication_tests.json)); all 42 new tests pass again. Required Lean integration remains enabled. The technical controller runs in `codex-rl4cv-e13v3-technical`, with launch/config/ownership receipts under the v3 work root.


The [strict-input identity certificate](results/strict_input_identity.json) verifies every v3 slot against the actual prior strict optimizer input, not only the task list. The initial controller has a reporting-only single-rank gradient-list mismatch; its exact launch source is retained, and the corrected follow-through requires successful update/export/refit receipts before completing the result. No expensive stage is repeated for that correction.

[Actual tensor-batch comparison](results/actual_batch_identity.json): input IDs, lengths, assistant masks, sample masks, behavior probabilities, recomputed trainer probabilities and reference probabilities are all bitwise identical to the strict-run batch. Only advantages differ: 0 versus 112 nonzero slots. Maximum absolute recomputed log-probability difference is exactly 0.

[Pre-update state identity](results/pre_update_state_identity.json): parameter and optimizer digests match exactly, as do Python, NumPy and CUDA random states. Torch CPU random state advances during the additional probability-recomputation pass. This is disclosed rather than claiming identical random state across reward conditions; every saved loss-input tensor except advantages remains bitwise identical. T3 uses v3’s own exact saved state.

The paired runner and validation adapter are implemented and pass 72 focused tests. The full repository suite passes again: 1,382 tests, 3 skips and 6 subtests in 488.23 seconds ([receipt](results/pilot_publication_tests.json)). They have not performed any pilot update or held-out generation. All 1,080 validation prompt records prepared successfully without a model call. The inherited full main-study allocation is outside this pilot dispatch; the prospective local pilot cost plan is documented in [PILOT_EXECUTION.md](PILOT_EXECUTION.md).

[Google findings companion](https://docs.google.com/document/d/1xkEn8vW800jBucuJANuXD8ph-sMQMofwNZw_nJzjJls/edit?tab=t.sglsb683kh5u): the dated 19:14 PDT evidence update was read back exactly, with previous notes and existing permissions preserved. [Verified background controllers](results/background_controllers.json) record the queued pilot, progress writer and terminal publication watcher; the dispatcher is waiting on the live technical follow-through and has not admitted pilot generation. Source implementation is pushed at `b2ac757`.

<!-- LIVE START -->
Live receipt status (10-16-2026 19:03 PDT): **TECHNICAL_GATES_RUNNING**. API spend: **$0**.

| Arm / seed | Completed updates | Latest observed train reward | Active / usable groups | Gradient norm |
|---|---:|---:|---:|---:|
| B / 1301 | 0 | unmeasured | unmeasured | unmeasured |
| A / 1301 | 0 | unmeasured | unmeasured | unmeasured |
| P / 1301 | 0 | unmeasured | unmeasured | unmeasured |
| B / 1302 | 0 | unmeasured | unmeasured | unmeasured |
| A / 1302 | 0 | unmeasured | unmeasured | unmeasured |
| P / 1302 | 0 | unmeasured | unmeasured | unmeasured |

[Every completed training step](results/pilot_trajectory.csv); [machine-readable gate and validation results](results/live_progress.json).
Training rows are fixed-run diagnostics (p-val=n/a), not an efficacy claim. Official SCSC remains unmeasured without validated coverage.
<!-- LIVE END -->

**TLDR-end:** [rl-4-code-verification: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3] The exact retained cohort is verified and the factored update is running; optimizer and downstream gates are not yet measured.
