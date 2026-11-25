# Experiment 25 results: smooth (B) versus strict (A) reward, GRPO on Qwen3-1.7B Lean SFT (AT-1788, 11-10-2026; third seed AT-2925, 11-11-2026)

**UPDATE 11-11-2026 (AT-2925, third seed per arm): the 2-seed +4.25 does not hold.** Seed 2 gave A 61.06% (2638/4320) and **B 3.82% (165/4320)**. Pooled over 3 seeds per arm (same analysis script, `--seeds 0,1,2`, task-group bootstrap, 10,000 draws, seed 20261021): A 50.89% [43.55, 57.84], B 34.64% [28.99, 40.15], **B minus A -16.25 points [-19.17, -13.28]**. The pre-registered rule (B minus A at least +1.5, lower bound above 0) is **not met** on 3 seeds. That interval holds the six trained models fixed and resamples only tasks, so it is not a seed-level test. At the run level the seed-paired B minus A is +12.5, -4.0, -57.2 points, and an exact 3-vs-3 permutation over the six run means gives p=0.50 (10 of 20 splits at least as extreme): the data cannot separate the arms, and the right reading is "no reliable difference, B has a failure mode". B s2 never learned: its training strict successes per 128 rollouts went 5.3 (first 6 updates) -> 6.8 (last 6), against 44 to 73 (last 6 updates) for the other five runs, and its validation pass@1 stayed at the start level (4.44% u16, 6.39% u32, 3.82% u48 vs 4.26% at update 0). Its outputs are valid files (finish_reason stop 99.1%, only 54 of 4320 without a Lean block, compile rate 3.84%), so this is a stalled run, not a broken evaluation. Not known: why seed 2 of B stalled (it was resumed from the update-8 state after a skampere1 reboot at about 21:27 on 11-10, like A s2 which did not stall; no check of the resume path was run). Harness: `train_e25.py` (fp16, vLLM sampling) plus the local frozen strict scorer, Qwen3-1.7B Lean SFT step_658, A100 on skampere1, no DT, no paid API. Third-seed files: `expt_v1/results/full_run_at2925/`. The text below is the 2-seed AT-1788 report, kept unchanged for the record; its TLDR is superseded by this paragraph.

| 3 seeds per arm, update 48 (32 samples, 4,320 cells per run) | seed 0 | seed 1 | seed 2 | pooled (task-group bootstrap) |
|---|---|---|---|---|
| A strict reward | 37.34% | 54.26% | 61.06% | 50.89 [43.55, 57.84] |
| B smooth reward | 49.86% | 50.23% | 3.82% | 34.64 [28.99, 40.14] |
| B minus A | +12.52 | -4.03 | -57.25 | -16.25 [-19.17, -13.28] |

Pooled, 3 seeds, by update: u16 (8 samples) A 11.94, B 9.72, B minus A -2.22 [-3.74, -0.73]; u32 (8 samples) A 29.20, B 28.67, B minus A -0.52 [-3.48, 2.38]. Seed-2 evaluations: A s2 u16 94/1080 (8.70%), u32 496/1080 (45.93%), u48 2638/4320 (61.06%); B s2 u16 48/1080 (4.44%), u32 69/1080 (6.39%), u48 165/4320 (3.82%). Third-seed compile rate is almost equal to the strict rate in both arms (QA 11-25-2026: A 2646/4320 = 61.25% compile vs 2638/4320 = 61.06% strict; B 166/4320 = 3.84% vs 165/4320 = 3.82%) (A s2 61.25%, B s2 3.84%); stated theorems per cell at 48: A s2 1.38, B s2 5.57 (start 9.16, B s0/s1 about 3.9 and 3.0). Goodhart audit pooled over 3 seeds, B minus A at 48: compile rate -16.3 points, stated theorems +1.33 per cell, honest theorems -0.10 per cell, truncated -0.7 points; the smooth training reward of B s2 rose only from 0.082 to 0.158 (first 6 -> last 6 updates), so this is a failure to learn, not reward gaming. A third seed per arm was the planned fix ("A third seed ... is the direct fix"); it changed the conclusion.

Deviations for the third seed: (1) skampere1 rebooted at about 21:27 on 11-10 and killed both seed-2 lanes (A at update 15, B at update 9); both resumed from `state_latest` (update 8) in job `full_run5.sh` (relaunch kept in `full/*.attempts`); a resumed lane does not replay the exact random stream. (2) The first job hit its 12 h cap and killed the B s2 u48 evaluation during scoring; it was rerun from the existing generations (generation 1 s on rerun) and scored fully (4,320 of 4,320 cells). (3) B s2 u32 evaluation first failed at vLLM startup (GPU busy), rerun later and scored (1,080 cells). (4) Seed 2 ran on GPUs 0 to 3 of skampere1 (GPUs 6 and 7 untouched); outputs are on `/dfs/scratch1/brando9/at2925` because `/lfs` was full; raw rollouts and checkpoints stay there. (5) `analyze_e25.py` got a `--seeds` option (default 0,1 reproduces the earlier output); agreement of the local scorer with saved scores was not re-run. (6) Training time of the seed-2 lanes was not summed into the A100-hour cap; the earlier total was 41.7 of 75 A100-h.

