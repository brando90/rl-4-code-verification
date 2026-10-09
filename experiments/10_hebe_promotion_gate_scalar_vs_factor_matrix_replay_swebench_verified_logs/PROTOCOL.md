# Experiment 10 protocol (DRAFT, not locked): promotion-gate replay on SWE-bench Verified per-item factor matrices

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/PROTOCOL.md>

**TLDR:** This draft defines the pair populations, task splits, gates, outcomes, statistics and frozen predictions for replaying AlphaHebe's promotion decision on experiment 07's 164 × 424 SWE-bench Verified factor matrix. It is **not locked**. It will be locked, and its predictions frozen with `rl4cv.forecast.freeze_forecast`, only after the design reviews are resolved and before any pair statistic is computed.

**Draft status:** written 10-09-2026 by Claude Code (`claude-opus-5-5`) for Brando, under review by GPT-6 Astra (effort ultra) and Claude Fable 5.1 (`reviews/`).

**Outcomes seen before the lock:**

- Experiment 07's published system-level results (H1, H1b, H2, H3) are known. They are cited in the README.
- No pair-level, split-level or gate statistic has been computed. Inspecting the per-cell file's field names and row count (91,000 rows; fields `instance_id, gate, t_fix, t_keep, resolved, d_gold, unmeasured_reason, submission, status, score, included, common_cohort`) is the only data contact.

## Inputs (pinned)

| Input | Pin |
|---|---|
| Per-cell factors | `experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/results/per_cell_e07.jsonl.gz`, SHA-256 `f064c3951860cf4d88879e7c3b81ec42c8b42780923c61198c71f98dc6463a4d` (added in commit `42384e0`) |
| System and task cohort | Experiment 07's 164 included systems and 424 common-cohort tasks (`included` and `common_cohort` flags). Reproducing both counts is a stop rule |
| Submission metadata (H4 only) | `metadata.yaml` per submission from `github.com/SWE-bench/experiments`, `evaluation/verified/<submission>/`, at a commit recorded at fetch time. Missing files are listed per submission |
| AlphaHebe semantics | `AndrewZhou924/AlphaHebe-dev@f89294e`: `control/promotion.py::gate_decision` (scalar strict improvement) |

## Cells and per-item factors

For system X and task t in the cohort:

- r_X(t) ∈ {0, 1} is `resolved`.
- The factor vector is f_X(t) = (g, t_fix, t_keep), using `gate`, `t_fix`, `t_keep`.
- When g = 0, the tests did not run. For factor arithmetic, t_fix and t_keep are then treated as 0, because nothing runs. This choice is fixed here and stated in results.
- Experiment 07 recorded 1 of 82,905 cells violating resolved ⇔ (g = 1, t_fix = 1, t_keep = 1). Recorded values are used as is, and the violating cell is listed.

## Splits

R = 1,000 random partitions of the 424 tasks into S (212) and H (212), with seed `20261009`. Every statistic is computed per split; split-level distributions are summarized by medians and 5th–95th percentiles, which are not confidence intervals.

## Pair statistics (ordered pair I → C, task set T ∈ {S, H})

- pass1_T(X) = mean_t r_X(t); Δpass1_T = pass1_T(C) − pass1_T(I).
- gains_T = #{t: r_I = 0, r_C = 1}; losses_T = #{t: r_I = 1, r_C = 0}.
- ΔSCS4C_T = the difference of per-cell SCS4C-T means, where per-cell SCS4C-T = g · √(t_fix · t_keep).
- **Total factor-regression mass:** TRM_T = (1/|T|) Σ_t Σ_k max(0, f_I,k(t) − f_C,k(t)) over k ∈ {g, t_fix, t_keep}.
- **Hidden factor-regression mass:** HRM_T is the same sum restricted to items with r_I(t) = r_C(t) = 0, that is, partial regressions that pass/fail cannot see.
- **Keep-regression mass:** KRM_T is the t_keep-only part of HRM_T, measuring newly broken existing tests on still-unresolved tasks.

## Pair populations (fixed before analysis)

- **P_near (primary):** pairs with 0 < Δpass1_S ≤ 0.05 in that split. This is the small-improvement regime where real harness edits live, and it is defined only from S.
- **P_all:** all ordered pairs of distinct included systems (164 × 163 = 26,732), restricted per split to Δpass1_S > 0 for gate analyses.
- **P_meta (H4 only):** metadata-labeled pairs.
  - Model change: same `tags.org`, different sorted `tags.model`.
  - Harness change: identical single-model `tags.model`, different `tags.org`.
  - Pairs that change both, or neither, are excluded and counted.

## Hypotheses, analyses and frozen predictions

### H1 (descriptive): the current gate's harm

