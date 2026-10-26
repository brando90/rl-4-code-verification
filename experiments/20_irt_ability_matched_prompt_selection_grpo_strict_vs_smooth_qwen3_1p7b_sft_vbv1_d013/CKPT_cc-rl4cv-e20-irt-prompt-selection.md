# CKPT cc-rl4cv-e20-irt-prompt-selection: worker resume record for experiment 20 (IRT prompt selection for GRPO)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/CKPT_cc-rl4cv-e20-irt-prompt-selection.md>

**TLDR:** Resume record of the Claude Code worker (tmux `cc-rl4cv-e20-irt-prompt-selection` on skampere1, deployment `deploy_ed87a5b1900b45d2af6e22c1707cc31e`, claude-fable-5-1 at max, profile cc, bypass permissions) that runs experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013 end to end. `CKPT_e20.md` is the dispatcher-facing checkpoint and points here.

Created: 10-21-2026 11:38 PDT
Last updated: 10-21-2026 12:40 PDT

## Goal
- Does IRT-online prompt selection (C) raise D-013 validation strict pass@1 over uniform (A), a pass-rate filter (S) and DAPO (E) at matched rollouts, and does a smooth reward (B, D) substitute for or add to it? Gated: Phase 0 -> IRT fit + G0 -> smoke -> pilot -> main -> evaluation. HANDOFF to a Codex gpt-6-astra ultra worker at 10-21-2026 12:40 PDT (see Log).

## What ran
- Done on branch `e20-irt-prompt-selection` (all pushed): PROTOCOL.md frozen draft (H1-H4, G0, arms, recipe, statistics fixed before any Phase 0 outcome), results.md live, README design, code: `expt_v1/{samplers,loss,irt,stats,train,analyze_phase0b}_e20.py` + 22 unit tests (`tests/test_e20_*.py`, all pass with CUDA_VISIBLE_DEVICES=""), Sherlock scripts in `expt_v1/sherlock/` (all pushed to `$SCRATCH/rl4cv_sherlock/e20/code/` via `sherlock/push_code_e20.sh`).
- Sherlock: train pack PASS (539 tasks, 135/135 validation prompt hashes reproduced; `e20/phase0/train_pack_manifest.json`); Phase 0a array **48841018** (chunk 0 RUNNING on sh04-11n10 since 12:02 PDT, 384/1,078 rows at 12:39; chunks 1-3 PENDING); scoring smoke **48841951 COMPLETED** (frozen scorer = experiment 08 v16 columns on 3/3 trials; adapter agrees 2/2, 1 parse failure -> zero credit per protocol); trainer smoke **48845232 PENDING** (builds the TRL 1.16 venv overlay in the SIF, then 2 updates of arm A with the log-prob mismatch gate). RUN START email sent for Phase 0a.
- Local: `analyze_phase0b_e20.py --synthetic --skip-cv` completed (exit 0; receipt `expt_v1/results/synthetic/phase0b_tables_e20.md`): the Phase 0b pipeline runs end to end.

## Results
- No experiment 20 number yet. Baseline from experiment 08 expt_v16: start policy validation strict pass@1 58/1080 = 5.37% [3.15, 8.06]. GPU-h used: Phase 0a about 0.6 (chunk 0 running) of the 10 GPU-h Phase 0 cap; $0 API.

## Stuck / blocked
- nothing. Sherlock gpu queue is deep (530 pending at 11:30 PDT); jobs are queued, not blocked. Inbox search for other agents' RUN START emails was not possible from this host (no mail read access; recorded, not blocking).

