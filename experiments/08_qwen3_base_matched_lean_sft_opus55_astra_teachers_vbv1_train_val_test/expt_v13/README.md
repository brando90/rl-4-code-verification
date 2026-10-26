# V13: Explicit proofs for the original Python-to-Lean training pool

**Doc link:** [Protocol](PROTOCOL.md)

**TLDR:** Rewrite broad proof automation in the original 2,585 complete Python-to-Lean teacher answers. Keep task semantics and executable tests fixed, verify every accepted replacement, and supply a matched second 1.7B training run with honest original fallbacks.

## Status — 10-19-2026

Completed as a partial cleanup phase: **818 replacements passed kernel, FILE/template, token-cap and protected-overlap checks**, with zero overlap hits across 764 protected references. All 2,585 rows are accounted for: 818 replacements, 227 unchanged originals needing no automation rewrite, and 1,540 explicitly flagged original fallbacks. The bound completion receipt released V12's second training preparation automatically. At 10:25 PDT, admission was frozen because conservative reservation headroom had reduced the pool to one worker and delayed that comparison; the last admitted case finished successfully. See the [prospective freeze amendment](AMENDMENT_freeze_comparison.md).

Ordinary-rate model-cost estimate: $237.391247; conservative ledger charge: $469.991219; no cleanup reservations remain. These are configured-price estimates, not an invoice. The final [contract receipt](results/final_contract_receipt.json) verifies row counts/order, unchanged prompts, original fallback bytes and both output hashes.

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
