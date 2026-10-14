# Experiment 13 v2 resume brief: fresh owner from G0 onward (SNAP, skampere1)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/cc_resume_g0.md>

**TLDR:** You are the new single writer for experiment 13 version 2. You replace the previous owner session `codex-rl4cv-e13v2-owner`, which is idle and low on context; do not use it or brief it.

Work in this order:

1. Re-arm the version 2 watchdog additively, for your own session.
2. Verify the exclusion manifest.
3. Freeze the A3 G0 wrapper, its tests and its lock.
4. Run G0 once.
5. If G0 passes, continue through Phase 1 and then Phase 2, as `PLAN.md` revision 2 and its amendments define them.

Success is a published report for each gate, ending with Phase 2's test analysis, or an honest stop under PLAN § 4's transition table with its evidence.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Read first

1. **Rules:** `~/agents-config/INDEX_RULES.md` and this repository's `CLAUDE.md`.
2. **In `expt_v2/`:**
   - `R2_A3_ADMISSION_10-14-2026.md`: **your entry point, binding**;
   - `PLAN.md`: binding;
   - the amendments: `AMENDMENT_A1_development_gates_10-13-2026.md`, `AMENDMENT_A2_R2_untyped_cells_and_admission_10-13-2026.md`, `AMENDMENT_A3_PROPOSED_R2_diagnosis_and_admission_10-14-2026.md` (adopted) and `AMENDMENT_A3_ADOPTION_10-14-2026.md`;
   - the results so far: `RESULTS_R2.md`, `RESULTS_R2_diagnosis.md` and `RESULTS_L1v2.md`;
   - the frozen G0 code: `reproduction/README.md` and `reproduction/g0.py`;
   - status: `CKPT_e13_v2_owner.md` and `results.md`.
3. **Also:** `../PROTOCOL.md` §§ 3–8, `../expt_v1/PHASE1_IRT_PLAN.md` and `../expt_v1/PHASE2_MATCHED_RL_PLAN.md`.

## 1. Setup

- **Paths.** The work root is `/lfs/skampere1/0/brando9/rl4cv_e13v2` (`WR`). Use its clone `WR/rl-4-code-verification` after `git fetch`. Its frozen environment, virtual environment and private ledgers are yours to read.
- **Single writer.** Before you write anything, confirm that the old owner is idle at its prompt and has no child processes. Never type into its session.
- **Watchdog.** Re-arm `expt_v2/watchdog_e13v2.sh` for your own tmux session and process identity.
  - Add cron lines additively: back up `crontab -l`, append your lines, install the result.
  - Check that the installed crontab equals the backup plus your lines.
  - Never replace or clear the crontab. Read it only with `crontab -l`; bare `crontab -` cleared the schedule on 10-13.
  - Self-test the watchdog with the fake mailer.

## 2. G0, exactly as the admission record specifies

1. **Verify the manifest.** Check `WR/R2_diagnosis_10-14-2026/a3_ordinary_exclusions_private.json`:
   - its SHA-256 is `c00b35abaecda874820d4b1b29015655e248c19f319fa574fefa3d0804124128`;
   - it holds exactly 217 unique IDs, all in `WR/R2/ordinary_manifest.jsonl` and none from the test split;
   - its composition is 168 typed limits plus 2 class (a), 4 class (c) and 43 class (d);
   - it includes the 4 class (c) IDs that `RESULTS_R2_diagnosis.md` names.

   Publish its counts per split and per policy, but no IDs.
2. **Freeze.** Write `reproduction/g0_a3.py`, its tests and `locks/G0_A3.json` as the admission record specifies. The wrapper imports the frozen `evaluate` and never runs `g0.py`'s `main`. Run `E13_REQUIRE_LEAN_INTEGRATION=1 make test`, then push to `main`. Compute no G0 statistic before this push.
3. **Run once and publish.** Run the wrapper once and publish `RESULTS_G0.md` with:
   - the verdict;
   - the number of affected tasks;
   - the minimum and maximum of each statistic;
   - the minimizing and maximizing `evaluate` outputs for 4B, 1.7B and 8B.

   Then update `results.md` and `CKPT_e13_v2_owner.md`.
4. **Transition.**
   - PASS: go to Phase 1.
   - FAIL or INCONCLUSIVE: arms B and C stop and Phase 2 is not run (PLAN § 4). Publish the result, send the completion email and stop.

## 3. Phase 1, then Phase 2

**Phase 1** follows PLAN § 5 in this order:

1. LP-1, the generation admission;
2. the anchor panel;
3. freeze the calibration, item parameters and F2;
4. independent batch 2;
5. G1 and H2, with the admission record's G1 bounds frozen in a lock before any fit.

Use devices only through the experiment-13 lease registry, after checking every process and every other owner's leases. GPUs 0–3 were another user's vLLM on 10-13.

**Phase 2** follows PLAN § 6.

- The primary outcome is strict pass@1 under the frozen official scorer.
- Formal specification coverage (FSC) test evaluation needs the validated Valkyrie judge, which has returned HTTP 403 since 10-13 (rl4cv issue #68). Run everything else and leave that step pending, with the blocker recorded.

## 4. Throughout

- **Publishing.** Push each finished step to `main` after `E13_REQUIRE_LEAN_INTEGRATION=1 make test`.
  - Stage explicit paths only.
  - Check test exit codes directly, never through a pipe.
- **Checkpoints.** Update `results.md` and `CKPT_e13_v2_owner.md` at each gate, and at least every 4 hours.
- **No retries.** No gate is retried from L1v2 onward.
- **Limits.** On an account, context or turn limit, checkpoint and continue under Rule 48, keeping one writer.
- **Email.** Use only the watchdog mailer (PLAN § 7): at completion, or on an event that needs Brando.

**TL;DR:** watchdog (additive) → verify the 217-cell manifest → freeze the wrapper, tests and lock → G0 once with worst-case completions → Phase 1 → Phase 2. FSC test scoring waits for Valkyrie; publish every gate.
