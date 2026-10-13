# Light quality-assurance review: experiment 14 draft at `1dad751`

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/reviews/light_qa_codex_gpt6_astra_ultra_10-12-2026.md>

This is the intended repository address; this review was written locally, not committed or published.

**TLDR:** FAIL before locking: numerical integration can materially distort accepted forecasts, and failed within-half fits can evade or influence the verdict gate. Split replay, data isolation, analytic derivatives, and the finite-data rank bootstrap passed the checks below; additional findings concern promotion gates, statistical interpretation, and failure reporting.

**Reviewer:** Codex `gpt-6-astra`, reasoning effort `ultra`, observed in the active session's `turn_context` metadata, not inferred from the requested filename. Runtime metadata also reports `approval_policy=never` and `sandbox_policy.type=danger-full-access`. One bounded numerical-validation assistant used the same observed model and effort within this review; there was no second review round.

**Reviewed revision:** `1dad75118def55fa35b0856c53cf8662f0727c53`, detached checkout. **Date:** 10-12-2026. **Role:** review only; no fixes, tracked-file edits, commits, pushes, or structural refactoring. The builder recorded in `results.md` is Claude Code `claude-opus-5-5`, effort `max`, Vals profile.

The experiment is `14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems`. Paths beginning `expt_v1/` below are relative to that experiment directory. Item response theory is abbreviated IRT; the one- and two-parameter logistic models are 1PL and 2PL; the three-category graded response model is GRM3; expected a posteriori ability is EAP. Mean absolute error is MAE, standard deviation is SD, standard error is SE, and confidence interval is CI. P1 and P2 are the protocol's primary rank and level rules; Q1 is its overall continuation question.

## Scope and checks run

Read `PROTOCOL.md` first, then the experiment's implementation, README, results ledger, run instructions, tests, experiment 07's relevant protocol/results/code, and `src/rl4cv/{scs4c,forecast}.py`. No real response matrix was loaded, no real-data IRT model was fitted, and no new real-data Q1 statistic was computed. The previously published experiment 07 results were read. Its reported real-data reproduction was not independently rerun during this review.

All Python checks disabled bytecode writes. The full synthetic run replaced only `write_outputs` with an in-memory serialization/render check, so the review file is the only file written. No synthetic result is evidence about the real cohort.

Commands ran from `/lfs/skampere1/0/brando9/rl4cv_e14_qa` with Python `/lfs/skampere1/0/brando9/uv_envs/rl4cv_e14/bin/python`, NumPy 2.2.6, and SciPy 1.16.3:

```bash
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=src \
  /lfs/skampere1/0/brando9/uv_envs/rl4cv_e14/bin/python \
  -m pytest -q -p no:cacheprovider tests/test_e14_irt.py
```

**Outcome:** 11 passed in 1.65 seconds.

The full pipeline used this in-memory invocation (the callback also printed validation counts):

```bash
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  /lfs/skampere1/0/brando9/uv_envs/rl4cv_e14/bin/python -u - <<'PY'
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path('experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/expt_v1').resolve()))
import analyze_e14 as a
def validate_outputs(out_dir, analysis, rows, fits, data):
    normalized = a.strict(analysis)
    text = json.dumps(normalized, allow_nan=False)
    rendered = a.render(normalized)
    print(len(text), len(rendered), {str(k): len(v) for k, v in rows.items()})
    print(analysis['validity'])
    print(analysis['primary_2pl_n50']['rank_bootstrap']['draws'],
          analysis['settings']['bootstrap_draws'])
a.write_outputs = validate_outputs
sys.argv = ['analyze_e14.py', '--synthetic', '2', '--splits', '40', '--boot', '50', '--workers', '8']
a.main()
PY
```

**Outcome:** exit 0, 112.0 seconds of analyzer time; serialization and rendering succeeded; 360 arm/split rows at each of four sizes; all 30 primary fold fits converged; all 320 primary within-half fits converged; the Rasch common-parameter check had zero nonzero rank differences in all 160 splits. Fold-seed and 73-system sensitivity paths completed. The rank bootstrap actually used 2,000 draws despite `--boot 50` (finding 7).

Additional commands used the same interpreter and thread/bytecode settings with Python here-documents, imported only the modules above, and performed these in-memory checks:

