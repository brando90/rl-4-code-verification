# Astra assignment: thin GX10 trainer port

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v19/astra_port_prompt.md

**TLDR:** Implement a thin path/device wrapper around the supplied frozen trainer for the ARM GB10 host. Preserve the exact optimization and dataset checks. Do not launch training or inference; the training owner runs the full-model smoke and later production.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

You are the user-requested Astra code port worker. Work only in this micro Git directory. Read the supplied `train.py`, `assemble.py`, `PROTOCOL.md` and `runtime_context.json`. Write `train_gx10.py` and `PORT_NOTES.md`. You may run Python syntax checks. No GPU work, model downloads, API calls, installs, Git commits/pushes, new agents, or edits outside this directory. Do not read training examples, validation tasks, model outputs or credentials. You have at most fifteen minutes; implement the smallest complete port.

The GX10 root is `/home/lethan3/workspace/rl4cv-gx10/experiment-v19`. Its user environment is `/home/lethan3/workspace/rl4cv-gx10/training-v14/.venv`; PyTorch 2.9.1+cu130, Transformers 4.55.4, ARM64, NVIDIA GB10 compute capability 12.1, 20 CPU cores, approximately 119 GiB shared RAM. Real BF16 matrix/backward/AdamW and tiny random Qwen3 SDPA controls passed. SNAP uses Torch 2.7.1+cu128; record the runtime phase difference, never promise numerical identity. No vLLM is installed or required for this training port.

Artifacts are being transferred once, hash-checked, into:

- `initial_hf/`: exact full 1.7B version 6 mixed checkpoint; `source_weights_manifest.json` binds its files.
- `conditions/partial818/data/`: immutable 10,940-row snapshot, 818 proof replacements, 13,420,616 assistant loss tokens, 5,470 updates. Use only for a disposable longest-sequence smoke; no partial818 production run is authorized.
- `code/expt_v12_frozen/`: exact receipt-bound original source files.
- `transfer_completion_initial.json`: sender/receiver hash-check readiness receipt. Require completion before model loading.

Expose configurable `--root`, `--condition`, `--frozen-source-dir`, and `--smoke` options. Preserve the original trainer by importing it after binding the supplied assemble-module constants (`ROOT`, `START`, `HERE`, etc.) to new physical paths; prefer this over copying/reimplementing its training loop. Validate that the original frozen source and data/initial manifests match, and record a new wrapper/runtime identity. Refuse production for partial818. Accept a future separately frozen final V18 condition only when all its source/data/weight checks are satisfied; do not silently weaken source provenance gates to make new data work.

The optimization contract is unchanged: full float32 model parameters and AdamW moments on CUDA, BF16 autocast, SDPA attention, gradient checkpointing with non-reentrant recomputation, one example per microbatch and accumulation over the existing two-example schedule, loss-token weighting/masking, seed 20261019, original learning-rate function, clip 1.0, betas (0.9,0.98), epsilon 1e-5, weight decay 0.1, original row order and exact assistant-token budget. No quantization, LoRA, CPU offload, BF16 master weights, changed optimizer, extra data, shorter context or silent batch/seed changes. Keep thread limits explicit for ARM. Preserve per-step progress, first-update identity, hashes and final checkpoint.

The smoke uses the entire 1.7B model from the exact same initialization, the longest 16,112-token row plus the shortest row, one disposable update, finite loss/gradients and measured peak memory. The training owner runs it, then measures early updates to estimate throughput. Do not start an optimizer here.

Write a separate `runtime_diagnostics.json` alongside smoke/training outputs, including `torch.cuda.max_memory_reserved`, `torch.cuda.max_memory_allocated`, current allocated/reserved memory, `torch.cuda.mem_get_info` free/total bytes, device name/capability, Torch/CUDA/Transformers versions, and whether the run was disposable smoke. Capture diagnostics in `finally` as well as normal completion. This observational wrapper must not alter the frozen trainer's optimizer, data, random state, memory dtype, schedule, or existing receipts.

Another agent owns validation generation, full 135×8 manifest, frozen prompts/seeds/settings and CPU scoring. Do not implement or modify its inference/scoring adapter. In `PORT_NOTES.md`, explain how your wrapper will be invoked, what exact checks it adds, the runtime differences, and any dependency on the other owner's full-model smoke. Report uncertainty directly instead of changing the frozen experiment to hide it.

**TL;DR:** Produce only the minimal trainer wrapper and its port notes, preserving the supplied training contract. The training owner will execute the independent full-model control and final-condition run.
