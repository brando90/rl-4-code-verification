# Experiment 20 runbook: does IRT-guided prompt selection raise held-out strict pass@1? (Azalia's test, IRT version)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/expt_v1/cc.md>

**TLDR:** You own rl4cv experiment 20. The question is Azalia's: does a decomposition raise the preferred downstream metric, rather than merely correlate with it? Here that becomes: does an item response theory (IRT) choice of which prompts GRPO (group relative policy optimization) trains on raise held-out validation strict pass@1 at an equal rollout cost? The comparisons are uniform sampling, a scalar pass-rate filter and DAPO-style dynamic sampling, crossed with strict versus smooth (partial-credit) reward. Setup: Qwen3-1.7B Lean SFT start policy, GPUs on Stanford Sherlock through the private runner, $0 API. The run is gated: calibration data, then IRT fit and gate G0, then trainer smoke test, pilot, main runs and evaluation. Every outcome is reported, including NULL.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Your setting

- **Who you are.** A Claude Code worker on SNAP `skampere1`, in tmux session `cc-rl4cv-e20-irt-prompt-selection`. You are the single writer of `experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/` in `brando90/rl-4-code-verification`. The folder already exists on `main` and holds this runbook, a README stub, `CKPT_e20.md` and a `results.md` stub.
- **Read first.** Refresh `~/agents-config` (`git -C ~/agents-config pull --ff-only`) and read `~/agents-config/INDEX_RULES.md` plus the rules it routes for experiments and dispatch (Rules 37, 39, 44, 70 and Hard Rule 11). Then read the repo's `CLAUDE.md` and `experiments/README.md`.
- **Your checkout.** Work in your own clone on SNAP under `/lfs/skampere1/0/brando9/` (for example `rl4cv_e20`). Never use a shared checkout.
- **GPU work runs on Sherlock** through the private runner `sherlockctl`, which needs no Duo prompt.
  - Install the client by following `brando90/sherlock-agent-bridge`'s README; `gh` is already authenticated as `brando90` on `skampere1`.
  - Verify it with `sherlockctl status` and `sherlockctl exec 'hostname; id -un'`.
  - Submit with `sherlockctl submit /abs/path/job.sbatch` (or `sherlockctl exec 'sbatch …'`).
- **Sherlock etiquette (binding).**
  - Wait at least 60 seconds between status checks.
  - Never duplicate a pending job.
  - Do heavy compute only inside `sbatch` jobs.
  - Brando's other jobs share this account and stay untouched: `vb120_*`, `rl4cv-v26*` and `v27*`, `g1s3rg`, `j_*`, and the runner's own `service` job. Never cancel a job you did not submit.
- **Other experiments.** Do not edit any other experiment's folder. Experiments 08 and 13 have live owners (SNAP and Sherlock), and experiment 19 is finished and frozen.
- **Split.** D-013: train 539, validation 135. The test split (222) stays unopened until Brando says otherwise.

## 1. The question

- **Azalia's suggestion** (10-13-2026 meeting; rl4cv decision D-008): a decomposed measurement is useful only if it raises the preferred downstream metric. D-008 operationalizes this as equal-cost decisions guided by the decomposition, compared with decisions guided by scalar feedback.
- **The decision here:** which prompt groups GRPO trains on.
- **The decomposition:** IRT's item difficulty and discrimination, plus the policy's latent ability θ.
- **The scalar alternatives:** the start policy's measured per-task pass rate (static filter, arm S) and DAPO's online all-pass/all-fail filtering (arm E).
- **No guidance:** uniform sampling (arm A).
- **Outcome:** validation strict pass@1 at a matched number of generated rollouts.
- **Brando's smoothness question:** is a smooth partial-credit reward (arms B, D) a substitute for IRT selection, or does it add to it?

## 2. Methods sources (read before designing; cite what you used)

**Textbook:** Truong and Koyejo, *AI Measurement Science* (updated 09-07-2026). Sang Truong confirmed on 10-21-2026 that this is the book he recommends. Chapter HTML is at `https://aimslab.stanford.edu/textbook/src/chapN.html`; the whole book is at `https://aimslab.stanford.edu/textbook/AI-Measurement-Science.pdf`.

