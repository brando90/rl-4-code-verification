# Experiment 20 protocol: IRT ability-matched prompt selection for GRPO on Lean, strict vs smooth reward (LOCKED before any training)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/PROTOCOL.md>

**Status:** DRAFT, written 10-21-2026 11:50 PDT before any Phase 0 outcome was read. Hypotheses H1–H4, gate G0, the IRT model family and the statistics (sections 1, 3, 4, 7) are frozen at this draft; they do not change after Phase 0 data are read. The pilot may only confirm operational parameters (per-update wall time, memory settings) that are marked "operational" below. After the pilot the file is LOCKED by commit and its hash is recorded in `results.md`. Deviations found later are documented in `results.md` under "Deviations", never by editing this file; a numbered amendment file may add analyses before the data they touch exist.

This file freezes the protocol before any GPU-budget-spending training run begins. It is written prior to seeing any experiment 20 result. Any deviation observed during execution is documented in `results.md` → "Deviations and open questions for Brando", not by editing this file.

**TLDR:** Azalia's test with IRT as the decomposition: does an item response theory (IRT) choice of which prompts GRPO (group relative policy optimization) trains on raise held-out validation strict pass@1 at an equal rollout budget, compared with uniform sampling (A), a scalar pass-rate filter (S) and DAPO dynamic sampling (E), and does a smooth partial-credit reward (B, D) substitute for or add to it? Start policy: Qwen3-1.7B-Base Lean SFT (experiment 08 v4, seed 20260831). Gated: Phase 0 calibration (539 train tasks × 8), IRT fit and gate G0, smoke test, pilot, main runs (6 arms × 2 seeds × 48 updates × 128 rollouts), validation evaluation. Compute: Sherlock GPUs, 200 GPU-h cap, $0 API.

Terms: **strict** = `kernel_binary` (the Lean file typechecks, states at least one `example` and at least one theorem, and the kernel accepts every stated theorem with axioms within {`propext`, `Classical.choice`, `Quot.sound`}); **active group** = a GRPO group of G = 8 rollouts on one prompt with 1–7 strict successes (only these carry gradient); **2PL** = two-parameter logistic item model P(success | θ) = σ(a_j θ + d_j) with discrimination a_j, intercept d_j (difficulty −d_j/a_j) and ability θ; **EAP** = expected a posteriori; **ECE** = expected calibration error; **AUC** = area under the ROC curve.

## Scientific question (locked)

**Question (Azalia Mirhoseini, 10-13-2026 meeting; rl4cv decision D-008).** A decomposed measurement is useful only if it raises the preferred downstream metric. Here the decision is which prompt groups GRPO trains on; the decomposition is IRT's item difficulty and discrimination plus the policy's latent ability θ; the scalar alternatives are the start policy's measured per-task pass rate (arm S) and DAPO's online all-pass/all-fail filtering (arm E); the no-guidance control is uniform sampling (arm A). The outcome is D-013 validation strict pass@1 at a matched number of generated rollouts. Brando's second question: is a smooth partial-credit reward (arms B, D) a substitute for IRT selection, or does it add to it?

**Operational pass/fail (frozen; thresholds named with their source):**

