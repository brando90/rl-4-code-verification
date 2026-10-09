# Experiment 12 phase A protocol — SCSC versus hidden gold-reference tests on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/PROTOCOL.md>

**TLDR:** This fixes the inputs, the hidden-test extraction, the adapter and its controls, the cell outcomes, the analyses and the stop rules for comparing SCSC with hidden gold-reference tests. The predictions were frozen on 10-09-2026 before any hidden-test outcome existed; this document is locked after the adapter controls pass and before any real candidate file is evaluated.

**Lock line:** `NOT LOCKED` — the worker replaces this with `LOCKED <UTC> at commit <hash>` after § 3's controls pass and before § 4 touches a real candidate. Any later change is a new version (`expt_v2`).

## 1. Inputs (pinned; read-only)

- **Gold references:** VeriBench at the `veribench` pin in `external/deps.lock.json` (`c11b99ba`): the 896 VeriBench V1 gold Lean files the frozen scorer maps tasks to. Record the path and SHA-256 of each.
- **Primary panel (11 systems × 896 tasks):**
  - VeriBench experiment 103 `results/summary.json` (`benchmark == vbv1_896`; 7 models: `claude-opus-5-max`, `gpt-6-astra-high`, `gpt-5.6-sol-high`, `gpt-5.6-luna-high`, `gpt-6-luna-high`, `gemini-3.1-pro-high`, `qwen3.6-27b-thinking`) plus each cell's collected Lean file from 103's private tree on `skampere1`;
  - VeriBench experiment 102 `results/tables/validated_per_candidate.csv` (4 systems: `codex`, `claude_code`, `leanstral`, `baseline`; `ic_ap` = IC_tests, `ic_pp` = IC_proofs, `validated_tc` = FSC) plus each cell's candidate file located through 102's `input_inventory_tier1.json` / `input_inventory_tier2.json`.
  - Join every factor row to its candidate file by SHA-256 where the inputs record one. A cell whose file cannot be located is `file_missing` and stays in the denominator.
- **Secondary panels:** rl4cv experiment 01 (9 models × 896, single call; factors from its scored JSONL; FSC where judged) and experiment 08's validation ladder (Base and SFT systems, 135 tasks × 8 samples; IC factors and `kernel_binary` only, no FSC).
- **Excluded:** sealed data (experiment 107's human-round packets and key, experiment 109's sealed FSC/SCSC), VeriBench V2 and multifile rows, experiment 08's test split.

## 2. Hidden test suites

- From each gold file, extract the **ground computational tests**: `example` declarations with no binders whose statement is a closed equation, inequality, negation or Boolean fact about gold implementation symbols applied to literal arguments, for example `example : f [2, 4, 6] = 0 := …` and `example : ¬ (f [2, 4, 6] > 1) := …`. Statements quantified over variables (`∀`, `∃`) are theorems, not tests, and belong to the later obligations phase.
- Record per task: the tests, the gold symbols each uses, and a suite SHA-256. A task with zero extractable tests is `no_tests`, listed and excluded from hidden-test outcomes (its count is reported).
- Freeze `expt_v1/results/hidden_tests_manifest.json` (task → tests, symbols, hash) before § 4.

## 3. Adapter and controls (must pass before the lock)

- **Symbol mapping**, in order:
  1. the same name after stripping or normalizing namespaces;
  2. else the unique candidate definition with the same arity whose type unifies with the gold symbol's type after the allowed numeric generalization;
  3. else `not_applicable`.