| Check | Outcome |
|---|---|
| Average ranks against `scipy.stats.rankdata`, including resampled duplicate columns, at 1, 2, 5, and 164 systems | Maximum difference 0 at every size |
| `bootstrap_rank` against scalar `rl4cv.scs4c.spearman`, 100 identical resamples of 12 systems across 7 synthetic splits, seed 911 | Median interval endpoints agreed within `3e-17`; share intervals and both tail probabilities agreed exactly |
| Analytic versus central finite-difference gradients, 17 systems × 9 items | Maximum absolute differences: 1PL `6.77e-11`, 2PL `7.64e-11`, GRM3 `1.93e-10` |
| Category probabilities and sufficient-statistic versus full-likelihood posteriors | Probability sums within `2.23e-16` of one; posterior differences at most `9.37e-17` |
| Perturb one synthetic target's half-B responses, keep its reference fit fixed, compare its six level predictors | Exactly zero forecast changes; reference fitting inputs for that target's fold were identical |
| Perturb every synthetic system's half-B responses and repeat the actual within-half 2PL fit | Bitwise-identical EAP and posterior SD |
| Call `main()` without a forecast, with `load_real` replaced by a function that raises if reached | Correctly refused with `STOP: the frozen forecast is missing or its hash does not verify`; loader was not reached |
| Numerical integration, nonfinite-fit bookkeeping, zero-SE pairs, skewed sign-flip null, and mocked Rasch-stop path | Counterexamples below |
| `git diff --check`; final tracked-file diff and checkout revision | Passed; tracked files unchanged at the reviewed revision |

The vectorized rank/bootstrap implementation is correct for the finite inputs tested, including duplicated systems. It resamples whole system trajectories and re-ranks each split, rather than treating 2,000 overlapping splits as independent systems. The generator burn order agrees with experiment 07: H1 task draws, H1 system draws, H1b task draws, H1b system draws, then the four permutation blocks. System insertion order in 07 is sorted submission order; experiment 14 preserves it and takes task order from `common_cohort_ids`. These are source/test findings, not a fresh real-data reproduction.

The rank-versus-level design separation is sound for the stated conditional, panel-based question. Within-half fits slice only A; fold fitting excludes the target's entire fold; both controls use reference systems only; fold assignment uses a seeded permutation without outcomes; rounding is applied after forecasting. The shared-parameter Rasch check is intentionally not a leakage-free level arm, and the code correctly excludes its level results. The GRM3 ordering, transformed-parameter priors, marginal-likelihood derivatives, EAP calculation, and posterior-predictive averaging are internally consistent.

## Numbered findings

### 1. CRITICAL — Optimization convergence does not establish grid accuracy; accepted forecasts can be substantially truncated

**Locations:** `expt_v1/irt_e14.py:10`, `expt_v1/irt_e14.py:116`, `expt_v1/irt_e14.py:147`; `PROTOCOL.md:47`, `PROTOCOL.md:52`, `PROTOCOL.md:118`.

**Problem:** Both fitting and scoring use a fixed 401-node grid on [−6, 6], with no resolution, support, or endpoint-mass validation. The gradient gate checks only the discretized objective. A sharp posterior can be under-resolved, and a target outside the reference panel can have substantial posterior mass beyond the grid. This follows the written grid specification, but the specification lacks a numerical validity gate.

**Evidence:** Fit 2PL to 148 all-zero synthetic reference systems × 424 items. The fit is accepted with maximum absolute gradient `2.95784e-11`; each item has slope `1.03942710` and intercept `−5.98490554`. Score one all-one target on 50 items and forecast the other 374, retaining exactly the same fitted parameters:

| Scoring grid | EAP | Posterior SD | Held-out forecast |
|---|---:|---:|---:|
| 401 nodes, [−6, 6] | 5.95836573 | 0.05261439 | 0.55187543 |
| 8,001 nodes, [−12, 12] | 7.51656142 | 0.36833571 | 0.85537107 |
| 16,001 nodes, [−24, 24] | 7.51656142 | 0.36833571 | 0.85537107 |

The original posterior places 40.9% of its mass on the upper endpoint, and the forecast changes by 0.303496 on the pass@1 scale. This is a valid synthetic reference-panel/target configuration, not a claim about its prevalence in the real data.

There is also a fitting-resolution counterexample without a constant reference panel. Let `theta = norm.ppf((arange(164)+.5)/164)`, `b = linspace(-2,2,424)+.011`, and `x = (theta[:,None] > b)`. The accepted coarse fit has maximum gradient `1.74153e-8`; evaluating its parameters on 4,001 nodes on the same support gives `5.73802e-4`, exceeding the protocol's `1e-4` criterion. A 1,601-node refit changes 50-item/374-item forecasts by up to `0.000143277`. Thus the optimizer's acceptance does not bound either integration or forecast error.

