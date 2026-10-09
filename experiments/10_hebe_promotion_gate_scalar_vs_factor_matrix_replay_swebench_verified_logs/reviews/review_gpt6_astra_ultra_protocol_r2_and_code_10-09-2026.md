# Revision 2 promotion-policy replay review: fix weighted matching and undefined estimands before lock

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/reviews/review_gpt6_astra_ultra_protocol_r2_and_code_10-09-2026.md>

**TLDR:** Not ready to lock: three blocking, five major and one minor finding remain. The existing eight tests pass, but synthetic counterexamples expose unmatched bootstrap selections, changing split support and an empty-population crash.

**Reviewer:** OpenAI Codex command-line interface 0.162.1, exact model `gpt-6-astra`, effort `ultra`, verified from this session's `turn_context`; default account/configuration profile `~/.codex` (no named profile selected). The account's personal/work label is not independently verified. Deployment `deploy_7f1f1fb8b11149c4b7a411039b61888d`; thread `01a122fa-fe6d-7cb0-ad46-a8288a05530f`; 10-09-2026. One inherited-model helper retrieved prior-finding locations; this reviewer owns the judgments.

**Evidence and scope:** Commit `94cb41468425219eb2a6b4c63c2c05e7732e6cdf`. References below are within `experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/`: **Code** means `expt_v1/analyze_e10.py`; **Protocol** means `PROTOCOL.md`. Line references identify the reviewed revision. Only synthetic outcomes were loaded. Code and protocol are unchanged; this report and the expressly requested results/checkpoint updates remain local and unpublished.

## Numbered findings

Priority `p` is reviewer-assigned urgency on a 10-point scale. `NaN` means an undefined numerical value.

1. **[p 10/10] Blocking — bootstrap policies do not retain matched weight within gain strata.** Protocol:105–108,163–166 promises the same validation-gain distribution. Code:154–161,260–268 implements an indivisible weighted prefix. With weights `[2,1,0]` and retention fraction `q=.5`, order `[0,1,2]` retains weight **0**, whereas `[1,0,2]` retains **1**, from the same budget 1.5. These weights can arise from resampled system multiplicities `[2,1,1,0]` on consecutive positive-gain pairs. Identity weights match across stratified policies; bootstrap weights need not, changing the comparison whose interval is reported.

   **Fix:** before lock, specify identical retained mass `floor(q*W_k)` in each stratum of total weight `W_k`, allowing the boundary pair to contribute some of its replicated weight. Return selected weights, not a Boolean mask. In sorted order:

   ```python
   budget = np.floor(q * w_sorted.sum(-1, keepdims=True))
   before = np.cumsum(w_sorted, axis=-1) - w_sorted
   selected_weight = np.clip(budget - before, 0, w_sorted)
   ```

   Undo sorting and use these weights for outcomes. Apply the same declared boundary convention to unstratified policies; test exact per-stratum matching across draws.

2. **[p 10/10] Blocking — undefined splits silently change the bootstrap estimand.** Code:365–386 uses `nanmean` separately for each draw and metric; Protocol:49,84,166 requires split-average estimates and counted undefined statistics. For split values `[[.2,.8],[.4,NaN]]` (columns: point/draw), code returns `[.3,.8]`: the draw uses one split and the point uses two. `draws_defined` counts the surviving average, concealing the missing split. Contrasts are correctly formed within splits, but different contrasts and utility checks can still use different support.

   **Fix:** freeze the undefined-split convention explicitly. Define and report each statistic's common split support, keep paired policies on that support, and invalidate a bootstrap draw if a required split statistic is undefined. Use ordinary means on admitted support; count undefined splits/draws and freeze minimum usable coverage. Do not let missing observations select the averaging denominator silently.

3. **[p 10/10] Blocking — empty populations crash before the degeneracy rule runs.** Code:350 calls `split_statistics` before checking the pair count at 351. `weighted_ranks` reaches `add.reduceat` at 189 with an empty array. A synthetic 4-system × 424-task all-unresolved matrix produces `IndexError`, instead of a counted degenerate split. Code:359–364 also lacks Protocol:66's “more than 10% degenerate ⇒ inconclusive” status unless every split is excluded.

   **Fix:** count pairs before computing statistics; skip and record degenerate primary splits. Emit an explicit inconclusive status whenever the primary exclusion fraction exceeds .10. Specify any secondary-population exclusion separately: Protocol:67 does not impose the primary 200-pair rule on it. Add empty, partially degenerate and threshold-boundary tests.

4. **[p 9/10] Major — the correlation condition-number gate checks the wrong matrix.** Protocol:84 sets a `10^10` design-matrix threshold. Code:203–212 checks the normal matrix `XᵀWX`, whose condition number squares that of the weighted design, then explicitly inverts it. For 3,000 observations with covariate ranks differing by one adjacent swap, measured conditions were **205,219.5** for the design and **4.2115×10^10** for the normal matrix. Code returned undefined; stable least squares gave partial rank correlation **0.59391046**. This is a deterministic counterexample, not an experiment estimate.

   **Fix:** use float64 weighted least squares on `sqrt(w)*X`, check that design's condition number, and define the numerical residual-variance tolerance. Runtime weights are float32 (Code:340), unlike the float64 duplication test. A separate synthetic 31-weight check found differences below `2.6e-7`, so no material ordinary-case precision failure was observed; it does not validate near-singular cases.

