# Experiment 12 results — hidden gold-reference tests on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/results.md>

Experiment `12_scsc_vs_hidden_gold_tests_vbv1_across_systems` phase A passed Amendment A1 input checks and 100/100 compilation reproductions; gold reproduction passes 591/591 tests, but renamed-symbol recovery fails at 2/50 tasks (4%), blocking evaluation under PROTOCOL § 3 with zero model calls.

**Status:** BLOCKED — renamed-symbol control C2 fails the ≥95% gate; no real candidate hidden-test outcomes.
**Last updated:** 10-09-2026 15:24 PDT

The smooth conjunctive score for code verification (SCSC) combines internal consistency of tests (IC_tests), internal consistency of proofs (IC_proofs), and formal specification coverage (FSC). Under the prospective [Amendment A1](PROTOCOL.md#8-amendment-a1-10-09-2026-master-before-any-hidden-test-outcome), the system score is the geometric mean of the three factor means over one common measured cohort. Published-value checks reproduce each source’s own convention.

| Step | Status | Evidence |
|---|---|---|
| Both frozen forecasts | PASS | Original `b29b71b7…`; A1 `81df7de2…`; both unchanged and verified |
| Published values | PASS, 11/11 | [A1 source-convention audit](expt_v1/results/aggregation_preflight_A1.json) |
| Primary joins | PASS | 9,678 hash-bound + 176 unique-path flagged + 2 missing = 9,856; zero ambiguous |
| Gold reference pin | PASS, 896/896 | Every file byte-identical to git pin `c11b99badfa386fd26810b208eef1eb8dc9f6806` |
| Compilation reproduction | PASS, 100/100 | [Frozen sample](expt_v1/results/compile_selection_A1.json), [compiler receipts](expt_v1/results/compile_reproduction_A1.json); gate ≥99/100 |
| Secondary inventory | FROZEN | 33,984 cells, 33 systems; [manifest](expt_v1/results/secondary_manifest_A1.json) |
| Hidden-test extraction | DONE | 10,534 tests from 882/896 tasks; 14 `no_tests` tasks listed in [manifest](expt_v1/results/hidden_tests_manifest.json) |
| Gold control C1 | PASS, 591/591 tests (100%) | All 50 tasks pass completely; required ≥98% |
| Renamed-gold control C2 | FAIL, 2/50 tasks (4%) | Required ≥95%; all 50 renamed modules compile, 48 have ambiguous mappings; [receipts](expt_v1/results/controls_e12.json) |
| Mutated / wrong-task controls C3/C4 | NOT RUN | Worker short-circuited after structural C2 failure; these gates remain unresolved |
| Protocol lock and real candidate evaluation | NOT STARTED | All adapter controls must pass first |

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

## Control result and structural blocker

The hidden suites contain only extracted statements and symbol metadata; bridges import candidate modules and evaluate the re-pointed propositions, without gold implementations. The 100-file compile sample and all control selections were fixed before their results. Original references, candidates and factors remain unchanged; renamed controls are private copies.

The corrected round uses the same first 50 tasks in the prescribed hash order. C1 passes **591/591 extracted tests (100%)**, across **50/50 tasks**; C2 recovers **2/50 tasks (4%)**, below PROTOCOL § 3’s **95%** threshold. All 50 renamed modules compile, and both fully mapped renamed tasks pass every test. The other 48 tasks have multiple compatible definitions. These are deterministic checks on the fixed control sample; no sampling interval or significance test is used (`p-val=n/a`).

This is a conflict between the stipulated control and the permitted mapping rule. Most references expose functional and imperative implementations with identical argument/result types. After all implementation names are replaced, the adapter must reject both as ambiguous under “the unique candidate definition.” A stronger type unifier cannot resolve identical types. [Direct Lean checks](expt_v1/results/ambiguity_witnesses.json) confirm this independently of the adapter parser for three selected tasks. Three unavoidable failures alone cap recovery at 47/50 = 94%, below the required 48/50 = 96% integer cutoff. For example:

```lean
MyFreeLiveHandle.e12renamed0000 (live : ℕ) : Bool
MyFreeLiveHandle.e12renamed0001 (live : ℕ) : Bool
```

No tie-breaking by source order, body contents, naming conventions or hidden-test success has been introduced. The protocol remains **NOT LOCKED**. Continuation requires a prospective protocol clarification defining how equivalent or same-type implementation alternatives are handled, while preserving the failed C2 result and the original thresholds. An implementation-only change that preserves strict uniqueness cannot fix these witnesses. The worker has not chosen or enacted that scientific change.

Round 1 is preserved: gold self-tests 570/590 (96.61%); renamed recovery 1/47 gold-passing tasks (2.13%). [Round-1 receipts](expt_v1/results/controls_e12_round1.json) remain unchanged. Round 2 fixed equation-definition parsing, projection renaming and structural `Except` equality. It retains all 10,429 original extracted statements and adds 105 previously missed statements, before any real-candidate hidden outcome. The current extraction contains 10,534 tests on 882 tasks, with 14 `no_tests` tasks.

**Incomplete runbook work:** the worker stopped before C3/C4 because the independent C2 requirement cannot pass under the current rule. This is a documented short-circuit, not a claim that PROTOCOL § 3 specifies sequential controls. C3/C4, protocol lock, all real-candidate evaluations and all analyses remain required after the blocker is resolved. External status is `BLOCKED`, not `DONE`.

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

The completed round-2 control runner returns exit 2, preserving its failed gate. Compilation and control scripts preserve completed receipts on resume. Host-only logs and copied control sources are in `/lfs/skampere1/0/brando9/rl4cv_e12/`; no candidate source is committed. Verification so far: repository tests 189 passed / 24 skipped; experiment-local tests 13 passed.

**TLDR-end:** [rl4cv: 12_scsc_vs_hidden_gold_tests_vbv1_across_systems] Hidden gold-test agreement cleared A1 input checks and 100/100 compilation reproductions, but renamed-symbol recovery fails at 2/50 against ≥95%. Evaluation remains blocked by identical-type alternatives under the unique-match rule; predictions are untested.
