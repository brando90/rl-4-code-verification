# V23: fresh-base1.7B training with repaired tiny proofs

**Doc link:** [prospective protocol](PROTOCOL.md)

**TLDR:** Train again from original Qwen3-1.7B-Base, adding all500 accepted tiny examples and eligible existing explicit alternatives. This is a new fresh-optimizer run; V20 validation proceeds separately.

## Status

Preparing dataset freeze and a genuinely empty A100 allocation. No production update claimed yet. Exact row counts, source hashes, first update, training progress and all1080validation cells will be recorded in this folder; raw artifacts stay under RUN/corpus_training_v23 on skampere1.

## Decision criterion

Measure the frozen VeriBench V1 validation binary success rate, target25%, with all declared cells retained and the test split sealed. [Protocol](PROTOCOL.md) fixes source admission, initialization, one-epoch training, hardware monitoring and full evaluation.