**Recommended fix:** Add and freeze a deterministic integration-accuracy gate before the real run. Check both finer resolution and wider support for the primary fitted objectives and scored posteriors; record endpoint mass, gradient discrepancies, and maximum changes in EAP, SD, and forecasts. Deterministically refine/refit, or mark the result INCONCLUSIVE when the locked numerical limits are exceeded. A concrete starting specification to validate synthetically is forecast/EAP/SD differences at most `1e-6`, endpoint mass at most `1e-8`, and the existing `1e-4` gradient criterion also holding on the finer grid; these are proposed numerical tolerances, not validated constants. Prespecify a refinement cap and require the primary decision to survive the accepted numerical comparison. Increasing node count on [−6, 6] alone does not fix support truncation.

### 2. CRITICAL — Failed within-half fits can be counted as converged or supply the decisive positive split

**Locations:** `expt_v1/analyze_e14.py:190`, `expt_v1/analyze_e14.py:218`, `expt_v1/analyze_e14.py:524`, `expt_v1/analyze_e14.py:614`; `PROTOCOL.md:91`.

**Problem:** `_within_half_job` discards the fit's `converged` flag, and `within_half` counts failures with `grads > GRAD_TOL`. A NaN (not-a-number) gradient makes that comparison false, although `irt.fit` correctly declares the same fit unconverged. Moreover, the allowed ≤1% finite, unconverged fits are still scored and used without qualification in the primary rank rule. The latter follows the draft's tolerance but leaves the decision vulnerable to known-invalid fits.

**Evidence:** An in-memory runner returning two NaN-gradient fit records yields `fits=2`, `not_converged=0`, and `max_abs_grad_max=nan`. Passing this count into `q1_verdict` permits CONTINUE. Nonfinite ability outputs can also be silently removed by the scalar correlation's finite-pair filter, while the vectorized ranker has no equivalent nonfinite policy.

For finite failed fits, construct 2,000 rank differences: 1,199 converged positive splits, one unconverged positive split, and 800 converged negative splits, with the level rule false. `primary_verdicts` and `q1_verdict` return CONTINUE: the recorded share is 1,200/2,000 = 0.60, and one failure is within the 20-fit allowance. Replacing the failed split's arbitrary positive result by a nonpositive result makes P1 fail. The synthetic bookkeeping check reproduced this outcome.

**Recommended fix:** Preserve each fit's convergence flag; count `~isfinite(grad) | (grad > GRAD_TOL)` as failed, and explicitly validate parameters, posteriors, abilities, SDs, and forecasts before using them. Keep failure identities and counts in output. For the permitted finite failures, do not allow their provisional scores to establish P1: retain the 2,000-split denominator, report valid-result bounds, and mark P1 inconclusive whenever its decision depends on failed fits. An independently valid P2 can support continuation only under the explicitly frozen combined fit rule. Add focused tests for NaN gradients and a threshold-crossing failed split.

### 3. MAJOR — Zero-SE pairs are discarded, matched counts can differ, and undefined harmful rates become zero

**Locations:** `expt_v1/analyze_e14.py:367`, `expt_v1/analyze_e14.py:393`, `expt_v1/analyze_e14.py:398`, `expt_v1/analyze_e14.py:429`; `PROTOCOL.md:104`–`108`.

**Problem:** Every zero-SE paired contrast becomes NaN, including a candidate that beats its incumbent on every A task. `top_n` additionally excludes infinities. Consequently the nominally matched pass@1 gate can select fewer pairs than the IRT gate. The summary then uses `harmful_promotion_rate or 0.0`, converting an undefined rate from zero promotions to a measured zero.

**Evidence:** Two synthetic systems have A responses `[0]*50` and `[1]*50`, EAPs −2 and +2, posterior SDs 0.1, and B rates 0.8 and 0.2. The paired gain is +1 with SE 0. The code selects one scalar promotion and one IRT promotion, but zero paired-SE promotions and zero promotions in the gate supposedly matched to the one IRT promotion. It reports the matched harmful-rate difference as `−1.0`, with no defined CI: this subtracts an observed rate of 1 from an invented rate of 0. Directly passing a positive-infinite contrast to `top_n` also selects nothing.