---

**TLDR:** Both arms improved a lot on held-out validation strict pass@1 (start 4.26% -> 45.8% A, 50.1% B at update 48). Pooled over 2 seeds, B minus A is **+4.25 points, 95% interval [+1.05, +7.78], p=0.0076** (paired task-group bootstrap, 10,000 draws, seed 20261021). That meets the pre-registered rule (at least +1.5 with lower bound above 0), so **H1 is supported by the pre-registered statistic**. It rests on 2 seeds per arm: A's seeds differ by 16.9 points (37.3 and 54.3), B's by 0.4 (49.9 and 50.2), seed-paired B minus A is +12.5 and -4.0, and an exact permutation test over the 4 runs cannot go below p=1.0 for this split pattern. The bootstrap resamples tasks only, so it does not contain seed variance. Treat as supported by the registered test, not as settled. Harness: `train_e25.py` (fp16, fp32 master weights, loss scale 16384, vLLM sampling) plus the local frozen strict scorer, Qwen3-1.7B Lean SFT step_658, A100 on skampere1. No DT.

Pre-registration: PROTOCOL.md (locked 11-09, section 10), forecast `expt_v1/forecasts/e25_forecast.json` (P supported 25%, both flat 55%, A better 20%). The event "supported" happened; the arms did not stay flat (both gained about +41 to +46 points over the start checkpoint, which the "flat" forecast did not cover as written).

## What ran
- 4 lanes (arm A strict reward, arm B smooth reward) x seeds 0 and 1, 48 updates each, lr 5e-6, 16 groups x 8 rollouts, 12,288 tokens, `--save-at 16,32,48`. All four reached update 48 (`RUN_DONE`), no `ABORT.json`, no non-finite value, in-loop mismatch gate at most 0.14% on any update (limit 1%).
- Training A100 time from state files: A s0 8.57 h, A s1 10.72 h, B s0 13.27 h, B s1 9.17 h = 41.7 A100-h (cap 75, section 7); evaluation generation 5.2 A100-h (cap 25; scoring is CPU). Excludes updates lost to crashes and re-done.
- Validation evaluation: frozen v12 sampler seed 91, 135 validation tasks; 32 samples at update 48 (4,320 cells per run), 8 samples at 16 and 32 (1,080 cells). Test split sealed and not scored. Training prompts were checked from `rollouts.jsonl`: every rollout of every lane is a train-split task (539 of 539 used, 0 validation, 0 test).
- Update-0 baseline: fresh fp16 generation of step_658, 46/1080 strict (4.26%), 8 samples (the saved-score replay is 53/1080).

## Primary result (strict pass@1 on validation, points; paired task-group bootstrap, 135 tasks in the groups of the D-013 manifest)
| update | A (strict reward) | B (smooth reward) | B minus A |
|---|---|---|---|
| 0 (8 samples) | 4.26 | 4.26 | 0 |
| 16 (8 samples) | 13.56 [9.09, 18.17] | 12.36 [8.43, 16.47] | -1.20 [-2.77, 0.38] |
| 32 (8 samples) | 20.83 [15.24, 26.71] | 39.81 [32.95, 46.70] | +18.98 [14.48, 23.76] |
| **48 (32 samples)** | **45.80 [38.52, 52.85]** | **50.05 [42.03, 57.95]** | **+4.25 [1.05, 7.78], p=0.0076** |

Gain over update 0 at 48: A +41.54 [35.20, 47.70], B +45.79 [38.68, 52.84].

## Per run (strict successes / cells; pass@1; tasks with at least one pass)
| run | u16 (8 samp) | u32 (8 samp) | u48 (32 samp) | tasks pass any at 48 |
|---|---|---|---|---|
| A s0 | 176/1080 = 16.30% | 259/1080 = 23.98% | 1613/4320 = 37.34% | 89 |
| A s1 | 117/1080 = 10.83% | 191/1080 = 17.69% | 2344/4320 = 54.26% | 110 |
| B s0 | 138/1080 = 12.78% | 338/1080 = 31.30% | 2154/4320 = 49.86% | 99 |
| B s1 | 129/1080 = 11.94% | 522/1080 = 48.33% | 2170/4320 = 50.23% | 100 |
Per-task pooled table: `expt_v1/results/full_run_at1788/per_task_u48.csv`.

