# 11-25-2026 — Experiment 02 real-task behavioral adapter repair

**Date:** 11-25-2026.
**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/adapter_11-25-2026/README.md>

**TLDR:** A new mechanical VERINA adapter supports **24/24 frozen real tasks**, with **158/158 fixed behavioral tests passing**, in an actual Lean 4.22.0 run. All 12 regression tests passed, exit 0. The historical 0/24 generic-endpoint result stays unchanged. This fixes the behavioral interface path, not reference-proof acceptance or production rollout isolation; #6 remains open and no GPU training was launched.

Harness: Codex CLI, GPT-6 Astra ultra (Vals account). The support count comes from actual Lean compilation/evaluation, not a mock or model reading. Candidate and wrapper axioms and all 158 concrete precondition witnesses were checked against `propext`, `Classical.choice`, and `Quot.sound`. Behavioral outputs use Lean evaluation; they are **not 158 proofs of the complete postconditions**. No DT: no differential comparison with Python. No solver/judge/model API calls and no GPU jobs.

## Cause and repair

The old exp04 version-3 applicability program unconditionally assigned `unsupported_adapter` to each real VERINA task because its evaluator only accepted a bounded JSON natural-number-to-natural-number expression language. Real tasks instead use `Int`, lists, arrays, strings, options, a public `Map` structure, helper definitions and preconditions. The 24 authored controls had never exercised those interfaces.

`verina_adapter.py` consumes the existing hash-locked external24 manifest and validates all original source-file hashes. It reads the upstream benchmark section markers without renaming arbitrary Lean declarations. It compiles a candidate module containing the fixed public interface and the three candidate implementation fragments, then materializes a separate evaluator module containing the fixed tests and postcondition definitions. Reference proof bodies are never copied into candidate inputs. A typed wrapper verifies argument order and return type; where the original callable omits a precondition argument, the wrapper still requires that precondition without adding an argument to the callable. JSON primitives are rendered according to their declared Lean type, including quoted strings.

The evaluator proves a concrete precondition witness for each fixed test, preserves every declared test, checks candidate/wrapper and witness transitive axioms, and records compiler return codes and full stdout/stderr. A wrong behavioral output is a measured failure; missing output, a failed type/interface check, or an untrusted witness is not silently scored zero. The source, interface, candidate and fixed requirement hashes are separate.

Regression controls use the **real** `verina_advanced_12` task. Its original implementation passes 8/8 tests; an always-`none` implementation passes 2/8 with byte-identical evaluator requirements. A Boolean return fails the expected `Option Int` interface. An auxiliary definition using `sorryAx` compiles but is rejected by the transitive-axiom check. Controls also reject attempts to replace evaluator primitives. The lexical filter is defense in depth, **not an operating-system sandbox or complete sanitizer for hostile Lean**.

## Evidence and scope

- [Final real24 receipt](real24_receipt_11-25-2026.json): 24 distinct manifest tasks, 24 supported, 158 measured behavioral tests, all passing. Source revision `66b3ce5014edafb20cb26b87c681e7f31847249f`; manifest SHA-256 `026fd9ed3058f28505a00ac2329e6ca36c872ea770e95a7e6f343cdcfea8ddef`; exact adapter hash and timestamps are in the receipt.
- [Pytest transcript](pytest_11-25-2026.log): **12 passed, exit 0**, 150.59 seconds; [retained compiler stdout/stderr](compiler_logs_11-25-2026/). Generated Lean modules remain under `/lfs/skampere1/0/brando9/rl4cv_at3598/pytest_adapter_final_11-25-2026/` at the paths in the receipt.
- [Runtime identity](runtime_11-25-2026.json): Lean library paths and workspace configuration hashes. Existing dependency directories were read, not changed.
- Development attempts remain in the workspace: run1 stopped on section-marker parsing; run2 stopped on numeric JSON serialization; run3 exposed optional precondition arguments and comment handling; run4 completed at 20/24 because four string-valued tasks were not yet quoted. The final full run includes all fixes and all 24 tasks. No failed attempt was relabeled successful.

**Original beside new:** historical generic endpoint applicability **0/24** versus new **behavioral adapter support 24/24**. These are different gates. The old reference diagnostics remain 6/24 original reference theorems kernel-honest, 16/24 with forbidden trust, and 2/24 unknown after original-source compilation failure. This run does not change or repair those reference proofs, accept an external reference pool, measure full formal-specification coverage, or claim the original repair/training admission gate passed. The known panel is development/validation evidence, not a fresh held-out confirmation set.

## Reproduce

Use the source revision and library paths from the receipts. With `VERINA_ROOT`, `VERINA_LEAN` and `VERINA_LEAN_PATH` set to the pinned checkout, Lean 4.22.0 binary and retained dependency path list:

```bash
python3 -m pytest -q experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/adapter_11-25-2026
```

The real-task tests explicitly skip without those dependencies; a skipped run must never be reported as 24/24 support. The standalone CLI supports `--manifest`, `--verina-root`, `--lean`, `--lean-path`, `--out` and `--timeout`; it refuses to overwrite an existing output directory.

02B/03 launch preparation and remaining gates are in the [dated 02B launch note](../phase_b_prospective_2x2_forecast_check/expt_v2/launch_note_11-25-2026.md) and [SNAP status](../../../docs/qa_11-25-2026/snap_status_at3598_11-25-2026.md). GPU approval is already given; available H200 capacity does not supply accepted references, a production Lean rollout/training configuration, the required external-only warm start, pre-RL probes, a prospective forecast, or exp03's missing locked protocol.
