# Protocol: experiment 18c, token-matched rerun of 18b (does a pre-RL law pick the generated environment that most improves a held-out target, when every run gets the same number of generated tokens?)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_18c/PROTOCOL_18c.md>

**TLDR:** Same 16 Reasoning Gym environments, same Qwen3-1.7B (thinking off), same custom PyTorch/HF GRPO trainer, same hyper-parameters, same held-out target and same six frozen forecasts as 18b (forecast file byte-identical, sha256 `31a533e3...a704ce`). Three changes: (1) every run stops when its cumulative generated response tokens reach **2,000,000** (after at least 10 and at most 1,000 updates) instead of after 40 updates, so the response-length confound of 18b (training response tokens vs gain, Spearman +0.606) is removed by design; (2) **3 seeds** (0, 1 as in 18b, 2 new); (3) the post-evaluation base-model reference is re-measured on the same stack. Frozen 11-25-2026 before any 18c job exists; any change after the first job is a new `expt_18d`.

**Harness and model:** custom PyTorch/HF GRPO (`grpo.py`, `train.py` of `expt_18b`, imported unchanged), Qwen3-1.7B pinned revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, vLLM 0.30.0 evaluation. No agent harness, no model API, no DT label (no spend).

## Why

18b: 16 environments x 2 seeds, 40 updates x 32 prompts x 8 samples = 10,240 rollouts per run (matched rollouts). Realised training response tokens ranged from 84,544 to 7,227,895 per run (`expt_18b/results/supp_18b.md`) and mean response length correlated with gain (Spearman +0.606, `results_18b.md`). So 18b's rho-H law could have been rewarded for tracking response length. 18b's `PROTOCOL_18b.md` rejected exact token matching because an 8-token environment would need hundreds of updates; here that cost is accepted because those updates are cheap (about 1 to 4 s each).

## Frozen design

| item | 18b | 18c |
|---|---|---|
| environments | 16 of `selection_18b.json` (sha256 `3e520e3e...d571`) | same file, unchanged |
| policy, prompt, reward, eval | Qwen3-1.7B, 18a prompt and pass reward, `eval.py` n=8, 256 items x 6 target components | unchanged (`eval.py`, `common18b.py` imported) |
| hyper-parameters | lr 1e-5, warm-up 3, 32 prompts x 8 samples, cap 1024 new tokens, no KL, Dr. GRPO | unchanged (`common18c.HP`, equal to 18b's except `steps`) |
| budget | 40 updates (10,240 rollouts) | **stop after the first update at which cumulative response tokens >= 2,000,000**, with at least **10** and at most **1,000** updates |
| seeds | 0, 1 | 0, 1, **2** (48 runs) |
| item stream | 1,280 item indices per run | up to 32,000 per run; the first 1,280 are exactly 18b's (checked: 32 of 32 sha256 equal 18b's `items_sha256`, `stream_check_18c.json`) |
| base reference | `eval_pre.json` on Sherlock H100 | re-measured on this stack (same code, items, n=8) |

**Token count.** Sum over all 256 rollouts of an update of the response length in tokens (EOS included; a response cut at 1,024 counts 1,024): the same `response_tokens` quantity as 18b's train summaries. Tokens of evaluation are not counted.

**Stopping rule** (`common18c.stop_reason`, tested): after update t (1-based): if t >= 10 and cumulative tokens >= 2,000,000 stop ("budget"); else if t = 1,000 stop ("cap", the run is **budget_limited**); else continue. A run is **matched** when it stopped on budget with tokens < 2,500,000 (one update may overshoot), **overshoot** when it stopped on budget with tokens >= 2,500,000 (only possible through the 10-update floor), **budget_limited** at the cap. Budget_limited and overshoot runs are reported as such, never silently counted as matched; the analysis also reports the fully matched subset.

**Repeat-limited environments.** The 32,000-index stream of `rg/basic_arithmetic/L0` holds only 4,929 distinct questions (all other environments at least 20,625). It is run as specified and flagged `repeat_limited` (threshold 5,000); other environments have no flag. Per-run distinct questions used are recorded.

**Failures.** A run that crashes or finds its GPU busy is re-run once from scratch (same seed). If more than 4 of the 48 runs fail twice, the experiment stops and is reported as incomplete. No other re-runs, no changes to any frozen number after the first job.

## Forecasts (frozen, identical to 18b)

