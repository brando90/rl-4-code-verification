# Experiment 10 protocol: promotion-policy replay on SWE-bench Verified per-item factor matrices

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/PROTOCOL.md>

**TLDR:** This protocol fixes every population, split, policy, outcome, interval and decision rule for replaying AlphaHebe-style promotion decisions on experiment 07's 164 × 424 SWE-bench Verified factor matrix.

- **Primary question:** at the same validation gain, does per-item information pick safer promotions than the scalar score? Binary losses and factor regressions are each tested, with three policies that promote the same validation-gain distribution.
- **Lock order:** the protocol is locked, and its predictions frozen with `rl4cv.forecast.freeze_forecast`, before any statistic is computed on the real data.

**Status:** LOCK CANDIDATE, revision 2 (10-09-2026). It applies the GPT-6 Astra (effort ultra) design review in [`reviews/`](reviews/) and the synthetic checks below.

- The Claude Fable 5.1 review of revision 1 did not finish (out of usage credits at 10:18 PDT). A replacement Fable review of this revision runs on another account before the lock.
- The lock is the commit that adds `expt_v1/forecasts/e10_forecast.json`.

## What was seen before the lock

- **Published system-level results** from experiment 07 (H1, H1b, H2, H3).
- **Field names and row counts of the per-cell file:**
  - 91,000 rows;
  - in the 164 × 424 cohort, 68,608 cells are measured test reports and 928 are "no patch or patch not applied".
- **Experiment 07's test-list drift, listed per cell:** 66 cells in 4 tasks (`pylint-dev__pylint-7080` 51, `astropy__astropy-7606` 13, `django__django-10097` 1, `django__django-13449` 1). Source: `expt_v1/inputs/test_list_drift_e07.json`.
- **Synthetic data only, for the code:** a system-level "breaks PASS_TO_PASS" signal set and a null set (`expt_v1/synthetic_e10.py`), plus a bootstrap-coverage simulation. No pair, split or policy statistic has been computed on the real cohort.

## Inputs (pinned)

| Input | Pin |
|---|---|
| Per-cell factors | `experiments/07_scs4c_vs_pass1_swebench_across_models/expt_v1/results/per_cell_e07.jsonl.gz`, SHA-256 `f064c3951860cf4d88879e7c3b81ec42c8b42780923c61198c71f98dc6463a4d` |
| Cohort | Experiment 07's 164 included systems × 424 common-cohort tasks; reproducing both counts is a stop rule. Declared upstream denominator: 182 systems × 500 tasks. Every estimate here is conditional on the 164 × 424 analysis cohort and is not extrapolated to all systems or tasks |
| Drift list (sensitivity only) | `expt_v1/inputs/test_list_drift_e07.json` |
| Code | `expt_v1/analyze_e10.py` and `tests/test_e10_replay.py` at the lock commit |
| AlphaHebe semantics | `AndrewZhou924/AlphaHebe-dev@f89294e`: `control/promotion.py::gate_decision` promotes iff `candidate.score > incumbent.score` |

## Cells and factors

For system X and task t:

- r_X(t) is `resolved`.
- The derived gated factors are a_X(t) = (g, g·t_fix, g·t_keep).
  - When g = 0 the tests did not run. The raw t_fix and t_keep stay null in evidence; only the derived gated fractions are 0. This matches experiment 07's `Cell.gated`.
- Experiment 07's single internally inconsistent cell (`20250516_cortexa_o3` on `matplotlib__matplotlib-20826`) is used as recorded and listed.
- **Sensitivity:** test-list drift cells are removed by dropping their 4 tasks, giving 164 × 420. Report-derived resolution stays the authority.

## Halves and what this replay is (and is not)

- **Splits:** R = 1,000 random partitions of the cohort tasks into a **validation** half V (212 tasks), which is what a promotion policy sees, and a **test** half E (212), the outcome. Seed `20261009`.
  - **What it mirrors:** in AlphaHebe the promotion gate evaluates the incumbent and the candidate on the promotion envelope (`control/controller.py`).
  - **What it omits:** public system pairs leave out candidate generation and search selection, so this is a screening study of promotion rules, not of live edits.
- **Estimands:** each is the average over these 1,000 splits of a split-level statistic. Split 5th–95th percentiles are reported as ranges, not confidence intervals.

## Pair statistics (ordered pair incumbent I → candidate C, task set T ∈ {V, E})

