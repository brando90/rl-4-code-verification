# Do VeriBench components help choose better repairs and training environments

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/README.md>

**TLDR:** Test whether access to VeriBench’s three components improves decisions and held-out verification at matched cost. Start by validating an independent reference-success outcome, then compare feedback policies; reuse the existing environment-scaling experiments for reinforcement learning.

**Created:** 10-05-2026. **Execution:** existing-artifact audit complete on SNAP; intervention, new proof and training runs not started. **Thesis inclusion:** intended, conditional on defensible evidence.

**Goal:** turn Azalia Mirhoseini's suggestion into a falsifiable test of the practical value of interpretable evaluation.
**Main uncertainty:** do the components identify a useful intervention beyond information already available in the aggregate and compiler feedback?
**Confidence:** moderate in the experiment's value; improvement is unmeasured. **Importance:** 9/10, agent-proposed because it links the thesis's evaluation and training contributions.

## What Azalia may mean

The email supports three applications: better environments, feedback for additional inference-time computation, and rewards for fine-tuning. It does not specify another benchmark, a causal design, or which components to optimize. Our interpretation below is a proposal to confirm with her, not a claim about her unstated intent.

The Smooth Conjunctive Score for Code verification (SCSC) **already is** a downstream evaluation outcome. The user's “SBCS” is treated as a spelling variant, not a new metric. Its per-artifact score is

`SCSC = (IC_tests × IC_proofs × FSC)^(1/3)`.

Here `IC_tests` is internal consistency with the artifact's own tests under the pinned scorer; `IC_proofs` is the fraction of its stated theorems accepted under the strict proof policy; and `FSC` is formal specification coverage of the reference requirements, estimated by the validated judge. Exact operational gates differ between benchmark conditions, so retain each scorer's contract. Aggregation needs explicit reconciliation before a new scored run: this repository’s `src/rl4cv/veribench/summarize.py` averages per-artifact geometric means, while the current VeriBench paper defines a geometric mean of dataset-level factor means. These differ. Preserve each historical convention, label both if shown, and freeze the authoritative reporting convention before new intervention outcomes. This audit reports availability counts only.

When all three factors are positive, increasing one while keeping the others fixed necessarily increases this score. If another factor is zero, the product remains zero. That is algebra, not the thesis result. It does not tell us which edit will work, whether it will damage another component, how much it costs, or whether an agent can raise its score by deleting difficult requirements.

**The thesis question:** given the same initial artifact and total budget, does revealing the decomposition help choose an intervention that yields better held-out verification outcomes than aggregate-only feedback or ordinary verifier feedback?

For example, an artifact with strong self-consistency but weak requirement coverage calls for a different repair from one with broad statements but unproved theorems. The aggregate may be identical. Whether a model can exploit that distinction effectively is empirical. With a zero factor, the aggregate also hides progress on the other factors; that makes the hypothesis plausible, not guaranteed.

## Three claims with different evidence

| Claim | Experiment | What would not establish it |
|---|---|---|
| Components explain different failure modes | Fixed-reference outcome audit; inspect disagreements and missing requirements | Correlating a geometric mean with its own factors |
| Components help choose actions | Randomized, cost-matched inference-time repair comparison on held-out tasks | Before/after change without a control or a bigger repair budget |
| Components help design learning environments | Screened training pools, frozen reward/environment choice, held-out checkpoint comparison | Training on VeriBench, selecting a checkpoint on its scores, or reward inflation |

An external benchmark such as SWE-bench is optional. The independent outcome can be an additional fixed-reference measurement on VeriBench artifacts. It is independent of the candidate's self-chosen requirements, not statistically independent of SCSC. Shared references/judges can still induce dependence and must be disclosed.

## Priority and sequence

Scores are predicted priorities, not measured effect sizes.

1. **[p 9/10] Validate the auxiliary outcome and audit existing evidence**, because a bad endpoint would invalidate both correlation and intervention claims; the first audit uses no new model calls.
2. **[p 9/10] Run a controlled inference-time repair study**, because it tests actionable interpretation more cheaply than training and isolates feedback information.
3. **[p 8/10] Reuse `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics` for environment and reward selection**, because that work already owns the training comparison and should not be duplicated.
4. **[p 6/10] Add the proposed specification-equivalence diagnostic**, because implication may be useful but adapter and proof-search failures limit interpretation.
5. **[p 4/10] Explore transfer to repository repair benchmarks**, after the within-VeriBench causal result; a SWE-bench factorization requires its own construct validation.

## First study and deliverables

Read [PROTOCOL.md](PROTOCOL.md) for the locked existing-artifact audit, [PLAN.md](PLAN.md) for all planned comparisons, and [METRICS.md](METRICS.md) for endpoints and equivalence. [results.md](results.md) contains current verified status, and [CKPT_azalia.md](CKPT_azalia.md) contains continuation state.

```text
04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/
  README.md                 interpretation, scope, priorities
  PLAN.md                   feedback, environment, reward and thesis designs
  METRICS.md                pass@1 and formal-specification comparison
  PROTOCOL.md               locked retrospective inventory
  sources/                  supplied email and retrieved source map
  expt_v1/cc.md              continuation instructions
  expt_v1/audit_existing.py  deterministic feasibility audit
  expt_v1/input_manifest.json
  expt_v1/results/           audit and execution receipts
  results.md                 live evidence
  CKPT_azalia.md              resume record
```

## Existing work and dependencies

- `01_small_open_models_veribench_v1_single_call_baseline`: reusable small-model outputs; its report suggests a severe score floor. It is prior exploratory evidence, not a new independent forecast.
- `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_c_reward_channel_for_fsc_kernel_vs_judge`: owns reward-channel training. This folder supplies the interpretation/control-policy question and auxiliary endpoints.
- `03_rl_on_never_solved_lean_prompts_binary_vs_dense_reward_eval_vbv1`: owns the initial zero-success training question; coordinate datasets and report overlap.
- VeriBench's `103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge`: modern saved scoring rows. The version-2 condition is a five-project study, not evidence for all future version-2 projects.
- VeriBench's `75_J1_validating_formal_spec_judge_train_val_test/prover_diagnostics`: prior adapter and proof replay work; strict kernel trust is unresolved for the complete historical set.
- Current thesis sources and provenance: [sources/context.md](sources/context.md). The `rl-env-scaling` local main branch is a planning checkout; submitted-paper numbers are not independently verified here.

No VeriBench task, reference or derived text enters training, warm starts, controller tuning, environment selection or checkpoint selection. An inference policy is fixed using screened external validation tasks before evaluation. Evaluator-only reference access is distinct from feedback delivered to a solver.
