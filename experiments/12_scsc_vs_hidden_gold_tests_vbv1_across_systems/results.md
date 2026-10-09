# Experiment 12 results — hidden gold-reference tests on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/results.md>

Experiment `12_scsc_vs_hidden_gold_tests_vbv1_across_systems` phase A audited 11 systems × 896 VeriBench V1 tasks with zero model calls and stopped at the prespecified aggregation gate before hidden-test evaluation.

**Status:** BLOCKED — PROTOCOL § 6 aggregation mismatch; evaluation has not begun.
**Last updated:** 10-09-2026 14:44 PDT

The smooth conjunctive score for code verification (SCSC) required by this protocol is the geometric mean of three factor means: internal consistency of tests (IC_tests), internal consistency of proofs (IC_proofs), and formal specification coverage (FSC). Experiment 103 instead publishes the mean of per-file SCSC on a measured subset. Those operations differ. Experiment 102 publishes the required geometric-of-means aggregate and reproduces correctly.

| Step | Status | Evidence |
|---|---|---|
| Launch and forecast verification | DONE | Launch pushed in `392ed49`; frozen forecast verified before input audit |
| Primary factor inventory and candidate hashes | DONE, with unresolved joins listed | All 9,856 cells retained in [input manifest](expt_v1/results/input_manifest.json) |
| Published aggregate reproduction | BLOCKED | 7/11 systems differ at three decimals; [audit](expt_v1/results/aggregation_preflight.json) |
| Gold inventory, secondary joins, 100-file compile reproduction | NOT RUN | Later preflight stages short-circuited by mandatory stop |
| Hidden-test extraction and adapter controls | NOT RUN | Aggregation gate failed |
| Protocol lock | NOT LOCKED | No changes to the protocol or forecast |
| Evaluation and analyses | NOT RUN | No hidden-test outcomes |

## Aggregation gate

All values below use the same measured cohort within each row. The factor means and geometric-of-means columns are recomputed from the exact protocol inputs. The published experiment-103 column is transcribed programmatically from its seven-row results table and agrees at three decimals with the recomputed mean of per-file SCSC. Experiment-102 values come from `VALIDATED_TABLES.json` → `all896_fixed_validated`. The match threshold is PROTOCOL § 6, not an outcome-dependent choice.

| Source / system | Common measured / declared | IC_tests | IC_proofs | FSC | Required formula, measured cohort | Published SCSC | Match at 3 decimals |
|---|---:|---:|---:|---:|---:|---:|---|
| VeriBench 103 / `claude-opus-5-max` | 681/896 | 0.607930 | 0.607403 | 0.736564 | 0.647908 | 0.605000 | FAIL |
| VeriBench 103 / `gpt-6-astra-high` | 855/896 | 0.523977 | 0.523707 | 0.966433 | 0.642476 | 0.522000 | FAIL |
| VeriBench 103 / `gpt-5.6-sol-high` | 889/896 | 0.388076 | 0.388076 | 0.920866 | 0.517619 | 0.383000 | FAIL |
| VeriBench 103 / `gpt-5.6-luna-high` | 890/896 | 0.162921 | 0.162921 | 0.855506 | 0.283178 | 0.158000 | FAIL |
| VeriBench 103 / `gpt-6-luna-high` | 888/896 | 0.143018 | 0.139764 | 0.881869 | 0.260254 | 0.140000 | FAIL |
| VeriBench 103 / `gemini-3.1-pro-high` | 889/896 | 0.057368 | 0.054435 | 0.866142 | 0.139330 | 0.053000 | FAIL |
| VeriBench 103 / `qwen3.6-27b-thinking` | 604/896 | 0.001656 | 0.001656 | 0.899421 | 0.013509 | 0.002000 | FAIL |
| VeriBench 102 / `claude_code` | 896/896 | 0.977679 | 0.977416 | 0.964174 | 0.973069 | 0.973069 | PASS |
| VeriBench 102 / `codex` | 896/896 | 0.998884 | 0.998724 | 0.918192 | 0.971176 | 0.971176 | PASS |
| VeriBench 102 / `leanstral` | 896/896 | 0.508929 | 0.534202 | 0.652679 | 0.561937 | 0.561937 | PASS |
| VeriBench 102 / `baseline` | 896/896 | 0.286830 | 0.289062 | 0.293638 | 0.289830 | 0.289830 | PASS |

