# Repair unresolved Workbook proofs with explicit tactics

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v11/README.md

**TLDR:** The user authorized Sol to repair the68remaining unresolved proof scripts, including writing replacement proofs. This lifts the earlier supplied-alternative-only restriction while keeping target statements fixed.

[Protocol](PROTOCOL.md) · [Results](results.md) · [Checkpoint](CKPT_repairs.md)

`repair_proofs.py prepare` freezes inputs and creates16isolated workers; `selftest` verifies the checker; `launch` starts Sol/high. Each model writes `proof.lean`, optional `support.lean` and `sketch.txt` in its assigned case folder. The coordinator assembles the unchanged statement, snapshots/checks exact bytes, and retains only actual verified final files.

Runtime: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v11/`. All original outcomes remain under adjacent version9/10folders. Only these68cases are assigned; all bulk/GX10checks continue independently. All 68 repairs passed final format/template/protected-screen checks; 61 unique rows are ready for downstream assembly.
