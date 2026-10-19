# Decision log

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/DECISIONS.md>

**TLDR:** Decided so far: separate repository; pinned clones instead of submodules; FSC always gated on compilation; forecasts hash-frozen before outcomes; work directly on `main`; self-hosted open-weight inference approved with model substitution allowed; FSC judge route and payer (`vb103_judge` on Valkyrie, Vals gateway); experiments restructured to Brando's two goals (D-007); VeriBench V1 split into train / validation / test for policy training, test held out (D-013); single-call Valkyrie teachers for experiments 02A v3 and 08 (D-014, D-015); matched warm-start ownership (Lethan 1.7B/8B, Rakshit 4B/14B) and the two RL-readiness criteria from the 10-13-2026 meeting (D-017). Still open for Brando: GPU compute, the pool source, the paper's code, and who leads.

Format: `D-NNN — title — status — date — owner`, then context, decision and consequences.
Append new entries; strike through superseded ones and point to the entry that replaces them.

## Decided

### D-001 — Separate project and repository — accepted — 09-30-2026 — Brando

- **Context:** The first analysis was drafted as an idea inside the VeriBench repository (draft PR brando90/veribench#428).
- **Decision:** Brando said this is a new project, separate from VeriBench, and created [`brando90/rl-4-code-verification`](https://github.com/brando90/rl-4-code-verification). The plan, code, prompts and meeting notes live here. VeriBench is a pinned external dependency.
- **Consequences:** VeriBench's own rules still govern any VeriBench number this project reports (see [CLAUDE.md](../CLAUDE.md)). The VeriBench PR's content was moved here.

### D-002 — Pinned clones instead of git submodules — accepted — 09-30-2026 — Claude (Brando: "fine with whatever")

- **Context:** The project reads three repositories: VeriBench (private, large, shared by many agents), its frozen scorer commit, and the rl-env-scaling fork.
- **Decision:** No submodules. [`external/deps.lock.json`](../external/deps.lock.json) records exact commits, and [`scripts/setup_external.sh`](../scripts/setup_external.sh) fetches each into `external/<name>` (git-ignored) and checks the resulting commit.
- **Why:**
  - Submodules need recursive authenticated clones on every remote host.
  - They leave detached-HEAD checkouts that agents accidentally commit into.
  - They make it easy to bump a pin silently.
  - A lock file keeps the pin change reviewable in one diff, and it allows two pins of the same repository (current VeriBench and experiment 103's frozen scorer), which submodules handle awkwardly.
- **Consequences:** Changing a pin is an explicit reviewed commit to `deps.lock.json`. Code finds VeriBench through `$VERIBENCH_ROOT` or `external/veribench`.

### D-003 — FSC is always gated on compilation — accepted — 09-30-2026 — Claude

- **Context:** VeriBench's judge scores non-compiling files, sometimes at 1.0 ([FACTS §3](FACTS_veribench_baselines.md#3-the-fsc-judge)).
- **Decision:** Any reward or outcome that uses FSC is gated: `fsc_compiled` pays FSC only when IC_tests = 1, and `scsc` is 0 whenever IC_tests · IC_proofs = 0. Ungated `fsc` exists only as a diagnostic.
- **Consequences:**
  - Judge calls are needed only for responses that compile and prove at least one theorem, which is cheap while success is rare.
  - Per-checkpoint SCSC is exact without judging the rest.

### D-004 — Prospective chronology is mechanical — accepted — 09-30-2026 — Claude

- **Decision:** Every forecast is written with `rl4cv.forecast.freeze_forecast` (canonical JSON, SHA-256 sidecar, append-only ledger) before any outcome it predicts is read. Scoring code refuses to compare against a forecast whose hash does not verify.

### D-005 — Same model family and scales as the paper for the law test — proposed — 09-30-2026 — Claude

- **Decision:** The generalization test (experiment 02B) uses Qwen3 Base 1.7B, 4B, 8B and 14B, as the paper did, so the domain is the main thing that changes.
- **Consequences:** Newer small models (Qwen3.5 0.8B–9B) appear in experiment 01 as baselines, not as the law's scale axis.

### D-006 — Work directly on `main` — accepted — 09-30-2026 — Brando

- **Context:** Brando: "can we start pushing to main? Merge all PRs/branches to main."
- **Decision:** Agents commit to `main` after `make test` passes and delete merged branches. The bootstrap PR (#1) and the other Claude branch (`claude/admiring-heisenberg-eok3j4`, notes on RL and base-model coverage) were merged into `main` on 09-30-2026.

### D-007 — Experiments restructured to Brando's two goals — accepted — 09-30-2026 — Brando

- **Context:** Brando: "I still see a lot of experiments when in my head we have 2-3 ... 1. doing what varun mentioned if we can create envs using our predictive eqn/law to solve vb's 3 metrics. And 2. resolving the question allen said/asked or I raised to allen (on snap since we need open weight models)".
- **Decision:** Three experiments. 01 stays the shared baseline. 02 is Varun's question, with the former experiments as phases: old 02 → 02A (pools, warm start, ρ–H probes), old 03 → 02B (prospective 2×2 forecast check, the "if we can" gate), old 04 → 02C (reward channel for FSC), old 06 → 02D (train the forecast-selected recipe and report VeriBench V1). Old 07 → 03, Allen's coverage question. Old 05 → `experiments/ideas/cross_family_env_mixtures_alignment` (deferred, not run). Claude chose the layout and names under agents-config Trigger Rule 57; the change is reversible (`git mv` history).
- **Consequences:** Only names, links and indexes changed; no hypothesis, protocol or threshold changed. Earlier decision entries, commits, issue comments and experiment 01's own files use the old numbers ([old → new map](../experiments/README.md#old--new-numbering-09-30-2026-d-007)). Experiment 01's folder becomes `01_small_qwen_vbv1_single_call_baseline_g8_signal_probe` after its run finishes.

### D-101 — Self-hosted open-weight inference — accepted — 09-30-2026 — Brando

- **Context:** Experiment 01 needed approval for running open-weight models outside Valkyrie.
- **Decision:** Brando: "just do the experiment, it's fine to change models. I want to do these experiments. Go." Self-hosted inference of open-weight models is authorized for this project, and substituting models is allowed. Every substitution or scale-down is a new, separately labelled condition (`expt_vN`), never an edit to a locked protocol.

### D-102 — FSC judge route and payer — accepted — 09-30-2026 — Brando

- **Context:** FSC in experiments 01–05 (old numbering; now 01, 02A–02C and the cross-family mixtures idea, see D-007) needed a judge route and payer; agents may not write direct provider API calls (agents-config Hard Rule 9).
- **Decision:** Brando: "use the vb103_judge Valkyrie route." Route: experiment 103's `vb103_judge` Valkyrie agent (experiment 100 H2 ensemble: GPT-6 Sol high + Claude Opus 5.5 max, median of 3 each, mean of the 2, divided by 5). Payer: the Vals model gateway, the same account and environment experiment 103 used.
- **Consequences:** Scope per `PROTOCOL.md`: every scored cell with IC_tests · IC_proofs > 0, plus the 60-file audit per model. Judging runs as a new, separately labelled suite (`rl4cv-e01:<label>`) on its own benchmark instance; experiment 103's existing judge records and runs under `veribench_vb103` are never modified. FSC in experiments 01–05 (old numbering, see D-007) is unblocked.

### D-012 — Push to `main` small and often — accepted — 10-07-2026 — Brando

- **Context:** Brando, 10-07-2026: "we likely need to put a reminder in the agents claude .md folders to push to main often since this repo is shared by 3+1+1 people!" The same day, three agent sessions edited one checkout at once and one held an unpushed local commit that touched shared files (`CLAUDE.md`, this file).
- **Decision:** `CLAUDE.md` → Repository conventions → "Push small and often": commit and push each finished, test-passing step immediately; pull before starting and before each push; never stage or commit another session's uncommitted files; when sessions share a checkout, work from a separate clone or a detached worktree that pushes `HEAD:main` (no feature branch). Extends D-006.

### D-014 — Single-call teachers for experiment 02A v3, an exception to D-108's vendor-agent rule — accepted — 10-07-2026 — Brando

- **Context:** experiment 02A v3 builds Lean warm-start data from frontier teachers through Valkyrie. D-108 asks for each vendor's own agent, but on 10-07-2026 none is runnable on Valkyrie for these teachers (the native Claude Code and Codex routes lost their credential route; there is no Google agent for Gemini 4 Argon).
- **Decision:** Brando chose "Approve single-call (Recommended)" over Terminus 2 with a Lean compiler and over waiting for vendor agents: one common single-call agent (`vb103_single_call`) for Claude Fable 5.1, GPT-6 Astra and Gemini 4 Argon through Valkyrie, Vals-funded, as specified in that experiment's `PROTOCOL.md` § 4.
- **Scope:** experiment 02A v3 only. D-108 is unchanged for every other experiment; payer verification, route naming and the runaway guard still apply.

### D-013 — VeriBench V1 train / validation / test split for policy training — accepted — 10-07-2026 — Brando

- **Authorization:** Brando, 10-07-2026: "maybe we can use VeriBench as a validation set … we can split VeriBench into train val test in a reasonable way, and then create a plan so that we use Valkyrie to create a bunch of synthetic data from Claude Opus 5.5 and Astra … start doing an SFT and then do the training."
- **Decision:** `rl4cv.splits` splits VeriBench V1 (896 tasks at the `veribench` pin `c11b99ba`) into train 539, validation 135 and test 222. Core is 369 / 93 / 152 and IndustrySet is 170 / 42 / 70.
  - Near-duplicates stay in one split. A near-duplicate is an exact normalized hash or a word-5-gram Jaccard ≥ 0.70 on the Python program or the gold Lean reference. Each security safe/vulnerable pair also stays together. The result is 664 groups.
  - Groups are assigned per family, in salted-hash order (salt `rl4cv-d013-vbv1-split-v1`), to the split with the largest deficit against 0.60 / 0.15 / 0.25.
  - No model output or score is read. Manifest SHA-256 `157ce781ed9e4ac93a1a1fe0c49f2ee2ae907be1260402485c8f6fa3d06e0e24` in `experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/`.
  - The largest cross-split Jaccard is 0.640 (Python) and 0.610 (gold Lean).
- **Use:**
  - Train: SFT and RL prompts, gold references and teacher outputs on train tasks.
  - Validation: checkpoint selection, tuning and RL monitoring.
  - Test: one evaluation per frozen checkpoint, never used for training, tuning or selection.
  - VeriBench numbers for trained policies are reported on the test split, core and IndustrySet separately, never on all 896, which now contain training tasks.
- **Consequences:**
  - `CLAUDE.md`'s "VeriBench is held out" becomes "VeriBench V1's test split is held out" for experiments locked from 10-07-2026 on. Experiments 01–07 and 02A v3 keep the rule they were locked under (all of VeriBench held out).
  - Experiment 05's per-task receipts restricted to the splits are free Base-model baselines.
  - Frontier evaluations in the VeriBench repository train nothing and are unaffected.
  - D-104 gains a pool: VeriBench train tasks with kernel-verified teacher files (experiment 08).
  - **Review clarification (10-07-2026):** `docs/DATASETS.md` screens D-013 training text against validation/test and other held-out panels; earlier locks still screen against all 896. Existing Base/teacher test summaries are prior exposure, not a previously unseen test; they cannot guide the prospective recipe or selection. D-009 common-cohort aggregation requires FSC for every IC_tests = 1 cell, even with zero proved theorems; experiment 08 adds that coverage to D-102's proof-positive scope and preserves its 60-file audit. Historical protocols and numbers are unchanged.

### D-015 — Single-call Valkyrie teachers (Claude Opus 5.5, GPT-6 Astra) for experiment 08's SFT data — accepted — 10-07-2026 — Brando (request), Claude master (route)

- **Context:** Brando asked on 10-07-2026 for synthetic SFT data "from Claude Opus 5.5 and Astra" via Valkyrie for experiment 08. D-108 asks for each vendor's own agent. No such route is runnable on Valkyrie for these teachers today, for the reasons D-014 records. The Qwen policy being trained answers in one call, so single-call teacher files match its format.
- **Decision:** the same route Brando approved for experiment 02A v3 in D-014: `vb103_single_call` through Valkyrie, Vals-funded. The teachers are `anthropic/claude-opus-5-5-no-fallback` at maximum compute effort and the highest-effort GPT-6 Astra selector the registry serves, with 4 samples per train task. Settings are in experiment 08's `PROTOCOL.md` § 3. The route choice was made by the master under agents-config Trigger Rule 57, following Brando's D-014 choice, and is flagged to Brando in the experiment 08 issue.
- **Scope:** experiment 08's teacher data only. These are data-generation calls, not a VeriBench evaluation. D-108 is unchanged elsewhere; payer verification, route naming and the runaway guard apply.

### D-016 — Experiment 01 follow-up owned by Rakshit — accepted — 10-07-2026 — Brando

- **Authorization:** Brando: "create a gitissue for experiment 01 and assign it to rakshit … figure out how to get qwen models that don't get zero on vb … I think it's reasonable to do some type of SFT. But we likely need to let the person think what."
- **Decision:** Rakshit Kaushik (@rakshit-kaushik) owns experiment 01's follow-up issue ([issue #8](https://github.com/brando90/rl-4-code-verification/issues/8)): its results, the 10-07-2026 zero-score diagnostic, and getting small Qwen models off SCSC ≈ 0. The SFT itself is experiment 08 (`08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test`), which he already owns (D-013, D-015). The issue's suggestions are a head start, not a lock; he chooses the design.
- **Scope:** this settles D-106 for experiment 01's follow-up only. Fixing VeriBench's digit-leading `namespace` hint is a separate VeriBench decision under agents-config Trigger Rule 43.

### D-017 — Matched warm-start ownership and RL-readiness criteria (10-13-2026 meeting) — accepted — 10-13-2026 — Brando (ownership, milestone), Varun (Base models, matched tokens, signal band)

- **Context:** Experiment 08 version 1 trained Qwen3 Base 1.7B, 4B, 8B and 14B with one matched recipe (658 updates, 5,752,936 loss tokens each, 1,315 examples from 476 of 539 train tasks) and closed PARTIAL on 10-11-2026: 8B (step 658) and 14B (step 334) pass the validation gates at different fractions; 1.7B and 4B pass no rung. Its version 2 matched test evaluation is route-blocked (Vals Valkyrie HTTP 403 since 10-13-2026 03:27 PDT; 0/5,328 new cells). Every reinforcement-learning (RL) phase waits on a common warm start. Record: [meeting folder](../experiments/meetings/oct_13_2026/oct_13_2026.md) ([transcript](../experiments/meetings/oct_13_2026/transcript.md), [summary](../experiments/meetings/oct_13_2026/summary.md), [PLAN](../experiments/meetings/oct_13_2026/PLAN.md)).
- **Decision:**
  - **Ownership.** Lethan (@lethan3) owns 1.7B and 8B; Rakshit (@rakshit-kaushik) owns 4B and 14B. Brando: "Ethan can do like 1.7B and 8B. And, and Rakshit, you can do the other 2. The 4B and 14B." Both work on one shared recipe with identical supervised fine-tuning (SFT) examples, order and loss-token budget at every size (Brando: "Crucial. That all the models are SFT'd. On the same. Data and same number of tokens, right? Varun?" Varun: "Yes." … "Same number of tokens."). Owning a size does not authorize a separate recipe. The work continues in [experiment 08 expt_v3](../experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/README.md).
  - **Base models, never Instruct**, so the sizes stay comparable (Varun's earlier rule, restated by Brando and confirmed).
  - **Readiness** is assessed on the validation split only, with two criteria kept visible because they measure different quantities: Varun's RL-signal band, "25 to 75% success rate … running it like 8 times on that model" (binary success per task over 8 attempts; mixed groups), and Brando's performance milestone, "close to 25% accuracy or 25% … SCSC" (Smooth Conjunctive Score for Code verification, the geometric mean of three factor means; SCSC ≥ 0.25 is not a 25% success probability). The existing frozen format/signal gates of experiment 08 (extraction ≥ 972/1,080, capped ≤ 108/1,080, mixed tasks ≥ 7/135) stay in force.
  - **Meeting format.** Mentees bring measured results and a short presentation to the next meeting instead of Brando prompting agents live (Ethan and Rakshit: "Agreed, agreed."). No deadline was agreed; Rakshit expected to resume after his midterm.
  - **Data sources.** OpenR1 math-only SFT data is a lower-priority alternative; Varun agreed Lean data is needed ("fine-tune with lean because it should understand the formatting of whatever it's trying to RL on"). VeriBench-Infinity (VBV3) is a candidate Lean source only after its source tasks are identified and disjointness from the validation and test splits is proved; it is not admitted by this decision. Training never uses the benchmark ("Don't train on the test set"); D-013 is the executable form.
  - **Keys.** The meeting's suggestion that mentees "can use the Coelho [Koyejo] lab keys like the Stanford or the Vals keys" does not override D-108: runs Brando or his agents execute use the Vals-funded Valkyrie route; collaborators use their own authorized access.
- **Consequences:** D-106 is settled for experiment 08. PLAN § 12 records that experiments 02B–02D, 03, 09 and 13 wait on a common validation-passing warm start. Experiment 08's index row names the owners and the expt_v3 preparation. Post-meeting status (10-14-2026): the MBPP warm-start file (587 rows / 455 tasks) was emailed to Lethan 10-14-2026 00:40 PDT and his SNAP access was completed 10-13-2026 15:00 PDT; Rakshit's SNAP access waits on IL Action ticket #149859; Brando's Slurm request is ticket #149865; the Vals route was asked about 10-14-2026 03:43 PDT. Details in [action_items.md](../experiments/meetings/oct_13_2026/action_items.md).

## Open — needs Brando

| ID | Question | Recommendation | Blocks |
|---|---|---|---|
| D-103 | Compute: whose GPUs and how many hours? Paper: about 350 B200 GPU-hours for 32 trajectories. The Lean replication likely needs 1.5–2× that because outputs are longer. | Varun's B200 allocation for experiments 02B–02D and 03; SNAP for experiment 01. Status 10-14-2026: Brando's SNAP Slurm request is IL Action ticket #149865, unanswered since 10-13-2026 12:27 PDT; Lethan's SNAP access completed 10-13-2026 15:00 PDT; Rakshit's waits on Prof. Koyejo's approval (ticket #149859, 10-13-2026 18:07 PDT) | experiments 02B–02D and 03; experiment 08 expt_v3 training |
| D-104 | Pool source for the full-file family: FVAPPS-derived, synthetic VeriBench-style, or both. Synthetic references need a frontier-model generation budget. | Start with FVAPPS (it already exists); add synthetic only if FVAPPS fails the quality screen | experiment 02A |
| D-105 | Access to the paper's exact code, NeMo RL configs and warm-start checkpoints. Upstream `madanva/rl-env-scaling` `main` (= the old pin `c75755c`) holds 91 planning files and no training code; the code is on the upstream branches `controlled-scaling-v2` (`7118b86`, 08-31-2026, 408 files), `progress/experimental-rigor` and `first-iteration`. GitHub's "Sync fork" syncs only `main`, so it would not bring the code over. On 09-30-2026 the fork received `controlled-scaling-v2` and `external/deps.lock.json` was provisionally re-pinned to `7118b86` (Claude, reversible). | Ask Varun which commit (or the submission zip) produced the submitted paper's numbers, which NeMo RL v0.7.0 configs it used, and where the SFT step-512 warm-starts for 1.7B/4B/8B/14B live; re-pin to his answer | experiments 02 (all phases) and 03 |
| D-106 | Lead and mentee assignment (experiment 07: settled by D-011, Emily owns it; experiment 01's SFT follow-up: settled by D-016, Rakshit owns it; experiment 08 matched warm start: settled by D-017, Lethan 1.7B/8B and Rakshit 4B/14B under one recipe) (notes A name Ethan Lee as a candidate lead). Brando, 09-30-2026: "I want to start running all of them and tagging Emily (@emxia18)". | Emily (@emxia18) runs the experiments on SNAP starting with 01 via `scripts/cc_prompt_run_experiment_on_snap.md`; Rakshit owns 01’s follow-up (D-016); lead for 02A remains open; mentees take pool construction and screens | scheduling |
| D-107 | VeriBench draft PR brando90/veribench#428 (the idea folder written before D-001). | Close it as superseded by this repository, or keep a one-line pointer in VeriBench's ideas index | housekeeping |

Note on D-105 (09-30-2026):

- Git submodules stay rejected (D-002); the paper's repository is a pinned clone in `external/deps.lock.json`.
- NeMo RL itself is pinned by package version (v0.7.0, the version named in upstream `docs/research/NEMORL_PAPER1_RL_ARCHITECTURE_AUDIT_20260830.md` on `controlled-scaling-v2`), not vendored into this repository.


### D-008 — Operationalize Azalia's suggestion through controlled decisions — accepted design — 10-05-2026 — Codex under Brando's requested experiment

- **Canonical home:** `experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/`.
- **Decision:** Treat the Smooth Conjunctive Score for Code verification (SCSC) as a downstream outcome in its own right. Test whether the factor vector improves fixed-budget repair/environment/reward choices beyond scalar feedback. Use fixed-reference success as an auxiliary construct check, not a replacement aggregate.
- **Execution:** Begin with a retrospective, zero-model-call inventory of existing modern score rows and separately labeled historical replay artifacts. New inference/training comparisons require an endpoint harness and a separately frozen full manifest; no benchmark reference edits or new provider charges in this first phase.
- **Reuse:** Existing `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_c_reward_channel_for_fsc_kernel_vs_judge` owns reward training; this experiment does not duplicate it. All controller training/tuning, environment choice and checkpoint selection use contamination-screened external data, never VeriBench.
- **Measurement caveat:** The current VeriBench paper and this repository's summary implementation use different dataset aggregation orders. Preserve historical evidence and resolve the intended reporting convention before new scored interventions. The first audit reports counts only.
- **Provenance:** Supplied Azalia email, retrieved September thesis decks and the Stanford weekly notes' 09-29-2026 Varun section; exact sources and an unsent clarification draft are colocated in the experiment.

### D-009 — Execute endpoint validation and a bounded external repair pilot — accepted — 10-05-2026 — Brando

- **Authorization:** Brando: "do it these tasks ... if we need to wait for the qwen evals wait then do it or just do it. GO!"
- **Decision:** Preserve the completed audit; use experiment04 version2 for restricted authored checker controls and version3 for real external-panel applicability and repair. Reuse experiment02 version2 preparation for screened source data and prospective training readiness. The existing experiment05 worker retains ownership of its Qwen3 Base evaluation.
- **Admission:** Implement and run deterministic controls now. Before scientific repair calls, freeze actual external task/reference identities, independent endpoint validity, model revision, prompts, full manifest, judge capacity and resource budget. Initial ceilings are 24 tasks, four conditions, two repairs, one graphics processor/six graphics-processor hours; details are in the version3 runbook. No large training allocation or invented checkpoint is implied.
- **Aggregation:** New official dataset summaries use the geometric mean of factor means on a common measured cohort, as stated in the current VeriBench ICML 2027 metric section. Per-artifact geometric means remain repair feedback; their arithmetic mean is a separately labeled diagnostic. Historical files and scoring implementation are not rewritten by this decision.
- **Scope:** The synthetic controls cannot replace accepted real external references. No benchmark-reference modifications, new provider charges, email/collaborator messages or VeriBench-based controller/training tuning are admitted.

### D-010 — Extend actionable metrics to SWE-bench Lite — accepted — 10-05-2026 — Brando

- **Authorization:** Brando requested a similar plan for SWE-bench, Terminal-Bench or a consequential coding benchmark, instructed execution, and said he was going to sleep.
- **Choice:** `06_swebench_lite_factor_feedback_matched_budget` runs in parallel with experiment04. SWE-bench Lite is selected because real repository repair has an independent official outcome and a smaller, existing validation split. Terminal-Bench 2.1 remains a documented extension with task-family-specific constructs.
- **Scientific scope:** The public diagnostic geometric mean is a new proxy, not VeriBench SCSC. Compare ordinary logs, aggregate-only feedback and aggregate-plus-components using shared initial patches and two repairs. Hold official patches, tests, identifiers and logs out of solver feedback. The first eight-task validation panel supports feasibility; a later 24-task test panel requires a new frozen protocol.
- **Execution bounds:** At most 56 solver responses plus eight public-check-author responses through an authenticated subscription CLI; zero graphics processors, two bounded containers, 18 wall hours and 160 processor-hours. Source hashes, all cells, prompts and tool isolation must freeze before model calls. Existing subscription access is not proof of remaining allowance or model entitlement. No new charges, benchmark-reference changes, training, collaborator messages or leaderboard submissions.
- **Dependency:** Qwen's ongoing evaluation is not required for this coding pilot. The existing remote worker and its files retain their owner; experiment06 uses a separate checkout and persistent session.

### D-011 — SCS4C for general code; experiment 07 owned by Emily — accepted — 10-07-2026 — Brando

- **Authorization:** Brando: "write it up as experiment 07 design doc … create a git issue … assign emily … Ping lethan to teach emily what the scsc metric is … Emily owns this set of experiments … once the whole experiment thing is done, dispatch it to snap and try to complete it … Light qa with very smart codex."
- **Definition:** SCS4C = G · (T_fix · T_keep · D_gold)^(1/3), where G is a patch-usable gate, T_fix and T_keep are the FAIL_TO_PASS and PASS_TO_PASS pass fractions, and D_gold is agreement with the gold patch on frozen generated inputs. Phase A uses SCS4C-T = G · (T_fix · T_keep)^(1/2). No docstring factor inside the product (reasons in the experiment 07 README).
- **Naming:** the smooth conjunctive score family; SCS4CV is VeriBench's SCSC ("SCS4CV (formerly SCSC)" in new prose; frozen evidence, paper versions and code identifiers keep `scsc`); SCS4C is the general-code member. Consistent with D-010's "new proxy, not VeriBench SCSC".
- **Execution:** phase A (public SWE-bench Verified logs, zero measured model calls) is locked for SNAP execution with one Codex light-QA round. The master reported dispatch, but no launch receipt is recorded in the checkpoint; execution is unverified. Phases B (SWE-Bench Pro Verified, D_gold, Valkyrie) and C (reward) need their own locked protocols.
- **Ownership:** Emily (@emxia18) owns experiment 07 and its follow-ups; Lethan (@lethan3) explains VeriBench's SCSC to her. This settles D-106 for experiment 07 only.

### D-108 — Vals Valkyrie for model calls when Brando runs the work — accepted — 10-07-2026 — Brando

- **Authorization:** Brando: "when brando is using this I have access to vals.ai valk so we can use it. See vb agents claude .md to see what this means and add these details to the agents claude files here."
- **Decision:** model calls in work Brando runs go through Vals Valkyrie with the saved private configuration, funded by Vals, under the rules copied from VeriBench's `CLAUDE.md` into this repository's `CLAUDE.md` → "Compute and model calls". D-102's judge route is unchanged; D-101 self-hosted inference remains the alternative.
- **Limits:** only Valkyrie- or Vals-managed credentials supplied through Valkyrie's secret mapping qualify as Valkyrie; copying Brando-held provider keys or subscription tokens into that mapping does not. Host-side/direct key use requires an experiment-specific named-key instruction; measured calls never fall back to personal funding. Verify the payer before the first call and name the route per call. Solver generation uses each vendor's own agent; D-102 judging keeps its validated custom agent and exact model, effort, rubric, inputs and aggregation, checked with positive and negative controls before first use. Collaborators need their own authorized Valkyrie access.
- **Source correction (10-07-2026, light review):** clarified the credential boundary, solver/judge distinction and control requirements against VeriBench's `CLAUDE.md`, “Experiment execution and funding.” This corrects the summary, without changing D-102 or any frozen condition.
- **Hosted-cloud setup correction (10-14-2026):** Brando supplied Jarett Forzano's migration notice and asked which projects and agent memory need updates. Current [Valkyrie configuration](https://docs.valkyrie.vals.ai/get-started/configuration) uses browser login or access keys, organization secrets, provider mappings and server-side benchmark registration; the former saved-YAML/Amazon Web Services setup is historical. The shared procedure is `~/agents-config/workflows/valkyrie.md`. Experiment 08 version 2 deployment/judging scripts still copy private YAML and select legacy environment variables; adapt and verify these before reuse. This documentation correction does not migrate accounts, move old data, clear run holds or change D-102, D-108 funding, scientific settings or completed results.

### D-109 — Retain compiler and kernel diagnostics — accepted — 10-19-2026 — Brando

- **Request:** “fix that for future runs and do it now” after completed scorer caches omitted failed compiler stderr.
- **Decision:** retain raw stdout/stderr, source/compiler identity, exit and timeout status for each compiler/kernel invocation in durable run artifacts. Use experiment08 `expt_v24/future_logging/parallel_scoring_logged.py` for new run versions25+; its default command factory requires the logged scorer. Historical frozen scorers and verdicts stay immutable.
- **Verification:** actual Lean success/error and kernel-policy equivalence, unchanged verifier bytecode, timeout partial-output parity, deleted-probe survival and controlled abrupt-stop log survival passed; the exact default worker command passed a frozen-CLI fixture. See `expt_v24/future_logging/results/`.
- **Recovery:** version24 reused851 earlier diagnostic logs and recovered930+897 failed fresh-run diagnostics using96 parallel single-threaded Lean processes with20-second diagnostic limits. Official scores unchanged; full3,240-cell classification and limits are in `expt_v24/README.md`.
