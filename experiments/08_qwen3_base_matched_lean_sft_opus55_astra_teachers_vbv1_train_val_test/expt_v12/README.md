# V12: current corpus and explicit-proof 1.7B continuations

**Doc link:** [protocol](PROTOCOL.md)

**TLDR:** Continue Qwen3-1.7B with all currently verified data, then run the matched proof-cleaned branch while recording independent validation progress toward 25% success.

**Status:** RUNNING, 10-19-2026 06:11 PDT. Production training passed its first actual optimizer update on A100 GPU1; the full pipeline and cleaned-branch watcher run remotely.

The [protocol](PROTOCOL.md) defines immutable admission, starting weights, one-pass exposure and validation settings. [Live results](results.md) and the [checkpoint](CKPT_training.md) record every phase; raw files remain at the remote root named in the protocol. The second branch waits for verified replacements and does not hold an idle GPU.