The seven experiment-103 rows have 5,696/6,272 complete factor records; 576 lack at least one factor. Consequently, their protocol-defined **all-896 aggregates are unavailable**. The displayed measured-cohort values diagnose the formula mismatch; they are not substitutes for those unavailable aggregates. Missing factors were never assigned zero. This is a deterministic census and arithmetic consistency check: confidence intervals and p-values are not applicable (`p-val=n/a`); no inferential agreement claim is made.

## Candidate provenance and remaining joins

The manifest retains 9,542 hash-bound cells, 176 cells with a located file but no recorded hash, 136 cells with distinct original/recovery files and no authoritative hash, and 2 missing files. Hashes bind the original summary to candidate bytes; recovery bytes never silently replace the original. The manifest records every unresolved cell and both paths where ambiguous. No candidate contents are committed.

The two missing files are Codex `cs_set/floyd_warshall` and Leanstral `cs_set/binary_search`, both already recorded as missing generation outputs in experiment 102. Thus the strict file-absence count is 2/9,856 (0.0203%), below the protocol’s 5% stop threshold. This passes only that gate: 136 ambiguous joins and 176 files lacking a recorded hash still require resolution before evaluation. The 564 hash-bound empty experiment-102 baseline outputs remain in the manifest and denominator.

## Frozen predictions and secondary panels

| Prediction or gate | Result | Verdict |
|---|---|---|
| P1: system ranking agreement | Not measured; interval unavailable | UNTESTED |
| P2: discrimination beyond compilation | Not measured; interval unavailable | UNTESTED |
| P3: graded agreement | Not measured; interval unavailable | UNTESTED |
| G-A: adapter applicability | Not measured; interval unavailable | UNTESTED |

No inspected disagreements or hidden-test bounds exist yet. The experiment-01 and experiment-08 secondary evaluations have not run. The experiment-08 test split and sealed experiment-107/109 data were not read. No Lean compilation was launched after the gate failed, and no protocol lock, adapter, control result, or hidden-test manifest is claimed.

## Reproduction and continuation

The frozen forecast remains unchanged and verifies with `rl4cv.forecast.verify_forecast`; its canonical SHA-256 (Secure Hash Algorithm, 256-bit) is `b29b71b7166b80df653220ddddec4b865a622ef9abc1fa42c6c1e559b067b0c5`. The audit records exact input paths/hashes and its own code hash.

```bash
PYTHONPATH=src python3 experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/scripts/audit_inputs_e12.py
```

Verification: repository `make test` passed (188 passed, 24 skipped); all six experiment-local audit tests passed; manifest uniqueness, source/script/forecast hashes, and whitespace checks passed.

Exit status `2` is the expected mandatory aggregation stop. The script only reads existing factors and hashes candidate bytes; it performs zero generation, judging, and hidden-test calls.

Continuation requires a prospectively recorded resolution of two incompatible input assumptions: the published aggregation formula and the missing-factor denominator. Preserve this forecast and audit, keep the geometric-of-factor-means definition required by repository decision D-009, and explicitly define a common measured cohort plus missing-cell bounds before any hidden outcome is observed. A new forecast/version must record any changed estimand. Then resolve candidate joins and perform the remaining runbook gates. This is a recommendation for the master, not an amendment made by this worker.

**TLDR-end:** [rl4cv: 12_scsc_vs_hidden_gold_tests_vbv1_across_systems] Hidden gold-test agreement is unmeasured: the primary input audit hit the frozen aggregation stop in 7/11 systems. All 9,856 cells and the unchanged forecast are preserved; no model calls were made.