- **H1, primary (Azalia's test).** C − A ≥ +1.5 points of validation strict pass@1 at update 48, with the 95% paired task-bootstrap interval above 0, pooled over 2 seeds. Threshold source: Brando's design document ("IRT for RL on Lean code verification", 10-20-2026); the seed spread of this pipeline is 0.56 points (experiment 08 expt_v16, the two v4 checkpoints). Verdict WORKED if both conditions hold; NULL if the interval includes 0; FAILED if the interval is below 0.
- **H3, key secondary (is the decomposition needed beyond a scalar?).** C − S and C − E at matched generated rollouts (6,144 per run; E is compared at its final checkpoint, whose generated-rollout count is reported), with intervals. IRT-specific value is claimed only if the C − S interval lies above 0; if that interval includes 0, the value is in measuring pass rates, not in IRT (recorded as NULL for the decomposition even when H1 holds).
- **H2, mechanism.** C has a higher mean active-group fraction per update than A and S (paired over updates, 48 per run, 2 seeds) and than E's pre-filter fraction. Online, the IRT forecast P(active) = 1 − p⁸ − (1 − p)⁸ with p = σ(a_j θ̂ + d_j) at the θ̂ in force when the group was drawn predicts active groups over all C and D groups with AUC ≥ 0.70 (experiment 13's gate F2, `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/PROTOCOL.md`).
- **H4, smooth reward × IRT.** The interaction (D − B) − (C − A) in validation strict pass@1 at update 48, with its interval. Classification: "substitutes" if the interval is below 0; "additive" if it includes 0; "synergy" if above 0. Agent-suggested classification rule, chosen before any data.
- **Pre-registered descriptive checks (no gate):** θ̂ against measured validation pass rate at updates 0, 16, 32 and 48 for C and D; per-update ECE of the C/D forecast (distribution shift of the frozen item parameters); a Goodhart audit of B and D (mean smooth reward per update against mean theorem count, compile rate and strict rate per update; a rising smooth reward with falling strict rate or compile rate is reported as gaming).

## Locked parameters

### 1. Data, splits and what was seen before this draft

- **Splits (D-013):** train 539 tasks (400 groups), validation 135 (100 groups), test 222 (never opened; test ids are read only as a guard; every loader drops test rows). Manifest: `experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/`.
- **Prompt pool:** the 539 D-013 train tasks, no external data. Prompts are experiment 103's single-call prompt built with experiment 08's pinned task adapter (`expt_v6/validation_adapter_v6.py`, sha256 recorded in the pack manifest) and addendum `vbv1`; the builder reproduces all 135 frozen validation prompt hashes of experiment 08 v3 as a control before the train pack is accepted.
- **Start policy:** Qwen3-1.7B-Base Lean SFT, experiment 08 v4 seed 20260831, weights `$SCRATCH/rl4cv_sherlock/expt_v4/runs/20260831/hf` on Sherlock (safetensors sha256 988ffbb3… and 7528a3e2…, from `expt_v4/results/persistent_verification.json`; re-hashed at every generation launch).
- **Panel respondents for the item fit:** experiment 12's 11 systems (`experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/results/input_manifest.json`), strict = 1[IC_tests = 1 and IC_proofs = 1] on train tasks, `measured` cells only (`zero_without_call`, `incomplete`, `unmeasured_infra`, `model_error` are missing). Experiment 05's Base models (`experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/expt_v1/results/per_task_*_g8.csv`, near zero everywhere) are added only if the G0 fit changes (both fits reported).
- **Task features:** experiment 19's `expt_v1/results/task_features_e19.csv` (train rows), the pre-registered feature set of its PROTOCOL §3.3 (log1p counts and flags z-scored with train moments, family-group indicators).
- **Seen before this draft:** the start policy's validation outcomes from experiment 08 expt_v16 (58/1080 strict, 24/135 mixed tasks); experiment 19's results (section 3 of the runbook); nothing from Phase 0.

### 2. Phase 0a manifest (calibration data)