- **Allowed transformations, and only these:** renaming, namespace qualification and opening, and re-elaborating the test's literals at the candidate's argument and result types (Lean's numeric and list literals are polymorphic). Literals that do not elaborate at the candidate's types make that test `unknown`. Nothing else: no coercion functions, no Option/Except unwrapping, no gold definitions in the bridge, no added hypotheses, no language model.
- **Bridge:** a file that imports Mathlib and the candidate's module under its own namespace and states each re-pointed test as a Boolean check evaluated with `#eval decide (…)` (or equivalent), recording `true` / `false` / error per test. Use the frozen grading project and a per-file timeout (`600 s`, matching the frozen scorer's compile check).
- **Controls**, each over at least 50 tasks drawn in `sha256("rl4cv-e12-ctl:" + task_id)` order, with its own expectation:
  - **C1 gold as candidate:** ≥ 98% of extracted tests applicable and passing.
  - **C2 renamed gold** (every gold implementation symbol renamed): the adapter recovers the mapping on ≥ 95% of tasks with C1 passing.
  - **C3 mutated gold** (one operator or literal mutation in the implementation, not the tests, that still compiles): at least one test fails on ≥ 60% of mutants; record the kill rate.
  - **C4 wrong task** (another task's gold as candidate): `not_applicable` or failing on ≥ 95% of pairs.
- If a control misses, fix the adapter or extraction and rerun every control; never weaken an expectation. The final adapter's code and hash enter the lock.

## 4. Cells and outcomes (after the lock)

- **Cell** = (system, task) for the primary panel and experiment 01; (system, task, sample) for experiment 08.
- **Per cell:**
  - `compiles`: the candidate file compiles, per the recorded factors.
  - `applicable`: adapter found and at least one test evaluable.
  - `hidden_pass_rate`: passed tests / applicable tests.
  - `hidden_all_pass`: every extracted test is applicable and passes.
  - `n_tests`, `n_applicable`, `n_unknown`.
- **Rules:**
  - A non-compiling candidate has `hidden_all_pass = 0` and `hidden_pass_rate = 0` (its code does not run).
  - A compiling candidate that is not applicable is **missing** for hidden outcomes: never zero, always listed, and covered by bounds (all missing fail / all missing pass).
  - `no_tests` tasks are excluded for every system alike.
- **SCSC per cell:** (IC_tests · IC_proofs · FSC)^(1/3) from the recorded factors. It is exactly 0 when IC_tests · IC_proofs = 0. Where a needed FSC is unmeasured, it is missing, never zero. **System SCSC:** the published aggregate (mean IC_tests · mean IC_proofs · mean FSC)^(1/3) over that system's 896 cells, recomputed from the inputs and checked against the published value.

## 5. Analyses (seed 20261009; task-cluster bootstrap, 10,000 draws; p-val=n/a unless stated)

- **P1** (primary panel, n = 11 systems):
  - Spearman(system SCSC, system hidden-test pass rate), where the system hidden-test pass rate is the mean `hidden_all_pass` over non-missing cells. Also report Pearson, Kendall τ-b, both means, mean bias (SCSC − pass rate) and mean absolute difference.
  - Intervals: task bootstrap, and system bootstrap as a sensitivity.
  - Frozen prediction: ρ ≥ 0.80.
  - Repeat with `hidden_pass_rate` and with each factor's system mean (IC_tests, IC_proofs, FSC) as descriptive rows.
- **P2** (compiling, applicable primary-panel cells): the system-stratified area under the ROC curve (AUC) of per-cell SCSC for `hidden_all_pass`, pooled by within-system ranks.
  - Frozen prediction: AUC ≥ 0.60, interval excluding 0.50.
  - Also report AUC for IC_proofs alone and FSC alone, and per system where both outcome classes have ≥ 10 cells.
- **P3** (same cells): pooled within-system Spearman(per-cell SCSC, `hidden_pass_rate`). Frozen prediction: > 0, interval excluding 0.
- **G-A:** applicable / compiling over the primary panel, overall and per system. Frozen gate: ≥ 0.50, else the verdict is LIMITED COVERAGE (the analyses still run and report bounds).
- **Descriptive:**
  - per-system table (all factors, compile rate, applicability, hidden rates, bounds);
  - 20 inspected disagreements, 10 high-SCSC failing and 10 low-SCSC passing, with reasons;
  - experiment 01 rows;
  - experiment 08 rows: hidden pass rate per checkpoint next to its `kernel_binary` rate, and among kernel-verified samples, the share that also pass all hidden tests.

## 6. Validity checks and stop rules

- Every factor row joins to exactly one file, or is `file_missing` and listed. Stop if more than 5% of the primary-panel cells are `file_missing`.
- Recomputed system SCSC must match the published value to 3 decimals, else stop and report the aggregation difference.
- Recompiling a sample of 100 candidates must reproduce the recorded `compiles` field on ≥ 99%, else stop.
- Never edit a candidate file, a gold file or a recorded factor. Never re-sample, drop or reorder cells by outcome.

## 7. Not in phase A

Hidden **proofs** (`reference_obligations_proved` with a fixed prover budget), Python-side differential tests, the agent-spec v8 fresh panel, and human acceptance ratings are later versions.
