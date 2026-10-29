# Experiment 18a v2 (wide) results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/results_v2.md>

**TLDR:** All 243 environments (75 families) finished on Qwen3-0.6B and Qwen3-1.7B with none incomplete (about 37 GPU-h on L40S: gen 36.6, embed rerun 0.4). Q2 (primary, size transfer) TRANSFERS: pass-rate Spearman 0.855, family-bootstrap 95% CI [0.787, 0.901]. Q1 (do v1's 8 families stand for the 75) DOES NOT HOLD: checks (a) and (c) fail. `PROTOCOL_v2.md` was frozen on 10-20-2026 in its own commit before any v2 job; the analyses below follow its plan exactly.

Data: `expt_v2_wide/results/summary_18a_v2.json` (analyses 1-7), `envs_18a_v2.jsonl` (243 envs x 2 models), `targets_18a_v2.jsonl`. Per-item scored files (about 0.5 GB) stay on the cluster and in the scratch bundle, not in git.

## Slurm jobs

| cluster | job id | what | state | notes |
|---|---|---|---|---|
| FarmShare | 1862608 | gen array (0.6B and 1.7B shards, one L40S each) | COMPLETED, exit 0 | 10 tasks, 36.6 GPU-h summed from Slurm accounting |
| FarmShare | 1862609 | embed | FAILED | CUDA out of memory in the LM head |
| FarmShare | 1863111 | embed rerun | COMPLETED | fix: take the last position's logits only (the embedding is unchanged); 0.4 GPU-h |
| FarmShare | 1862610 | score | COMPLETED, exit 0 | CPU |
| FarmShare | 1862611 | analyze | COMPLETED, exit 0 | CPU |

## Q2 (primary): does difficulty transfer across model size?

Pass-rate Spearman, Qwen3-0.6B vs Qwen3-1.7B, 243 environments: **rho_s = 0.855**, family-bootstrap 95% CI [0.787, 0.901], environment-bootstrap CI [0.811, 0.891]. Verdict **TRANSFERS** by the frozen thresholds (rho_s >= 0.7 and CI lower bound > 0.5). The forecast was about 0.85.

Robustness:
- Without the 8 low-diversity environments (235 left): 0.850.
- Without the 40 format-dominated cells (203 left): 0.848.
- The 32 v1 environments rerun with new seeds agree with v1: rho_s 0.989 at 0.6B, 0.981 at 1.7B.

By category (rho_s, n envs):
- graphs 0.91 (20)
- games 0.90 (33)
- arithmetic 0.88 (52)
- cognition 0.87 (16)
- algorithmic 0.83 (79)
- algebra 0.58 (15)
- logic 0.23 (12)

## Q1: do v1's 8 families stand for the 75? DOES NOT HOLD

- (a) Same transfer verdict: FAILS. The 8 families alone give rho_s 0.695 (CI [0.05, 0.96], "partial"); the other 67 families give 0.840 ("transfers").
- (b) Monotone share within 0.25: passes.
- (c) Learnable-band share within 0.20: FAILS. 41% (0.6B) and 72% (1.7B) for the 8, against 20% and 27% for the other 67.
- (d) Coordinate signs agree: passes.

The 8 families were not an atypical draw: v1's subset sits at the 12th percentile of 10,000 random 8-family subsets (inside the 5-95% band).

## Other analyses

Within-family monotonicity (difficulty rises with level): 71 of 75 families at 0.6B, 69 of 75 at 1.7B.

Learnable band (0.1 <= pass <= 0.9 and rho > 0): 55 environments (23%) at 0.6B, 80 (33%) at 1.7B, Jaccard 0.55.

Coordinates: pass rate tracks rho (0.94 at 0.6B, 0.89 at 1.7B) and H (0.97, 0.90) closely and target alignment only weakly (0.27, 0.39). Family explains 72% (0.6B) and 67% (1.7B) of pass-rate variance.

Targets, pass rate at 0.6B / 1.7B:
- gsm_symbolic 0.067 / 0.214
- calendar_arithmetic 0.125 / 0.285
- time_intervals 0.109 / 0.248
- syllogism 0.689 / 0.394
- base_conversion 0.035 / 0.304
- GSM8K test256 0.305 / 0.677

## History

Status until 2026-10-28: no measurement yet (jobs submitted from 2026-10-20; table was empty).
