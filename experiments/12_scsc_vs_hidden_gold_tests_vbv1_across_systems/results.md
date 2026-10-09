# Experiment 12 results — hidden gold-reference tests on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/results.md>

Experiment `12_scsc_vs_hidden_gold_tests_vbv1_across_systems` phase A passed Amendment A1 input checks and 100/100 compilation reproductions; gold and renamed-gold adapter controls are running with zero model calls.

**Status:** RUNNING — adapter admission controls; no real candidate hidden-test outcomes.
**Last updated:** 10-09-2026 15:04 PDT

The smooth conjunctive score for code verification (SCSC) combines internal consistency of tests (IC_tests), internal consistency of proofs (IC_proofs), and formal specification coverage (FSC). Under the prospective [Amendment A1](PROTOCOL.md#8-amendment-a1-10-09-2026-master-before-any-hidden-test-outcome), the system score is the geometric mean of the three factor means over one common measured cohort. Published-value checks reproduce each source’s own convention.

| Step | Status | Evidence |
|---|---|---|
| Both frozen forecasts | PASS | Original `b29b71b7…`; A1 `81df7de2…`; both unchanged and verified |
| Published values | PASS, 11/11 | [A1 source-convention audit](expt_v1/results/aggregation_preflight_A1.json) |
| Primary joins | PASS | 9,678 hash-bound + 176 unique-path flagged + 2 missing = 9,856; zero ambiguous |
| Gold reference pin | PASS, 896/896 | Every file byte-identical to git pin `c11b99badfa386fd26810b208eef1eb8dc9f6806` |
| Compilation reproduction | PASS, 100/100 | [Frozen sample](expt_v1/results/compile_selection_A1.json), [compiler receipts](expt_v1/results/compile_reproduction_A1.json); gate ≥99/100 |
| Secondary inventory | FROZEN | 33,984 cells, 33 systems; [manifest](expt_v1/results/secondary_manifest_A1.json) |
| Hidden-test extraction | DONE | 10,429 tests from 881/896 tasks; 15 `no_tests` tasks listed in [manifest](expt_v1/results/hidden_tests_manifest.json) |
| Gold / renamed-gold controls | RUNNING | First 50 eligible tasks in prescribed hash order; two low-priority Lean processes |
| Mutated / wrong-task controls | PENDING | Require resolving the gold/renamed-gold admission gates |
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

## Control implementation and potential ambiguity

The hidden suites contain only extracted statements and symbol metadata; bridges import candidate modules and evaluate the re-pointed propositions, without gold implementations. The 100-file compile sample and all control selections were fixed before their results. Original references, candidates and factors remain unchanged; renamed controls are private copies.

The preliminary mapping check finds ambiguous compatible signatures on 48/50 selected renamed-gold tasks. Most expose a functional and an imperative implementation with the same argument and result types. The adapter preserves the rule requiring a **unique** compatible definition; it does not break ties by source order, body contents, naming conventions, or hidden-test success. Actual gold and renamed-gold Lean compilation and self-test control results are pending.

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

Compilation and control scripts preserve completed receipts on resume. Host-only logs and copied control sources are in `/lfs/skampere1/0/brando9/rl4cv_e12/`; no candidate source is committed. Verification so far: repository tests 189 passed / 24 skipped; experiment-local tests 12 passed.

**TLDR-end:** [rl4cv: 12_scsc_vs_hidden_gold_tests_vbv1_across_systems] Hidden gold-test agreement has cleared A1 input gates and reproduced all 100 compile statuses. The gold/renamed-gold controls are checking whether the permitted mechanical adapter can satisfy its admission requirements.
