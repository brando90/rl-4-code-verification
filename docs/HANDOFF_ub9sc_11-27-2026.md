# SNAP handoff for ub9sc (ub9cw) — 11-27-2026

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/docs/HANDOFF_ub9sc_11-27-2026.md

**TLDR:** Brando approved moving the non-GPU prep forward on 11-27-2026. ub9sc takes the SNAP half: a fresh GPU inventory, an agent-sync claim, then the 14B relaunch and the 02B v2 gates that still need Lean or a GPU. Check live job `job-1ca3e7a2` before any fourth seed of experiment 25 arm B. Free hardware only, no paid API, 80% plan ceiling, work under `/lfs/$(hostname)/0/$USER/`.

**Authorization:** Brando, 11-27-2026: "fix it all, I want 'yes go ahead, move the projects forward, I approve!'" The four items below are the ones he named from `docs/NEXT_STEPS_11-26-2026.md`. This note does not launch a job. D-111 limits stand: free hardware only, no paid API, the 80% plan ceiling, no extra charges. The 22 historical remote branches stay (D-112).

Account on the handoff: `ub9sc` (`ub9cw`). Work root on whichever SNAP host is admitted: `/lfs/$(hostname)/0/$USER/`. Never DFS home.

## R1 — experiment 08, four 14B validation rungs

Plan and CPU gate: [r1_14b_oom_fix_launch_plan_11-27-2026.md](../experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/r1_14b_oom_fix_launch_plan_11-27-2026.md) and `r1_14b_memory_budget_11-27-2026.py` in the same folder.

- Host order: eight exclusive B200s on skampere3, else eight exclusive H200s on skampere2. A100-80GB on skampere1 is refused for this rank.
- Floors: 160 GiB free on each B200, 120 GiB free on each H200, `used_mib == 0`, no foreign compute PID. Set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
- Rungs, in order: `v3_E_14b_f0p5` (step 335), `v3_E_14b_f1p0` (step 667), `v3_R_14b_f0p5` (step 334), `v3_R_14b_f1p0` (step 658). Each is 0/1,080 today.
- Leave the locked `PROTOCOL.md`, the frozen forecast, and the 12,960 measured cells untouched. New logs and coverage go in `expt_v3/results/r1_14b_11-27-2026/`.
- Before launch: fresh `nvidia-smi` inventory, agent-sync claim, hash-check `ckpt/14B/hf/step_658`. Do not call `multinode_training.py` (that plan puts two ranks on A100s).

## R2 — experiment 02B v2, on free H200s only after the scientific gates

Prep: [prerequisites_11-27-2026.md](../experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/prep_11-27-2026/prerequisites_11-27-2026.md).

- Public init is pinned: `Qwen/Qwen3-1.7B-Base` @ `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`. Re-hash it on the host. Do not load an experiment 08 VeriBench SFT checkpoint.
- Accepted reference proofs are still open (6/24 kernel-honest, 16/24 `sorryAx`, 2/24 unknown). lethan3 runs Lean 4.22.0. The exact commands that do not count as acceptance are in the prep note.
- Freeze the forecast with `forecast_freeze_11-27-2026.py` only after pre-RL ρ and H exist, and before any training outcome is read. `paper_frozen_14b_model()` is OpenR1-Math, not a Lean standardizer.
- The 11-25-2026 19:54 PST inventory (skampere2 H200s 4–7 idle) is stale. Take a new one. Placement: B200, then H200, then A100-80GB, among free devices.

## R5 — look at job-1ca3e7a2 before a fourth B seed

`docs/qa_11-25-2026/snap_status_at3598_11-25-2026.md` saw job `job-1ca3e7a2` live on skampere1, log `B_s3`, command `train_e25.py --arm B --seed 3`, last completed update 6 at 19:03:35 PST on 11-25-2026, parent timeout 12 hours. The repository still has no outcome for a fourth B seed. D-111 said that seed had not been launched as of 10:05 that morning; the later inventory found this process. Read the log and the exit receipt under `/lfs/skampere1/0/brando9/at3558/` before deciding. Experiment 25 is final at three seeds per arm unless that job's receipt says otherwise. Do not start another B seed while this question is open.

## How to start

Follow `scripts/cc_prompt_run_experiment_on_snap.md`: inventory every host, then the GPU order B200 (skampere3), H200 (skampere2), A100-80GB (skampere1). Baseline, estimate, the go-ahead above, launch, verify, clean up. Release idle GPUs when a stage ends.

**TLDR-end:** [rl4cv: ub9sc handoff 11-27] Brando approved the prep. ub9sc inventories free GPUs, claims the 14B exclusive-node relaunch and the 02B Lean gates, and reads job-1ca3e7a2 before any fourth experiment 25 seed.
