# Experiment 13 Phase 0: exact strict controls and declaration diagnostics

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v1/PHASE0_CONTROL_PLAN.md>

**TLDR:** The executable entry point freezes authored controls and runs the pinned strict scorer. Historical declaration scoring remains gated on a real adapter, source manifest and L1; this is not a completed measurement.

The binding definitions and gates are in `../PROTOCOL.md` §§1–3. `src/rl4cv/e13.py` validates typed, source-bound receipts; it is not a Lean declaration parser. Its strict channel calls the existing reward implementation, and the original 11 input hashes remain unchanged in `../REVIEW_REQUEST.json`.

1. Run `phase0_prepare.py` with the paths in `RUNBOOK.md`. It checks scorer bytes/toolchain and split/source manifests, freezes L0 and fixture source bytes, then executes authored strict controls. Each fixture has raw compile/axiom evidence and an independent expected label. Its output is write-once. It makes no model call or historical factor measurement.
2. Implement the declaration adapter in the owned experiment directory, using Lean elaborator command spans and fully qualified theorem identities. Regex-only diagnostic attribution is insufficient. Apply the full fixture list in the protocol; handle error recovery and dependency taint. Preserve official compile status separately from declaration cleanliness. Compile-only fixture success does not qualify this adapter.
3. Freeze L1, F0/F1, every source receipt/response hash and cell ID, grouped validation folds and the exact adapter/config. The available ladder cohort has 20,520 cells; the parent ladder still declares 25,920 with 5,400 missing. Build an equality manifest for all 21,504 historical base-model cells, reusing the overlapping 3,240 validation cells. Source absence blocks the control; no resampling or denominator reduction.
4. Run all train/validation comparisons with the typed receipt checker; execute the complete sealed historical-test equality audit through its separate locked process. Its public receipt exposes only count/hash/equality status. Do not fit on it or inspect individual test outcomes. Test-scoped rows are rejected by the ordinary harness.
5. Only complete exact reproduction admits G0; a G0 pass admits Phase 1. Mutation audits, independent coverage checks and LP precede B/C training. Padding and dropping hard obligations remain known vulnerabilities of the experimental fractions, not bugs in the immutable official strict metric.

The first phase-0 command is concrete and CPU-only (central processing unit). No prior reproduction result is needed to run it. Remaining adapter/sealed-audit implementation is explicit in `PHASE0_READY.json`; master may dispatch that work immediately. Training requires later gates and measured resources.
