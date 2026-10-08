# What VeriBench already tells us: baselines, saturation and the FSC judge

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/FACTS_veribench_baselines.md>

**TLDR:** Before experiment 01, no model at or below 14B parameters had been evaluated on the current VeriBench V1 panel; experiment 01 now measures these models directly. In experiment 103, the smallest Qwen solver run, Qwen3.6-27B, scored SCSC 0.002 because almost nothing it wrote compiled. Frontier agents are near the ceiling on the two kernel-checked factors, and formal specification coverage (FSC) is their lowest factor. But the FSC judge also gives high scores to files that do not compile, so FSC must be gated on compilation before it can be used as a reward or an outcome.

Collected on 09-30-2026 from the VeriBench repository at commit `c11b99ba` (pinned in [`external/deps.lock.json`](../external/deps.lock.json)).
Paths below are relative to that repository.
Abbreviations:

- **IC_tests:** 1 if the file typechecks and states at least one `example`.
- **IC_proofs:** the fraction of stated theorems the Lean kernel accepted using only `propext`, `Classical.choice` and `Quot.sound`.
- **FSC:** formal specification coverage, the judged coverage of the reference theorem statements.
- **SCSC:** VeriBench's aggregate, (IC_tests · IC_proofs · FSC)^(1/3).
- **VBV1:** VeriBench V1, 896 tasks: a 614-task core plus the 282-task IndustrySet.
- **VBV2:** VeriBench V2.

## 1. Small open-weight models: prior evidence and experiment 01 update

| Model | Benchmark, n | IC_tests | IC_proofs | FSC | SCSC | Route | Source |
|---|---|---:|---:|---:|---:|---|---|
| Qwen3.6-27B, thinking on | VBV1, 604 of 896 measured | 0.002 | 0.002 | 0.900 | 0.002 | single call via Valkyrie, 65,536-token cap | `experiments/103_…/results.md` |
| Leanstral 1.5.1 (119B MoE, 6.5B active) | VBV1 core 614 | 0.510 | 0.522 | 0.637 | 0.553 | its own agent via the Mistral API | `experiments/102_…/results/tables/TABLES.md` |
| DeepSeek-Prover-V2-7B, Goedel-Prover-V2-8B | veribench@1.0, 170 tasks | compiled 0–1 of 170 | — | — | — | single call, local vLLM, 03-2026 | archival, `research_archive/experiments/35_vb_x_harbor/` |

How Qwen3.6-27B failed (experiment 103):

- 245 of its 292 lost cells hit the 65,536-token output cap, and 47 were gateway timeouts.
- 87.5% of its sampled zeros do not parse as Lean 4.

**An invalid namespace hint copied by small models (experiment 01 diagnostic, 10-07-2026).**

- VeriBench's task instruction (`vb_harbor/adapter/adapter.py:134`, at the pin `c11b99ba` and at HEAD `9e312c9052`) suggests ``namespace {file stem}``.
- For 533 of the 896 VBV1 tasks (all of easy_set, realcode_set and security_set) the stem starts with a digit, e.g. `namespace 1_MyAdd`. That is not a Lean identifier; the gold files use `namespace MyAdd`.
- The legacy regex matches digit-leading namespace text in 516 Qwen3-14B files out of 896 declared cells; those 516 files fail to compile. The historical namespace rewrite raises its positive-test-and-proof cells from 1/896 to 25/896 (2.8%, 95% Wilson interval [1.9%, 4.1%], unit = task; diagnostic only). Most cells still score zero. The [results write-up](../experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md) records 13 legacy rewrites across models that also affected literal/prose text; none contributes a positive cell, and the guarded counterfactual was not recompiled.
- Frontier single-call models in experiment 103 have higher compile-with-example rates on these task families than elsewhere. Family difficulty confounds this comparison; it does not measure the namespace hint's causal effect.
- Fixing the template is a benchmark change, so Trigger Rule 43 applies.

The statement "an open model of ≤14B starts at about 0 on VeriBench" was an extrapolation from this 27B row before experiment 01. [Experiment 01](../experiments/01_small_open_models_veribench_v1_single_call_baseline/README.md) measures it directly.

## 2. Frontier systems: two factors are nearly saturated; FSC carries the remaining signal

Single calls on VBV1, all 896 tasks, validated judge (experiment 103):

