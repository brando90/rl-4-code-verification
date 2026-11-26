# Gemma-3 smoke: 4B OOM in backward, chunked loss fix, resubmitted (11-26-2026)

Own PyTorch/HF trainer plus vLLM, Sherlock, no agent harness, no spend. AT-3575.

## What failed (11-26-2026)
- 53692828 (gemma4b, eager, H100 80 GB, seed 20260831): FAILED exit 1 after 2:00, `torch.OutOfMemoryError` in `backward()`: tried to allocate 16.82 GiB, 59.2 GiB allocated by PyTorch, GPU full at 79.1 GiB. Model loaded in 63 s; steps.csv has only the header.
- 53692827 (gemma4b, sdpa, seed 20260830): FAILED exit 1 after 0:48, same error at the same line (tried 16.82 GiB, 57.3 GiB allocated).
- 53692831 (smokegen-g4b): CANCELLED at 0 s, dependency (afterok on 53692827) failed.
- 53692825, 53692826 (gemma1b smokes) and 53692830 (smokegen-g1b) had not started (still pending for an 80 GB GPU since 11-25 12:30).

## Cause (ours, shared by both)
16.82 GiB = 17,221 tokens x 262,144 vocabulary x 4 bytes: the fp32 logits of the longest (17,221-token) example. HF's `labels=` loss materialises them for the whole sequence (and the same again in backward). With 4B fp32 weights + grads (~32 GiB) on top, the 80 GB card fills. Gemma-3's vocabulary is 262,144; Llama's is 128,256, which is why the Llama smokes fit.

## Fix
`chunked_lm_loss` in train_v28.py: run the base model, then the lm_head + cross-entropy in checkpointed 2,048-position chunks over the assistant positions only (mean over assistant tokens, same as the HF loss; final-logit softcap honoured if the config has one). It is on for the gemma3 family only (`V28_CHUNKED_LOSS=auto|on|off`), so the Llama code path is unchanged. identity.json records `chunked_loss`.
- tests/test_chunked_loss.py: value and gradient equal to the HF loss on a short example (CPU, fp32): see results below.

## Resubmitted (Sherlock, $SCRATCH/rl4cv_sherlock/expt_v28_gemma_smoke; ids in jobs_v28_gemma_smoke_attempt2.tsv)
- prepare2 53779892 (re-hashes the changed trainer into prepare_receipt.json; same tokens, MAX_SEQ 17408)
- chunktest 53779913 (CPU equivalence test, after prepare2)
- gemma4b sdpa 53779920, gemma4b eager 53779923, smokegen gemma4b 53779926 (after sdpa)
- the still-pending gemma1b smokes 53692825/26 and 53692830 kept; their dependency now also waits on prepare2 and chunktest (so they use the fixed trainer; they never ran).
- the failed attempt's trainer is kept as train_v28.attempt1_full_logits.py; failed run dirs runs_smoke/gemma4b_s2026083{0,1} (identity.json + header-only steps.csv) are evidence and will block the re-run ("existing trajectory") unless moved: moved to runs_smoke_attempt1_oom/ before the new jobs start.

## Update 07:30 PST (attempt 3 reads)
- prepare2 53779892 PASS (2:37). chunktest 53779913 PASS: HF loss 2.761373996734619 vs chunked 2.761373996734619 (abs diff 0.0), worst relative gradient difference 3.0e-6 over 340 parameter tensors (gemma1b, eager, CPU, fp32).
- gemma4b eager 53779923 (seed 20260831): FAILED exit 1 after 2:08, again `OutOfMemoryError` in backward, now a different allocation: tried 8.27 GiB, 54.13 GiB allocated by PyTorch plus 18.53 GiB reserved-but-unallocated (73.4 GiB in use of 79.1). The 16.8 GiB logits are gone, so the chunked loss worked; what is left is eager attention at 17k tokens (T x T scores per layer, quadratic) plus allocator fragmentation. No step was logged (peak memory unrecorded). The eager probe is a side question (sdpa is what Llama used); not resubmitted. Run dir moved to runs_smoke_attempt2_eager_oom/.
- run_job.sh now sets PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True for train/smoke jobs (no numerical effect). Pending jobs pick it up when they start: 4B sdpa 53779920 (Slurm est. start 09:24), 1B smokes 53692825/26 (est. 12:02), generations after them.

## Open
Per-model pass/fail, peak GPU memory at 17,221 tokens, vLLM load of the 4B export, and the keep-1315-rows vs drop-2-long-rows choice: after the new jobs end.
