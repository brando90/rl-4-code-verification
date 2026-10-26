# V19: prospective GX10 training and complete validation protocol

**Doc link:** [experiment home](README.md)

**TLDR:** Reuse the admitted corpus and V6 mixed starting checkpoint, change execution host to GX10 with explicit runtime disclosure, and complete training plus the full fixed validation manifest. The 818-replacement snapshot is used only for a discarded hardware control; production waits for the fully processed V18 cleanup cohort.

## Authorization and scope

The user explicitly authorized GX10 execution, installation and an Astra terminal worker to convert the code. The root coordinator owns the global paid-model cap, currently $900 total across related work; this training/evaluation code makes no hosted-model calls. Training port and the single artifact relay are owned by `/root/unattended_and_gap_sources`; `/root/train_current_and_cleaned` owns the actual GPU controls, production launch, inference and scoring. No external messages or email are part of this work.

The idle SNAP watcher PID2110195 was stopped before any cleaned-condition optimizer update; its immutable fence is `../expt_v12/results/gx10_migration_fence.json`. Existing SNAP and GX10 jobs belonging to other owners are preserved.

## Data and starting weights

- Common initial weights: completed V6 mixed 1.7B checkpoint, SNAP `/lfs/skampere1/0/eth127/rl4cv_tiny_training/onep7/runs/mixed/hf`. The original file manifest hash is `0acf7b913175e58d9bc3ead57bd0c0eb0a71669f494918cef404dec77dc9ee7b`; verify every weight/tokenizer/configuration file after transfer.
- Control snapshot only: V12 `cleaned/data`, SHA256 `deefba0e3dc86c6910a1d5d3b3137cd18510efc1cb943395cff5f372b9356d6c`, 10,940 rows, 818 verified replacements, 13,420,616 supervised tokens. No production run is launched on this interim snapshot.
- Production original-pool source: V18's final fully processed cleanup manifest. All 2,585 original source row identities must be accounted for; every retained replacement has unchanged implementation/API/specifications/statements, proof-only scope receipts, exact source hashes, pinned-kernel checks and frozen FILE/Qwen-template checks. Honest unresolved rows may be excluded with an explicit table. Do not call unresolved fallbacks fully cleaned.
- Non-original sources remain the admitted V12 500 tiny +7,794 unique Workbook +61 repaired Workbook examples under their prior verified-fallback policy. They are not newly described as free of broad automation.
- Keep the admitted V12 logical order for retained rows, one pass each; any removed row is listed. If exclusions change row identities or lengths, report that this is not a strict row-matched or equal-token ablation. No truncation; total prompt plus assistant cap 16,384. Recheck the 764 protected references with no retained exact or near overlap. Teacher workers never receive protected validation/test source, student validation outputs or source-dependent diagnostics.
- Freeze final dataset, source, schedule, initial-weight and prompt/scorer manifests before production optimizer updates. V12, V13 and their historical receipts remain immutable.

## Training and hardware control

- GX10 environment supplied by the existing setup: `/home/lethan3/workspace/rl4cv-gx10/training-v14/.venv`, observed PyTorch2.9.1+cu130 and Transformers4.55.4. Record actual GPU model, architecture, usable memory, driver and package versions at launch. V12 used A100/PyTorch2.7.1+cu128; numerical equivalence or a data-only causal comparison is not claimed.
- Reuse V12's actual training code through a small host/path wrapper where possible: float32 parameters and CUDA AdamW states; bfloat16 autocast; scaled-dot-product attention; gradient checkpointing; microbatch1/accumulation2; assistant-token weighted loss with masked prompts; fresh AdamW beta=(0.9,0.98), epsilon1e-5, weight decay0.1, clip1.0; seed20261019; learning rate2e-5, 3% token warmup then cosine decay. Supervise the same end-of-turn/EOS sequence. No optimizer, precision, mask or attention substitution to make a failed control appear successful.
- Before production, load the ENTIRE real 1.7B initial checkpoint and run one discarded update combining the actual longest16,112-token control row and shortest row. Check finite loss, nonzero gradient, peak allocated/reserved memory and actual device context. The earlier tiny-Qwen installation control is not this acceptance gate.
- Reload the original starting checkpoint and fresh optimizer for production. Report training started only after its first real optimizer update; a tmux session or a loaded model is insufficient. Preserve every failed control and the exact source/runtime settings.
- One GX10 GPU, explicitly `CUDA_VISIBLE_DEVICES=0`. Expected full-state footprint from A100 observations is roughly50GB allocated /60–70GB reserved plus host/runtime memory; measure unified-memory headroom locally. Duration is unknown until real full-model throughput is measured; then record an estimate from the frozen token schedule. No idle duplicate training on SNAP.

## Validation and scoring

- Complete all135 frozen VeriBench V1 validation tasks ×eight samples =1,080 cells. The held-out test split stays sealed. Same prompt hashes, addendum, thinking-on chat rendering and FILE extraction as V6/V12.
- Fixed decoding: temperature0.6, top-p0.95, top-k20, max12,288 new tokens, extra stop `<|im_end|>`, seed for each cell `91*100003+sample_idx`. Preserve each declared cell, failure, length cap and infrastructure retry. Do not resample based on scores.
- Prefer the existing frozen vLLM route on SNAP if an eligible GPU becomes available. Provide a GX10 GPU Transformers fallback so cluster saturation cannot leave the experiment at weights alone. Record the actual backend and any implementation/numerical difference; retain per-cell random seeds rather than advertising unused seeds. A custom GPU sampler must be checked for stop handling, sampling support and per-cell random streams before measured generation.
- Use the exact pinned scorer/kernel source hashes from V12 scoring preflight, `score_scsc.py --skip-tc`, original gold mapping, native Lean4.22.0 and matching Mathlib. Native ARM Lean already exists under `/home/lethan3/workspace/rl4cv-gx10/lean-v4.22.0/`; verify the actual executable, imports and positive/negative kernel controls. No verifier, statement or accepted-axiom relaxation.
- Apply the same `reward_kernel_binary` and syntactic non-vacuity gate as V6. Report format extraction, compilation, proof/test factors, length caps, full-declared coverage, 135-task bootstrap95% intervals and Core/Industry separately. No formal-specification-coverage judge is silently substituted; it remains unmeasured unless separately authorized.

## Persistence and records

GX10 home: `/home/lethan3/workspace/rl4cv-gx10/experiment-v19/`, with `initial_hf/`, `conditions/<condition>/data/`, code and receipts. Artifact relay is single-writer, encrypted SSH via the Mac when host-to-host authentication is unavailable, with checksums and resumable partial files. Once staged, training and subsequent generation/scoring run in named remote sessions with ordinary-code completion/death watches and do not depend on the laptop staying awake.

The root coordinator publishes compact per-row tables and live updates to Git. Raw generations, logs, model weights and optimizer states stay on the execution host behind an exact artifact manifest. Every change to these prospective settings is recorded before its affected phase; later failures are retained rather than rewritten as an original forecast.
