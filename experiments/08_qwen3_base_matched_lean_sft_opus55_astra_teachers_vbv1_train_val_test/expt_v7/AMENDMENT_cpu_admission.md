# Diagnostic CPU admission adjustment

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v7/AMENDMENT_cpu_admission.md

**TLDR:** Keep two diagnostic compiler workers active alongside the eight v6
control scorers, for at most ten combined compiler processes. Preserve the
original protocol and every existing model/check result.

Recorded 10-19-2026 03:59 PDT, after generation and before this continuation.
All 100 generation cells are complete. Exactly 30 diagnostic result records
were complete when the initial queue policy began waiting for the eight control
scorers. The original coordinator and checking stage remain as historical receipts.

The current host has 128 CPUs, load average 33.46/43.14/38.26 and 1.7 TiB
available RAM. Two additional single-thread diagnostic Lean processes fit this
observed headroom. Version 6 retains its exact eight-worker maximum and all its
existing jobs. Version 7 retains its two-worker maximum and original two-hour
checking deadline, including time already spent waiting.

End only the owned diagnostic checker while it is waiting and has no compiler
children. Preserve its deliberate termination receipt and the coordinator's
terminal record. Continue checking through `resume_checking.py`, which imports
the unchanged, hash-verified checker and replaces only the CPU-admission wait.
Already completed per-function records are read unchanged; remaining cells are
checked once. No model generation, source repair, correctness retry, scorer or
criterion change is introduced. Keep the original model identity and raw-generation
hash beside the new resource-admission receipt.