| Model | IC_tests | IC_proofs | FSC | SCSC | measured n |
|---|---:|---:|---:|---:|---:|
| `claude-opus-5-max` | 0.608 | 0.607 | 0.737 | 0.605 | 681 |
| `gpt-6-astra-high` | 0.524 | 0.524 | 0.966 | 0.522 | 855 |
| `gpt-5.6-sol-high` | 0.388 | 0.388 | 0.921 | 0.383 | 889 |
| `gemini-3.1-pro-high` | 0.057 | 0.054 | 0.866 | 0.053 | 889 |
| `qwen3.6-27b-thinking` | 0.002 | 0.002 | 0.900 | 0.002 | 604 |

Agents with the validated judge, on raw judge scores (experiment 102 and the TMLR paper):

| System | Tasks | IC_tests | IC_proofs | FSC | SCSC |
|---|---|---:|---:|---:|---:|
| Claude Code | core 614 | 0.977 | 0.977 | 0.956 | 0.970 |
| Codex | core 614 | 0.998 | 0.998 | 0.897 | 0.963 |
| Claude Code | all 896 | 0.978 | 0.977 | 0.964 | 0.973 |
| Codex | all 896 | 0.999 | 0.999 | 0.918 | 0.971 |

- **Lowest factor.** On raw scores, FSC is the lowest of the three factors for these agents. On VBV2 it is clearly lowest: the GPT-6 Luna agent scores IC 1.00 and 1.00 but FSC 0.65 (experiment 100, phase 7, small n).
- **Ceiling on VBV1.** The share of items at FSC = 1.0 is 54.9–81.2% for single calls, against 16.0% for VBV2 single calls (4 of 25) (experiment 103, `results/fsc_ceiling.json`).
- **Expert scale.** An isotonic map fitted to expert ratings on 36 items puts the two agents' FSC at 0.571 and 0.549. But that map is clipped: every raw score of 0.8 or more maps to 0.577, so it cannot measure the top of the scale.
- **What the paper concludes.** The TMLR abstract says the ranking of systems is validated, "while the size of the coverage gap depends on the judge's absolute scale".

So your reading is right in direction. FSC is where frontier headroom remains. But on VBV1 the measurement of that headroom is limited by the judge's scale.

## 3. The FSC judge

- **Configuration.** Experiment 100's "H2" ensemble: `openai/gpt-6-sol-high` (high effort) plus `anthropic/claude-opus-5-5-no-fallback` (max effort). Each takes the median of 3 calls, the two medians are averaged, and the 0–5 integer is divided by 5. That is 6 calls per candidate.
- **Agreement with experts.**
  - Test split: Spearman 0.826 and ICC 0.727 on 30 items.
  - Five-fold cross-validated recipe on all 75 expert-rated items: Spearman 0.603 and ICC 0.593 (experiment 104).
- **Lenient in the partial band.** The judge's mean is 0.730 where the experts' mean is 0.437.
- **Judges files that do not compile.** Any non-empty file is judged.
  - Experiment 103: "`bst` scores `FSC` 1.00 for four different models whose files do not compile at all".
  - Leanstral's non-compiling core files average FSC 0.586.
- **Ignores proofs.** Replacing every proof with `sorry` shifts FSC by +0.002 (experiment 105).
- **Route.** A custom Valkyrie agent, `vb103_judge`, in `experiments/103_…/scripts/valkyrie_judge_agent/`. The older host-side gateway route is retired.
  - `scripts/scsc/run_real_eval.py` still hard-codes the old judge that failed validation (Sonnet 4.6, rubric `tc_coverage_v1`). Never use its built-in FSC; always run the scorer with `--skip-tc` and judge separately.
- **Cost.** About $0.07 per judge call and about $0.40 per fully judged candidate.
  - Experiment 102: 18,108 calls for $1,227.90.
  - Experiment 103: 26,466 calls for $1,828.76. Its Qwen3.6-27B suite alone cost $290.77.
  - These are Vals-side figures.

## 4. What this means for this project

1. **Phase 0 is required.** Small Qwen models have no VeriBench numbers; measure them first.
2. **Gate FSC on compilation.** An ungated FSC reward or outcome pays for Lean-looking text that does not typecheck. The official SCSC already gates FSC, because it is 0 whenever IC_tests · IC_proofs = 0. It is also *exact* without any judge call for such files, which keeps per-checkpoint judging cheap while compile rates are low.
3. **Target VeriBench through SCSC.** SCSC is the only aggregate VeriBench allows. Report all three factors and n with it.
4. **Watch the FSC ceiling.** VBV1 raw FSC saturates near the top, so FSC-driven gains show up mainly in SCSC (through the IC gate) and on VBV2-style tasks. Any claim about the top of the FSC scale must state the judge's scale.
5. **Reuse experiment 103 exactly.** Use its prompt, extraction and frozen scorer (commit `59059a20d`, hashes in `external/deps.lock.json`), so small-model baselines line up with its table.
