# Next steps and open-work register after the 11-26-2026 issue close-out

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/docs/NEXT_STEPS_11-26-2026.md

**TLDR:** On 11-26-2026 Brando asked to close all issues, merge all branches to main, and suggest and do the next steps (D-113). The four open issues (#3, #5, #6, #34) are closed with a comment each. None of the work they tracked is finished, so it is carried here as items R1 to R6 with owners, blockers, evidence and launch gates. All 22 branches were already contained in main. On 11-27-2026 Brando approved the four non-GPU prep items (D-114). The plan, the 02B config, the experiment 14 pin and the SNAP handoff are linked below. Nothing in this file launches a GPU job: every launch still needs a fresh GPU inventory and an agent-sync claim. The handoff is [HANDOFF_ub9sc_11-27-2026.md](HANDOFF_ub9sc_11-27-2026.md).

## 1. What this replaces

Issues #34 (experiment 08 14B rungs), #6 (experiment 02), #5 (experiment 07) and #3 (SNAP runs) were the only open issues. Their last comments, posted 11-25-2026, each say the issue remains open and name a blocker. Closing them without a register would lose that tracking, so this file keeps the blockers, owners, evidence and launch gates. Owners are unchanged. Reopen an issue if the tracker is wanted again.

`[p N/10]` below means my confidence that the step is the right next one and can go ahead as written.

## 2. Open-work register

1. **R1. Experiment 08, four Qwen3-14B-Base validation rungs (was #34).**
   - Missing: `v3_R_14b_f0p5`, `v3_R_14b_f1p0` (original-data replay, half and full budget) and `v3_E_14b_f0p5`, `v3_E_14b_f1p0` (admitted expansion, half and full budget). Each is 0 of 1,080 measured (VeriBench V1 validation, 135 tasks × 8 attempts, no DT, Lean `kernel_binary`). 4,320 of 17,280 version-3 validation cells are missing; 12,960 are measured and stay untouched.
   - Blocker: the last expansion attempt hit CUDA out of memory on skampere3 at step 183 of 335 toward the half-budget checkpoint; no half-budget checkpoint was kept and replay 14B had not started. The device list in the old issue is a historical receipt, not a running job.
   - Gate: a fresh inventory and an agent-sync claim; free hardware only. Brando's 11-27-2026 go-ahead covers the plan (D-114). The launch itself is still the SNAP host's step. Preserve every locked `PROTOCOL.md`, frozen forecast, the validation denominator and the held-out test split; add new evidence beside the measured cells.
   - Plan (11-27-2026): [memory fix and launch plan](../experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/r1_14b_oom_fix_launch_plan_11-27-2026.md). Exclusive 8× B200 on skampere3, else exclusive 8× H200 on skampere2. A100-80GB is refused. The recorded cause is a foreign 130.69 GiB process, not the Gemma chunked-logit bug.
   - Evidence: [version-3 results](../experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/results.md) and [closing note](../experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/closing_note_11-25-2026.md).
2. **R2. Experiment 02B to 02D (was #6; owner lethan3).**
   - Done: the behavioral adapter supports 24 of 24 real frozen tasks (158 of 158 fixed behavioral tests, Lean 4.22.0, no DT; commit [8ac36188](https://github.com/brando90/rl-4-code-verification/commit/8ac36188), a real VERINA adapter with a 24-task Lean regression). The historical 0 of 24 full-endpoint result is preserved.
   - Missing: accepted reference proofs, the production rollout and training configuration, and a prospective forecast frozen before any outcome is read. The 11-25-2026 comment says bounded 02B v2 permits a pinned public Qwen3 Base initialization ([db70b465](https://github.com/brando90/rl-4-code-verification/commit/db70b465)).
   - Hardware is not the blocker: GPU approval was given and skampere2 H200s 4 to 7 were idle at the 11-25-2026 19:54 PST inventory (not reserved). 02B was not launched; the launch checks and their exit-2 NOT LAUNCHED receipts are in [b2937d63](https://github.com/brando90/rl-4-code-verification/commit/b2937d63).
   - Prep (11-27-2026, still not launched): [prerequisites](../experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/prep_11-27-2026/prerequisites_11-27-2026.md). Public `Qwen/Qwen3-1.7B-Base` @ `ea980cb0a6c2ae4b936e82123acc929f1cec04c1` is pinned. Accepted proofs, probes and the forecast freeze still wait on Lean and a fresh inventory.
   - Evidence: [adapter README](../experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/adapter_11-25-2026/README.md), [SNAP status](qa_11-25-2026/snap_status_at3598_11-25-2026.md).
3. **R3. Experiment 03, RL on never-solved Lean prompts (was #3; owner Allen).** No locked protocol exists yet, and it needs the external-only warm start from R2. Write and lock the protocol before any run. Folder: [03](../experiments/03_rl_on_never_solved_lean_prompts_binary_vs_dense_reward_eval_vbv1/).
4. **R4. Experiment 07 phases B and C (was #5; owner emxia18).**
   - Done: saved-result CPU diagnostics and one real D_gold control (256 of 256 gold-repeat agreements, 256 of 256 base disagreements, DT). Commit [266516c1](https://github.com/brando90/rl-4-code-verification/commit/266516c1).
   - Missing: 730 of 731 task controls, whole-package admission, the separate phase B procedure and authenticated included-funded solver panel, and phase C.
   - Blocker: the Valkyrie login is expired (D-108 route); only Brando can refresh it.
5. **R5. Experiment 25, optional fourth seed of arm B, and one job to check (was #3).** The experiment is final at three seeds per arm (11-11-2026; update-48 B minus A is −16.25 points [−19.17, −13.28]; B seed 2 stalled at 3.82%). A job named `job-1ca3e7a2`, log `B_s3`, was live on skampere1 at the 11-25-2026 inventory; its name suggests a fourth B seed, but the repository records no outcome for it. Check that job before launching anything else; D-111 said the fourth seed had not been launched at 10:05 that morning. [Results](../experiments/25_smooth_vs_strict_reward_grpo_qwen3_1p7b_sft_vbv1_3_d013/results.md).
6. **R6. How to start any SNAP run (was #3's body).** Use [`scripts/cc_prompt_run_experiment_on_snap.md`](../scripts/cc_prompt_run_experiment_on_snap.md): inventory every host, pick by the rule B200 (skampere3) then H200 (skampere2) then A100-80GB (skampere1), and follow the GPU discipline in CLAUDE.md (baseline, estimate, ask Brando, launch, verify, clean up). Work under `/lfs/$(hostname)/0/$USER/`, never DFS home. D-111 limits stand: free hardware only, no paid API, the 80% plan ceiling.

## 3. Findings from the 11-26-2026 QA that the owners should act on

1. **Experiment 14 (locked run not portable).** Its stop rule compares the experiment 07 H2 replay at n_A = 50 with exact equality. On numpy 2.5.3 the replay gives −0.012140 against the published −0.012139 (sixth decimal; the split count 92 of 2,000 is identical). The locked run used numpy 2.2.6 and scipy 1.16.3. **Acted on 11-27-2026:** [dated amendment](../experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/AMENDMENT_stop_rule_numpy_pin_11-27-2026.md) pins those versions and, for any other numpy, uses a 5e-6 median tolerance with exact split counts. `PROTOCOL.md` was not edited.
2. **Experiment 10 v2 wording.** "Within 0.0035" holds at q = 0.50 (maximum 0.00345). At q = 0.25 one absolute-reduction contrast differs by 0.0037 and relative reductions by up to 0.030. A dated scope note is added to the v2 results.
3. **Stale statuses.** **Refreshed 11-27-2026 from committed files.** Experiment 08 version 6: last measurement 10-19-2026 04:55 PDT is not a live job; 1.7B control 99/1,080 and mixed 74/1,080 are complete in `expt_v6/results.md`; 4B mixed is 526/904 updates and 0/1,080 validation cells, with no later completion file. Experiment 13 version 4: Dispatch 8 CPU implementation landed 10-21-2026, admission `9209a408ce9ca1d6ae42e5769dd61c9228d0155dd89eba80ebc74a5ee490d2a4`, T1 and every gate statistic unmeasured (`expt_v4/CKPT_v4_implementation.md`). Experiment 16 toy: the README TLDR-end now follows the results ledger through night 5 (POSITIVE, law+alpha regret 0.96 [0.56, 1.73] vs random 2.23). The index rows match these files.
4. **Test counts.** `qa_11-25-2026/results.md` line 64 reports 1,399 passed, 7 failed, 65 skipped, 1 error; the committed log ends with 7 failed, 1,440 passed, 48 skipped. The log is the record.
5. **Three folders are numbered 25** (checkpoint reuse, the fp16 real-Lean smoke, smooth versus strict). All three are now in the index; none is renamed, because commits and results cite the current names.

## 4. Next steps, in order

1. **[p 9/10] Refresh the Valkyrie login (Brando).** It unblocks R4 and any D-108 run.
2. **[p 8/10] Open the two Anarres pull requests (Brando).** Both merge cleanly into upstream main and pass their gates; the commands are in [anarres_11-26-2026/README.md](anarres_11-26-2026/README.md).
3. **[p 7/10] Finish the 02B prerequisites that still need Lean (lethan3 with ub9sc).** The 11-27-2026 config and freeze command are in the prep folder. Accepted reference proofs, then the host re-hash and mismatch baseline, then freeze the prospective forecast with `rl4cv.forecast.freeze_forecast` before any outcome is read, then launch 02B v2 on free GPUs after a fresh inventory.
4. **[p 7/10] Run the 14B memory plan (R1) on free hardware.** The plan is written (D-114). ub9sc takes a fresh inventory, claims the job, and launches on exclusive B200s or H200s. The evidence files are named in the plan.
5. **[p 6/10] Decide whether experiment 25 needs a fourth B seed (R5).** The first question is what `job-1ca3e7a2` is.
6. **Done 11-27-2026: the experiment 14 stop rule is pinned** (finding 1). A rerun uses numpy 2.2.6 and scipy 1.16.3, or the dated 5e-6 amendment. The locked protocol file was not edited.

## 5. Decisions only Brando can make

1. Repository visibility and the scope of the privacy rule in `CLAUDE.md` (details were sent to Brando directly).
2. Whether `docs/anarres_11-25-2026/` (two git bundles and reviews of another project) stays here once the Anarres pull requests are open.
3. Deleting the 22 remote branches (still on hold per D-112). Two superseded branches hold the only copies of six files, so tag them first. Agent sessions cannot push tags (the proxy refuses), so run once from a normal checkout:
   ```
   git fetch origin claude/admiring-heisenberg-eok3j4 ub9/valkyrie-hosted-migration
   git tag archive/claude-admiring-heisenberg-eok3j4-11-26-2026 b5e3125960d21a4b2934fad2f43dc8f350a2540a
   git tag archive/ub9-valkyrie-hosted-migration-11-26-2026 e9d69a3808a3e2d8ed2fccc6fdec3c8de71f50c4
   git push origin archive/claude-admiring-heisenberg-eok3j4-11-26-2026 archive/ub9-valkyrie-hosted-migration-11-26-2026
   ```
   The six files: four under `experiments/01_predict_rl_env_utility_veribench_qwen35_snap/` (`README.md`, `config.yaml`, `scripts/cc_prompt_launch_phase0_on_snap.md`, `scripts/cc_runbook_phase0_coverage_census.md`) and `src/rl4cv/valkyrie_hosted.py` with `tests/test_valkyrie_hosted.py`.
4. The SNAP launch of R1 and R2 after the 11-27-2026 prep (inventory and claim still required; the handoff names them), whether R5's fourth seed is wanted after `job-1ca3e7a2` is read, and refreshing the Valkyrie login for R4.
5. The three open decisions in [MERGE_PLAN_rl4cv_into_anarres_11-25-2026.md](anarres_11-25-2026/MERGE_PLAN_rl4cv_into_anarres_11-25-2026.md).

**TLDR-end:** [rl4cv: next steps 11-26-2026] The four issues are closed and their unfinished work is items R1 to R6 here. On 11-27-2026 the 14B plan, the 02B pin and freeze command, the experiment 14 numpy pin and the ub9sc handoff landed. The next SNAP moves are a fresh inventory, the 14B exclusive-node relaunch, Lean reference proofs for 02B, and a look at job-1ca3e7a2.
