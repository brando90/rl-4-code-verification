# V18: Finish explicit proof cleanup of the original 2,585 training answers

**Doc link:** [Protocol](PROTOCOL.md)

**TLDR:** Continue all 1,540 remaining original-pool proof repairs in a new immutable run. Reuse 818 verified V13 files, kernel-check the 227 unchanged originals, and admit only verified explicit files to the fully cleaned training pool; unresolved cases are explicit exclusions, never automated fallbacks.

## Status — 10-19-2026

Source and prospective protocol are prepared. Deployment was interrupted when the existing SNAP SSH master died at 10:40:39 PDT; no V18 model call has started. The root coordinator is restoring the connection. Existing remote jobs and V13's immutable completed artifacts remain intact.

The new shared budget helper authorizes total campaign spending up to $900 including prior charges, with cleanup up to $780 and adaptation up to $120. Focused four-file Terra/high batches target an additional conservative $154–$308; the first actual batch will calibrate that uncertain forecast before scaling.

## Components

- `repair_batches.py`: immutable case preparation, inherited receipts, focused four-file workers, exact full-file checks, original-source audit.
- `controls.py`: mock extended-cap/activation/idempotent-settlement checks and actual unchanged frozen kernel/policy controls.
- `watch_batches.py`: ordinary 15-second remote supervision of death, orphaned healthy children, funding/budget holds, audit and finalization.
- `finalize_full.py`: accepted-only final training data, complete 2,585-row accounting, unchanged prompt/FILE/template/cap gates, protected screens and bound completion hashes.
- `CKPT_full_cleanup.md`: precise continuation state.

The final output is `lean_corpus_v18/final/fully_cleaned_existing_training.jsonl`; `completion.json` binds its hash and the complete outcome table. V19 owns the subsequent training run. V12/V13 completed data and watches are not altered.
