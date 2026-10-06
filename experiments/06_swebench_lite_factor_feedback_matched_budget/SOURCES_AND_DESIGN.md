# SWE bench Lite sources and factor feedback design

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/06_swebench_lite_factor_feedback_matched_budget/SOURCES_AND_DESIGN.md>

**TLDR:** Use SWE-bench Lite for the first extension of interpretable feedback to repository repair, with eight validation tasks and a later frozen 24-task test panel. Public diagnostic factors and their geometric mean are a new proxy; the official hidden resolution outcome stays evaluator-only.

**Verified on:** 10-05-2026. This source note does not establish a launched or completed experiment. The Doc link is the intended publication address until the file is pushed.

## Target and alternatives

| Benchmark | Official scope and runtime | Decision for this experiment |
|---|---|---|
| SWE-bench Lite | 300 test tasks and 23 validation tasks, named `dev` upstream; selection emphasizes self-contained bug fixes with one changed file and at most three reference-patch hunks. Docker harness. | **Selected:** consequence is a real repository issue; smaller edits make an initial repair comparison more tractable. |
| SWE-bench Verified | 500 human-reviewed test tasks; same harness, without Lite's narrow patch filter. | Better later confirmation of breadth; it supplies no separate validation split. |
| Terminal-Bench 2.1 | Revision of the 89-task 2.0 collection, fixing 28 tasks; Harbor runs task-specific container environments and verifiers. | Broader terminal workflows complicate a common factor definition and hardware matching. The release documents external-dependency, resource and instruction/test mismatch fixes. |
| LiveCodeBench | Competition-programming tasks with public/private tests; `release_v6` has 1,055 tasks, stored as a test split. Python checker; official default timeout is six seconds per test. | Practical fallback for isolated Python execution, but it tests smaller algorithmic programs rather than repository maintenance. |

