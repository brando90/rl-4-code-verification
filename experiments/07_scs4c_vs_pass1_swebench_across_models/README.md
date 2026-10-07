# Experiment 07 — SCS4C, a smooth conjunctive score for general code, versus pass@1 on SWE-bench across models

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/07_scs4c_vs_pass1_swebench_across_models/README.md>

**TLDR:** VeriBench scores verified code with SCSC, which this project will call SCS4CV: the geometric mean of three factors, so any zero factor sinks the score while partial progress still counts. This experiment defines the general-code version, **SCS4C**, for SWE-bench, and tests whether it tracks the downstream metric, pass@1, across many models, and whether its partial credit carries information pass@1 throws away. Phase A uses only public SWE-bench Verified evaluation logs, so it needs no model calls. Phases B and C add a gold-patch differential factor on SWE-Bench Pro Verified and test SCS4C as an RL reward. Owner: Emily (@emxia18). Status: see [results.md](results.md).

Created: 10-07-2026. Owner: Emily (@emxia18), assigned by Brando on 10-07-2026; Lethan (@lethan3) walks her through VeriBench's SCSC. Phase A executor: a Claude Code worker on SNAP dispatched for Brando.

## Origin

- **Azalia Mirhoseini (thesis committee):** show that the metrics "not just correlate with downstream evals, but also can help guide designing better environments, feedback loops for model test time scaling … or as a reward for model fine tuning (e.g. in an RL setup)" ([email](../04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/sources/email_supplied.md)).
- **Brando, weekly notes 10-05-2026 and 10-07-2026:** write "scs4c" for the most recent SWE-bench, check whether it tracks the downstream eval (pass@1), and rename VeriBench's SCSC to SCS4CV ("smooth conjunctive score for code verification").
- **Factor choice (Brando and Claude, 10-07-2026):** Brando proposed the geometric mean of docstring, tests, property-based tests and fuzzer tests. The adopted definition keeps the form and the behaviour factors but drops the docstring from the product and splits tests into fix and no-regression parts; reasons below.

## Definition

Per artifact (one patch for one task), after the agent has stopped, with gold artifacts never visible to the agent:

```
G      = 1 if a nonempty patch applies (phase B: and the package installs and imports); otherwise SCS4C = 0
T_fix  = fraction of the report FAIL_TO_PASS tests that pass (phase A)      (does it fix the issue)
T_keep = fraction of the report PASS_TO_PASS tests that pass (phase A)      (does it break nothing)
D_gold = fraction of frozen generated inputs (property-based and fuzzed) to the functions the gold patch
         changes on which the patch behaves like the gold patch (same value, or same exception type)
SCS4C   = G · (T_fix · T_keep · D_gold)^(1/3)        (full, phases B and C)
SCS4C-T = G · (T_fix · T_keep)^(1/2)                 (tests only, phase A)
```

