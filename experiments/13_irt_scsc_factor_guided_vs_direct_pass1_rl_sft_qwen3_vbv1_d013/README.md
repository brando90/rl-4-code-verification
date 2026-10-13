# Experiment 13 — Does RL guided by a factored model of the evaluation (SCSC factors or a conjunctive IRT model) beat RL on the strict pass@1 reward? Qwen3-4B SFT on VeriBench V1 (D-013)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/README.md>

**TLDR:** This tests the crux of SCSC ↔ evals ↔ RL. At matched compute, does reinforcement learning (RL) guided by a factored, interpretable model of the evaluation improve held-out strict pass@1 more than RL on the strict reward itself? No experiment has tested this yet: experiment 09 failed its technical gate with zero optimizer updates.

A new zero-call measurement shows a naive test would have been null by construction. On all 15 finished supervised fine-tuning (SFT) checkpoints of experiment 08, VeriBench's kernel-checked factors equal the strict pass/fail outcome, so a factored kernel reward adds no learning signal.

The plan has three phases:

- **Phase 0:** build per-declaration partial-credit factors. Lean v4.22.0 reports every theorem's status even when one proof fails.
- **Phase 1:** fit and validate a conjunctive item response theory (IRT) model that predicts held-out pass@1 and pass@k.
- **Phase 2:** run four RL arms from the Qwen3-4B SFT checkpoint: strict reward, SCSC-style factored reward, IRT-guided reward and prompt sampling, and a placebo dense reward.

Status (10-13-2026): **version 2 RUNNING under A1; R0 attempt 2 PASS, 30/30**. Historical oracle value/status and complete components matched all 30 fixtures; the required repository suite passed 283 tests with 23 unrelated skips. [Attempt-2 report](expt_v2/RESULTS_R0_attempt_2.md). R1 train-only diagnostic is next. Attempt 1 remains failed and unchanged; version 1 evidence remains byte-identical.

- **Created:** 10-09-2026 by Claude Code (`claude-opus-5-5`) for Brando.
- **Owner:** version 2 skampere1 owner resumed under Amendment A1; the Mac master retains the parent experiment.
- **Terms:**
  - An *arm* is one condition being compared.
  - *Strict* is `kernel_binary`: the file typechecks, has at least one example, states at least one theorem, every stated theorem is a proved theorem with allowed axioms, and none is vacuous.
  - SCSC = (IC_tests · IC_proofs · FSC)^(1/3), where FSC is formal specification coverage.
  - GRPO is group relative policy optimization.

## Origin