**Recommended fix:** Prespecify the degenerate-contrast convention: positive gain/zero SE maps to +infinity, negative gain/zero SE to −infinity, and identical responses to a zero contrast for ordering (or an explicitly defined common eligibility rule). Make `top_n` preserve legitimate infinities and deterministic index tie-breaking. Assert the promised matched counts in every split; if eligibility prevents matching, report that comparison unavailable. Preserve `None` for any rate difference with a zero denominator instead of substituting zero. Test saturated pairs, identical-response pairs, exact matched counts, and zero-promotion summaries.

### 4. MAJOR — The sign-flip p-value is labeled as testing a weaker null than it supports

**Locations:** `PROTOCOL.md:81`; `expt_v1/analyze_e14.py:317`, `expt_v1/analyze_e14.py:343`.

**Problem:** The function's docstring correctly describes sign symmetry, but the protocol and exported `test` label say merely “zero mean difference.” Independent sign flipping requires exchangeability under sign changes; zero mean alone does not supply that property. Split-averaged differences of two absolute errors need not be symmetric. The plus-one Monte Carlo calculation is otherwise implemented correctly. The distinction also appears in the [SciPy paired permutation-test documentation](https://docs.scipy.org/doc/scipy-1.16.0/reference/generated/scipy.stats.permutation_test.html).

**Evidence:** A bounded difference distribution with value −0.01 with probability 0.99 and +0.99 with probability 0.01 has mean exactly zero. A sample of 164 independent systems is all negative with probability `0.99**164 = 0.1923853`. For that sample, the actual `signflip_p` with seed 17 and 10,000 flips returns `0.0000999900`. Thus even under independence, the claimed zero-mean null has configurations with at least a 19.2% rejection probability at a nominal 5% level. This is a mathematical/synthetic counterexample, not an estimate from the real cohort.

**Recommended fix:** Before locking, either label and interpret this as a sign-exchangeability/symmetry diagnostic everywhere, explicitly stating the assumption and keeping it separate from P2's bootstrap-CI decision, or replace it with a prespecified test targeting the mean under the stated system-resampling assumptions. Do not call the existing procedure a general zero-mean permutation test. Add a test ensuring the output's null description matches the implemented procedure.

### 5. MAJOR — A Rasch STOP retains a positive continuation outcome and returns success

**Locations:** `expt_v1/analyze_e14.py:597`, `expt_v1/analyze_e14.py:624`, `expt_v1/analyze_e14.py:915`–`927`; `PROTOCOL.md:123`.

**Problem:** The code notices a failed Rasch check only after the whole analysis has run. It removes the prose `q1_verdict`, but leaves `q1_continue`, primary rule booleans, and the interpretation flag available to forecast evaluation. It also returns normally, unlike the earlier STOP paths. A downstream consumer can therefore record a successful continuation prediction for an invalid analysis.

**Evidence:** Exercising `main` with entirely synthetic/mocked inputs, a mocked `run` returning one nonzero Rasch difference and `q1_continue=True`, and a mocked frozen prediction pointing to `q1_continue`, produced:

```text
status: STOP: Rasch common-parameter rank check failed (code defect)
q1_verdict: null
q1_continue: true
forecast outcome: true; note: event occurred
main_returned_normally: True
```

No real loader, fit, or statistic was invoked in this control-flow test.

**Recommended fix:** Propagate invalidity before evaluating any decision forecast. Preserve diagnostic measurements, but set all verdict-dependent outcomes to unavailable with a reason; do not translate an invalid experiment into either success or failure of the frozen prediction. Write the failure receipt and exit nonzero. Prefer stopping downstream analysis as soon as the Rasch check fails. Add a synthetic failure-path test covering the status, exit behavior, and frozen-forecast outcome.

### 6. MAJOR — Generated results omit the required level-win attribution and uncertainty scope

**Locations:** `expt_v1/analyze_e14.py:568`, `expt_v1/analyze_e14.py:625`, `expt_v1/analyze_e14.py:732`–`758`, `expt_v1/analyze_e14.py:794`; `PROTOCOL.md:82`, `PROTOCOL.md:92`.

**Problem:** The analyzer computes `level_win_beyond_reference_panel`, but `render` never reads or states it. Its headline always credits “2PL ability” when P2 wins, even if P1 fails and the linear-regression control is better. A control table later in the document does not apply the protocol's explicit attribution rule. The rendered primary intervals also omit the protocol's conditioning on the observed cohort and fitted parameters; only the promotion section mentions conditioning on selections.