| Chapter | What to take from it |
|---|---|
| 3 Models | Rasch, 2PL, 3PL, factor models and amortized prediction for cold-start items: your item model and its task-feature prior |
| 4 Learning | Maximum likelihood, expectation–maximization, Bayesian inference and regularization: marginal maximum a posteriori fits, with priors chosen by grouped cross-validation |
| 6 Efficiency | Fisher information, computerized adaptive testing (CAT) and D-optimal design. Arm C is CAT applied to training prompts: select items by a²p(1−p) at the current ability estimate θ̂, and update θ̂ sequentially |
| 8 Predictability | Multidimensional factor models and parallel analysis: check whether strict and partial-credit responses need separate skills before one θ drives both rewards |
| 9 Intervention | Causal models, distribution shift and counterfactuals. Treat each arm as an intervention; the estimand is the sampler's effect on held-out strict pass@1 at matched cost. Item parameters calibrated on the start policy are a distribution-shift risk once the policy learns, so monitor them |
| 10 Ecosystem | Goodhart's law and gaming: a smooth reward can rise without strict gains, so audit the smooth arms |

**Lectures:** CS321M recordings (`https://aims.stanford.edu/cs321m`). Sang's picks are Lecture 2 (response models: Rasch, 2PL, 3PL, factor models, Bradley–Terry) and Lecture 3 (inference: EM, MLE, Bayesian methods, AUC, ECE). Also use Lecture 4 (cold-start and amortization), Lecture 5 (sample-efficient measurement and active learning) and Discussions 1–3, which have Colab and Drive notebooks.
- You cannot watch video. Read the slide PDFs and notebooks linked from that page where they open.
- In `PROTOCOL.md`, list which sources you actually opened and which method choice each one supports. Never cite a source you could not open.

**Literature and design history:** Brando's design document "IRT for RL on Lean code verification: literature, Experiment 20, ready-to-run prompt" (Google Doc `1Z3sSe9640qzhkux6n9rzWyEuguGQKwUim5MS9qKl4l8`). Sections 4–7 below reproduce its design, so you do not need the document if you cannot open it.
- Cite in README: Truong et al., ICML 2025 (arXiv 2503.13335); Item Response Scaling Laws (2606.07616); Lalor and Yu, DDaCLAE (2011.00080); Foster and Foerster (2502.12272); Bae et al. (2504.03380); DAPO (2503.14476); AdaRFT (2504.05520); CDAS (2505.17652); ThinkPrior (2609.09075).

## 3. Binding design inputs from experiment 19 (done 10-21-2026, `experiments/19_*/results.md`)

1. **A scalar baseline is strong; task content is stronger.** Panel IRT from 11 VeriBench systems, with no start-policy data, ranks a 4B start policy's mixed strict groups at AUC 0.862, but the scalar panel pass rate scores 0.852 and task-content features alone 0.954.
   - So in experiment 20 the start policy's own Phase 0 responses are a respondent, task features enter as an explanatory (amortized) prior, and arm S is the scalar comparison that matters.
2. **Ranking was good; level was not.** Mean predicted mixed share was 0.48 against 0.24 observed, because predicted per-task success rates were too tightly spread.
   - So gate G0 reports calibration (expected calibration error, ECE, and predicted against observed active share) besides AUC. Arm C's weights a²p(1−p) depend on the level of p.
3. **Few respondents need strong regularization, chosen by data.** With about 11–16 respondents per item, weak priors overfit. Grouped cell-level cross-validation inside train chose strong shrinkage: slope SD 0.25, at the edge of its grid.
   - So choose priors by grouped cross-validation inside train with a wider grid (slope SD down to 0.1), and report the 1PL too.
4. **Check the integration numerically.** A two-skill model on a coarse product grid failed its check-grid gate.
   - So any multidimensional model needs a convergence gate on a finer check grid before use. Reuse experiment 19's `irt_e19.py` grids and gates.
5. **Hash convention for frozen forecasts.** `rl4cv.forecast.freeze_forecast` hashes the canonical JSON without its final newline, so verify with `verify_forecast`, not a plain `sha256sum`.
6. **The decomposition did not beat a simple model.** Across systems, IRT added nothing over a simple additive model for held-out strict prediction.
   - So hypothesis H3 (C against S) is the real test of whether the decomposition is needed. A NULL there is a result.
