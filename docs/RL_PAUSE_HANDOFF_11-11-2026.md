# RL pause handoff (11-11-2026): where RL for code verification was left, and how to resume

> **RESUMED 11-25-2026 10:05 PST (Brando):** "given we have a round robin right now, I think it's good to use it. Hopefully this saves us tokens so let's turn on all the RL stuff back." The pause below is over: RL runs, the daily RL check and held Sherlock jobs resume. Rules kept: free hardware only (no paid API), the 80% plan ceiling, no extra charges, claim each experiment in agent-sync `assistants/experiment-claims.md` first. The pause note at the top of `AGENTS.md` and `CLAUDE.md` is removed in the commit that adds this note. The text below is the state as of 11-11-2026.

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/RL_PAUSE_HANDOFF_11-11-2026.md>

**TLDR:** On 11-11-2026 (16:25 to 16:33 PST) Brando paused all RL experiments until he explicitly re-engages after his Dec 10 defense. No new runs, no queued job goes ahead, and nobody (the assistant "ub9sc" = ultimate brando9 scalable coworker, other agents, collaborators) spends credits or compute on RL meanwhile. This file records the state at the pause so any agent can continue later. Last result: Experiment 25 (smooth versus strict reward) did not replicate with a third seed; the earlier +4.25 is superseded.

## The rule (Brando's words, 11-11-2026)
- 16:25: "I don't think I have mental bandwidth to keep track of the RL for code verificaiton experiments. Are you running more experiments? Can we pause all your RL experiments for now at least until my defense december 10th?"
- 16:29: "but pause themt oo cuz I don't want you to spend credits or anyone credits on it right now"
- 16:29: "drop RL until december 10th and I explicitly re-engage with it."
- 16:29: "document well were we left off so other agents or u can continue it them"
- 16:33: "I do like azalia's idea on smooth metric --> downstream harsh metric but for now I will do that later (if at all)"
- So: RL stays off after Dec 10 too, until Brando says so himself. No automatic resume date. Do not ask him to re-engage; do not send RL updates.
- Until then his experiment and paper time goes to what feeds the thesis and defense: VeriBench v1, the judge papers, cert judge and VeriBench private. RL is not part of that.

## What is running, queued, held (checked live 11-11-2026 ~16:45 PST by ssh)
- **Sherlock (account sanmi):** no RL job running. 18 job ids (21 pending array entries) of the rl-env-scaling cross-family replication (Llama-3.2-3B, Qwen3-4B, Gemma-3-4B; `/scratch/users/brando9/xfam`) are held with `scontrol hold` (JobHeldUser), not cancelled, dependency chains kept. Ids: 50675045_3, 50675049, 50675050, 51640615 to 51640623, 51640625, 51640651 to 51640655. The held ids are listed again in `rl-env-scaling/docs/RL_PAUSE_HANDOFF_11-11-2026.md`.
- **skampere1:** none of brando9's RL jobs running. The Exp 25 third-seed run ended `FULL_RUN_DONE`. The cron `e13v3-autoresume` (restarted dead Exp 13 v3 pilot trajectories every 10 min; it was only logging "restart limit 3 reached") is commented out with the marker `# agent-stop 11-11-2026_RL-pause-until-Dec11` (the marker's "Dec11" is not a resume date; resume only when Brando explicitly re-engages); backup of the crontab: `/lfs/skampere1/0/brando9/crontab.before_rl_pause_11-11-2026.bak`. Other RL crons were already stopped 11-03-2026. Exp 08 orphan-cleanup and capacity-probe crons are still active (they clean up and probe, they start nothing).
- **skampere2, FarmShare:** nothing RL running or queued.
- **Not checked:** Snap (ssh exit 255, no reason) and Delta (ACCESS CIS262365, sign-in not verified). Nothing is known to be queued on either.
- **Not RL, left alone:** vb-priv rerun `vb120_batch4_rerun_v1`; jr1-c03/c04 (JR1 Exp 03/04, Qwen joint reasoning retention); the `sherlock-agent-bridge` service job.

## Results already on main (all numbers copied from the repo files named; harness and model as each file states)
Index caveat: `experiments/README.md` is stale after 10-28-2026 for Exp 08, 18, 20 and 25. Per-experiment `results.md` files are the truth.

