# Experiment 25 PROTOCOL (DRAFT, NOT LOCKED; lock only after the freeze list below is complete)

**TLDR:** Smooth reward (arm B) versus strict reward (arm A), GRPO on Qwen3-1.7B Lean SFT (Experiment 08 v1 step_658), D-013 split of `veribench@1.3`, primary metric validation strict pass@1 at update 48, B minus A. This draft applies all 13 fixes from [QA_plan1_10-28-2026.md](QA_plan1_10-28-2026.md). Status 10-28-2026: no training run started; stages 0 and 1 are building blocks, not experiment runs.

## 1. Question and hypothesis
Does GRPO with the smooth reward (Experiment 13's factored reward, a training proxy for SCSC, not official SCSC) yield higher held-out strict pass@1 than GRPO with the strict reward at equal rollouts? H1: B minus A at least +1.5 points (supported only if the paired-bootstrap lower bound is above 0). Minimum detectable effect is about 2 points (QA item 5): a result between 0 and 2 points is reported as inconclusive, not as support or refutation. Secondary measures are descriptive; no claim rests on them.

## 2. Data and policy
Benchmark: public `veribench@1.3` (Harbor registry, 896 tasks); pins `c11b99ba` (task packs), `59059a20` (frozen scorer, `--skip-tc`). Split D-013 (manifest SHA-256 `157ce781...`): train 539, validation 135, test 222 sealed (loaders drop test ids; one test pass only on Brando's word). Start policy: Experiment 08 v1 `step_658` (validation strict 4.91% = 53/1080), weights SHA recorded. The Phase 0 numbers (strict 4.43%, 13.7% mixed groups) were measured on the Sherlock v4 replicate, not this checkpoint; the pilot re-measures them on step_658.

## 3. Arms and recipe
Arm A strict reward; arm B smooth reward (adapter `partial_credit_e20.py`, unresolved reward = 0). Same prompt stream and seeds in both arms. 16 groups x 8 rollouts per update, 12,288 new tokens, T 0.6, top-p 0.95, top-k 20, AdamW wd 0, grad clip 1.0, clipped surrogate eps 0.2/0.28, truncated importance sampling cap 2.0 ON in both arms and both dtypes. 48 updates, 2 seeds per arm (third seed if the budget caps allow). Log per arm: strict curve (adapter strict in B), trained_sequences, grad_norm, IS min/max, mismatch share.

## 4. Precision
bf16 is expected to fail (6.1% to 6.4% mismatch measured, Exps 21 and 22). Decision rule: measure the mismatch gate inside the trainer loop on the GPU that trains, at the chosen lr; bf16 if at most 1% on every update of the smoke and pilot, else fp16 with fp32 master weights and static loss scale 16384 (Exp 24). Per-update abort above 1% mismatch or on any non-finite value (every update computes the mismatch; no `--smoke` shortcut).

## 5. Learning rate pilot (training reward only; validation not read)
Arms A and B, lr in {1e-6, 5e-6}, 12 updates each (4 runs). Rule: choose the largest lr at which both arms pass the gate and finiteness and neither arm's strict training reward falls (mean strict successes per 128 over updates 7 to 12 minus updates 1 to 6 not below 0); ties go to 1e-6. "Moves" means that same difference at least +2 points of successes per 128. If neither arm moves at either lr, stop and report the null power result (no 48-update run).

## 6. Evaluation
Update-0 validation of step_658 through the new pipeline must reproduce 53/1080 before any trained checkpoint is scored. Primary: validation strict pass@1 at update 48, 135 tasks x 32 samples; paired bootstrap over task groups (10,000 draws, seed 20261021), seeds pooled. Updates 16 and 32 at 8 samples. Goodhart audit: smooth up while strict, compile rate or theorem count down is reported as gaming.

## 7. Stages, caps and stop rules
0. Local scorer (AT-1786) with agreement check on SNAP-resident scored files (Exp 13 T2 attempt_3 cells or Exp 08 validation `raw.jsonl` plus `per_task.csv`). 1. Code to land and test: fp16 flags plus real reward in one trainer, local evaluation driver, CPU gradient accumulation, vLLM memory about 0.5 on A4000; A4000 memory and seconds per update. 2. Two-update smoke, both arms. 3. Pilot (section 5). 4. Full run.
GPU-hour caps (A100-equivalent, stop at cap and ask Brando): stage 1 and 2 at most 8; pilot at most 15; full run at most 75; evaluations at most 25. Disk about 20 GB per run (optimizer state): check free space first. Stop rules: mismatch above 1%, any NaN or inf, pilot reward not moving, strict disagreement with saved scores, another user needing the GPU. Release idle GPUs after each stage. Hardware: mercury1 and mercury2 (A4000 16 GB) and skampere1 A100 80 GB when idle; free only, no paid API, no Duo.

## 8. Forecast (to be frozen with `rl4cv.forecast.freeze_forecast` before any outcome, D-004)
P(B minus A at least +1.5 with lower bound above 0) 25%; both arms flat within noise 55%; A better than B 20%. Null results are reported like any other.

## 9. Freeze list (all frozen and committed before stage 4)
This PROTOCOL (hypothesis, threshold, statistics, lr, dtype with the measured gate value, loss scale, unresolved reward = 0 rule); forecast JSON; pins (checkpoint SHA, pack manifest `157ce781`, scorer `59059a20`, task packs `c11b99ba`, `veribench@1.3`, Lean 4.22 and Mathlib commit, venv `pip freeze`, code commit); evaluation sampler (v12, seed 91); bootstrap seed 20261021; test-seal mechanism.