7. **Reusable code:** experiment 19's `expt_v1/irt_e19.py` (random-intercept and explanatory 2PL, grids, gates), `features_e19.py` (train and validation task features, hash-checked) and `data_e19.py` (panel loader with test-split guards).

## 4. Hypotheses (freeze in `PROTOCOL.md` before any training)

- **H1, primary (Azalia's test).** C minus A is at least +1.5 points of validation strict pass@1 at update 48, with a 95% paired task-bootstrap interval above 0, pooled over 2 seeds. Threshold source: Brando's design document; seed spread on this pipeline is 0.56 points (experiment 08 v16).
- **H3, key secondary (is the decomposition needed beyond a scalar?).** C minus S and C minus E, at matched generated rollouts, with intervals. If C ≈ S, the value is in measuring pass rates, not in IRT.
- **H2, mechanism.** C has a higher active-group fraction than A, S and E. Online, the IRT forecast 1 − p⁸ − (1 − p)⁸ predicts active groups with AUC ≥ 0.70 (experiment 13's gate F2).
- **H4, smooth reward × IRT.** The interaction (D − B) − (C − A), with an interval. Negative means the two are substitutes; about zero means they add.
- **Pre-registered descriptive checks:**
  - θ̂ against measured validation pass rate at updates 0, 16, 32 and 48: does IRT track learning?
  - Per-update calibration of the C forecast (ECE): distribution shift of the frozen item parameters.
  - A Goodhart audit of B and D: does the smooth reward rise while mean theorem count, compile rate or strict rate falls?

## 5. Arms (one trainer, config, seed set and rollout budget; only the sampler and reward differ)

| Arm | Prompt sampler | Reward |
|---|---|---|
| A | uniform without replacement over the 539 train tasks | strict |
| S | uniform over train tasks the start policy solved 1–7 of 8 times in Phase 0 (static, no IRT) | strict |
| E | DAPO dynamic sampling: oversample, drop all-0 and all-1 groups, refill. Every generated rollout counts against E's budget | strict |
| C | IRT-online: 75% of groups drawn in proportion to a_j²·p_j(1−p_j) at the current θ̂, 25% uniform for exploration | strict |
| B | uniform, the same prompt stream as A | smooth: experiment 13's `factored_reward` (`src/rl4cv/e13.py`, unchanged) |
| D | IRT-online as in C | smooth, as in B |

- **Arm C's ability update.** p_j = σ(a_j θ̂ + d_j), with item parameters frozen after Phase 0.
  - After each update, θ̂ is the expected a posteriori (EAP) estimate. The prior is N(θ̂ from the previous update, 1), updated with that update's 128 strict outcomes: a CAT-style sequential update (chapter 6).
  - Log θ̂ and its posterior SD at every update.
- **Rollout budget:** 48 updates × 16 groups × G = 8, so 6,144 rollouts per run. Arm E stops when its generated rollouts reach 6,144.
- **Recipe:**
  - AdamW at learning rate 1e-6; clipping 0.2 below and 0.28 above; KL coefficient 0; token-normalized loss.
  - The frozen v12 sampler: temperature 0.6, top-p 0.95, top-k 20, 12,288 new tokens, thinking on.
  - vLLM→trainer importance-sampling correction capped at 2.
  - Seeds: 2 per arm. A and B share one prompt stream per seed.

## 6. Phases and gates (stop at a failed gate, write the NULL honestly, email, never redesign silently)

1. **Setup.**
   - Create branch `e20-irt-prompt-selection` from `origin/main`.
   - Fill in `README.md` (design and status), `PROTOCOL.md` (draft), `results.md` (live, per Rule 37) and `CKPT_e20.md` (Rule 44: stamps, six headings, log).
   - Every document starts with `# Title`, a `**Doc link:**` line and a `**TLDR:**`.
2. **Phase 0a, calibration data (Sherlock, about 6.5 GPU-h).**
   - Generate the 539 train tasks × 8 samples for the start policy: Qwen3-1.7B-Base Lean SFT, experiment 08 v4 seed 20260831, weights at `$SCRATCH/rl4cv_sherlock/expt_v4/runs/20260831/hf`. Use the frozen v12 sampler, seed 91.
   - Reuse `$SCRATCH/rl4cv_sherlock/v4_validation/rl4cv_gen`: `prep_pack.sh` (build a train pack the way the validation pack was built), `gen.sh`, `full.sbatch` and the vllm 0.30 Apptainer image, with `-C 'GPU_SKU:L40S|GPU_SKU:H100_SXM5'`.
   - Score with `$SCRATCH/rl4cv_sherlock/grading/score_sherlock.sh` (scorer pinned at 59059a2, `--skip-tc`) as normal-partition CPU arrays (`-c 1 --mem 16G`), never on the dev partition.
   - Repo decision D-109 applies to every scoring launch here, including the reward calls during training. Retain raw Lean compiler and kernel stdout/stderr, partial timeout output, source and compiler identity, and exit status outside disposable directories. If `score_sherlock.sh` does not do this, add the logging wrapper from `experiments/08_*/expt_v24/future_logging/` before the first measured launch.
   - The prompt pool is the D-013 train split only, with no external data.
   - Record per cell: strict, `factored_reward`, the SCSC factors, generated tokens and the token-cap flag. Commit the per-cell table: train-split results tables go in git under Rule 39.
3. **Phase 0b, IRT fit (CPU).**
   - **Respondents:** the start policy (binomial k of 8 on 539 tasks) and experiment 12's 11 systems (`experiments/12_*/expt_v1/results/input_manifest.json`: strict on train tasks; `zero_without_call` cells missing).
   - Experiment 05's Base models (`per_task_*_g8.csv`) are near zero everywhere. Include them only if they change the fit, and report either way.
   - **Item models:** random-intercept and explanatory binomial 2PL, by marginal MAP on a 1,201-node grid with a check grid (reuse `irt_e19.py`). The explanatory prior uses experiment 19's train-task features. Choose priors by grouped 5-fold cell-level cross-validation inside train (folds by D-013 `group_id`). Report the 1PL.
   - **For the smooth reward:** a graded-response or Beta-IRT fit on `factored_reward`, following Item Response Scaling Laws. Point masses at 0 and 1 favour the graded model, as experiments 14 and 19 found.
   - **Dimensionality (chapter 8):** do strict and partial credit share one θ? Use held-out likelihood, under a convergence gate.
4. **Gate G0 (pre-registered).** On 5 grouped folds over train tasks, with the start policy's cells held out by task group, the selected model must:
   - predict the start policy's held-out active groups (1–7 of 8) with AUC ≥ 0.70;
   - beat the population Beta(1,1) pass rate on log loss.
   Report beside it, without gating on them: ECE, predicted against observed active share, and the panel pass-rate and features-only alternatives.
   - **If G0 fails:** drop arms C and D, run A, S, E and B, and record IRT selection as NULL.
   - **Before training:** freeze item parameters and forecasts with `rl4cv.forecast.freeze_forecast` and write `input_pins_e20.json`.
5. **Trainer and smoke test.**
   - Use the Hugging Face TRL `GRPOTrainer` with vLLM colocated, inside the vllm 0.30 Apptainer image (venv or overlay for `trl`), with pinned versions.
   - Implement the sampler as pluggable classes (`Uniform`, `StaticFilter`, `DynamicDAPO`, `IRTOnline`), with unit tests in `tests/test_e20_*.py`. `make test` must pass before every push.
   - The reward calls the pinned Lean grader. Batch rollout scoring in parallel Lean processes on the node, or on a CPU array between updates; measure which is faster in the smoke test.
   - **Smoke:** 2 updates of arm A plus a log-probability mismatch check. Stop if more than 1% of tokens have |Δlog p| > 0.05; that was experiment 09's failure.
   - If TRL cannot run cleanly on Sherlock (glibc 2.17, no Docker), port experiment 13's NeMo RL backend into the image and record the choice in `PROTOCOL.md`.
6. **Pilot:** A, C and S, seed 1, 16 updates each, about 10 GPU-h.
   - Stop and report if A already has at least 50% active groups (selection has nothing to fix), or if C's active-group fraction is below 1.5× A's.
   - Otherwise lock `PROTOCOL.md`: commit it and record the hash.
7. **Main:** 6 arms × 2 seeds × 48 updates, about 105 GPU-h.
   - Submit as Slurm arrays, resumable from checkpoints saved at updates 16, 32 and 48.
   - Use `--mail-type=END,FAIL --mail-user=brando.science@gmail.com`.
8. **Evaluation.**
   - Validation 135 × 8 with the frozen v12 evaluation at updates 0 and 48 for every run, and at 16 and 32 where budget allows.
   - Test stays unopened. A single test pass of each arm's update-48 checkpoint happens only after Brando says so.

**Budget caps (binding; from Brando's estimate of 140–190 GPU-h):**
- Phase 0: 10 GPU-h; pilot: 15 GPU-h; main: 130 GPU-h; evaluation: 80 GPU-h.
- Total: 200 GPU-h and $0 of API spend. Use open-weight models only and no provider or Vals keys.
- If a cap would be exceeded, stop at the phase boundary and report.

## 7. Statistics and reporting (Hard Rule 11; `~/agents-config/workflows/statistics-reporting.md`)

- **Intervals and tests.** Every headline is reported as x [lo, hi] p-val=Z. Intervals come from paired task bootstraps: 10,000 draws over validation task groups, with seeds kept paired. A two-sided test of a zero difference (bootstrap or paired-seed sign-swap) supplies the p-value.
- **Per arm:** pass@1 and pass@8, active-group fraction per update, generated tokens per active group, GPU-h, and θ̂ against measured pass rate.
- **Thresholds** are named with their source: Brando's design document, experiment 13's F2, or agent-suggested.
- **Missing cells** stay in the denominator and are listed.
- **Copy-ready status sentence.** `results.md` opens with one, then at most 5 numbered findings, one next step and the live phase table. It closes with `**TLDR-end:**` tagged `[rl4cv: expt20 IRT prompt selection for GRPO]`.

## 8. Records, git and notifications

- **Commits.**
  - Commit and push to your branch after every landed step, staging explicit pathspecs only, never `git add -A`.
  - Open one PR into `main` for review. Brando's design asks for a PR, so do not merge it yourself.
  - Keep `CKPT_e20.md` current on every event: a run starts or ends, a number moves, something blocks, or the session ends.
- **Run emails (agents-config Rule 70).** Send `[RUN START] rl4cv expt20 <phase>` when each GPU phase launches, and `[RUN DONE] rl4cv expt20 <phase>: <status>` when it ends.
  - Address them To `brando.science@gmail.com`, with BCC `brando.science@gmail.com,brando9@stanford.edu,brandojazz@gmail.com,brando@vals.ai`.
  - Use `uutils.emailing.send_email_smtp` as the rule describes.
  - Before Phase 0, search that inbox (or ask the coordinator) for other agents' `[RUN START]` emails for this repo, so work is not duplicated.
- **At the end:**
  - an `experiments/README.md` row;
  - plots in `expt_v1/results/`: learning curves, active-group fraction and the H4 2×2;
  - a one-bullet entry for Brando's "Experiment log (all projects)" Google Doc under "RL for code verification", tagged `Paper: rl4cv` with the verdict WORKED, NULL or FAILED. If you lack Google Docs access, put the bullet in `results.md` and the DONE email, and say so.

## 9. Blockers and honesty

- **Real blockers:** a credential that is missing or expired (for example, the runner is offline), an exhausted budget cap, or a failed gate. Record each in `CKPT_e20.md` with its exact evidence, email once, and stop at that boundary. Never redesign silently or weaken a gate.
- **Infrastructure failures:** retry the identical job up to 3 times. Never resample or drop a cell because of its score.
- **Silence about cost is not success.** Report GPU-h used against each cap at every phase boundary.

**TL;DR:** Calibrate the 1.7B start policy on 539 train tasks × 8. Fit a regularized, feature-informed 2PL and pass gate G0. Then test whether IRT-online prompt selection (C) beats uniform (A), a pass-rate filter (S) and DAPO (E) on validation strict pass@1 at matched rollouts, crossed with strict versus smooth reward (B, D). Run on Sherlock within 200 GPU-h at $0, with gates at every phase and honest NULLs.
