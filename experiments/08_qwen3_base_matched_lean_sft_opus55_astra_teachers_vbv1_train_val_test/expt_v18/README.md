# V18: Finish explicit proof cleanup of the original 2,585 training answers

**Doc link:** [Protocol](PROTOCOL.md)

**TLDR:** Continue all 1,540 remaining original-pool proof repairs in a new immutable run. Reuse 818 verified V13 files, kernel-check the 227 unchanged originals, and admit only verified explicit files to the fully cleaned training pool; unresolved cases are explicit exclusions, never automated fallbacks.

## Status — 10-19-2026

The user explicitly stopped paid proof generation and requested immediate training from available strict examples. The immutable snapshot is ready: **800 admitted** sources, all 2,585 originals accounted, and 1,785 exclusions. Of the 1,050 sources with current kernel evidence at cutoff, 250 lack requested commentary (227 lack the sketch header; 23 lack inline comments). Their proofs remain preserved outside training. The admitted pool contains 795 inherited Terra repairs, 1 new Terra repair and 4 CPU-only reflexivity repairs.

All paid proof workers and the CPU prescreen are stopped. V18 total configured estimates are $3.337045 conservative and $1.689919 ordinary rate, with zero cleanup reservations. The first mixed-length sample verified 0/4 (all four failed; QA 11-25-2026 wording fix); the shortest-four sample yielded one exact checked proof before the user stop. The prospective full-pass cost forecast was not supported and full cleanup is not claimed. No Lean recompilation or model call was used to freeze the available pool.

## Components

- `repair_batches.py`: immutable case preparation, inherited receipts, focused four-file workers, exact full-file checks, original-source audit.
- `controls.py`: mock extended-cap/activation/idempotent-settlement checks and actual unchanged frozen kernel/policy controls.
- `watch_batches.py`: ordinary 15-second remote supervision of death, orphaned healthy children, funding/budget holds, audit and finalization.
- `finalize_full.py`: accepted-only final training data, complete 2,585-row accounting, unchanged prompt/FILE/template/cap gates, protected screens and bound completion hashes.
- `mechanical_prescreen.py`: CPU-only prescreen of the existing reflexivity candidate, with no API calls and unchanged checker/candidate limits.
- `CKPT_full_cleanup.md`: precise continuation state.

The final output is `lean_corpus_v18/final/fully_cleaned_existing_training.jsonl`, SHA256 `bc29f309b387cbf27f9e5e89c5ca66c81137d8a5fe67d617dff5738e6f93f998`. `completion.json` binds the data, 800 exact portable proof receipts, 764-reference protected screen (0 exact/0 near) and complete outcome table. Its explicit state is `USER_STOPPED_PARTIAL`, with `all_remaining_batches_attempted=false`. V20 owns the new training run from the original Qwen3-1.7B-Base initialization; earlier V12/V13 frozen data remain unchanged.