| Statistic | Definition |
|---|---|
| gains_T, losses_T | Tasks resolved by C but not I, and by I but not C; net_T = gains_T − losses_T; Δpass1_T = net_T/|T| |
| ΔSCS_T | Difference in system SCS4C-T, the geometric mean of the gated t_fix and t_keep means (decision D-009, as in experiment 07) |
| TRM_T (policy penalty, range [0, 3]) | (1/|T|) Σ_t Σ_k max(0, a_I,k(t) − a_C,k(t)) |
| HRM_T (hidden) | The same sum over tasks jointly unresolved by I and C, still divided by |T| |
| KRM_T | The gated-t_keep part of HRM_T: a net fractional decline in passing PASS_TO_PASS fractions, not a count of newly broken tests |
| GLM_T | The TRM_T contribution from tasks where I's gate is 1 and C's is 0. Reported, not used for decisions |

## Populations (fixed)

- **P_near (primary):** ordered pairs of distinct systems with 1 ≤ net_V ≤ 10, the "small validation gain" regime (0 < Δpass1_V ≤ 0.05 at |V| = 212).
  - Similar validation scores do not make the two systems similar edits; this is a conditional association study.
  - A split with fewer than 200 P_near pairs is degenerate and excluded, with the count reported. If more than 10% of splits are degenerate, the P_near verdicts are **inconclusive**; there is no switch of population.
- **P_pos (secondary):** all ordered pairs with net_V ≥ 1. Point estimates and split ranges only, with no bootstrap interval.
- The fourth hypothesis of revision 1 (model versus harness change from organization tags) is **deferred**: organization tags do not identify interventions (GPT-6 review, finding 9).

## H1 (descriptive): the scalar rule's harm

Among P_near pairs, all of which the current scalar rule promotes, report:

- the harmful promotion rate HPR (share with Δpass1_E < 0);
- the share with losses_E ≥ 1;
- the mean losses_E / |E|;
- the mean Δpass1_E (the regression-to-the-mean check).

## H2 (descriptive association, not a mechanism test)

**(a)** Partial Spearman correlation of HRM_V with losses_E/|E|, controlling for losses_V, gains_V and pass1_V(I).

- Pass1_V(C) is omitted, because it is determined by these three.
- Ranks are average ranks for ties. The residual correlation is undefined, and counted, when a design matrix is ill-conditioned (condition number ≥ 10¹⁰) or a residual variance is zero.

**(b)** Sensitivities:

- KRM_V in place of HRM_V;
- HRM_V with the incumbent's and candidate's marginal gate rate and gated factor means added as covariates;
- TRM_V controlling for gains_V and pass1_V(I).

**(c)** Predictive comparison with endpoint-disjoint systems. Per split, the systems are split randomly into halves A and B; ordinary least squares is fit on P_near pairs within A × A and evaluated on pairs within B × B, predicting losses_E/|E|.

- M0: binary features (losses_V, gains_V, pass1_V(I)).
- M1: M0 plus the six marginals.
- M2: M1 plus HRM_V, KRM_V, TRM_V and GLM_V.
- Report the median out-of-sample R² and the median and share of ΔR² (M2 − M1) > 0 over splits. These are split ranges, not intervals.

**Caveat, measured before the lock on synthetic data:** H2(a) was positive even on a null synthetic set without any system-specific breakage trait (0.112 [0.056, 0.148]); with marginals it was 0.037 [0.007, 0.081]. Factor values on hard, jointly unresolved tasks also sharpen the estimate of a candidate's ability. A positive H2 is therefore **not** evidence of a regression-specific mechanism.

**Frozen prediction (agent-suggested):** H2(a) > 0 with its interval excluding 0. It is reported with the caveat and does not drive decisions.

## H3 (primary): gain-stratified matched-rate screening policies

Within each split and each validation net-gain stratum k ∈ {1, …, 10} of P_near:

- each policy keeps the q fraction of the stratum's pairs (cumulative weight ≤ q × stratum weight), so all policies promote the **same validation-gain distribution**;
- ties are broken by an outcome-independent SHA-256 hash of the ordered system names;
- q = 0.5 is primary; q ∈ {0.25, 0.75} are sensitivities.

| Policy | Within each stratum, keeps the pairs with … | Information beyond the scalar score |
|---|---|---|
| R0 | hash order only | none (what a scalar gate can do at equal gain) |
| R1 | largest ΔSCS_V | smooth aggregate |
| R2 | smallest losses_V (at fixed net gain: least churn) | binary per-item outcomes |
| R3 | smallest TRM_V | full factor matrix |
| R3h | smallest HRM_V | factor regressions that pass/fail cannot see |