5. **[p 9/10] Major — undefined denominators become misleading numerical results.** Code:280 reports harmful promotion rate **0** when the deployable rule accepts **0** pairs. A synthetic incumbent losing one validation success and gaining two reproduced this. Code:273 similarly makes recall zero when no test-positive pair exists. Code:398 converts undefined predictive differences to `False` before `nanmean`: `[.1,NaN]` yields positive share **.5**, instead of **1/1 defined comparison**, or a wholly undefined summary under a stricter convention.

   **Fix:** return undefined for zero conditional denominators; preserve accepted/positive counts. Filter predictive comparisons with `isfinite` before computing the positive share and report both defined and attempted split counts. Freeze this convention and the currently undocumented 50-pair fitting/evaluation cutoff (Code:299).

6. **[p 9/10] Major — incomplete evidence and drift dimensions are not fully guarded.** Code:61 converts `resolved=None` to false; Code:65 omits the gate array from missingness checks. Synthetic rows with missing resolution, and separately a nonfinite gate with finite factors, were accepted. Duplicate system/task keys overwrite at 57–64. In sensitivity mode, Code:334 skips all shape validation, although Protocol:42 requires **164 × 420** and 173–174 requires complete evidence.

   **Fix:** validate unique keys, explicit binary resolution/gates, finite factor fractions in [0,1], and null raw fractions only where permitted for a zero gate. Check all four derived arrays. Assert expected dimensions for both modes and exactly the declared four drift-task removals. No defect in the pinned real cells is alleged; these are missing enforcement checks.

7. **[p 8/10] Major — unstratified comparator tie-breaking adds an unregistered gain preference.** Code:171–172 sorts equal binary-loss or total-factor-penalty pairs by **descending net gain before hash**. Protocol:119–126 describes those policies as ranking by regression risk while ignoring gain size. Equal penalties, gains `[1,2]` and ascending hashes `[0,1]` produce order `[1,0]` for both policies.

   **Fix:** either remove `-net` from these two `lexsort` keys, using `(hash, penalty)`, or explicitly freeze the extra gain key in the protocol before outcomes. Integer binary losses make this more consequential than a rare floating-point tie.

8. **[p 8/10] Major — failure to establish superiority is described as evidence of no benefit.** Protocol:156 says per-item information “does not pick safer promotions” whenever the recommendation gates fail. Failure can mean insufficient precision, an undefined statistic, or failure of the benefit-preservation guard despite a safety improvement. README:41–50 additionally retains the old mechanism and deployment verdicts; README:65–66 retains obsolete resampling and two-envelope admission text.

   **Power evidence:** the existing synthetic signal artifact, `expt_v1/results/synthetic/signal_20splits_100draws.json`, has 164 systems, 424 tasks, 20 splits and 100 system-bootstrap draws. Factor-versus-binary harmful-rate reduction is **0.01052 [−0.00959, 0.03934] p-val=n/a**; factor-versus-scalar is **0.01475 [−0.00773, 0.03385] p-val=n/a**. These conditional 95% intervals both cross zero. They demonstrate uncertainty in that simulation, not impossibility of meeting the gates or measured power on real data. The coverage experiment does not measure recommendation power; additional task splits do not create additional independent systems.

   **Fix:** use “no recommendation; superiority or retained utility not established,” with reason codes. Reconcile README with revision 2. Before claiming adequate power, measure the complete decision rule on prespecified synthetic alternatives/nulls at the intended dimensions. A positive ranking result justifies developing a fixed-threshold candidate gate; freeze its calibration before live use. Neither split-conditional intervals nor public-system pairs establish safety for adaptive live edits.

9. **[p 6/10] Minor — required split ranges are missing for policy outputs.** Protocol:49,67 calls for split ranges, with secondary positive-gain pairs receiving point estimates/ranges only. Code:376,389 emits policy and deployable summaries without ranges; their secondary intervals are merely undefined. Predictive fit/evaluation counts from Code:298 are also discarded.

   **Fix:** add identity-weight split 5th–95th percentiles and defined-split counts to these outputs; retain predictive sample counts. Label ranges explicitly, and omit bootstrap-interval fields for the secondary population.

## Verification and earlier blocking findings

`tests/test_e10_replay.py`: **8/8 passed in 1.56 seconds**, using the runbook's isolated `uv` command with `PYTHONDONTWRITEBYTECODE=1` and pytest cache disabled. The supplied environment has no pytest. Synthetic probes above executed in memory or automatically removed temporary directories.

Correct source-level mappings include the **1–10** primary net-gain band at 212 validation tasks (also 1–10 at 210), average tie ranks, specified correlation covariates, disjoint fitting/evaluation endpoints, system-multiplicity product weights on distinct original endpoints, common task splits, identity-only secondary weights, contrast signs and recommended-minus-comparator benefit inputs. The weighted-rank duplication test passes.

One generated signal matrix (seed 1), **164 × 424**, **one split × 1,000 draws**, all three retention fractions, used **4.8 seconds** inside `run` and **1,559,412,736 bytes** maximum resident memory for the process. Linear extrapolation is approximately **80 minutes** for 1,000 splits, not a measured full-run duration. Code:354 retains every split's arrays, adding roughly a gigabyte at full size; a full-size peak-memory bound remains unmeasured. Stream sums/counts and identity-weight ranges if resource limits require it.

Earlier finding **1** is addressed by Protocol:46–48,181–182. Finding **7** is substantially addressed by 140–154 and 157, subject to findings 1–2 and 8 above. Earlier findings **10/11** concern `11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified`: Protocol:177–186 consistently defers live execution and separately admits later records, but does **not** establish keyed-evidence or leakage-audit completion. That live README:32,74,84–88 still lacks the full controls requested previously; current issue changes were not verified. “All 15 addressed” in the original results ledger overstates completion.

**Lock verdict:** Not safe to lock this revision. After the blocking and major fixes, deterministic counterexamples and synthetic checks pass, and the protocol's separately required review is satisfied, it can be locked as a conditional screening study; this review does not certify those future fixes or live deployment safety.
