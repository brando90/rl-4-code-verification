# Experiment 12 — Does SCSC track hidden gold-reference tests? VeriBench V1 across 11 systems

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/README.md>

**TLDR:** We need to show that VeriBench's score, SCSC (the smooth conjunctive score for code verification), tracks what people actually want from a verification: Lean code that really does what the original program does. This experiment measures that with **hidden gold-reference tests**. Every VeriBench task has a gold Lean reference whose `example` tests the model never sees. We re-point those tests at each model's own Lean function through a frozen, mechanical adapter and check whether they pass. Then we ask, as experiment 07 did for SWE-bench, whether SCSC ranks systems like hidden-test success, and whether it separates passing from failing files beyond "does it compile". It uses the saved outputs of 11 systems on all 896 VeriBench V1 tasks, with **zero model calls**.

**Owner:** Emily Xia (@emxia18), with Ethan Li (@lethan3) advising on SCSC. **Set up by:** the Claude Code master session for Brando, 10-09-2026. **Status:** see [results.md](results.md).

## Origin

- **Brando, 10-09-2026:** "we definitely need to show that the smooth conjunctive score for code verification correlates with what people actually want … passing tests and passing proofs from the gold reference … I think that one for sure." Then: "Go".
- **The downstream outcome was already defined, never measured.** [D-008](../../docs/DECISIONS.md) keeps "fixed-reference success" as the check on SCSC. Experiment 04's [METRICS.md](../04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/METRICS.md) defines `reference_tests_pass` (the candidate's implementation passes every fixed reference test through a frozen interface) and `reference_obligations_proved` (every reference theorem, restated about the candidate's implementation, gets an allowed-axiom proof). Experiment 04 never computed them on VeriBench outputs: its generic adapter supported 0/24 external tasks, and an older VeriBench replay (experiment 75's adapter synthesis) mapped only 1,061 of 3,112 candidate files cleanly (776 name only, 677 type mismatch, 598 failed).
- **Why it matters now.**
  - Workshop reviewers called SCSC arbitrary (Ethan Li, 10-05-2026 meeting).
  - Azalia asked for metrics that track downstream evaluations ([meeting notes](../../docs/meeting_notes/README.md)).
  - Experiment 07 showed the general-code analogue tracks pass@1 on SWE-bench but had no VeriBench counterpart.
- **This version is step 1:** hidden **tests** on outputs we already have. Hidden **proofs** (`reference_obligations_proved`) and a fresh panel on a fixed task spec (agent-spec v8: valid namespace and a fixed entry point) are later versions.

## Goal, hypotheses and decision criterion

- **Uncertainty.** Does SCSC agree with an outcome it never sees, the gold reference's own tests run against the model's code, and does it carry information beyond compile status?
- **Primary panel:** 11 systems × 896 tasks with all three SCSC factors judged by the validated FSC judge (formal specification coverage; experiment 100's H2 ensemble, median of 3):
  - experiment 103's single calls: Claude Opus 5 max, GPT-6 Astra high, GPT-5.6 Sol high, GPT-5.6 Luna high, GPT-6 Luna high, Gemini 3.1 Pro high, Qwen3.6-27B thinking;
  - experiment 102's validated rescoring of the paper's systems: Codex, Claude Code, Leanstral, baseline.
- **Secondary panels (descriptive):** rl4cv experiment 01's 9 small Qwen models (896 tasks, single call), and experiment 08's validation ladder (Base and SFT checkpoints, 135 tasks × 8 samples). For 08 this answers "is the SFT models' code actually correct?", beyond the kernel check.
- **Predictions** (frozen before any hidden-test outcome exists; thresholds agent-suggested; [forecast](expt_v1/forecasts/e12_phase_a_forecast.json)):

  | Id | Claim | Frozen prediction |
  |---|---|---|
  | P1 | System level: SCSC ranks systems like hidden-test success | Spearman(system SCSC, system hidden-test pass rate) ≥ 0.80 over the 11 primary systems |
  | P2 | Beyond compiling: among files that compile, SCSC separates files that pass all hidden tests from files that fail some | System-stratified AUC of per-file SCSC ≥ 0.60, task-cluster bootstrap 95% interval excluding 0.50 |
  | P3 | Graded agreement: among compiling files, higher SCSC goes with a higher share of hidden tests passed | Within-system Spearman > 0, interval excluding 0 |
  | G-A | Engineering gate: the adapter applies to enough compiling files | ≥ 50% of compiling primary-panel files; below that the verdict is LIMITED COVERAGE |

- **Reading the outcome** (written before measuring):
  - P1 and P2 hold → SCSC tracks hidden correctness and adds information beyond compiling. This is the paper's claim.
  - P1 holds, P2 fails → system-level agreement may be mostly compile rate; the proof and coverage factors are not shown to help.
  - P1 fails → SCSC and hidden-test success rank systems differently. Inspect matched disagreements before concluding: SCSC also rewards proofs and specifications that tests cannot see (`METRICS.md`).

## Method

1. **Hidden test suites (zero calls).** From each task's gold reference at the `veribench` pin, extract the ground computational `example` tests: closed statements about the gold implementation, such as `example : f [2, 4, 6] = 0`. The extraction is frozen and hashed before any candidate is evaluated, and a task with zero extractable tests is listed and excluded.
2. **Mechanical adapter (frozen before outcomes).** Map each gold implementation symbol a test uses to the candidate's definition. Use the same name after namespace normalization, else the unique definition with matching arity and compatible types. A small, listed set of transformations is allowed (renaming, namespace qualification, numeric literals elaborated at the candidate's types). No language model, no gold code in the bridge, no added assumptions. The adapter is validated on controls:
   - the gold file as its own candidate (all tests apply and pass);
   - gold with renamed symbols (the adapter must find them);
   - mutated gold (tests must catch most mutants);
   - another task's candidate (must not apply).