| Experiment | Result | Harness / model | Where |
|---|---|---|---|
| **25 smooth (B) vs strict (A) reward GRPO** | 3 seeds per arm, update-48 validation strict pass@1: A 37.34 / 54.26 / 61.06, B 49.86 / 50.23 / 3.82. Pooled A 50.89 [43.55, 57.84], B 34.64 [28.99, 40.15], **B minus A -16.25 [-19.17, -13.28]** (task bootstrap, 10,000 draws; holds the 6 trained models fixed). Pre-registered rule (B minus A at least +1.5, lower bound above 0) **not met**. Run level (6 runs, exact permutation) p = 0.50: no reliable difference, B has a failure mode. **B seed 2 stalled** (never learned: 5.3 -> 6.8 train successes per 128 rollouts vs 44 to 73 for the other five runs; compile rate 3.84%; outputs valid, so a stalled run, not a broken eval). Why it stalled: not known. A skampere1 reboot (~21:27 on 11-10) killed both seed-2 lanes; both resumed from the update-8 state; A s2 did not stall; the resume path was not tested. The earlier 2-seed **+4.25 [1.05, 7.78] is superseded**; anything citing it needs the correction. | `train_e25.py` (fp16, vLLM sampling) + local frozen strict Lean scorer, Qwen3-1.7B Lean SFT (step_658), A100 on skampere1, no DT, no paid API, veribench@1.3, D-013 split | `experiments/25_smooth_vs_strict_reward_grpo_qwen3_1p7b_sft_vbv1_3_d013/results.md`; third seed `expt_v1/results/full_run_at2925/`; commit 72870984 |
| 18b generated-env pre-RL scoring | 16 Reasoning Gym envs x 2 seeds. The rho-H law ranks environments better than chance (Spearman +0.476 [+0.04, +0.74]) but its top pick (rg/mini_sudoku/L2) has top-1 regret 0.382 vs 0.232 for a random pick. | Qwen3-1.7B, thinking off, custom PyTorch/HF GRPO, vLLM 0.30.0 eval, no DT; Sherlock H100; 32 runs, all exit 0 | `experiments/18_.../expt_18b/results_18b.md` |
| 08 v26 seed replicates (Sherlock) | 1.7B seeds 4.81 / 5.37 / 4.91% val pass@1 (SD 0.30); 4B 8.98 / 8.70% (SNAP 4B 9.26%); noise bar: gaps under ~1 pt pass@1 or ~5 pts pass@8 are noise | Qwen3-1.7B/4B-Base Lean SFT, vLLM + Lean scorer, no DT, Sherlock | `experiments/08_.../expt_v26_sherlock_seed_replicates/` |
| 08 v28 Llama | Llama-3.2-1B 2.96%, 3B 7.35% val pass@1 (3 seeds each, no DT); 3B minus 1B +4.38 [2.62, 6.42]; below Qwen3 at matched size but CIs overlap. Gemma-3 smoke package prepared, not submitted. | Llama-3.2 Lean SFT, Sherlock, $0 | `experiments/08_.../expt_v28_llama32_family/results.md` |
| 20 to 24 | Exp 20 stopped at its trainer gate (log-prob mismatch 2.62% > 1%); fix found: fp16/fp16 passes (0.065%), bf16 does not (2.4 to 6.4%). | Qwen3-1.7B SFT | `experiments/20_*`, `21_*` to `24_*` |
| 13 v3, 19, 16, 17, 14, 15, 12, 10 | zero-cost analyses and the Exp 13 v3 pilot as in `experiments/README.md` (not re-read today). | see README | `experiments/README.md` |
| rl-env-scaling xfam | small-scale cross-family replication stopped by the 0.5 pp spread rule (prereg D5, D10); mid-scale (Qwen3-4B, Gemma-3-4B, Llama-3.2-3B) pre-RL chain submitted 11-01 and continued 11-09: pre-RL sampling jobs only, **no mid-scale RL training trained, no result claimed**. | custom PyTorch + vLLM 0.30.0 via Apptainer, Sherlock L40S/H100, no DT | `brando90/rl-env-scaling` `replication/cross_family/results/RUNS.md` |

