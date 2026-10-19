# 1.7B seen-versus-fresh tiny-function diagnostic

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v7/README.md

**TLDR:** One greedy inference per each of 50 seen training functions and 50
fresh compositions, from the completed augmented 1.7B checkpoint. Check output
format, Lean compilation, kernel proofs and 32 Python differential cases per task.
No additional training is authorized by or performed in this diagnostic.

- [Prospective protocol](PROTOCOL.md)
- [Live results](results.md)
- [Continuation checkpoint](CKPT_seen_fresh.md)
- [Manifest builder](build_diagnostic.py), [checker](check_diagnostic.py),
  [persistent coordinator](run_diagnostic.py)

The fresh set is structurally disjoint from normalized existing function bodies
while using familiar primitives. It includes new compositions and can be harder;
the cohort difference is descriptive. Finite differential tests do not establish
universal equivalence or reference-specification coverage. This is distinct from
the 135-task benchmark validation and never opens the 222-task benchmark test.

## Storage and execution

Sources live at this experiment-relative path in the owned cluster checkout.
Runtime root:
`/lfs/skampere1/0/eth127/rl4cv_tiny_training/diagnostic_seen_fresh_v7`.
Its `manifest.jsonl`, `screening.json`, `admission.json`, `cells.json`,
`model_identity.json`, controls, stage receipts and complete per-function results
are mirrored into `results/` here. Bulky raw responses, extracted files and
compiled kernel evidence remain under that cluster root. Their identities and
retrieval paths are retained in the compact receipts.

Status: COMPLETE, 100/100 checked. Final continuation session was
`rl4cv-tiny-seen-fresh-12`; completed sessions may exit. Coordinator logs, stage
receipts and status are saved in the runtime root. Generation releases its GPU
before CPU checking. Resource amendments increased checking from two to twelve
workers, preserving completed results and the original deadline.

This phase remains in the active experiment home because its interpretation
depends on the still-running version-6 matched control and 4B evaluation.