## Next steps
1. Watch 48841018 and 48845232 (`sherlockctl exec 'squeue -j 48841018,48845232 -h -o "%i %T %M %R"'`, >= 60 s apart). Do not cancel anything.
2. When all 4 `e20/phase0/gen/chunk_*/timing.json` exist: `sherlockctl exec 'module load python/3.12.1; cd $SCRATCH/rl4cv_sherlock/e20 && python3 code/materialize_e20.py'`; then `sherlockctl submit <expt_v1>/sherlock/phase0_score.sbatch` and `... phase0_partial.sbatch` (32 + 32 normal-partition tasks).
3. After both arrays: `sherlockctl exec 'module load python/3.12.1; RL4CV_SRC=$SCRATCH/rl4cv_sherlock/grading/rl4cv/src python3 $SCRATCH/rl4cv_sherlock/e20/code/build_phase0_cells_e20.py'`; gzip + `sherlockctl get` `e20/phase0/phase0_cells_e20.csv` (get limit 1 MiB) into `expt_v1/results/phase0_cells_e20.csv`; commit. Then locally `venvs/rl4cv_e20/bin/python expt_v1/analyze_phase0b_e20.py --workers 8` (about 30-60 min CPU; G0 verdict; freezes `expt_v1/forecasts/e20_item_params.json`); commit; if G0 fails drop C and D.
4. Trainer smoke 48845232: read `$SCRATCH/rl4cv_sherlock/e20/smoke_train/A_s1/smoke_logprob_check.json` and `smoke_train/runtime_versions.json` (copy into `expt_v1/results/`); first-run risks: TRL helper + vllm 0.30 `external_launcher` inside Apptainer, sleep mode, CPU AdamW master weights, per-request seeds; fix and re-push with `sherlock/push_code_e20.sh`.
5. Pilot (needs G0 + smoke): `sherlockctl exec 'bash $SCRATCH/rl4cv_sherlock/e20/code/sherlock/submit_train_e20.sh A 1 16'`, `... S 1 16 "" $SCRATCH/rl4cv_sherlock/e20/phase0/phase0_cells_e20.csv`, `... C 1 16 "" "" <pushed e20_item_params.json>`; RUN START email; pilot gates; lock PROTOCOL (commit hash in results.md); main 6x2x48 (A/C/S seed 1 resume from pilot state); evaluations via `sherlock/submit_eval_e20.sh <label> <model_dir>` (update 0 once, then 16/32/48); statistics with `stats_e20.py`; plots; experiments/README.md row; `expt_v1/results/E20_FINISHED.txt`; RUN DONE email; one PR into main (not merged by the worker).

## Brando to-do
- none
## Log
- 10-21-2026 11:38 PDT -- worker started; dispatch receipt logged in CKPT_e20.md; README dispatch line fixed (profile cc); branch e20-irt-prompt-selection created from origin/main 63a0d3d0.
- 10-21-2026 11:54 PDT -- Phase 0a generation submitted: Sherlock array 48841018_[0-3]; RUN START email sent; PROTOCOL.md draft + results.md written.
- 10-21-2026 12:23 PDT -- scoring smoke PASS (job 48841951); trainer smoke submitted (job 48845232); trainer/loss/samplers/IRT/stats code + 22 unit tests pushed (ab2f28e6); PROTOCOL reward-of-unresolved note added.
- 10-21-2026 12:40 PDT -- analyze_phase0b_e20.py (synthetic) PASS; Sherlock train/eval/submit scripts pushed; Phase 0a chunk 0 at 384 rows; trainer smoke 48845232 pending.
- 10-21-2026 12:40 PDT -- worker change: Claude Fable 5.1 (personal account) -> Codex gpt-6-astra ultra (personal ~/.codex), reason: Claude personal weekly allowance reserved; implementation-only role, no measured model or protocol change. Monitors still running at handoff: Claude session Monitor task b99ixz2kg (Sherlock poll every 10 min, expires by about 12:53 PDT on its own); dispatcher tmux `watch-e20`. Local background: none (synthetic run finished). Open decisions: main-phase GPU-h (estimate 96-170 vs cap 130) decided after the pilot's measured per-update time; two-skill check optional (`--two-skill`); experiment 05 Base models excluded from the primary fit (sensitivity reported); Google experiment-log bullet goes into results.md + DONE email (no Google access here).
