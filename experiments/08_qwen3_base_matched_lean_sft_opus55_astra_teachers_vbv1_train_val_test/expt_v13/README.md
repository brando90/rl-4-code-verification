# V13: Explicit proofs for the original Python-to-Lean training pool

**Doc link:** [Protocol](PROTOCOL.md)

**TLDR:** Rewrite broad proof automation in the original 2,585 complete Python-to-Lean teacher answers. Keep task semantics and executable tests fixed, verify every accepted replacement, and supply a matched second 1.7B training run with honest original fallbacks.

## Status — 10-19-2026

All 2,585 files parsed successfully; 2,358 answers have targeted automation and 227 need no replacement. The first four real Terra/high cases passed kernel, FILE/template and protected-overlap checks. Full dispatch is active: 23 concurrent paid workers under shared exposure reservations, with 12 kernel-verified replacements at the latest collected snapshot. The ordinary remote supervisor handles death, quota holds, budget settlement, the preapproved second tranche and complete fallback accounting before automatically releasing the matched second training run.

## Files

- `clean_existing.py`: frozen source preparation, proof-only reconstruction, kernel checks and Terra CLI workers.
- `proof_ranges.lean`: actual Lean parser extraction of original proof-term ranges.
- `budget_ledger.py`: shared campaign exposure reservations, usage guard and conservative charges.
- `finalize_cleaned.py`: full denominator accounting, FILE/template/protected-screen gates and replacement contract.
- `watch_cleaned.py`: remote liveness/recovery, budget and finalization supervision.
- `guard_controls.py`: harmless actual-child usage termination and dead-driver controls.
- `sync_cleanup.py`: compact receipt and live-report collection, without Git mutations.
- `PROTOCOL.md`: fixed model, scope, bounds, acceptance and outputs.
- `results.md`: live measured results.
- `CKPT_cleanup.md`: exact continuation state.

No additional datasets or validation content enter these teacher inputs. The experiment tests proof presentation and explicit reasoning while preserving each original Python-to-Lean assignment.