**Evidence:** The source contains a single assignment to `level_win_beyond_reference_panel` and no renderer reference. `q1_verdict({'rank_holds': False, 'level_holds': True}, True, True)` unconditionally claims an ability advantage without consulting the control comparison. `render` contains no primary uncertainty-scope sentence. The protocol itself scopes the intervals substantially more carefully than the generated artifact.

**Recommended fix:** Render the interpretation flag immediately beside the overall verdict. In the level-only/control-not-beaten case, retain the protocol's CONTINUE decision but explicitly credit reference-panel calibration and say that additional item-level IRT information was not established. State beside the primary intervals that whole submissions are resampled with fitted parameters, fold assignments, reference-control fits, and task splits held fixed; these are not uncertainty intervals for a refitted learning procedure, unseen tasks, or new model families. Include both interpretation cases in a renderer check.

### 7. MINOR — Synthetic `--boot` and sign-flip settings do not control all resampling calls

**Locations:** `expt_v1/analyze_e14.py:317`, `expt_v1/analyze_e14.py:346`, `expt_v1/analyze_e14.py:606`, `expt_v1/analyze_e14.py:905`.

**Problem/evidence:** Python evaluates default arguments once. Changing global `BOOT` and `SIGNFLIPS` in `main` does not change the defaults of `bootstrap_rank(..., draws=BOOT)` or `signflip_p(..., draws=SIGNFLIPS)`. In the completed `--synthetic 2 --splits 40 --boot 50` run, settings declared 50 bootstrap draws while the rank-bootstrap result recorded 2,000. The analogous sign-flip default remains 10,000 despite the synthetic setting of 1,000. This affects synthetic runtime and provenance, not the normal real run's prescribed counts.

**Recommended fix:** Pass `draws=BOOT` and `draws=SIGNFLIPS` explicitly at call sites, or resolve a `None` default at runtime. Construct test-description strings from actual counts rather than hard-coding 2,000/10,000. Verify synthetic output settings agree with executed counts.

## Reproducing the numerical counterexamples

The following is an equivalent compact version of the numerical assistant's executed here-document. It reads only code, fits only constructed arrays, and writes nothing:

```bash
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  /lfs/skampere1/0/brando9/uv_envs/rl4cv_e14/bin/python - <<'PY'
import sys
import numpy as np
from scipy.special import logsumexp
from scipy.stats import norm
sys.path.insert(0, 'experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/expt_v1')
import irt_e14 as m
def grid(lo, hi, count):
    m.GRID = np.linspace(lo, hi, count)
    m.LOG_PRIOR_W = -.5*m.GRID**2 - logsumexp(-.5*m.GRID**2)
theta = norm.ppf((np.arange(164)+.5)/164)
b = np.linspace(-2, 2, 424)+.011
x = (theta[:, None] > b).astype(float)
f = m.fit('2pl', [1-x, x], maxiter=2000)
print('coarse gradient', f['max_abs_grad'])
grid(-6, 6, 4001)
print('fine gradient', np.max(np.abs(m.objective(f['x'], '2pl', [1-x, x])[1])))
grid(-6, 6, 401)
z = np.zeros((148, 424))
f = m.fit('2pl', [1-z, z], maxiter=2000)
target = np.ones((1, 424))
for lo, hi, count in [(-6, 6, 401), (-12, 12, 8001), (-24, 24, 16001)]:
    grid(lo, hi, count)
    scorer = m.Scorer(f)
    post = scorer.posterior([1-target, target], np.arange(50))
    mean, sd = m.eap(post)
    forecast = scorer.forecast(post, np.arange(50, 424))
    print(lo, hi, count, mean[0], sd[0], forecast[0], post[0, -1])
PY
```

These checks establish failure modes, not their frequency or their effect on the sealed real-data verdict. Fixes belong to the driver; this review applies none and requests no additional review round.

VERDICT: FAIL
CRITICAL_ISSUES: 2
MAJOR_ISSUES: 4
FIXES_APPLIED: 0
STRUCTURAL: SKIP
SUMMARY: Fix numerical-integration validation and failed-fit decision handling before locking the protocol. The synthetic pipeline and core formula/replay checks pass, but promotion, null-hypothesis, STOP-state, and result-interpretation defects also require correction; no real-data outcomes were computed.