Not checked today: whether anything finished on Sherlock or skampere1 after the last repo commit (72870984); the Exp 08 v3 14B expansion waiter on skampere1 (per `experiments/README.md`, a waiter restarts a 14B job when its GPUs are free; its current state is unknown); Snap and Delta.

## Open work at the pause (none of it runs now)
- Exp 25: a fourth seed of B and a stall check of B seed 2 were proposed (about a day on free skampere1 A100s) and **not run**. Cancelled by the pause; do not start unless Brando re-engages.
- Exp 25 Stage 2b real Lean RL pilot for checkpoint reuse (gated); Exp 03 / 02B (need a trainer and frozen forecast, about 90 and 500 to 700 B200 GPU-h); Exp 13 v3 retries (missing optimizer checkpoint, no free GPU); widening the replications past the 0.5 pp spread rule (Brando had said widen).
- rl-env-scaling xfam: mid-scale RL cells (HH/HL/LH/LL x seeds 1,2 x 128 steps) after the held selection/gate jobs; small-scale Llama-1B/Gemma-1B/Qwen-1.7B RL cells; OLMo-2-1B only if budget allows; admission-mechanism ablation (overlong filter off).
- Exp 08 v28 Gemma-3 (1B, 4B) smoke on Sherlock.
- Emails to Ethan Lee and Rakshit urging them to engage with rl4cv, and the follow-ups that push others into RL: held. Do not send them.
- Azalia's smooth-to-harsh idea (`docs/SMOOTH_TO_HARSH.md`): Brando likes it, will do it later "if at all".

## Brando's Exp 25 message, saved as pasted (11-11-2026 16:32, "save this as it's part of the RL stuff we aren't going to do right now")
> Exp 25 did NOT replicate: with the third seed, smooth (B) no longer beats strict (A). The earlier +4.25 for B is gone.
> - Harness and model: train_e25.py, Qwen3-1.7B Lean SFT, strict Lean scorer, free A100s on skampere1, no DT, no paid API.
> - Strict pass@1 at update 48, A / B per seed. Seed 0: 37.34 / 49.86. Seed 1: 54.26 / 50.23. Seed 2: 61.06 / 3.82.
> - Pooled over 3 seeds: A 50.89, B 34.64, B minus A -16.25 [-19.17, -13.28]. That interval only resamples tasks, not runs.
> - Run level (6 runs, exact permutation): p = 0.50, so no reliable difference either way.
> - B seed 2 never learned: its training successes stayed flat while the other runs rose. The outputs are valid, so it's a stalled run, not a broken eval. Why it stalled: not known. A skampere1 reboot hit both seed-2 runs and A recovered fine, but I didn't test the resume path.
> - Anything citing +4.25 needs the correction.
> - Everything is in commit 72870984 on main, no branch.
> Your call: run a fourth seed of B plus a stall check on seed 2? About a day on free A100s, no spend. My suggestion is yes, since 1 stall in 3 runs is too few to say if B is flaky.

## How to resume (only after Brando explicitly re-engages; ask nobody else first)
1. Get his explicit word in writing (message or email) that RL for code verification is back on. After Dec 10 is not enough by itself.
2. Check spend rules in `CLAUDE.md` (free hardware, no paid API; the automatic-job rules: transcript log, end condition, manifest, 80% ceiling, stop email).
3. Sherlock: `scontrol release <id>` for the held ids above, in dependency order (the chains keep their `afterok` dependencies; check `squeue -u brando9 -o "%i %j %T %r"` first).
4. skampere1: if the Exp 13 v3 autoresume is wanted, restore the cron line from `/lfs/skampere1/0/brando9/crontab.before_rl_pause_11-11-2026.bak` (remove the `agent-stop` marker). Check free GPUs first (`nvidia-smi`); GPUs 6 and 7 belong to another user.
5. Re-enable the assistant's recurring RL check and weekly RL update only on his word.
6. Remove the pause note from the top of `AGENTS.md` and `CLAUDE.md` in this repo and in `rl-env-scaling`, in the same commit that resumes.
7. Start with his decision on the Exp 25 fourth seed of B and the stall check (the open question above). Straight to main, no branches; numbered experiment folders.
