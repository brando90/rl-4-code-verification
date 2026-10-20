# V20: fresh-base 1.7B explicit commented-proof training

**Doc link:** [frozen prospective protocol](PROTOCOL.md)

**TLDR:** Train Qwen3-1.7B-Base from its original pretrained weights on the currently available checked examples with explicit proofs, proof-sketch headers and inline comments. New teacher generation is stopped; unresolved rows do not block this run.

## Goal and decision

Measure the frozen1,080-attempt VeriBench V1 validation binary success rate, targeting25%. The setup changes both initialization and the admitted dataset relative to V12, so results cannot identify which component caused any difference. Test data remain sealed.

## Contents and status

- [Protocol](PROTOCOL.md): prospective data gates, training defaults, resource plan and full evaluation.
- Runtime root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v20`.
- Training COMPLETE: 1,784/1,784 updates on 3,568 admitted rows. Validation COMPLETE: 20/1080 (1.85%) vs V12’s 120/1080 (11.11%). See [results](results.md).
- Existing V18 subset initially800 comment-qualified original-task proofs; additional eligible existing tiny, Workbook and public examples are subject to exact manifest admission. Missing comments, broad automation and invalid receipts cause visible exclusions.
- Training worker owns assembly/execution/death watch; root publishes compact evidence. No new paid generation or Lean compilation is required for this assembly.
