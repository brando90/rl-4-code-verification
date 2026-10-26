# Sherlock H100 training replication protocol

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/PROTOCOL.md>

**TLDR:** Train Qwen3-1.7B-Base twice on the same previously screened Lean corpus, with two fixed shuffled data orders, to establish a usable Sherlock training path. This is a separate Transformers implementation and a training reliability study, not a continuation of the frozen NeMo runs or evidence of improved VeriBench performance.

**Status:** LOCKED 10-18-2026 14:57 PDT; publication and input checks precede the first optimizer update.

## Question and decision criterion

Can one scheduler-managed 80 GB H100 complete a full, reproducible, train-only supervised fine-tuning pass and export a usable checkpoint? Continue toward larger Sherlock training only after both declared runs complete all 658 optimizer updates, consume every admitted example once, keep finite losses and gradients, and produce hashed model exports. A missing or failed run remains incomplete; no seeds or rows are replaced. Queue acceptance is not successful training.

## Inputs and population

- Model: `Qwen/Qwen3-1.7B-Base`, revision `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`.
- Corpus: the original 1,315 admitted examples from 476 VeriBench V1 train tasks; SHA-256 `885d4ae2d6cf193bddc43df6ad6274cacfa8c98a5e5ecd63bd2519472f5e7354`. Source: `/lfs/skampere1/0/brando9/rl4cv_e08/sft/s_v1.jsonl`. The existing D-013 split and held-out screening admission are reused by exact corpus identity.
- Each run consumes 5,752,936 assistant loss tokens, including the inherited formatting and end token. Every prompt and assistant token sequence must match the committed version-1 per-example hashes in `token_manifest.jsonl`; any mismatch prevents all training. Maximum sequence length 16,384; no truncation or packing.
- Seeds `20260830` and `20260831` independently permute all 1,315 row indices using Python's `random.Random(seed).shuffle`. Persist the order hash. Both begin at the same Base weights. This changes the historical order deliberately and is a new version.
- Validation and test text, references and outcomes are not loaded. This run measures optimization and execution only. No formal-correctness or generalization claim is admitted.

## Training recipe and implementation differences

One GPU, global batch two sequences using serial microbatches of one; final odd batch contains its one remaining example with token-normalized loss. Assistant-only causal cross-entropy, aggregated by assistant token count within each batch. AdamW learning rate 0.00002, betas (0.9, 0.98), epsilon 0.00001, weight decay 0.1; gradient clipping 1.0. Twenty-step linear warmup from 5% to full rate, then 638-step cosine decay to zero. Activation checkpointing enabled.

Sherlock's installed Python 3.14.2, PyTorch module `2.9.1_py314` (runtime reports `2.9.1a0`) and Transformers 4.57.3 are used. Parameters and AdamW states are float32; autocast activations use bfloat16; attention uses PyTorch scaled dot-product attention. The original run used NeMo distributed tensors and a different runtime. Numerical equivalence with that run is not assumed. All actual versions, device identities and input/source hashes are recorded. Seeds and data order are repeatable; bitwise reproducibility across hardware is not claimed.

## Resources, scope and stopping

Brando requested Sherlock training on 10-18-2026. Use existing `sanmi` scheduler access, one H100 at a time, four CPU cores and 64 GB host memory. Estimated device memory 40–70 GB at the longest sequences; compute-bound forward/backward passes with brief checkpoint I/O pauses. Expected total training 2–4 hours, uncertain until initial throughput is measured. Each of the two jobs has a four-hour limit: maximum eight GPU-hours. A preceding CPU-only preparation job has four cores, 16 GB RAM and one hour. No paid provider, judge, subscription or dashboard calls.

Preparation must pass before seed 0 starts; seed 1 depends on successful seed 0. Use scheduler-provided `CUDA_VISIBLE_DEVICES`, never an unallocated device. If an operation fails, retain its receipt and stop dependent work. No automatic retry, budget reset, seed substitution or data resampling. No foreign process is signalled. Existing SNAP training and recovery workers retain their ownership.

## Evidence and lifecycle

Store per-step loss, gradient norm, consumed-token count, elapsed time and peak device memory in CSV; full state every 100 steps and at completion; final Hugging Face export and SHA-256 manifest. Read final checkpoint configuration/weights and all 658 receipt rows before claiming completion. These training metrics have no held-out accuracy interpretation; intervals and statistical significance are not estimated from two training runs.

Canonical remote home: `/scratch/users/brando9/rl4cv_sherlock/expt_v4`. Sherlock scratch expires after 90 days without content changes; archive needed final weights to approved persistent storage before that policy applies. Keep only bulky corpus, token tensors, training states and weights outside Git; publish per-step tables and receipts in this experiment. Submission: `bash submit.sh`; scheduler identifiers are in `jobs.tsv`. The local master publishes progress and final results; scheduler jobs survive browser closure.

**TLDR-end:** [rl4cv: Sherlock training] `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4` tests full two-seed training on Sherlock with exact admitted data and separate runtime provenance; held-out performance remains unmeasured.

## Operational launch addendum, 10-18-2026 15:19 PDT

Before any training, CPU preparation was moved from the interactive-only development partition to `normal`; the Slurm wrapper uses `SLURM_SUBMIT_DIR` because Slurm spools batch scripts. One unstarted preparation job was cancelled and replaced. These changes do not alter scientific inputs or the training recipe. A terminal `afterany` collector records failures as well as success, copies retained checkpoints to the verified writable persistent group directory, checks file hashes, and builds a compact results bundle. Three deterministic controls exercise successful, failed/cancelled/timed-out and truncated/missing outcomes. No training retry is introduced.
