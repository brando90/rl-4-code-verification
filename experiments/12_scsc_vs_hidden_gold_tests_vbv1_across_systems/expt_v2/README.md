# Experiment 12 version 2 — corrected prospective hidden-test adapter (SCSC versus hidden gold-reference tests, VeriBench V1, 11 systems)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/README.md>

**TLDR:** Version 1 (DONE 10-10-2026) showed that SCSC, the smooth conjunctive score for code verification, tracks hidden gold-reference tests on VeriBench V1 (P1 Spearman 0.891, P2 area 0.640, P3 Spearman 0.151, applicability 3,224/4,674 = 0.690), but its inspection found that the frozen adapter sometimes tested a precondition helper instead of the model's entry point and counted partially applicable cells as failures. Version 2 is the corrected, prospective rerun of the same question on the same saved outputs with zero model calls: a Lean-faithful identifier lexer, an explicit entry-point priority order that never prefers helpers, and per-test applicability. This round (10-14-2026) delivers the design, the adapter with 64 passing unit tests, zero-compilation static controls over all 882 gold suites and a mapping census on the host, a locked protocol (one dated amendment, V2-A1, after the static controls) and a frozen forecast (plus its amendment note). The Lean evaluation (4,626 compiling primary cells, optionally the 33,984 secondary cells) is Emily Xia's run, scripted in [cc.md](cc.md). No hidden-test outcome has been computed in version 2.

**Owner:** Emily Xia (@emxia18), with Ethan Li (@lethan3) advising. **Prepared by:** a Claude Code worker (claude-fable-5-1) for Brando's 10-14-2026 progress push. **Status:** see [results.md](results.md) and [CKPT_e12_v2.md](CKPT_e12_v2.md).

## Why a version 2

The version-1 adapter and outcomes are frozen (protocol lock `a1d985c`, 43,840/43,840 cells). Its inspection of 20 selected disagreements (`../results.md`, "Inspected disagreements") attributed the high-score failures to the adapter, not the models: 6/10 mapped a `*Condition`/`pre*`/`post*` helper, 4/10 had only some gold tests evaluable at the candidate's types, and the root cause of the helper cases was an identifier lexer without `?`/`!` suffixes. A changed adapter is a new version, never an edit of frozen bytes (D-004). Version 2 therefore:

1. fixes the lexer, the entry-point rule and the applicability bookkeeping ([DESIGN.md](DESIGN.md));
2. measures, without compiling anything, how the mapping changes over the 11 primary systems' saved files ([results.md](results.md), `results/mapping_census_v2.json`);
3. locks a protocol ([PROTOCOL.md](PROTOCOL.md)) and freezes a forecast (`forecasts/`) before any version-2 hidden outcome exists;
4. hands the evaluation to the owner with exact commands ([cc.md](cc.md)).

## Goal, hypotheses and decision criterion

- **Uncertainty.** Does SCSC's agreement with hidden gold tests survive an adapter that tests the model's actual entry point and does not count unevaluable tests as failures? Version 1's agreement could in principle be inflated or deflated by the mis-mappings.
- **Panel.** Unchanged from version 1: 11 primary systems × 896 tasks (VeriBench experiments 103 and 102), factors and compile status as recorded in `../expt_v1/results/input_manifest_A1.json`; hidden tests as frozen in `../expt_v1/results/hidden_tests_manifest.json` (10,534 tests, 882 tasks). Secondary panels (experiments 01 and 08 validation) are optional descriptives.
- **Predictions** (thresholds carried from version 1; the point predictions and the expected direction relative to version 1 are frozen in `forecasts/e12_v2_forecast.json` after the census and before any evaluation):

  | Id | Claim | Frozen threshold | Version 1 | Expected direction in version 2 |
  |---|---|---|---|---|
  | P1 | Spearman(system SCSC, system hidden all-pass rate) over 11 systems | ≥ 0.80 | 0.891 | about unchanged |
  | P2 | System-stratified area under the ROC curve of per-cell SCSC for `hidden_all_pass`, fully applicable compiling cells | ≥ 0.60, interval excluding 0.50 | 0.640 | up |
  | P3 | Pooled within-system Spearman(per-cell SCSC, hidden pass rate) | > 0, interval excluding 0 | 0.151 | up |
  | G-A | Fully applicable / compiling cells with tests (stricter than version 1's ≥ 1 evaluable test) | ≥ 0.50 | 0.690 (≥ 1 evaluable) | 0.55–0.70 fully applicable; ≥ 1 evaluable about unchanged or up |

- **Reading the outcome** (written before measuring): P1 and P2 hold with P2 above 0.640 → the version-1 claim stands and was conservative. P2 falls below 0.640 with the same cohort size → the version-1 agreement partly reflected the helper mappings; report both. G-A fails → LIMITED COVERAGE; analyses still run with bounds.

## What this round produced (zero model calls, zero Lean compilations)

- `scripts/adapter_v2.py` — lexer, declarations, signatures, helper rule, entry-point selection, per-test plan, bridge and cell outcome; imports version-1 helpers read-only.
- `scripts/mapping_census_v2.py` — static mapping over the 4,626 compiling primary cells with tests, compared with the version-1 receipts' mapping fields only.
- `fixtures/disagreement_skeletons_e12v2.json` — declaration skeletons (names, headers, own example statements; no bodies) of the 20 inspected candidates with their gold symbols and tests.
- `scripts/static_controls_v2.py` — zero-Lean gold-self and renamed-gold controls over all 882 suites (`results/static_controls_v2.json`: 882/882 and 0/882 wrong).
- `tests/test_e12_adapter_v2.py` (repository `tests/`) — 64 tests: 10 lexer cases, 16 helper-name cases, 13 affinity cases, the 20 inspected rows, per-test applicability, bridge format, 5 version-1 control fixtures.
- `results/mapping_census_v2.json` and the tables in `results.md`.
- `PROTOCOL.md` (locked; § 8 amendment V2-A1), `forecasts/e12_v2_forecast.json` and `e12_v2_forecast_amendment_A1.json` (frozen), `cc.md`, `CKPT_e12_v2.md`.

## Structure

```
expt_v2/
├── README.md            ← this design doc
├── DESIGN.md            ← lexer grammar, priority order, per-test applicability, expected movement
├── PROTOCOL.md          ← locked before any version-2 hidden outcome
├── results.md           ← census now; evaluation results when Emily runs it
├── cc.md                ← Emily's runbook (commands, compute estimate, host layout)
├── CKPT_e12_v2.md       ← checkpoint
├── fixtures/            ← the 20 inspected disagreement skeletons
├── forecasts/           ← frozen forecast (D-004)
├── scripts/             ← adapter_v2.py, mapping_census_v2.py, freeze_forecast_v2.py
└── results/             ← mapping_census_v2.json; evaluation receipts and analysis later
```

## Dependencies and limits

- Inputs are the version-1 manifests and the saved candidate files on `skampere1` (`/lfs/skampere1/0/brando9/rl4cv_e12/`, read-only for this round); gold references at the `veribench` pin `c11b99ba`.
- No model calls, no judge calls, no GPUs; the evaluation needs CPU Lean (v4.22.0 + Mathlib) in the frozen grading project, as in version 1.
- Sealed data (experiments 107 and 109) and experiment 08's test split are never read. Decisions D-004, D-008, D-013.
