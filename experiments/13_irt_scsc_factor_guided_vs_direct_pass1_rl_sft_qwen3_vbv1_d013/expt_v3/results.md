# Experiment 13 v3: factored reward technical gate and paired learning pilot

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/results.md>

**TLDR:** The paired pilot is resuming after the six trajectory processes exited on 10-18-2026. Finished generations are kept. Seed 1302 had no generations and starts update 1 again when a GPU is free. API spend remains $0. No held-out pass@1 result yet.

**Status:** PILOT_RUNNING
**Last updated:** 10-18-2026 19:26 PDT

The exact retained 256-rollout train cohort has been assembled in v3. Its 255 measured scores reproduce 21 positive factored rewards, 14/31 active complete groups and 112/248 nonzero-advantage slots. The incomplete eight-response group remains masked. These are fixed-cohort diagnostics, not evidence of learning or held-out performance (p-val=n/a).

| Stage | Status | Evidence |
|---|---|---|
| Retained cohort | DONE | [Every group and original generation hash](results/retained_cohort.json) |
| T2: one update and eight-response refit | PASS | [Measured result](RESULTS_T2_v3.md) |
| T3: saved-batch replay | PASS | [Receipt](results/live_progress.json) |
| T4: eight-cell train evaluation cost | PASS | [Receipt](results/live_progress.json) |
| T5 and paired B/A/P pilot | INCOMPLETE | See live table below. |
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

The paired runner and validation adapter are implemented and pass 75 focused tests ([publication isolation](results/publication_isolation_tests.json), [cost accounting](results/cost_probe_accounting_tests.json)). The full repository suite passes again: 1,382 tests, 3 skips and 6 subtests in 488.23 seconds ([receipt](results/pilot_publication_tests.json)). They have not performed any pilot update or held-out generation. All 1,080 validation prompt records prepared successfully without a model call. The inherited full main-study allocation is outside this pilot dispatch; the prospective local pilot cost plan is documented in [PILOT_EXECUTION.md](PILOT_EXECUTION.md).

[Google findings companion](https://docs.google.com/document/d/1xkEn8vW800jBucuJANuXD8ph-sMQMofwNZw_nJzjJls/edit?tab=t.sglsb683kh5u): the dated 19:14 PDT evidence update was read back exactly, with previous notes and existing permissions preserved. [Verified background controllers](results/background_controllers.json) record the queued pilot, progress writer and terminal publication watcher; the dispatcher is waiting on the live technical follow-through and has not admitted pilot generation. Source implementation is pushed at `9845810`; [the current publisher receipt](results/background_publisher_v2.json) supersedes the original publisher PID.

<!-- LIVE START -->
Live receipt status (10-18-2026 19:26 PDT): **PILOT_RUNNING**. Factored seed 1301 update 10 is accounted. Placebo seed 1301 update 9 is in its optimizer step. Strict seed 1301 update 11 is loading on GPU 5. Five empty permission-failed attempts were archived and those arms were restarted. API spend: **$0**.

| Arm / seed | Completed updates | Latest observed train reward | Active / usable groups | Gradient norm |
|---|---:|---:|---:|---:|
| B / 1301 | 9 | 0.008076 | 20/32 | 0.208121 |
| A / 1301 | 9 | 0.000000 | 0/32 | 0 |
| P / 1301 | 8 | 0.009904 | 17/32 | 0.256924 |
| B / 1302 | 0 | unmeasured | unmeasured | unmeasured |
| A / 1302 | 0 | unmeasured | unmeasured | unmeasured |
| P / 1302 | 0 | unmeasured | unmeasured | unmeasured |

[Every completed training step](results/pilot_trajectory.csv); [machine-readable gate and validation results](results/live_progress.json).
Training rows are fixed-run diagnostics (p-val=n/a), not an efficacy claim. Validation receipts retain grouped-task bootstrap intervals and missingness bounds. Coverage requiring a judge remains unmeasured; a known zero local factor can determine a zero composite.
<!-- LIVE END -->

**TLDR-end:** [rl-4-code-verification: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3] The paired pilot is resuming with finished generations kept; seed 1301 strict update 10 is exporting and no provider calls were added.
