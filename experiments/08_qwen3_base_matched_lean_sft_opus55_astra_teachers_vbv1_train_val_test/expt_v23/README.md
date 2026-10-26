# V23: fresh-base1.7B training with repaired tiny proofs

**Doc link:** [prospective protocol](PROTOCOL.md)

**TLDR:** Train again from original Qwen3-1.7B-Base, adding all500 accepted tiny examples and eligible existing explicit alternatives. This is a new fresh-optimizer run; V20 validation proceeds separately.

## Status

Training and validation COMPLETE: 17/1080 (1.57%) on the sealed VeriBench V1 validation panel (see [results](results.md)). Still below V12’s 120/1080 (11.11%). Raw artifacts stay under `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v23`.

## Decision criterion

Measure the frozen VeriBench V1 validation binary success rate, target25%, with all declared cells retained and the test split sealed. [Protocol](PROTOCOL.md) fixes source admission, initialization, one-epoch training, hardware monitoring and full evaluation.