- **Gate, not factor.** When the patch does not apply or import, no test can run: the score is 0 and the factors are recorded as not run, never as invented failures (the same convention as VeriBench's compile gate and [experiment 06](../06_swebench_lite_factor_feedback_matched_budget/PROTOCOL.md)). A pass/fail factor inside a geometric mean would inflate every working patch: with factors multiplying to 0.125, a gate gives 0.50, a fourth factor 0.59. An infrastructure failure (the gold patch also fails to import) is unmeasured and rerun, not 0.
- **System score.** The geometric mean of the gated factor means over a common measured cohort, as for VeriBench (decision D-009). The mean of per-artifact scores is a separately labelled diagnostic; per-artifact scores are the repair-feedback and RL-reward unit.
- **Denominators.** SWE-bench's official report for each artifact lists the FAIL_TO_PASS and PASS_TO_PASS tests the harness ran; those lists are the denominators, so `resolved` is exactly T_fix = T_keep = 1 for a usable patch. Explicitly empty test lists are vacuously 1; absent test-status groups are unmeasured. Phases B and C use their own frozen gold test lists.
- **Why no docstring factor.** A docstring is not part of a SWE-bench deliverable and has no gold counterpart; scoring it needs a validated judge; and because any zero sinks a geometric mean, a correct fix without a docstring would score 0, which breaks tracking pass@1 and rewards docstring padding. A judged natural-language specification coverage score may be reported beside SCS4C, never inside it, and only after judge validation.
- **Mapping to SCS4CV.** VeriBench's factors are two internal-consistency checks of the agent's artifact (its tests typecheck; its stated theorems are kernel-proved) and one gold-coverage factor judged by a model (formal specification coverage). VeriBench could not run gold tests on agent code (Python to Lean gave type errors, not evidence). SWE-bench can: same repository, same language. So SCS4C's gold-referenced factors are mechanical, with no judge.
- **Naming.** The family is the smooth conjunctive score. SCS4CV is VeriBench's SCSC; new prose writes "SCS4CV (formerly SCSC)" while frozen evidence, paper versions and code identifiers keep `scsc`. SCS4C is the general-code member. Decision D-010 already labels the SWE-bench aggregate "a new proxy, not VeriBench SCSC".

## Goal, hypotheses and decision criterion

Does SCS4C track pass@1 across models, and does its partial credit carry capability information that pass@1 discards? Because `resolved` implies T_fix = T_keep = 1, a high correlation between SCS4C and pass@1 is guaranteed in part by construction; the informative tests are H1b and H2. Thresholds are agent-suggested and locked in [PROTOCOL.md](PROTOCOL.md) before cross-system analysis; that protocol discloses the single pre-lock format-check cell and prior leaderboard exposure.

| ID | Question | Prediction (frozen) | Verdict rule |
|---|---|---|---|
| H1 | Construct check: across systems, does SCS4C-T rank like pass@1? | Spearman ≥ 0.90 | Reported, not evidence of usefulness |
| H1b | Does a system's partial credit on the tasks it failed track its pass@1? | Spearman > 0, 95% task-bootstrap interval excludes 0 | Positive: partial credit carries capability signal. Interval covering 0: no evidence. Negative: partial credit misleads |
| H2 | On held-out tasks, does SCS4C-T measured on 50 tasks predict pass@1 on the remaining tasks better than pass@1 on the same 50 tasks? | Median Δ > 0 and Δ > 0 in at least 60% of 2,000 random splits | Positive: smoother, better small-sample ranking. Otherwise: no ranking advantage |
| H3 | How much reward signal does partial credit add? | Descriptive | Share of unresolved artifacts with SCS4C-T > 0 |

**What follows.** H1b and H2 positive: SCS4C-T already adds signal, proceed to phase B and C. H1b positive, H2 not: partial credit is informative but not a better ranker; phase C (reward) is still justified. H1b null or negative: test-only partial credit is uninformative, and phase B must show that D_gold adds what tests do not.

## Phases

| Phase | What | Model calls | State |
|---|---|---|---|
| A | SCS4C-T versus pass@1 across every public SWE-bench Verified submission with per-test logs (about 180 systems × 500 tasks) | None | Protocol locked; dispatch reported, launch receipt unverified |
| B | Full SCS4C (with D_gold) on SWE-Bench Pro Verified (731 tasks), a panel of at least 6 models from at least 3 families in each vendor's own agent, through Vals Valkyrie | Valkyrie (D-108) | Designed, not admitted |
| C | SCS4C as an RL reward: at group size 8, mixed-group share and ρ/H under SCS4C versus binary `resolved` on screened training environments disjoint from evaluation, then pass@1 on SWE-Bench Pro Verified | Self-hosted or Valkyrie | Designed, not admitted |

**Phase B admission** requires phase A's results, a frozen D_gold harness that passes its controls on at least 90% of tasks (gold versus gold agrees on at least 99% of inputs; base versus gold disagrees on at least one input, so the harness can see the bug), a verified Valkyrie benchmark service for SWE-Bench Pro Verified, and a model × task manifest with a receipt per cell. **Phase C** reuses the ρ–H probes of experiments 02 and 03; candidate training pools (for example SWE-Gym, SWE-smith or R2E-Gym) must be verified and screened against the evaluation set first.

## Structure

```
07_scs4c_vs_pass1_swebench_across_models/
├── README.md          ← this design doc
├── PROTOCOL.md        ← phase A protocol, locked before any outcome is read
├── results.md         ← live results and status
└── expt_v1/           ← phase A
    ├── cc.md              ← SNAP worker prompt
    ├── fetch_e07.py       ← gold lists + public per-instance report.json files
    ├── analyze_e07.py     ← primary H1, H1b, H2, H3 and validity checks
    ├── forecasts/         ← frozen phase A forecast (rl4cv.forecast)
    └── results/           ← committed summaries; raw logs stay on the host
```

The worker still implements GitHub-hosted log adapters and the one-system-per-base-model sensitivity in `expt_v1/cc.md` before publishing results. Invalid or empty cohorts and undefined split correlations produce explicit unavailable results, and every declared cell has a receipt.

The metric itself lives in [`src/rl4cv/scs4c.py`](../../src/rl4cv/scs4c.py) (tested in `tests/test_scs4c.py`) so phase C can use it as a reward.

## Dependencies

- Public data: [SWE-bench/experiments](https://github.com/SWE-bench/experiments) at commit `40f164d5`, its unsigned S3 bucket `swe-bench-submissions`, and the [SWE-bench Verified](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified) task list at revision `c104f840`.
- Phase B: [SWE-Bench Pro Verified](https://arxiv.org/abs/2609.08149) (731 tasks, September 2026); Valkyrie under D-108.
- Related: [experiment 06](../06_swebench_lite_factor_feedback_matched_budget/README.md) (decomposed public feedback during repair; its harness-validity failures inform phase B's controls) and [experiment 04](../04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/README.md) (the VeriBench factor work).

## Status

| Step | Status | Notes |
|---|---|---|
| Definition and design | Done (10-07-2026) | this file |
| Phase A protocol and frozen forecast | Done (10-07-2026) | [PROTOCOL.md](PROTOCOL.md), `expt_v1/forecasts/` |
| Phase A run on SNAP | Dispatch reported; execution unverified (10-07-2026) | No launch receipt recorded; [results.md](results.md) |
| Phases B and C | Designed, not admitted | needs phase A, D_gold harness controls, Valkyrie service |
