# Experiment 02A v2 — FVAPPS external pool and 24-task candidate panel protocol

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v2/PROTOCOL.md>

**TLDR:** This protocol freezes only source identity, contamination screening, and outcome-blind candidate selection for an external 24-task panel. The candidate panel is blocked from fixed-reference scoring, repair evaluation, training, and checkpoint selection until every selected task has an accepted Lean 4.22.0 reference without admissions and a frozen disjoint allocation.

## Frozen source and selection

- Dataset: `quinn-dougherty/fvapps`, revision `3552a173e74837dd0017d72431c6ede8fa903bb7`, `train.jsonl` SHA-256 `e0874ed37ab4c0a1e727cc2e11fdc9d4add5f34316ddc726b1f3922d60146bc1`.
- Eligible rows: exactly `assurance_level == guarded_and_plausible` with nonempty `spec` and `units`.
- Screening text: the concatenation of `apps_question`, `spec`, and `units`; protected corpus: every VeriBench `py_src/*.py` plus non-build, non-playground `lean_src/*.lean` file.
- Exclusion: normalized exact hash matches are removed; word-5-gram Jaccard similarity at least 0.70 is removed.
- Selection: stable ascending SHA-256 of canonical source fields, first 24 clean rows. No model outcome, repair outcome, test result, or human rating may affect ordering or replacement.

## Reference gate

FVAPPS provides theorem *statements* and executable stubs, not accepted Lean implementations or proofs: its `spec` field contains `sorry`. A candidate remains `SCREENED_CANDIDATE_PENDING_REFERENCE_ACCEPTANCE` unless a separately materialized reference compiles under Lean 4.22.0, every named obligation has only `propext`, `Classical.choice`, or `Quot.sound`, and non-vacuity is checked. The original `units` cannot by itself validate a `sorry`-defined executable because Lean blocks `#eval` through `sorryAx`.

## Decision rule

Continue only if at least 24 candidates remain after a fresh remote rerun and all 24 receive independently accepted references before allocation. Otherwise report the shortfall; do not replace tasks after observing model behavior.
