# Experiment 12 results — hidden gold-reference tests on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/results.md>

Experiment `12_scsc_vs_hidden_gold_tests_vbv1_across_systems` phase A passed Amendment A1 input checks and 100/100 compilation reproductions; all four adapter controls passed under prospective Amendment A2 with zero experiment model calls.

**Status:** RUNNING under prospective Amendment A2 (`a7c2ea2`). Round-2 failure retained below; round-5 controls PASS; protocol LOCKED; evaluation is active after lock publication `f64c084`. No real-candidate hidden outcomes existed at lock.
**Last updated:** 10-09-2026 19:08 PDT

The smooth conjunctive score for code verification (SCSC) combines internal consistency of tests (IC_tests), internal consistency of proofs (IC_proofs), and formal specification coverage (FSC). Under the prospective [Amendment A1](PROTOCOL.md#8-amendment-a1-10-09-2026-master-before-any-hidden-test-outcome), the system score is the geometric mean of the three factor means over one common measured cohort. Published-value checks reproduce each source’s own convention.

| Step | Status | Evidence |
|---|---|---|
| All three frozen forecasts | PASS | Original `b29b71b7…`; A1 `81df7de2…`; A2 `674be36b…`; all unchanged and verified |
| Published values | PASS, 11/11 | [A1 source-convention audit](expt_v1/results/aggregation_preflight_A1.json) |
| Primary joins | PASS | 9,678 hash-bound + 176 unique-path flagged + 2 missing = 9,856; zero ambiguous |
| Gold reference pin | PASS, 896/896 | Every file byte-identical to git pin `c11b99badfa386fd26810b208eef1eb8dc9f6806` |
| Compilation reproduction | PASS, 100/100 | [Frozen sample](expt_v1/results/compile_selection_A1.json), [compiler receipts](expt_v1/results/compile_reproduction_A1.json); gate ≥99/100 |
| Secondary inventory | FROZEN | 33,984 cells, 33 systems; [manifest](expt_v1/results/secondary_manifest_A1.json) |
| Hidden-test extraction | DONE | 10,534 tests from 882/896 tasks; 14 `no_tests` tasks listed in [manifest](expt_v1/results/hidden_tests_manifest.json) |
| Round-2 gold control C1 | PASS, 591/591 tests (100%) | All 50 tasks pass completely; required ≥98% |
| Round-2 renamed-gold control C2 | FAIL, 2/50 tasks (4%); superseded prospectively by A2 | Required ≥95%; all 50 renamed modules compile, 48 have ambiguous mappings; [round-2 receipts](expt_v1/results/controls_e12_round2.json) |
| Round-3b controls C1–C4 | COMPLETE, failed admission | C1 591/591; C2 47/50; C3 42/48 with two unavailable mutants; C4 49/50 |
| Round-4 controls C1–C4 | COMPLETE, failed admission | C1 591/591; C2 48/50; C3 43/49 with one unavailable mutant; C4 49/50 |
| Round-5 controls C1–C4 | PASS, all 50 tasks | C1 591/591; C2 48/50; C3 44/50; C4 49/50; [full receipts](expt_v1/results/controls_e12.json) |
| Protocol lock | LOCKED | Code `a1d985c`; [exact hashes](expt_v1/results/protocol_lock.json); before real-candidate outcomes |
| Real candidate evaluation | RUNNING | Full 43,840-cell frozen set; 5,386 unique compiling pairs; [launch](expt_v1/results/evaluation_launch.json), [live snapshot](expt_v1/results/evaluation_status.json) |

## Factor inputs under A1

These are existing inputs, not hidden-test results. The seven experiment-103 rows retain 5,696/6,272 common measured cells and 576 missing-factor cells. The original and recovery files are resolved under A1.4 while preserving every recorded factor; recovery output never inherits original measured factors. A1.3’s primary and sensitivity cohorts remain distinct.

| Source / system | Common measured / declared | IC_tests | IC_proofs | FSC | System score | Published source score |
|---|---:|---:|---:|---:|---:|---:|
| VeriBench 103 / `claude-opus-5-max` | 681/896 | 0.607930 | 0.607403 | 0.736564 | 0.647908 | 0.605000 |
| VeriBench 103 / `gpt-6-astra-high` | 855/896 | 0.523977 | 0.523707 | 0.966433 | 0.642476 | 0.522000 |
| VeriBench 103 / `gpt-5.6-sol-high` | 889/896 | 0.388076 | 0.388076 | 0.920866 | 0.517619 | 0.383000 |
| VeriBench 103 / `gpt-5.6-luna-high` | 890/896 | 0.162921 | 0.162921 | 0.855506 | 0.283178 | 0.158000 |
| VeriBench 103 / `gpt-6-luna-high` | 888/896 | 0.143018 | 0.139764 | 0.881869 | 0.260254 | 0.140000 |
| VeriBench 103 / `gemini-3.1-pro-high` | 889/896 | 0.057368 | 0.054435 | 0.866142 | 0.139330 | 0.053000 |
| VeriBench 103 / `qwen3.6-27b-thinking` | 604/896 | 0.001656 | 0.001656 | 0.899421 | 0.013509 | 0.002000 |
| VeriBench 102 / `claude_code` | 896/896 | 0.977679 | 0.977416 | 0.964174 | 0.973069 | 0.973069 |
| VeriBench 102 / `codex` | 896/896 | 0.998884 | 0.998724 | 0.918192 | 0.971176 | 0.971176 |
| VeriBench 102 / `leanstral` | 896/896 | 0.508929 | 0.534202 | 0.652679 | 0.561937 | 0.561937 |
| VeriBench 102 / `baseline` | 896/896 | 0.286830 | 0.289062 | 0.293638 | 0.289830 | 0.289830 |

The two missing files are Codex `cs_set/floyd_warshall` and Leanstral `cs_set/binary_search`: 2/9,856 = 0.0203%, below A1.4’s 5% missing-plus-ambiguous gate. The 564 empty baseline outputs remain present. These are deterministic census/arithmetic checks; confidence intervals and p-values are not applicable (`p-val=n/a`).

## Amendment A2 execution

The master resolved the round-2 unique-type conflict prospectively in `a7c2ea2`. All three frozen forecasts verify; the original and A1 files are unchanged. The A2 adapter compares compatible candidate definitions with each other on hidden argument tuples only, then uses the candidate’s own example/theorem reference counts as specified. Every mapping records its deciding step. The original round-2 receipt is preserved byte-for-byte as [controls_e12_round2.json](expt_v1/results/controls_e12_round2.json).

Round 3 keeps the same 50 tasks and runs all four controls. Historical intermediate snapshot: [22/50 tasks](expt_v1/results/controls_round3b_status.json); C1 224/224, C2 22/22, C3 20/21, C4 21/22. Attempt 3a was stopped on a mutant-copy construction error: proof deletion left orphan documentation comments. [Partial receipts](expt_v1/results/controls_e12_round3a_partial.json) are retained. Corrected attempt 3b masks comments in private mutant copies and reruns the entire sample. No expected value is used to select a mapping or mutation. Mutants use the first compiling single operator/literal edit in source order; wrong-task pairs use the next selected task cyclically, fixed before results. A semantically equivalent equality-check pair was accepted in C4 and remains a recorded failure of that control.

Complete round 3b is archived in [controls_e12_round3b.json](expt_v1/results/controls_e12_round3b.json): C1 591/591; C2 47/50; C3 42/48 compiling mutants (two unavailable); C4 49/50. The three renamed failures were max/min heap operations, increment/decrement counter operations, and Floyd–Warshall input graphs incorrectly treated as implementations.

Round 4 corrects extraction of literal input fixtures: a zero-argument alias with a closed literal body is expanded only when every occurrence is inside an implementation-call argument. Expected-result aliases, nonliteral bodies and constants directly under test are not expanded. This preserves the gold test’s fixed input instead of incorrectly re-pointing it to candidate data. No gold function body or definition enters a bridge. [Reconciliation](expt_v1/results/fixture_input_normalization.json) retains all 10,534 tests and original text, with 23 aliases / 70 tests / 10 tasks normalized; the same 50 control task IDs remain. C3 adds a string-literal fallback only after all existing operator/numeric edits fail to compile. Existing successful mutant selections do not change. All four controls rerun in full, with two low-priority Lean workers. [Current round-4 snapshot](expt_v1/results/controls_round4_status.json): 50/50 tasks; C1 591/591, C2 48/50, C3 43/49, C4 49/50. The string-repeat fallback now compiles and is detected.

Round 4 is archived unchanged in [controls_e12_round4.json](expt_v1/results/controls_e12_round4.json). Its sole failed gate is the missing Floyd–Warshall mutant: both tested entry functions delegate to helpers and contain no direct operator/literal mutation. Round 5 adds a final reachable-helper fallback after all direct attempts, preserving source-order selection and every previously successful mutant choice; it reruns all four controls on all 50 tasks. Mapping, tests and expectations stay fixed. [Round-5 live snapshot](expt_v1/results/controls_round5_status.json): 50/50 tasks; gold 591/591, renamed 48/50, mutants killed 44/50, wrong-task rejection 49/50; every gate passes.

The evaluator is running after the published lock, with A1/A2 sensitivities and per-step shares prepared for the completed cohort. Immediate accounting preserves 38,454 noncompiling, missing, unmeasured or no-test cells; 5,386 unique compiling task/code pairs require Lean evaluation. Current published progress: 750/5,386 compilation jobs, 39,204/43,840 retained cell records. No frozen prediction verdict is computed until completion. Deterministic checks: 32 experiment-local tests pass, including synthetic statistics cases; repository suite 204 passed / 24 skipped.

## Historical round-2 control result and structural blocker

The hidden suites contain only extracted statements and symbol metadata; bridges import candidate modules and evaluate the re-pointed propositions, without gold implementations. The 100-file compile sample and all control selections were fixed before their results. Original references, candidates and factors remain unchanged; renamed controls are private copies.

The corrected round uses the same first 50 tasks in the prescribed hash order. C1 passes **591/591 extracted tests (100%)**, across **50/50 tasks**; C2 recovers **2/50 tasks (4%)**, below PROTOCOL § 3’s **95%** threshold. All 50 renamed modules compile, and both fully mapped renamed tasks pass every test. The other 48 tasks have multiple compatible definitions. These are deterministic checks on the fixed control sample; no sampling interval or significance test is used (`p-val=n/a`).

This is a conflict between the stipulated control and the permitted mapping rule. Most references expose functional and imperative implementations with identical argument/result types. After all implementation names are replaced, the adapter must reject both as ambiguous under “the unique candidate definition.” A stronger type unifier cannot resolve identical types. [Direct Lean checks](expt_v1/results/ambiguity_witnesses.json) confirm this independently of the adapter parser for three selected tasks. Three unavoidable failures alone cap recovery at 47/50 = 94%, below the required 48/50 = 96% integer cutoff. For example:

```lean
MyFreeLiveHandle.e12renamed0000 (live : ℕ) : Bool
MyFreeLiveHandle.e12renamed0001 (live : ℕ) : Bool
```

At round 2, no tie-breaking by source order, body contents, naming conventions or hidden-test success had been introduced. The protocol was **NOT LOCKED** at that historical stop. At round 2, continuation required a prospective clarification; Amendment A2 now supplies it while preserving the failed receipt and thresholds. An implementation-only change that preserves strict uniqueness cannot fix these witnesses. The master supplied A2 before any real-candidate outcome.

Round 1 is preserved: gold self-tests 570/590 (96.61%); renamed recovery 1/47 gold-passing tasks (2.13%). [Round-1 receipts](expt_v1/results/controls_e12_round1.json) remain unchanged. Round 2 fixed equation-definition parsing, projection renaming and structural `Except` equality. It retains all 10,429 original extracted statements and adds 105 previously missed statements, before any real-candidate hidden outcome. The current extraction contains 10,534 tests on 882 tasks, with 14 `no_tests` tasks.

**Incomplete runbook work:** the worker stopped before C3/C4 because the independent C2 requirement cannot pass under the current rule. This is a documented short-circuit, not a claim that PROTOCOL § 3 specifies sequential controls. C3/C4, protocol lock, all real-candidate evaluations and all analyses remain required after the blocker is resolved. This historical stop is resolved by A2; current external status is `RUNNING`.

## Secondary panels and outstanding analyses

Experiment 01: 9 systems × 896 = 8,064 cells. Experiment 08: its frozen 24-system validation ladder × 135 tasks × 8 samples = 25,920 cells. Together 28,584/33,984 have recorded factors; all 5,400 unavailable cells remain explicit. Only validation candidate files are read for experiment 08. Later arrivals do not silently modify this frozen snapshot.

P1 system ranking, P2 discrimination beyond compilation, P3 graded agreement, and G-A applicability remain **UNTESTED**, with no estimate, confidence interval, disagreement examples or hidden-test bounds yet. Primary, A1 sensitivity, Core 614 and IndustrySet 282 summaries will remain separate. No sealed experiment-107/109 data has been read.

## Provenance and reproduction

The pre-A1 stop is retained in [the original audit](expt_v1/results/aggregation_preflight.json), committed as `c696725`. The master resolved it prospectively in `a50618e`, before extraction or hidden outcomes. Resume/input milestone: `a6dce92`. Both forecast files and the original receipt remain unchanged.

```bash
PYTHONPATH=src python3 experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/scripts/prepare_A1.py
PYTHONPATH=src python3 experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/scripts/prepare_secondary.py
PYTHONPATH=src python3 experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/scripts/compile_reproduction.py
PYTHONPATH=src python3 experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/scripts/extract_hidden_tests.py
PYTHONPATH=src python3 experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/scripts/controls_e12.py
```

The completed round-2 control runner returns exit 2, preserving its failed gate. Compilation and control scripts preserve completed receipts on resume. Host-only logs and copied control sources are in `/lfs/skampere1/0/brando9/rl4cv_e12/`; no candidate source is committed. Verification so far: repository tests 204 passed / 24 skipped; experiment-local tests 32 passed.

**TLDR-end:** [rl4cv: 12_scsc_vs_hidden_gold_tests_vbv1_across_systems] Hidden gold-test agreement passed all four A2 controls and is locked before real-candidate outcomes. Full candidate evaluation is active; frozen prediction analyses follow completion.