**Unstratified comparators** (keep the q fraction of all P_near pairs):

- S0+: largest net_V, the "just be stricter" rule;
- S1: largest ΔSCS_V;
- S2: smallest losses_V;
- S3: smallest TRM_V.

The last two (S2, S3) rank by regression risk while ignoring gain size; they are reported but are not fair information tests.

**Outcomes per policy:**

- HPR;
- mean losses_E/|E|;
- mean Δpass1_E (benefit retained);
- recall: the weighted share of P_near pairs with Δpass1_E > 0 that are kept;
- achieved rate.

**Paired contrasts:** the same splits and draws are used throughout, and each difference is HPR(first) − HPR(second), so positive means the second policy is safer.

| Contrast | Question |
|---|---|
| C_bin = R0 − R2 | Does binary per-item information pick safer promotions at equal gain? |
| C_fac = R2 − R3 | Does the factor matrix add beyond binary information? |
| C_fac0 = R0 − R3 | Factor matrix versus scalar only |
| C_hid = R0 − R3h | Hidden partial regressions alone |
| C_agg = R0 − R1 | Smooth aggregate versus scalar only |
| C_strict = S0+ − R3, S0+ − R2 | Information-based rules versus simply demanding larger validation gains |

**Utility guard:** for any recommended policy, the paired difference in mean Δpass1_E (recommended minus comparator) must have a 95% lower bound above −0.01.

**Frozen predictions and verdict rules (thresholds agent-suggested):**

1. **Factor gate.** Recommend a factor-matrix promotion check for AlphaHebe, and make it a primary arm of experiment 11, iff all of these hold:
   - C_fac > 0 with its interval excluding 0;
   - C_fac0 > 0 with its interval excluding 0;
   - the utility guard passes against R2 and R0.
2. **Binary gate.** Otherwise, recommend binary per-item non-regression iff C_bin > 0 with its interval excluding 0 and the utility guard passes against R0.
3. **Neither.** Otherwise, per-item information does not pick safer promotions at equal validation gain on public system pairs, and the factor feedback question moves to experiment 11 without a gate claim.
4. **Practical comparison (reported).** A 20% relative HPR reduction versus S0+, as GPT-6 suggested, is a practical target, not evidence of a true reduction of at least 20%.

**Deployable rule (descriptive):** the share of P_near and P_pos pairs that a strict per-candidate rule would accept, and its HPR. The rule is net_V ≥ 1 and losses_V = 0, rejecting on any incomplete evidence. It is reported at its natural acceptance rate and not forced to q.

## Statistics

- **Bootstrap:** a dyadic system bootstrap with B = 1,000 draws, seed `20261010`, over the same 1,000 splits.
  - Each draw resamples the 164 systems with replacement; pair (I, C) between distinct original systems gets weight m_I·m_C. Self pairs never occur.
  - Selection, ranks and summaries are redone with these weights.
  - Interval: the percentile interval of the split-averaged statistic over the draws. Draws with an undefined statistic are dropped and counted.
- **What the interval covers:** resampling systems conditions on the 424 tasks and the 1,000 splits. It does not cover task sampling, family dependence between related submissions, or repository effects.
- **Format:** reported as `x [lo, hi] p-val=n/a` (no null-hypothesis test), with pairs per split, splits used and systems.
- **Synthetic coverage check** (recorded in [results.md](results.md) before the lock): the nominal 95% intervals' coverage of known population values in a node-dependent simulation. This is a sanity check, not a proof of calibration.

## Validity checks and stop rules

- An input SHA-256 mismatch, or failure to reproduce 164 × 424, stops the analysis.
- An unmeasured or incomplete cohort cell stops the analysis.
- Policies, q, populations, covariates and seeds are fixed. Any change is a new `expt_v2` with a new lock; retrospective rankings cannot retune this test.

## Phase B (separate admission)

Replay the policies on real AlphaHebe incumbent/candidate per-task records, which the AlphaHebe team will export.

- **No reuse of decision outcomes:** the outcomes used to make a promotion decision cannot also estimate its later harm. Phase B needs untouched third-envelope outcomes, or a prospective partition of existing promotion tasks into decision and test parts, with records whose adaptive history used the test part rejected.
- A separate addendum is frozen before reading those records.

## Not in this experiment

New model calls, new SWE-bench evaluations, D_gold, VeriBench factors, organization-tag interventions, and live AlphaHebe optimization (experiment 11).
