# Experiment 08 device-layout admission — 10-09-2026

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/layout_10-09-2026/README.md>

The smaller-device investigation is complete for this bounded coordinator phase. No new production layout is admitted, and 14B production remains at 0/658 updates. The most promising measured alternative is eight 16-GiB RTX A4000 cards on Mercury2 with central processing unit (CPU) state offload and whole-decoder activation checkpointing. Its resumed optimizer-update gate is unfinished.

## Decision and measured evidence

| Route | Evidence | Admission |
|---|---|---|
| Two A100 80-GiB devices, tensor parallelism (TP) 2, CPU state offload | Two full-length optimizer updates per rank; about 59.08 GiB peak reserved/device; first logged step 372.264s under heavy shared CPU load | Blocked: all 80/80 query/key normalization gradient hashes differ across the two ranks; changing head partitions changes the pinned implementation's gradient semantics |
| Eight RTX A4000 16-GiB devices, TP8, CPU state offload, whole-decoder checkpointing | Two logical updates; training times 124.020 s and 121.506 s; native random access memory (RAM) checkpoint 27.126 s; peak reserved 14.471 GiB/device including resume initialization | Pending: checkpoint restored, 16/16 sampled parameter hashes matched, and one full-length backward completed on each resumed rank; the third optimizer update did not finish before the probe deadline |
| Historical eight-device A100 route | Original frozen configuration, existing environment and launch chain preserved | Admitted; unavailable in final survey (only devices 1,2 idle) |

The eight-device shape is not a protocol requirement. Protocol sections 8/14 permit recorded infrastructure changes. The actual pinned TP implementation makes the current TP2 candidate scientifically inequivalent: head-sharded query/key normalization gradients lack TP synchronization, and replicated contributions also enter clipping. No normalization/optimizer repair was silently applied. Four devices have a plausible raw state-memory budget (about 55.04 GiB/device), but a TP4 change has the same unresolved head-partition issue; no four-device memory failure is claimed. The historical four-visible-device ResourceInsufficientError was a world-size request failure.

The native worker keeps float32 master parameters, gradients/reductions and AdamW moments, with bfloat16 compute and foreach=false/fused=false. State storage is about 220.065 GiB total, or 110.032 GiB/device without offload at TP2. Mercury used four CPU threads per rank (32/96 logical CPUs); skampere1 used eight per rank (16/128 CPUs) while shared load exceeded 700. These are two Mercury steps and one fully logged A100 step, not stable long-run throughput estimates or a controlled speed comparison.

## Gates and limitations

Exact Base/tokenizer hashes and all 527 tracked NeMo files matched their pins. All 1,315 rendered training examples, loss masks and ordering reproduced, followed by one fully masked pad; global batch 2, microbatch 1, sequence 16384 without packing, seed 20260830, 658 updates, warmup 20/cosine 638, and checkpoints 82/164/334/497/658 remain fixed. The frozen cumulative assistant-token budgets are 720775/1442549/2884708/4318781/5752936. Production padding remains divisible by 8; only disposable probes padded every microbatch to 16384.

Mercury's native logs report assistant-token counts 8837 and 14076, losses 0.4581782222 and 0.3743437529, learning rates approximately 1e-6 and 1.95e-6, and unclipped gradient norms 2.2707908154 and 1.8795242310 (clipping threshold 1). CPU versus CUDA AdamW samples passed the prospectively fixed relative tolerance 1e-5/absolute tolerance 1e-7 check; samples cover 2 parameters × 2048 elements per rank/update. They do not prove whole-trajectory or bitwise equivalence. GPU/CPU/topology changes can change floating-point trajectories. All actual checkpoint inputs observed were bfloat16 [1,16384,5120]. Validation, selection, inference and test gates are unchanged.

A completed native step 2 checkpoint contained 177,249,587,197 bytes in 28 files. Resume loaded weights/optimizer/dataloader state; native zero-learning-rate optimizer initialization was excluded from training-update counts. The resumed step 3 update and its expected 7405 real assistant tokens remain unverified. Checkpoint metadata and complete file hashes were retained, and the disposable RAM tensor payload was removed to release 165.08 GiB. It cannot initialize production. A new admitted production run must start from pinned Base.

## Probe accounting and recovery

The prospective plan was written before allocation. After source/execution evidence rejected TP2, a prospective revised resource shape allowed eight smaller cards while preserving the original cumulative 1800-second accelerator window. Every failure remains recorded: 78.302 s for premature GPU binding, 9.088 s for an excessive Ray socket path, 114.577 s for a hook that missed deserialized worker globals (real CUDA memory error in the original submodule-checkpoint path), then 593.912 s for the actual whole-decoder attempt. The original TP2 attempt used 988.028 s.

Total accelerator window: 1783.9074669163674/1800 seconds; 16.09253308363259 seconds remain, insufficient for another native resume. Total device-time is 8343.091856226325 seconds across the recorded shapes. All accelerator leases and owned probe children are released. No budget or attempt was reset. No extra provider call, purchase, billing reset or evaluation occurred.

The healthy pipeline was safely reloaded from process 3371983/start 1616401 to 4005026/start 8095062 on the same boot, while no scientific child or live lease existed. Its first new tick read the admission registry; all scientific retry counters were preserved. It can automatically execute the historical admitted route when idle devices are available. Registry candidates cannot launch merely because they fit memory. Mercury additionally needs a completed bounded resume check and a tested remote production adapter; a draft supervisor outside the repository was never launched and is not admission evidence.

Final survey: skampere1 idle 1,2; skampere2 none; skampere3 only B200 index 7; Mercury1/2 all 10 A4000s idle. This is an execution-ready resource wait for the admitted historical route, plus an explicit unresolved admission gate for the measured alternative. Future coordination must read the cumulative ledger and preserve every failed attempt; it must not infer a fresh probe budget or an eight-device scientific prerequisite.

The scientific study remains 15/20 trained rungs and 20,520/25,920 full validation cells (17,280 new + 3,240 reused). All 5,400 missing cells belong to trained 14B; selection and new test/judging remain pending. Completed 1.7B/4B/8B and reused baselines were not changed.

Receipts: [admission registry](../sft_layout_admission_14B.json), [TP2 summary](tp2_execution_summary.json), [Mercury summary](mercury_execution_summary.json), [probe ledger](probe_accounting.json), [resource survey](final_resource_survey.json), [static invariants](static_invariants.json), [rendered-data check](render_comparison.json), [source semantics](source_semantics.json), and [pipeline reload](pipeline_reload.json).

Deterministic validation: `make test` **204 passed,4 skipped**; Python compilation and `git diff --check` passed. The four skips are the existing optional dependency cases.
