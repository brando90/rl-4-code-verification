# Protocol for the existing artifact feasibility audit

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/PROTOCOL.md>

**TLDR:** Version 1 is a retrospective, zero-model-call inventory. It cannot establish an intervention effect or a new benchmark score.

This protocol is frozen before the new audit computation. Earlier reports and selected example rows have already been read; this is NOT a prospective prediction. Never rewrite the frozen version to fit the audit. A changed scientific setup gets `expt_v2/` and a separate protocol before any measured model calls.

## Scientific question (locked)

Do retained artifacts support a defensible correlation between the Smooth Conjunctive Score for Code verification (SCSC) and an independently measured reference-success outcome, and what prevents a causal intervention experiment from starting?

Decision criterion: permit correlation only if records contain an independently defined, trusted endpoint joined by immutable candidate identity, with both success classes and nonconstant scores. This is an identifiability gate, not a statistical-power guarantee. Otherwise record NOT IDENTIFIABLE and implement endpoint validation before new correlation claims. Historical replay labels alone do not pass the trust gate.

## Locked parameters

- Entire saved `results/summary.json` from VeriBench's `103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge`; no score-based row selection.
- Full declared original VeriBench V1 matrix: seven model configurations × 896 tasks. Report snapshot absence separately from measured failures; it does not establish the live job's status.
- VeriBench V1 core (614 tasks) and IndustrySet (282 tasks) remain separate. Version 2 and multifile conditions remain separate, including recoveries. No recovery wins replace original failures.
- Historical `adapter_status.csv` and `pair_kernel.csv` from `75_J1_validating_formal_spec_judge_train_val_test/prover_diagnostics`: inventory only. Their historical field names do not certify strict kernel trust.
- Immutable input hashes plus source revision/path in `expt_v1/input_manifest.json`; full bytes stored in ignored `expt_v1/inputs/`, durable copy on Stanford Network Analysis Project (SNAP).
- No generation, judge, training or prover calls; zero graphics processing unit hours and zero incremental provider charges. One processor, proposed maximum five minutes for the audit itself; health checks/transfers are separate.
- Descriptive counts cover this fixed snapshot, not a random sample. Confidence intervals and p-values are not applicable to file/schema counts. Do not estimate intervention effects, correlation, or score levels from missing endpoints.
- A zero per-artifact SCSC is mathematically identifiable when an explicitly observed factor is zero. Missing factors are never coerced to zero. Store supplied score availability separately from this mathematical diagnostic.
- No scoring implementation, reference, frozen input, dependency pin or old report is edited.

## Scale verification (no further normalization)

SCSC and its three factors are already on [0,1]. Do not divide formal specification coverage by five again. Historical replay fields are reported as stored labels only; no calibration makes them strict kernel outcomes.

## Verified data schema

`summary.json`: `rows` with `benchmark`, `model`, `task`, `cell_status`, `condition` when supplied, `IC_tests`, `IC_proofs`, `FSC`, `SCSC`. Version 1 also includes `solution_sha256` and `sanity_verdict` where available. The audit must not invent hashes for missing artifacts.

`adapter_status.csv`: `task_id`, `system`, `solution_sha`, `adapter_status`, `n_gold_properties` and provenance fields.

`pair_kernel.csv`: `gold_key`, `system`, `split`, `n_properties`, `n_proved`, `n_disproved`, `n_unproved_budget`, `n_unstatable`, `kernel_decision`; these are historical bounded-search results, not accepted new correctness measurements.

## Completion and reproducibility

Hash-check every input before reading, account for every supplied row, reject duplicate candidate keys within a condition, and emit JSON plus a readable report. Record actual host, start/end, script hash and exit code. No persistent model worker is needed for this deterministic command. The named remote terminal session owns the bounded command and records its terminal receipt. The coordinator verifies and publishes outputs. A missing or mismatching input stops the audit without silently narrowing its scope.

`expt_v1/cc.md` gives continuation instructions. The larger causal program remains PLANNED after this inventory completes.
