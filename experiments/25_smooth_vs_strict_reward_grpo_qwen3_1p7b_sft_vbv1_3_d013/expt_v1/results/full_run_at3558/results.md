# Exp 25, fourth seed of arm B (AT-3558): launch record and B seed 2 stall check

**Dated 11-25-2026 10:55 PST (ub9sc, for Brando).** Status: **RUNNING, no result yet.** Harness: none (Slurm-free local lane on skampere1 with the repo's own `lane.sh` / `eval_local.sh`; no agent harness, no model API). Model: Qwen3-1.7B Lean SFT start checkpoint `step_658_float16` (Exp 08), fp16 trainer. DT label: no DT (local Lean strict pass@1 on the VeriBench v1 validation split, D-013).

## Launch record
- 11-25-2026 10:49 PST: arm B (smooth reward), seed 3, 48 updates, lr 5e-6, same flags as AT-2925 (`full_run_at2925/full_run5.sh`), one lane on skampere1 GPU 3 (the only A100 with 0 MiB used at 10:46; the other 7 carry other users' jobs and were not touched).
- Host job `job-1ca3e7a2` (ssh_launch, 12 h limit, ends 22:49 PST), script [full_run6.sh](full_run6.sh), outputs in `/lfs/skampere1/0/brando9/at3558/` (checkpoints in `at3558_ckpt/`; `/dfs/scratch1` is full, `/lfs/skampere1/0/` had 7.8 TB free). After training the same script evaluates u016, u032 (8 samples) and u048 (32 samples) on GPU 3.
- The script resumes from `state_latest` when rerun, so a second launch after the 12 h limit continues the run. Earlier seeds took about 12 to 17 h of training plus evaluation, so expect results about Thu 11-26 afternoon to evening.
- Nothing else launched for Exp 25: the 7 other A100s were busy at 10:36 (mostly Rylan's jobs) and Sherlock GPU jobs sit in the queue (Priority) behind the 18 rl-env-scaling jobs.

## Stall check of B seed 2 (analysis of existing logs, no new compute)
Script: [stall_check.py](stall_check.py), output: [stall_check_out.txt](stall_check_out.txt). Window means over updates of the training logs (`log.jsonl`), six runs of Exp 25.

| Run | Updates | mean strict (train) | active-group fraction | truncated rollouts / update | train_max_scaled_grad |
|---|---|---|---|---|---|
| B seed 0 | 25-48 | 0.355 | 0.42 | 0.6 | 169 |
| B seed 1 | 25-48 | 0.473 | 0.51 | 0.8 | 206 |
| **B seed 2** | 25-48 | **0.052** | **0.13** | **3.1** | 227 |
| A seed 0 / 1 / 2 | 25-48 | 0.269 / 0.283 / 0.438 | 0.41 / 0.37 / 0.48 | 4.8 / 1.9 / 1.5 | 88 / 135 / 149 |

- Finding (from the logs): B seed 2 never took off. Its training strict success stayed at 0.03 to 0.05 for updates 9 to 24 and 0.05 for 25 to 48, while B seeds 0 and 1 reached 0.35 and 0.47. Fewer than 1 in 7 groups had any learning signal (active fraction 0.13 versus 0.42 to 0.51), and it kept truncating at the token limit (12.2 per update in updates 9 to 24 versus 3.9 and 1.6 for B seeds 0 and 1).
- It is not a numeric failure: `train_nonfinite_sequences` is 0 in every update, loss scale stayed 16384, no abort.
- Cause: **not confirmed.** Consistent with a run that never left the long-truncated-output regime (the smooth reward gives about 0.05 to 0.15 for truncated or unresolved outputs, so early signal is weak), but one stalled seed cannot separate that from chance. Seed 3 is the test: if it also stalls, it points at the smooth reward early on; if it takes off like seeds 0 and 1, seed 2 was an unlucky start.
- Caveat: training-time strict success is on the training tasks, not the held-out validation score in `results.md`; held-out numbers for seed 2 are 3.82% (B) versus 61.06% (A) as already recorded.