`forecasts_18c.json` is byte-identical to `forecasts_18b.json` (sha256 `31a533e3af16b76260cb8723d70c8e3e18cc27405daadbfe0bc0930f5ca704ce`): primary rho_h (the paper's frozen law), law_alpha, alpha, difficulty, smaller_model, random; secondary rho_only, H_only, pass_band. They are properties of the environments from 18a cells and do not depend on the training budget. The primary question is unchanged: Spearman of rho_h against the 3-seed mean held-out gain over the 16 environments (bootstrap over environments, 10,000 draws, as `expt_18b/analyze.py`, imported unchanged), plus Kendall, top-1 and top-3 regret.

## Added analyses (frozen now; descriptive unless stated)

1. **Token-confound check (the reason for 18c):** Spearman of each environment's mean response length per rollout (3-seed mean) vs its 3-seed mean gain, with bootstrap CI, against 18b's +0.606; also total tokens vs gain.
2. 3-seed reliability: mean pairwise seed-seed Spearman r, Spearman-Brown reliability of the 3-seed mean 3r/(1+2r), max forecast Spearman = its square root (18b: reliability +0.656).
3. Fully matched subset: the frozen analysis on environments whose three runs are all matched (reported only with at least 4 environments).
4. Cross-check: Spearman of 18c env gain vs 18b env gain.
5. Per environment and seed: steps, tokens, stop reason, run class, distinct questions used, gain with item-bootstrap CI.

Outputs and numbers are read from `analyze18c.py` (uses 18b's `analyze.py`) over `results/eval_pre.json`, `results/post/`, `results/train/`.

## Predictions written before any job (11-25-2026, my guesses; scored afterwards)

- **Run length:** environments whose 18b runs generated only about 2,000 to 3,000 tokens per update (basic_arithmetic/L0, family_relationships/L0, letter_counting/L1 and L3, and a seed of family_relationships/L2 and word_sorting/L0) take about 700 to 977 updates; the others stop after about 10 to 45 updates. P(no run reaches the 1,000-update cap) = 80%; P(a run is budget_limited) = 20% (letter_counting needs about 977 updates at its 2,048-token floor).
- **Token confound (primary added claim):** length-vs-gain Spearman falls from +0.606 to **+0.25** (my guess), 70% that it is below +0.45 and 85% that it is below 18b's +0.606.
- **rho_h Spearman: +0.30** (18b +0.476); P(95% CI lower bound > 0) = 30%; P(point estimate > 0) = 75%.
- **H_only Spearman: +0.35**; law_alpha +0.25; alpha, difficulty, smaller_model and random between -0.4 and +0.2.
- **rho_h top-1 regret: 0.25** (18b 0.382; random expected about 0.23): P(better than random expected) = 45%.
- **Mean gain over environments: +0.08** (18b +0.106): long-response environments get fewer updates than in 18b, short ones many more.
- **3-seed reliability:** 0.65; P(>= 0.6) = 60%.
- **Cross-check Spearman of 18c vs 18b env gain: +0.5.**

## Cost and hardware

Estimate 25 to 35 GPU-hours of H200 for 48 runs plus 49 evaluations (18b: 19.4 H100-h for 32 runs, no DT). Free hardware only, no spend: first choice skampere2 H200 GPUs 5, 6, 7 (stack: `rl4cv_e08_v3_gen` venv, same vLLM 0.30.0 / torch 2.13.0+cu130 / transformers 5.18.0 as 18b's Sherlock image), more idle GPUs if free; Sherlock H100 via the 18b package only if skampere2 stops being free. Deviation to note at result time: H200 instead of H100, eval pre re-measured on the same stack; numerical nondeterminism of HF generate and vLLM means 18b's seeds 0 and 1 are not reproduced bit for bit.

## Files

`common18c.py`, `train18c.py`, `analyze18c.py`, `make_tasks18c.py`, `stream_check_18c.py` + `stream_check_18c.json`, `forecasts_18c.json` (+ `.sha256`, `forecast_ledger_18c.jsonl`), `skampere/` (`env.sh`, `pre_eval.sh`, `worker.sh`, `tasks.tsv`), tests in `tests/test_e18c.py`. Results note: `results_18c.md` (written after the runs). The freeze commit contains no result and no job id; the first job id is recorded in `results_18c.md` and must postdate it.