- **Brando, 10-09-2026 (chat):** "It seems crucially we have not shown any factored decomposed model (irt or scsc) helps more than optimizing the downstream eval...this is surprising because the features should tell us what to optimize, so I really want to make an excellent experiment plan for this so that it actually works. Is there such an experiment already? If not make it."
- **His other request, same message:** use the SFT models "to make 'irt interpretable models' that improves our RL runs (and alpha apollo, hebe, diana)".
- **The 10-08-2026 meeting** ([record](../meetings/oct_7_2026/oct_7_2026.md)) set the order: first show a factorized measure correlates with the downstream metric, then optimize it, and automate the factors with IRT later.
- **Literature scan and zero-call tests:** the VeriBench idea page [IRT for SCSC factors](https://github.com/brando90/veribench/blob/main/experiments/ideas/irt_latent_factors_for_scsc_vs_pass1_and_rl_guidance/README.md). This experiment takes over its RL-facing tests.

## Is there already such an experiment? No

| Experiment | What it asks | Why it does not answer the crux |
|---|---|---|
| [09](../09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/README.md) | Strict vs SCSC reward vs SCSC plus disclosed factors, Qwen3-1.7B SFT, GRPO | FAILED_TECHNICAL_GATE 10-08-2026: 4/4,077 sampled tokens fell outside the trainer's recomputed top-k/top-p support, and 367/4,073 log-probability errors exceeded 0.05, so there were zero optimizer updates. By the measurement below, its kernel factors would also have equaled its strict reward |
| [03](../03_rl_on_never_solved_lean_prompts_binary_vs_dense_reward_eval_vbv1/README.md) | Binary vs dense reward on never-solved prompts | Designed, not run; uses the same uninformative kernel factors; no placebo |
| [04](../04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/README.md), [06](../06_swebench_lite_factor_feedback_matched_budget/README.md) | Factor-guided repair; SWE-bench factor feedback | Blocked before any model update |
| [07](../07_scs4c_vs_pass1_swebench_across_models/README.md) | Does SCS4C track pass@1 across 164 SWE-bench systems? | Evaluation only. Its H2 (ranking systems from 50 tasks) failed, which says nothing about optimization |
| [10](../10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/README.md), [11](../11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified/README.md) | AlphaHebe promotion gate replay; live loop | Harness edits, not weights; designed or blocked |
| [12](../12_scsc_vs_hidden_gold_tests_vbv1_across_systems/README.md) | Does SCSC track hidden gold-reference tests? | Validity of the metric, not optimization (running) |
| [Curriculum design note](../meetings/oct_7_2026/item_factor_matrix_experiment_design.md) | Aligned vs permuted factor-informed task sampling | Not launched; no IRT; uses the same kernel factors |

So the crux has never run with a working trainer. With today's factors it could not have shown a difference.

## Why a factored reward could not help yet (zero model calls)

[`design_evidence/factor_redundancy_e08.py`](design_evidence/factor_redundancy_e08.py) reads experiment 08's validation cells (135 tasks × 8 samples per system) and writes [`factor_redundancy_e08.json`](design_evidence/factor_redundancy_e08.json).

| System | Strict pass rate | Tasks with mixed strict outcomes (GRPO signal) | Tasks where only the kernel smooth score varies | Compiled but not strict | No Lean extracted | Lean extracted, does not typecheck |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3-4B Base | 0.003 | 3/135 | 0/135 | 2 | 167 | 908 |
| SFT 1.7B, full schedule | 0.049 | 20/135 | 0/135 | 0 | 183 | 844 |
| SFT 4B, full schedule | 0.093 | 32/135 (Wilson 95% [0.173, 0.315]) | 0/135 | 0 | 134 | 846 |
| SFT 8B, full schedule | 0.096 | 32/135 | 0/135 | 0 | 106 | 870 |

- **The factors collapse to one bit.** Across all 15 finished SFT checkpoints, the kernel smooth score `sqrt(IC_tests · IC_proofs)` varies within a group of constant strict outcomes on 0/135 tasks; the one exception is 1/135 at SFT 8B, 12.5% of the schedule. Compiled-but-not-strict samples number 0 on 14 of the 15 checkpoints.
- **Why they collapse.** The fine-tuned models never write `sorry`, and one failed proof makes the whole file fail to typecheck. That zeroes IC_tests, and IC_proofs with it. So a file either passes everything or scores 0 on both kernel factors.
- **SCSC adds nothing for failures.** It also contains FSC, but FSC is compile-gated in rewards (D-003), so SCSC is 0 on every strict failure. It grades coverage only among strict successes, and gives no partial credit where RL lacks signal.
- **Where the signal is missing.** For SFT 4B, 846 of 1,080 samples are Lean files that fail to typecheck, and 134 are cut off at the output cap. Under the strict reward, 103 of 135 tasks give GRPO zero gradient.
- **The fix is available.** [`design_evidence/lean_partial_credit_probe.lean`](design_evidence/lean_partial_credit_probe.lean) and [its output](design_evidence/lean_partial_credit_probe_output.txt) show Lean v4.22.0 keeps elaborating after a failed proof. The failed theorem depends on `sorryAx`; the other theorem depends only on `propext`; a theorem after the failure still elaborates. One compile therefore gives per-declaration status: implementation and examples, each theorem's proof, and how far the file elaborates.

## Reviewed execution design

The one requested Codex `gpt-6-astra` / `ultra` review has reconciled the plan and receipt harness; see [review findings](expt_v1/REVIEW.md). The original design evidence above remains historical. No new factor measurement, fitted model, training update or test evaluation is claimed.

[PROTOCOL.md](PROTOCOL.md) is the authoritative prospective specification. It separates the immutable strict scorer from experimental declaration fractions, models strict probability with conditional hurdles, and defines arm C as a train-only weighted reward. Its typed receipt harness checks exact source/cell identities. A valid token-cap completion remains eligible under the existing strict scorer; at least one example is required.

The phase plans provide [scorer controls](expt_v1/PHASE0_CONTROL_PLAN.md), [model validation](expt_v1/PHASE1_IRT_PLAN.md) and [reinforcement-learning execution](expt_v1/PHASE2_MATCHED_RL_PLAN.md). A/B/P share uniform prompt order; C changes weighting and sampling. The primary comparison uses a common cumulative generated-token budget fixed from the pilot, with measured crossing-group overshoot bounded at 1%; actual device and scorer costs are reported. Three paired seeds support exploratory estimates, not a confirmatory claim from bootstrap intervals.

The reward fractions remain vulnerable to padding and dropping hard statements. Mutation and coverage audits are required before learning, and the pilot has a frozen gaming stop rule. The official scorer is unchanged.

## Status and next admitted work

Version 2 passed its second authored fixture attempt under [Amendment A1](expt_v2/AMENDMENT_A1_development_gates_10-13-2026.md). The complete train-only diagnostic must pass before L1v2 and historical reproduction. No fitting or training is admitted yet.

The ladder declares 25,920 validation cells, with 20,520 available and 5,400 missing from five 14B checkpoints. Preserve those missing cells and reuse overlapping historical base outputs once. Full historical test equality checks use an opaque locked audit; test outcomes cannot enter model fitting.

The measured resource plan and a valid current device allocation are still absent. The 260–350 A100-hour estimate is not an allocation. Existing SNAP preapproval applies within resources; no extra human approval gate is introduced. Publication of this phase does not complete `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013`.