- Cells: 539 train tasks × 8 samples × 1 model = 4,312 cells, one receipt each (`raw.jsonl` rows), chunked into 4 Slurm array tasks by sorted task id (135/135/135/134 tasks). Resumable; a retry reruns the identical cell.
- Sampler (frozen v12, experiment 08 `expt_v12/pipeline.py`): temperature 0.6, top-p 0.95, top-k 20, 12,288 new tokens, thinking on, stop `<|im_end|>`, seed 91 (per-cell seed 91·100003 + sample index, independent of the task chunking), batch 128, vLLM 0.30.0 in the Apptainer image `vllm-openai_v0.30.0.sif`.
- Scoring: VeriBench's frozen scorer (pin 59059a2, `score_scsc.py --skip-tc`, lake shim `lake env lean` → Lean v4.22.0, Mathlib 79e94a09) through the D-109 durable-capture wrapper (`expt_v1/sherlock/logged_scorer_e20.py`, a port of experiment 08 `expt_v24/future_logging/logged_scorer.py` + `durable_capture.py`), as a normal-partition CPU array (`-c 1 --mem 16G`), never on the dev partition. Every compiler and kernel call keeps stdout/stderr, source snapshot, compiler identity and exit status under `compiler_diagnostics/` outside any temporary directory.
- Partial credit: experiment 13's declaration adapter (`experiments/13_…/expt_v1/declaration_adapter.py` + `DeclarationProbe.lean`, unchanged) gives `factored_reward` (`src/rl4cv/e13.py`, unchanged) per cell; its strict value must equal the frozen scorer's strict on every Phase 0 cell (control; a disagreement is reported and the scorer's value is authoritative).
- Per-cell table committed to git: task id, sample, strict, factored_reward, IC_tests, IC_proofs, FSC = unmeasured (no judge calls; $0), generated tokens, token-cap flag, extraction method, finish reason.

### 3. Phase 0b item models and gate G0

- **Responses:** start policy as one respondent with binomial k of 8 per task; panel systems as binary respondents. Fits are marginal maximum a posteriori on experiment 19's grids (`irt_e19.py`: 1,201 nodes on [−12, 12], check grid 4,801 nodes on [−18, 18], gradient gate 1e-4 on both), abilities N(0, 1).
- **Models:** random-intercept 2PL (log a_j ~ N(0, s_a²), d_j = w0 + e_j, e_j ~ N(0, σ_e²), w0 ~ N(0, 2²)); explanatory 2PL (d_j = x_j·w + e_j, w ~ N(0, 2²), x_j = (1, task features)); the 1PL (a_j ≡ 1) reported beside them.
- **Prior choice (R0):** (s_a, σ_e) ∈ {0.1, 0.25, 0.5, 1.0} × {0.25, 0.5, 1, 2, 4}, chosen by mean held-out log loss over all train cells under grouped 5-fold cell-level cross-validation (folds by a hash of (respondent, D-013 group id); seed 20261021), separately for the two models. Ties go to the larger σ_e, then the larger s_a. Experiment 19 chose s_a = 0.25 at its grid edge; the grid now extends to 0.1.
- **Gate G0 (pre-registered):** 5 grouped folds over train tasks (by group id, seed 20261021). In each fold the start policy's cells on the held-out tasks are removed; the panel cells and features stay. The selected model is refitted; θ̂ of the start policy is its EAP from the in-fold cells; each held-out task's P(active) is the posterior-predictive E_θ[1 − p⁸ − (1 − p)⁸]. Pooled over folds (each task predicted once): AUC for the observed active groups (1–7 of 8) ≥ 0.70 (experiment 13's F2), and mean log loss below the population Beta(1,1) baseline (in-fold pooled rate p̄ = (K + 1)/(N + 2) over the start policy's in-fold cells, P(active) = 1 − p̄⁸ − (1 − p̄)⁸). Reported beside it without gating: ECE (10 equal-width bins), predicted against observed active share, the panel strict pass rate and the features-only (explanatory prior, no item data) alternatives. The random-intercept and explanatory models are both evaluated; the one with the lower G0 log loss is the selected model for arm C (ties → random intercept). Bootstrap: 10,000 draws over train task groups.
- **If G0 fails:** arms C and D are dropped, arms A, S, E, B run, and IRT selection is recorded as NULL.
- **Smooth reward (descriptive, no gate):** a graded response model on `factored_reward` categories 0 | (0, 0.5] | (0.5, 0.8] | (0.8, 1) | 1 (point masses at 0 and 1 favour the graded model over Beta-IRT, as experiments 14 and 19 found), with the 8 sample indices of the start policy as pseudo-respondents; item thresholds and the per-task forecast of a non-constant smooth reward are reported.
- **Dimensionality (descriptive):** rank correlations (Pearson, Spearman, Kendall; 1,000 item-group bootstraps) between strict item difficulty (−d_j/a_j) and the graded model's first threshold across the 539 items; experiment 19's two-skill model (strict on skill s, graded on skill f) is fitted under its convergence gate on the finer check grid and, if it converges, its held-out likelihood against the tied one-skill model on the start policy's cells is reported (5 grouped folds). A failed gate is reported as unavailable. Only one respondent carries both channels, so no claim about shared skills across systems is made.
- **Before training:** item parameters (a_j, d_j for 539 tasks, the selected model), θ̂₀ with its posterior SD, per-task p_j and P(active) forecasts, and this experiment's own numeric forecasts of H1–H4 are frozen with `rl4cv.forecast.freeze_forecast` (`expt_v1/forecasts/`); `expt_v1/input_pins_e20.json` pins every input hash.

### 4. Arms (one trainer, config, seed set and rollout budget; only the sampler and reward differ)

| Arm | Prompt sampler | Reward |
|---|---|---|
| A | uniform without replacement over the 539 train tasks (a seeded permutation, re-permuted when exhausted) | strict |
| S | uniform without replacement over the train tasks the start policy solved 1–7 of 8 times in Phase 0 (static filter, no IRT) | strict |
| E | DAPO dynamic sampling: draw 16 groups from A's stream, drop all-0 and all-1 groups, refill in batches of 16 prompts until 16 active groups are held; the update uses exactly the first 16 active groups. Every generated rollout counts against E's 6,144 budget; E stops at the first update whose cumulative generated rollouts reach 6,144 (overshoot ≤ 127 rollouts, reported). If the budget ends mid-refill with ≥ 1 active group, that final smaller update is taken; otherwise the run ends without it | strict |
| C | IRT-online: per update 12 of 16 groups drawn without replacement in proportion to a_j²·p_j(1 − p_j) (the 2PL item Fisher information at the current θ̂, textbook §6.2.2), 4 uniform from the remaining tasks | strict |
| B | uniform, the same prompt stream as A (same seed, same permutation) | smooth: experiment 13's `factored_reward` (`src/rl4cv/e13.py`, unchanged) |
| D | IRT-online as in C | smooth, as in B |

- **Arm C/D ability update (CAT-style sequential update, textbook §6.2.2):** item parameters frozen after Phase 0. θ̂₀ = EAP of the start policy on the Phase 0 data. After update u, the posterior on the 1,201-node grid is ∝ N(θ; θ̂_{u−1}, 1) × Π over the update's 16 tasks of Binomial(k_j | 8, σ(a_j θ + d_j)) with k_j the strict successes; θ̂_u is its EAP; θ̂_u and its posterior SD are logged at every update. The strict outcomes drive the update in D too (the smooth reward never enters the IRT update).
- **Rollout budget:** 48 updates × 16 groups × G = 8 = 6,144 rollouts per run. Seeds: 2 per arm (run seeds 1 and 2; the seed sets the prompt permutation, the sampler RNG and the per-rollout vLLM seeds). A and B share the prompt stream per seed; C and D share the IRT sampler's RNG seed and diverge once their outcomes differ.
- **Recipe (frozen):** AdamW, learning rate 1e-6 constant, β = (0.9, 0.999), weight decay 0, gradient-norm clip 1.0, one optimizer step per update (on-policy); clipped objective with ε_low = 0.2 and ε_high = 0.28; KL coefficient 0 (no reference model); token-normalized loss (sum of per-token losses over all completion tokens of the update divided by their count, TRL's `loss_type="dapo"`); group-normalized advantages (r − mean_group)/(std_group + 1e-4), so a degenerate group contributes zero advantage but its tokens stay in the normalizer; vLLM→trainer importance-sampling ratio exp(logp_trainer − logp_vLLM,processed) per token, truncated at 2.0 (TRL `token_truncate`, clip_max 2.0, no lower clip); gradient checkpointing; bf16 forward/backward with fp32 master weights and fp32 optimizer state.
- **Rollout sampler (frozen v12):** temperature 0.6, top-p 0.95, top-k 20, 12,288 new tokens, thinking on, stop `<|im_end|>`, max model length 16,384 (operational: verified against the longest Phase 0 prompt). A rollout that hits the cap keeps whatever the extraction rule yields (no overlong filtering; the cap flag is logged).
- **Trainer (recorded choice):** TRL 1.16's `GRPOTrainer` cannot host arms C and E as designed: its `RepeatSampler` fixes every generation batch before any reward of the run is observed, and it has no dynamic-sampling refill, so the IRT-online update and DAPO's refill cannot be expressed without rewriting its data path. The trainer is therefore this experiment's own loop (`expt_v1/train_e20.py`) that reuses TRL's colocated vLLM helper (`trl.generation.vllm_generation.VLLMGeneration`: in-process `vllm.LLM`, sleep mode, `logprobs_mode="processed_logprobs"`, `sync_weights`) and implements the loss above with pluggable samplers (`Uniform`, `StaticFilter`, `DynamicDAPO`, `IRTOnline`; `expt_v1/samplers_e20.py`, unit-tested in `tests/test_e20_samplers.py`, loss in `tests/test_e20_loss.py`). Runtime: the vLLM 0.30.0 Apptainer image (torch 2.13.0+cu130, transformers 5.17.0) with a venv overlay holding `trl==1.16.0`; exact versions are recorded in `expt_v1/results/runtime_versions.json` at the smoke test. The NeMo RL port of experiment 13's backend is not used.
- **Reward computation during training:** strict via the frozen scorer on the training node (one job directory per sample index, 8 parallel scorer processes, D-109 wrapper); smooth via the declaration adapter (which also yields strict for logging). The smoke test measures whether a CPU array between updates would be faster and records the choice (operational).
- **Checkpoints:** full resumable state (weights, optimizer, sampler state, θ̂ history, RNG) at updates 16, 32 and 48; the pilot's A, C, S seed-1 runs continue as the first 16 updates of their main runs (identical config and streams), so the pilot is not re-run.

### 5. Evaluation manifest

- Validation 135 tasks × 8 samples with the frozen v12 evaluation sampler (seed 91, as Phase 0a), strict via the frozen scorer, at update 0 (the shared start policy, measured once and cross-checked against experiment 08 expt_v16's 58/1080) and at updates 16, 32 and 48 of every run (E: its final checkpoint; its intermediate checkpoints at 16 and 32 where they exist). Declared cells: (12 runs × 3 checkpoints + 1) × 1,080 = 39,960, each with a receipt; infrastructure retries rerun the identical cell up to 3 times; unmeasured cells stay in the denominator and are listed.
- The test split stays unopened; a single test pass of each arm's update-48 checkpoint happens only after Brando says so.

### 6. Phases, gates and budget caps

| Phase | Gate / stop rule | GPU-h cap |
|---|---|---|
| 0a calibration | 4,312/4,312 cells generated and scored; D-109 evidence present | 10 (Phase 0 total) |
| 0b IRT fit | G0 as in §3; fail → drop C, D | CPU |
| Smoke | 2 updates of arm A; stop if > 1% of completion tokens have abs(logp_trainer − logp_vLLM) > 0.05 on the recomputed sampling support (experiment 09's failure); runtime versions recorded | counted in pilot |
| Pilot | A, C, S seed 1, 16 updates each; stop if A already has ≥ 50% active groups (selection has nothing to fix) or C's active-group fraction < 1.5 × A's; otherwise lock this file | 15 |
| Main | 6 arms × 2 seeds × 48 updates; Slurm jobs resumable from 16/32/48 | 130 |
| Evaluation | §5 | 80 |

Total 200 GPU-h and $0 API spend (open-weight models only; no provider or Vals keys). GPU-h are summed from `sacct` elapsed time × GPUs per job and reported against each cap at every phase boundary. If a cap would be exceeded, the work stops at the phase boundary and is reported (never silently shrunk).

### 7. Statistics (Hard Rule 11; `~/agents-config/workflows/statistics-reporting.md`)

- Every headline is x [lo, hi] p-val=Z. Intervals: paired task bootstrap, 10,000 draws over validation task groups (100 groups; near-duplicate and safe/vulnerable pairs move together), seed 20261021, seeds kept paired (each draw resamples groups once and evaluates every run on the same resampled set; arm means pool the 2 seeds). p-values: two-sided percentile test of a zero difference, 2·min(P(Δ* ≤ 0), P(Δ* ≥ 0)), floored at 1/10,000; a paired-seed sign-swap test is reported as a secondary p-value where seeds are the unit. Intervals cover validation task sampling, not seed sampling (2 seeds), which is reported as the between-seed difference.
- Per arm: pass@1 and pass@8 (validation), active-group fraction per update, generated tokens per active group, GPU-h, θ̂ against measured pass rate (C, D).
- Missing cells stay in the denominator and are listed with their reason.

## Scale verification (no further normalization)

Strict ∈ {0, 1}; `factored_reward`, IC_tests, IC_proofs ∈ [0, 1] as the scorer and adapter emit them (no re-division); pass@1 is reported in percentage points (mean of 8 samples × 100); AUC, ECE and log loss on their natural scales. Advantages are group-normalized inside the trainer only.

## Verified data layout

- `raw.jsonl` (rl4cv.veribench.generate): `task_id`, `sample_idx`, `label`, `model`, `sampling{temperature, top_p, top_k, max_tokens, seed, thinking, stop_tokens}`, `instruction_sha256`, `addendum_sha256`, `prompt_sha256`, `system_prompt_sha256`, `prompt_tokens`, `generated_tokens`, `finish_reason` (`stop`/`length`), `measured`, `truncated`, `admitted`, `extraction` (`file_blocks`/`no_lean_block`/…), `lean`, `completion`.
- Scorer `<name>_per_task.csv` (frozen 59059a2 column names): `task`, `IC_ap` (= IC_tests), `IC_pp` (= IC_proofs), `TC` (judge; unused), `agent_compiles`, `agent_n_ex`, `agent_n_thm`, `agent_n_sorry`, `kernel_n_theorems`, `kernel_n_honest`, `kernel_probe_ok`, `kernel_declared_axioms`, `scoring_status`; strict = `rl4cv.rewards.reward_kernel_binary(rl4cv.veribench.jobs.scored_response(row, gen_row))`, exactly as experiment 08's ladder tables.
- Experiment 12 manifest cells: `system`, `task_id`, `source_status`, `IC_tests`, `IC_proofs`, `FSC`; loaded by experiment 19's `data_e19.load_panel` (test rows dropped on read).
- Split manifest: `task_id, family, core, split, group_id, group_size, py_relpath, gold_relpath, py_sha256, gold_sha256`.
- Features CSV: `task_id, split, family, family_group, core, py_stmts, py_funcs, py_loops, py_branches, py_float, py_str, py_check_asserts, gold_theorems, gold_examples, gold_loc`.

## Pre-conditions for run

- Sherlock private runner online (`sherlockctl status`), identity `brando9`; grading project `$SCRATCH/rl4cv_sherlock/grading/READY`; image `$SCRATCH/rl4cv_sherlock/containers/vllm-openai_v0.30.0.sif`; start-policy weights hash-verified; train pack manifest `status: PASS`; TRL venv overlay built inside the image (smoke test).
- Local analysis: `/lfs/skampere1/0/brando9/venvs/rl4cv_e20` (Python 3.12.14, NumPy 2.5.4, SciPy 1.18.1, pytest 9.1.1); `make test` passes before every push.
- No provider keys, no Valkyrie: the experiment makes zero model API calls.

## Estimated wall-clock

- Phase 0a generation: about 1.7 h per chunk on an L40S (experiment 08 expt_v16 measured 1,080 cells in 5,718 s), 4 chunks in parallel, about 7 GPU-h; queue wait on the shared gpu partition is unknown (530 pending jobs at 11:30 PDT on 10-21-2026).
- Phase 0a scoring: 4,312 files at about 10–25 CPU-s each as a 32-task normal-partition array, about 1 h wall; partial credit about the same again.
- Phase 0b: about 1–2 CPU-h on skampere1 (grids of 20 prior settings × 5 folds × 2 models).
- Smoke: about 1 GPU-h. Pilot: 3 × 16 updates at an estimated 10–18 min per update (generation about 5–11 min, scoring about 3–5 min, optimizer step about 2–4 min), about 8–14 GPU-h.
- Main: 12 × 48 updates at the pilot's measured per-update time: 96–170 GPU-h if 10–18 min per update; the pilot's measurement decides whether the 130 GPU-h cap holds before launch. Evaluation: 37 × about 1.6 GPU-h ≈ 60 GPU-h.

## Pass/fail / abort rules

- Smoke pass admits the pilot; the pilot's two gates admit or stop the main runs (a stop is a reported NULL on selection, not a redesign).
- During any phase: an infrastructure failure is retried up to 3 times on the identical cell or job; a scientific gate failure stops at that boundary with its exact evidence; a cap that would be exceeded stops at the phase boundary. Never resample or drop a cell because of its score. Every outcome, including NULL, is reported in `results.md` with the same statistics.
- `expt_v1/results/E20_FINISHED.txt` is written at the end with the verdict (WORKED, NULL, FAILED or STOPPED at <gate>) and the final commit.

## Identity / contact crib (verified)

- GitHub `brando90` (verified: `gh auth status` on skampere1, 10-21-2026); repository `brando90/rl-4-code-verification`, branch `e20-irt-prompt-selection`, one PR into `main`, not merged by the worker.
- Sherlock user `brando9`, account `sanmi` (verified through `sherlockctl exec 'id -un'`, 10-21-2026); Slurm mail `brando.science@gmail.com`.
- Run emails: To `brando.science@gmail.com`, BCC the four inboxes, via `uutils.emailing.send_email_smtp` with `~/keys/gmail_app_password.txt` (never printed).
- Worker: tmux `cc-rl4cv-e20-irt-prompt-selection` on skampere1 (Claude Code claude-fable-5-1, max effort, profile cc); checkpoint `CKPT_cc-rl4cv-e20-irt-prompt-selection.md`.

## Sources opened for the method choices

- Truong and Koyejo, *AI Measurement Science* (updated 09-07-2026), HTML at `https://aims.stanford.edu/textbook/src/chapN.html` (the runbook's `aimslab.stanford.edu` address redirects there). Opened: chapter 3 Models (§3.3 Rasch, §3.6 2PL/3PL; the item model here is the 2PL with a 1PL reported), chapter 4 Learning (§4.3.3 marginal maximum likelihood, §4.5 Bayesian priors and MAP as L2-regularized likelihood, §4.6 regularization chosen by cross-validation: the marginal MAP fits with grouped cross-validated priors), chapter 6 Efficiency (§6.2.2 Fisher information a²P(1 − P) and the CAT loop: arm C's selection weights and sequential θ̂ update; §6.2.5 D-optimal design, not used because one ability dimension is fitted), chapter 7 Discovery (§7.1 dimensionality by parallel analysis, §7.2 the factor model: the dimensionality check is descriptive here because one respondent carries both channels), chapter 8 Predictability (§8.1 amortized models predicting item parameters from item features: the explanatory prior and the features-only forecast), chapter 9 Intervention (§9.1 causal framing of each arm as an intervention; §9.3 distribution shift: the frozen item parameters are monitored by per-update ECE), chapter 10 Ecosystem (§10.1 Goodhart's law, §10.3 gaming: the Goodhart audit of the smooth arms). Note: the runbook's table placed factor models in chapter 3 and dimensionality in chapter 8; in the current book those are chapter 7, and chapter 8 holds the amortized models.
- CS321M slides (PDFs opened and text-extracted): Lecture 2 (Rasch, 2PL, 3PL, Bradley–Terry), Lecture 3 (MLE, EM, MAP = L2-regularized likelihood, AUC and ECE as the fitted-model checks used in G0), Lecture 4 (K-factor models, cold start, prediction-guided evaluation with item-side predictors: the explanatory prior), Lecture 5 (item information, max-information CAT, Thompson sampling; arm C's 25% uniform share is the exploration analogue). Discussion notebooks (Colab/Drive) were not opened (no browser on this host). The design document (Google Doc) was not opened; the runbook reproduces it.
- Literature list cited in the README (arXiv ids as given by the runbook; not re-read in this session).