Sources: [Lite selection and split](https://www.swebench.com/lite.html), [Verified dataset and schema](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified), [Terminal-Bench 2.1 release](https://www.tbench.ai/news/terminal-bench-2-1), [LiveCodeBench releases](https://github.com/LiveCodeBench/LiveCodeBench), [LiveCodeBench checker](https://github.com/LiveCodeBench/LiveCodeBench/blob/28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24/lcb_runner/evaluation/testing_util.py).

## Frozen source candidates

The public repository metadata returned these exact revisions. Freeze downloaded bytes, container image digests, task base commits and exported-view hashes in the executable manifest; a revision lookup is not a runtime acceptance receipt.

| Component | Public revision |
|---|---|
| [SWE-bench harness](https://github.com/SWE-bench/SWE-bench/tree/02e7a74ffd0b707aab73d203fe87bdc7c76afc8e) | `02e7a74ffd0b707aab73d203fe87bdc7c76afc8e` |
| [Lite dataset, legacy namespace](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite/tree/6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2) | `6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2` |
| [Verified dataset, legacy namespace](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified/tree/c104f840cc67f8b6eec6f759ebc8b2693d585d4a) | `c104f840cc67f8b6eec6f759ebc8b2693d585d4a` |
| [Terminal-Bench repository](https://github.com/harbor-framework/terminal-bench/tree/771e556f4d1c9c51b0315138361aab682ade7674) | `771e556f4d1c9c51b0315138361aab682ade7674` |
| [LiveCodeBench harness](https://github.com/LiveCodeBench/LiveCodeBench/tree/28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24) | `28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24` |
| [LiveCodeBench lite dataset](https://huggingface.co/datasets/livecodebench/code_generation_lite/tree/0fe84c3912ea0c4d4a78037083943e8f0c4dd505) | `0fe84c3912ea0c4d4a78037083943e8f0c4dd505` |

SWE-bench's newer namespace publishes a different schema: `SWE-bench/SWE-bench_Lite` revision `b0dde1093fe417d83b7184254edf8199c1f0dff5`. Do not mix namespaces silently. Metadata confirms the selected legacy Lite split sizes, 300 test and 23 validation; these are dataset counts, with confidence intervals and p-values not applicable.

## Proxy and independent endpoint

The design extends [04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2](../04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/README.md)'s feedback-information question in parallel. It does not transfer the meaning of Smooth Conjunctive Score for Code verification (SCSC) to Python patches.

A proposed public factor vector is `(execution viability, regression preservation, issue behavior)`: respectively, fractions of frozen syntax/import checks, pre-existing repository checks, and issue-derived behavioral checks passed. Each lies in `[0,1]`; every denominator must be nonempty. Define `diagnostic_geometric_mean = (viability × preservation × behavior)^(1/3)`. These are new operational constructs, not formal proof or specification coverage. Create checks from the issue statement and base repository alone before candidate outcomes; freeze their identities and counts. Select repository checks without using reference changed-file lists or hidden test identities. Missing applicability stays explicit. No benchmark reference is rewritten.

The independent official endpoint is the pinned harness's `resolved` flag: all issue-resolution tests in `FAIL_TO_PASS` must pass and all regression tests in `PASS_TO_PASS` must be maintained under the official parser's semantics. Retain official handling of skipped tests, invalid test runs and infrastructure faults. Do not construct this score from public factors. [Pinned grading implementation](https://github.com/SWE-bench/SWE-bench/blob/02e7a74ffd0b707aab73d203fe87bdc7c76afc8e/swebench/harness/grading.py).

Solver access is limited to issue text, the base repository and permitted public diagnostics. Reference patches, `test_patch`, hidden test identities, evaluator logs and hidden counterexamples remain outside the solver filesystem and prompts. Remove repository remotes and future commit objects and restrict network retrieval of solved issues. Official dataset viewers expose reference snippets; source inspection must never become solver context. Score hidden outcomes only after every condition's final patch is frozen, and return no outcome to subsequent repairs.

## Pilot and runtime limits

**[p 9/10] Start with eight hash-selected validation tasks**, because this cheaply tests whether public factors identify actionable failures. Select before compilation or model outcomes, preserve every task and fault receipt, and share each initial patch across ordinary diagnostics, scalar feedback, and scalar-plus-factor feedback. Two repair steps per condition require at most `8 + 8 × 3 × 2 = 56` solver responses. Any changed setup gets a new version. Freeze prompts, models, budgets, diagnostic computation and total-cost accounting before calls; equal response caps alone do not establish equal cost. The later 24-task test panel requires a fixed controller and manifest and at most 168 responses with the same structure. Eight-task results establish feasibility, not a general improvement claim.

The official harness recommends x86_64, eight processor cores, 16 gigabytes of memory and 120 gigabytes of free storage. Actual image download/build time and solver runtime are unmeasured. Standard execution is `python -m swebench.harness.run_evaluation --dataset_name princeton-nlp/SWE-bench_Lite --split dev --predictions_path <frozen-predictions.jsonl> --max_workers 2 --run_id <unique-condition-step-hash>` from the pinned installed checkout. [Harness requirements and commands](https://github.com/SWE-bench/SWE-bench).

**Cache trap:** the harness caches by `run_id` and `instance_id`, not prediction content. Use a new run identifier for every condition, step and patch hash or later evaluations can reuse an earlier patch's result. Retain prediction hashes and grader receipts. Primary analysis compares paired official resolution after step two, factor feedback minus scalar feedback, with task-level uncertainty, all missing cells and measured cost. Freeze criteria before measuring.

Terminal-Bench would additionally require task-level processor, memory, graphics processor, storage and timeout pins, plus isolation of `tests/` and `solution/`. Harbor supports separate verifier environments; its general configuration defaults are not the benchmark's measured runtime. [Task structure](https://docs.harborframework.com/tasks/overview), [resource and verifier configuration](https://docs.harborframework.com/tasks/configuration). LiveCodeBench also needs an actual isolated execution environment: its reliability guard explicitly is not a security sandbox, and its normal evaluation sample combines public and private tests. Build a separate public feedback sample; do not forward official checker error metadata containing hidden inputs and expected outputs. [Pinned sample construction](https://github.com/LiveCodeBench/LiveCodeBench/blob/28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24/lcb_runner/benchmarks/code_generation.py).