3. **Evaluate.** For each compiling candidate, build a bridge file that imports the candidate and states each re-pointed test, then evaluate it in the frozen grading project (Lean v4.22.0 + Mathlib). Each test is `pass`, `fail` (the values differ) or `unknown` (adapter or elaboration failure, timeout). Evaluating tests may use `decide`, `rfl` and `native_decide`: this is test execution, not proof, and proved-theorem scoring is untouched. A non-compiling candidate fails every hidden test. A compiling candidate with no applicable adapter is **missing**, never zero, and is reported with bounds.
4. **Analyze** as frozen in [PROTOCOL.md](PROTOCOL.md): P1, P2, P3 and G-A with task-cluster bootstrap intervals (10,000 draws, seed 20261009), absolute agreement and mean bias for levels, per-system tables, the secondary panels, and inspected disagreements.

## Structure

```
12_scsc_vs_hidden_gold_tests_vbv1_across_systems/
├── README.md       ← this design doc
├── PROTOCOL.md     ← locked by the worker after the adapter controls pass, before any real candidate is evaluated
├── results.md      ← live results
└── expt_v1/
    ├── cc.md                ← SNAP worker runbook
    ├── CKPT_e12.md          ← worker checkpoint
    ├── forecasts/           ← frozen predictions (D-004)
    ├── scripts/             ← extraction, adapter, bridge evaluation, analysis
    └── results/             ← manifests, controls, summaries (raw candidate files stay on the host)
```

## Dependencies

- Inputs: VeriBench experiment 103 (`results/summary.json`, per-cell factors) and experiment 102 (`results/tables/validated_per_candidate.csv`) with their private candidate files on `skampere1`; rl4cv experiments 01 and 08 outputs on `skampere1`; gold references at the `veribench` pin in `external/deps.lock.json`.
- No sealed data: experiment 107's human-round packets and experiment 109's sealed FSC/SCSC are not read.
- No model calls, no judge calls, no GPUs. Decisions D-004 (frozen forecasts), D-008 (fixed-reference check), D-013 (08's split; this study only evaluates).

## Status

| Step | Status |
|---|---|
| Design and frozen forecast | Done (10-09-2026) |
| Input preflight under A1 | PASS: published values 11/11, joins pass, compile reproduction 100/100 |
| Hidden-test extraction and adapter controls | PASS under A2: C1 591/591, C2 48/50, C3 44/50, C4 49/50; all original 50 tasks |
| Protocol lock | LOCKED 10-09-2026 after all four controls pass; code `a1d985c` |
| Evaluation and analysis | DONE 10-10-2026: 43,840/43,840 cells; P1 ρ=0.891, P2 area=0.640, P3 ρ=0.151; all frozen predictions hold; applicability 3,224/4,674 (69.0%) |
| Interpretation and inspections | 20/20 inspected; helper mapping and partial applicability limit semantic-correctness claims; frozen lexer defect documented in results |
| Verification | Repository 237 passed / 24 skipped; experiment-local 32 passed; all forecasts and lock hashes unchanged |