Among P_near pairs that G0 promotes (Δpass1_S > 0), report:

- the **harmful promotion rate** HPR = share with Δpass1_H < 0;
- the share with losses_H ≥ 1;
- the mean losses_H.

Each comes as a median over splits, with a 95% system-cluster bootstrap interval (below).

### H2: do hidden factor regressions predict held-out losses?

Over P_near pairs per split, compute the partial Spearman correlation between HRM_S and losses_H/|H|, controlling for losses_S, gains_S and pass1_S(I). Use rank-transformed ordinary-least-squares residuals, then the Pearson correlation of the residuals. The statistic is the median over splits.

- **Frozen prediction:** median partial ρ > 0, and its 95% system-cluster bootstrap interval excludes 0.
- **Secondary:** the same with KRM_S, and with TRM_S controlling for gains_S and pass1_S(I) only.

### H3 / H3b: gates at a matched promotion rate

Within each split, start from the pairs G0 promotes in P_near. Each gate keeps a fraction q of them, with q = 0.5 primary and q ∈ {0.25, 0.75} secondary:

| Gate | Keeps the q fraction of G0-promoted pairs with … |
|---|---|
| G0+ (stricter scalar, the comparator) | largest Δpass1_S |
| G1 (aggregate smooth) | largest ΔSCS4C_S |
| G2 (binary per-item non-regression) | smallest losses_S / |S|; ties broken by larger Δpass1_S |
| G3 (factor matrix) | smallest TRM_S; ties broken by larger Δpass1_S |

Outcomes per gate:

- **Primary:** HPR.
- **Secondary:** mean losses_H, mean Δpass1_H (the benefit kept) and the share of G0-promoted pairs with Δpass1_H > 0 that the gate retains (recall of real improvements).

**Frozen predictions:**

- **H3:** the relative HPR reduction of G3 versus G0+ at q = 0.5, (HPR(G0+) − HPR(G3)) / HPR(G0+), is ≥ 0.20 with a 95% interval excluding 0.
- **H3b:** G2 versus G0+ is reported with the same statistic, no threshold.
- **G3 versus G2:** reported (does the matrix add beyond binary non-regression).
- **G1 versus G0+:** expected ≤ 0 given experiment 07 H2. Reported.

### H4 (secondary, exploratory): model versus harness change

- **Features on S,** oriented I → C:
  - Δ gate rate;
  - Δ mean t_fix among gated items;
  - Δ mean t_keep among gated items;
  - HRM_S, KRM_S and TRM_S.
- **Classifier:** L2 logistic regression with C = 1.0 and standardized features.
- **Cross-validation:** leave-one-org-out over P_meta, on a single fixed split (the first seed).
- **Frozen prediction:** AUC ≥ 0.65, with a 95% org-cluster bootstrap interval excluding 0.5.
- **Not run:** if fewer than 30 labeled pairs of either type exist, or metadata is missing for more than 20% of systems, H4 is reported as not run, with counts.

## Statistics

- **Dependence:** pairs share systems, so intervals use a system-cluster bootstrap. Each draw resamples the 164 systems with replacement, rebuilds ordered pairs between distinct original systems, and recomputes each statistic on a fixed subsample of 100 splits. B = 500 draws, seed `20261010`; report 2.5th and 97.5th percentiles.
- **Format:** reported as `x [lo, hi] p-val=n/a` (bootstrap interval, no null-hypothesis test), with denominators: number of pairs promoted per split, number of splits and number of systems.
- **Instrument:** factors come from the official SWE-bench harness reports; there is no judge.
- **Reading the results:** these are associations among different public systems, not causal effects of edits. External validity to AlphaHebe edits is tested only in phase B.

## Validity checks and stop rules

- **Input identity:** a mismatched input SHA-256, or failure to reproduce 164 systems × 424 tasks, stops the analysis.
- **Degenerate splits:** a split where P_near has fewer than 200 G0-promoted pairs is recorded as degenerate and excluded from that statistic, with the count reported. If more than 10% of splits are degenerate, P_all becomes the primary population, and this switch is pre-declared here.
- **No retuning:** the gates, q, populations and features are fixed. Any change is a new `expt_v2` with a new lock.

## Phase B (separate admission)

- **What:** replay G0, G0+, G2 and G3 on real AlphaHebe incumbent/candidate per-task records (their GEPA and Meta-Harness runs), using AlphaHebe's own search and promotion envelopes in place of random splits.
- **Admission:** per-task scores and, where available, per-task factors for every candidate on both envelopes, with run identities.
- **Before reading any outcome:** a separate protocol addendum is frozen.

## Not in this experiment

New model calls, new SWE-bench evaluations, D_gold (experiment 07 phase B), VeriBench factors, and live AlphaHebe optimization (experiment 11).
