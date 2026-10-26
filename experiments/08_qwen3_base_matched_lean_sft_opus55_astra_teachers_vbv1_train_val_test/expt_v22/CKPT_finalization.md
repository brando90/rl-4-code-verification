# expt_v22 — Sol review delta admission handoff

## State (10-19-2026)

- Admission source owner: `unattended_and_gap_sources`; review worker/deployment owner: `cleanup_original_pool`.
- Source ready: `finalize_review.py` SHA-256 `e97fb51ae800e17e19e40fde1be9fa71426c674b9ec3d35999ccf25baa14adde`.
- Finalization requires the exact immutable `CLOSED` cohort manifest, final experiment 21 completion, and terminal outcomes for every one of the N review cases.
- The cohort must equal all terminal experiment 21 `EXCLUDED_BOUNDED_REPAIR` tasks, with exact original task/index mappings and first-pass status hashes.
- Output is an accepted-only delta, `lean_corpus_v22/final/repaired_tiny_training.jsonl`; all N outcomes and portable proof/failure receipts are retained. Experiment 21 and running experiment 20 remain unchanged.
- Reuses pinned experiment 21 strict scope, exact receipt, pure comment-only, tokenizer, protected-reference and portable evidence helpers. Dedup includes final experiment 21 accepted rows and the immutable live experiment 20 baseline.
- Controls pass: unchanged strict scope controls plus six review-cohort controls. See `results/finalization_controls.json`.
- Actual preflight passed 5/5 then-accepted Sol sources, maximum assistant loss span 271 tokens; the dynamic cohort contained 28 cases and remained open. This is not the final declared-cohort result.
- Source generation, controls and preflight made zero model calls and zero Lean compilations.
- Command after closure and all terminal outcomes: existing training virtual-environment Python, `finalize_review.py --baseline /lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v20/base/data/training.jsonl`.
- Final publication is atomic, followed by root completion; failed build directories never become training inputs.

## Event log

- 10-19-2026: Delivered the strict closed-cohort delta finalizer, amendment, controls and actual five-source preflight to the review worker/deployment owner. Requested immutable cohort-closure receipts from the source owner.