## Why this is fragile (read before using the +4.25)
- Two seeds per arm. Seed-paired B minus A at 48: seed 0 +12.52, seed 1 -4.03. A's seed spread (16.9 points) is larger than the effect. B's two seeds agree closely (49.9, 50.2).
- The bootstrap resamples the 135 validation tasks (in groups) and holds the four trained models fixed. It shows the effect is not an artifact of which tasks were drawn; it does not say a new pair of seeds would agree. The exact 2-vs-2 permutation over the four run means gives p=1.0 (all 6 splits have a difference at least as large), so the run-level data cannot separate the arms.
- A third seed per arm (allowed by the protocol if caps allow; 41.7 of 75 A100-h used) is the direct fix. Not run.

## Goodhart audit (PROTOCOL section 6: smooth up while strict, compile rate or theorem count down is reported as gaming)
Validation, update 48, B minus A (task-group bootstrap, per-cell means): compile rate +4.2 points [+1.1, +7.8]; stated theorems per cell -0.09 [-0.17, -0.03]; honest (kernel-checked) theorems per cell +0.18 [+0.07, +0.30]; truncated outputs -1.2 points [-1.9, -0.6]. So B does not trade strict, compile rate or honest-theorem count against smooth reward relative to A.
Against update 0 (both arms): stated theorems per cell fell from 9.16 to about 3 to 4 (A -5.61 [-6.23, -5.02], B -5.71 [-6.30, -5.14]); honest theorems per cell rose (A +1.26, B +1.44); truncated outputs fell from 18.1% to 0.2% to 2.5%; compile rate rose from 4.3% to 37% to 54%. By the letter of the rule ("theorem count down") the stated-theorem drop fires, but it is the same in both arms, including the strict-reward arm, so it is a property of this training recipe and not of the smooth reward. Whether the shorter files also state fewer of the gold's obligations is not measured here (a statement-coverage check was not run).
Not measurable: the scorer's `S_tilde` is 0 on every cell under `--skip-tc`, so validation smooth SCSC was not computed. Training-time smooth reward of arm B (its own training metric) rose from about 0.05 to 0.15 in the first updates to 0.50 and 0.53 (last 6 updates mean, seeds 1 and 0).
In every run the compile rate equals the strict pass rate to within 0.6 point (nearly every compiling file counts as strict), so compile rate carries almost no information beyond strict here.
Training strict successes per 128 rollouts (mean of first 6 updates -> last 6; train prompts): A s0 14.3 -> 44.5, A s1 6.2 -> 64.8, B s0 7.5 -> 63.0, B s1 7.0 -> 58.7.

## Deviations and facts to know (none silent)
1. Crashes from another user's GPU use (out-of-memory) killed lane processes several times; lanes resumed from `state_latest` (full state every 8 updates) in jobs `full_run.sh` to `full_run4.sh` (all kept). B s0 was the slow lane: 8 out-of-memory crashes on GPU 3 on 11-10 00:34, moved to GPU 7. `rollouts.jsonl` therefore holds repeated updates (6,528, 6,400, 7,552, 6,912 rows against 6,144 expected); `log.jsonl` was reduced to the last entry per update for the curves. A resumed lane does not replay the exact random stream of an uninterrupted one.
2. B s0 update-48 evaluation: sample 31 failed scoring when `/tmp` on skampere1 ran out of space (exit 1, kept as `B_s0_u048_s31_failed_enospc_stdout.log`); the same job dir was rescored with the same scorer after space was free; the table uses 32 of 32 samples (4,320 cells; 2,154 successes). Before the rescore the 31-sample result was 2,088/4,185 = 49.89%.
3. The analysis script `expt_v1/code/analyze_e25.py` was written after the per-run pass rates in the evaluation summaries had been seen and before the pooled statistics were computed; the statistic is the protocol's (seeds pooled, task-group bootstrap, 10,000 draws, seed 20261021). It is not in the section 9 freeze list.
4. Update 16 and 32 numbers are 8 samples per run; update-0 is 8 samples of one fresh generation, so baseline noise (46 against 53 of 1,080) is not in any interval.
5. Evaluation checkpoints were generated in fp16 with vLLM; nothing is compared with bf16 evaluation.
6. No test-split pass, no paid API, no Duo. Disk: `/lfs/skampere1/0` stayed near 100% full (shared); checkpoints on `/dfs/scratch1/brando9/at1788_ckpt/`.
7. Agreement of the local scorer with saved scores was verified at stages 1 and 2 (53/1080) and not re-run for these evaluations.

## Files
`expt_v1/results/full_run_at1788/`: `analysis_e25.json` (all intervals and run summaries), `per_task_u48.csv`, `evals/summary_eval_*.json` (12 evaluations), `full/<lane>/log.jsonl`, `gate_report.json`, run manifests, launch scripts, rescore logs. Raw rollouts (4.8 GB) and checkpoints stay on skampere1 (`/lfs/skampere1/0/brando9/at1788/evals`, `/dfs/scratch1/brando9/at1788_ckpt`).
